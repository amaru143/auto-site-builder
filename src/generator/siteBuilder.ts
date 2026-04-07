import type { GeneratedContent } from './contentGen';
import type { Business } from '../db/client';

// Maps industry → color scheme
const THEMES: Record<string, { primary: string; accent: string; bg: string }> = {
  'food-beverage':   { primary: '#c0392b', accent: '#e67e22', bg: '#fdf6ee' },
  'beauty-wellness': { primary: '#8e44ad', accent: '#e91e8c', bg: '#fdf0f8' },
  'medical':         { primary: '#2980b9', accent: '#27ae60', bg: '#f0f7ff' },
  'home-services':   { primary: '#2c3e50', accent: '#e67e22', bg: '#f8f9fa' },
  'auto':            { primary: '#1a252f', accent: '#e74c3c', bg: '#f8f9fa' },
  'professional':    { primary: '#1a3a5c', accent: '#2980b9', bg: '#f0f4f8' },
  'generic':         { primary: '#2c3e50', accent: '#3498db', bg: '#f8f9fa' },
};

function getTheme(industry: string) {
  return THEMES[industry] || THEMES['generic'];
}

function photoOrFallback(photos: string[], index: number): string {
  if (photos && photos[index]) return photos[index];
  return `https://images.unsplash.com/photo-1497366216548-37526070297c?w=1200&auto=format&fit=crop`;
}

