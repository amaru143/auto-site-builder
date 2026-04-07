import axios from 'axios';
import * as dotenv from 'dotenv';
dotenv.config();

const API_KEY = process.env.GOOGLE_PLACES_API_KEY!;
const BASE = 'https://maps.googleapis.com/maps/api/place';

// Business types that benefit from scheduling
const SCHEDULING_CATEGORIES = new Set([
  'hair_care', 'beauty_salon', 'spa', 'barber', 'gym', 'health',
  'dentist', 'doctor', 'physiotherapist', 'veterinary_care',
  'lawyer', 'accounting', 'real_estate_agency', 'insurance_agency',
  'restaurant', 'cafe', 'bakery',
  'plumber', 'electrician', 'general_contractor', 'roofing_contractor',
  'painter', 'locksmith', 'moving_company', 'storage',
  'car_repair', 'car_wash',
  'laundry', 'dry_cleaning',
  'tutoring', 'school',
]);

// Maps Google types → our normalized industry templates
const INDUSTRY_MAP: Record<string, string> = {
  restaurant: 'food-beverage',
  cafe: 'food-beverage',
  bakery: 'food-beverage',
  bar: 'food-beverage',
  meal_delivery: 'food-beverage',
  meal_takeaway: 'food-beverage',
  hair_care: 'beauty-wellness',
  beauty_salon: 'beauty-wellness',
  spa: 'beauty-wellness',
  gym: 'beauty-wellness',
  health: 'beauty-wellness',
  barber: 'beauty-wellness',
  dentist: 'medical',
  doctor: 'medical',
  hospital: 'medical',
  physiotherapist: 'medical',
  veterinary_care: 'medical',
  pharmacy: 'medical',
  plumber: 'home-services',
  electrician: 'home-services',
  general_contractor: 'home-services',
  roofing_contractor: 'home-services',
  painter: 'home-services',
  locksmith: 'home-services',
  moving_company: 'home-services',
  lawn_care: 'home-services',
  cleaning: 'home-services',
  car_repair: 'auto',
  car_wash: 'auto',
  car_dealer: 'auto',
  lawyer: 'professional',
  accounting: 'professional',
  insurance_agency: 'professional',
  real_estate_agency: 'professional',
  finance: 'professional',
  school: 'professional',
  tutoring: 'professional',
};

function normalizeIndustry(types: string[]): string {
  for (const t of types) {
    if (INDUSTRY_MAP[t]) return INDUSTRY_MAP[t];
  }
  return 'generic';
}

function needsScheduling(types: string[]): boolean {
  return types.some(t => SCHEDULING_CATEGORIES.has(t));
}

function parseAddressParts(address: string): { city: string; state: string; zip: string } {
  // Typical format: "123 Main St, Dallas, TX 75201, USA"
  const parts = address.split(',').map(p => p.trim());
  const city = parts[1] || '';
  const stateZip = parts[2] || '';
  const stateZipParts = stateZip.trim().split(' ');
  const state = stateZipParts[0] || '';
  const zip = stateZipParts[1] || '';
  return { city, state, zip };
}

export async function getPlaceDetails(placeId: string) {
  const fields = [
    'name',
    'formatted_address',
    'formatted_phone_number',
    'website',
    'opening_hours',
    'photos',
    'rating',
    'user_ratings_total',
    'reviews',
    'geometry',
    'types',
    'business_status',
  ].join(',');

  const { data } = await axios.get(`${BASE}/details/json`, {
    params: { place_id: placeId, fields, key: API_KEY },
  });

  const p = data.result;
  if (!p || p.business_status !== 'OPERATIONAL') return null;

  // Skip if they already have a website
  if (p.website) return null;

  const types: string[] = p.types || [];
  const { city, state, zip } = parseAddressParts(p.formatted_address || '');

  // Pull up to 5 photo reference URLs
  const photos: string[] = (p.photos || []).slice(0, 5).map((ph: any) =>
    `${BASE}/photo?maxwidth=1200&photo_reference=${ph.photo_reference}&key=${API_KEY}`
  );

  // Pull top 3 review texts for testimonials
  const reviews: string[] = (p.reviews || [])
    .filter((r: any) => r.rating >= 4)
    .slice(0, 3)
    .map((r: any) => ({ text: r.text, author: r.author_name, rating: r.rating }));

  return {
    place_id: placeId,
    name: p.name,
    address: p.formatted_address,
    city,
    state,
    zip,
    phone: p.formatted_phone_number || null,
    website: null,
    category: types[0] || 'business',
    industry: normalizeIndustry(types),
    hours: p.opening_hours?.weekday_text || [],
    photos,
    rating: p.rating || null,
    review_count: p.user_ratings_total || 0,
    reviews,
    lat: p.geometry?.location?.lat,
    lng: p.geometry?.location?.lng,
    needs_scheduling: needsScheduling(types),
  };
}

export async function searchBusinessesWithoutWebsite(
  query: string,
  location: string,
  pageToken?: string
): Promise<{ results: any[]; nextPageToken?: string }> {
  const params: any = {
    query: `${query} in ${location}`,
    key: API_KEY,
    type: 'establishment',
  };
  if (pageToken) params.pagetoken = pageToken;

  const { data } = await axios.get(`${BASE}/textsearch/json`, { params });

  if (data.status !== 'OK' && data.status !== 'ZERO_RESULTS') {
    throw new Error(`Google Places error: ${data.status} — ${data.error_message || ''}`);
  }

  const results: any[] = [];

  for (const place of data.results || []) {
    // Quick check — skip if website is already in the text search result
    if (place.website) continue;

    const details = await getPlaceDetails(place.place_id);
    if (details) {
      results.push(details);
      console.log(`  ✓ ${details.name} (${details.city}, ${details.state}) — ${details.industry}`);
    }

    await sleep(250); // Stay within API rate limits
  }

  return { results, nextPageToken: data.next_page_token };
}

function sleep(ms: number) {
  return new Promise(resolve => setTimeout(resolve, ms));
}
