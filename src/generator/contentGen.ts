import Anthropic from '@anthropic-ai/sdk';
import * as dotenv from 'dotenv';
dotenv.config();

const client = new Anthropic();

export interface GeneratedContent {
  // Hero
  tagline: string;           // Short punchy headline, e.g. "Dallas's Most Trusted Plumber"
  subheadline: string;       // 1-2 sentence description
  ctaText: string;           // Button text, e.g. "Book a Free Estimate"

  // About
  aboutTitle: string;
  aboutBody: string;         // 3-4 sentences about the business

  // Services (3-6 items)
  services: {
    name: string;
    description: string;
    icon: string;            // emoji icon
  }[];

  // Why choose us (3 items)
  valueProps: {
    title: string;
    description: string;
    icon: string;
  }[];

  // Scheduling section (only if needs_scheduling)
  schedulingTitle?: string;
  schedulingSubtitle?: string;

  // Contact section
  contactTitle: string;
  contactSubtitle: string;

  // SEO
  metaTitle: string;
  metaDescription: string;

  // Footer tagline
  footerTagline: string;
}

export async function generateSiteContent(business: {
  name: string;
  category: string;
  industry: string;
  city: string;
  state: string;
  address: string;
  phone?: string;
  rating?: number;
  review_count?: number;
  reviews?: any[];
  hours?: string[];
  needs_scheduling: boolean;
}): Promise<GeneratedContent> {
  const reviewsText = business.reviews?.length
    ? `\nTop customer reviews:\n${business.reviews.map((r: any) => `- "${r.text}" — ${r.author}`).join('\n')}`
    : '';

  const hoursText = business.hours?.length
    ? `\nBusiness hours:\n${business.hours.join('\n')}`
    : '';

  const prompt = `You are a professional web copywriter creating website content for a real local business.

Business Details:
- Name: ${business.name}
- Type: ${business.category.replace(/_/g, ' ')}
- Location: ${business.city}, ${business.state}
- Address: ${business.address}
- Phone: ${business.phone || 'Not listed'}
- Google Rating: ${business.rating ? `${business.rating}/5 (${business.review_count} reviews)` : 'Not rated yet'}
${reviewsText}
${hoursText}

Write website content that is:
- Specific to this exact business and city (mention the city name naturally)
- Professional, warm, and trustworthy
- Action-oriented
- Realistic — do NOT invent specific claims about years of experience, certifications, or awards unless mentioned in reviews

Return ONLY a valid JSON object matching this exact structure:
{
  "tagline": "short punchy headline mentioning city",
  "subheadline": "1-2 sentence pitch",
  "ctaText": "action button text",
  "aboutTitle": "section title",
  "aboutBody": "3-4 sentence paragraph about the business",
  "services": [
    { "name": "service name", "description": "1 sentence", "icon": "emoji" }
  ],
  "valueProps": [
    { "title": "short title", "description": "1-2 sentences", "icon": "emoji" }
  ],
  ${business.needs_scheduling ? `"schedulingTitle": "Book with Us",
  "schedulingSubtitle": "Schedule your appointment in seconds — we'll confirm within 24 hours.",` : ''}
  "contactTitle": "Get in Touch",
  "contactSubtitle": "1 sentence",
  "metaTitle": "SEO page title (under 60 chars)",
  "metaDescription": "SEO meta description (under 160 chars)",
  "footerTagline": "short footer tagline"
}

Include 4-6 services that make sense for this type of business.`;

  const message = await client.messages.create({
    model: 'claude-opus-4-6',
    max_tokens: 1500,
    messages: [{ role: 'user', content: prompt }],
  });

  const text = (message.content[0] as any).text;

  // Extract JSON from response
  const jsonMatch = text.match(/\{[\s\S]*\}/);
  if (!jsonMatch) throw new Error('Claude did not return valid JSON');

  return JSON.parse(jsonMatch[0]) as GeneratedContent;
}
