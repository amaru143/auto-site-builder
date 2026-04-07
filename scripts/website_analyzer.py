#!/usr/bin/env python
"""
Website Quality Analyzer
Scores business websites on mobile friendliness, design, speed, SEO, trust signals, CTAs, and contact clarity.
"""
import os
import sys
import json
import re
import time
import requests
from pathlib import Path
from datetime import datetime
from urllib.parse import urlparse

sys.path.insert(0, str(Path(__file__).parent.parent))
from config.settings import *

try:
    from bs4 import BeautifulSoup
except ImportError:
    print("[!] BeautifulSoup not installed. Run: pip install beautifulsoup4")
    BeautifulSoup = None


def analyze_website(url: str, business_name: str = "") -> dict:
    """Analyze a website and return quality scores."""
    result = {
        "url": url,
        "business_name": business_name,
        "analyzed_at": datetime.now().isoformat(),
        "reachable": False,
        "scores": {},
        "total_score": 0,
        "max_score": 100,
        "grade": "F",
        "issues": [],
        "recommendations": [],
        "summary": ""
    }

    if not url:
        result["issues"].append("No website URL provided")
        result["summary"] = "Business has no website. This is a high-priority lead."
        result["grade"] = "N/A"
        return result

    # Ensure URL has protocol
    if not url.startswith(('http://', 'https://')):
        url = 'https://' + url

    # Try to fetch the website
    try:
        headers = {
            'User-Agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/120.0.0.0 Safari/537.36'
        }
        start_time = time.time()
        resp = requests.get(url, headers=headers, timeout=15, allow_redirects=True)
        load_time = time.time() - start_time
        result["reachable"] = True
        result["status_code"] = resp.status_code
        result["load_time_seconds"] = round(load_time, 2)
        result["final_url"] = resp.url
    except requests.exceptions.SSLError:
        result["issues"].append("SSL certificate error - site not secure")
        result["scores"]["security"] = 0
        try:
            resp = requests.get(url.replace('https://', 'http://'), headers=headers, timeout=15)
            load_time = time.time() - start_time
            result["reachable"] = True
            result["status_code"] = resp.status_code
            result["load_time_seconds"] = round(load_time, 2)
        except:
            result["issues"].append("Website completely unreachable")
            result["summary"] = f"Website at {url} is unreachable. Broken website - high priority lead."
            return result
    except requests.exceptions.ConnectionError:
        result["issues"].append("Connection refused - website may be down")
        result["summary"] = f"Website at {url} is down or broken. High priority lead."
        return result
    except requests.exceptions.Timeout:
        result["issues"].append("Website took too long to respond (>15 seconds)")
        result["summary"] = f"Website at {url} is extremely slow. High priority lead."
        return result
    except Exception as e:
        result["issues"].append(f"Error accessing website: {str(e)}")
        result["summary"] = f"Could not access website at {url}. Error: {str(e)}"
        return result

    if resp.status_code >= 400:
        result["issues"].append(f"Website returns error status: {resp.status_code}")
        result["summary"] = f"Website returns HTTP {resp.status_code} error. Broken website - high priority lead."
        return result

    html = resp.text
    if not BeautifulSoup:
        result["summary"] = "BeautifulSoup not available for analysis"
        return result

    soup = BeautifulSoup(html, 'html.parser')

    # 1. Mobile Friendliness (0-15 points)
    mobile_score = score_mobile_friendliness(soup, html)
    result["scores"]["mobile_friendliness"] = mobile_score

    # 2. Design Quality (0-15 points)
    design_score = score_design_quality(soup, html, url)
    result["scores"]["design_quality"] = design_score

    # 3. Speed Indicators (0-15 points)
    speed_score = score_speed(load_time, html, soup)
    result["scores"]["speed"] = speed_score

    # 4. Trust Signals (0-10 points)
    trust_score = score_trust_signals(soup, html)
    result["scores"]["trust_signals"] = trust_score

    # 5. SEO Basics (0-15 points)
    seo_score = score_seo(soup, html, url)
    result["scores"]["seo"] = seo_score

    # 6. CTA Clarity (0-15 points)
    cta_score = score_cta_clarity(soup, html)
    result["scores"]["cta_clarity"] = cta_score

    # 7. Contact Clarity (0-15 points)
    contact_score = score_contact_clarity(soup, html)
    result["scores"]["contact_clarity"] = contact_score

    # Calculate total
    total = sum(result["scores"].values())
    result["total_score"] = total

    # Grade
    if total >= 85:
        result["grade"] = "A"
    elif total >= 70:
        result["grade"] = "B"
    elif total >= 55:
        result["grade"] = "C"
    elif total >= 40:
        result["grade"] = "D"
    else:
        result["grade"] = "F"

    # Generate issues and recommendations
    result["issues"] = generate_issues(result["scores"], soup, html, load_time)
    result["recommendations"] = generate_recommendations(result["scores"])
    result["summary"] = generate_summary(result)

    return result


