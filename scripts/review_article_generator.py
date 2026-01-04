"""Generate comprehensive product review articles"""
from google import genai
from config import TEXT_MODEL, GEMINI_API_KEY
import re
import json

client = genai.Client(api_key=GEMINI_API_KEY)


def generate_review_article(product_data, sales_data, affiliate_link="[AFFILIATE_LINK_HERE]"):
    """
    Generate comprehensive product review article with embedded images
    
    Args:
        product_data: Dict from muncheye_scraper
        sales_data: Dict from sales_page_scraper
        affiliate_link: Affiliate URL
    
    Returns:
        Complete article in Jekyll format
    """
    
    product_name = product_data['name']
    creator = product_data['creator']
    price = product_data['price']
    commission = product_data['commission']
    platform = product_data['platform']
    launch_date = product_data['launch_date']
    
    features = sales_data.get('features', [])
    description = sales_data.get('description', '')
    benefits = sales_data.get('benefits', [])
    pricing_info = sales_data.get('pricing', [])
    bonuses = sales_data.get('bonuses', [])
    guarantee = sales_data.get('guarantee', '')
    images = sales_data.get('images', [])
    
    # Prepare image information for Gemini
    image_list = []
    for idx, img in enumerate(images[:10], 1):  # Limit to 10 images
        image_list.append({
            'id': f'image_{idx}',
            'url': img['url'],
            'alt': img.get('alt', f'{product_name} screenshot {idx}'),
            'markdown': f'![{img.get("alt", product_name)}]({img["url"]})'
        })
    
    prompt = f"""
Write a comprehensive, unbiased product review for: {product_name} by {creator}

PRODUCT INFORMATION:
- Name: {product_name}
- Creator: {creator}
- Price: ${price}
- Platform: {platform}
- Launch Date: {launch_date}
- Description: {description}

FEATURES:
{json.dumps(features, indent=2)}

BENEFITS:
{json.dumps(benefits, indent=2)}

BONUSES:
{json.dumps(bonuses, indent=2)}

GUARANTEE:
{guarantee}

AVAILABLE IMAGES FROM SALES PAGE:
{json.dumps(image_list, indent=2)}

AFFILIATE LINK PLACEHOLDER: {affiliate_link}

ARTICLE REQUIREMENTS:

## Image Usage Instructions:
- You have {len(image_list)} images available from the product sales page
- Use these images strategically throughout the article
- Place images where they best illustrate the content
- Insert images using markdown: ![alt text](image_url)
- Use at least 3-5 images if available
- Good places for images:
  * After the introduction (overview screenshot)
  * In the "Key Features" section (feature screenshots)
  * In the "How Does It Work" section (workflow/process images)
  * In the "Pricing" section (pricing table screenshot)
  * In the "Interface/Dashboard" section
- Add descriptive alt text for each image
- Center images using HTML if needed: <p align="center"><img src="url" alt="description"></p>

## Structure:
1. **Introduction** (2-3 paragraphs)
   - Hook with the problem this product solves
   - Brief overview of what the product is
   - Who it's for
   - [INSERT RELEVANT IMAGE HERE - product overview/hero image]

2. **What is {product_name}?** (H2)
   - Detailed explanation
   - Main purpose and functionality
   - Target audience
   - [INSERT DASHBOARD/INTERFACE IMAGE IF AVAILABLE]

3. **Key Features** (H2)
   - List 5-10 main features with explanations
   - Use H3 subheadings for each major feature
   - [INSERT FEATURE SCREENSHOTS BETWEEN FEATURES]
   - Include practical use cases

4. **How Does It Work?** (H2)
   - Step-by-step process
   - User experience overview
   - [INSERT WORKFLOW/PROCESS IMAGES]

5. **Benefits of Using {product_name}** (H2)
   - Concrete benefits
   - Real-world applications
   - Time/money savings

6. **Pricing & Packages** (H2)
   - Price breakdown (${price})
   - Value analysis
   - [INSERT PRICING TABLE IMAGE IF AVAILABLE]
   - Money-back guarantee details
   - Include affiliate link with call-to-action

7. **Pros and Cons** (H2)
   - Honest pros (5-7 points)
   - Honest cons (3-5 points)
   - Use tables for comparison

8. **Who Should Buy {product_name}?** (H2)
   - Ideal customers
   - Who will benefit most
   - Who shouldn't buy (be honest)

9. **Bonuses & Special Offers** (H2)
   - List bonus items
   - [INSERT BONUS IMAGES IF AVAILABLE]
   - Limited-time offers
   - Exclusive deals

10. **{product_name} vs Competitors** (H2)
    - Comparison with 2-3 similar products
    - Unique selling points
    - Comparison table

11. **Frequently Asked Questions** (H2)
    - 8-10 relevant questions with answers
    - Use H3 for each question

12. **Final Verdict** (H2)
    - Overall assessment
    - Rating (X/10)
    - Final recommendation
    - Call-to-action with affiliate link

## WRITING STYLE:
- Write for a 10-year-old's reading level
- Use "you" to address readers
- Max 3 sentences per paragraph
- Conversational but professional tone
- Include specific examples
- Be honest about limitations
- Use bullet points and lists where appropriate
- Include comparison tables
- Add "Quick Summary" boxes

## SEO OPTIMIZATION:
- Naturally include product name throughout
- Use semantic keywords: software review, {creator} product, {platform} launch, digital marketing tools
- Include LSI keywords: features, benefits, pricing, honest review, worth it
- Meta-friendly structure

## SPECIAL ELEMENTS:
- Add a "Quick Verdict" box at the top after intro
- Include pricing calculator if relevant
- Add affiliate link in 3-4 strategic places with clear disclosure
- Use comparison tables
- Add "Key Takeaways" box before conclusion

## AFFILIATE LINK USAGE:
Place affiliate links in these sections:
1. After introduction with "Check Latest Price" button
2. In pricing section
3. Before pros/cons
4. In final verdict

Format: <a href="{affiliate_link}" target="_blank" rel="nofollow">Get {product_name} Now</a>

## IMPORTANT:
- Article must be 2500+ words
- Write in Jekyll format (NO front matter, that's added separately)
- Use H2, H3, H4 headings (NO H1)
- Be balanced - include genuine cons
- Include affiliate disclosure: "This review contains affiliate links, meaning we may earn a commission if you make a purchase through our links at no extra cost to you."
- Add comparison tables in markdown format
- Include FAQ schema-friendly format
- STRATEGICALLY EMBED THE AVAILABLE IMAGES THROUGHOUT THE ARTICLE

Write the complete article now with images embedded:
"""
    
    print("🤖 Generating comprehensive review article with embedded images...")
    response = client.models.generate_content(
        model=TEXT_MODEL,
        contents=prompt
    )
    
    content = remove_front_matter(response.text)
    
    print(f"✅ Article generated ({len(content)} characters)")
    
    # Count embedded images
    image_count = len(re.findall(r'!\[.*?\]\(.*?\)', content))
    print(f"📸 Embedded {image_count} images in the article")
    
    return content


