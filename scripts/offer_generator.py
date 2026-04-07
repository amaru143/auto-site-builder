#!/usr/bin/env python
"""
Offer Generator
Creates tailored website improvement offers for each qualified lead.
"""
import os
import sys
import json
import re
from pathlib import Path
from datetime import datetime

sys.path.insert(0, str(Path(__file__).parent.parent))
from config.settings import *


def generate_offer(lead: dict, analysis: dict) -> str:
    """Generate a markdown offer document for a lead."""
    name = lead.get("business_name", "Business")
    category = lead.get("category", "service").replace("_", " ").title()
    city = lead.get("search_city", "your area")
    website = lead.get("website", "")
    phone = lead.get("phone", "")
    rating = lead.get("rating", 0)
    review_count = lead.get("review_count", 0)

    grade = analysis.get("grade", "N/A")
    score = analysis.get("total_score", 0)
    issues = analysis.get("issues", [])
    recommendations = analysis.get("recommendations", [])
    scores = analysis.get("scores", {})

    # Build the offer
    if not website or grade == "N/A":
        current_status = f"""## Current Web Presence

**{name} currently has no website.**

This means:
- Customers searching for "{category.lower()} near me" or "{category.lower()} in {city}" cannot find you online
- 97% of consumers search online before choosing a local business
- 75% of people judge a business's credibility based on their website
- Competitors with websites are capturing customers that should be yours
- You're invisible to the largest source of new customer leads
"""
    else:
        score_breakdown = ""
        score_labels = {
            "mobile_friendliness": ("Mobile Friendliness", 15),
            "design_quality": ("Design Quality", 15),
            "speed": ("Loading Speed", 15),
            "trust_signals": ("Trust Signals", 10),
            "seo": ("SEO Basics", 15),
            "cta_clarity": ("Call-to-Action Clarity", 15),
            "contact_clarity": ("Contact Information", 15)
        }
        for key, (label, max_val) in score_labels.items():
            val = scores.get(key, 0)
            bar = "█" * int(val / max_val * 10) + "░" * (10 - int(val / max_val * 10))
            score_breakdown += f"| {label} | {bar} | {val}/{max_val} |\n"

        issues_text = "\n".join(f"- ❌ {issue}" for issue in issues) if issues else "- No critical issues found"

        current_status = f"""## Current Website Analysis

**Website:** {website}
**Overall Score:** {score}/100 (Grade: {grade})

### Score Breakdown

| Category | Score | Points |
|----------|-------|--------|
{score_breakdown}

### Issues Found

{issues_text}
"""

    # What we'd improve
    improvements = f"""## What a New Website Would Include

### For a {category} business like {name}, a professional website should have:

1. **Mobile-First Responsive Design**
   - 60%+ of local searches happen on mobile devices
   - Your site will look and work perfectly on any screen size
   - One-tap calling and easy navigation on phones

2. **Professional, Trust-Building Design**
   - Clean, modern layout that establishes credibility instantly
   - High-quality imagery relevant to {category.lower()} services
   - Consistent branding with your business colors and style

3. **Customer Reviews & Social Proof**
   {"- Your " + str(review_count) + " Google reviews prominently displayed" if review_count > 0 else "- Space for customer testimonials and reviews"}
   {"- Your " + str(rating) + "-star rating featured on the homepage" if rating > 0 else "- Trust badges and ratings section"}
   - Real customer feedback builds trust with new visitors

4. **Clear Calls-to-Action**
   - Prominent "Get a Free Quote" / "Call Now" buttons
   - Easy contact form for lead capture
   - Click-to-call functionality for mobile users

5. **Local SEO Optimization**
   - Optimized for "{category.lower()} in {city}" searches
   - Proper meta tags, headers, and structured data
   - Google Business Profile integration
   - Schema markup for local business

6. **Service Pages**
   - Detailed descriptions of all your services
   - Clear pricing guidance (if applicable)
   - Service area information

7. **Contact & Location**
   - Phone number prominently displayed
   - Business address with Google Maps embed
   - Hours of operation
   - Contact form for after-hours inquiries
"""

    value_prop = f"""## Value Proposition

### What this means for {name}:

- **More Visibility**: Appear in Google searches when people look for {category.lower()} services in {city}
- **More Credibility**: A professional website makes customers trust you over competitors without one
- **More Leads**: Clear calls-to-action convert website visitors into actual phone calls and quotes
- **More Revenue**: Even 2-3 extra jobs per month from your website pays for itself many times over
- **24/7 Marketing**: Your website works for you around the clock, even when you're not available

### Investment

**One-time cost: ${PRICE}**

This includes:
- Complete professional website
- Mobile-responsive design
- SEO optimization
- All source files
- Full setup guide to get it live on your domain
- Free revisions before purchase

No monthly fees. No hidden costs. One payment, and the website is yours forever.
"""

    offer = f"""# Website Improvement Offer for {name}

**Prepared by:** {YOUR_BUSINESS_NAME}
**Date:** {datetime.now().strftime("%B %d, %Y")}
**Business:** {name}
**Category:** {category}
**Location:** {city}

---

{current_status}

---

{improvements}

---

{value_prop}

---

## Next Steps

1. **Review the preview website** we've built for you
2. **Request any changes** — we'll update it at no cost
3. **Purchase for ${PRICE}** — one-time payment
4. **Receive your setup guide** — step-by-step instructions to go live
5. **Your website is live** — start getting found online

---

*This offer was prepared by {YOUR_BUSINESS_NAME}. We specialize in building professional websites for local service businesses.*

*Contact: {YOUR_EMAIL} | {YOUR_PHONE}*
"""

    return offer


def generate_all_offers(leads_file: str = None, analyses_file: str = None):
    """Generate offers for all qualified leads."""
    leads_path = Path(leads_file) if leads_file else LEADS_DIR / "all_leads.json"
    analyses_path = Path(analyses_file) if analyses_file else ANALYSIS_DIR / "all_analyses.json"

    if not leads_path.exists():
        print(f"[!] Leads file not found: {leads_path}")
        return

    with open(leads_path, 'r', encoding='utf-8') as f:
        leads = json.load(f)

    analyses_map = {}
    if analyses_path.exists():
        with open(analyses_path, 'r', encoding='utf-8') as f:
            analyses = json.load(f)
            analyses_map = {a.get("lead_id", ""): a for a in analyses}

    generated = 0
    for lead in leads:
        lead_id = lead.get("id", "")
        analysis = analyses_map.get(lead_id, {
            "grade": "N/A", "total_score": 0,
            "issues": [], "recommendations": [], "scores": {}
        })

        # Only generate for qualified leads
        priority = analysis.get("priority", lead.get("priority", "medium"))
        if priority in ["critical", "high", "medium"]:
            offer_md = generate_offer(lead, analysis)

            safe_name = re.sub(r'[^\w\s-]', '', lead['business_name']).strip().replace(' ', '_').lower()
            offer_path = OFFERS_DIR / f"offer_{safe_name}.md"

            with open(offer_path, 'w', encoding='utf-8') as f:
                f.write(offer_md)

            generated += 1
            print(f"[+] Offer generated: {offer_path}")

    print(f"\n[+] Generated {generated} offers in {OFFERS_DIR}")


if __name__ == "__main__":
    import argparse
    parser = argparse.ArgumentParser(description="Generate website improvement offers")
    parser.add_argument("--leads-file", help="Path to leads JSON")
    parser.add_argument("--analyses-file", help="Path to analyses JSON")
    args = parser.parse_args()
    generate_all_offers(args.leads_file, args.analyses_file)
