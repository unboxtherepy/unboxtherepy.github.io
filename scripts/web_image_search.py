"""Reliable web image search using multiple sources"""
import requests
from bs4 import BeautifulSoup
import re
from urllib.parse import quote_plus, urljoin, urlparse
import json

USER_AGENT = "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/120.0.0.0 Safari/537.36"


def search_duckduckgo_images(query, limit=10):
    """
    Search DuckDuckGo for images (most reliable, doesn't block)
    """
    print(f"🦆 Searching DuckDuckGo Images...")
    
    try:
        # DuckDuckGo doesn't require API key
        url = "https://duckduckgo.com/"
        
        session = requests.Session()
        session.headers.update({'User-Agent': USER_AGENT})
        
        # Get initial page to get vqd token
        response = session.get(url, timeout=10)
        
        # Now search for images
        search_url = f"https://duckduckgo.com/?q={quote_plus(query)}&iax=images&ia=images"
        
        response = session.get(search_url, timeout=10)
        
        # Try to extract image URLs from the page
        # DuckDuckGo loads images via JavaScript, but we can try to find some in HTML
        soup = BeautifulSoup(response.text, 'html.parser')
        
        images = []
        
        # Look for image elements
        img_tags = soup.find_all('img', src=True)
        
        for img in img_tags:
            src = img.get('src')
            if src and src.startswith('http') and 'logo' not in src.lower():
                images.append({
                    'url': src,
                    'alt': img.get('alt', query),
                    'source': 'duckduckgo'
                })
                print(f"📸 Found: {src[:80]}...")
                
                if len(images) >= limit:
                    break
        
        return images
        
    except Exception as e:
        print(f"❌ DuckDuckGo search failed: {e}")
        return []


def search_bing_images(query, limit=10):
    """
    Search Bing Images (more scraper-friendly than Google)
    """
    print(f"🔍 Searching Bing Images...")
    
    try:
        url = f"https://www.bing.com/images/search?q={quote_plus(query)}"
        
        headers = {
            'User-Agent': USER_AGENT,
            'Accept': 'text/html,application/xhtml+xml,application/xml;q=0.9,*/*;q=0.8',
        }
        
        response = requests.get(url, headers=headers, timeout=15)
        response.raise_for_status()
        
        soup = BeautifulSoup(response.text, 'html.parser')
        images = []
        
        # Bing stores image data in special attributes
        image_elements = soup.find_all('a', class_=re.compile('iusc'))
        
        for element in image_elements[:limit * 2]:
            m = element.get('m')
            if m:
                try:
                    # Parse JSON data
                    data = json.loads(m)
                    image_url = data.get('murl') or data.get('turl')
                    
                    if image_url:
                        images.append({
                            'url': image_url,
                            'alt': data.get('t', query),
                            'source': 'bing'
                        })
                        print(f"📸 Found: {image_url[:80]}...")
                        
                        if len(images) >= limit:
                            break
                except:
                    continue
        
        return images
        
    except Exception as e:
        print(f"❌ Bing search failed: {e}")
        return []


def search_product_hunt(product_name, limit=5):
    """
    Search Product Hunt for product images
    """
    print(f"🚀 Searching Product Hunt...")
    
    try:
        # Product Hunt search
        search_query = quote_plus(product_name)
        url = f"https://www.producthunt.com/search?q={search_query}"
        
        headers = {'User-Agent': USER_AGENT}
        response = requests.get(url, headers=headers, timeout=15)
        
        soup = BeautifulSoup(response.text, 'html.parser')
        images = []
        
        # Find product images
        img_tags = soup.find_all('img', src=True)
        
        for img in img_tags:
            src = img.get('src')
            if src and 'producthunt' in src and any(x in src for x in ['screenshot', 'product', 'image']):
                images.append({
                    'url': src,
                    'alt': product_name,
                    'source': 'producthunt'
                })
                print(f"📸 Found: {src[:80]}...")
                
                if len(images) >= limit:
                    break
        
        return images
        
    except Exception as e:
        print(f"❌ Product Hunt search failed: {e}")
        return []


