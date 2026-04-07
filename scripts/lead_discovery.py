#!/usr/bin/env python
"""
Lead Discovery Module
Finds local businesses with weak or missing websites using Google Places API.
"""
import os
import sys
import json
import csv
import time
import requests
from pathlib import Path
from datetime import datetime

# Add parent dir to path
sys.path.insert(0, str(Path(__file__).parent.parent))
from config.settings import *


def search_businesses(category: str, city: str, state: str = "", api_key: str = None) -> list:
    """Search for businesses using Google Places API (New) - v1 Text Search."""
    key = api_key or GOOGLE_PLACES_API_KEY
    if not key or key == 'your_google_places_api_key_here':
        print("[!] No Google Places API key configured. Using mock data.")
        return generate_mock_leads(category, city)

    query = f"{category} in {city}" + (f", {state}" if state else "")
    url = "https://places.googleapis.com/v1/places:searchText"

    headers = {
        "Content-Type": "application/json",
        "X-Goog-Api-Key": key,
        "X-Goog-FieldMask": "places.id,places.displayName,places.formattedAddress,places.nationalPhoneNumber,places.websiteUri,places.googleMapsUri,places.rating,places.userRatingCount,places.businessStatus,places.types,places.reviews,places.photos"
    }

    body = {
        "textQuery": query,
        "maxResultCount": 20
    }

    all_results = []
    try:
        resp = requests.post(url, headers=headers, json=body, timeout=15)
        data = resp.json()

        if "error" in data:
            print(f"[!] API error: {data['error'].get('message', 'Unknown error')}")
            print(f"    Falling back to mock data.")
            return generate_mock_leads(category, city)

        places = data.get("places", [])

        # Convert new API format to a common format
        for place in places:
            result = {
                "place_id": place.get("id", ""),
                "name": place.get("displayName", {}).get("text", "Unknown"),
                "formatted_address": place.get("formattedAddress", ""),
                "phone": place.get("nationalPhoneNumber", ""),
                "website": place.get("websiteUri", ""),
                "google_maps_url": place.get("googleMapsUri", ""),
                "rating": place.get("rating", 0),
                "user_ratings_total": place.get("userRatingCount", 0),
                "business_status": place.get("businessStatus", "OPERATIONAL"),
                "types": place.get("types", []),
                "photos": place.get("photos", []),
                "reviews": []
            }

            # Convert reviews from new API format
            for review in place.get("reviews", []):
                result["reviews"].append({
                    "author_name": review.get("authorAttribution", {}).get("displayName", "Customer"),
                    "rating": review.get("rating", 5),
                    "text": review.get("text", {}).get("text", ""),
                    "relative_time_description": review.get("relativePublishTimeDescription", ""),
                    "profile_photo_url": review.get("authorAttribution", {}).get("photoUri", "")
                })

            all_results.append(result)

    except Exception as e:
        print(f"[!] Error calling Places API: {e}")
        print(f"    Falling back to mock data.")
        return generate_mock_leads(category, city)

    return all_results


def get_place_details(place_id: str, api_key: str = None) -> dict:
    """Get detailed info for a specific place using Places API (New) v1."""
    key = api_key or GOOGLE_PLACES_API_KEY
    url = f"https://places.googleapis.com/v1/places/{place_id}"

    headers = {
        "Content-Type": "application/json",
        "X-Goog-Api-Key": key,
        "X-Goog-FieldMask": "id,displayName,formattedAddress,nationalPhoneNumber,websiteUri,googleMapsUri,rating,userRatingCount,businessStatus,reviews,photos"
    }
    try:
        resp = requests.get(url, headers=headers, timeout=10)
        data = resp.json()
        return {
            "name": data.get("displayName", {}).get("text", ""),
            "formatted_address": data.get("formattedAddress", ""),
            "formatted_phone_number": data.get("nationalPhoneNumber", ""),
            "website": data.get("websiteUri", ""),
            "url": data.get("googleMapsUri", ""),
            "rating": data.get("rating", 0),
            "user_ratings_total": data.get("userRatingCount", 0),
            "business_status": data.get("businessStatus", "OPERATIONAL"),
            "reviews": data.get("reviews", []),
            "photos": data.get("photos", [])
        }
    except Exception as e:
        print(f"[!] Error getting place details: {e}")
        return {}


