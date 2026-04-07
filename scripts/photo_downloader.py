#!/usr/bin/env python
"""
Photo Downloader
Downloads business photos from Google Places API for use in generated websites.
"""
import os
import sys
import json
import re
import requests
import time
from pathlib import Path
from datetime import datetime

sys.path.insert(0, str(Path(__file__).parent.parent))
from config.settings import *


def get_place_photos(place_id: str, api_key: str = None, max_photos: int = 10) -> list:
    """Get photo references for a place from Google Places API."""
    key = api_key or GOOGLE_PLACES_API_KEY
    if not key:
        return []

    url = "https://maps.googleapis.com/maps/api/place/details/json"
    params = {
        "place_id": place_id,
        "fields": "photos,name",
        "key": key
    }

    try:
        resp = requests.get(url, params=params, timeout=10)
        data = resp.json()
        result = data.get("result", {})
        photos = result.get("photos", [])
        return photos[:max_photos]
    except Exception as e:
        print(f"[!] Error fetching photos for {place_id}: {e}")
        return []


def download_photo(photo_name: str, output_path: str, max_width: int = 1200, api_key: str = None) -> bool:
    """Download a single photo from Google Places API (New) v1."""
    key = api_key or GOOGLE_PLACES_API_KEY
    if not key:
        return False

    # New API: photo_name is like "places/PLACE_ID/photos/PHOTO_REF"
    url = f"https://places.googleapis.com/v1/{photo_name}/media"
    params = {
        "maxWidthPx": max_width,
        "key": key
    }

    try:
        resp = requests.get(url, params=params, timeout=15, stream=True)
        if resp.status_code == 200:
            with open(output_path, 'wb') as f:
                for chunk in resp.iter_content(1024):
                    f.write(chunk)
            return True
        else:
            print(f"[!] Photo download failed with status {resp.status_code}")
            return False
    except Exception as e:
        print(f"[!] Error downloading photo: {e}")
        return False


def download_business_photos(lead: dict, api_key: str = None) -> dict:
    """Download all available photos for a business and organize them."""
    place_id = lead.get("id", "")
    business_name = lead.get("business_name", "Unknown")

    # Create output directory
    safe_name = re.sub(r'[^\w\s-]', '', business_name).strip().replace(' ', '_').lower()
    assets_dir = GENERATED_SITES_DIR / safe_name / "assets" / "images"
    assets_dir.mkdir(parents=True, exist_ok=True)

    photo_manifest = {
        "business_name": business_name,
        "place_id": place_id,
        "downloaded_at": datetime.now().isoformat(),
        "photos": []
    }

    if not place_id or place_id.startswith("mock_"):
        print(f"  [i] Skipping photo download for mock lead: {business_name}")
        return photo_manifest

    # Use photos_meta from lead data (already fetched during discovery)
    photos = lead.get("photos_meta", [])
    if not photos:
        # Fallback: try fetching from API
        photos = get_place_photos(place_id, api_key)

    if not photos:
        print(f"  [i] No photos found for {business_name}")
        return photo_manifest

    print(f"  [+] Found {len(photos)} photos for {business_name}")

    for i, photo in enumerate(photos):
        # New API format: photo has "name" field like "places/xxx/photos/yyy"
        ref = photo.get("name", photo.get("photo_reference", ""))
        if not ref:
            continue

        # Determine photo purpose based on index
        if i == 0:
            filename = "hero.jpg"
            purpose = "hero"
            width = 1920
        elif i == 1:
            filename = "about.jpg"
            purpose = "about"
            width = 800
        elif i == 2:
            filename = "logo_candidate.jpg"
            purpose = "logo"
            width = 400
        else:
            filename = f"gallery_{i-2}.jpg"
            purpose = "gallery"
            width = 800

        output_path = assets_dir / filename

        success = download_photo(ref, str(output_path), max_width=width, api_key=api_key)

        if success:
            photo_info = {
                "filename": filename,
                "purpose": purpose,
                "path": str(output_path),
                "relative_path": f"assets/images/{filename}",
                "attributions": photo.get("html_attributions", []),
                "width": photo.get("width", 0),
                "height": photo.get("height", 0)
            }
            photo_manifest["photos"].append(photo_info)
            print(f"    [{purpose}] Downloaded: {filename}")

        time.sleep(0.2)  # Rate limiting

    # Save manifest
    manifest_path = GENERATED_SITES_DIR / safe_name / "assets" / "photo_manifest.json"
    with open(manifest_path, 'w') as f:
        json.dump(photo_manifest, f, indent=2)

    return photo_manifest


def download_all_photos(leads_file: str = None):
    """Download photos for all leads."""
    leads_path = Path(leads_file) if leads_file else LEADS_DIR / "all_leads.json"

    if not leads_path.exists():
        print(f"[!] Leads file not found: {leads_path}")
        return

    with open(leads_path, 'r', encoding='utf-8') as f:
        leads = json.load(f)

    total = 0
    for lead in leads:
        if lead.get("flag_no_website") or lead.get("priority") in ["critical", "high"]:
            print(f"\n[{total+1}] Downloading photos for: {lead['business_name']}")
            manifest = download_business_photos(lead)
            total += len(manifest.get("photos", []))

    print(f"\n[+] Downloaded {total} photos total")


if __name__ == "__main__":
    import argparse
    parser = argparse.ArgumentParser(description="Download business photos")
    parser.add_argument("--leads-file", help="Path to leads JSON")
    args = parser.parse_args()
    download_all_photos(args.leads_file)
