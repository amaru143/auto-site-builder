#!/usr/bin/env python
"""
Payment Server
Flask server handling Stripe payments, webhook processing, and site previews.
"""
import os
import sys
import json
import re
import subprocess
import threading
import stripe
from pathlib import Path
from datetime import datetime
from flask import Flask, request, jsonify, send_from_directory, redirect, render_template_string

sys.path.insert(0, str(Path(__file__).parent.parent))
from config.settings import *

app = Flask(__name__)
stripe.api_key = STRIPE_SECRET_KEY

# Payment tracking
PAYMENTS_FILE = BASE_DIR / "leads" / "payments.json"

# Pipeline process tracking
pipeline_process = None
pipeline_log = []
pipeline_running = False


def load_payments():
    if PAYMENTS_FILE.exists():
        with open(PAYMENTS_FILE, 'r') as f:
            return json.load(f)
    return {}


def save_payments(payments):
    with open(PAYMENTS_FILE, 'w') as f:
        json.dump(payments, f, indent=2)


def create_payment_link(lead_id: str, business_name: str, amount: int = None) -> str:
    """Create a Stripe payment link for a lead."""
    if not STRIPE_SECRET_KEY or STRIPE_SECRET_KEY == 'your_stripe_secret_key_here':
        print(f"[!] Stripe not configured. Would create payment link for {business_name}")
        return f"{PAYMENT_SERVER_URL}/pay/{lead_id}"

    price = amount or PRICE

    try:
        # Create a Stripe product
        product = stripe.Product.create(
            name=f"Professional Website - {business_name}",
            description=f"Complete professional website for {business_name}. Includes full setup guide, mobile-responsive design, SEO optimization, and all source files. One-time payment.",
            metadata={"lead_id": lead_id, "business_name": business_name}
        )

        # Create a price
        stripe_price = stripe.Price.create(
            product=product.id,
            unit_amount=price * 100,  # Stripe uses cents
            currency="usd"
        )

        # Create payment link
        payment_link = stripe.PaymentLink.create(
            line_items=[{"price": stripe_price.id, "quantity": 1}],
            metadata={"lead_id": lead_id, "business_name": business_name},
            after_completion={
                "type": "redirect",
                "redirect": {"url": f"{PAYMENT_SERVER_URL}/thank-you/{lead_id}"}
            }
        )

        # Track payment
        payments = load_payments()
        payments[lead_id] = {
            "business_name": business_name,
            "amount": price,
            "payment_link_id": payment_link.id,
            "payment_link_url": payment_link.url,
            "status": "pending",
            "created_at": datetime.now().isoformat()
        }
        save_payments(payments)

        return payment_link.url

    except Exception as e:
        print(f"[!] Stripe error: {e}")
        return f"{PAYMENT_SERVER_URL}/pay/{lead_id}"


def create_all_payment_links():
    """Create payment links for all leads."""
    leads_path = LEADS_DIR / "all_leads.json"
    if not leads_path.exists():
        print("[!] No leads found")
        return {}

    with open(leads_path, 'r') as f:
        leads = json.load(f)

    links = {}
    for lead in leads:
        if lead.get("flag_no_website") or lead.get("priority") in ["high", "critical"]:
            link = create_payment_link(lead["id"], lead["business_name"])
            links[lead["id"]] = link
            print(f"[+] Payment link for {lead['business_name']}: {link}")

    return links


# === Flask Routes ===

@app.route('/')
def index():
    """Dashboard redirect."""
    return redirect('/dashboard')


