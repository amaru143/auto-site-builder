/**
 * Business Discovery Runner
 *
 * Usage:
 *   npm run discover -- --query "plumber" --location "Dallas, TX" --pages 3
 *   npm run discover -- --query "hair salon" --location "Phoenix, AZ"
 *
 * This will:
 * 1. Search Google Places for that business type + city
 * 2. Filter to only businesses WITHOUT a website
 * 3. Save them to Supabase with status = 'discovered'
 */

import { searchBusinessesWithoutWebsite } from './googlePlaces';
import { db } from '../db/client';
import * as dotenv from 'dotenv';
dotenv.config();

// Parse CLI args
const args = process.argv.slice(2);
function getArg(name: string): string | undefined {
  const i = args.indexOf(`--${name}`);
  return i !== -1 ? args[i + 1] : undefined;
}

const QUERY = getArg('query') || 'plumber';
const LOCATION = getArg('location') || 'Austin, TX';
const MAX_PAGES = parseInt(getArg('pages') || '2');

async function run() {
  console.log(`\nSearching for "${QUERY}" in ${LOCATION} (up to ${MAX_PAGES} pages)\n`);

  let pageToken: string | undefined;
  let page = 0;
  let totalFound = 0;
  let totalSaved = 0;

  do {
    page++;
    console.log(`--- Page ${page} ---`);

    const { results, nextPageToken } = await searchBusinessesWithoutWebsite(
      QUERY,
      LOCATION,
      pageToken
    );

    pageToken = nextPageToken;
    totalFound += results.length;

    if (results.length === 0) {
      console.log('No results without websites on this page.');
      break;
    }

    // Upsert into Supabase (skip duplicates by place_id)
    const { data, error } = await db
      .from('businesses')
      .upsert(results, { onConflict: 'place_id', ignoreDuplicates: true });

    if (error) {
      console.error('DB error:', error.message);
    } else {
      totalSaved += results.length;
    }

    // Google requires a short wait before using nextPageToken
    if (nextPageToken && page < MAX_PAGES) {
      console.log('Waiting 2s before next page...');
      await sleep(2000);
    }
  } while (pageToken && page < MAX_PAGES);

  console.log(`\nDone. Found ${totalFound} businesses without websites. Saved ${totalSaved} new records.`);
}

function sleep(ms: number) {
  return new Promise(resolve => setTimeout(resolve, ms));
}

run().catch(err => {
  console.error('Fatal error:', err.message);
  process.exit(1);
});
