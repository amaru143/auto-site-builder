#!/usr/bin/env python
"""
Outreach Generator
Creates personalized cold emails, follow-ups, and SMS drafts for each lead.
Honest, direct, and professional. Includes payment link and setup guide mention.
"""
import os
import sys
import json
import re
from pathlib import Path
from datetime import datetime

sys.path.insert(0, str(Path(__file__).parent.parent))
from config.settings import *


def generate_outreach_package(lead: dict, analysis: dict, site_url: str = "", payment_link: str = "") -> dict:
    """Generate complete outreach package for a lead."""
    name = lead.get("business_name", "Business Owner")
    category = lead.get("category", "local service")
    city = lead.get("search_city", "your area")
    phone = lead.get("phone", "")
    website = lead.get("website", "")
    grade = analysis.get("grade", "N/A")
    score = analysis.get("total_score", 0)
    issues = analysis.get("issues", [])
    recommendations = analysis.get("recommendations", [])

    # Build issue text
    if grade == "N/A" or not website:
        problem_summary = f"we noticed that {name} doesn't currently have a website"
        problem_detail = "Without a website, potential customers searching for your services online can't find you. Studies show that 97% of consumers search online for local businesses, and 75% judge a business's credibility based on their website."
    else:
        problem_summary = f"we took a look at {name}'s current website and found some areas that could be improved"
        issue_text = "\n".join(f"  - {issue}" for issue in issues[:4]) if issues else "  - General design and functionality improvements needed"
        problem_detail = f"Here's what we found:\n{issue_text}\n\nYour current site scored {score}/100 in our analysis."

    # Site preview URL
    preview_text = ""
    if site_url:
        preview_text = f"\nWe've already built a preview of what your new website could look like:\n{site_url}\n"

    # Payment info
    price = PRICE
    payment_text = ""
    if payment_link:
        payment_text = f"\nIf you like what you see, you can get it live today for ${price}:\n{payment_link}\n\nAfter payment, you'll receive a complete setup guide to get the website on your own domain — we walk you through every step.\n"

    business_name = YOUR_BUSINESS_NAME

    # === EMAIL 1: Short cold email ===
    email_short = f"""Subject: A new website for {name} — ready to preview

Hi {name} team,

This is an automated outreach from {business_name} — we help local {category} businesses get online with professional websites.

We noticed {name} {"doesn't have a website yet" if not website else "could benefit from a website upgrade"}, so we went ahead and built one for you.

{f"Check it out here: {site_url}" if site_url else "We'd love to build a preview for you."}

It's fully mobile-friendly, designed for your industry, and ready to go live on your own domain.

{f"If you're interested, you can get it on the spot for ${price} — and you'll receive a full setup guide to get it live on your own domain right after payment." if payment_link else f"The cost is ${price} — including a full setup guide to get it live on your own domain."}
{f"Pay here: {payment_link}" if payment_link else ""}
Want changes? Just reply to this email with what you'd like different, and we'll update it for you at no extra cost before you pay.

The website URL will include a note that a full setup guide is included after purchase, so you know exactly what you're getting.

Best,
{business_name} Team
{YOUR_EMAIL}

---
This email was sent by an automated system. We build websites for local businesses that need them. If you're not interested, no worries — just ignore this email."""

    # === EMAIL 2: Longer detailed email ===
    email_long = f"""Subject: {name} — here's why a professional website could change your business

Hi {name} team,

This is an automated outreach from {business_name}. We specialize in building professional websites for local {category} businesses — and {problem_summary}.

{problem_detail}

Here's what a professional website would do for {name}:

1. **Get found online** — When someone searches "{category} near me" or "{category} in {city}", your business needs to show up with a professional presence.

2. **Build instant trust** — 75% of consumers judge a business's credibility by its website. A clean, modern site with real customer reviews makes the difference between getting the call or losing it to a competitor.

3. **Mobile-ready** — Over 60% of local searches happen on phones. Our sites are built mobile-first, so they look and work perfectly on any device.

4. **Clear calls to action** — One-tap calling, easy quote requests, and clear service descriptions mean more leads converting into paying customers.

{preview_text}The site includes:
- Professional homepage with your business info
- Services section tailored to {category}
- Real customer reviews from your Google profile
- Contact section with phone, address, and map
- Mobile-optimized responsive design
- SEO basics so you show up in local searches
- Clear call-to-action buttons

{f"Ready to go? Get your website live today for ${price}: {payment_link}" if payment_link else f"The investment is ${price} — a one-time cost for a complete, professional website."}

After payment, you'll receive a comprehensive setup guide that walks you through:
- Connecting the site to your own domain name
- Setting up your payment systems
- Making the site live
- Everything you need to get running

Want to make changes first? Just reply with what you'd like different — we'll update the site and send it back, no charge. You only pay when you're happy with it.

Best,
{business_name} Team
{YOUR_EMAIL}
{YOUR_PHONE}

---
This is an automated email from {business_name}. We build websites for local businesses. If this isn't relevant to you, simply ignore this email — no further messages will be sent without your reply."""

    # === EMAIL 3: Follow-up email ===
    email_followup = f"""Subject: Quick follow-up — your {name} website preview

Hi {name} team,

Just a quick follow-up on the website we built for {name}.

{f"In case you missed it, here's the preview: {site_url}" if site_url else "We'd still love to show you what we built."}

A few things worth mentioning:
- The site is already built and ready to go
- It's mobile-friendly and optimized for local search
- You can request any changes before purchasing
- It's ${price} total — one-time cost, no monthly fees
- You get a full setup guide after payment to get it live on your domain

{f"Ready? {payment_link}" if payment_link else ""}

No pressure — if now isn't the right time, that's completely fine. But the site is ready whenever you are.

Best,
{business_name} Team

---
Automated message from {business_name}. Reply STOP to opt out."""

    # === EMAIL 4: Thank you email (sent after payment) ===
    email_thankyou = f"""Subject: Thank you! Here's your website setup guide — {name}

Hi {name} team,

Thank you for your purchase! We're excited to help {name} get online with a professional website.

Here's everything you need to get your new website live:

**Your Website Files**
We've attached your complete website package. You can also download it from your confirmation page.

**Setup Guide**

**Step 1: Get a Domain Name** (if you don't have one)
- Go to Namecheap.com or GoDaddy.com
- Search for a domain like {re.sub(r'[^a-zA-Z0-9]', '', name).lower()}.com
- Purchase it (usually $10-15/year)

**Step 2: Get Hosting**
- We recommend Netlify (free) or Hostinger ($2.99/mo)
- Create an account and follow their upload instructions

**Step 3: Upload Your Website**
- If using Netlify: Simply drag and drop your website folder onto their dashboard
- If using traditional hosting: Upload via their file manager or FTP

**Step 4: Connect Your Domain**
- In your hosting dashboard, add your domain name
- Update your domain's nameservers to point to your hosting provider
- This usually takes 24-48 hours to propagate

**Step 5: Set Up Payment Systems** (optional)
- For online payments, create a Stripe account at stripe.com
- Add the Stripe payment button code to your site
- Or use Square, PayPal, or any payment processor you prefer

**Need Help?**
Reply to this email with any questions — we're happy to help you get set up. We want to make sure your website is live and working perfectly.

Welcome aboard!
{business_name} Team
{YOUR_EMAIL}
{YOUR_PHONE}"""

    # === SMS Draft ===
    sms_draft = f"""Hi {name}! This is {business_name}. We build professional websites for local {category} businesses. We noticed you {"don't have a website yet" if not website else "could use a website upgrade"} and built a preview for you{f": {site_url}" if site_url else ""}. It's ${price}, mobile-ready, and includes a full setup guide. Interested? Reply YES or check it out at the link. - {business_name} Team"""

    return {
        "lead_id": lead.get("id", ""),
        "business_name": name,
        "category": category,
        "city": city,
        "generated_at": datetime.now().isoformat(),
        "emails": {
            "short_pitch": email_short.strip(),
            "detailed_pitch": email_long.strip(),
            "follow_up": email_followup.strip(),
            "thank_you_post_payment": email_thankyou.strip()
        },
        "sms": {
            "initial_outreach": sms_draft.strip()
        },
        "site_url": site_url,
        "payment_link": payment_link,
        "status": "draft"
    }


