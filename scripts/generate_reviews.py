"""Main script to generate product review posts from MunchEye"""
import os
import time
import datetime
from slugify import slugify

# Import all modules
from config import *
from muncheye_scraper import get_products_for_review
from sales_page_scraper import scrape_sales_page, search_product_info
from json_tracker import (
    get_existing_reviews, 
    filter_unreviewed_products, 
    display_review_stats,
    log_published_review
)
from review_article_generator import (
    generate_review_article,
    create_review_front_matter,
    generate_image_prompt
)
from image_utils import try_download_featured_image, validate_image_file


def submit_to_google_indexing_safe(post_url):
    """Safely attempt Google Indexing (optional)"""
    if not ENABLE_GOOGLE_INDEXING:
        print("⏭️  Google Indexing disabled (no credentials)")
        return "Disabled"
    
    try:
        from google_indexing import submit_to_google_indexing, check_indexing_status
        
        print(f"\n{'='*60}")
        print(f"📤 Submitting to Google Search Console")
        print(f"{'='*60}")
        
        success = submit_to_google_indexing(post_url)
        if success:
            time.sleep(10)
            status_result = check_indexing_status(post_url)
            if status_result and 'latestUpdate' in status_result:
                return "Confirmed in Queue"
            return "Success"
        return "Failed"
    except Exception as e:
        print(f"⚠️  Google Indexing failed: {e}")
        return f"Failed - {str(e)[:100]}"


def send_push_notification_safe(title, permalink, focus_kw):
    """Safely attempt push notification (optional)"""
    if not ENABLE_PUSH_NOTIFICATIONS:
        print("⏭️  Push notifications disabled (no credentials)")
        return False
    
    try:
        from webpushr_notifier import send_blog_post_notification
        
        print(f"\n{'='*60}")
        print(f"📢 Sending Push Notification")
        print(f"{'='*60}")
        
        return send_blog_post_notification(title, permalink, focus_kw)
    except Exception as e:
        print(f"⚠️  Push notification failed: {e}")
        return False


