/**
 * Website Generator Runner
 *
 * Usage:
 *   npm run build-site                  -- processes next 10 'discovered' businesses
 *   npm run build-site -- --limit 5     -- process only 5
 *   npm run build-site -- --id <uuid>   -- process a single business by ID
 */

import { generateSiteContent } from './contentGen';
import { buildSiteHTML } from './siteBuilder';
import { deploySite } from './deploy';
import { db } from '../db/client';
import * as dotenv from 'dotenv';
dotenv.config();

const args = process.argv.slice(2);
function getArg(name: string) {
  const i = args.indexOf(`--${name}`);
  return i !== -1 ? args[i + 1] : undefined;
}

const LIMIT = parseInt(getArg('limit') || '10');
const SINGLE_ID = getArg('id');

async function run() {
  let query = db
    .from('businesses')
    .select('*')
    .eq('status', 'discovered')
    .is('website', null)
    .order('discovered_at', { ascending: true })
    .limit(LIMIT);

  if (SINGLE_ID) {
    query = db.from('businesses').select('*').eq('id', SINGLE_ID).limit(1);
  }

  const { data: businesses, error } = await query;
  if (error) throw new Error(error.message);
  if (!businesses || businesses.length === 0) {
    console.log('No businesses to process.');
    return;
  }

  console.log(`\nBuilding sites for ${businesses.length} businesses...\n`);

  for (const biz of businesses) {
    console.log(`\n[${biz.name}] — ${biz.industry} — ${biz.city}, ${biz.state}`);

    try {
      // 1. Generate AI content
      console.log('  → Generating content with Claude...');
      const content = await generateSiteContent({
        name: biz.name,
        category: biz.category,
        industry: biz.industry,
        city: biz.city,
        state: biz.state,
        address: biz.address,
        phone: biz.phone,
        rating: biz.rating,
        review_count: biz.review_count,
        reviews: biz.reviews,
        hours: biz.hours,
        needs_scheduling: biz.needs_scheduling,
      });

      // 2. Build HTML
      console.log('  → Building HTML...');
      const html = buildSiteHTML(biz, content);

      // 3. Deploy to Vercel
      console.log('  → Deploying to Vercel...');
      const { projectId, deploymentUrl, previewUrl } = await deploySite(biz.name, html);

      // 4. Save generated site to DB
      const { data: site, error: siteErr } = await db
        .from('generated_sites')
        .insert({
          business_id: biz.id,
          preview_url: previewUrl,
          vercel_project_id: projectId,
          vercel_deployment_url: deploymentUrl,
          template_type: biz.industry,
          generated_content: content,
          deployed: true,
        })
        .select()
        .single();

      if (siteErr) throw new Error(siteErr.message);

      // 5. Update business status
      await db
        .from('businesses')
        .update({ status: 'site_built' })
        .eq('id', biz.id);

      console.log(`  ✅ Live at: ${previewUrl}`);
    } catch (err: any) {
      console.error(`  ✗ Failed for ${biz.name}: ${err.message}`);
    }
  }

  console.log('\nDone building sites.');
}

run().catch(err => {
  console.error('Fatal:', err.message);
  process.exit(1);
});
