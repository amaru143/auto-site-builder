#!/usr/bin/env python
"""
Email Sender Module
Sends outreach emails via Gmail SMTP. Handles initial pitches, follow-ups, and post-payment thank-you emails.
NEVER auto-sends without explicit user confirmation.
"""
import os
import sys
import json
import re
import smtplib
import ssl
from email.mime.text import MIMEText
from email.mime.multipart import MIMEMultipart
from email.mime.base import MIMEBase
from email import encoders
from pathlib import Path
from datetime import datetime

sys.path.insert(0, str(Path(__file__).parent.parent))
from config.settings import *

# Email tracking
EMAIL_LOG_FILE = BASE_DIR / "outreach" / "email_log.json"


def load_email_log():
    if EMAIL_LOG_FILE.exists():
        with open(EMAIL_LOG_FILE, 'r') as f:
            return json.load(f)
    return {}


def save_email_log(log):
    with open(EMAIL_LOG_FILE, 'w') as f:
        json.dump(log, f, indent=2)


def create_smtp_connection():
    """Create Gmail SMTP connection."""
    if not GMAIL_ADDRESS or GMAIL_ADDRESS == 'your_gmail@gmail.com':
        return None
    if not GMAIL_APP_PASSWORD or GMAIL_APP_PASSWORD == 'your_gmail_app_password_here':
        return None

    context = ssl.create_default_context()
    server = smtplib.SMTP_SSL('smtp.gmail.com', 465, context=context)
    server.login(GMAIL_ADDRESS, GMAIL_APP_PASSWORD)
    return server


def send_email(to_email: str, subject: str, body: str, is_html: bool = False, attachments: list = None) -> bool:
    """Send a single email."""
    if not to_email:
        print(f"[!] No recipient email address")
        return False

    msg = MIMEMultipart()
    msg['From'] = f"{YOUR_BUSINESS_NAME} <{GMAIL_ADDRESS}>"
    msg['To'] = to_email
    msg['Subject'] = subject

    # Convert plain text to simple HTML for better formatting
    if not is_html:
        html_body = body.replace('\n', '<br>\n')
        html_body = re.sub(r'\*\*(.*?)\*\*', r'<strong>\1</strong>', html_body)
        msg.attach(MIMEText(html_body, 'html'))
    else:
        msg.attach(MIMEText(body, 'html'))

    # Add attachments
    if attachments:
        for filepath in attachments:
            path = Path(filepath)
            if path.exists():
                with open(path, 'rb') as f:
                    part = MIMEBase('application', 'octet-stream')
                    part.set_payload(f.read())
                    encoders.encode_base64(part)
                    part.add_header('Content-Disposition', f'attachment; filename={path.name}')
                    msg.attach(part)

    try:
        server = create_smtp_connection()
        if not server:
            print(f"[!] Gmail not configured. Email would be sent to: {to_email}")
            print(f"    Subject: {subject}")
            return False

        server.sendmail(GMAIL_ADDRESS, to_email, msg.as_string())
        server.quit()
        print(f"[+] Email sent to {to_email}: {subject}")
        return True

    except Exception as e:
        print(f"[!] Failed to send email to {to_email}: {e}")
        return False


def send_pitch_email(lead: dict, email_type: str = "short_pitch", payment_link: str = "", site_url: str = "") -> bool:
    """Send a pitch email to a lead."""
    lead_id = lead.get("id", "")
    business_name = lead.get("business_name", "")

    # Find the business email
    to_email = lead.get("email", "")
    if not to_email:
        print(f"[!] No email found for {business_name}. Skipping.")
        return False

    # Load outreach package
    safe_name = re.sub(r'[^\w\s-]', '', business_name).strip().replace(' ', '_').lower()
    outreach_dir = OUTREACH_DIR / safe_name
    email_file = outreach_dir / f"{email_type}.txt"

    if not email_file.exists():
        print(f"[!] Outreach email not found: {email_file}")
        return False

    with open(email_file, 'r', encoding='utf-8') as f:
        content = f.read()

    # Extract subject from content
    subject = ""
    body = content
    if content.startswith("Subject:"):
        lines = content.split('\n', 1)
        subject = lines[0].replace("Subject:", "").strip()
        body = lines[1].strip() if len(lines) > 1 else ""

    # Replace placeholder URLs with actual URLs
    if payment_link:
        body = body.replace("[PAYMENT_LINK]", payment_link)
        body = re.sub(r'\[PREVIEW_URL_FOR_\w+\]', site_url or '', body)

    if site_url:
        body = re.sub(r'\[PREVIEW_URL_FOR_\w+\]', site_url, body)

    # Send
    success = send_email(to_email, subject, body)

    # Log
    log = load_email_log()
    log[lead_id] = log.get(lead_id, {"emails_sent": []})
    log[lead_id]["emails_sent"].append({
        "type": email_type,
        "to": to_email,
        "subject": subject,
        "sent_at": datetime.now().isoformat(),
        "success": success
    })
    save_email_log(log)

    return success


