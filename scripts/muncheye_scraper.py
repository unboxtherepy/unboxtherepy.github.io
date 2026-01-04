"""Scrape products from MunchEye.com - IMPROVED with section targeting"""
import requests
from bs4 import BeautifulSoup
import re
from datetime import datetime, timedelta
from google import genai
from config import GEMINI_API_KEY, TEXT_MODEL
import json

MUNCHEYE_URL = "https://muncheye.com/"
USER_AGENT = "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/120.0.0.0 Safari/537.36"

# Initialize Gemini client
client = genai.Client(api_key=GEMINI_API_KEY) if GEMINI_API_KEY else None


def scrape_muncheye_products(sections=None, limit_per_section=5):
    """
    Scrape products from specific MunchEye sections using AI
    """
    if sections is None:
        sections = ['big_launches', 'just_launched']
    
    print(f"🔍 Scraping MunchEye.com for sections: {', '.join(sections)}")
    
    try:
        headers = {
            'User-Agent': USER_AGENT,
            'Accept': 'text/html,application/xhtml+xml,application/xml;q=0.9,*/*;q=0.8',
            'Accept-Language': 'en-US,en;q=0.5',
            'Connection': 'keep-alive',
        }
        
        print(f"📥 Fetching MunchEye homepage...")
        response = requests.get(MUNCHEYE_URL, headers=headers, timeout=30)
        response.raise_for_status()
        
        html_content = response.text
        
        # Use Gemini to intelligently parse the page
        products = parse_with_gemini(html_content, sections, limit_per_section)
        
        if not products:
            print(f"⚠️  Gemini parsing returned no products, trying fallback...")
            products = parse_with_beautifulsoup(html_content, sections, limit_per_section)
        
        print(f"\n✅ Total products scraped: {len(products)}")
        return products
        
    except Exception as e:
        print(f"❌ Error scraping MunchEye: {e}")
        import traceback
        traceback.print_exc()
        return []


def parse_with_gemini(html_content, sections, limit_per_section):
    """Use Gemini AI to intelligently parse MunchEye HTML"""
    
    if not client:
        print("⚠️  Gemini client not available, using fallback parser")
        return []
    
    print(f"🤖 Using Gemini AI to parse MunchEye sections...")
    
    # Truncate HTML to stay within token limits
    html_sample = html_content[:50000]  # First 50k characters
    
    section_names = []
    if 'big_launches' in sections:
        section_names.append("All Launches")
    if 'just_launched' in sections:
        section_names.append("Just Launched")
    
    prompt = f"""
You are parsing the MunchEye.com website to extract product launch information.

TASK: Extract products ONLY from these sections: {', '.join(section_names)}

HTML CONTENT (truncated):
{html_sample}

INSTRUCTIONS:
1. Find sections titled "All Launches" and/or "Just Launched"
2. Extract products ONLY from these specific sections
3. Ignore all other sections (like "Coming Soon", "Yesterday's Launches", etc.)
4. For each product, extract:
   - Product name (often in format "Creator: Product Name")
   - Creator/Vendor name
   - Price (look for $ amounts)
   - Commission percentage (look for "at XX%")
   - Platform (JVZoo, WarriorPlus, ClickBank, etc.)
   - Launch date if available
   - Product URL/link

5. Return ONLY products from "All Launches" and "Just Launched" sections
6. Maximum {limit_per_section} products per section

OUTPUT FORMAT (JSON array):
[
  {{
    "name": "Product Name",
    "creator": "Creator Name",
    "price": "47",
    "commission": "50",
    "platform": "JVZoo",
    "launch_date": "2026-01-05",
    "url": "https://muncheye.com/product-link",
    "section": "All Launches"
  }}
]

CRITICAL RULES:
- ONLY include products from "All Launches" or "Just Launched" sections
- DO NOT include products from other sections
- Return valid JSON array
- If no products found in target sections, return empty array []
- Extract actual URLs from the HTML

Return ONLY the JSON array, no markdown formatting, no explanations.
"""
    
    try:
        print(f"🔄 Sending HTML to Gemini for analysis...")
        response = client.models.generate_content(
            model=TEXT_MODEL,
            contents=prompt
        )
        
        # Clean response
        response_text = response.text.strip()
        
        # Remove markdown code blocks if present
        response_text = re.sub(r'^```json\s*', '', response_text)
        response_text = re.sub(r'^```\s*', '', response_text)
        response_text = re.sub(r'\s*```$', '', response_text)
        response_text = response_text.strip()
        
        # Parse JSON
        products_data = json.loads(response_text)
        
        if not isinstance(products_data, list):
            print(f"❌ Gemini returned non-list data")
            return []
        
        # Validate and enrich products
        validated_products = []
        for product in products_data:
            if not product.get('name'):
                continue
            
            # Ensure all required fields
            validated_product = {
                'name': product.get('name', 'Unknown Product'),
                'creator': product.get('creator', 'Unknown Creator'),
                'price': str(product.get('price', 'Unknown')),
                'commission': str(product.get('commission', '50')),
                'platform': product.get('platform', 'Unknown'),
                'launch_date': product.get('launch_date', datetime.now().strftime('%Y-%m-%d')),
                'url': product.get('url', MUNCHEYE_URL),
                'section': product.get('section', 'Unknown'),
                'category': 'Product Launch',
                'scraped_at': datetime.now().isoformat()
            }
            
            validated_products.append(validated_product)
            print(f"✅ Found: {validated_product['creator']}: {validated_product['name']} (${validated_product['price']}) - Section: {validated_product['section']}")
        
        print(f"\n✅ Gemini extracted {len(validated_products)} products from target sections")
        return validated_products
        
    except json.JSONDecodeError as e:
        print(f"❌ Failed to parse Gemini JSON response: {e}")
        print(f"Response text: {response_text[:500]}...")
        return []
    except Exception as e:
        print(f"❌ Gemini parsing error: {e}")
        import traceback
        traceback.print_exc()
        return []