export function buildSiteHTML(business: Business, content: GeneratedContent): string {
  const theme = getTheme(business.industry || 'generic');
  const photos = business.photos || [];
  const hasScheduling = business.needs_scheduling;

  const servicesHTML = content.services.map(s => `
    <div class="service-card">
      <span class="service-icon">${s.icon}</span>
      <h3>${s.name}</h3>
      <p>${s.description}</p>
    </div>`).join('');

  const valuePropsHTML = content.valueProps.map(v => `
    <div class="value-card">
      <span class="value-icon">${v.icon}</span>
      <h3>${v.title}</h3>
      <p>${v.description}</p>
    </div>`).join('');

  const hoursHTML = business.hours?.length ? `
    <div class="info-block">
      <h4>Hours</h4>
      <ul class="hours-list">
        ${business.hours.map(h => `<li>${h}</li>`).join('')}
      </ul>
    </div>` : '';

  const reviewsHTML = (business.reviews as any[] || []).length ? `
    <section class="section reviews-section" id="reviews">
      <div class="container">
        <h2 class="section-title">What Our Customers Say</h2>
        <div class="reviews-grid">
          ${(business.reviews as any[]).map(r => `
            <div class="review-card">
              <div class="stars">${'★'.repeat(r.rating || 5)}</div>
              <p>"${r.text}"</p>
              <span class="reviewer">— ${r.author}</span>
            </div>`).join('')}
        </div>
      </div>
    </section>` : '';

  const schedulingSection = hasScheduling ? `
    <section class="section scheduling-section" id="book">
      <div class="container">
        <h2 class="section-title">${content.schedulingTitle || 'Book an Appointment'}</h2>
        <p class="section-sub">${content.schedulingSubtitle || 'Schedule your visit — we\'ll confirm within 24 hours.'}</p>
        <div class="booking-widget">
          <!-- Cal.com embed — replace YOUR_CAL_LINK with your Cal.com link -->
          <div id="cal-placeholder">
            <div class="cal-cta">
              <p>Ready to book? Call us or fill out the contact form below.</p>
              ${business.phone ? `<a href="tel:${business.phone}" class="btn btn-primary">📞 Call ${business.phone}</a>` : ''}
            </div>
            <!--
              To activate online booking:
              1. Create a free account at cal.com
              2. Set up your event type
              3. Replace the div above with:
              <div id="cal-booking" style="min-height:500px;"></div>
              <script>
                (function(C,A,L){let p=function(a,ar){a.q.push(ar)};let d=C.document;C.Cal=C.Cal||function(){let cal=C.Cal;let ar=arguments;if(!cal.loaded){cal.ns={};cal.q=cal.q||[];d.head.appendChild(d.createElement("script")).src=A;cal.loaded=true}if(ar[0]===L){const api=function(){p(api,arguments)};const namespace=ar[1];api.q=[];if(typeof namespace==="string"){cal.ns[namespace]=api;p(cal,["initNamespace",namespace])}else p(cal,ar);return}p(cal,ar)};"init","https://app.cal.com/embed/embed.js","NOINIT")(window,document,"init");
                Cal("init", {origin:"https://app.cal.com"});
                Cal("inline", {elementOrSelector:"#cal-booking", calLink:"YOUR_USERNAME/YOUR_EVENT"});
              </script>
            -->
          </div>
        </div>
      </div>
    </section>` : '';

  const navSchedulingLink = hasScheduling ? `<a href="#book">Book Now</a>` : '';

  return `<!DOCTYPE html>
<html lang="en">
<head>
  <meta charset="UTF-8" />
  <meta name="viewport" content="width=device-width, initial-scale=1.0" />
  <title>${content.metaTitle}</title>
  <meta name="description" content="${content.metaDescription}" />
  <link rel="preconnect" href="https://fonts.googleapis.com" />
  <link href="https://fonts.googleapis.com/css2?family=Inter:wght@400;500;600;700;800&display=swap" rel="stylesheet" />
  <style>
    :root {
      --primary: ${theme.primary};
      --accent: ${theme.accent};
      --bg: ${theme.bg};
      --text: #1a1a2e;
      --text-muted: #6b7280;
      --radius: 12px;
    }
    * { margin: 0; padding: 0; box-sizing: border-box; }
    html { scroll-behavior: smooth; }
    body {
      font-family: 'Inter', sans-serif;
      color: var(--text);
      background: var(--bg);
      line-height: 1.6;
    }

    /* NAV */
    nav {
      position: fixed; top: 0; left: 0; right: 0; z-index: 100;
      background: rgba(255,255,255,0.95);
      backdrop-filter: blur(10px);
      border-bottom: 1px solid rgba(0,0,0,0.08);
      padding: 0 2rem;
      height: 64px;
      display: flex; align-items: center; justify-content: space-between;
    }
    .nav-logo { font-weight: 800; font-size: 1.1rem; color: var(--primary); text-decoration: none; }
    .nav-links { display: flex; gap: 1.5rem; }
    .nav-links a { text-decoration: none; color: var(--text); font-weight: 500; font-size: 0.95rem; transition: color 0.2s; }
    .nav-links a:hover { color: var(--primary); }
    .nav-cta { background: var(--primary); color: white !important; padding: 0.5rem 1.2rem; border-radius: 8px; }
    .nav-cta:hover { opacity: 0.9; }

    /* HERO */
    .hero {
      min-height: 100vh;
      background: linear-gradient(135deg, var(--primary) 0%, ${theme.accent} 100%);
      display: flex; align-items: center;
      padding: 6rem 2rem 4rem;
      position: relative;
      overflow: hidden;
    }
    .hero::before {
      content: '';
      position: absolute; inset: 0;
      background: url('${photoOrFallback(photos, 0)}') center/cover;
      opacity: 0.15;
    }
    .hero-content {
      position: relative; z-index: 1;
      max-width: 700px; margin: 0 auto; text-align: center;
      color: white;
    }
    .hero-badge {
      display: inline-block;
      background: rgba(255,255,255,0.2);
      border: 1px solid rgba(255,255,255,0.3);
      padding: 0.4rem 1rem;
      border-radius: 100px;
      font-size: 0.85rem;
      font-weight: 600;
      margin-bottom: 1.5rem;
      letter-spacing: 0.05em;
    }
    .hero h1 { font-size: clamp(2rem, 5vw, 3.5rem); font-weight: 800; line-height: 1.2; margin-bottom: 1rem; }
    .hero p { font-size: 1.2rem; opacity: 0.9; margin-bottom: 2rem; }
    .hero-btns { display: flex; gap: 1rem; justify-content: center; flex-wrap: wrap; }
    .btn {
      display: inline-block; padding: 0.85rem 2rem;
      border-radius: 10px; font-weight: 700; font-size: 1rem;
      text-decoration: none; transition: all 0.2s; cursor: pointer;
      border: none;
    }
    .btn-primary { background: white; color: var(--primary); }
    .btn-primary:hover { transform: translateY(-2px); box-shadow: 0 8px 25px rgba(0,0,0,0.2); }
    .btn-secondary { background: rgba(255,255,255,0.15); color: white; border: 2px solid rgba(255,255,255,0.6); }
    .btn-secondary:hover { background: rgba(255,255,255,0.25); }
    .hero-rating {
      margin-top: 2rem; font-size: 0.9rem; opacity: 0.85;
      display: flex; align-items: center; justify-content: center; gap: 0.5rem;
    }

    /* SECTIONS */
    .section { padding: 5rem 2rem; }
    .container { max-width: 1100px; margin: 0 auto; }
    .section-title { font-size: clamp(1.6rem, 3vw, 2.2rem); font-weight: 800; text-align: center; margin-bottom: 0.75rem; }
    .section-sub { text-align: center; color: var(--text-muted); font-size: 1.05rem; margin-bottom: 3rem; max-width: 600px; margin-left: auto; margin-right: auto; }

    /* ABOUT */
    .about-section { background: white; }
    .about-grid { display: grid; grid-template-columns: 1fr 1fr; gap: 4rem; align-items: center; }
    .about-img { border-radius: var(--radius); overflow: hidden; aspect-ratio: 4/3; }
    .about-img img { width: 100%; height: 100%; object-fit: cover; }
    .about-text h2 { font-size: 2rem; font-weight: 800; margin-bottom: 1rem; }
    .about-text p { color: var(--text-muted); line-height: 1.8; margin-bottom: 1.5rem; }

    /* SERVICES */
    .services-grid { display: grid; grid-template-columns: repeat(auto-fit, minmax(280px, 1fr)); gap: 1.5rem; }
    .service-card {
      background: white; border-radius: var(--radius); padding: 2rem;
      box-shadow: 0 2px 15px rgba(0,0,0,0.06);
      transition: transform 0.2s, box-shadow 0.2s;
    }
    .service-card:hover { transform: translateY(-4px); box-shadow: 0 8px 30px rgba(0,0,0,0.1); }
    .service-icon { font-size: 2rem; margin-bottom: 1rem; display: block; }
    .service-card h3 { font-size: 1.1rem; font-weight: 700; margin-bottom: 0.5rem; }
    .service-card p { color: var(--text-muted); font-size: 0.95rem; }

    /* VALUE PROPS */
    .values-section { background: var(--primary); color: white; }
    .values-section .section-title { color: white; }
    .values-section .section-sub { color: rgba(255,255,255,0.8); }
    .values-grid { display: grid; grid-template-columns: repeat(auto-fit, minmax(250px, 1fr)); gap: 2rem; }
    .value-card { text-align: center; padding: 1.5rem; }
    .value-icon { font-size: 2.5rem; display: block; margin-bottom: 1rem; }
    .value-card h3 { font-size: 1.1rem; font-weight: 700; margin-bottom: 0.5rem; }
    .value-card p { opacity: 0.85; font-size: 0.95rem; }

    /* REVIEWS */
    .reviews-section { background: white; }
    .reviews-grid { display: grid; grid-template-columns: repeat(auto-fit, minmax(280px, 1fr)); gap: 1.5rem; }
    .review-card {
      background: var(--bg); border-radius: var(--radius); padding: 1.75rem;
      border-left: 4px solid var(--accent);
    }
    .stars { color: #f59e0b; font-size: 1.1rem; margin-bottom: 0.75rem; }
    .review-card p { color: var(--text-muted); font-style: italic; margin-bottom: 0.75rem; line-height: 1.7; }
    .reviewer { font-weight: 600; font-size: 0.9rem; color: var(--primary); }

    /* SCHEDULING */
    .scheduling-section { background: var(--bg); }
    .booking-widget { max-width: 700px; margin: 0 auto; }
    .cal-cta { text-align: center; padding: 3rem 2rem; background: white; border-radius: var(--radius); box-shadow: 0 2px 15px rgba(0,0,0,0.06); }
    .cal-cta p { color: var(--text-muted); margin-bottom: 1.5rem; font-size: 1.05rem; }
    .cal-cta .btn-primary { background: var(--primary); color: white; }

    /* CONTACT */
    .contact-section { background: white; }
    .contact-grid { display: grid; grid-template-columns: 1fr 1fr; gap: 4rem; align-items: start; }
    .info-block { margin-bottom: 2rem; }
    .info-block h4 { font-weight: 700; margin-bottom: 0.75rem; color: var(--primary); text-transform: uppercase; font-size: 0.8rem; letter-spacing: 0.1em; }
    .info-block p, .info-block a { color: var(--text-muted); text-decoration: none; }
    .info-block a:hover { color: var(--primary); }
    .hours-list { list-style: none; }
    .hours-list li { padding: 0.2rem 0; font-size: 0.9rem; color: var(--text-muted); }
    .contact-form { background: var(--bg); padding: 2rem; border-radius: var(--radius); }
    .form-group { margin-bottom: 1.25rem; }
    .form-group label { display: block; font-weight: 600; font-size: 0.9rem; margin-bottom: 0.4rem; }
    .form-group input, .form-group textarea, .form-group select {
      width: 100%; padding: 0.75rem 1rem;
      border: 1px solid #e5e7eb; border-radius: 8px;
      font-family: inherit; font-size: 0.95rem;
      background: white; color: var(--text);
      transition: border-color 0.2s;
    }
    .form-group input:focus, .form-group textarea:focus, .form-group select:focus {
      outline: none; border-color: var(--primary);
    }
    .form-group textarea { resize: vertical; min-height: 120px; }
    .btn-submit {
      width: 100%; background: var(--primary); color: white;
      padding: 0.9rem; border: none; border-radius: 10px;
      font-size: 1rem; font-weight: 700; cursor: pointer;
      transition: opacity 0.2s;
    }
    .btn-submit:hover { opacity: 0.9; }
    #form-success { display: none; text-align: center; padding: 1rem; color: #16a34a; font-weight: 600; }

    /* FOOTER */
    footer {
      background: var(--text);
      color: rgba(255,255,255,0.7);
      padding: 3rem 2rem;
      text-align: center;
    }
    .footer-name { font-weight: 800; font-size: 1.2rem; color: white; margin-bottom: 0.5rem; }
    .footer-tagline { margin-bottom: 1rem; }
    .footer-contact { display: flex; justify-content: center; gap: 2rem; flex-wrap: wrap; margin-bottom: 1.5rem; }
    .footer-contact a { color: rgba(255,255,255,0.7); text-decoration: none; }
    .footer-contact a:hover { color: white; }
    .footer-copy { font-size: 0.8rem; opacity: 0.5; }

    /* RESPONSIVE */
    @media (max-width: 768px) {
      .about-grid, .contact-grid { grid-template-columns: 1fr; gap: 2rem; }
      .nav-links { display: none; }
    }
  </style>
</head>
<body>

  <!-- NAV -->
  <nav>
    <a href="#" class="nav-logo">${business.name}</a>
    <div class="nav-links">
      <a href="#about">About</a>
      <a href="#services">Services</a>
      ${hasScheduling ? `<a href="#book">Appointments</a>` : ''}
      <a href="#contact">Contact</a>
      ${hasScheduling
        ? `<a href="#book" class="nav-cta">Book Now</a>`
        : `<a href="#contact" class="nav-cta">Get in Touch</a>`}
    </div>
  </nav>

  <!-- HERO -->
  <section class="hero">
    <div class="hero-content">
      ${business.city ? `<div class="hero-badge">📍 Serving ${business.city}, ${business.state}</div>` : ''}
      <h1>${content.tagline}</h1>
      <p>${content.subheadline}</p>
      <div class="hero-btns">
        ${business.phone ? `<a href="tel:${business.phone}" class="btn btn-primary">📞 Call ${business.phone}</a>` : ''}
        <a href="${hasScheduling ? '#book' : '#contact'}" class="btn btn-secondary">${content.ctaText}</a>
      </div>
      ${business.rating ? `<div class="hero-rating">⭐ ${business.rating}/5 — Rated by ${business.review_count}+ customers on Google</div>` : ''}
    </div>
  </section>

  <!-- ABOUT -->
  <section class="section about-section" id="about">
    <div class="container">
      <div class="about-grid">
        <div class="about-img">
          <img src="${photoOrFallback(photos, 1)}" alt="${business.name}" loading="lazy" />
        </div>
        <div class="about-text">
          <h2>${content.aboutTitle}</h2>
          <p>${content.aboutBody}</p>
          <a href="${hasScheduling ? '#book' : '#contact'}" class="btn btn-primary" style="background:var(--primary);color:white;">${content.ctaText}</a>
        </div>
      </div>
    </div>
  </section>

  <!-- SERVICES -->
  <section class="section" id="services">
    <div class="container">
      <h2 class="section-title">Our Services</h2>
      <p class="section-sub">Everything you need, done right the first time.</p>
      <div class="services-grid">
        ${servicesHTML}
      </div>
    </div>
  </section>

  <!-- VALUE PROPS -->
  <section class="section values-section">
    <div class="container">
      <h2 class="section-title">Why Choose ${business.name}?</h2>
      <p class="section-sub" style="color:rgba(255,255,255,0.8)">We're proud to serve ${business.city || 'our community'}.</p>
      <div class="values-grid">
        ${valuePropsHTML}
      </div>
    </div>
  </section>

  <!-- REVIEWS -->
  ${reviewsHTML}

  <!-- SCHEDULING -->
  ${schedulingSection}

  <!-- CONTACT -->
  <section class="section contact-section" id="contact">
    <div class="container">
      <h2 class="section-title">${content.contactTitle}</h2>
      <p class="section-sub">${content.contactSubtitle}</p>
      <div class="contact-grid">
        <div class="contact-info">
          ${business.phone ? `<div class="info-block"><h4>Phone</h4><p><a href="tel:${business.phone}">${business.phone}</a></p></div>` : ''}
          ${business.email ? `<div class="info-block"><h4>Email</h4><p><a href="mailto:${business.email}">${business.email}</a></p></div>` : ''}
          ${business.address ? `<div class="info-block"><h4>Address</h4><p>${business.address}</p></div>` : ''}
          ${hoursHTML}
        </div>
        <div class="contact-form">
          <form id="contact-form">
            <div class="form-group">
              <label for="name">Your Name</label>
              <input type="text" id="name" name="name" placeholder="John Smith" required />
            </div>
            <div class="form-group">
              <label for="email">Email</label>
              <input type="email" id="email" name="email" placeholder="john@email.com" required />
            </div>
            <div class="form-group">
              <label for="phone-input">Phone</label>
              <input type="tel" id="phone-input" name="phone" placeholder="(555) 555-5555" />
            </div>
            <div class="form-group">
              <label for="message">How can we help?</label>
              <textarea id="message" name="message" placeholder="Tell us about your project..." required></textarea>
            </div>
            <button type="submit" class="btn-submit">Send Message →</button>
          </form>
          <div id="form-success">✅ Message sent! We'll be in touch soon.</div>
        </div>
      </div>
    </div>
  </section>

  <!-- FOOTER -->
  <footer>
    <div class="footer-name">${business.name}</div>
    <div class="footer-tagline">${content.footerTagline}</div>
    <div class="footer-contact">
      ${business.phone ? `<a href="tel:${business.phone}">${business.phone}</a>` : ''}
      ${business.email ? `<a href="mailto:${business.email}">${business.email}</a>` : ''}
      ${business.address ? `<span>${business.city}, ${business.state}</span>` : ''}
    </div>
    <div class="footer-copy">© ${new Date().getFullYear()} ${business.name}. All rights reserved.</div>
  </footer>

  <script>
    // Contact form handler (sends to Formspree or similar — update action URL after sale)
    document.getElementById('contact-form').addEventListener('submit', async function(e) {
      e.preventDefault();
      const form = e.target;
      const data = new FormData(form);
      // TODO: Replace with actual form endpoint (Formspree, EmailJS, etc.)
      // For now, show success message
      form.style.display = 'none';
      document.getElementById('form-success').style.display = 'block';
    });
  </script>
</body>
</html>`;
}