def create_review_front_matter(product_data, permalink):
    """Create Jekyll front matter for review article"""
    
    product_name = product_data['name']
    creator = product_data['creator']
    
    title = f"{product_name} Review {product_data['launch_date'][:4]} - Honest Analysis by Real Users"
    
    description = generate_review_description(product_name, creator, product_data['price'])
    
    category = determine_category(product_name)
    
    escaped_title = title.replace('"', '\\"')
    escaped_desc = description.replace('"', '\\"')
    
    front_matter = f"""---
title: "{escaped_title}"
description: "{escaped_desc}"
author_profile: false
read_time: true
comments: true
share: true
related: true
toc: true 
toc_sticky: true 
toc_icon: "list-ul"
tags: [{category}, Software Review, {creator}]
categories: [Product Reviews]
featured: true
image: '/images/{permalink}.webp'
rating: 0
product_name: "{product_name}"
creator: "{creator}"
price: "${product_data['price']}"
launch_date: "{product_data['launch_date']}"
affiliate_disclosure: true
---"""
    
    return front_matter


def generate_review_description(product_name, creator, price):
    """Generate SEO meta description for review"""
    
    prompt = f"""
Generate a compelling meta description for this product review.

Product: {product_name}
Creator: {creator}
Price: ${price}

Requirements:
- EXACTLY 150-160 characters
- Include product name and "review"
- Mention honest, unbiased analysis
- Include key benefit or feature
- Make it click-worthy
- No quotes or special characters

Return ONLY the description text.
"""
    
    response = client.models.generate_content(
        model=TEXT_MODEL,
        contents=prompt
    )
    
    description = response.text.strip()
    
    if len(description) > 160:
        description = description[:157] + "..."
    
    return description


def generate_image_prompt(title):
    """Generate image prompt for Freepik AI"""
    prompt = f"""
Create a photorealistic featured image prompt for this blog post:
Title: {title}

Requirements:
- Professional, high-quality
- NO text or words in the image
- Suitable as a blog featured image
- 16:9 aspect ratio
- Relevant to the topic

Return ONLY the image prompt, nothing else.
"""
    
    print("🎨 Generating image prompt...")
    response = client.models.generate_content(
        model=TEXT_MODEL,
        contents=prompt
    )
    return response.text.strip()


def determine_category(product_name):
    """Determine product category from name"""
    
    name_lower = product_name.lower()
    
    categories = {
        'ai': ['ai', 'artificial intelligence', 'chatgpt', 'gpt', 'machine learning'],
        'video': ['video', 'youtube', 'reel', 'tiktok', 'shorts'],
        'social': ['social', 'instagram', 'facebook', 'twitter', 'linkedin'],
        'seo': ['seo', 'rank', 'traffic', 'search engine'],
        'email': ['email', 'autoresponder', 'newsletter', 'mail'],
        'ecommerce': ['ecommerce', 'shopify', 'amazon', 'store', 'shop'],
        'website': ['website', 'site', 'builder', 'wordpress', 'hosting'],
        'marketing': ['marketing', 'funnel', 'sales', 'conversion'],
        'content': ['content', 'writing', 'article', 'blog'],
        'graphics': ['graphic', 'design', 'image', 'logo', 'banner']
    }
    
    for category, keywords in categories.items():
        if any(keyword in name_lower for keyword in keywords):
            return category.title()
    
    return 'Software Review'


def remove_front_matter(content):
    """Remove any front matter from AI-generated content"""
    content = re.sub(r'^---\s*\n.*?\n---\s*\n', '', content, flags=re.DOTALL)
    
    lines = content.split('\n')
    clean_lines = []
    skip_yaml = True
    
    for line in lines:
        if line.strip().startswith('#') or (line.strip() and ':' not in line):
            skip_yaml = False
        
        if not skip_yaml:
            clean_lines.append(line)
        elif skip_yaml and line.strip() and ':' not in line:
            skip_yaml = False
            clean_lines.append(line)
    
    return '\n'.join(clean_lines).strip()