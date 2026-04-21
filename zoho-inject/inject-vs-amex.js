(function(){
  'use strict';

  // 1. Remove ALL existing <style> and <link rel="stylesheet"> from DOM
  document.querySelectorAll('style, link[rel="stylesheet"]').forEach(function(el){ el.remove(); });

  // 2. Inject reference CSS clean into <head>
  var style = document.createElement('style');
  style.textContent = `/* ─── VELTM DESIGN SYSTEM. Butler Button vs. Amex ──────────────────────
   Dark Apple-style. Indigo accent. Matches rest of Butler Button site.
   ──────────────────────────────────────────────────────────────────────── */

/* ─── RESET & BASE ────────────────────────────────────────────────────── */
*, *::before, *::after { box-sizing: border-box; margin: 0; padding: 0; }
html { scroll-behavior: smooth; }
body {
  font-family: -apple-system, BlinkMacSystemFont, 'SF Pro Display',
               'Helvetica Neue', Helvetica, Arial, sans-serif;
  background: #000;
  color: #f5f5f7;
  overflow-x: hidden;
  -webkit-font-smoothing: antialiased;
  -moz-osx-font-smoothing: grayscale;
}
img { display: block; max-width: 100%; }
a { text-decoration: none; color: inherit; }

/* ─── COLOR TOKENS ────────────────────────────────────────────────────── */
:root {
  --indigo:    #4f46e5;
  --indigo-lt: #818cf8;
  --dark:      #000;
  --dark-2:    #0a0a12;
  --dark-3:    #111;
  --gray-bg:   #f5f5f7;
  --white:     #fff;
  --text-dark: #1d1d1f;
  --text-mid:  #6e6e73;
  --text-mute: #86868b;
  --text-dim:  #3a3a3c;
}

/* ─── SCROLL PROGRESS BAR ─────────────────────────────────────────────── */
.scroll-progress {
  position: fixed; top: 0; left: 0; right: 0; height: 2px;
  background: var(--indigo); z-index: 2000;
  transform-origin: left; transform: scaleX(0);
}
@media (prefers-reduced-motion: no-preference) {
  @supports (animation-timeline: scroll()) {
    .scroll-progress {
      animation: grow-bar linear both;
      animation-duration: auto;
      animation-timeline: scroll(root block);
    }
  }
}
@keyframes grow-bar { from { transform: scaleX(0); } to { transform: scaleX(1); } }

/* ─── REVEAL SYSTEM ───────────────────────────────────────────────────── */
@media (prefers-reduced-motion: no-preference) {
  [data-reveal] {
    opacity: 0; transform: translateY(36px);
    transition:
      opacity   0.8s cubic-bezier(0.22, 1, 0.36, 1) var(--delay, 0s),
      transform 0.8s cubic-bezier(0.22, 1, 0.36, 1) var(--delay, 0s);
  }
  [data-reveal].visible { opacity: 1; transform: none; }
}

/* ─── NAV ─────────────────────────────────────────────────────────────── */
.nav {
  position: fixed; top: 0; left: 0; right: 0; z-index: 500;
  padding: 1.1rem 5vw;
  display: flex; align-items: center; justify-content: space-between;
  transition: background 0.4s ease, backdrop-filter 0.4s ease;
  background: rgba(0,0,0,0.72);
  backdrop-filter: blur(20px); -webkit-backdrop-filter: blur(20px);
  border-bottom: 1px solid rgba(255,255,255,0.04);
}
.nav-brand { font-size: 1rem; font-weight: 700; letter-spacing: -0.02em; color: #f5f5f7; }
.nav-brand em { color: var(--indigo-lt); font-style: normal; }
.nav-links { display: flex; gap: 2rem; list-style: none; }
.nav-links a {
  font-size: 0.82rem; color: rgba(255,255,255,0.55);
  letter-spacing: -0.01em; transition: color 0.2s;
}
.nav-links a:hover { color: #f5f5f7; }
.nav-book {
  padding: 8px 22px; background: var(--indigo); color: #fff;
  border-radius: 980px; font-size: 0.82rem; font-weight: 500;
  transition: background 0.2s, transform 0.15s;
}
.nav-book:hover { background: #4338ca; transform: scale(1.02); }
@media (max-width: 700px) { .nav-links { display: none; } }

/* ─── BUTTONS ─────────────────────────────────────────────────────────── */
.btn {
  display: inline-block; cursor: pointer; border: none;
  border-radius: 980px; font-weight: 500; letter-spacing: -0.01em;
  transition: transform 0.18s ease, box-shadow 0.18s ease, background 0.18s ease;
  text-decoration: none;
}
.btn:active { transform: scale(0.97) !important; }
.btn-lg { padding: 16px 40px; font-size: 1.05rem; }
.btn-md { padding: 12px 28px; font-size: 0.9rem; }
.btn-sm { padding: 9px 20px; font-size: 0.82rem; }
.btn-indigo { background: var(--indigo); color: #fff; }
.btn-indigo:hover { background: #4338ca; box-shadow: 0 8px 32px rgba(79,70,229,0.45); transform: scale(1.02); }
.btn-ghost-light { background: transparent; color: #f5f5f7; border: 1px solid rgba(255,255,255,0.22); }
.btn-ghost-light:hover { background: rgba(255,255,255,0.06); border-color: rgba(255,255,255,0.4); }

/* ─── EYEBROW ─────────────────────────────────────────────────────────── */
.eyebrow {
  display: block; font-size: 0.72rem; font-weight: 600;
  letter-spacing: 0.16em; text-transform: uppercase; margin-bottom: 1.2rem;
}
.eyebrow-soft   { color: var(--indigo-lt); }
.eyebrow-mute   { color: var(--text-mute); }

/* ─── HERO ────────────────────────────────────────────────────────────── */
.hero {
  min-height: 88vh;
  display: flex; flex-direction: column;
  align-items: center; justify-content: center;
  text-align: center;
  position: relative; overflow: clip;
  padding: 9rem 5vw 4rem;
}
.hero-bg {
  position: absolute; inset: 0;
  background: radial-gradient(ellipse 90% 70% at 50% 65%, #1a0a3e 0%, #000 68%);
}
.hero-grid {
  position: absolute; inset: 0;
  background-image: radial-gradient(circle, rgba(99,102,241,0.18) 1px, transparent 1px);
  background-size: 40px 40px;
  mask-image: radial-gradient(ellipse 70% 60% at 50% 60%, black 30%, transparent 80%);
  -webkit-mask-image: radial-gradient(ellipse 70% 60% at 50% 60%, black 30%, transparent 80%);
}
.hero-orb {
  position: absolute; width: 640px; height: 640px; border-radius: 50%;
  background: radial-gradient(circle, rgba(79,70,229,0.18) 0%, transparent 65%);
  top: 50%; left: 50%; transform: translate(-50%, -48%);
  animation: orb-pulse 5s ease-in-out infinite;
}
@keyframes orb-pulse {
  0%, 100% { opacity: 0.5; transform: translate(-50%,-48%) scale(1); }
  50%       { opacity: 1;   transform: translate(-50%,-48%) scale(1.12); }
}
.hero-content { position: relative; z-index: 2; max-width: 900px; width: 100%; }
.hero-badge {
  display: inline-flex; align-items: center; gap: 0.5rem;
  padding: 6px 14px 6px 8px;
  background: rgba(79,70,229,0.15); border: 1px solid rgba(129,140,248,0.25);
  border-radius: 980px; font-size: 0.75rem; color: var(--indigo-lt);
  letter-spacing: 0.04em; margin-bottom: 2rem;
}
.hero-badge-dot {
  width: 6px; height: 6px; border-radius: 50%;
  background: var(--indigo-lt); animation: dot-blink 2s ease-in-out infinite;
}
@keyframes dot-blink { 0%,100%{opacity:1} 50%{opacity:0.3} }
.hero-h1 {
  font-size: clamp(2.6rem, 6.5vw, 5.4rem);
  font-weight: 700; letter-spacing: -0.04em; line-height: 1.02;
  color: #f5f5f7; margin-bottom: 1.5rem;
}
.hero-h1 span { color: var(--indigo-lt); }
.hero-sub {
  font-size: clamp(1rem, 1.8vw, 1.18rem);
  color: rgba(255,255,255,0.62); max-width: 680px; margin: 0 auto 1.6rem;
  line-height: 1.55; letter-spacing: -0.01em;
}
.hero-actions { display: flex; gap: 1rem; justify-content: center; flex-wrap: wrap; }
.urgency-pill {
  display:inline-block; margin:.3rem auto 1.6rem;
  background:rgba(129,140,248,.14); color:var(--indigo-lt);
  border:1px solid rgba(129,140,248,.32); border-radius:999px;
  padding:6px 14px; font-size:.78rem; font-weight:600; letter-spacing:.005em;
}
.cta-guarantee { margin-top:1rem; font-size:.78rem; color:rgba(245,245,247,.66); letter-spacing:.005em; text-align:center; }

/* ─── MATH BLOCK ($225 vs $895) ───────────────────────────────────────── */
.math-section {
  background: var(--dark-2);
  padding: clamp(4rem, 9vw, 8rem) 5vw;
  border-top: 1px solid rgba(255,255,255,0.04);
}
.math-head { text-align: center; margin-bottom: 3rem; }
.math-head h2 {
  font-size: clamp(1.9rem, 4vw, 3rem);
  font-weight: 700; letter-spacing: -0.035em; line-height: 1.1;
  color: #f5f5f7; margin-bottom: 0.55rem;
}
.math-head p { font-size: 1rem; color: var(--text-mute); max-width: 520px; margin: 0 auto; }
.math-grid {
  max-width: 1040px; margin: 0 auto;
  display: grid; grid-template-columns: 1fr 1fr; gap: 1.5rem;
}
.math-card {
  border-radius: 22px; padding: 2.4rem 2rem; position: relative;
  border: 1px solid rgba(255,255,255,0.08);
}
.math-card--bb {
  background: linear-gradient(155deg, #1e1b4b 0%, #2e2878 100%);
  border-color: rgba(129,140,248,0.3);
}
.math-card--amex {
  background: rgba(255,255,255,0.03);
  border-color: rgba(255,255,255,0.07);
}
.math-tier {
  font-size: 0.68rem; font-weight: 700; letter-spacing: 0.14em;
  text-transform: uppercase; margin-bottom: 0.55rem;
}
.math-card--bb .math-tier { color: var(--indigo-lt); }
.math-card--amex .math-tier { color: var(--text-mute); }
.math-trip {
  font-size: 1.1rem; font-weight: 600; color: #f5f5f7;
  letter-spacing: -0.02em; margin-bottom: 1.4rem;
}
.math-card--amex .math-trip { color: rgba(245,245,247,0.78); }
.math-lines { list-style: none; margin-bottom: 1.2rem; }
.math-lines li {
  display: flex; justify-content: space-between; align-items: baseline;
  padding: 0.55rem 0; border-bottom: 1px dashed rgba(255,255,255,0.08);
  font-size: 0.93rem; letter-spacing: -0.005em;
}
.math-lines li .ml-label { color: rgba(245,245,247,0.72); }
.math-lines li .ml-val { font-weight: 600; color: #f5f5f7; }
.math-card--amex .math-lines li .ml-label { color: rgba(245,245,247,0.58); }
.math-card--amex .math-lines li .ml-val { color: rgba(245,245,247,0.78); }
.math-total {
  display: flex; justify-content: space-between; align-items: baseline;
  padding-top: 1rem; margin-top: 0.4rem;
  border-top: 1px solid rgba(255,255,255,0.12);
}
.math-total .mt-label {
  font-size: 0.72rem; font-weight: 700; letter-spacing: 0.12em;
  text-transform: uppercase; color: rgba(245,245,247,0.7);
}
.math-total .mt-val {
  font-size: clamp(2.4rem, 4.5vw, 3.2rem);
  font-weight: 700; letter-spacing: -0.045em; line-height: 1;
}
.math-card--bb .math-total .mt-val { color: var(--indigo-lt); }
.math-card--amex .math-total .mt-val { color: #f5f5f7; opacity: 0.85; }
.math-diff {
  max-width: 1040px; margin: 2.2rem auto 0;
  text-align: center; font-size: clamp(1rem, 2vw, 1.25rem);
  color: #f5f5f7; font-weight: 600; letter-spacing: -0.015em; line-height: 1.5;
}
.math-diff strong { color: var(--indigo-lt); font-weight: 700; }
.math-diff em { color: var(--text-mute); font-style: normal; font-weight: 400; }
@media (max-width: 820px) { .math-grid { grid-template-columns: 1fr; } }

/* ─── FEATURE COMPARISON TABLE ────────────────────────────────────────── */
.compare-section {
  background: #000;
  padding: clamp(4rem, 9vw, 8rem) 5vw;
  border-top: 1px solid rgba(255,255,255,0.04);
}
.compare-head { text-align: center; margin-bottom: 2.5rem; }
.compare-head h2 {
  font-size: clamp(1.9rem, 4vw, 3rem);
  font-weight: 700; letter-spacing: -0.035em; line-height: 1.1;
  color: #f5f5f7; margin-bottom: 0.55rem;
}
.compare-head p { font-size: 1rem; color: var(--text-mute); max-width: 520px; margin: 0 auto; }
.compare-table {
  max-width: 1040px; margin: 0 auto;
  border: 1px solid rgba(255,255,255,0.08); border-radius: 18px; overflow: hidden;
}
.compare-row {
  display: grid; grid-template-columns: 1.4fr 1.3fr 1.3fr;
  border-bottom: 1px solid rgba(255,255,255,0.05);
}
.compare-row:last-child { border-bottom: none; }
.compare-cell {
  padding: 1.05rem 1.2rem; font-size: 0.9rem; line-height: 1.45;
  color: rgba(245,245,247,0.75); letter-spacing: -0.005em;
  display: flex; align-items: center;
}
.compare-row.header .compare-cell {
  font-size: 0.68rem; font-weight: 700; letter-spacing: 0.12em;
  text-transform: uppercase; color: rgba(255,255,255,0.55);
  background: rgba(255,255,255,0.03);
}
.compare-cell.feat { font-weight: 600; color: #f5f5f7; font-size: 0.92rem; }
.compare-cell.bb {
  color: var(--indigo-lt); font-weight: 600;
  background: rgba(79,70,229,0.08);
}
.compare-row.header .compare-cell.bb { color: var(--indigo-lt); background: rgba(79,70,229,0.15); }
.compare-cell.amex { color: rgba(245,245,247,0.55); }
.compare-mark { font-weight: 700; margin-right: 0.45rem; flex-shrink: 0; }
.compare-mark.ok { color: var(--indigo-lt); }
.compare-mark.no { color: #ef4444; }
.compare-mark.warn { color: #f59e0b; }
@media (max-width: 720px) {
  .compare-row { grid-template-columns: 1fr; }
  .compare-row.header { display: none; }
  .compare-cell { border-bottom: 1px solid rgba(255,255,255,0.05); padding: 0.8rem 1rem; }
  .compare-cell.feat { background: rgba(255,255,255,0.03); }
}

/* ─── P.S. BLOCK ──────────────────────────────────────────────────────── */
.ps-block { background:#0a0a0a; border-top:1px solid rgba(255,255,255,.04); padding: clamp(3rem, 6vw, 5rem) 5vw; }
.ps-inner {
  max-width:860px; margin:0 auto;
  border-left:3px solid var(--indigo-lt);
  padding:1.2rem 1.8rem; background:rgba(129,140,248,.05);
}
.ps-inner p { font-size:1.02rem; color:rgba(245,245,247,.82); line-height:1.7; letter-spacing:-.005em; margin-bottom:.7rem; }
.ps-inner p strong { color: var(--indigo-lt); }
.ps-inner em { color: rgba(245,245,247,.65); font-style: italic; }
.ps-inner .ps-cta {
  display:inline-block; margin-top:.4rem; font-size:.88rem; font-weight:600;
  color:var(--indigo-lt); text-decoration:none;
  border-bottom:1px solid rgba(129,140,248,.4); padding-bottom:2px;
  transition: color 0.2s, border-color 0.2s;
}
.ps-inner .ps-cta:hover { color: #fff; border-color: #fff; }

/* ─── FOOTER ──────────────────────────────────────────────────────────── */
.site-footer {
  background: #000;
  border-top: 1px solid rgba(255,255,255,0.05);
  padding: 2.5rem 5vw;
  display: flex; align-items: center; justify-content: space-between;
  flex-wrap: wrap; gap: 1.5rem;
}
.footer-brand { font-size: 0.85rem; font-weight: 700; color: #86868b; }
.footer-brand em { color: var(--indigo-lt); font-style: normal; }
.footer-links { display: flex; gap: 1.5rem; list-style: none; flex-wrap: wrap; padding: 0; margin: 0; }
.footer-links a { font-size: 0.75rem; color: var(--text-dim); transition: color 0.2s; }
.footer-links a:hover { color: #86868b; }
.footer-legal { font-size: 0.72rem; color: var(--text-dim); }
@media (max-width: 720px) {
  .site-footer { justify-content: center; text-align: center; flex-direction: column; }
}
`;
  style.id = 'bb-styles';
  document.head.appendChild(style);

  // 3. MutationObserver: block Zoho from re-injecting styles; re-apply if body replaced
  (function(){
    var obs = new MutationObserver(function(mutations){
      mutations.forEach(function(m){
        m.addedNodes.forEach(function(node){
          if(node.nodeType !== 1) return;
          var tag = node.tagName && node.tagName.toLowerCase();
          if(tag === 'style' && node.id !== 'bb-styles') { node.remove(); return; }
          if(tag === 'link' && node.rel === 'stylesheet') { node.remove(); return; }
          if(tag === 'body') { applyBody(); return; }
        });
      });
    });
    obs.observe(document.documentElement, { childList: true, subtree: true });
  })();

  // 4. Body HTML stored for re-application by applyBody()
  var bodyHTML = `
<div class="scroll-progress"></div>
<nav class="nav">
  <a class="nav-brand" href="https://veltm-butler.zohosites.in/">Butler<em>Button</em></a>
  <ul class="nav-links">
    <li><a href="https://veltm-butler.zohosites.in/">Home</a></li>
    <li><a href="https://veltm-butler.zohosites.in/trip-planning">Trip Planning</a></li>
    <li><a href="https://veltm-butler.zohosites.in/concierge">Concierge</a></li>
    <li><a href="https://veltm-butler.zohosites.in/travel-advisor">Travel Advisor</a></li>
  </ul>
  <a class="nav-book" href="https://veltmtours.com/embed/butler-booking?popup=true" data-butler-button>Book Now. From $25</a>
</nav>

<section class="hero">
  <div class="hero-bg"></div>
  <div class="hero-grid"></div>
  <div class="hero-orb"></div>
  <div class="hero-content">
    <div class="hero-badge"><span class="hero-badge-dot"></span>Butler Button vs. Credit Card Concierge</div>
    <!-- Butler Button vs. your credit card concierge. -->
    <h1 class="hero-h1" data-reveal>Butler Button vs. <span>your credit card concierge.</span></h1>
    <p class="hero-sub" data-reveal style="--delay:0.1s">If you hold an Amex Platinum, Chase Sapphire Reserve, or Visa Infinite, you already have a &ldquo;concierge.&rdquo; Here&rsquo;s what that actually costs vs. what Butler Button costs.</p>
    <div class="urgency-pill" data-reveal style="--delay:.15s">● Available for May &amp; June trips. Launch pricing guaranteed through June 30</div>
    <div class="hero-actions" data-reveal style="--delay:0.2s">
      <a class="btn btn-indigo btn-lg" href="https://veltmtours.com/embed/butler-booking?popup=true" data-butler-button>Start Planning. $25/Trip Plan</a>
      <a class="btn btn-ghost-light btn-lg" href="https://veltmtours.com/embed/butler-booking?popup=true" data-butler-button>Get Concierge. From $25/Day</a>
    </div>
    <div class="cta-guarantee" data-reveal style="--delay:.3s">✓ Full refund before delivery &nbsp;·&nbsp; ✓ &lt;4 min human response &nbsp;·&nbsp; ✓ Cancel any time</div>
  </div>
</section>

<!-- ═══ THE $225 vs $895 MATH BLOCK ═══ -->
<section class="math-section">
  <div class="math-head" data-reveal>
    <span class="eyebrow eyebrow-soft">The real math</span>
    <h2>$225 vs. $895.</h2>
    <p>Same 8-day trip. Same kind of help. Very different bill.</p>
  </div>
  <div class="math-grid">
    <div class="math-card math-card--bb" data-reveal>
      <div class="math-tier">Butler Button</div>
      <div class="math-trip">One 8-day Tokyo trip</div>
      <ul class="math-lines">
        <li><span class="ml-label">Trip Plan</span><span class="ml-val">$25</span></li>
        <li><span class="ml-label">8-Hour Concierge &times; 8 days</span><span class="ml-val">$200</span></li>
      </ul>
      <div class="math-total"><span class="mt-label">Total</span><span class="mt-val">$225</span></div>
    </div>
    <div class="math-card math-card--amex" data-reveal style="--delay:0.1s">
      <div class="math-tier">Amex Platinum</div>
      <div class="math-trip">One 8-day Tokyo trip</div>
      <ul class="math-lines">
        <!-- Annual fee $695 -->
        <li><span class="ml-label">Annual fee</span><span class="ml-val">$695</span></li>
        <li><span class="ml-label">Premium concierge ~$25/day &times; 8</span><span class="ml-val">$200</span></li>
      </ul>
      <div class="math-total"><span class="mt-label">Total</span><span class="mt-val">$895</span></div>
    </div>
  </div>
  <p class="math-diff" data-reveal style="--delay:0.2s"><strong>$670 difference</strong>. <em>what a five-star hotel costs per night.</em></p>
</section>

<!-- ═══ FEATURE COMPARISON TABLE ═══ -->
<section class="compare-section">
  <div class="compare-head" data-reveal>
    <span class="eyebrow eyebrow-mute">Side by side</span>
    <h2>Feature by feature.</h2>
    <p>What the Platinum brochure promises vs. what actually happens at 11pm in Tokyo.</p>
  </div>
  <div class="compare-table" data-reveal>
    <div class="compare-row header">
      <div class="compare-cell">Feature</div>
      <div class="compare-cell bb">Butler Button</div>
      <div class="compare-cell">Credit card concierge</div>
    </div>
    <div class="compare-row">
      <div class="compare-cell feat">Pay only when you travel</div>
      <div class="compare-cell bb"><span class="compare-mark ok">✓</span>$25/day, cancel any time</div>
      <div class="compare-cell amex"><span class="compare-mark no">✗</span>$695-$895 annual fee whether you travel or not</div>
    </div>
    <div class="compare-row">
      <div class="compare-cell feat">Response time</div>
      <div class="compare-cell bb"><span class="compare-mark ok">✓</span>&lt;4 min to a human</div>
      <div class="compare-cell amex"><span class="compare-mark warn">⚠️</span>15-60 min via call center</div>
    </div>
    <div class="compare-row">
      <div class="compare-cell feat">Reads your itinerary before you leave</div>
      <div class="compare-cell bb"><span class="compare-mark ok">✓</span>Always</div>
      <div class="compare-cell amex"><span class="compare-mark no">✗</span>Never. Starts cold each call</div>
    </div>
    <div class="compare-row">
      <div class="compare-cell feat">Same advisor start to finish</div>
      <div class="compare-cell bb"><span class="compare-mark ok">✓</span>Yes</div>
      <div class="compare-cell amex"><span class="compare-mark no">✗</span>Random agent each time</div>
    </div>
    <div class="compare-row">
      <div class="compare-cell feat">Crisis rebookings at 11pm</div>
      <div class="compare-cell bb"><span class="compare-mark ok">✓</span>97% resolved &lt;60 min</div>
      <div class="compare-cell amex"><span class="compare-mark warn">⚠️</span>Business-hours only in practice</div>
    </div>
    <div class="compare-row">
      <div class="compare-cell feat">Trip planning included</div>
      <div class="compare-cell bb"><span class="compare-mark ok">✓</span>$25/country</div>
      <div class="compare-cell amex"><span class="compare-mark no">✗</span>Not included (upsell to travel portal)</div>
    </div>
    <div class="compare-row">
      <div class="compare-cell feat">Regional specialist</div>
      <div class="compare-cell bb"><span class="compare-mark ok">✓</span>Every advisor is a destination expert</div>
      <div class="compare-cell amex"><span class="compare-mark no">✗</span>Generalist call center</div>
    </div>
    <div class="compare-row">
      <div class="compare-cell feat">First contact</div>
      <div class="compare-cell bb"><span class="compare-mark ok">✓</span>100% human</div>
      <div class="compare-cell amex"><span class="compare-mark warn">⚠️</span>IVR / chatbot triage</div>
    </div>
  </div>
</section>

<!-- ═══ P.S. BLOCK (audit #8) ═══ -->
<section class="ps-block">
  <div class="ps-inner" data-reveal>
    <p><strong>P.S.</strong>. If you&rsquo;re already paying the annual fee, Butler Button is the thing you wish that concierge were. One client said it best: <em>&ldquo;I cancelled my Platinum after the first trip.&rdquo;</em></p>
    <a class="ps-cta" href="https://veltmtours.com/embed/butler-booking?popup=true" data-butler-button>Try Butler Button. From $25 →</a>
  </div>
</section>

<footer class="site-footer">
  <a class="footer-brand" href="https://veltm-butler.zohosites.in/">Butler<em>Button</em> by VELTM</a>
  <ul class="footer-links">
    <li><a href="https://veltm-butler.zohosites.in/">Home</a></li>
    <li><a href="#">Trip Planning</a></li>
    <li><a href="#">Concierge</a></li>
    <li><a href="#">Advisor</a></li>
    <li><a href="#">FAQ</a></li>
  </ul>
  <span class="footer-legal">&copy; 2026 VELTM Tours</span>
</footer>
<script src="https://lobodotstreehouse.github.io/butler-button-variants/js/veltm.js"></script>
<script>
(function(){
  if (window._bbModal) return;
  window._bbModal = true;
  var BB = 'https://veltmtours.com/embed/butler-booking?popup=true';
  function openModal() {
    var w = 660, h = 740;
    var left = Math.max(0, (screen.width  - w) / 2);
    var top  = Math.max(0, (screen.height - h) / 2);
    window.open(BB, 'butler_booking',
      'width=' + w + ',height=' + h +
      ',left=' + left + ',top=' + top +
      ',resizable=yes,scrollbars=yes,toolbar=no,menubar=no,location=no,status=no');
  }
  document.addEventListener('click', function(e){
    var t = e.target.closest('[data-butler-button]');
    if (t) { e.preventDefault(); openModal(); }
  });
})();
</script>
<script>
(function(){
  if (!('IntersectionObserver' in window)) {
    document.querySelectorAll('[data-reveal]').forEach(function(el){ el.classList.add('visible'); });
    return;
  }
  var io = new IntersectionObserver(function(entries){
    entries.forEach(function(e){
      if (e.isIntersecting) { e.target.classList.add('visible'); io.unobserve(e.target); }
    });
  }, { threshold: 0.12 });
  document.querySelectorAll('[data-reveal]').forEach(function(el){ io.observe(el); });
})();
</script>
`;

  // 5. applyBody: replace DOM content + re-exec scripts (hoisted, called below + by observer/interval)
  function applyBody() {
    document.body.innerHTML = bodyHTML;
    document.body.style.cssText = 'background:#000;margin:0;padding:0;overflow-x:hidden';
    Array.from(document.body.querySelectorAll('script')).forEach(function(oldScript){
      var newScript = document.createElement('script');
      if(oldScript.src) { newScript.src = oldScript.src; newScript.async = false; }
      else { newScript.textContent = oldScript.textContent; }
      oldScript.parentNode.replaceChild(newScript, oldScript);
    });
  }

  applyBody();
  document.documentElement.style.visibility = '';

  // 6. Periodic guard: re-inject if Zoho SPA overwrites our content (runs for 5s after load)
  var _bbN = 0;
  var _bbT = setInterval(function(){
    _bbN++;
    if (_bbN > 50) { clearInterval(_bbT); return; }
    if (!document.getElementById('bb-styles')) {
      document.querySelectorAll('style, link[rel="stylesheet"]').forEach(function(el){ el.remove(); });
      var s2 = document.createElement('style');
      s2.id = 'bb-styles';
      s2.textContent = style.textContent;
      document.head.appendChild(s2);
      applyBody();
    }
  }, 100);

})();