def generate_all_outreach(leads_file: str = None, analyses_file: str = None):
    """Generate outreach for all analyzed leads."""
    leads_path = Path(leads_file) if leads_file else LEADS_DIR / "all_leads.json"
    analyses_path = Path(analyses_file) if analyses_file else ANALYSIS_DIR / "all_analyses.json"

    if not leads_path.exists():
        print(f"[!] Leads file not found: {leads_path}")
        return []

    with open(leads_path, 'r', encoding='utf-8') as f:
        leads = json.load(f)

    # Load analyses if available
    analyses_map = {}
    if analyses_path.exists():
        with open(analyses_path, 'r', encoding='utf-8') as f:
            analyses = json.load(f)
            analyses_map = {a.get("lead_id", ""): a for a in analyses}

    all_outreach = []
    for lead in leads:
        lead_id = lead.get("id", "")
        analysis = analyses_map.get(lead_id, {
            "grade": "N/A", "total_score": 0,
            "issues": ["No analysis available"], "recommendations": []
        })

        # Check if generated site exists
        safe_name = re.sub(r'[^\w\s-]', '', lead['business_name']).strip().replace(' ', '_').lower()
        site_dir = GENERATED_SITES_DIR / safe_name
        site_url = ""  # Would be set to hosted URL
        payment_link = ""  # Would be set to Stripe payment link

        if site_dir.exists():
            # For now, use local path - will be replaced with hosted URL
            site_url = f"[PREVIEW_URL_FOR_{safe_name}]"

        package = generate_outreach_package(lead, analysis, site_url, payment_link)
        all_outreach.append(package)

        # Save individual outreach package
        outreach_dir = OUTREACH_DIR / safe_name
        outreach_dir.mkdir(parents=True, exist_ok=True)

        # Save each email as separate file
        for email_type, content in package["emails"].items():
            email_path = outreach_dir / f"{email_type}.txt"
            with open(email_path, 'w', encoding='utf-8') as f:
                f.write(content)

        # Save SMS
        sms_path = outreach_dir / "sms_draft.txt"
        with open(sms_path, 'w', encoding='utf-8') as f:
            f.write(package["sms"]["initial_outreach"])

        # Save full package JSON
        pkg_path = outreach_dir / "outreach_package.json"
        with open(pkg_path, 'w', encoding='utf-8') as f:
            json.dump(package, f, indent=2)

        print(f"[+] Generated outreach for: {lead['business_name']}")

    # Save master outreach file
    master_path = OUTREACH_DIR / "all_outreach.json"
    with open(master_path, 'w', encoding='utf-8') as f:
        json.dump(all_outreach, f, indent=2)

    print(f"\n[+] Generated {len(all_outreach)} outreach packages")
    print(f"[+] Saved to {OUTREACH_DIR}")

    return all_outreach


if __name__ == "__main__":
    import argparse
    parser = argparse.ArgumentParser(description="Generate outreach packages")
    parser.add_argument("--leads-file", help="Path to leads JSON")
    parser.add_argument("--analyses-file", help="Path to analyses JSON")
    args = parser.parse_args()
    generate_all_outreach(args.leads_file, args.analyses_file)
