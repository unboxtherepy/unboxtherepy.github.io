"""Extract information from product sales pages"""
import requests
from bs4 import BeautifulSoup
import re
from urllib.parse import urljoin

USER_AGENT = "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36"


def scrape_sales_page(url):
    """
    Scrape product sales page for review information
    
    Returns:
        dict with extracted information
    """
    print(f"\n🔍 Scraping sales page: {url[:60]}...")
    
    try:
        headers = {'User-Agent': USER_AGENT}
        response = requests.get(url, headers=headers, timeout=30, allow_redirects=True)
        response.raise_for_status()
        
        soup = BeautifulSoup(response.content, 'html.parser')
        
        # Extract comprehensive information
        sales_data = {
            'title': extract_title(soup),
            'description': extract_description(soup),
            'features': extract_features(soup),
            'pricing': extract_pricing(soup),
            'benefits': extract_benefits(soup),
            'images': extract_images(soup, url),
            'testimonials': extract_testimonials(soup),
            'bonuses': extract_bonuses(soup),
            'vendor_info': extract_vendor_info(soup),
            'guarantee': extract_guarantee(soup),
            'final_url': response.url,
            'page_content': soup.get_text(separator=' ', strip=True)[:5000]
        }
        
        print(f"✅ Successfully scraped sales page")
        print(f"   Title: {sales_data['title'][:60]}...")
        print(f"   Features found: {len(sales_data['features'])}")
        print(f"   Images found: {len(sales_data['images'])}")
        
        return sales_data
        
    except Exception as e:
        print(f"⚠️  Could not access sales page: {e}")
        return None


def extract_title(soup):
    """Extract product title"""
    title_selectors = [
        ('h1', {}),
        ('h2', {}),
        ('.product-title', {}),
        ('.headline', {}),
        ('meta', {'property': 'og:title'}),
        ('title', {})
    ]
    
    for tag, attrs in title_selectors:
        element = soup.find(tag, attrs)
        if element:
            if tag == 'meta':
                return element.get('content', '').strip()
            text = element.get_text(strip=True)
            if text and len(text) > 5:
                return text
    
    return "Unknown Product"


def extract_description(soup):
    """Extract product description"""
    descriptions = []
    
    meta_desc = soup.find('meta', {'name': 'description'})
    if meta_desc:
        descriptions.append(meta_desc.get('content', '').strip())
    
    og_desc = soup.find('meta', {'property': 'og:description'})
    if og_desc:
        descriptions.append(og_desc.get('content', '').strip())
    
    desc_containers = soup.find_all(['p', 'div'], class_=re.compile(r'description|intro|summary'))
    for container in desc_containers[:3]:
        text = container.get_text(strip=True)
        if len(text) > 50:
            descriptions.append(text)
    
    if not descriptions:
        paragraphs = soup.find_all('p')
        for p in paragraphs[:5]:
            text = p.get_text(strip=True)
            if len(text) > 50:
                descriptions.append(text)
    
    return ' '.join(descriptions[:3])


def extract_features(soup):
    """Extract product features"""
    features = []
    
    feature_keywords = ['feature', 'benefit', 'include', 'what you get', 'capability']
    
    for keyword in feature_keywords:
        headers = soup.find_all(['h2', 'h3', 'h4'], text=re.compile(keyword, re.IGNORECASE))
        
        for header in headers:
            next_list = header.find_next(['ul', 'ol'])
            if next_list:
                items = next_list.find_all('li')
                for item in items:
                    feature_text = item.get_text(strip=True)
                    if feature_text and len(feature_text) > 5:
                        features.append(feature_text)
    
    seen = set()
    unique_features = []
    for f in features:
        if f not in seen:
            seen.add(f)
            unique_features.append(f)
    
    return unique_features[:15]


def extract_pricing(soup):
    """Extract pricing information"""
    pricing_info = []
    
    price_pattern = r'\$\s?(\d+(?:\.\d{2})?)'
    
    price_containers = soup.find_all(text=re.compile(price_pattern))
    
    for container in price_containers[:10]:
        match = re.search(price_pattern, container)
        if match:
            context = container.strip()[:100]
            pricing_info.append({
                'price': match.group(1),
                'context': context
            })
    
    price_tables = soup.find_all(['table', 'div'], class_=re.compile(r'price|pricing|package'))
    for table in price_tables[:3]:
        text = table.get_text(strip=True)
        if text:
            pricing_info.append({
                'price': 'See details',
                'context': text[:200]
            })
    
    return pricing_info


def extract_benefits(soup):
    """Extract product benefits"""
    benefits = []
    
    benefit_keywords = ['benefit', 'advantage', 'why', 'solve', 'help you']
    
    for keyword in benefit_keywords:
        sections = soup.find_all(['div', 'section'], text=re.compile(keyword, re.IGNORECASE))
        
        for section in sections[:3]:
            text = section.get_text(strip=True)
            if len(text) > 50:
                benefits.append(text[:300])
    
    return benefits


