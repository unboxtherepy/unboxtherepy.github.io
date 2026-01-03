"""Configuration settings for the review blog generator"""
import os

# File paths
POSTS_DIR = "_posts"
IMAGES_DIR = "images"

# Google Sheets
SHEETS_RANGE = "Sheet1!A:I"  # Range to check for existing reviews

# Site settings
SITE_DOMAIN = "https://unboxtherapy.github.io"

# AI Models
TEXT_MODEL = "gemini-2.5-flash"
FREEPIK_ENDPOINT = "https://api.freepik.com/v1/ai/text-to-image/flux-dev"

# Generation settings
POSTS_PER_RUN = 1  # How many product reviews to generate per run

# Image settings
IMAGE_QUALITY = 80  # 1-100
IMAGE_MAX_WIDTH = 1920
IMAGE_MAX_HEIGHT = 1080
OPTIMIZE_IMAGE = True

# Timing
WAIT_TIME_BEFORE_INDEXING = 180  # seconds (3 minutes)

# MunchEye Settings
MUNCHEYE_SECTIONS = ['just_launched', 'big_launches']  # Which sections to scrape
REVIEW_RECENT_DAYS = 14  # Review products launched within X days

# API Keys (from environment)
GEMINI_API_KEY = os.environ.get("GEMINI_API_KEY")
FREEPIK_API_KEY = os.environ.get("FREEPIK_API_KEY")
GOOGLE_SERVICE_ACCOUNT_JSON = os.environ.get("GOOGLE_SERVICE_ACCOUNT_JSON")
GOOGLE_SPREADSHEET_ID = os.environ.get("GOOGLE_SPREADSHEET_ID")

# Social media (optional)
TWITTER_API_KEY = os.environ.get("TWITTER_API_KEY")
TWITTER_API_SECRET = os.environ.get("TWITTER_API_SECRET")
TWITTER_ACCESS_TOKEN = os.environ.get("TWITTER_ACCESS_TOKEN")
TWITTER_ACCESS_TOKEN_SECRET = os.environ.get("TWITTER_ACCESS_TOKEN_SECRET")
TWITTER_BEARER_TOKEN = os.environ.get("TWITTER_BEARER_TOKEN")

LINKEDIN_ACCESS_TOKEN = os.environ.get("LINKEDIN_ACCESS_TOKEN")
LINKEDIN_PERSON_ID = os.environ.get("LINKEDIN_PERSON_ID")

WEBPUSHR_API_KEY = os.environ.get("WEBPUSHR_API_KEY")
WEBPUSHR_AUTH_TOKEN = os.environ.get("WEBPUSHR_AUTH_TOKEN")

# Create directories
os.makedirs(POSTS_DIR, exist_ok=True)
os.makedirs(IMAGES_DIR, exist_ok=True)