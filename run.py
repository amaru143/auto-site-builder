#!/usr/bin/env python
"""
Auto Site Builder — Main Orchestrator
Run the complete pipeline: discover leads → analyze → generate sites → prepare outreach → send emails

Usage:
    python run.py --full --city Austin --state TX
    python run.py --discover --city Austin --state TX
    python run.py --analyze
    python run.py --generate
    python run.py --outreach
    python run.py --send --dry-run
    python run.py --server
    python run.py --demo
"""
import os
import sys
import json
import argparse
from pathlib import Path
from datetime import datetime

# Ensure project root is in path
PROJECT_ROOT = Path(__file__).parent
sys.path.insert(0, str(PROJECT_ROOT))

from config.settings import *


def print_banner():
    print("""
============================================================
     AUTO SITE BUILDER
     Find - Analyze - Build - Pitch
============================================================
    """)


def step_discover(categories, cities, states):
    """Step 1: Discover leads."""
    print("\n" + "="*60)
    print("STEP 1: LEAD DISCOVERY")
    print("="*60)

    from scripts.lead_discovery import discover_leads
    leads = discover_leads(categories, cities, states)
    print(f"\n✓ Discovered {len(leads)} leads")
    return leads


def step_analyze():
    """Step 2: Analyze websites."""
    print("\n" + "="*60)
    print("STEP 2: WEBSITE ANALYSIS")
    print("="*60)

    from scripts.website_analyzer import analyze_leads
    analyses = analyze_leads()

    if analyses:
        critical = sum(1 for a in analyses if a.get('priority') == 'critical')
        high = sum(1 for a in analyses if a.get('priority') == 'high')
        print(f"\n✓ Analyzed {len(analyses)} websites")
        print(f"  Critical (no website): {critical}")
        print(f"  High priority: {high}")

    return analyses


def step_generate():
    """Step 3: Generate websites."""
    print("\n" + "="*60)
    print("STEP 3: WEBSITE GENERATION")
    print("="*60)

    from scripts.site_generator import generate_all_websites
    generate_all_websites()

    # Count generated sites
    generated = sum(1 for d in GENERATED_SITES_DIR.iterdir() if d.is_dir() and (d / 'index.html').exists())
    print(f"\n✓ Generated {generated} websites")


def step_offers():
    """Step 3.5: Generate improvement offers."""
    print("\n" + "="*60)
    print("STEP 3.5: OFFER GENERATION")
    print("="*60)

    from scripts.offer_generator import generate_all_offers
    generate_all_offers()


def step_outreach():
    """Step 4: Generate outreach materials."""
    print("\n" + "="*60)
    print("STEP 4: OUTREACH PREPARATION")
    print("="*60)

    from scripts.outreach_generator import generate_all_outreach
    packages = generate_all_outreach()
    print(f"\n✓ Created {len(packages)} outreach packages")


def step_send(email_type="short_pitch", dry_run=True):
    """Step 5: Send emails (with confirmation)."""
    print("\n" + "="*60)
    print(f"STEP 5: EMAIL OUTREACH {'(DRY RUN)' if dry_run else '(LIVE)'}")
    print("="*60)

    from scripts.email_sender import send_bulk_outreach
    send_bulk_outreach(email_type, confirm=True, dry_run=dry_run)


def step_server():
    """Start the payment server and dashboard."""
    print("\n" + "="*60)
    print("STARTING SERVER & DASHBOARD")
    print("="*60)

    from scripts.payment_server import app, PAYMENT_SERVER_PORT
    print(f"\nDashboard: http://localhost:{PAYMENT_SERVER_PORT}/dashboard")
    print(f"API: http://localhost:{PAYMENT_SERVER_PORT}/api/leads")
    print("\nPress Ctrl+C to stop.\n")
    app.run(host='0.0.0.0', port=PAYMENT_SERVER_PORT, debug=True)


def step_demo():
    """Run a full demo with mock data."""
    print("\n" + "="*60)
    print("RUNNING DEMO WITH MOCK DATA")
    print("="*60)

    # Discover
    leads = step_discover(
        categories=["plumbing", "roofing", "landscaping", "cleaning", "barbershop", "auto detailing", "restaurant", "dental"],
        cities=["Austin"],
        states=["TX"]
    )

    # Analyze
    analyses = step_analyze()

    # Generate sites
    step_generate()

    # Generate offers
    step_offers()

    # Generate outreach
    step_outreach()

    # Summary
    print_summary()

    print("\n" + "="*60)
    print("DEMO COMPLETE!")
    print("="*60)
    print(f"\nTo view the dashboard, run:")
    print(f"  python run.py --server")
    print(f"\nTo preview generated sites, open:")
    print(f"  {GENERATED_SITES_DIR}")
    print(f"\nTo send emails (dry run first!):")
    print(f"  python run.py --send --dry-run")