def score_mobile_friendliness(soup, html: str) -> int:
    """Score mobile friendliness 0-15."""
    score = 0

    # Check for viewport meta tag
    viewport = soup.find('meta', attrs={'name': 'viewport'})
    if viewport:
        score += 5
        content = viewport.get('content', '')
        if 'width=device-width' in content:
            score += 3

    # Check for responsive CSS indicators
    if any(x in html for x in ['@media', 'responsive', 'mobile', 'bootstrap', 'tailwind']):
        score += 4

    # Check for overly large fixed widths
    if re.search(r'width:\s*\d{4,}px', html):
        score -= 3

    # Check for flexible images
    if 'max-width' in html or 'img-fluid' in html or 'w-full' in html:
        score += 3

    return max(0, min(15, score))


def score_design_quality(soup, html: str, url: str) -> int:
    """Score design quality 0-15."""
    score = 0

    # Check for modern CSS framework
    if any(x in html.lower() for x in ['bootstrap', 'tailwind', 'bulma', 'material', 'foundation']):
        score += 4

    # Check for custom fonts
    if any(x in html for x in ['fonts.googleapis.com', 'typekit', 'font-face', 'font-family']):
        score += 2

    # Check for images
    images = soup.find_all('img')
    if len(images) >= 3:
        score += 3
    elif len(images) >= 1:
        score += 1

    # Check for structured layout
    if soup.find('header') or soup.find('nav'):
        score += 2
    if soup.find('footer'):
        score += 1

    # Check for modern HTML5 structure
    html5_elements = ['section', 'article', 'aside', 'main', 'header', 'footer', 'nav']
    html5_count = sum(1 for el in html5_elements if soup.find(el))
    if html5_count >= 3:
        score += 3
    elif html5_count >= 1:
        score += 1

    # Penalize free website builders
    free_builders = ['wix.com', 'weebly.com', 'blogspot.com', 'wordpress.com', 'sites.google.com', 'godaddy.com/website-builder']
    parsed = urlparse(url)
    if any(builder in parsed.netloc + parsed.path for builder in free_builders):
        score -= 3

    return max(0, min(15, score))


def score_speed(load_time: float, html: str, soup) -> int:
    """Score speed indicators 0-15."""
    score = 0

    # Load time scoring
    if load_time < 1.0:
        score += 6
    elif load_time < 2.0:
        score += 4
    elif load_time < 3.0:
        score += 2
    elif load_time < 5.0:
        score += 1

    # Check HTML size
    html_size = len(html)
    if html_size < 100000:
        score += 3
    elif html_size < 300000:
        score += 2
    elif html_size < 500000:
        score += 1

    # Check for optimization indicators
    if 'async' in html or 'defer' in html:
        score += 2
    if 'loading="lazy"' in html:
        score += 2

    # Check for excessive scripts
    scripts = soup.find_all('script')
    if len(scripts) > 20:
        score -= 2

    # Check for minification indicators
    if '.min.css' in html or '.min.js' in html:
        score += 2

    return max(0, min(15, score))


def score_trust_signals(soup, html: str) -> int:
    """Score trust signals 0-10."""
    score = 0

    # Check for reviews/testimonials
    trust_words = ['testimonial', 'review', 'rating', 'stars', 'customer says', 'what our clients']
    if any(w in html.lower() for w in trust_words):
        score += 3

    # Check for certifications/badges
    cert_words = ['certified', 'licensed', 'insured', 'bonded', 'accredited', 'bbb', 'guarantee']
    if any(w in html.lower() for w in cert_words):
        score += 2

    # Check for social proof
    social_words = ['facebook', 'instagram', 'twitter', 'yelp', 'google review', 'linkedin']
    if any(w in html.lower() for w in social_words):
        score += 2

    # Check for HTTPS
    # Already checked elsewhere but contributes to trust
    if 'https' in html[:100]:
        score += 1

    # Check for about/team section
    if any(w in html.lower() for w in ['about us', 'our team', 'our story', 'meet the team']):
        score += 2

    return max(0, min(10, score))


