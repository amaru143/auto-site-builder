import os
from pathlib import Path
from dotenv import load_dotenv

# Load environment variables
load_dotenv(Path(__file__).parent.parent / '.env')

# Paths
BASE_DIR = Path(__file__).parent.parent
LEADS_DIR = BASE_DIR / 'leads'
ANALYSIS_DIR = BASE_DIR / 'analysis'
OFFERS_DIR = BASE_DIR / 'offers'
GENERATED_SITES_DIR = BASE_DIR / 'generated-sites'
OUTREACH_DIR = BASE_DIR / 'outreach'
DASHBOARD_DIR = BASE_DIR / 'dashboard'
TEMPLATES_DIR = BASE_DIR / 'site-generator' / 'templates'

# Ensure directories exist
for d in [LEADS_DIR, ANALYSIS_DIR, OFFERS_DIR, GENERATED_SITES_DIR, OUTREACH_DIR, DASHBOARD_DIR, TEMPLATES_DIR]:
    d.mkdir(parents=True, exist_ok=True)

# API Keys
GOOGLE_PLACES_API_KEY = os.getenv('GOOGLE_PLACES_API_KEY', '')
ANTHROPIC_API_KEY = os.getenv('ANTHROPIC_API_KEY', '')
STRIPE_SECRET_KEY = os.getenv('STRIPE_SECRET_KEY', '')
STRIPE_PUBLISHABLE_KEY = os.getenv('STRIPE_PUBLISHABLE_KEY', '')
STRIPE_WEBHOOK_SECRET = os.getenv('STRIPE_WEBHOOK_SECRET', '')

# Gmail
GMAIL_ADDRESS = os.getenv('GMAIL_ADDRESS', '')
GMAIL_APP_PASSWORD = os.getenv('GMAIL_APP_PASSWORD', '')

# Business
YOUR_BUSINESS_NAME = os.getenv('YOUR_BUSINESS_NAME', 'WebLift')
YOUR_WEBSITE = os.getenv('YOUR_WEBSITE', 'https://yourdomain.com')
YOUR_PHONE = os.getenv('YOUR_PHONE', '')
YOUR_EMAIL = os.getenv('YOUR_EMAIL', '')
PRICE = int(os.getenv('PRICE', '500'))

# Server
PAYMENT_SERVER_PORT = int(os.getenv('PAYMENT_SERVER_PORT', '5000'))
PAYMENT_SERVER_URL = os.getenv('PAYMENT_SERVER_URL', 'http://localhost:5000')

# Supported business types
BUSINESS_TYPES = [
    'plumbing', 'roofing', 'landscaping', 'cleaning',
    'barbershop', 'auto_detailing', 'restaurant', 'dental',
    'hvac', 'electrical', 'painting', 'moving',
    'pest_control', 'flooring', 'general_contractor'
]

# Search settings
DEFAULT_SEARCH_RADIUS = 50000  # meters (50km)
MAX_RESULTS_PER_SEARCH = 60