def process_leads(raw_results: list, category: str, city: str, api_key: str = None) -> list:
    """Process raw Places results into structured leads with quality flags."""
    leads = []

    for place in raw_results:
        place_id = place.get("place_id", "")
        website = place.get("website", "")
        has_website = bool(website)

        # Photos metadata (for later downloading)
        photos_meta = place.get("photos", [])

        lead = {
            "id": place_id or f"lead_{int(time.time())}_{len(leads)}",
            "business_name": place.get("name", "Unknown"),
            "category": category,
            "search_city": city,
            "address": place.get("formatted_address", ""),
            "phone": place.get("phone", ""),
            "website": website,
            "google_maps_url": place.get("google_maps_url", ""),
            "rating": place.get("rating", 0),
            "review_count": place.get("user_ratings_total", 0),
            "has_website": has_website,
            "flag_no_website": not has_website,
            "flag_needs_analysis": has_website,
            "business_status": place.get("business_status", "OPERATIONAL"),
            "reviews": place.get("reviews", []),
            "photos_meta": photos_meta,
            "discovered_at": datetime.now().isoformat(),
            "status": "new",
            "priority": "high" if not has_website else "medium",
            "notes": "No website found - high priority lead" if not has_website else "Has website - needs quality analysis"
        }

        leads.append(lead)
        print(f"  [+] {lead['business_name']} - {'NO WEBSITE' if not has_website else website}")

    return leads


