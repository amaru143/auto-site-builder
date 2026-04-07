-- Run this in your Supabase SQL editor

CREATE TABLE businesses (
  id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
  place_id TEXT UNIQUE NOT NULL,
  name TEXT NOT NULL,
  address TEXT,
  city TEXT,
  state TEXT,
  zip TEXT,
  phone TEXT,
  email TEXT,
  website TEXT,
  category TEXT,             -- raw Google type (e.g. "plumber")
  industry TEXT,             -- normalized (e.g. "home-services")
  hours JSONB,               -- ["Monday: 8AM-5PM", ...]
  photos JSONB,              -- array of photo URLs
  rating DECIMAL,
  review_count INTEGER,
  reviews JSONB,             -- top 3 review texts for testimonials
  lat DECIMAL,
  lng DECIMAL,
  needs_scheduling BOOLEAN DEFAULT false,
  discovered_at TIMESTAMPTZ DEFAULT NOW(),
  status TEXT DEFAULT 'discovered'
  -- discovered → site_built → email_found → email_sent → replied → sold → delivered
);

CREATE TABLE generated_sites (
  id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
  business_id UUID REFERENCES businesses(id) ON DELETE CASCADE,
  preview_url TEXT,                -- e.g. acme-plumbing.preview.yourdomain.com
  vercel_project_id TEXT,
  vercel_deployment_url TEXT,
  template_type TEXT,              -- which template was used
  generated_content JSONB,         -- the AI-generated copy stored as JSON
  created_at TIMESTAMPTZ DEFAULT NOW(),
  deployed BOOLEAN DEFAULT false
);

CREATE TABLE outreach (
  id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
  business_id UUID REFERENCES businesses(id) ON DELETE CASCADE,
  site_id UUID REFERENCES generated_sites(id),
  email_to TEXT,
  email_subject TEXT,
  email_body TEXT,
  sent_at TIMESTAMPTZ,
  reply_received_at TIMESTAMPTZ,
  reply_content TEXT,
  reply_from TEXT,
  status TEXT DEFAULT 'pending',
  -- pending → sent → replied → interested → sold → declined → unsubscribed
  notes TEXT
);

-- Indexes
CREATE INDEX idx_businesses_status ON businesses(status);
CREATE INDEX idx_businesses_industry ON businesses(industry);
CREATE INDEX idx_outreach_status ON outreach(status);
