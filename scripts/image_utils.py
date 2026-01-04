"""Image utilities for downloading and processing images"""
import os
import requests
from PIL import Image
from io import BytesIO
from config import IMAGE_QUALITY, IMAGE_MAX_WIDTH, IMAGE_MAX_HEIGHT


def download_and_save_image(image_url, output_path, min_width=400, min_height=300):
    """
    Download image from URL and save as optimized WEBP
    
    Args:
        image_url: URL of the image
        output_path: Where to save the image
        min_width: Minimum acceptable width
        min_height: Minimum acceptable height
    
    Returns:
        bool: Success status
    """
    try:
        print(f"📥 Downloading: {image_url[:80]}...")
        
        headers = {
            'User-Agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36'
        }
        
        response = requests.get(image_url, headers=headers, timeout=30, stream=True)
        response.raise_for_status()
        
        # Check content type
        content_type = response.headers.get('content-type', '')
        if 'image' not in content_type.lower():
            print(f"⚠️  Not an image: {content_type}")
            return False
        
        # Load image
        img = Image.open(BytesIO(response.content))
        
        # Convert to RGB if needed
        if img.mode in ('RGBA', 'LA', 'P'):
            # Create white background
            background = Image.new('RGB', img.size, (255, 255, 255))
            if img.mode == 'P':
                img = img.convert('RGBA')
            background.paste(img, mask=img.split()[-1] if img.mode == 'RGBA' else None)
            img = background
        elif img.mode != 'RGB':
            img = img.convert('RGB')
        
        # Check dimensions
        width, height = img.size
        print(f"📐 Original size: {width}x{height}")
        
        if width < min_width or height < min_height:
            print(f"⚠️  Image too small ({width}x{height}), skipping")
            return False
        
        # Resize if too large (maintain aspect ratio)
        if width > IMAGE_MAX_WIDTH or height > IMAGE_MAX_HEIGHT:
            print(f"🔧 Resizing to fit {IMAGE_MAX_WIDTH}x{IMAGE_MAX_HEIGHT}...")
            img.thumbnail((IMAGE_MAX_WIDTH, IMAGE_MAX_HEIGHT), Image.Resampling.LANCZOS)
            new_width, new_height = img.size
            print(f"✅ Resized to: {new_width}x{new_height}")
        
        # Save as optimized WEBP
        img.save(
            output_path,
            "WEBP",
            quality=IMAGE_QUALITY,
            method=6,
            optimize=True
        )
        
        # Get file size
        file_size = os.path.getsize(output_path)
        print(f"💾 Saved: {output_path} ({file_size / 1024:.1f} KB)")
        
        return True
        
    except requests.exceptions.RequestException as e:
        print(f"❌ Download failed: {e}")
        return False
    except Exception as e:
        print(f"❌ Image processing failed: {e}")
        return False


def try_download_featured_image(images_list, output_path):
    """
    Try to download featured image from a list of candidates
    
    Args:
        images_list: List of image dicts with 'url' and 'alt' keys
        output_path: Where to save the featured image
    
    Returns:
        bool: Success status
    """
    if not images_list:
        print("⚠️  No images available")
        return False
    
    print(f"\n{'='*60}")
    print(f"🎯 Attempting to download featured image")
    print(f"📊 {len(images_list)} candidate images available")
    print(f"{'='*60}")
    
    for idx, img in enumerate(images_list[:5], 1):  # Try first 5 images
        print(f"\n🔄 Attempt {idx}/{min(5, len(images_list))}")
        print(f"   Alt: {img.get('alt', 'No alt text')[:60]}")
        
        if download_and_save_image(img['url'], output_path):
            print(f"✅ Successfully downloaded featured image!")
            return True
        else:
            print(f"⏭️  Trying next image...")
    
    print(f"\n❌ Failed to download any images from sales page")
    return False


def validate_image_file(image_path):
    """
    Check if image file exists and is valid
    
    Args:
        image_path: Path to image file
    
    Returns:
        bool: True if valid
    """
    if not os.path.exists(image_path):
        return False
    
    try:
        img = Image.open(image_path)
        img.verify()
        return True
    except Exception:
        return False


def create_placeholder_image(output_path, text="Product Image"):
    """
    Create a simple placeholder image
    
    Args:
        output_path: Where to save the placeholder
        text: Text to display on placeholder
    
    Returns:
        bool: Success status
    """
    try:
        from PIL import ImageDraw, ImageFont
        
        # Create image
        width, height = 1200, 630
        img = Image.new('RGB', (width, height), color=(52, 152, 219))
        
        draw = ImageDraw.Draw(img)
        
        # Draw text
        try:
            font = ImageFont.truetype("/usr/share/fonts/truetype/dejavu/DejaVuSans-Bold.ttf", 60)
        except:
            font = ImageFont.load_default()
        
        # Center text
        text_bbox = draw.textbbox((0, 0), text, font=font)
        text_width = text_bbox[2] - text_bbox[0]
        text_height = text_bbox[3] - text_bbox[1]
        
        x = (width - text_width) // 2
        y = (height - text_height) // 2
        
        draw.text((x, y), text, fill=(255, 255, 255), font=font)
        
        # Save
        img.save(output_path, "WEBP", quality=85)
        print(f"✅ Created placeholder image: {output_path}")
        return True
        
    except Exception as e:
        print(f"❌ Failed to create placeholder: {e}")
        return False