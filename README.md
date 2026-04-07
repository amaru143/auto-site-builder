# Auto Site Builder

Automated pipeline that finds local businesses with weak or missing websites, builds them a professional replacement, and sends a personalized sales pitch with a preview link and Stripe payment flow.

**Find leads > Analyze their sites > Generate better ones > Send outreach > Collect payment**

---

## Quick Start

```bash
# 1. Install dependencies
pip install -r requirements.txt

# 2. Copy the example env and fill in your keys (see Setup below)
cp .env.example .env

# 3. Run the demo (no API keys needed)
python run.py --demo

# 4. View the dashboard
python run.py --server
# Open http://localhost:5000/dashboard
```

---

## Setup

### API Keys

Create a `.env` file in the project root with the following:

```env
# Google Places (required for lead discovery)
GOOGLE_PLACES_API_KEY=your_key_here

# Stripe (required for payment collection)
STRIPE_SECRET_KEY=sk_test_...
STRIPE_PUBLISHABLE_KEY=pk_test_...
STRIPE_WEBHOOK_SECRET=whsec_...

# Gmail SMTP (required for sending outreach)
GMAIL_ADDRESS=you@gmail.com
GMAIL_APP_PASSWORD=xxxx xxxx xxxx xxxx

# Your business info (shown in outreach emails and generated sites)
YOUR_BUSINESS_NAME=WebLift
YOUR_WEBSITE=https://yourdomain.com
YOUR_PHONE=555-123-4567
YOUR_EMAIL=you@yourdomain.com
PRICE=500
```

### How to Get Each Key

| Key | Where |
|-----|-------|
| **Google Places API** | [console.cloud.google.com](https://console.cloud.google.com) > Enable "Places API" > Credentials > Create API Key |
| **Stripe** | [dashboard.stripe.com](https://dashboard.stripe.com) > Developers > API Keys (use test keys first) |
| **Gmail App Password** | [myaccount.google.com](https://myaccount.google.com) > Security > 2-Step Verification > App Passwords > generate one for "Mail" |

---

## Commands

| Command | What It Does |
|---------|--------------|
| `python run.py --demo` | Run the full pipeline with mock data (no API keys needed) |
| `python run.py --full --cities Austin --states TX` | Run the entire pipeline for real |
| `python run.py --discover --cities "Dallas" --states "TX" --categories plumbing roofing` | Find leads only |
| `python run.py --analyze` | Score websites of discovered leads |
| `python run.py --generate` | Build replacement sites for analyzed leads |
| `python run.py --offers` | Generate improvement offer documents |
| `python run.py --outreach` | Create email/SMS drafts |
| `python run.py --send --dry-run` | Preview outreach emails without sending |
| `python run.py --send` | Send outreach emails (asks for confirmation) |
| `python run.py --server` | Start the dashboard and payment server at `localhost:5000` |
| `python run.py --summary` | Print a summary of all pipeline data |

### Additional Options

```
--categories    Business types to target (default: all supported types)
--cities        Cities to search (default: Austin)
--states        States to search (default: TX)
--email-type    short_pitch | detailed_pitch | follow_up
--dry-run       Preview emails without actually sending
```

---

## How the Pipeline Works

```
1. DISCOVER  ──>  Google Places API finds local businesses
                  Saves leads to leads/

2. ANALYZE   ──>  Visits each business website (or flags missing ones)
                  Scores quality (mobile, speed, SEO, design)
                  Saves reports to analysis/

3. GENERATE  ──>  Builds a modern replacement site for each lead
                  Uses Jinja2 templates tailored to business type
                  Outputs to generated-sites/<business-name>/

4. OFFERS    ──>  Creates a markdown improvement proposal per lead
                  Saves to offers/

5. OUTREACH  ──>  Drafts personalized emails with preview links
                  Saves to outreach/

6. SEND      ──>  Sends emails via Gmail SMTP
                  Includes link to preview site + Stripe checkout

7. SERVER    ──>  Flask app serves the dashboard, site previews,
                  and handles Stripe payment webhooks
```

---

## Project Structure

```
auto-site-builder/
├── run.py                    # Main orchestrator (all commands route through here)
├── requirements.txt          # Python dependencies
├── .env                      # API keys (not committed)
├── config/
│   ├── __init__.py
│   └── settings.py           # Central configuration and paths
├── scripts/
│   ├── lead_discovery.py     # Google Places API lead finder
│   ├── website_analyzer.py   # Website quality scorer
│   ├── site_generator.py     # Website generation engine
│   ├── offer_generator.py    # Improvement offer creator
│   ├── outreach_generator.py # Email/SMS draft creator
│   ├── email_sender.py       # Gmail SMTP sender
│   └── payment_server.py     # Flask server (dashboard + Stripe + previews)
├── site-generator/
│   └── templates/
│       └── base_template.html # Jinja2 website template
├── leads/                    # Discovered leads (CSV + JSON)
├── analysis/                 # Website analysis reports
├── offers/                   # Markdown improvement offers
├── generated-sites/          # One folder per business with index.html
├── outreach/                 # Email/SMS drafts per lead
└── dashboard/                # Dashboard files
```

---

## Supported Business Types

plumbing, roofing, landscaping, cleaning, barbershop, auto detailing, restaurant, dental, hvac, electrical, painting, moving, pest control, flooring, general contractor

---

## Customization

- **Pricing** -- set `PRICE` in `.env` (default: 500)
- **Templates** -- edit `site-generator/templates/base_template.html` to change the generated site design
- **Email copy** -- modify `scripts/outreach_generator.py` to change pitch wording, tone, or structure
- **Business types** -- add new types in `config/settings.py` under `BUSINESS_TYPES`
- **Search radius** -- change `DEFAULT_SEARCH_RADIUS` in `config/settings.py` (default: 50km)
- **Server port** -- set `PAYMENT_SERVER_PORT` in `.env` (default: 5000)

---

## What to Improve Next

- Add more site templates per business category (currently one base template)
- Add SMS sending support alongside email
- Build a follow-up sequence (automated second/third emails)
- Add lead scoring to prioritize the best prospects
- Integrate a CRM or spreadsheet export for tracking conversations
- Add A/B testing for email subject lines
- Deploy the payment server to a public host so preview links work remotely
- Add screenshot generation of the built sites to include in outreach emails
