import axios from 'axios';
import * as dotenv from 'dotenv';
dotenv.config();

const VERCEL_TOKEN = process.env.VERCEL_TOKEN!;
const VERCEL_TEAM_ID = process.env.VERCEL_TEAM_ID; // optional
const PREVIEW_DOMAIN = process.env.PREVIEW_DOMAIN!; // e.g. "preview.yourdomain.com"

const vercel = axios.create({
  baseURL: 'https://api.vercel.com',
  headers: { Authorization: `Bearer ${VERCEL_TOKEN}` },
  params: VERCEL_TEAM_ID ? { teamId: VERCEL_TEAM_ID } : {},
});

// Converts business name to a clean URL slug
export function slugify(name: string): string {
  return name
    .toLowerCase()
    .replace(/[^a-z0-9\s-]/g, '')
    .replace(/\s+/g, '-')
    .replace(/-+/g, '-')
    .slice(0, 50);
}

export async function deploySite(
  businessName: string,
  html: string
): Promise<{ projectId: string; deploymentUrl: string; previewUrl: string }> {
  const slug = slugify(businessName);
  const projectName = `biz-${slug}-${Date.now().toString(36)}`;

  // Encode HTML as base64 for Vercel Files API
  const htmlBase64 = Buffer.from(html).toString('base64');

  // Create a new Vercel deployment (single HTML file)
  const { data: deployment } = await vercel.post('/v13/deployments', {
    name: projectName,
    files: [
      {
        file: 'index.html',
        data: htmlBase64,
        encoding: 'base64',
      },
    ],
    projectSettings: {
      framework: null, // static HTML
      outputDirectory: './',
    },
    target: 'production',
  });

  const deploymentUrl = `https://${deployment.url}`;
  const previewUrl = `https://${slug}.${PREVIEW_DOMAIN}`;

  // Optionally add a custom preview subdomain alias
  // (Only works if your domain is configured in Vercel)
  try {
    await vercel.post(`/v2/deployments/${deployment.id}/aliases`, {
      alias: `${slug}.${PREVIEW_DOMAIN}`,
    });
  } catch {
    // Alias might fail if domain isn't set up yet — deployment URL still works
    console.warn(`  ⚠ Could not add alias ${slug}.${PREVIEW_DOMAIN} — using deployment URL`);
  }

  return {
    projectId: deployment.projectId || projectName,
    deploymentUrl,
    previewUrl: deploymentUrl, // fallback to deployment URL
  };
}
