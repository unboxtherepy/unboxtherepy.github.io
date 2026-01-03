"""Scrape products from MunchEye.com"""
import requests
from bs4 import BeautifulSoup
import re
from datetime import datetime, timedelta
import time

MUNCHEYE_URL = "https://muncheye.com/"
USER_AGENT = "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/120.0.0.0 Safari/537.36"


def scrape_muncheye_products(sections=None, limit_per_section=5):
    """
    Scrape products from MunchEye - IMPROVED VERSION
    """
    if sections is None:
        sections = ['big_launches', 'just_launched']
    
    print(f"🔍 Scraping MunchEye.com...")
    
    try:
        headers = {
            'User-Agent': USER_AGENT,
            'Accept': 'text/html,application/xhtml+xml,application/xml;q=0.9,*/*;q=0.8',
            'Accept-Language': 'en-US,en;q=0.5',
            'Connection': 'keep-alive',
        }
        response = requests.get(MUNCHEYE_URL, headers=headers, timeout=30)
        response.raise_for_status()
        
        soup = BeautifulSoup(response.content, 'html.parser')
        products = []
        
        # Try to find ANY product listings
        print(f"\n🔎 Searching for product listings...")
        
        # Method 1: Look for product links
        product_links = soup.find_all('a', href=re.compile(r'/[a-z0-9-]+/?$'))
        
        if product_links:
            print(f"✅ Found {len(product_links)} potential product links")
            
            for link in product_links[:limit_per_section * 3]:
                try:
                    product = extract_product_from_link(link)
                    if product and product['name'] != 'Unknown Product':
                        products.append(product)
                        if len(products) >= limit_per_section * len(sections):
                            break
                except Exception as e:
                    continue
        
        # Method 2: Look for structured product data
        if not products:
            print(f"⚠️ No products from links, trying alternative methods...")
            products = scrape_alternative_structure(soup, limit_per_section * len(sections))
        
        print(f"\n✅ Total products scraped: {len(products)}")
        return products
        
    except Exception as e:
        print(f"❌ Error scraping MunchEye: {e}")
        return []


def extract_product_from_link(link_element):
    """Extract product info from a link element"""
    
    href = link_element.get('href', '')
    if not href or href in ['/', '#', 'http://muncheye.com', 'https://muncheye.com']:
        return None
    
    # Get full URL
    if not href.startswith('http'):
        href = MUNCHEYE_URL.rstrip('/') + '/' + href.lstrip('/')
    
    # Get product name from link text
    product_text = link_element.get_text(strip=True)
    
    if not product_text or len(product_text) < 5:
        return None
    
    # Parse creator and product name
    creator = ""
    product_name = product_text
    
    if ':' in product_text:
        parts = product_text.split(':', 1)
        creator = parts[0].strip()
        product_name = parts[1].strip() if len(parts) > 1 else product_text
    
    # Try to find parent container for more info
    parent = link_element.find_parent(['div', 'li', 'tr'])
    
    # Extract date, price, commission from parent
    parent_text = parent.get_text() if parent else ""
    
    # Extract date
    launch_date = extract_date(parent_text) if parent_text else datetime.now().strftime('%Y-%m-%d')
    
    # Extract price
    price_match = re.search(r'\$\s?(\d+(?:\.\d+)?)', parent_text)
    price = price_match.group(1) if price_match else "Unknown"
    
    # Extract commission
    commission_match = re.search(r'at\s+(\d+)%', parent_text)
    commission = commission_match.group(1) if commission_match else "50"
    
    # Extract platform
    platform = extract_platform_from_text(parent_text) if parent_text else "Unknown"
    
    product_data = {
        'name': product_name,
        'creator': creator if creator else "Unknown Creator",
        'url': href,
        'launch_date': launch_date,
        'price': price,
        'commission': commission,
        'platform': platform,
        'category': 'Product Launch',
        'scraped_at': datetime.now().isoformat()
    }
    
    print(f"✅ Found: {creator}: {product_name} (${price})")
    
    return product_data


