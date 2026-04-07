# Auto Site Builder — Setup Guide

## Accounts You Need (all free tiers work to start)

| Service | What For | Sign Up |
|---|---|---|
| Google Cloud | Find businesses | console.cloud.google.com |
| Supabase | Database | supabase.com |
| Anthropic | AI content generation | console.anthropic.com |
| Vercel | Host generated sites | vercel.com |
| Hunter.io | Find business emails | hunter.io |
| Resend | Send pitch emails | resend.com |

---

## Step 1 — Install dependencies

```bash
cd auto-site-builder
npm install
```

## Step 2 — Set up environment variables

```bash
cp .env.example .env
# Fill in all values in .env
```

## Step 3 — Set up Google Places API

1. Go to console.cloud.google.com
2. Create a new project
3. Enable **Places API**
4. Create an API key → paste into `.env` as `GOOGLE_PLACES_API_KEY`

## Step 4 — Set up Supabase

1. Create a project at supabase.com
2. Go to SQL Editor → paste contents of `src/db/schema.sql` → Run
3. Copy your Project URL and service_role key → paste into `.env`

## Step 5 — Set up Vercel

1. Create account at vercel.com
2. Go to Account Settings → Tokens → Create token
3. Paste into `.env` as `VERCEL_TOKEN`
4. Optional: set up a domain and add it as `PREVIEW_DOMAIN`

## Step 6 — Set up Resend (email sending)

1. Sign up at resend.com
2. Verify your sending domain
3. Create API key → paste into `.env`
4. Set `OUTREACH_EMAIL` to your verified sending address
5. Set `OUTREACH_NAME` to your name

---

## Running the Pipeline

### Phase 1: Discover businesses

```bash
# Search for plumbers in Dallas with no websites
npm run discover -- --query "plumber" --location "Dallas, TX" --pages 3

# More examples:
npm run discover -- --query "hair salon" --location "Phoenix, AZ"
npm run discover -- --query "restaurant" --location "Memphis, TN"
npm run discover -- --query "electrician" --location "Charlotte, NC"
```

### Phase 2: Build websites

```bash
# Build sites for next 10 discovered businesses
npm run build-site

# Build only 3 at a time
npm run build-site -- --limit 3

# Build for a specific business
npm run build-site -- --id <uuid-from-supabase>
```

### Phase 3: Send outreach emails

```bash
# Test run (finds emails, doesn't send)
npm run send-outreach -- --dry-run

# Send to next 10 businesses with sites
npm run send-outreach -- --limit 10
```

### Phase 4: Track responses

Open `src/dashboard/index.html` in your browser.
Add your Supabase URL and anon key at the top of the file.

---

## After a Sale ($500)

When a business says yes:

1. Mark them as `sold` in the dashboard
2. Transfer their Vercel project to their own account, OR
3. Point their domain to your Vercel deployment
4. Set up [Formspree](https://formspree.io) on their contact form (free)
5. Set up [Cal.com](https://cal.com) if they need scheduling (free)
6. Give them their site login (Cal.com + Formspree are their only accounts needed)
7. Mark as `delivered`

---

## Scheduling Setup (Cal.com) — for relevant businesses

After sale, to activate booking on their site:

1. Create a free Cal.com account for the business
2. Set up an event type (e.g. "30-min Consultation")
3. In `index.html` of their site, find the `<!-- To activate online booking -->` comment
4. Follow the instructions in that comment to embed their Cal.com link
5. Redeploy

The client only needs their Cal.com login to manage appointments — no tech skills required.