def parse_with_beautifulsoup(html_content, sections, limit_per_section):
    """Fallback parser using BeautifulSoup"""
    print(f"🔄 Using BeautifulSoup fallback parser...")
    
    soup = BeautifulSoup(html_content, 'html.parser')
    products = []
    
    # Look for section headers
    section_headers = soup.find_all(['h2', 'h3', 'div'], text=re.compile(r'(All Launches|Just Launched)', re.IGNORECASE))
    
    print(f"📍 Found {len(section_headers)} potential section headers")
    
    for header in section_headers:
        section_name = header.get_text(strip=True)
        print(f"\n🔍 Processing section: {section_name}")
        
        # Get products after this header
        container = header.find_next(['div', 'ul', 'table'])
        
        if not container:
            continue
        
        # Find all links in this section
        links = container.find_all('a', href=True)
        
        section_products = 0
        for link in links:
            if section_products >= limit_per_section:
                break
            
            product = extract_product_from_link(link, section_name)
            if product and product not in products:
                products.append(product)
                section_products += 1
        
        print(f"✅ Extracted {section_products} products from {section_name}")
    
    return products


def extract_product_from_link(link_element, section_name="Unknown"):
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
    
    # Skip navigation links
    if any(skip in product_text.lower() for skip in ['home', 'contact', 'about', 'login', 'register']):
        return None
    
    # Parse creator and product name
    creator = ""
    product_name = product_text
    
    if ':' in product_text:
        parts = product_text.split(':', 1)
        creator = parts[0].strip()
        product_name = parts[1].strip() if len(parts) > 1 else product_text
    
    # Try to find parent container for more info
    parent = link_element.find_parent(['div', 'li', 'tr', 'td'])
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
        'section': section_name,
        'category': 'Product Launch',
        'scraped_at': datetime.now().isoformat()
    }
    
    return product_data


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
    Get products ready for review from All Launches and Just Launched sections
    """
    print(f"\n{'='*60}")
    print(f"🎯 Fetching products from MunchEye")
    print(f"🎯 Target sections: All Launches, Just Launched")
    print(f"{'='*60}")
    
    # Scrape products with increased limit to account for filtering
    fetch_limit = limit * 2
    
    products = scrape_muncheye_products(
        sections=['big_launches', 'just_launched'],
        limit_per_section=fetch_limit
    )
    
    if not products:
        print("❌ No products found in target sections")
        return []
    
    print(f"\n✅ Found {len(products)} total products from All Launches & Just Launched")
    
    # Remove duplicates
    seen = set()
    unique_products = []
    for p in products:
        product_key = f"{p['creator'].lower()}-{p['name'].lower()}"
        if product_key not in seen:
            seen.add(product_key)
            unique_products.append(p)
    
    print(f"✅ {len(unique_products)} unique products after deduplication")
    
    # Show breakdown by section
    section_counts = {}
    for p in unique_products:
        section = p.get('section', 'Unknown')
        section_counts[section] = section_counts.get(section, 0) + 1
    
    print(f"\n📊 Products by section:")
    for section, count in section_counts.items():
        print(f"   - {section}: {count} products")
    
    return unique_products


if __name__ == "__main__":
    # Test the scraper
    print("Testing MunchEye scraper with section targeting...")
    products = get_products_for_review(limit=10)
    
    if products:
        print(f"\n{'='*60}")
        print(f"📊 Sample Products from All Launches & Just Launched")
        print(f"{'='*60}")
        
        for i, product in enumerate(products[:10], 1):
            print(f"\n{i}. {product['creator']}: {product['name']}")
            print(f"   Section: {product['section']}")
            print(f"   Price: ${product['price']} | Commission: {product['commission']}%")
            print(f"   Platform: {product['platform']}")
            print(f"   URL: {product['url']}")
    else:
        print("\n❌ No products found")