def scrape_alternative_structure(soup, limit):
    """Alternative scraping method if main structure fails"""
    products = []
    
    print(f"🔄 Trying alternative scraping methods...")
    
    # Look for any div/section with product-like content
    containers = soup.find_all(['div', 'article', 'section'], class_=re.compile(r'product|launch|post'))
    
    print(f"📦 Found {len(containers)} potential product containers")
    
    for container in containers[:limit * 2]:
        try:
            # Find link in container
            link = container.find('a', href=True)
            if not link:
                continue
            
            product = extract_product_from_link(link)
            if product and product not in products:
                products.append(product)
                
        except Exception as e:
            continue
    
    return products[:limit]


def extract_platform_from_text(text):
    """Extract platform from text"""
    text_lower = text.lower()
    
    if 'jvzoo' in text_lower or 'jvz' in text_lower:
        return 'JVZoo'
    elif 'warrior' in text_lower or 'w+' in text_lower:
        return 'WarriorPlus'
    elif 'clickbank' in text_lower:
        return 'ClickBank'
    elif 'paykickstart' in text_lower:
        return 'PayKickstart'
    
    return 'Unknown'


def extract_date(text):
    """Extract launch date from text"""
    today = datetime.now()
    
    # Try to find date pattern
    date_pattern = r'(\d{1,2})\s+(Jan|Feb|Mar|Apr|May|Jun|Jul|Aug|Sep|Oct|Nov|Dec)'
    match = re.search(date_pattern, text, re.IGNORECASE)
    
    if match:
        day = int(match.group(1))
        month_abbr = match.group(2)
        
        months = {
            'Jan': 1, 'Feb': 2, 'Mar': 3, 'Apr': 4, 'May': 5, 'Jun': 6,
            'Jul': 7, 'Aug': 8, 'Sep': 9, 'Oct': 10, 'Nov': 11, 'Dec': 12
        }
        
        month = months.get(month_abbr, today.month)
        year = today.year
        
        try:
            date = datetime(year, month, day)
            if date < today:
                date = datetime(year + 1, month, day)
            return date.strftime('%Y-%m-%d')
        except ValueError:
            pass
    
    return today.strftime('%Y-%m-%d')


def get_products_for_review(limit=5, categories=None):
    """
    Get products ready for review
    """
    print(f"\n{'='*60}")
    print(f"🎯 Fetching products from MunchEye")
    if categories:
        print(f"🏷️  Filtering by categories: {', '.join(categories)}")
    print(f"{'='*60}")
    
    # Scrape products with increased limit
    fetch_limit = limit * 5  # Get even more to ensure we have enough
    
    products = scrape_muncheye_products(
        sections=['big_launches', 'just_launched', 'all_launches'],
        limit_per_section=fetch_limit
    )
    
    if not products:
        print("❌ No products found")
        print("💡 This might be because:")
        print("   - MunchEye structure has changed")
        print("   - Network issues")
        print("   - Bot detection")
        return []
    
    print(f"\n✅ Found {len(products)} total products")
    
    # Remove duplicates
    seen = set()
    unique_products = []
    for p in products:
        product_key = f"{p['creator'].lower()}-{p['name'].lower()}"
        if product_key not in seen:
            seen.add(product_key)
            unique_products.append(p)
    
    print(f"✅ {len(unique_products)} unique products after deduplication")
    
    return unique_products


if __name__ == "__main__":
    # Test the scraper
    print("Testing MunchEye scraper...")
    products = get_products_for_review(limit=5)
    
    if products:
        print(f"\n{'='*60}")
        print(f"📊 Sample Products")
        print(f"{'='*60}")
        
        for i, product in enumerate(products[:5], 1):
            print(f"\n{i}. {product['creator']}: {product['name']}")
            print(f"   Price: ${product['price']} | Commission: {product['commission']}%")
            print(f"   Platform: {product['platform']}")
            print(f"   URL: {product['url']}")
    else:
        print("\n❌ No products found - scraper may need updates")