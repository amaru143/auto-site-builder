#!/usr/bin/env python
"""
Website Generator
Generates polished, professional websites from lead data using Jinja2 templates.
Supports multiple business types with tailored content.
"""
import os
import sys
import json
import re
import shutil
from pathlib import Path
from datetime import datetime

sys.path.insert(0, str(Path(__file__).parent.parent))
from config.settings import *

try:
    from jinja2 import Environment, FileSystemLoader
except ImportError:
    print("[!] Jinja2 not installed. Run: pip install jinja2")
    sys.exit(1)


# Business type configurations
BUSINESS_CONFIGS = {
    "plumbing": {
        "icon": "🔧",
        "hero_headline": "Professional Plumbing Services You Can Trust",
        "hero_subheadline": "Fast, reliable plumbing solutions for your home and business",
        "primary_color": "#1e40af",
        "secondary_color": "#3b82f6",
        "accent_color": "#dbeafe",
        "gradient_from": "#1e3a5f",
        "gradient_to": "#1e40af",
        "services": [
            {"name": "Emergency Repairs", "description": "24/7 emergency plumbing service. Burst pipes, leaks, and clogs fixed fast.", "icon": "🚨"},
            {"name": "Drain Cleaning", "description": "Professional drain cleaning and unclogging for sinks, tubs, and main lines.", "icon": "🚿"},
            {"name": "Water Heater Service", "description": "Installation, repair, and maintenance of all water heater types.", "icon": "🔥"},
            {"name": "Pipe Repair & Replacement", "description": "Expert pipe repair, repiping, and replacement services.", "icon": "🔧"},
            {"name": "Bathroom Remodeling", "description": "Complete bathroom plumbing for remodels and new construction.", "icon": "🛁"},
            {"name": "Sewer Line Service", "description": "Sewer line inspection, repair, and replacement with modern techniques.", "icon": "🏗️"}
        ],
        "cta_text": "Get a Free Estimate",
        "about_template": "{name} has been providing reliable plumbing services to {city} and surrounding areas. Our team of licensed, insured plumbers is committed to delivering quality workmanship at fair prices. Whether it's a leaky faucet or a complete repiping project, we treat every job with the same level of professionalism and care.",
        "seo_keywords": "plumber, plumbing, drain cleaning, water heater, pipe repair, emergency plumber",
        "cta_hero": "Get a Free Estimate",
        "cta_secondary": "Emergency Service",
        "trust_badges": ["Licensed & Insured", "24/7 Emergency", "Free Estimates"],
        "special_sections": []
    },
    "roofing": {
        "icon": "🏠",
        "hero_headline": "Expert Roofing — Built to Last",
        "hero_subheadline": "Trusted roofing solutions for residential and commercial properties",
        "primary_color": "#92400e",
        "secondary_color": "#d97706",
        "accent_color": "#fef3c7",
        "gradient_from": "#78350f",
        "gradient_to": "#92400e",
        "services": [
            {"name": "Roof Replacement", "description": "Complete roof replacement with premium materials and expert installation.", "icon": "🏗️"},
            {"name": "Roof Repair", "description": "Fast, reliable repairs for leaks, storm damage, and wear.", "icon": "🔨"},
            {"name": "Roof Inspection", "description": "Thorough inspections to catch problems early and extend roof life.", "icon": "🔍"},
            {"name": "Storm Damage Repair", "description": "Emergency storm damage repair and insurance claim assistance.", "icon": "⛈️"},
            {"name": "Gutter Installation", "description": "Seamless gutter installation and repair to protect your home.", "icon": "🏠"},
            {"name": "Commercial Roofing", "description": "Flat roof, TPO, EPDM, and commercial roofing solutions.", "icon": "🏢"}
        ],
        "cta_text": "Get a Free Roof Inspection",
        "about_template": "{name} is a trusted roofing contractor serving {city} and the surrounding area. We specialize in high-quality roof installations, repairs, and inspections. Our experienced team uses only the best materials and techniques to ensure your roof protects your home for years to come.",
        "seo_keywords": "roofing, roof repair, roof replacement, roofer, storm damage, gutter installation",
        "cta_hero": "Get a Free Roof Inspection",
        "cta_secondary": "Storm Damage?",
        "trust_badges": ["Licensed & Insured", "Free Inspections", "Warranty Included"],
        "special_sections": [{"type": "before_after", "title": "Our Work"}]
    },
    "landscaping": {
        "icon": "🌿",
        "hero_headline": "Transform Your Outdoor Space",
        "hero_subheadline": "Professional landscaping and lawn care that makes your property shine",
        "primary_color": "#166534",
        "secondary_color": "#22c55e",
        "accent_color": "#dcfce7",
        "gradient_from": "#14532d",
        "gradient_to": "#166534",
        "services": [
            {"name": "Lawn Maintenance", "description": "Regular mowing, edging, and lawn care to keep your yard pristine.", "icon": "🌱"},
            {"name": "Landscape Design", "description": "Custom landscape design to transform your outdoor living space.", "icon": "🎨"},
            {"name": "Tree & Shrub Care", "description": "Professional pruning, trimming, and tree removal services.", "icon": "🌳"},
            {"name": "Irrigation Systems", "description": "Sprinkler installation, repair, and smart irrigation solutions.", "icon": "💧"},
            {"name": "Hardscaping", "description": "Patios, walkways, retaining walls, and outdoor living areas.", "icon": "🧱"},
            {"name": "Seasonal Cleanup", "description": "Spring and fall cleanup, mulching, and bed maintenance.", "icon": "🍂"}
        ],
        "cta_text": "Get a Free Consultation",
        "about_template": "{name} provides professional landscaping services to homes and businesses in {city}. From regular lawn maintenance to complete landscape transformations, our skilled team creates beautiful outdoor spaces that increase property value and curb appeal.",
        "seo_keywords": "landscaping, lawn care, landscape design, tree service, irrigation, hardscaping",
        "cta_hero": "Get a Free Consultation",
        "cta_secondary": "See Our Work",
        "trust_badges": ["Licensed & Insured", "Eco-Friendly", "Satisfaction Guaranteed"]
    },
    "cleaning": {
        "icon": "✨",
        "hero_headline": "Spotless Cleaning, Every Time",
        "hero_subheadline": "Professional cleaning services for homes and offices",
        "primary_color": "#0e7490",
        "secondary_color": "#06b6d4",
        "accent_color": "#cffafe",
        "gradient_from": "#164e63",
        "gradient_to": "#0e7490",
        "services": [
            {"name": "Residential Cleaning", "description": "Thorough home cleaning tailored to your needs and schedule.", "icon": "🏡"},
            {"name": "Deep Cleaning", "description": "Intensive deep cleaning for kitchens, bathrooms, and living spaces.", "icon": "🧽"},
            {"name": "Office Cleaning", "description": "Professional commercial and office cleaning services.", "icon": "🏢"},
            {"name": "Move-In/Out Cleaning", "description": "Comprehensive cleaning for moving transitions.", "icon": "📦"},
            {"name": "Post-Construction", "description": "Detailed cleanup after renovation or construction projects.", "icon": "🏗️"},
            {"name": "Window Cleaning", "description": "Crystal-clear window cleaning for homes and businesses.", "icon": "🪟"}
        ],
        "cta_text": "Book Your Cleaning",
        "about_template": "{name} delivers professional cleaning services to homes and businesses across {city}. Our trained, insured cleaning specialists use eco-friendly products and proven methods to make every space spotless. We're committed to your satisfaction on every visit.",
        "seo_keywords": "cleaning service, house cleaning, office cleaning, deep cleaning, maid service",
        "cta_hero": "Book Your Cleaning",
        "cta_secondary": "Get a Quote",
        "trust_badges": ["Bonded & Insured", "Eco-Friendly Products", "Satisfaction Guaranteed"]
    },
    "barbershop": {
        "icon": "💈",
        "hero_headline": "Premium Cuts & Classic Style",
        "hero_subheadline": "Where tradition meets modern grooming excellence",
        "primary_color": "#1f2937",
        "secondary_color": "#6b7280",
        "accent_color": "#f3f4f6",
        "gradient_from": "#111827",
        "gradient_to": "#1f2937",
        "services": [
            {"name": "Haircuts", "description": "Classic and modern haircuts tailored to your style.", "icon": "✂️"},
            {"name": "Beard Trim & Shaping", "description": "Expert beard grooming, trimming, and shaping.", "icon": "🧔"},
            {"name": "Hot Towel Shave", "description": "Luxurious straight razor shave with hot towel treatment.", "icon": "🪒"},
            {"name": "Kids' Cuts", "description": "Friendly, patient haircuts for children of all ages.", "icon": "👦"},
            {"name": "Hair Coloring", "description": "Professional hair coloring and gray blending services.", "icon": "🎨"},
            {"name": "Scalp Treatment", "description": "Relaxing scalp massage and treatment services.", "icon": "💆"}
        ],
        "cta_text": "Book an Appointment",
        "about_template": "{name} is a premier barbershop in {city} dedicated to the art of men's grooming. Our skilled barbers combine time-honored techniques with modern styles to deliver the perfect cut every time. Step into our shop and experience the difference.",
        "seo_keywords": "barbershop, haircut, beard trim, men's grooming, barber, hot shave",
        "cta_hero": "Book an Appointment",
        "cta_secondary": "Walk-Ins Welcome",
        "trust_badges": ["Master Barbers", "Walk-Ins Welcome", "Premium Products"],
        "special_sections": [{"type": "pricing_menu", "title": "Services & Pricing", "items": [{"name": "Classic Haircut", "price": "$25"}, {"name": "Beard Trim", "price": "$15"}, {"name": "Hot Towel Shave", "price": "$30"}, {"name": "Haircut + Beard", "price": "$35"}, {"name": "Kids Cut", "price": "$18"}, {"name": "Hair Color", "price": "$45+"}]}]
    },
    "auto_detailing": {
        "icon": "🚗",
        "hero_headline": "Showroom-Quality Detailing",
        "hero_subheadline": "Professional auto detailing that makes your vehicle look brand new",
        "primary_color": "#7c2d12",
        "secondary_color": "#ea580c",
        "accent_color": "#fff7ed",
        "gradient_from": "#431407",
        "gradient_to": "#7c2d12",
        "services": [
            {"name": "Full Detail", "description": "Complete interior and exterior detailing for a like-new finish.", "icon": "✨"},
            {"name": "Paint Correction", "description": "Multi-stage paint correction to remove scratches and swirl marks.", "icon": "🎨"},
            {"name": "Ceramic Coating", "description": "Long-lasting ceramic coating for ultimate paint protection.", "icon": "🛡️"},
            {"name": "Interior Detail", "description": "Deep cleaning, conditioning, and protection of all interior surfaces.", "icon": "🪑"},
            {"name": "Exterior Wash & Wax", "description": "Hand wash and premium wax for a brilliant, protected shine.", "icon": "💎"},
            {"name": "Paint Protection Film", "description": "Invisible film to protect against chips, scratches, and road debris.", "icon": "🔒"}
        ],
        "cta_text": "Book Your Detail",
        "about_template": "{name} provides premium auto detailing services in {city}. Our certified detailing specialists use only the finest products and techniques to restore and protect your vehicle. From daily drivers to exotic cars, we treat every vehicle like it's our own.",
        "seo_keywords": "auto detailing, car detailing, paint correction, ceramic coating, car wash",
        "cta_hero": "Book Your Detail",
        "cta_secondary": "View Packages",
        "trust_badges": ["Certified Detailers", "Premium Products", "Satisfaction Guaranteed"],
        "special_sections": [{"type": "pricing_menu", "title": "Detailing Packages", "items": [{"name": "Basic Wash", "price": "$49"}, {"name": "Interior Detail", "price": "$149"}, {"name": "Full Detail", "price": "$249"}, {"name": "Paint Correction", "price": "$399"}, {"name": "Ceramic Coating", "price": "$599"}, {"name": "Ultimate Package", "price": "$899"}]}]
    },
    "restaurant": {
        "icon": "🍽️",
        "hero_headline": "Fresh Flavors, Unforgettable Dining",
        "hero_subheadline": "Experience the taste of exceptional food and warm hospitality",
        "primary_color": "#991b1b",
        "secondary_color": "#dc2626",
        "accent_color": "#fef2f2",
        "gradient_from": "#450a0a",
        "gradient_to": "#991b1b",
        "services": [
            {"name": "Dine-In", "description": "Enjoy our full menu in a warm, welcoming atmosphere.", "icon": "🍽️"},
            {"name": "Takeout & Delivery", "description": "Order online or call ahead for convenient pickup and delivery.", "icon": "📦"},
            {"name": "Catering", "description": "Full-service catering for events, parties, and corporate functions.", "icon": "🎉"},
            {"name": "Private Events", "description": "Host your special occasion in our private dining area.", "icon": "🥂"},
            {"name": "Daily Specials", "description": "Fresh daily specials featuring seasonal and local ingredients.", "icon": "⭐"},
            {"name": "Family Meals", "description": "Family-sized portions perfect for sharing at home.", "icon": "👨‍👩‍👧‍👦"}
        ],
        "cta_text": "View Menu & Order",
        "about_template": "{name} has been serving {city} with delicious food and exceptional hospitality. Our kitchen uses fresh, quality ingredients to create dishes that bring people together. Whether it's a casual lunch or a special celebration, we're here to make it memorable.",
        "seo_keywords": "restaurant, dining, catering, takeout, delivery, food",
        "cta_hero": "View Our Menu",
        "cta_secondary": "Order Online",
        "trust_badges": ["Fresh Ingredients", "Family Owned", "Dine-In & Takeout"],
        "special_sections": [{"type": "menu", "title": "Our Menu", "categories": [{"name": "Appetizers", "items": [{"name": "Appetizer 1", "price": "$8", "desc": "Delicious starter"}, {"name": "Appetizer 2", "price": "$10", "desc": "Chef's favorite"}]}, {"name": "Main Courses", "items": [{"name": "Entree 1", "price": "$16", "desc": "House specialty"}, {"name": "Entree 2", "price": "$18", "desc": "Customer favorite"}, {"name": "Entree 3", "price": "$22", "desc": "Premium selection"}]}, {"name": "Desserts", "items": [{"name": "Dessert 1", "price": "$8", "desc": "Sweet finish"}, {"name": "Dessert 2", "price": "$10", "desc": "Signature dessert"}]}]}, {"type": "hours_banner", "title": "Hours & Location"}]
    },
    "dental": {
        "icon": "🦷",
        "hero_headline": "Your Smile, Our Priority",
        "hero_subheadline": "Comprehensive dental care for the whole family",
        "primary_color": "#0369a1",
        "secondary_color": "#0ea5e9",
        "accent_color": "#e0f2fe",
        "gradient_from": "#0c4a6e",
        "gradient_to": "#0369a1",
        "services": [
            {"name": "General Dentistry", "description": "Cleanings, exams, fillings, and preventive dental care.", "icon": "🦷"},
            {"name": "Cosmetic Dentistry", "description": "Whitening, veneers, and smile makeovers for a confident smile.", "icon": "✨"},
            {"name": "Dental Implants", "description": "Permanent tooth replacement with state-of-the-art implants.", "icon": "🔩"},
            {"name": "Orthodontics", "description": "Braces and clear aligners for straighter, healthier teeth.", "icon": "😁"},
            {"name": "Emergency Dental", "description": "Same-day emergency dental care when you need it most.", "icon": "🚨"},
            {"name": "Pediatric Dentistry", "description": "Gentle, friendly dental care designed for children.", "icon": "👶"}
        ],
        "cta_text": "Schedule an Appointment",
        "about_template": "{name} provides comprehensive dental care to patients in {city} and surrounding communities. Our modern office features the latest technology, and our caring team is dedicated to making every visit comfortable. We believe everyone deserves a healthy, beautiful smile.",
        "seo_keywords": "dentist, dental care, teeth whitening, dental implants, orthodontics, family dentist",
        "cta_hero": "Schedule an Appointment",
        "cta_secondary": "New Patient? Learn More",
        "trust_badges": ["Board Certified", "Modern Technology", "Insurance Accepted"],
        "special_sections": [{"type": "insurance_banner", "title": "Insurance & Payment", "text": "We accept most major insurance plans. Flexible payment options available."}]
    }
}