def score_seo(soup, html: str, url: str) -> int:
    """Score SEO basics 0-15."""
    score = 0

    # Title tag
    title = soup.find('title')
    if title and title.string:
        title_text = title.string.strip()
        if len(title_text) > 10 and len(title_text) < 70:
            score += 3
        elif title:
            score += 1

    # Meta description
    meta_desc = soup.find('meta', attrs={'name': 'description'})
    if meta_desc and meta_desc.get('content', ''):
        desc = meta_desc['content']
        if len(desc) > 50 and len(desc) < 160:
            score += 3
        elif desc:
            score += 1

    # Header tags
    h1 = soup.find('h1')
    if h1:
        score += 2

    h2_tags = soup.find_all('h2')
    if len(h2_tags) >= 2:
        score += 2
    elif h2_tags:
        score += 1

    # Image alt tags
    images = soup.find_all('img')
    if images:
        with_alt = sum(1 for img in images if img.get('alt'))
        ratio = with_alt / len(images) if images else 0
        if ratio > 0.8:
            score += 2
        elif ratio > 0.5:
            score += 1

    # Schema markup
    if 'schema.org' in html or 'application/ld+json' in html:
        score += 2

    # Canonical URL
    if soup.find('link', attrs={'rel': 'canonical'}):
        score += 1

    return max(0, min(15, score))


def score_cta_clarity(soup, html: str) -> int:
    """Score call-to-action clarity 0-15."""
    score = 0

    # Look for CTA buttons/links
    cta_words = ['call now', 'get a quote', 'book now', 'schedule', 'contact us', 'free estimate',
                 'get started', 'request', 'buy now', 'order now', 'sign up', 'learn more',
                 'free consultation', 'call today', 'book appointment']

    buttons = soup.find_all(['button', 'a'])
    cta_found = 0
    for btn in buttons:
        text = btn.get_text().lower().strip()
        classes = ' '.join(btn.get('class', []))
        if any(cta in text for cta in cta_words) or 'btn' in classes or 'button' in classes or 'cta' in classes:
            cta_found += 1

    if cta_found >= 3:
        score += 8
    elif cta_found >= 2:
        score += 6
    elif cta_found >= 1:
        score += 3

    # Check for prominent phone number
    phone_pattern = r'[\(]?\d{3}[\)]?[-.\s]?\d{3}[-.\s]?\d{4}'
    if re.search(phone_pattern, html):
        score += 4

    # Check for form
    forms = soup.find_all('form')
    if forms:
        score += 3

    return max(0, min(15, score))


def score_contact_clarity(soup, html: str) -> int:
    """Score contact information clarity 0-15."""
    score = 0

    # Phone number
    phone_pattern = r'[\(]?\d{3}[\)]?[-.\s]?\d{3}[-.\s]?\d{4}'
    if re.search(phone_pattern, html):
        score += 4

    # Email
    email_pattern = r'[a-zA-Z0-9._%+-]+@[a-zA-Z0-9.-]+\.[a-zA-Z]{2,}'
    if re.search(email_pattern, html):
        score += 3

    # Physical address
    address_words = ['street', 'avenue', 'road', 'blvd', 'suite', 'floor', 'zip']
    if any(w in html.lower() for w in address_words):
        score += 2

    # Contact page link
    links = soup.find_all('a')
    contact_link = any('contact' in (a.get('href', '') + a.get_text()).lower() for a in links)
    if contact_link:
        score += 2

    # Google Maps embed
    if 'maps.google' in html or 'google.com/maps' in html or 'maps/embed' in html:
        score += 2

    # Hours of operation
    hours_words = ['hours', 'open', 'monday', 'tuesday', 'am', 'pm', 'schedule']
    if sum(1 for w in hours_words if w in html.lower()) >= 2:
        score += 2

    return max(0, min(15, score))


def generate_issues(scores: dict, soup, html: str, load_time: float) -> list:
    """Generate list of issues found."""
    issues = []

    if scores.get("mobile_friendliness", 0) < 8:
        issues.append("Poor mobile optimization - site may not display well on phones")
    if scores.get("design_quality", 0) < 8:
        issues.append("Outdated or amateur design that may hurt credibility")
    if scores.get("speed", 0) < 8:
        issues.append(f"Slow loading speed ({load_time:.1f}s) - visitors may leave before page loads")
    if scores.get("trust_signals", 0) < 5:
        issues.append("Missing trust signals - no reviews, testimonials, or certifications visible")
    if scores.get("seo", 0) < 8:
        issues.append("Poor SEO fundamentals - business may not appear in Google searches")
    if scores.get("cta_clarity", 0) < 8:
        issues.append("Unclear calls-to-action - visitors don't know what to do next")
    if scores.get("contact_clarity", 0) < 8:
        issues.append("Contact information is hard to find or incomplete")

    return issues


def generate_recommendations(scores: dict) -> list:
    """Generate recommendations based on scores."""
    recs = []

    if scores.get("mobile_friendliness", 0) < 10:
        recs.append("Build a fully responsive mobile-first website")
    if scores.get("design_quality", 0) < 10:
        recs.append("Modern professional redesign with clean typography and imagery")
    if scores.get("speed", 0) < 10:
        recs.append("Optimize for fast loading with modern hosting and clean code")
    if scores.get("trust_signals", 0) < 7:
        recs.append("Add customer testimonials, ratings, and trust badges")
    if scores.get("seo", 0) < 10:
        recs.append("Implement proper SEO with meta tags, headers, and structured data")
    if scores.get("cta_clarity", 0) < 10:
        recs.append("Add clear CTAs like 'Get a Free Quote' and 'Call Now' buttons")
    if scores.get("contact_clarity", 0) < 10:
        recs.append("Make contact info prominent with phone, email, address, and map")

    return recs