@app.route('/dashboard')
def dashboard():
    """Simple dashboard showing leads and payment status."""
    payments = load_payments()
    leads_path = LEADS_DIR / "all_leads.json"
    leads = []
    if leads_path.exists():
        with open(leads_path, 'r', encoding='utf-8') as f:
            leads = json.load(f)

    html = """
    <!DOCTYPE html>
    <html>
    <head>
        <title>WebLift Dashboard</title>
        <script src="https://cdn.tailwindcss.com"></script>
        <link href="https://fonts.googleapis.com/css2?family=Inter:wght@300;400;500;600;700&display=swap" rel="stylesheet">
    </head>
    <body class="bg-gray-50 font-[Inter]">
        <div class="max-w-7xl mx-auto px-4 py-8">
            <div class="flex items-center justify-between mb-8">
                <h1 class="text-3xl font-bold text-gray-900">WebLift Dashboard</h1>
                <div class="flex gap-3">
                    <button id="btn-start" onclick="startPipeline()" class="px-5 py-2.5 bg-green-600 text-white font-semibold rounded-lg hover:bg-green-700 transition-colors flex items-center gap-2">
                        <span>&#9654;</span> Start Pipeline
                    </button>
                    <button id="btn-stop" onclick="stopPipeline()" class="px-5 py-2.5 bg-red-600 text-white font-semibold rounded-lg hover:bg-red-700 transition-colors flex items-center gap-2 hidden">
                        <span>&#9632;</span> Stop Pipeline
                    </button>
                    <span id="status-badge" class="hidden px-3 py-2 bg-green-100 text-green-800 rounded-lg text-sm font-medium animate-pulse">Running...</span>
                </div>
            </div>

            <!-- Pipeline Log (hidden by default, shown when running) -->
            <div id="log-panel" class="hidden mb-8 bg-gray-900 rounded-xl shadow-sm p-4 max-h-64 overflow-y-auto">
                <div class="flex justify-between items-center mb-2">
                    <span class="text-gray-400 text-sm font-medium">Pipeline Log</span>
                    <button onclick="document.getElementById('log-panel').classList.add('hidden')" class="text-gray-500 hover:text-white text-sm">Hide</button>
                </div>
                <pre id="log-output" class="text-green-400 text-xs font-mono whitespace-pre-wrap"></pre>
            </div>

            <div class="grid grid-cols-1 md:grid-cols-4 gap-6 mb-8">
                <div class="bg-white rounded-xl shadow-sm p-6">
                    <div class="text-sm text-gray-500">Total Leads</div>
                    <div class="text-3xl font-bold text-gray-900">""" + str(len(leads)) + """</div>
                </div>
                <div class="bg-white rounded-xl shadow-sm p-6">
                    <div class="text-sm text-gray-500">No Website</div>
                    <div class="text-3xl font-bold text-red-600">""" + str(sum(1 for l in leads if l.get('flag_no_website'))) + """</div>
                </div>
                <div class="bg-white rounded-xl shadow-sm p-6">
                    <div class="text-sm text-gray-500">Payments Pending</div>
                    <div class="text-3xl font-bold text-yellow-600">""" + str(sum(1 for p in payments.values() if p.get('status') == 'pending')) + """</div>
                </div>
                <div class="bg-white rounded-xl shadow-sm p-6">
                    <div class="text-sm text-gray-500">Payments Complete</div>
                    <div class="text-3xl font-bold text-green-600">""" + str(sum(1 for p in payments.values() if p.get('status') == 'paid')) + """</div>
                </div>
            </div>

            <div class="bg-white rounded-xl shadow-sm overflow-hidden">
                <table class="w-full">
                    <thead class="bg-gray-50">
                        <tr>
                            <th class="px-6 py-3 text-left text-xs font-medium text-gray-500 uppercase">Business</th>
                            <th class="px-6 py-3 text-left text-xs font-medium text-gray-500 uppercase">Category</th>
                            <th class="px-6 py-3 text-left text-xs font-medium text-gray-500 uppercase">Website</th>
                            <th class="px-6 py-3 text-left text-xs font-medium text-gray-500 uppercase">Priority</th>
                            <th class="px-6 py-3 text-left text-xs font-medium text-gray-500 uppercase">Payment</th>
                            <th class="px-6 py-3 text-left text-xs font-medium text-gray-500 uppercase">Actions</th>
                        </tr>
                    </thead>
                    <tbody class="divide-y divide-gray-200">"""

    for lead in leads:
        lid = lead.get('id', '')
        payment = payments.get(lid, {})
        priority = lead.get('priority', 'medium')
        priority_colors = {'critical': 'red', 'high': 'orange', 'medium': 'yellow', 'low': 'green'}
        pcolor = priority_colors.get(priority, 'gray')
        pstatus = payment.get('status', 'none')

        html += f"""
                        <tr class="hover:bg-gray-50">
                            <td class="px-6 py-4 text-sm font-medium text-gray-900">{lead.get('business_name', '')}</td>
                            <td class="px-6 py-4 text-sm text-gray-500">{lead.get('category', '')}</td>
                            <td class="px-6 py-4 text-sm text-gray-500">{'&#10060; None' if lead.get('flag_no_website') else '&#9989; Has site'}</td>
                            <td class="px-6 py-4"><span class="px-2 py-1 text-xs rounded-full bg-{pcolor}-100 text-{pcolor}-800">{priority}</span></td>
                            <td class="px-6 py-4 text-sm text-gray-500">{pstatus}</td>
                            <td class="px-6 py-4 text-sm">
                                <a href="/preview/{lid}" class="text-blue-600 hover:underline mr-3">Preview</a>
                                <a href="/outreach/{lid}" class="text-green-600 hover:underline">Outreach</a>
                            </td>
                        </tr>"""

    html += """
                    </tbody>
                </table>
            </div>
        </div>
        <script>
        let pollTimer = null;
        function startPipeline() {
            fetch('/api/pipeline/start', {method:'POST', headers:{'Content-Type':'application/json'}, body:JSON.stringify({})})
            .then(r=>r.json()).then(d=>{
                if(d.status==='started'||d.status==='already_running'){
                    document.getElementById('btn-start').classList.add('hidden');
                    document.getElementById('btn-stop').classList.remove('hidden');
                    document.getElementById('status-badge').classList.remove('hidden');
                    document.getElementById('log-panel').classList.remove('hidden');
                    pollTimer = setInterval(pollStatus, 2000);
                }
            });
        }
        function stopPipeline() {
            fetch('/api/pipeline/stop', {method:'POST'}).then(r=>r.json()).then(d=>{
                document.getElementById('btn-start').classList.remove('hidden');
                document.getElementById('btn-stop').classList.add('hidden');
                document.getElementById('status-badge').classList.add('hidden');
                if(pollTimer) clearInterval(pollTimer);
            });
        }
        function pollStatus() {
            fetch('/api/pipeline/status').then(r=>r.json()).then(d=>{
                document.getElementById('log-output').textContent = d.log.join('');
                document.getElementById('log-panel').scrollTop = document.getElementById('log-panel').scrollHeight;
                if(!d.running){
                    document.getElementById('btn-start').classList.remove('hidden');
                    document.getElementById('btn-stop').classList.add('hidden');
                    document.getElementById('status-badge').classList.add('hidden');
                    if(pollTimer) clearInterval(pollTimer);
                    setTimeout(()=>location.reload(), 1000);
                }
            });
        }
        // Check initial status
        fetch('/api/pipeline/status').then(r=>r.json()).then(d=>{
            if(d.running){
                document.getElementById('btn-start').classList.add('hidden');
                document.getElementById('btn-stop').classList.remove('hidden');
                document.getElementById('status-badge').classList.remove('hidden');
                document.getElementById('log-panel').classList.remove('hidden');
                pollTimer = setInterval(pollStatus, 2000);
            }
        });
        </script>
    </body>
    </html>"""

    return html