def get_business_config(category: str) -> dict:
    """Get configuration for a business type."""
    cat_key = category.lower().replace(" ", "_")
    return BUSINESS_CONFIGS.get(cat_key, BUSINESS_CONFIGS["plumbing"])


def build_trust_badges(lead: dict, config: dict) -> list:
    """Build trust badges from actual business data, not generic claims."""
    badges = []
    rating = lead.get("rating", 0)
    review_count = lead.get("review_count", 0)

    # Rating-based badge (only if they actually have ratings)
    if rating >= 4.5 and review_count >= 10:
        badges.append(f"{rating}-Star Rated")
    elif rating >= 4.0 and review_count >= 5:
        badges.append(f"{rating} Stars on Google")

    # Review count badge
    if review_count >= 50:
        badges.append(f"{review_count}+ Reviews")
    elif review_count >= 10:
        badges.append(f"{review_count} Reviews")

    # Category-appropriate generic badges (safe claims)
    category = lead.get("category", "").lower()
    if category in ["plumbing", "roofing", "electrical", "hvac"]:
        badges.append("Free Estimates")
    elif category in ["cleaning", "landscaping"]:
        badges.append("Free Quotes")
    elif category in ["barbershop"]:
        badges.append("Walk-Ins Welcome")
    elif category in ["restaurant"]:
        badges.append("Dine-In & Takeout")
    elif category in ["dental"]:
        badges.append("New Patients Welcome")
    elif category in ["auto_detailing", "auto detailing"]:
        badges.append("Mobile Service Available")

    # Fill to 3 badges with safe options
    safe_fillers = ["Locally Owned", "Serving " + lead.get("search_city", "Your Area"), "Quality Service"]
    for filler in safe_fillers:
        if len(badges) >= 3:
            break
        if filler not in badges:
            badges.append(filler)

    return badges[:3]