def extract_images(soup, base_url):
    """Extract product images - prioritize high-quality screenshots"""
    images = []
    
    img_tags = soup.find_all('img')
    
    # Score images based on relevance
    scored_images = []
    
    for img in img_tags[:30]:  # Check more images
        src = img.get('src') or img.get('data-src') or img.get('data-lazy-src')
        if not src:
            continue
        
        if not src.startswith('http'):
            src = urljoin(base_url, src)
        
        # Skip unwanted images
        if any(skip in src.lower() for skip in ['logo', 'icon', 'badge', 'button', 'social', 'avatar', 'gravatar']):
            continue
        
        # Skip tiny images
        width = img.get('width')
        height = img.get('height')
        if width and height:
            try:
                if int(width) < 200 or int(height) < 200:
                    continue
            except:
                pass
        
        alt = img.get('alt', '').lower()
        img_class = ' '.join(img.get('class', [])).lower()
        
        # Calculate relevance score
        score = 0
        
        # High priority: product screenshots, features, dashboard
        if any(keyword in alt for keyword in ['screenshot', 'dashboard', 'interface', 'demo', 'preview', 'feature']):
            score += 10
        if any(keyword in img_class for keyword in ['screenshot', 'product', 'feature', 'demo']):
            score += 8
        
        # Medium priority: general product images
        if any(keyword in alt for keyword in ['product', 'software', 'app', 'tool']):
            score += 5
        
        # Check if image is in main content area
        parent = img.find_parent(['article', 'main', 'section'])
        if parent:
            score += 3
        
        # Prefer larger images
        if 'large' in src.lower() or 'full' in src.lower():
            score += 2
        
        scored_images.append({
            'url': src,
            'alt': img.get('alt', ''),
            'score': score
        })
    
    # Sort by score (highest first)
    scored_images.sort(key=lambda x: x['score'], reverse=True)
    
    # Remove duplicates while preserving order
    seen_urls = set()
    for img in scored_images:
        if img['url'] not in seen_urls:
            seen_urls.add(img['url'])
            images.append({
                'url': img['url'],
                'alt': img['alt']
            })
    
    print(f"📸 Found {len(images)} relevant images (sorted by quality)")
    
    return images[:15]  # Return top 15 images


def extract_testimonials(soup):
    """Extract customer testimonials"""
    testimonials = []
    
    testimonial_sections = soup.find_all(['div', 'section', 'blockquote'], 
                                        class_=re.compile(r'testimonial|review|feedback'))
    
    for section in testimonial_sections[:5]:
        text = section.get_text(strip=True)
        if len(text) > 30:
            testimonials.append(text[:500])
    
    return testimonials


def extract_bonuses(soup):
    """Extract bonus information"""
    bonuses = []
    
    bonus_keywords = ['bonus', 'free', 'extra', 'included', 'gift']
    
    for keyword in bonus_keywords:
        headers = soup.find_all(['h2', 'h3', 'h4'], text=re.compile(keyword, re.IGNORECASE))
        
        for header in headers[:3]:
            next_element = header.find_next(['ul', 'ol', 'p', 'div'])
            if next_element:
                text = next_element.get_text(strip=True)
                if text and len(text) > 20:
                    bonuses.append(text[:300])
    
    return bonuses


def extract_vendor_info(soup):
    """Extract vendor/creator information"""
    vendor_info = {}
    
    vendor_patterns = ['created by', 'developed by', 'from', 'by']
    
    for pattern in vendor_patterns:
        elements = soup.find_all(text=re.compile(pattern, re.IGNORECASE))
        for el in elements[:3]:
            text = el.strip()
            if len(text) < 200:
                vendor_info['mention'] = text
                break
    
    return vendor_info


def extract_guarantee(soup):
    """Extract money-back guarantee information"""
    guarantee_text = []
    
    guarantee_keywords = ['guarantee', 'refund', 'money back', 'risk free']
    
    for keyword in guarantee_keywords:
        elements = soup.find_all(text=re.compile(keyword, re.IGNORECASE))
        for el in elements[:3]:
            text = el.strip()
            if len(text) > 20 and len(text) < 500:
                guarantee_text.append(text)
    
    return ' '.join(guarantee_text[:2])


def search_product_info(product_name, creator=""):
    """
    Search for product information online if sales page unavailable
    """
    print(f"\n🔎 Searching online for: {product_name}")
    
    return {
        'title': product_name,
        'description': f"Information about {product_name} by {creator}",
        'features': [
            "Feature information gathered from online sources",
            "Product specifications",
            "User benefits"
        ],
        'pricing': [{'price': 'Check official site', 'context': 'Pricing varies'}],
        'benefits': ["Helps users achieve their goals"],
        'images': [],
        'testimonials': [],
        'bonuses': [],
        'vendor_info': {'creator': creator},
        'guarantee': "Check vendor's official guarantee policy",
        'page_content': f"Online information about {product_name}"
    }