def generate_mock_leads(category: str, city: str) -> list:
    """Generate realistic mock data for testing without API key."""
    mock_businesses = {
        "plumbing": [
            {"name": f"{city} Pro Plumbing", "formatted_address": f"123 Main St, {city}", "rating": 4.2, "user_ratings_total": 45, "place_id": "mock_plumb_001", "business_status": "OPERATIONAL"},
            {"name": f"Quick Fix Plumbing & Drain", "formatted_address": f"456 Oak Ave, {city}", "rating": 3.8, "user_ratings_total": 23, "place_id": "mock_plumb_002", "website": "http://quickfixplumbing-old.weebly.com", "business_status": "OPERATIONAL"},
            {"name": f"A1 Emergency Plumbers", "formatted_address": f"789 Elm St, {city}", "rating": 4.5, "user_ratings_total": 89, "place_id": "mock_plumb_003", "business_status": "OPERATIONAL"},
            {"name": f"Dave's Drain Service", "formatted_address": f"321 Pine Rd, {city}", "rating": 4.0, "user_ratings_total": 12, "place_id": "mock_plumb_004", "business_status": "OPERATIONAL"},
            {"name": f"RootGuard Plumbing Solutions", "formatted_address": f"555 Cedar Ln, {city}", "rating": 3.5, "user_ratings_total": 8, "place_id": "mock_plumb_005", "website": "http://rootguard.biz", "business_status": "OPERATIONAL"},
        ],
        "roofing": [
            {"name": f"{city} Roofing Experts", "formatted_address": f"100 Roof Rd, {city}", "rating": 4.3, "user_ratings_total": 67, "place_id": "mock_roof_001", "business_status": "OPERATIONAL"},
            {"name": f"SkyShield Roofing Co", "formatted_address": f"200 Shingle Ave, {city}", "rating": 4.7, "user_ratings_total": 134, "place_id": "mock_roof_002", "website": "http://skyshieldroofing.com", "business_status": "OPERATIONAL"},
            {"name": f"Budget Roof Repair", "formatted_address": f"300 Tar Blvd, {city}", "rating": 3.2, "user_ratings_total": 5, "place_id": "mock_roof_003", "business_status": "OPERATIONAL"},
        ],
        "landscaping": [
            {"name": f"GreenScape {city}", "formatted_address": f"101 Garden Way, {city}", "rating": 4.6, "user_ratings_total": 78, "place_id": "mock_land_001", "business_status": "OPERATIONAL"},
            {"name": f"Perfect Lawn Care", "formatted_address": f"202 Grass St, {city}", "rating": 3.9, "user_ratings_total": 34, "place_id": "mock_land_002", "business_status": "OPERATIONAL"},
        ],
        "cleaning": [
            {"name": f"Sparkle Clean {city}", "formatted_address": f"111 Clean St, {city}", "rating": 4.4, "user_ratings_total": 56, "place_id": "mock_clean_001", "business_status": "OPERATIONAL"},
            {"name": f"Fresh Start Cleaning Co", "formatted_address": f"222 Mop Ave, {city}", "rating": 4.1, "user_ratings_total": 29, "place_id": "mock_clean_002", "website": "http://freshstartcleaning.wix.com", "business_status": "OPERATIONAL"},
        ],
        "barbershop": [
            {"name": f"Classic Cuts Barbershop", "formatted_address": f"150 Barber Ln, {city}", "rating": 4.8, "user_ratings_total": 203, "place_id": "mock_barb_001", "business_status": "OPERATIONAL"},
            {"name": f"The Gentleman's Chair", "formatted_address": f"250 Style Ave, {city}", "rating": 4.3, "user_ratings_total": 87, "place_id": "mock_barb_002", "business_status": "OPERATIONAL"},
        ],
        "auto_detailing": [
            {"name": f"Mirror Finish Auto Detail", "formatted_address": f"175 Shine Blvd, {city}", "rating": 4.5, "user_ratings_total": 91, "place_id": "mock_auto_001", "business_status": "OPERATIONAL"},
            {"name": f"Precision Detail Studio", "formatted_address": f"275 Wax Way, {city}", "rating": 4.0, "user_ratings_total": 42, "place_id": "mock_auto_002", "website": "http://precisiondetail-studio.blogspot.com", "business_status": "OPERATIONAL"},
        ],
        "restaurant": [
            {"name": f"Mama Rosa's Kitchen", "formatted_address": f"500 Food Court, {city}", "rating": 4.6, "user_ratings_total": 312, "place_id": "mock_rest_001", "business_status": "OPERATIONAL"},
            {"name": f"The Local Grill", "formatted_address": f"600 Flame Ave, {city}", "rating": 4.2, "user_ratings_total": 178, "place_id": "mock_rest_002", "business_status": "OPERATIONAL"},
        ],
        "dental": [
            {"name": f"{city} Family Dental", "formatted_address": f"800 Smile Dr, {city}", "rating": 4.4, "user_ratings_total": 156, "place_id": "mock_dent_001", "website": "http://cityfamilydental.com", "business_status": "OPERATIONAL"},
            {"name": f"Bright Smile Dentistry", "formatted_address": f"900 Tooth Ln, {city}", "rating": 4.1, "user_ratings_total": 67, "place_id": "mock_dent_002", "business_status": "OPERATIONAL"},
        ],
    }

    # Return businesses for the category, or a generic set
    cat_key = category.lower().replace(" ", "_")
    businesses = mock_businesses.get(cat_key, mock_businesses.get("plumbing", []))

    # Add mock reviews
    mock_reviews = [
        {"author_name": "John D.", "rating": 5, "text": "Excellent service! Very professional and on time.", "time": 1700000000, "relative_time_description": "2 months ago"},
        {"author_name": "Sarah M.", "rating": 4, "text": "Good work, fair pricing. Would recommend to friends.", "time": 1700100000, "relative_time_description": "2 months ago"},
        {"author_name": "Mike R.", "rating": 5, "text": "Best in the area. They went above and beyond.", "time": 1700200000, "relative_time_description": "1 month ago"},
        {"author_name": "Lisa K.", "rating": 3, "text": "Decent service but took longer than expected.", "time": 1700300000, "relative_time_description": "3 weeks ago"},
        {"author_name": "Tom B.", "rating": 5, "text": "Highly professional. Will definitely use again.", "time": 1700400000, "relative_time_description": "2 weeks ago"},
    ]

    for biz in businesses:
        biz["reviews"] = mock_reviews[:3] if not biz.get("website") else mock_reviews[:2]

    return businesses


