(function(){
  'use strict';

  document.querySelectorAll('style, link[rel="stylesheet"]').forEach(function(el){ el.remove(); });

  var style = document.createElement('style');
  style.id = 'bb-styles';
  style.textContent = `
    *, *::before, *::after { box-sizing: border-box; margin: 0; padding: 0; }
    html { scroll-behavior: smooth; }
    body {
      font-family: -apple-system, BlinkMacSystemFont, 'SF Pro Display',
                   'Helvetica Neue', Helvetica, Arial, sans-serif;
      background: #000; color: #f5f5f7;
      overflow-x: hidden;
      -webkit-font-smoothing: antialiased;
      -moz-osx-font-smoothing: grayscale;
    }
    a { text-decoration: none; color: inherit; }
    :root {
      --indigo:    #4f46e5;
      --indigo-lt: #818cf8;
      --text-mid:  #6e6e73;
      --text-dim:  #3a3a3c;
    }

    /* ─── NAV ─── */
    .nav {
      position: fixed; top: 0; left: 0; right: 0; z-index: 500;
      padding: 1.1rem 5vw;
      display: flex; align-items: center; justify-content: space-between;
      background: rgba(0,0,0,0.88);
      backdrop-filter: blur(20px); -webkit-backdrop-filter: blur(20px);
      border-bottom: 1px solid rgba(255,255,255,0.06);
    }
    .nav-brand { font-size: 1rem; font-weight: 700; letter-spacing: -0.02em; color: #f5f5f7; }
    .nav-brand em { color: var(--indigo-lt); font-style: normal; }
    .nav-links { display: flex; gap: 2rem; list-style: none; }
    .nav-links a { font-size: 0.82rem; color: rgba(255,255,255,0.50); letter-spacing: -0.01em; transition: color 0.2s; }
    .nav-links a:hover { color: #f5f5f7; }
    .nav-book {
      padding: 8px 22px; background: var(--indigo); color: #fff;
      border-radius: 980px; font-size: 0.82rem; font-weight: 500;
      transition: background 0.2s;
    }
    .nav-book:hover { background: #4338ca; }
    @media (max-width: 700px) { .nav-links { display: none; } }

    /* ─── PAGE WRAPPER ─── */
    .doc-wrap {
      max-width: 780px; margin: 0 auto;
      padding: 10rem 5vw 8rem;
    }

    /* ─── DOCUMENT HEADER ─── */
    .doc-eyebrow {
      font-size: 0.68rem; font-weight: 700; letter-spacing: 0.18em;
      text-transform: uppercase; color: var(--indigo-lt);
      margin-bottom: 1.2rem; display: block;
    }
    .doc-title {
      font-size: clamp(2.2rem, 5vw, 3.4rem);
      font-weight: 700; letter-spacing: -0.04em; line-height: 1.08;
      color: #f5f5f7; margin-bottom: 1.8rem;
    }
    .doc-meta {
      font-size: 0.75rem; color: var(--text-mid); letter-spacing: 0.02em;
      padding-bottom: 2.4rem;
      border-bottom: 1px solid rgba(255,255,255,0.07);
      margin-bottom: 2.8rem;
    }
    .doc-intro {
      font-size: 1.05rem; line-height: 1.7; color: rgba(245,245,247,0.80);
      margin-bottom: 3rem; letter-spacing: -0.01em;
    }

    /* ─── SECTIONS ─── */
    .doc-section {
      margin-bottom: 2.8rem;
      padding-bottom: 2.8rem;
      border-bottom: 1px solid rgba(255,255,255,0.05);
    }
    .doc-section:last-of-type { border-bottom: none; }
    .doc-section-num {
      font-size: 0.63rem; font-weight: 700; letter-spacing: 0.15em;
      text-transform: uppercase; color: var(--indigo-lt);
      margin-bottom: 0.6rem; display: block;
    }
    .doc-section-title {
      font-size: 1.1rem; font-weight: 700; letter-spacing: -0.025em;
      color: #f5f5f7; margin-bottom: 0.9rem;
    }
    .doc-section p {
      font-size: 0.9rem; line-height: 1.75; color: rgba(245,245,247,0.65);
      letter-spacing: -0.005em;
    }
    .doc-section p + p { margin-top: 0.9rem; }

    /* ─── FOOTER ─── */
    .site-footer {
      background: #000; border-top: 1px solid rgba(255,255,255,0.05);
      padding: 2.5rem 5vw;
      display: flex; align-items: center; justify-content: space-between;
      flex-wrap: wrap; gap: 1.2rem;
    }
    .footer-brand { font-size: 0.85rem; font-weight: 700; color: #86868b; }
    .footer-brand em { color: var(--indigo-lt); font-style: normal; }
    .footer-links { display: flex; gap: 1.5rem; list-style: none; flex-wrap: wrap; padding: 0; margin: 0; }
    .footer-links a { font-size: 0.75rem; color: var(--text-dim); transition: color 0.2s; }
    .footer-links a:hover { color: #86868b; }
    .footer-legal { font-size: 0.72rem; color: var(--text-dim); }
    @media (max-width: 720px) { .site-footer { justify-content: center; text-align: center; flex-direction: column; } }
  `;
  document.head.appendChild(style);

  /* ─── MutationObserver — block Zoho re-injection ─── */
  (function(){
    var obs = new MutationObserver(function(mutations){
      mutations.forEach(function(m){
        m.addedNodes.forEach(function(node){
          if(node.nodeType !== 1) return;
          var tag = node.tagName && node.tagName.toLowerCase();
          if(tag === 'style' && node.id !== 'bb-styles') { node.remove(); return; }
          if(tag === 'link' && node.rel === 'stylesheet') { node.remove(); return; }
        });
      });
    });
    obs.observe(document.documentElement, { childList: true, subtree: true });
  })();

  document.body.innerHTML = `
<nav class="nav">
  <a class="nav-brand" href="/">Butler<em>Button</em></a>
  <ul class="nav-links">
    <li><a href="/">Home</a></li>
    <li><a href="/trip-planning">Trip Planning</a></li>
    <li><a href="/concierge">Concierge</a></li>
    <li><a href="/travel-advisor">Travel Advisor</a></li>
  </ul>
  <a class="nav-book" href="https://veltmtours.com/embed/butler-booking?popup=true">Book Now. From $25</a>
</nav>

<div class="doc-wrap">
  <span class="doc-eyebrow">Legal &amp; Compliance</span>
  <h1 class="doc-title">Supplier Code of&nbsp;Conduct</h1>
  <p class="doc-meta">Effective date: April 2026 &nbsp;·&nbsp; VELTM, Inc., operating as Butler Button &nbsp;·&nbsp; go.veltmtours.com</p>

  <p class="doc-intro">Butler Button welcomes quality travel service providers — hotels, ground transportation companies, aviation operators, experience vendors, and local specialists — into our supplier network to enhance the journey of our clients. To work with Butler Button's clients and advisors, please review and abide by the following Supplier Code of Conduct.</p>

  <div class="doc-section">
    <span class="doc-section-num">01</span>
    <h2 class="doc-section-title">Liability Indemnification</h2>
    <p>It is expressly agreed that VELTM, Inc. (d/b/a Butler Button) shall have no liability whatsoever in respect of the provision of goods or services by any supplier. You agree to indemnify VELTM, Inc. against any claims made by any person or entity in respect of any loss or damage caused directly or indirectly by the provision of your goods or services.</p>
  </div>

  <div class="doc-section">
    <span class="doc-section-num">02</span>
    <h2 class="doc-section-title">Professional Standards of Service</h2>
    <p>All goods and services for Butler Button clients will be performed in a professional manner and in accordance with the instructions provided at the time of booking. Our clients expect, and our advisors promise, a concierge experience that operates to an exceptional standard.</p>
    <p>If you are unable to provide services in the timeframe or manner requested, you must inform Butler Button no later than two (2) business days after a request is placed, or sooner if the timeline requires it. For time-sensitive travel requests (same-day or within 24 hours), you must notify us within one (1) hour of receiving the request.</p>
  </div>

  <div class="doc-section">
    <span class="doc-section-num">03</span>
    <h2 class="doc-section-title">Terms &amp; Conditions Disclosure</h2>
    <p>Any terms and conditions of booking — including cancellation, refund, deposit, and rescheduling policies — must be provided to Butler Button prior to engagement, or they shall have no effect on the client. Failure to disclose material terms at the outset of engagement may result in removal from the supplier network.</p>
  </div>

  <div class="doc-section">
    <span class="doc-section-num">04</span>
    <h2 class="doc-section-title">Insurance Requirements</h2>
    <p>You agree to maintain current General Liability insurance in an amount no less than $1,000,000 USD. For inherently higher-risk activities — including but not limited to ground transportation, yacht or boat charters, helicopter and private aviation charters, equestrian activities, water sports, or activities involving firearms — coverage of no less than $5,000,000 USD is required.</p>
    <p>Proof of coverage must be provided upon request. Butler Button reserves the right to suspend or remove any supplier who cannot demonstrate compliant coverage.</p>
  </div>

  <div class="doc-section">
    <span class="doc-section-num">05</span>
    <h2 class="doc-section-title">Non-Solicitation</h2>
    <p>As a supplier introduced through Butler Button, you and your affiliates shall not solicit, contact, or accept direct business from any client, contact, or partner brand made available to you through your relationship with Butler Button, without prior written consent. This includes direct outreach via any channel — phone, email, SMS, social media, or in person — for purposes outside of fulfilling an active Butler Button booking.</p>
    <p>Violation of this clause constitutes grounds for immediate removal from the supplier network and may be subject to legal remedy.</p>
  </div>

  <div class="doc-section">
    <span class="doc-section-num">06</span>
    <h2 class="doc-section-title">Non-Disparagement</h2>
    <p>You, your employees, and your affiliates agree to strict non-disparagement of VELTM, Inc. and Butler Button, our clients, our advisors, and our partner brands, whether written or oral, across any public or private channel, including social media, review platforms, and press.</p>
  </div>

  <div class="doc-section">
    <span class="doc-section-num">07</span>
    <h2 class="doc-section-title">Data Protection &amp; Privacy</h2>
    <p>As a Butler Button supplier, you warrant compliance with all applicable data protection and privacy laws, including the California Consumer Privacy Act (CCPA, 2018) and the General Data Protection Regulation (GDPR, 2018), as they apply to any personal data processed in connection with this relationship.</p>
    <p>You shall obtain all necessary consents for the processing of client personal data. You shall not retain, sell, or transfer any client data beyond what is strictly necessary to fulfill an active booking. All personal data must be processed and secured to a high standard of care. Each party shall indemnify the other against any loss arising from wrongful processing of personal data.</p>
  </div>

  <div class="doc-section">
    <span class="doc-section-num">08</span>
    <h2 class="doc-section-title">Payment Card Security (PCI Compliance)</h2>
    <p>You are responsible for the security of any cardholder data — credit or debit — that Butler Button provides to you by any means (verbally, electronically, or in writing). You must handle all payment data in full compliance with PCI DSS standards. Butler Button reserves the right to terminate any supplier relationship with immediate effect if security procedures do not meet acceptable standards.</p>
  </div>

  <div class="doc-section">
    <span class="doc-section-num">09</span>
    <h2 class="doc-section-title">Client Communication Standards</h2>
    <p>All communication with Butler Button clients must be conducted through the designated channel established at the time of booking. You shall not independently initiate contact with a client outside of an active engagement without the express coordination of a Butler Button advisor.</p>
    <p>Butler Button serves as the primary point of contact and relationship holder. Suppliers should direct all status updates, delays, or issues to the assigned advisor — not directly to the client — unless an emergency requires otherwise.</p>
  </div>

  <div class="doc-section">
    <span class="doc-section-num">10</span>
    <h2 class="doc-section-title">Confirmation &amp; Response Standards</h2>
    <p>Booking confirmations must be provided within two (2) hours of a standard request and within thirty (30) minutes of an urgent or same-day request. Failure to confirm within these windows may result in Butler Button securing an alternative supplier at no penalty to the client.</p>
    <p>All suppliers are expected to maintain availability monitoring and notify Butler Button immediately of any capacity constraints or service changes that may affect an active or upcoming booking.</p>
  </div>
</div>

<footer class="site-footer">
  <a class="footer-brand" href="/">Butler<em>Button</em> by VELTM</a>
  <ul class="footer-links">
    <li><a href="/">Home</a></li>
    <li><a href="/trip-planning">Trip Planning</a></li>
    <li><a href="/concierge">Concierge</a></li>
    <li><a href="/travel-advisor">Travel Advisor</a></li>
    <li><a href="/supplier-code">Supplier Code of Conduct</a></li>
    <li><a href="https://help.veltmtours.com/portal/en/kb/">Help Center</a></li>
  </ul>
  <span class="footer-legal">&copy; 2026 VELTM, Inc.</span>
</footer>
  `;

  document.body.style.cssText = 'background:#000;margin:0;padding:0;overflow-x:hidden';

  Array.from(document.body.querySelectorAll('script')).forEach(function(oldScript){
    var newScript = document.createElement('script');
    if(oldScript.src){ newScript.src = oldScript.src; newScript.async = false; }
    else { newScript.textContent = oldScript.textContent; }
    oldScript.parentNode.replaceChild(newScript, oldScript);
  });

  document.documentElement.style.visibility = '';
  document.documentElement.style.background = '';
})();