def send_thank_you_email(lead_id: str) -> bool:
    """Send thank-you email with setup guide after payment."""
    leads_path = LEADS_DIR / "all_leads.json"
    if not leads_path.exists():
        return False

    with open(leads_path, 'r') as f:
        leads = json.load(f)

    lead = next((l for l in leads if l.get('id') == lead_id), None)
    if not lead:
        print(f"[!] Lead not found: {lead_id}")
        return False

    business_name = lead.get("business_name", "")
    to_email = lead.get("email", "")

    if not to_email:
        print(f"[!] No email for {business_name}")
        return False

    # Load thank-you email
    safe_name = re.sub(r'[^\w\s-]', '', business_name).strip().replace(' ', '_').lower()
    email_file = OUTREACH_DIR / safe_name / "thank_you_post_payment.txt"

    if email_file.exists():
        with open(email_file, 'r', encoding='utf-8') as f:
            content = f.read()

        subject = ""
        body = content
        if content.startswith("Subject:"):
            lines = content.split('\n', 1)
            subject = lines[0].replace("Subject:", "").strip()
            body = lines[1].strip() if len(lines) > 1 else ""
    else:
        subject = f"Thank you! Here's your website setup guide — {business_name}"
        body = f"""Hi {business_name} team,

Thank you for your purchase! Your professional website is ready.

Please find your website files attached. Here's your setup guide:

1. Get a domain name (Namecheap.com or GoDaddy.com)
2. Get hosting (Netlify is free, or Hostinger at $2.99/mo)
3. Upload your website files
4. Connect your domain
5. You're live!

Reply to this email if you need any help getting set up.

Best,
{YOUR_BUSINESS_NAME} Team"""

    # Attach the website zip if it exists
    site_dir = GENERATED_SITES_DIR / safe_name
    attachments = []
    zip_path = GENERATED_SITES_DIR / f"{safe_name}.zip"

    if site_dir.exists() and not zip_path.exists():
        # Create zip of website
        import shutil
        shutil.make_archive(str(GENERATED_SITES_DIR / safe_name), 'zip', str(site_dir))

    if zip_path.exists():
        attachments.append(str(zip_path))

    success = send_email(to_email, subject, body, attachments=attachments)

    # Log
    log = load_email_log()
    log[lead_id] = log.get(lead_id, {"emails_sent": []})
    log[lead_id]["emails_sent"].append({
        "type": "thank_you",
        "to": to_email,
        "subject": subject,
        "sent_at": datetime.now().isoformat(),
        "success": success
    })
    save_email_log(log)

    return success


def send_revision_email(lead_id: str, changes_description: str, site_url: str) -> bool:
    """Send updated website after requested changes."""
    leads_path = LEADS_DIR / "all_leads.json"
    if not leads_path.exists():
        return False

    with open(leads_path, 'r') as f:
        leads = json.load(f)

    lead = next((l for l in leads if l.get('id') == lead_id), None)
    if not lead:
        return False

    business_name = lead.get("business_name", "")
    to_email = lead.get("email", "")

    if not to_email:
        return False

    subject = f"Your updated website is ready — {business_name}"
    body = f"""Hi {business_name} team,

We've made the changes you requested:

{changes_description}

Check out your updated website here: {site_url}

If everything looks good, you can get it live for ${PRICE}:
[PAYMENT_LINK]

After payment, you'll receive a complete setup guide to get the website on your own domain.

Want more changes? Just reply to this email.

Best,
{YOUR_BUSINESS_NAME} Team

---
Automated message from {YOUR_BUSINESS_NAME}."""

    return send_email(to_email, subject, body)


def send_bulk_outreach(email_type: str = "short_pitch", confirm: bool = True, dry_run: bool = False):
    """Send outreach emails to all qualified leads."""
    leads_path = LEADS_DIR / "all_leads.json"
    if not leads_path.exists():
        print("[!] No leads found")
        return

    with open(leads_path, 'r') as f:
        leads = json.load(f)

    email_log = load_email_log()

    # Filter leads that haven't been emailed yet
    eligible = []
    for lead in leads:
        lead_id = lead.get('id', '')
        if lead.get('email') and lead_id not in email_log:
            if lead.get('flag_no_website') or lead.get('priority') in ['critical', 'high']:
                eligible.append(lead)

    print(f"\n{'='*60}")
    print(f"BULK OUTREACH - {email_type}")
    print(f"{'='*60}")
    print(f"Eligible leads: {len(eligible)}")

    if not eligible:
        print("No eligible leads to email.")
        return

    if confirm and not dry_run:
        print("\nLeads to email:")
        for lead in eligible:
            print(f"  - {lead['business_name']} ({lead.get('email', 'NO EMAIL')})")

        response = input("\nSend emails to these businesses? (yes/no): ")
        if response.lower() != 'yes':
            print("Aborted.")
            return

    if dry_run:
        print("\n[DRY RUN] Would send to:")
        for lead in eligible:
            print(f"  - {lead['business_name']} ({lead.get('email', 'NO EMAIL')})")
        return

    sent = 0
    failed = 0
    for lead in eligible:
        success = send_pitch_email(lead, email_type)
        if success:
            sent += 1
        else:
            failed += 1

    print(f"\n[+] Sent: {sent} | Failed: {failed}")


if __name__ == "__main__":
    import argparse
    parser = argparse.ArgumentParser(description="Send outreach emails")
    parser.add_argument("--type", default="short_pitch", choices=["short_pitch", "detailed_pitch", "follow_up"])
    parser.add_argument("--dry-run", action="store_true", help="Preview without sending")
    parser.add_argument("--no-confirm", action="store_true", help="Skip confirmation prompt")
    parser.add_argument("--lead-id", help="Send to specific lead only")
    args = parser.parse_args()

    if args.lead_id:
        leads_path = LEADS_DIR / "all_leads.json"
        with open(leads_path, 'r') as f:
            leads = json.load(f)
        lead = next((l for l in leads if l.get('id') == args.lead_id), None)
        if lead:
            send_pitch_email(lead, args.type)
        else:
            print(f"[!] Lead not found: {args.lead_id}")
    else:
        send_bulk_outreach(args.type, confirm=not args.no_confirm, dry_run=args.dry_run)