def generate_content(lead: dict, config: dict) -> dict:
    """Generate all content for a website based on lead data."""
    name = lead.get("business_name", "Business Name")
    city = lead.get("search_city", "Your City")
    phone = lead.get("phone", "(555) 123-4567")
    address = lead.get("address", "123 Main St")
    category = lead.get("category", "service")
    rating = lead.get("rating", 4.5)
    review_count = lead.get("review_count", 0)

    # Format reviews
    raw_reviews = lead.get("reviews", [])
    reviews = []
    for r in raw_reviews[:5]:
        reviews.append({
            "author": r.get("author_name", "Customer"),
            "rating": r.get("rating", 5),
            "text": r.get("text", "Great service!"),
            "date": r.get("relative_time_description", "Recently"),
            "stars": "★" * int(r.get("rating", 5)) + "☆" * (5 - int(r.get("rating", 5)))
        })

    # If no reviews, use placeholders
    if not reviews:
        reviews = [
            {"author": "Verified Customer", "rating": 5, "text": "Outstanding service! Professional, punctual, and fairly priced. Highly recommend!", "date": "Recently", "stars": "★★★★★"},
            {"author": "Verified Customer", "rating": 5, "text": "Best in the area. They went above and beyond our expectations.", "date": "Recently", "stars": "★★★★★"},
            {"author": "Verified Customer", "rating": 4, "text": "Great experience from start to finish. Would definitely use again.", "date": "Recently", "stars": "★★★★☆"}
        ]

    about_text = config["about_template"].format(name=name, city=city)

    return {
        "business_name": name,
        "tagline": config["hero_subheadline"],
        "headline": config["hero_headline"],
        "subheadline": config["hero_subheadline"],
        "phone": phone,
        "phone_clean": re.sub(r'[^\d+]', '', phone),
        "email": lead.get("email", f"info@{re.sub(r'[^a-zA-Z0-9]', '', name).lower()}.com"),
        "address": address,
        "city": city,
        "category": category,
        "category_display": category.replace("_", " ").title(),
        "rating": rating,
        "review_count": review_count,
        "google_maps_url": lead.get("google_maps_url", "#"),
        "primary_color": config["primary_color"],
        "secondary_color": config["secondary_color"],
        "accent_color": config["accent_color"],
        "gradient_from": config["gradient_from"],
        "gradient_to": config["gradient_to"],
        "services": config["services"],
        "reviews": reviews,
        "about_text": about_text,
        "cta_text": config["cta_text"],
        "icon": config["icon"],
        "seo_title": f"{name} — Professional {category.replace('_', ' ').title()} in {city}",
        "seo_description": f"{name} provides professional {category.replace('_', ' ')} services in {city}. {config['hero_subheadline']}. Call {phone} for a free estimate.",
        "seo_keywords": config["seo_keywords"],
        "year": datetime.now().year,
        "payment_link": "",
        "setup_guide_note": "Full setup guide included after purchase",
        "business_config": config,
        # Business-specific fields
        "cta_hero": config.get("cta_hero", config.get("cta_text", "Get a Free Quote")),
        "cta_secondary": config.get("cta_secondary", "Call Now"),
        "trust_badges": build_trust_badges(lead, config),
        "special_sections": config.get("special_sections", []),
        # Photo paths (will be populated if photos exist)
        "hero_image": "",
        "about_image": "",
        "gallery_images": [],
        "has_photos": False
    }

    # Check for downloaded photos
    safe_name_check = re.sub(r'[^\w\s-]', '', name).strip().replace(' ', '_').lower()
    manifest_path = GENERATED_SITES_DIR / safe_name_check / "assets" / "photo_manifest.json"
    if manifest_path.exists():
        with open(manifest_path, 'r') as f:
            manifest = json.load(f)
        photos = manifest.get("photos", [])
        if photos:
            content["has_photos"] = True
            for p in photos:
                if p["purpose"] == "hero":
                    content["hero_image"] = p["relative_path"]
                elif p["purpose"] == "about":
                    content["about_image"] = p["relative_path"]
                elif p["purpose"] == "gallery":
                    content["gallery_images"].append(p["relative_path"])

    return content