@app.route('/preview/<lead_id>')
def preview_site(lead_id):
    """Serve a generated website preview."""
    # Find the lead
    leads_path = LEADS_DIR / "all_leads.json"
    if not leads_path.exists():
        return "No leads found", 404

    with open(leads_path, 'r') as f:
        leads = json.load(f)

    lead = next((l for l in leads if l.get('id') == lead_id), None)
    if not lead:
        return "Lead not found", 404

    import re
    safe_name = re.sub(r'[^\w\s-]', '', lead['business_name']).strip().replace(' ', '_').lower()
    site_dir = GENERATED_SITES_DIR / safe_name

    if site_dir.exists() and (site_dir / 'index.html').exists():
        return send_from_directory(str(site_dir), 'index.html')

    return f"No generated site found for {lead['business_name']}", 404


@app.route('/preview/<lead_id>/<path:filename>')
def preview_static(lead_id, filename):
    """Serve static files for previews."""
    leads_path = LEADS_DIR / "all_leads.json"
    if not leads_path.exists():
        return "Not found", 404

    with open(leads_path, 'r') as f:
        leads = json.load(f)

    lead = next((l for l in leads if l.get('id') == lead_id), None)
    if not lead:
        return "Not found", 404

    import re
    safe_name = re.sub(r'[^\w\s-]', '', lead['business_name']).strip().replace(' ', '_').lower()
    site_dir = GENERATED_SITES_DIR / safe_name

    if site_dir.exists():
        return send_from_directory(str(site_dir), filename)

    return "Not found", 404


