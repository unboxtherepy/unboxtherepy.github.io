"""Send push notifications via Webpushr"""
import os
import requests
from config import SITE_DOMAIN, TEXT_MODEL, GEMINI_API_KEY
from google import genai

# Webpushr API credentials from environment
WEBPUSHR_API_KEY = os.environ.get("WEBPUSHR_API_KEY")
WEBPUSHR_AUTH_TOKEN = os.environ.get("WEBPUSHR_AUTH_TOKEN")

# Initialize Gemini client for description generation
client = genai.Client(api_key=GEMINI_API_KEY) if GEMINI_API_KEY else None


def generate_description(title, focus_kw):
    """Generate SEO-optimized meta description (150-160 characters)"""
    if not client:
        # Fallback if Gemini not available
        return f"Read our honest review of {focus_kw}. Features, pricing, pros & cons analysis."
    
    prompt = f"""
Generate a compelling meta description for this product review.

Title: {title}
Focus Keyword: {focus_kw}

Requirements:
- EXACTLY 150-160 characters (this is critical)
- Include the focus keyword naturally
- Action-oriented and engaging
- Make readers want to click
- No quotes or special characters
- Complete sentence

Return ONLY the description text, nothing else.
"""
    
    try:
        response = client.models.generate_content(
            model=TEXT_MODEL,
            contents=prompt
        )
        
        description = response.text.strip()
        
        # Ensure it's under 160 characters
        if len(description) > 160:
            description = description[:157] + "..."
        
        return description
    except Exception as e:
        print(f"⚠️ Error generating description: {e}")
        # Fallback description
        return f"Comprehensive review of {focus_kw}. Read our honest analysis, features, pricing & pros/cons before buying."


def send_webpushr_notification(title, message, target_url, image_url=None):
    """
    Send push notification via Webpushr
    
    Args:
        title: Notification title
        message: Notification message
        target_url: URL to open when clicked
        image_url: Optional large image URL
    
    Returns:
        bool: Success status
    """
    
    if not WEBPUSHR_API_KEY:
        print("⚠️ WEBPUSHR_API_KEY not found - skipping notification")
        return False
    
    if not WEBPUSHR_AUTH_TOKEN:
        print("⚠️ WEBPUSHR_AUTH_TOKEN not found - skipping notification")
        return False
    
    try:
        print(f"🔔 Sending Webpushr notification...")
        
        # Webpushr API endpoint
        api_url = "https://api.webpushr.com/v1/notification/send/all"
        
        # Prepare headers
        headers = {
            "webpushrKey": WEBPUSHR_API_KEY,
            "webpushrAuthToken": WEBPUSHR_AUTH_TOKEN,
            "Content-Type": "application/json"
        }
        
        # Prepare notification data
        payload = {
            "title": title,
            "message": message,
            "target_url": target_url,
            "icon": f"{SITE_DOMAIN}/assets/images/site-logo.webp",  # Your site logo
            "auto_hide": 1  # Auto hide after shown
        }
        
        # Add large image if provided
        if image_url:
            payload["image"] = image_url
        
        # Send notification
        response = requests.post(api_url, headers=headers, json=payload, timeout=30)
        
        if response.status_code == 200:
            result = response.json()
            print(f"✅ Notification sent successfully!")
            print(f"📊 Queue ID: {result.get('qid', 'N/A')}")
            return True
        else:
            print(f"❌ Failed to send notification: {response.status_code}")
            print(f"Response: {response.text}")
            return False
        
    except Exception as e:
        print(f"❌ Error sending Webpushr notification: {e}")
        return False