def search_imgur_reddit(product_name, limit=5):
    """
    Search for product images on Imgur (often linked from Reddit)
    """
    print(f"📷 Searching Imgur/Reddit...")
    
    try:
        # Search Reddit for the product
        search_query = quote_plus(f"{product_name} review screenshot")
        url = f"https://www.reddit.com/search.json?q={search_query}&limit=10"
        
        headers = {'User-Agent': USER_AGENT}
        response = requests.get(url, headers=headers, timeout=15)
        
        if response.status_code == 200:
            data = response.json()
            images = []
            
            # Extract image URLs from Reddit posts
            for post in data.get('data', {}).get('children', []):
                post_data = post.get('data', {})
                
                # Check for image URL
                url = post_data.get('url', '')
                if any(ext in url.lower() for ext in ['.jpg', '.jpeg', '.png', '.gif', '.webp']):
                    images.append({
                        'url': url,
                        'alt': post_data.get('title', product_name),
                        'source': 'reddit'
                    })
                    print(f"📸 Found: {url[:80]}...")
                    
                    if len(images) >= limit:
                        break
            
            return images
        
        return []
        
    except Exception as e:
        print(f"❌ Reddit search failed: {e}")
        return []


def search_product_images_web(product_name, creator="", limit=15):
    """
    Search for product images using multiple sources
    
    Args:
        product_name: Product name
        creator: Creator/vendor name
        limit: Maximum images to return
    
    Returns:
        List of image dicts
    """
    print(f"\n{'='*60}")
    print(f"🌐 Searching Web for Product Images")
    print(f"🎯 Product: {product_name}")
    if creator:
        print(f"👤 Creator: {creator}")
    print(f"{'='*60}")
    
    all_images = []
    
    # Build search query
    search_terms = [product_name]
    if creator and creator != "Unknown Creator":
        search_terms.append(creator)
    search_terms.extend(["software", "screenshot"])
    
    query = " ".join(search_terms)
    
    # Try multiple sources
    sources = [
        (search_bing_images, "Bing"),
        (search_duckduckgo_images, "DuckDuckGo"),
        (search_product_hunt, "Product Hunt"),
        (search_imgur_reddit, "Reddit/Imgur")
    ]
    
    for search_func, source_name in sources:
        try:
            print(f"\n{'─'*60}")
            print(f"📡 Source: {source_name}")
            print(f"{'─'*60}")
            
            if search_func == search_product_hunt or search_func == search_imgur_reddit:
                images = search_func(product_name, limit=5)
            else:
                images = search_func(query, limit=10)
            
            if images:
                all_images.extend(images)
                print(f"✅ {source_name}: Found {len(images)} images")
            else:
                print(f"⚠️  {source_name}: No images found")
            
            # Stop if we have enough
            if len(all_images) >= limit:
                break
                
        except Exception as e:
            print(f"❌ {source_name} error: {e}")
            continue
    
    # Remove duplicates
    seen_urls = set()
    unique_images = []
    for img in all_images:
        if img['url'] not in seen_urls:
            seen_urls.add(img['url'])
            unique_images.append(img)
    
    result = unique_images[:limit]
    
    print(f"\n{'='*60}")
    print(f"📊 Search Complete")
    print(f"{'='*60}")
    print(f"✅ Total unique images found: {len(result)}")
    
    if result:
        print(f"\n📸 Image sources breakdown:")
        source_counts = {}
        for img in result:
            source = img.get('source', 'unknown')
            source_counts[source] = source_counts.get(source, 0) + 1
        
        for source, count in source_counts.items():
            print(f"   - {source}: {count} images")
    
    return result


def get_product_image_from_web(product_name, creator=""):
    """
    Get best featured image for product from the web
    
    Args:
        product_name: Product name
        creator: Creator/vendor name
    
    Returns:
        dict with image url and alt text, or None
    """
    images = search_product_images_web(product_name, creator, limit=15)
    
    if not images:
        return None
    
    # Return the first (best) image
    print(f"\n✅ Best image selected:")
    print(f"   URL: {images[0]['url'][:80]}...")
    print(f"   Alt: {images[0]['alt']}")
    print(f"   Source: {images[0]['source']}")
    
    return images[0]


def search_and_get_product_images(product_name, creator="", limit=15):
    """
    Search for product images and return list for article embedding
    
    Args:
        product_name: Product name
        creator: Creator name
        limit: Maximum images to return
    
    Returns:
        List of image dicts
    """
    images = search_product_images_web(product_name, creator, limit)
    
    if images:
        print(f"\n✅ Images ready for article embedding")
        print(f"📝 Gemini will place these strategically in the review")
    
    return images


if __name__ == "__main__":
    # Test the search
    print("Testing Web Image Search...")
    
    test_product = "Canva"
    test_creator = ""
    
    images = search_product_images_web(test_product, test_creator, limit=10)
    
    if images:
        print(f"\n{'='*60}")
        print(f"✅ Test Results: Found {len(images)} images")
        print(f"{'='*60}")
        
        for i, img in enumerate(images[:5], 1):
            print(f"\n{i}. {img['alt'][:60]}")
            print(f"   URL: {img['url'][:80]}...")
            print(f"   Source: {img['source']}")
    else:
        print("\n❌ No images found in test")