def save_leads(leads: list, category: str, city: str):
    """Save leads to CSV and JSON files."""
    timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
    safe_cat = category.replace(" ", "_").lower()
    safe_city = city.replace(" ", "_").lower()
    base_name = f"leads_{safe_cat}_{safe_city}_{timestamp}"

    # Save JSON
    json_path = LEADS_DIR / f"{base_name}.json"
    with open(json_path, 'w', encoding='utf-8') as f:
        json.dump(leads, f, indent=2, ensure_ascii=False)
    print(f"\n[+] Saved {len(leads)} leads to {json_path}")

    # Save CSV
    csv_path = LEADS_DIR / f"{base_name}.csv"
    if leads:
        # Flatten for CSV (exclude reviews)
        csv_fields = [k for k in leads[0].keys() if k != 'reviews']
        with open(csv_path, 'w', newline='', encoding='utf-8') as f:
            writer = csv.DictWriter(f, fieldnames=csv_fields)
            writer.writeheader()
            for lead in leads:
                row = {k: v for k, v in lead.items() if k != 'reviews'}
                writer.writerow(row)
        print(f"[+] Saved CSV to {csv_path}")

    # Also update/create master leads file
    master_json = LEADS_DIR / "all_leads.json"
    existing = []
    if master_json.exists():
        with open(master_json, 'r', encoding='utf-8') as f:
            existing = json.load(f)

    # Merge, avoiding duplicates by place_id
    existing_ids = {l['id'] for l in existing}
    for lead in leads:
        if lead['id'] not in existing_ids:
            existing.append(lead)

    with open(master_json, 'w', encoding='utf-8') as f:
        json.dump(existing, f, indent=2, ensure_ascii=False)
    print(f"[+] Master leads file updated: {len(existing)} total leads")

    return json_path, csv_path


def discover_leads(categories: list = None, cities: list = None, states: list = None):
    """Main discovery function - searches for businesses across categories and cities."""
    if not categories:
        categories = ["plumbing", "roofing", "landscaping", "cleaning"]
    if not cities:
        cities = ["Austin"]
    if not states:
        states = ["TX"]

    all_leads = []

    for city_idx, city in enumerate(cities):
        state = states[city_idx] if city_idx < len(states) else ""
        for category in categories:
            print(f"\n{'='*60}")
            print(f"Searching: {category} in {city}, {state}")
            print(f"{'='*60}")

            raw = search_businesses(category, city, state)
            print(f"  Found {len(raw)} raw results")

            leads = process_leads(raw, category, city)

            no_site = sum(1 for l in leads if l['flag_no_website'])
            print(f"  Processed {len(leads)} leads ({no_site} without websites)")

            save_leads(leads, category, city)
            all_leads.extend(leads)

    # Summary
    print(f"\n{'='*60}")
    print(f"DISCOVERY COMPLETE")
    print(f"{'='*60}")
    print(f"Total leads found: {len(all_leads)}")
    print(f"Without websites: {sum(1 for l in all_leads if l['flag_no_website'])}")
    print(f"With websites (need analysis): {sum(1 for l in all_leads if l['flag_needs_analysis'])}")

    return all_leads


if __name__ == "__main__":
    import argparse
    parser = argparse.ArgumentParser(description="Discover local business leads")
    parser.add_argument("--categories", nargs="+", default=["plumbing", "roofing", "landscaping", "cleaning", "barbershop", "auto detailing", "restaurant", "dental"])
    parser.add_argument("--cities", nargs="+", default=["Austin"])
    parser.add_argument("--states", nargs="+", default=["TX"])
    args = parser.parse_args()

    discover_leads(args.categories, args.cities, args.states)