def generate_summary(result: dict) -> str:
    """Generate a readable summary of the analysis."""
    grade = result["grade"]
    total = result["total_score"]
    name = result.get("business_name", "This business")

    if grade == "N/A":
        return f"{name} has no website. This represents a significant missed opportunity for online visibility and customer acquisition."

    severity = {
        "A": "good shape overall, with minor improvements possible",
        "B": "decent but has notable areas for improvement",
        "C": "below average with significant issues hurting their online presence",
        "D": "poor quality and likely costing the business customers",
        "F": "very poor quality and urgently needs replacement"
    }

    summary = f"{name}'s website scored {total}/100 (Grade: {grade}). "
    summary += f"The site is in {severity.get(grade, 'poor condition')}. "

    issues = result.get("issues", [])
    if issues:
        summary += f"Key issues: {'; '.join(issues[:3])}."

    return summary


def analyze_leads(leads_file: str = None) -> list:
    """Analyze all leads from a JSON file."""
    if not leads_file:
        leads_file = LEADS_DIR / "all_leads.json"

    leads_path = Path(leads_file)
    if not leads_path.exists():
        print(f"[!] Leads file not found: {leads_path}")
        return []

    with open(leads_path, 'r', encoding='utf-8') as f:
        leads = json.load(f)

    analyses = []
    for i, lead in enumerate(leads):
        print(f"\n[{i+1}/{len(leads)}] Analyzing: {lead['business_name']}")

        if lead.get('flag_no_website') or not lead.get('website'):
            analysis = {
                "url": "",
                "business_name": lead['business_name'],
                "analyzed_at": datetime.now().isoformat(),
                "reachable": False,
                "scores": {
                    "mobile_friendliness": 0, "design_quality": 0, "speed": 0,
                    "trust_signals": 0, "seo": 0, "cta_clarity": 0, "contact_clarity": 0
                },
                "total_score": 0,
                "max_score": 100,
                "grade": "N/A",
                "issues": ["No website exists"],
                "recommendations": [
                    "Build a professional responsive website",
                    "Add clear service descriptions and pricing",
                    "Include customer testimonials and reviews",
                    "Implement SEO for local search visibility",
                    "Add clear calls-to-action and contact info"
                ],
                "summary": f"{lead['business_name']} has no website. This is a critical gap in their online presence."
            }
        else:
            analysis = analyze_website(lead['website'], lead['business_name'])

        analysis["lead_id"] = lead.get("id", "")
        analysis["category"] = lead.get("category", "")
        analysis["priority"] = determine_priority(analysis)
        analyses.append(analysis)

        # Save individual analysis
        safe_name = re.sub(r'[^\w\s-]', '', lead['business_name']).strip().replace(' ', '_').lower()
        analysis_path = ANALYSIS_DIR / f"analysis_{safe_name}.json"
        with open(analysis_path, 'w', encoding='utf-8') as f:
            json.dump(analysis, f, indent=2)

        print(f"  Score: {analysis['total_score']}/100 (Grade: {analysis['grade']}) - Priority: {analysis['priority']}")

    # Save all analyses
    all_path = ANALYSIS_DIR / "all_analyses.json"
    with open(all_path, 'w', encoding='utf-8') as f:
        json.dump(analyses, f, indent=2)
    print(f"\n[+] All analyses saved to {all_path}")

    return analyses


def determine_priority(analysis: dict) -> str:
    """Determine lead priority based on analysis."""
    score = analysis.get("total_score", 0)
    grade = analysis.get("grade", "F")

    if grade == "N/A" or score == 0:
        return "critical"  # No website at all
    elif score < 30:
        return "high"  # Very poor website
    elif score < 50:
        return "medium"  # Below average
    elif score < 70:
        return "low"  # Decent but improvable
    else:
        return "skip"  # Good enough, not a strong lead


if __name__ == "__main__":
    import argparse
    parser = argparse.ArgumentParser(description="Analyze website quality for leads")
    parser.add_argument("--url", help="Analyze a single URL")
    parser.add_argument("--leads-file", help="Path to leads JSON file")
    parser.add_argument("--name", default="", help="Business name for single URL analysis")
    args = parser.parse_args()

    if args.url:
        result = analyze_website(args.url, args.name)
        print(json.dumps(result, indent=2))
    else:
        analyze_leads(args.leads_file)