@app.route('/pay/<lead_id>')
def pay(lead_id):
    """Redirect to Stripe payment or show payment page."""
    payments = load_payments()
    payment = payments.get(lead_id)

    if payment and payment.get('payment_link_url'):
        return redirect(payment['payment_link_url'])

    # Fallback payment page
    return render_template_string("""
    <!DOCTYPE html>
    <html>
    <head>
        <title>Get Your Website - ${{ price }}</title>
        <script src="https://cdn.tailwindcss.com"></script>
    </head>
    <body class="bg-gray-50 min-h-screen flex items-center justify-center">
        <div class="max-w-md mx-auto bg-white rounded-2xl shadow-lg p-8 text-center">
            <h1 class="text-2xl font-bold mb-4">Get Your Professional Website</h1>
            <p class="text-gray-600 mb-6">One-time payment of <span class="text-3xl font-bold text-green-600">${{ price }}</span></p>
            <ul class="text-left text-gray-600 mb-6 space-y-2">
                <li>&#9989; Professional responsive website</li>
                <li>&#9989; Mobile-optimized design</li>
                <li>&#9989; SEO optimized</li>
                <li>&#9989; All source files included</li>
                <li>&#9989; Full setup guide to get it live</li>
                <li>&#9989; Free revisions before purchase</li>
            </ul>
            <p class="text-sm text-gray-500 mb-6">Payment processing is being set up. Please contact us to complete your purchase.</p>
            <a href="mailto:{{ email }}" class="bg-blue-600 text-white px-8 py-3 rounded-lg font-semibold hover:bg-blue-700 inline-block">Contact Us to Pay</a>
        </div>
    </body>
    </html>
    """, price=PRICE, email=YOUR_EMAIL)


@app.route('/thank-you/<lead_id>')
def thank_you(lead_id):
    """Post-payment thank you page."""
    payments = load_payments()
    if lead_id in payments:
        payments[lead_id]['status'] = 'paid'
        payments[lead_id]['paid_at'] = datetime.now().isoformat()
        save_payments(payments)

    return render_template_string("""
    <!DOCTYPE html>
    <html>
    <head>
        <title>Thank You!</title>
        <script src="https://cdn.tailwindcss.com"></script>
    </head>
    <body class="bg-green-50 min-h-screen flex items-center justify-center">
        <div class="max-w-lg mx-auto bg-white rounded-2xl shadow-lg p-8 text-center">
            <div class="text-6xl mb-4">&#127881;</div>
            <h1 class="text-3xl font-bold text-green-700 mb-4">Thank You!</h1>
            <p class="text-gray-600 mb-6">Your payment has been received. You'll receive an email shortly with your complete website files and setup guide.</p>
            <div class="bg-green-50 rounded-lg p-4 text-sm text-green-800">
                <p class="font-semibold mb-2">What happens next:</p>
                <ol class="text-left space-y-1">
                    <li>1. You'll receive an email with your website files</li>
                    <li>2. The email includes a step-by-step setup guide</li>
                    <li>3. Follow the guide to get your site live on your domain</li>
                    <li>4. Reply to the email if you need any help</li>
                </ol>
            </div>
        </div>
    </body>
    </html>
    """)


@app.route('/webhook/stripe', methods=['POST'])
def stripe_webhook():
    """Handle Stripe webhook events."""
    payload = request.data
    sig_header = request.headers.get('Stripe-Signature')

    try:
        if STRIPE_WEBHOOK_SECRET and STRIPE_WEBHOOK_SECRET != 'your_stripe_webhook_secret_here':
            event = stripe.Webhook.construct_event(payload, sig_header, STRIPE_WEBHOOK_SECRET)
        else:
            event = json.loads(payload)
    except Exception as e:
        return jsonify({"error": str(e)}), 400

    if event.get('type') == 'checkout.session.completed':
        session = event['data']['object']
        metadata = session.get('metadata', {})
        lead_id = metadata.get('lead_id', '')

        if lead_id:
            payments = load_payments()
            if lead_id in payments:
                payments[lead_id]['status'] = 'paid'
                payments[lead_id]['paid_at'] = datetime.now().isoformat()
                payments[lead_id]['stripe_session_id'] = session.get('id')
                save_payments(payments)

                print(f"[+] Payment received for lead {lead_id}: {payments[lead_id]['business_name']}")

                # Trigger thank-you email
                try:
                    from scripts.email_sender import send_thank_you_email
                    send_thank_you_email(lead_id)
                except Exception as e:
                    print(f"[!] Error sending thank-you email: {e}")

    return jsonify({"status": "ok"})