def print_summary():
    """Print a summary of all data."""
    print("\n" + "="*60)
    print("PIPELINE SUMMARY")
    print("="*60)

    # Leads
    leads_path = LEADS_DIR / "all_leads.json"
    if leads_path.exists():
        with open(leads_path, 'r', encoding='utf-8') as f:
            leads = json.load(f)
        no_site = sum(1 for l in leads if l.get('flag_no_website'))
        print(f"\nLeads: {len(leads)} total ({no_site} without websites)")

    # Analyses
    analyses_path = ANALYSIS_DIR / "all_analyses.json"
    if analyses_path.exists():
        with open(analyses_path, 'r', encoding='utf-8') as f:
            analyses = json.load(f)
        by_priority = {}
        for a in analyses:
            p = a.get('priority', 'unknown')
            by_priority[p] = by_priority.get(p, 0) + 1
        print(f"Analyses: {len(analyses)} total")
        for p, c in sorted(by_priority.items()):
            print(f"  {p}: {c}")

    # Generated sites
    generated = sum(1 for d in GENERATED_SITES_DIR.iterdir() if d.is_dir() and (d / 'index.html').exists()) if GENERATED_SITES_DIR.exists() else 0
    print(f"Generated sites: {generated}")

    # Outreach
    outreach_path = OUTREACH_DIR / "all_outreach.json"
    if outreach_path.exists():
        with open(outreach_path, 'r', encoding='utf-8') as f:
            outreach = json.load(f)
        print(f"Outreach packages: {len(outreach)}")

    # Offers
    offers = list(OFFERS_DIR.glob("*.md")) if OFFERS_DIR.exists() else []
    print(f"Offers: {len(offers)}")


def run_full_pipeline(categories, cities, states, dry_run=True):
    """Run the complete pipeline."""
    print_banner()

    # Step 1: Discover
    leads = step_discover(categories, cities, states)

    # Step 2: Analyze
    analyses = step_analyze()

    # Step 3: Generate websites
    step_generate()

    # Step 3.5: Generate offers
    step_offers()

    # Step 4: Prepare outreach
    step_outreach()

    # Step 5: Send emails (dry run by default)
    if not dry_run:
        step_send(dry_run=False)
    else:
        print("\n[i] Skipping email send (use --send to enable)")

    # Summary
    print_summary()

    print(f"\nDone! Run 'python run.py --server' to view the dashboard.")


if __name__ == "__main__":
    parser = argparse.ArgumentParser(description="Auto Site Builder — Complete Pipeline")

    # Pipeline steps
    parser.add_argument("--full", action="store_true", help="Run complete pipeline")
    parser.add_argument("--demo", action="store_true", help="Run demo with mock data")
    parser.add_argument("--discover", action="store_true", help="Run lead discovery only")
    parser.add_argument("--analyze", action="store_true", help="Run website analysis only")
    parser.add_argument("--generate", action="store_true", help="Generate websites only")
    parser.add_argument("--offers", action="store_true", help="Generate offers only")
    parser.add_argument("--outreach", action="store_true", help="Generate outreach materials only")
    parser.add_argument("--send", action="store_true", help="Send outreach emails")
    parser.add_argument("--server", action="store_true", help="Start payment server & dashboard")
    parser.add_argument("--summary", action="store_true", help="Print pipeline summary")

    # Options
    parser.add_argument("--categories", nargs="+", default=["plumbing", "roofing", "landscaping", "cleaning", "barbershop", "auto detailing", "restaurant", "dental"])
    parser.add_argument("--cities", nargs="+", default=["Austin"])
    parser.add_argument("--states", nargs="+", default=["TX"])
    parser.add_argument("--dry-run", action="store_true", help="Preview emails without sending")
    parser.add_argument("--email-type", default="short_pitch", choices=["short_pitch", "detailed_pitch", "follow_up"])

    args = parser.parse_args()

    print_banner()

    if args.demo:
        step_demo()
    elif args.full:
        run_full_pipeline(args.categories, args.cities, args.states, dry_run=args.dry_run)
    elif args.discover:
        step_discover(args.categories, args.cities, args.states)
    elif args.analyze:
        step_analyze()
    elif args.generate:
        step_generate()
    elif args.offers:
        step_offers()
    elif args.outreach:
        step_outreach()
    elif args.send:
        step_send(args.email_type, args.dry_run)
    elif args.server:
        step_server()
    elif args.summary:
        print_summary()
    else:
        parser.print_help()
        print("\n\nQuick start:")
        print("  python run.py --demo          # Run full demo with mock data")
        print("  python run.py --full          # Run full pipeline (needs API keys)")
        print("  python run.py --server        # Start dashboard & payment server")