def generate_website(lead: dict, payment_link: str = "") -> Path:
    """Generate a complete website for a lead."""
    config = get_business_config(lead.get("category", "plumbing"))
    content = generate_content(lead, config)
    content["payment_link"] = payment_link

    # Set up Jinja2
    env = Environment(loader=FileSystemLoader(str(TEMPLATES_DIR)))

    try:
        template = env.get_template("base_template.html")
    except Exception as e:
        print(f"[!] Template error: {e}")
        return None

    # Render
    html = template.render(**content)

    # Create output directory
    safe_name = re.sub(r'[^\w\s-]', '', lead['business_name']).strip().replace(' ', '_').lower()
    output_dir = GENERATED_SITES_DIR / safe_name
    output_dir.mkdir(parents=True, exist_ok=True)

    # Write index.html
    index_path = output_dir / "index.html"
    with open(index_path, 'w', encoding='utf-8') as f:
        f.write(html)

    # Create assets directory and placeholders
    assets_dir = output_dir / "assets"
    assets_dir.mkdir(exist_ok=True)

    # Create assets checklist
    checklist = f"""# Assets Needed for {lead['business_name']}

## Required Images
- [ ] Logo (PNG, transparent background, min 200x200px)
- [ ] Hero background image (1920x1080px, high quality photo related to {lead.get('category', 'business')})
- [ ] About section image (800x600px, team photo or workplace)
- [ ] Service images (6 images, 600x400px each)
- [ ] Gallery images (6-8 images, 800x600px)

## Optional Assets
- [ ] Favicon (32x32px and 180x180px)
- [ ] Social media profile images
- [ ] Video content (hero background video)
- [ ] PDF menu/brochure (if applicable)

## Image Guidelines
- Use high-quality, professional photos
- Compress for web (use TinyPNG or similar)
- Use consistent style and color grading
- Ensure images are properly licensed
"""
    with open(assets_dir / "assets_checklist.md", 'w') as f:
        f.write(checklist)

    # Create a simple SVG placeholder logo
    svg_logo = f"""<svg xmlns="http://www.w3.org/2000/svg" viewBox="0 0 200 60" fill="none">
  <text x="10" y="42" font-family="Arial, sans-serif" font-size="28" font-weight="bold" fill="{config['primary_color']}">{lead['business_name'][:20]}</text>
</svg>"""
    with open(assets_dir / "logo.svg", 'w') as f:
        f.write(svg_logo)

    print(f"[+] Generated website: {output_dir}")
    print(f"    Index: {index_path}")

    return output_dir