@app.route('/api/leads')
def api_leads():
    """API endpoint for leads data."""
    leads_path = LEADS_DIR / "all_leads.json"
    if leads_path.exists():
        with open(leads_path, 'r', encoding='utf-8') as f:
            return jsonify(json.load(f))
    return jsonify([])


@app.route('/api/analyses')
def api_analyses():
    """API endpoint for analyses data."""
    analyses_path = ANALYSIS_DIR / "all_analyses.json"
    if analyses_path.exists():
        with open(analyses_path, 'r', encoding='utf-8') as f:
            return jsonify(json.load(f))
    return jsonify([])


@app.route('/api/payments')
def api_payments():
    """API endpoint for payment data."""
    return jsonify(load_payments())


@app.route('/api/pipeline/start', methods=['POST'])
def api_pipeline_start():
    """Start the pipeline process."""
    global pipeline_process, pipeline_running, pipeline_log

    if pipeline_running:
        return jsonify({"status": "already_running"})

    data = request.json or {}
    categories = data.get("categories", "plumbing roofing landscaping cleaning barbershop restaurant dental")
    cities = data.get("cities", "Austin")
    states = data.get("states", "TX")

    cmd = f'python run.py --full --categories {categories} --cities {cities} --states {states}'

    pipeline_log = [f"[{datetime.now().strftime('%H:%M:%S')}] Starting pipeline...\n"]
    pipeline_running = True

    def run_pipeline():
        global pipeline_process, pipeline_running, pipeline_log
        try:
            proc = subprocess.Popen(
                cmd, shell=True, cwd=str(BASE_DIR),
                stdout=subprocess.PIPE, stderr=subprocess.STDOUT,
                text=True, encoding='utf-8', errors='replace'
            )
            pipeline_process = proc
            for line in iter(proc.stdout.readline, ''):
                pipeline_log.append(line)
                if len(pipeline_log) > 500:
                    pipeline_log = pipeline_log[-300:]
            proc.wait()
            pipeline_log.append(f"\n[{datetime.now().strftime('%H:%M:%S')}] Pipeline finished (exit code: {proc.returncode})\n")
        except Exception as e:
            pipeline_log.append(f"\n[ERROR] {str(e)}\n")
        finally:
            pipeline_running = False
            pipeline_process = None

    t = threading.Thread(target=run_pipeline, daemon=True)
    t.start()

    return jsonify({"status": "started"})


@app.route('/api/pipeline/stop', methods=['POST'])
def api_pipeline_stop():
    """Stop the pipeline process."""
    global pipeline_process, pipeline_running

    if pipeline_process and pipeline_running:
        pipeline_process.terminate()
        pipeline_running = False
        pipeline_log.append(f"\n[{datetime.now().strftime('%H:%M:%S')}] Pipeline stopped by user.\n")
        return jsonify({"status": "stopped"})

    return jsonify({"status": "not_running"})


@app.route('/api/pipeline/status')
def api_pipeline_status():
    """Get pipeline status and log."""
    return jsonify({
        "running": pipeline_running,
        "log": pipeline_log[-100:]
    })