def send_blog_post_notification(title, permalink, focus_kw):
    """
    Send notification for new blog post/review
    
    Args:
        title: Blog post title
        permalink: Post permalink
        focus_kw: Focus keyword for categorization
    
    Returns:
        bool: Success status
    """
    
    # Construct full URL
    post_url = f"{SITE_DOMAIN}/{permalink}"
    
    # Construct image URL (remove leading slash from permalink if present)
    clean_permalink = permalink.strip('/').split('/')[-1]
    image_url = f"{SITE_DOMAIN}/assets/images/{clean_permalink}.webp"
    
    # Generate description
    try:
        description = generate_description(title, focus_kw)
    except Exception as e:
        print(f"⚠️ Error generating description: {e}")
        description = f"New review: {title[:100]}"
    
    # Create notification message (truncate title if too long)
    notification_title = title[:80] if len(title) > 80 else title
    notification_message = description
    
    # Send notification
    return send_webpushr_notification(
        title=notification_title,
        message=notification_message,
        target_url=post_url,
        image_url=image_url
    )


def send_review_notification(product_name, creator, permalink):
    """
    Send notification specifically for product reviews
    
    Args:
        product_name: Name of the product
        creator: Creator/vendor name
        permalink: Post permalink
    
    Returns:
        bool: Success status
    """
    
    # Construct URLs
    post_url = f"{SITE_DOMAIN}/{permalink}"
    clean_permalink = permalink.strip('/').split('/')[-1]
    image_url = f"{SITE_DOMAIN}/assets/images/{clean_permalink}.webp"
    
    # Create engaging notification
    notification_title = f"New Review: {product_name}"
    notification_message = f"Check out our honest review of {product_name} by {creator}. Features, pricing & verdict!"
    
    # Send notification
    return send_webpushr_notification(
        title=notification_title,
        message=notification_message,
        target_url=post_url,
        image_url=image_url
    )


def send_segmented_notification(title, message, target_url, segment_id=None):
    """
    Send notification to specific segment
    
    Args:
        title: Notification title
        message: Notification message
        target_url: URL to open when clicked
        segment_id: Webpushr segment ID (optional)
    
    Returns:
        bool: Success status
    """
    
    if not WEBPUSHR_API_KEY or not WEBPUSHR_AUTH_TOKEN:
        print("⚠️ Webpushr credentials not found")
        return False
    
    try:
        # Different endpoint for segmented notifications
        if segment_id:
            api_url = f"https://api.webpushr.com/v1/notification/send/sid/{segment_id}"
        else:
            api_url = "https://api.webpushr.com/v1/notification/send/all"
        
        headers = {
            "webpushrKey": WEBPUSHR_API_KEY,
            "webpushrAuthToken": WEBPUSHR_AUTH_TOKEN,
            "Content-Type": "application/json"
        }
        
        payload = {
            "title": title,
            "message": message,
            "target_url": target_url,
            "icon": f"{SITE_DOMAIN}/assets/images/site-logo.webp"
        }
        
        response = requests.post(api_url, headers=headers, json=payload, timeout=30)
        
        if response.status_code == 200:
            print(f"✅ Segmented notification sent!")
            return True
        else:
            print(f"❌ Failed: {response.status_code} - {response.text}")
            return False
            
    except Exception as e:
        print(f"❌ Error: {e}")
        return False


def send_category_notification(product_name, category, permalink):
    """
    Send notification with category information
    
    Args:
        product_name: Name of the product
        category: Product category
        permalink: Post permalink
    
    Returns:
        bool: Success status
    """
    
    post_url = f"{SITE_DOMAIN}/{permalink}"
    clean_permalink = permalink.strip('/').split('/')[-1]
    image_url = f"{SITE_DOMAIN}/assets/images/{clean_permalink}.webp"
    
    # Category-specific messages
    category_messages = {
        'ai': '🤖 AI-powered tool review!',
        'video': '🎥 Video creation tool review!',
        'social_media': '📱 Social media tool review!',
        'seo': '📈 SEO tool review!',
        'email': '📧 Email marketing tool review!',
        'ecommerce': '🛒 eCommerce tool review!',
        'marketing': '📊 Marketing tool review!',
        'graphics': '🎨 Design tool review!',
    }
    
    category_lower = category.lower().replace(' ', '_')
    prefix = category_messages.get(category_lower, '✨ New tool review!')
    
    notification_title = f"{prefix} {product_name}"
    notification_message = f"In-depth review of {product_name}. Features, pricing, pros & cons analysis."
    
    return send_webpushr_notification(
        title=notification_title,
        message=notification_message,
        target_url=post_url,
        image_url=image_url
    )