def main():
    print("=" * 60)
    print("🚀 MunchEye Product Review Generator")
    print("=" * 60)
    
    # Verify environment variables
    if not GEMINI_API_KEY:
        print("❌ GEMINI_API_KEY not found")
        return
    print("✅ GEMINI_API_KEY found")
    
    if not FREEPIK_API_KEY:
        print("❌ FREEPIK_API_KEY not found")
        return
    print("✅ FREEPIK_API_KEY found")
    
    # Optional features status
    print(f"📋 Google Indexing: {'✅ Enabled' if ENABLE_GOOGLE_INDEXING else '❌ Disabled'}")
    print(f"📋 Push Notifications: {'✅ Enabled' if ENABLE_PUSH_NOTIFICATIONS else '❌ Disabled'}")
    
    # Get products to review
    print(f"\n{'='*60}")
    print(f"Step 1: Fetching Products from MunchEye")
    print(f"🎯 Targeting: Big Launches & Just Launched sections ONLY")
    print(f"{'='*60}")
    
    # Get products from specific sections
    initial_products = get_products_for_review(limit=POSTS_PER_RUN * 3)
    
    if not initial_products:
        print("❌ No products found in Big Launches or Just Launched sections")
        return
    
    print(f"\n✅ Found {len(initial_products)} products from target sections")
    
    # Step 2: Check for existing reviews
    print(f"\n{'='*60}")
    print(f"Step 2: Checking for Duplicate Reviews")
    print(f"{'='*60}")
    
    existing_reviews = get_existing_reviews()
    display_review_stats()
    
    # Filter out already reviewed products
    products = filter_unreviewed_products(initial_products, existing_reviews)
    
    if not products:
        print("\n❌ All scraped products have already been reviewed!")
        print("💡 Try again later when new products are launched on MunchEye")
        return
    
    # Limit to desired number
    products = products[:POSTS_PER_RUN]
    
    print(f"\n✅ {len(products)} new products ready for review")
    
    posts_generated = 0
    
    for i, product in enumerate(products, 1):
        print(f"\n{'='*60}")
        print(f"📝 Processing Product {i}/{len(products)}")
        print(f"{'='*60}")
        
        product_name = product['name']
        creator = product['creator']
        
        print(f"\n📦 Product: {creator}: {product_name}")
        print(f"💰 Price: ${product['price']} | Commission: {product['commission']}%")
        print(f"🏷️  Platform: {product['platform']}")
        print(f"📅 Launch: {product['launch_date']}")
        
        # Generate permalink
        permalink = slugify(f"{creator}-{product_name}-review")[:100]
        
        # Double-check if review exists locally
        today = datetime.date.today().isoformat()
        post_path = f"{POSTS_DIR}/{today}-{permalink}.md"
        image_file = f"{IMAGES_DIR}/{permalink}.webp"
        
        if os.path.exists(post_path):
            print(f"\n⚠️  Review already exists locally: {post_path}")
            print("⏭️  Skipping to next product...")
            continue
        
        # Check for similar posts with different dates
        existing_posts = [f for f in os.listdir(POSTS_DIR) if permalink in f]
        if existing_posts:
            print(f"\n⚠️  Similar review found: {existing_posts[0]}")
            print("⏭️  Skipping to next product...")
            continue
        
        try:
            # Scrape sales page
            print(f"\n{'='*60}")
            print(f"Step 3: Extracting Product Information")
            print(f"{'='*60}")
            
            sales_data = scrape_sales_page(product['url'])
            
            # Check if we got good data from sales page
            has_sales_data = (
                sales_data and 
                (sales_data.get('features') or sales_data.get('images'))
            )
            
            if not has_sales_data:
                print(f"\n⚠️  Sales page data incomplete or unavailable")
                print(f"🌐 Falling back to web search for product info and images...")
                sales_data = search_product_info(product_name, creator)
            else:
                print(f"✅ Sales page data extracted successfully")
                print(f"   Features: {len(sales_data.get('features', []))}")
                print(f"   Images: {len(sales_data.get('images', []))}")
            
            # Log image availability
            if sales_data.get('images'):
                print(f"\n📸 {len(sales_data['images'])} images available for article")
            else:
                print(f"\n⚠️  No images found - article will be text-only")
            
            # Generate review article
            print(f"\n{'='*60}")
            print(f"Step 4: Generating Review Article")
            print(f"{'='*60}")
            
            affiliate_link = f"https://your-affiliate-link.com/{permalink}"
            
            article_content = generate_review_article(
                product_data=product,
                sales_data=sales_data,
                affiliate_link=affiliate_link
            )
            
            print(f"✅ Article generated ({len(article_content)} characters)")
            
            # Create front matter
            print(f"\n{'='*60}")
            print(f"Step 5: Creating Front Matter")
            print(f"{'='*60}")
            
            front_matter = create_review_front_matter(product, permalink)
            full_article = front_matter + "\n\n" + article_content
            
            # Generate featured image
            print(f"\n{'='*60}")
            print(f"Step 6: Setting Featured Image")
            print(f"{'='*60}")
            
            featured_image_set = False
            
            # Strategy 1: Try sales page images
            if sales_data.get('images') and len(sales_data['images']) > 0:
                print(f"📸 Found {len(sales_data['images'])} images available")
                print(f"🎯 Strategy: Using images from sales page/web search")
                
                featured_image_set = try_download_featured_image(
                    sales_data['images'],
                    image_file
                )
            
            # Strategy 2: If no sales images, search web
            if not featured_image_set:
                print(f"\n⚠️  Could not get image from sales page")
                print(f"🔍 Strategy: Searching web for product images...")
                print(f"📡 Sources: Bing, DuckDuckGo, Product Hunt, Reddit")
                
                from web_image_search import get_product_image_from_web
                
                try:
                    best_image = get_product_image_from_web(product_name, creator)
                    
                    if best_image:
                        featured_image_set = try_download_featured_image(
                            [best_image],
                            image_file
                        )
                except Exception as e:
                    print(f"❌ Web image search failed: {e}")
            
            # Final check
            if featured_image_set:
                print(f"\n✅ Featured image successfully set!")
            else:
                print(f"\n⚠️  No featured image could be set")
                print(f"💡 Post will be published without featured image")
                # Note: Jekyll can handle posts without featured images
            
            # Save post
            print(f"\n{'='*60}")
            print(f"Step 7: Saving Review Post")
            print(f"{'='*60}")
            
            with open(post_path, "w", encoding="utf-8") as f:
                f.write(full_article)
            
            print(f"✅ Review saved: {post_path}")
            
            post_url = f"{SITE_DOMAIN}/{permalink}"
            
            print(f"\n{'='*60}")
            print(f"✅ SUCCESS! Review {i} Generated")
            print(f"{'='*60}")
            print(f"📰 Title: {product_name} Review")
            print(f"🌐 URL: {post_url}")
            
            posts_generated += 1
            
            # Post-generation tasks (only after last post)
            if i == len(products):
                # Wait for GitHub Pages deployment
                print(f"\n{'='*60}")
                print(f"Step 8: Waiting for GitHub Pages Deployment")
                print(f"{'='*60}")
                
                for remaining in range(WAIT_TIME_BEFORE_INDEXING, 0, -30):
                    minutes = remaining // 60
                    seconds = remaining % 60
                    print(f"⏰ Time remaining: {minutes}m {seconds}s", end='\r')
                    time.sleep(30)
                
                print(f"\n✅ Wait complete!")
                
                # Submit to Google (optional)
                indexing_status = submit_to_google_indexing_safe(post_url)
                
                # Log to database
                print(f"\n{'='*60}")
                print(f"Step 9: Logging to Reviews Database")
                print(f"{'='*60}")
                
                try:
                    success = log_published_review(
                        title=f"{product_name} Review",
                        focus_kw=product_name,
                        permalink=permalink,
                        image_path=image_file,
                        article_content=article_content,
                        indexing_status=indexing_status
                    )
                    
                    if not success:
                        print(f"⚠️  Database logging had issues, but continuing...")
                        
                except Exception as e:
                    print(f"⚠️  Database logging failed: {e}")
                    print(f"💡 This is non-critical, continuing...")
                    import traceback
                    traceback.print_exc()
                
                # Send push notification (optional)
                try:
                    send_push_notification_safe(
                        title=f"{product_name} Review",
                        permalink=permalink,
                        focus_kw=product_name
                    )
                except Exception as e:
                    print(f"⚠️  Push notification failed: {e}")
            
        except Exception as e:
            print(f"\n{'='*60}")
            print(f"❌ FAILED: {e}")
            print(f"{'='*60}")
            import traceback
            traceback.print_exc()
            continue
    
    # Final summary
    print(f"\n{'='*60}")
    print(f"🎉 REVIEW GENERATION COMPLETE")
    print(f"{'='*60}")
    print(f"✅ Reviews generated: {posts_generated}")
    print(f"📊 Products processed: {len(products)}")


if __name__ == "__main__":
    main()