def generate_all_websites(leads_file: str = None):
    """Generate websites for all qualified leads."""
    leads_path = Path(leads_file) if leads_file else LEADS_DIR / "all_leads.json"

    if not leads_path.exists():
        print(f"[!] Leads file not found: {leads_path}")
        return

    with open(leads_path, 'r', encoding='utf-8') as f:
        leads = json.load(f)

    generated = 0
    for lead in leads:
        if lead.get("flag_no_website") or lead.get("priority") in ["critical", "high"]:
            print(f"\n{'='*60}")
            print(f"Generating website for: {lead['business_name']}")
            print(f"Category: {lead.get('category', 'unknown')}")
            print(f"{'='*60}")

            output = generate_website(lead)
            if output:
                generated += 1

    print(f"\n[+] Generated {generated} websites in {GENERATED_SITES_DIR}")


if __name__ == "__main__":
    import argparse
    parser = argparse.ArgumentParser(description="Generate websites for leads")
    parser.add_argument("--leads-file", help="Path to leads JSON")
    parser.add_argument("--lead-id", help="Generate for specific lead only")
    args = parser.parse_args()

    if args.lead_id:
        leads_path = Path(args.leads_file) if args.leads_file else LEADS_DIR / "all_leads.json"
        with open(leads_path, 'r') as f:
            leads = json.load(f)
        lead = next((l for l in leads if l.get('id') == args.lead_id), None)
        if lead:
            generate_website(lead)
        else:
            print(f"[!] Lead not found: {args.lead_id}")
    else:
        generate_all_websites(args.leads_file)