def send_action_button_notification(title, message, target_url, button_title="Read Review", button_url=None):
    """
    Send notification with action buttons
    
    Args:
        title: Notification title
        message: Notification message
        target_url: Default URL to open
        button_title: Action button text (default: "Read Review")
        button_url: URL for action button (optional)
    
    Returns:
        bool: Success status
    """
    
    if not WEBPUSHR_API_KEY or not WEBPUSHR_AUTH_TOKEN:
        print("⚠️ Webpushr credentials not found")
        return False
    
    try:
        api_url = "https://api.webpushr.com/v1/notification/send/all"
        
        headers = {
            "webpushrKey": WEBPUSHR_API_KEY,
            "webpushrAuthToken": WEBPUSHR_AUTH_TOKEN,
            "Content-Type": "application/json"
        }
        
        payload = {
            "title": title,
            "message": message,
            "target_url": target_url,
            "icon": f"{SITE_DOMAIN}/assets/images/site-logo.webp",
            "action_buttons": [
                {
                    "title": button_title,
                    "url": button_url or target_url,
                    "icon": ""
                }
            ]
        }
        
        response = requests.post(api_url, headers=headers, json=payload, timeout=30)
        
        if response.status_code == 200:
            print(f"✅ Action button notification sent!")
            return True
        else:
            print(f"❌ Failed: {response.status_code}")
            return False
            
    except Exception as e:
        print(f"❌ Error: {e}")
        return False


def get_subscriber_count():
    """Get total subscriber count from Webpushr"""
    
    if not WEBPUSHR_API_KEY or not WEBPUSHR_AUTH_TOKEN:
        return None
    
    try:
        api_url = "https://api.webpushr.com/v1/subscribers/count"
        
        headers = {
            "webpushrKey": WEBPUSHR_API_KEY,
            "webpushrAuthToken": WEBPUSHR_AUTH_TOKEN
        }
        
        response = requests.get(api_url, headers=headers, timeout=30)
        
        if response.status_code == 200:
            data = response.json()
            count = data.get("count", 0)
            print(f"📊 Total subscribers: {count}")
            return count
        else:
            return None
            
    except Exception as e:
        print(f"❌ Error getting subscriber count: {e}")
        return None


def send_batch_notifications(reviews):
    """
    Send notifications for multiple reviews (batch processing)
    
    Args:
        reviews: List of dicts with {product_name, creator, permalink}
    
    Returns:
        dict: Success count and failed count
    """
    
    if not reviews:
        return {'success': 0, 'failed': 0}
    
    print(f"\n{'='*60}")
    print(f"📢 Sending Batch Notifications for {len(reviews)} Reviews")
    print(f"{'='*60}")
    
    success_count = 0
    failed_count = 0
    
    for i, review in enumerate(reviews, 1):
        print(f"\n📤 Notification {i}/{len(reviews)}")
        
        try:
            result = send_review_notification(
                product_name=review['product_name'],
                creator=review['creator'],
                permalink=review['permalink']
            )
            
            if result:
                success_count += 1
            else:
                failed_count += 1
                
        except Exception as e:
            print(f"❌ Error sending notification for {review['product_name']}: {e}")
            failed_count += 1
    
    print(f"\n{'='*60}")
    print(f"📊 Batch Notification Results")
    print(f"{'='*60}")
    print(f"✅ Successful: {success_count}")
    print(f"❌ Failed: {failed_count}")
    
    return {'success': success_count, 'failed': failed_count}


if __name__ == "__main__":
    # Test notifications
    print("Testing Webpushr notifications...")
    
    # Test subscriber count
    count = get_subscriber_count()
    
    # Test simple notification
    if WEBPUSHR_API_KEY and WEBPUSHR_AUTH_TOKEN:
        test_result = send_blog_post_notification(
            title="Test Product Review",
            permalink="test-product-review",
            focus_kw="test product"
        )
        print(f"\nTest notification result: {'✅ Success' if test_result else '❌ Failed'}")