@app.route('/test/<lead_id>')
def test_walkthrough(lead_id):
    """Test walkthrough showing the full pitch experience for a real lead."""
    leads_path = LEADS_DIR / "all_leads.json"
    if not leads_path.exists():
        return "No leads found", 404

    with open(leads_path, 'r', encoding='utf-8') as f:
        leads = json.load(f)

    lead = next((l for l in leads if l.get('id') == lead_id), None)
    if not lead:
        return "Lead not found", 404

    business_name = lead.get('business_name', '')
    safe_name = re.sub(r'[^\w\s-]', '', business_name).strip().replace(' ', '_').lower()

    # Load outreach email
    email_content = ""
    email_path = OUTREACH_DIR / safe_name / "short_pitch.txt"
    if email_path.exists():
        with open(email_path, 'r', encoding='utf-8') as f:
            email_content = f.read()

    detailed_email = ""
    detailed_path = OUTREACH_DIR / safe_name / "detailed_pitch.txt"
    if detailed_path.exists():
        with open(detailed_path, 'r', encoding='utf-8') as f:
            detailed_email = f.read()

    thankyou_email = ""
    thankyou_path = OUTREACH_DIR / safe_name / "thank_you_post_payment.txt"
    if thankyou_path.exists():
        with open(thankyou_path, 'r', encoding='utf-8') as f:
            thankyou_email = f.read()

    # Load analysis
    analysis = {}
    analysis_path = ANALYSIS_DIR / f"analysis_{safe_name}.json"
    if analysis_path.exists():
        with open(analysis_path, 'r', encoding='utf-8') as f:
            analysis = json.load(f)

    has_site = (GENERATED_SITES_DIR / safe_name / 'index.html').exists()

    return render_template_string("""
    <!DOCTYPE html>
    <html>
    <head>
        <title>Test Walkthrough - {{ name }}</title>
        <script src="https://cdn.tailwindcss.com"></script>
        <link href="https://fonts.googleapis.com/css2?family=Inter:wght@300;400;500;600;700&display=swap" rel="stylesheet">
        <style>body{font-family:'Inter',sans-serif} .step{display:none} .step.active{display:block} pre{white-space:pre-wrap;word-wrap:break-word}</style>
    </head>
    <body class="bg-gray-100 min-h-screen">
        <div class="max-w-5xl mx-auto px-4 py-8">
            <a href="/dashboard" class="text-blue-600 hover:underline text-sm mb-4 inline-block">&larr; Back to Dashboard</a>
            <h1 class="text-3xl font-bold text-gray-900 mb-2">Test Walkthrough</h1>
            <p class="text-gray-500 mb-8">Simulating the full pitch experience for <strong>{{ name }}</strong></p>

            <!-- Step Navigation -->
            <div class="flex gap-2 mb-8 flex-wrap">
                <button onclick="showStep(0)" class="step-btn px-4 py-2 rounded-lg text-sm font-medium bg-blue-600 text-white">1. Lead Found</button>
                <button onclick="showStep(1)" class="step-btn px-4 py-2 rounded-lg text-sm font-medium bg-gray-200 text-gray-700">2. Analysis</button>
                <button onclick="showStep(2)" class="step-btn px-4 py-2 rounded-lg text-sm font-medium bg-gray-200 text-gray-700">3. Email Sent</button>
                <button onclick="showStep(3)" class="step-btn px-4 py-2 rounded-lg text-sm font-medium bg-gray-200 text-gray-700">4. Website Preview</button>
                <button onclick="showStep(4)" class="step-btn px-4 py-2 rounded-lg text-sm font-medium bg-gray-200 text-gray-700">5. They Reply</button>
                <button onclick="showStep(5)" class="step-btn px-4 py-2 rounded-lg text-sm font-medium bg-gray-200 text-gray-700">6. Payment</button>
                <button onclick="showStep(6)" class="step-btn px-4 py-2 rounded-lg text-sm font-medium bg-gray-200 text-gray-700">7. Thank You</button>
            </div>

            <!-- Step 0: Lead Found -->
            <div class="step active" id="step-0">
                <div class="bg-white rounded-xl shadow-sm p-8">
                    <h2 class="text-xl font-bold text-gray-900 mb-4">Step 1: Lead Discovered</h2>
                    <p class="text-gray-500 mb-6">The system found this business via Google Places API:</p>
                    <div class="grid grid-cols-2 gap-4 text-sm">
                        <div><span class="font-medium text-gray-700">Business:</span> {{ name }}</div>
                        <div><span class="font-medium text-gray-700">Category:</span> {{ lead.category }}</div>
                        <div><span class="font-medium text-gray-700">Address:</span> {{ lead.address }}</div>
                        <div><span class="font-medium text-gray-700">Phone:</span> {{ lead.phone or 'Not listed' }}</div>
                        <div><span class="font-medium text-gray-700">Website:</span> {{ lead.website or 'NONE - High Priority!' }}</div>
                        <div><span class="font-medium text-gray-700">Rating:</span> {{ lead.rating }} ({{ lead.review_count }} reviews)</div>
                    </div>
                    <div class="mt-6"><button onclick="showStep(1)" class="px-6 py-2 bg-blue-600 text-white rounded-lg font-medium hover:bg-blue-700">Next: See Analysis &rarr;</button></div>
                </div>
            </div>

            <!-- Step 1: Analysis -->
            <div class="step" id="step-1">
                <div class="bg-white rounded-xl shadow-sm p-8">
                    <h2 class="text-xl font-bold text-gray-900 mb-4">Step 2: Website Analysis</h2>
                    <div class="grid grid-cols-2 gap-4 text-sm mb-4">
                        <div><span class="font-medium">Score:</span> {{ analysis.get('total_score', 0) }}/100</div>
                        <div><span class="font-medium">Grade:</span> {{ analysis.get('grade', 'N/A') }}</div>
                        <div><span class="font-medium">Priority:</span> {{ analysis.get('priority', 'high') }}</div>
                    </div>
                    <h3 class="font-semibold mb-2">Issues Found:</h3>
                    <ul class="list-disc pl-6 text-sm text-gray-600 space-y-1">
                    {% for issue in analysis.get('issues', ['No website exists']) %}
                        <li>{{ issue }}</li>
                    {% endfor %}
                    </ul>
                    <div class="mt-6"><button onclick="showStep(2)" class="px-6 py-2 bg-blue-600 text-white rounded-lg font-medium hover:bg-blue-700">Next: See Email &rarr;</button></div>
                </div>
            </div>

            <!-- Step 2: Email Sent -->
            <div class="step" id="step-2">
                <div class="bg-white rounded-xl shadow-sm p-8">
                    <h2 class="text-xl font-bold text-gray-900 mb-4">Step 3: Pitch Email Sent</h2>
                    <p class="text-gray-500 mb-4">This is exactly what the business owner would receive:</p>
                    <div class="bg-gray-50 rounded-lg p-6 border border-gray-200">
                        <pre class="text-sm text-gray-800">{{ email }}</pre>
                    </div>
                    <div class="mt-6"><button onclick="showStep(3)" class="px-6 py-2 bg-blue-600 text-white rounded-lg font-medium hover:bg-blue-700">Next: See Website &rarr;</button></div>
                </div>
            </div>

            <!-- Step 3: Website Preview -->
            <div class="step" id="step-3">
                <div class="bg-white rounded-xl shadow-sm p-8">
                    <h2 class="text-xl font-bold text-gray-900 mb-4">Step 4: Generated Website</h2>
                    <p class="text-gray-500 mb-4">When they click the link, they see this professional website built for them:</p>
                    {% if has_site %}
                    <div class="border border-gray-200 rounded-lg overflow-hidden" style="height:600px">
                        <iframe src="/preview/{{ lead.id }}" class="w-full h-full"></iframe>
                    </div>
                    <a href="/preview/{{ lead.id }}" target="_blank" class="inline-block mt-3 text-blue-600 hover:underline text-sm">Open in new tab &rarr;</a>
                    {% else %}
                    <p class="text-gray-400">No website generated for this lead.</p>
                    {% endif %}
                    <div class="mt-6"><button onclick="showStep(4)" class="px-6 py-2 bg-blue-600 text-white rounded-lg font-medium hover:bg-blue-700">Next: They Reply &rarr;</button></div>
                </div>
            </div>

            <!-- Step 4: They Reply -->
            <div class="step" id="step-4">
                <div class="bg-white rounded-xl shadow-sm p-8">
                    <h2 class="text-xl font-bold text-gray-900 mb-4">Step 5: Business Owner Replies</h2>
                    <p class="text-gray-500 mb-4">Simulated reply from the business owner:</p>
                    <div class="bg-blue-50 rounded-lg p-6 border border-blue-200 mb-6">
                        <p class="text-sm text-gray-600 mb-1"><strong>From:</strong> {{ name }} &lt;owner@{{ name | lower | replace(' ','') }}.com&gt;</p>
                        <p class="text-sm text-gray-600 mb-3"><strong>Subject:</strong> Re: A new website for {{ name }}</p>
                        <p class="text-sm text-gray-800">"Hi, I checked out the website and it looks great! Can you change the phone number to (512) 555-0199 and add that we also do commercial work? Also can you make the colors a bit darker? Thanks!"</p>
                    </div>
                    <p class="text-gray-500 mb-4">The system processes changes and sends the updated site back:</p>
                    <div class="bg-green-50 rounded-lg p-6 border border-green-200">
                        <p class="text-sm text-gray-600 mb-1"><strong>From:</strong> WebLift &lt;{{ your_email }}&gt;</p>
                        <p class="text-sm text-gray-600 mb-3"><strong>Subject:</strong> Your updated website is ready - {{ name }}</p>
                        <p class="text-sm text-gray-800">Hi {{ name }} team,<br><br>We've made the changes you requested:<br>- Updated phone number to (512) 555-0199<br>- Added commercial services section<br>- Darkened the color scheme<br><br>Check out your updated website: [PREVIEW LINK]<br><br>If everything looks good, you can get it live for ${{ price }}: [PAYMENT LINK]<br><br>Best,<br>WebLift Team</p>
                    </div>
                    <div class="mt-6"><button onclick="showStep(5)" class="px-6 py-2 bg-blue-600 text-white rounded-lg font-medium hover:bg-blue-700">Next: Payment &rarr;</button></div>
                </div>
            </div>

            <!-- Step 5: Payment -->
            <div class="step" id="step-5">
                <div class="bg-white rounded-xl shadow-sm p-8">
                    <h2 class="text-xl font-bold text-gray-900 mb-4">Step 6: Payment</h2>
                    <p class="text-gray-500 mb-4">They click the payment link and see the Stripe checkout:</p>
                    <div class="max-w-md mx-auto bg-white border-2 border-gray-200 rounded-2xl p-8 text-center">
                        <h3 class="text-2xl font-bold mb-2">Professional Website</h3>
                        <p class="text-gray-500 mb-4">{{ name }}</p>
                        <div class="text-5xl font-bold text-green-600 mb-6">${{ price }}</div>
                        <ul class="text-left text-sm space-y-2 mb-6">
                            <li class="flex items-center gap-2"><span class="text-green-500">&#10003;</span> Complete responsive website</li>
                            <li class="flex items-center gap-2"><span class="text-green-500">&#10003;</span> Mobile-optimized design</li>
                            <li class="flex items-center gap-2"><span class="text-green-500">&#10003;</span> SEO optimized</li>
                            <li class="flex items-center gap-2"><span class="text-green-500">&#10003;</span> All source files</li>
                            <li class="flex items-center gap-2"><span class="text-green-500">&#10003;</span> Full setup guide</li>
                        </ul>
                        <button onclick="showStep(6)" class="w-full py-3 bg-blue-600 text-white font-bold rounded-lg hover:bg-blue-700">Pay ${{ price }} (simulated)</button>
                    </div>
                </div>
            </div>

            <!-- Step 6: Thank You -->
            <div class="step" id="step-6">
                <div class="bg-white rounded-xl shadow-sm p-8">
                    <h2 class="text-xl font-bold text-gray-900 mb-4">Step 7: Post-Payment</h2>
                    <p class="text-gray-500 mb-4">After payment, they automatically receive this email with the setup guide:</p>
                    <div class="bg-green-50 rounded-lg p-6 border border-green-200">
                        <pre class="text-sm text-gray-800">{{ thankyou }}</pre>
                    </div>
                    <div class="mt-8 p-6 bg-blue-50 rounded-xl text-center">
                        <p class="text-lg font-bold text-blue-900 mb-2">Walkthrough Complete!</p>
                        <p class="text-blue-700 text-sm">This is the full automated experience from discovery to delivery.</p>
                        <a href="/dashboard" class="inline-block mt-4 px-6 py-2 bg-blue-600 text-white rounded-lg font-medium hover:bg-blue-700">&larr; Back to Dashboard</a>
                    </div>
                </div>
            </div>
        </div>
        <script>
        function showStep(n){
            document.querySelectorAll('.step').forEach(s=>s.classList.remove('active'));
            document.getElementById('step-'+n).classList.add('active');
            document.querySelectorAll('.step-btn').forEach((b,i)=>{
                b.className = i===n ? 'step-btn px-4 py-2 rounded-lg text-sm font-medium bg-blue-600 text-white' : 'step-btn px-4 py-2 rounded-lg text-sm font-medium bg-gray-200 text-gray-700';
            });
            window.scrollTo(0,0);
        }
        </script>
    </body>
    </html>
    """, name=business_name, lead=lead, analysis=analysis, email=email_content,
         detailed=detailed_email, thankyou=thankyou_email, has_site=has_site,
         price=PRICE, your_email=YOUR_EMAIL)


if __name__ == "__main__":
    print(f"[+] Starting payment server on port {PAYMENT_SERVER_PORT}")
    print(f"[+] Dashboard: http://localhost:{PAYMENT_SERVER_PORT}/dashboard")
    app.run(host='0.0.0.0', port=PAYMENT_SERVER_PORT, debug=True)
