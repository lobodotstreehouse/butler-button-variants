(function(){
  'use strict';

  // 1. Remove ALL existing <style> and <link rel="stylesheet"> from DOM
  document.querySelectorAll('style, link[rel="stylesheet"]').forEach(function(el){ el.remove(); });

  // 2. Inject reference CSS clean into <head>
  var style = document.createElement('style');
  style.textContent = `/* ─── VELTM DESIGN SYSTEM. Butler Button Variants ────────────────────────
   Extracted from showcase/v2. Dark Apple-style. Indigo accent.
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
  [data-reveal-left] {
    opacity: 0; transform: translateX(-48px);
    transition:
      opacity   0.9s cubic-bezier(0.22, 1, 0.36, 1) var(--delay, 0s),
      transform 0.9s cubic-bezier(0.22, 1, 0.36, 1) var(--delay, 0s);
  }
  [data-reveal-left].visible { opacity: 1; transform: none; }
  [data-reveal-right] {
    opacity: 0; transform: translateX(48px);
    transition:
      opacity   0.9s cubic-bezier(0.22, 1, 0.36, 1) var(--delay, 0s),
      transform 0.9s cubic-bezier(0.22, 1, 0.36, 1) var(--delay, 0s);
  }
  [data-reveal-right].visible { opacity: 1; transform: none; }
}

/* ─── NAV ─────────────────────────────────────────────────────────────── */
.nav {
  position: fixed; top: 0; left: 0; right: 0; z-index: 500;
  padding: 1.1rem 5vw;
  display: flex; align-items: center; justify-content: space-between;
  transition: background 0.4s ease, backdrop-filter 0.4s ease;
}
.nav.bg {
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

/* ─── BACK LINK ───────────────────────────────────────────────────────── */
.back-bar {
  position: fixed; top: 0; left: 0; right: 0; z-index: 600;
  padding: 6px 5vw;
  background: rgba(0,0,0,0.9);
  backdrop-filter: blur(12px); -webkit-backdrop-filter: blur(12px);
  display: flex; align-items: center; justify-content: space-between;
  border-bottom: 1px solid rgba(255,255,255,0.05);
}
.back-bar a {
  font-size: 0.72rem; color: var(--indigo-lt);
  letter-spacing: 0.01em;
  transition: color 0.2s;
}
.back-bar a:hover { color: #fff; }
.back-bar .back-bar-label {
  font-size: 0.65rem; color: rgba(255,255,255,0.25);
  letter-spacing: 0.06em; text-transform: uppercase;
}

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
.btn-white { background: #fff; color: var(--text-dark); }
.btn-white:hover { background: #f0f0f5; transform: scale(1.02); }
.btn-ghost-light { background: transparent; color: #f5f5f7; border: 1px solid rgba(255,255,255,0.22); }
.btn-ghost-light:hover { background: rgba(255,255,255,0.06); border-color: rgba(255,255,255,0.4); }
.btn-ghost-dark { background: transparent; color: var(--indigo); border: 1.5px solid var(--indigo); }
.btn-ghost-dark:hover { background: var(--indigo); color: #fff; }
.btn-outline-light { background: rgba(255,255,255,0.07); color: var(--indigo-lt); border: 1px solid rgba(129,140,248,0.3); }
.btn-outline-light:hover { background: rgba(255,255,255,0.12); }

/* ─── EYEBROW ─────────────────────────────────────────────────────────── */
.eyebrow {
  display: block; font-size: 0.72rem; font-weight: 600;
  letter-spacing: 0.16em; text-transform: uppercase; margin-bottom: 1.2rem;
}
.eyebrow-indigo { color: var(--indigo); }
.eyebrow-soft   { color: var(--indigo-lt); }
.eyebrow-mute   { color: var(--text-mute); }

/* ─── HERO SCAFFOLD ───────────────────────────────────────────────────── */
.hero {
  min-height: 100vh;
  display: flex; flex-direction: column;
  align-items: center; justify-content: center;
  text-align: center;
  position: relative; overflow: clip;
  padding: 8rem 5vw 5rem;
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
.hero-ring {
  position: absolute; width: 420px; height: 420px; border-radius: 50%;
  border: 1px solid rgba(99,102,241,0.12);
  top: 50%; left: 50%; transform: translate(-50%, -50%);
  animation: ring-spin 20s linear infinite;
}
.hero-ring-2 { width: 620px; height: 620px; border-color: rgba(99,102,241,0.06); animation-duration: 30s; animation-direction: reverse; }
@keyframes ring-spin { to { transform: translate(-50%,-50%) rotate(360deg); } }
.hero-content {
  position: relative; z-index: 2;
  max-width: 860px; width: 100%;
}
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
  font-size: clamp(3.2rem, 8.5vw, 7.5rem);
  font-weight: 700; letter-spacing: -0.04em; line-height: 0.97;
  color: #f5f5f7; margin-bottom: 1.5rem;
}
.hero-h1 span { color: var(--indigo-lt); }
.hero-h1-lg {
  font-size: clamp(2.4rem, 6vw, 5.5rem);
  font-weight: 700; letter-spacing: -0.04em; line-height: 1.05;
  color: #f5f5f7; margin-bottom: 1.5rem;
}
.hero-h1-lg span { color: var(--indigo-lt); }
.hero-sub {
  font-size: clamp(1rem, 1.8vw, 1.2rem);
  color: rgba(255,255,255,0.5); max-width: 520px; margin: 0 auto 2.5rem;
  line-height: 1.6; letter-spacing: -0.01em;
}
.hero-actions {
  display: flex; gap: 1rem; justify-content: center; flex-wrap: wrap;
}

/* ─── STATS STRIP ─────────────────────────────────────────────────────── */
.section-stats {
  background: #000;
  padding: clamp(4rem, 8vw, 7rem) 5vw;
  border-top: 1px solid rgba(255,255,255,0.04);
}
.stats-inner {
  max-width: 1040px; margin: 0 auto;
  display: grid; grid-template-columns: repeat(4, 1fr);
  gap: 2rem; text-align: center;
}
.stat-num {
  font-size: clamp(3rem, 6vw, 5rem);
  font-weight: 700; letter-spacing: -0.045em; line-height: 1;
  color: #f5f5f7; margin-bottom: 0.5rem;
}
.stat-num sup { font-size: 0.5em; vertical-align: super; color: var(--indigo-lt); }
.stat-label { font-size: 0.82rem; color: var(--text-mute); letter-spacing: -0.01em; }
@media (max-width: 700px) { .stats-inner { grid-template-columns: 1fr 1fr; } }

/* ─── PRODUCT CARDS ───────────────────────────────────────────────────── */
.section-products {
  background: var(--dark-2);
  padding: clamp(5rem, 10vw, 9rem) 5vw;
}
.section-head { text-align: center; margin-bottom: 3.5rem; }
.section-title-light {
  font-size: clamp(2rem, 4.5vw, 3.6rem);
  font-weight: 700; letter-spacing: -0.035em; line-height: 1.1;
  color: #f5f5f7; margin-bottom: 0.75rem;
}
.section-sub-light {
  font-size: 1.05rem; color: var(--text-mute);
  max-width: 460px; margin: 0 auto; letter-spacing: -0.01em;
}
.products-grid {
  max-width: 1080px; margin: 0 auto;
  display: grid; grid-template-columns: repeat(3, 1fr);
  gap: 1.25rem;
}
.pcard {
  background: rgba(255,255,255,0.04); border-radius: 22px;
  border: 1px solid rgba(255,255,255,0.08);
  padding: 2.5rem 2rem 2rem;
  position: relative; overflow: hidden;
  transition: transform 0.3s cubic-bezier(0.22,1,0.36,1), box-shadow 0.3s ease, border-color 0.3s ease;
  cursor: pointer;
}
.pcard:hover { transform: translateY(-5px); box-shadow: 0 24px 60px rgba(79,70,229,0.12); border-color: rgba(129,140,248,0.25); }
.pcard--featured { background: linear-gradient(155deg, #1e1b4b 0%, #2e2878 100%); border-color: rgba(129,140,248,0.3); }
.pcard__badge {
  position: absolute; top: 1.5rem; right: 1.5rem;
  font-size: 0.65rem; font-weight: 700; letter-spacing: 0.1em;
  text-transform: uppercase; color: #fff;
  background: var(--indigo-lt); padding: 4px 10px; border-radius: 20px;
}
.pcard__bar { width: 36px; height: 3px; border-radius: 2px; margin-bottom: 2rem; }
.pcard--trip     .pcard__bar { background: var(--indigo); }
.pcard--featured .pcard__bar { background: var(--indigo-lt); }
.pcard--elite    .pcard__bar { background: #7c3aed; }
.pcard__tier {
  font-size: 0.68rem; font-weight: 600; letter-spacing: 0.14em;
  text-transform: uppercase; margin-bottom: 0.4rem;
}
.pcard--trip     .pcard__tier { color: var(--text-mute); }
.pcard--featured .pcard__tier { color: var(--indigo-lt); }
.pcard--elite    .pcard__tier { color: var(--text-mute); }
.pcard__name {
  font-size: 1.45rem; font-weight: 700;
  letter-spacing: -0.025em; line-height: 1.2; margin-bottom: 1.5rem;
}
.pcard--trip     .pcard__name { color: #f5f5f7; }
.pcard--featured .pcard__name { color: #f5f5f7; }
.pcard--elite    .pcard__name { color: #f5f5f7; }
.pcard__price-row { display: flex; align-items: baseline; gap: 0.25rem; margin-bottom: 0.2rem; }
.pcard__price { font-size: clamp(2.4rem, 4vw, 3.2rem); font-weight: 700; letter-spacing: -0.045em; }
.pcard--trip     .pcard__price { color: var(--indigo-lt); }
.pcard--featured .pcard__price { color: var(--indigo-lt); }
.pcard--elite    .pcard__price { color: #a78bfa; }
.pcard__unit { font-size: 0.8rem; letter-spacing: -0.01em; }
.pcard--trip     .pcard__unit { color: var(--text-mute); }
.pcard--featured .pcard__unit { color: rgba(199,210,254,0.8); }
.pcard--elite    .pcard__unit { color: var(--text-mute); }
.pcard__divider { border: none; border-top: 1px solid rgba(255,255,255,0.07); margin: 1.5rem 0; }
.pcard__features { list-style: none; margin-bottom: 2rem; }
.pcard__features li {
  font-size: 0.88rem; padding: 0.45rem 0;
  border-bottom: 1px solid rgba(255,255,255,0.05);
  display: flex; gap: 0.5rem; letter-spacing: -0.01em;
  color: rgba(199,210,254,0.75);
}
.pcard--featured .pcard__features li { color: rgba(199,210,254,0.85); border-bottom-color: rgba(255,255,255,0.06); }
.pcard__features li::before { content: '\\2713'; font-weight: 700; flex-shrink: 0; }
.pcard--trip     .pcard__features li::before { color: var(--indigo-lt); }
.pcard--featured .pcard__features li::before { color: var(--indigo-lt); }
.pcard--elite    .pcard__features li::before { color: #a78bfa; }
.pcard .btn { width: 100%; text-align: center; }
@media (max-width: 820px) { .products-grid { grid-template-columns: 1fr; max-width: 420px; margin: 0 auto; } }

/* ─── SCENARIOS SECTION ───────────────────────────────────────────────── */
.section-scenarios {
  background: #000;
  padding: clamp(5rem, 10vw, 9rem) 5vw;
  border-top: 1px solid rgba(255,255,255,0.04);
}
.scenarios-grid {
  max-width: 1080px; margin: 0 auto;
  display: grid; grid-template-columns: repeat(3, 1fr);
  gap: 1.25rem;
}
.scard {
  background: var(--dark-3); border: 1px solid rgba(255,255,255,0.05);
  border-radius: 20px; padding: 2rem;
  transition: border-color 0.3s ease, transform 0.3s ease, box-shadow 0.3s ease;
  display: block; text-decoration: none; color: inherit; cursor: pointer;
}
.scard:hover {
  border-color: rgba(99,102,241,0.35);
  transform: translateY(-4px);
  box-shadow: 0 16px 48px rgba(79,70,229,0.12);
}
.scard__where {
  font-size: 0.68rem; font-weight: 700; letter-spacing: 0.14em;
  text-transform: uppercase; color: var(--indigo-lt); margin-bottom: 1.1rem;
}
.scard__situation {
  font-size: 1.05rem; font-weight: 600; color: #f5f5f7;
  letter-spacing: -0.02em; line-height: 1.45; margin-bottom: 1rem;
}
.scard__outcome {
  font-size: 0.88rem; color: var(--text-mute);
  line-height: 1.65; letter-spacing: -0.01em;
}
.scard__tag {
  display: inline-flex; align-items: center; gap: 4px; margin-top: 1.5rem;
  font-size: 0.75rem; font-weight: 600;
  color: var(--indigo-lt); letter-spacing: -0.01em;
}
@media (max-width: 820px) { .scenarios-grid { grid-template-columns: 1fr; max-width: 500px; margin: 0 auto; } }

/* ─── FOOTER (showcase/v2 single-row layout) ──────────────────────────── */
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

/* ─── WINNER BADGE ────────────────────────────────────────────────────── */
.winner-tab {
  position: fixed; top: 60px; right: 0; z-index: 400;
  background: var(--indigo); color: #fff;
  font-size: 0.65rem; font-weight: 700; letter-spacing: 0.1em; text-transform: uppercase;
  padding: 8px 16px 8px 14px;
  border-top-left-radius: 8px; border-bottom-left-radius: 8px;
  box-shadow: -4px 4px 24px rgba(79,70,229,0.4);
}
.runner-tab {
  position: fixed; top: 60px; right: 0; z-index: 400;
  background: rgba(129,140,248,0.15); color: var(--indigo-lt);
  border: 1px solid rgba(129,140,248,0.3);
  font-size: 0.65rem; font-weight: 700; letter-spacing: 0.1em; text-transform: uppercase;
  padding: 8px 16px 8px 14px;
  border-top-left-radius: 8px; border-bottom-left-radius: 8px;
  border-right: none;
}

/* ─── SECTION TITLE HELPERS ───────────────────────────────────────────── */
.section-title-dark {
  font-size: clamp(2rem, 4.5vw, 3.6rem);
  font-weight: 700; letter-spacing: -0.035em; line-height: 1.1;
  color: #f5f5f7; margin-bottom: 0.75rem;
}
.section-sub-dark {
  font-size: 1.05rem; color: var(--text-mute);
  max-width: 460px; margin: 0 auto; letter-spacing: -0.01em;
}


  .hero { min-height: 100vh; background: #000; align-items: center; justify-content: center; padding-top: 8rem; }
  .hero-content { max-width: 860px; }

  /* AI compare */
  .anti-ai-section { background: var(--dark-2); padding: clamp(5rem,10vw,9rem) 5vw; border-top: 1px solid rgba(255,255,255,0.04); }
  .ai-compare { max-width: 1080px; margin: 2.5rem auto 0; display: grid; grid-template-columns: 1fr 1fr 1fr; gap: 1.25rem; }
  .ai-col { border-radius: 18px; padding: 1.75rem; }
  .ai-col.ai-bad { background: rgba(255,255,255,0.03); border: 1px solid rgba(255,255,255,0.06); }
  .ai-col.ai-good { background: rgba(79,70,229,0.1); border: 1px solid rgba(129,140,248,0.25); }
  .ai-col-label { font-size: 0.62rem; font-weight: 700; letter-spacing: 0.12em; text-transform: uppercase; color: var(--text-mute); margin-bottom: 0.75rem; }
  .ai-col.ai-good .ai-col-label { color: var(--indigo-lt); }
  .ai-col h3 { font-size: 0.88rem; font-weight: 700; color: rgba(255,255,255,0.5); margin-bottom: 1rem; font-style: italic; }
  .ai-col.ai-good h3 { color: #f5f5f7; font-style: normal; }
  .ai-item { font-size: 0.78rem; color: rgba(255,255,255,0.35); padding: 0.45rem 0; border-bottom: 1px solid rgba(255,255,255,0.04); display: flex; gap: 0.5rem; }
  .ai-item::before { content: '\\2715'; color: rgba(255,100,100,0.5); flex-shrink: 0; font-weight: 700; }
  .ai-col.ai-good .ai-item { color: rgba(199,210,254,0.75); }
  .ai-col.ai-good .ai-item::before { content: '\\2713'; color: var(--indigo-lt); }

  @media (max-width:720px) { .ai-compare { grid-template-columns:1fr; } }

  /* Dissection section */
  .diss-section { background: #000; padding: clamp(5rem,10vw,9rem) 5vw; border-top: 1px solid rgba(255,255,255,0.04); }
  .diss-inner { max-width: 760px; margin: 0 auto; }
  .diss-inner h2 { margin-bottom: 0.5rem; }
  .diss-box { margin-top: 3rem; border: 1px solid rgba(255,255,255,0.08); border-radius: 18px; overflow: hidden; }
  .diss-box h3 { font-size: 0.72rem; font-weight: 700; letter-spacing: 0.1em; text-transform: uppercase; color: rgba(255,255,255,0.3); padding: 1rem 1.5rem 0.75rem; border-bottom: 1px solid rgba(255,255,255,0.06); }
  .diss-line { display: flex; justify-content: space-between; align-items: baseline; gap: 1rem; padding: 0.85rem 1.5rem; border-bottom: 1px solid rgba(255,255,255,0.04); }
  .diss-item { font-size: 0.84rem; color: rgba(255,255,255,0.45); line-height: 1.4; }
  .diss-item small { display: block; font-size: 0.7rem; color: rgba(255,255,255,0.25); margin-top: 0.2rem; }
  .diss-cost { font-size: 0.84rem; font-weight: 600; white-space: nowrap; }
  .cost-included { color: rgba(255,255,255,0.25); }
  .cost-real { color: rgba(250,204,21,0.8); }
  .diss-total { display: flex; justify-content: space-between; align-items: center; gap: 1rem; padding: 1rem 1.5rem; background: rgba(250,204,21,0.06); }
  .diss-total-label { font-size: 0.8rem; color: rgba(250,204,21,0.7); font-weight: 600; }
  .diss-total-price { font-size: 1.1rem; font-weight: 800; color: rgba(250,204,21,0.9); }
  .diss-vs { margin-top: 2rem; padding: 2rem; background: rgba(79,70,229,0.1); border: 1px solid rgba(129,140,248,0.2); border-radius: 18px; }
  .diss-vs-label { font-size: 0.62rem; font-weight: 700; letter-spacing: 0.14em; text-transform: uppercase; color: var(--indigo-lt); margin-bottom: 0.5rem; }
  .diss-vs-price { display: flex; align-items: baseline; gap: 0.25rem; line-height: 1; margin-bottom: 0.5rem; }
  .diss-vs-amount { font-size: 3rem; font-weight: 800; letter-spacing: -0.04em; color: #f5f5f7; }
  .diss-vs-per { font-size: 1.2rem; font-weight: 400; color: var(--text-mute); }
  .diss-vs-unit { font-size: 0.84rem; color: var(--text-mute); }

  /* photo-background sections */
  .section-products, .anti-ai-section, .section-scenarios {
    position: relative;
    background-size: cover;
    background-position: center;
    background-repeat: no-repeat;
  }
  .section-products::before, .anti-ai-section::before, .section-scenarios::before {
    content: '';
    position: absolute; inset: 0;
    background: rgba(0,0,0,0.72);
    z-index: 0;
  }
  .section-products > *, .anti-ai-section > *, .section-scenarios > * { position: relative; z-index: 1; }

  /* ─── AUDIT ADDITIONS (conversion-rate audit) ────────────────────────── */
  .stat-because { margin-top: .65rem; font-size: 0.72rem; line-height: 1.5; color: rgba(245,245,247,0.55); max-width: 230px; margin-left:auto; margin-right:auto; text-align:center; }
  .stats-footnote { margin-top: 2.2rem; font-size: 0.68rem; color: rgba(245,245,247,0.38); text-align: center; letter-spacing: .005em; max-width: 720px; margin-left:auto; margin-right:auto; }
  .urgency-pill { display:inline-block; margin:.6rem auto 1.2rem; background:rgba(129,140,248,.14); color:var(--indigo-lt); border:1px solid rgba(129,140,248,.32); border-radius:999px; padding:6px 14px; font-size:.78rem; font-weight:600; letter-spacing:.005em; }
  .cta-guarantee { margin-top:1rem; font-size:.78rem; color:rgba(245,245,247,.66); letter-spacing:.005em; text-align:center; }
  .pcard__guarantee { margin-top:.85rem; font-size:.72rem; line-height:1.5; color:rgba(245,245,247,.55); letter-spacing:.005em; }
  .pcard__guarantee--light { color:rgba(245,245,247,.66); }
  .ps-block { background:#0a0a0a; border-top:1px solid rgba(255,255,255,.04); padding: clamp(2.5rem, 5vw, 4rem) 5vw; }
  .ps-inner { max-width:820px; margin:0 auto; border-left:3px solid var(--indigo-lt); padding:1rem 1.6rem; background:rgba(129,140,248,.05); }
  .ps-inner p { font-size:1rem; color:rgba(245,245,247,.78); line-height:1.65; letter-spacing:-.005em; margin-bottom:.6rem; }
  .ps-inner .ps-cta { display:inline-block; margin-top:.3rem; font-size:.82rem; font-weight:600; color:var(--indigo-lt); text-decoration:none; border-bottom:1px solid rgba(129,140,248,.4); padding-bottom:2px; }
  .lead-magnet { background:#0a0a0a; border-top:1px solid rgba(255,255,255,.04); padding: clamp(3rem, 6vw, 5rem) 5vw; }
  .lm-inner { max-width:760px; margin:0 auto; background: linear-gradient(135deg, #1e1b4b 0%, #312e81 100%); border:1px solid rgba(129,140,248,.22); border-radius:18px; padding: clamp(1.8rem, 3.5vw, 2.6rem); display:grid; grid-template-columns: 1fr auto; gap:2rem; align-items:center; }
  .lm-headline { font-size:clamp(1.1rem, 2.2vw, 1.45rem); font-weight:700; color:#f5f5f7; letter-spacing:-.02em; margin-bottom:.35rem; line-height:1.28; }
  .lm-sub { font-size:.88rem; color:rgba(199,210,254,.85); line-height:1.5; }
  .lm-form { display:flex; gap:.6rem; align-items:stretch; }
  .lm-form input { background:rgba(0,0,0,.35); border:1px solid rgba(255,255,255,.14); border-radius:10px; padding:.72rem .9rem; color:#f5f5f7; font-size:.88rem; min-width:220px; outline:none; font-family:inherit; }
  .lm-form input::placeholder { color:rgba(199,210,254,.5); }
  .lm-form input:focus { border-color:var(--indigo-lt); background:rgba(0,0,0,.55); }
  .lm-form button { background:var(--indigo-lt); color:#0a0a0a; border:none; border-radius:10px; padding:.72rem 1.1rem; font-weight:700; font-size:.82rem; letter-spacing:.01em; cursor:pointer; font-family:inherit; white-space:nowrap; }
  .lm-form button:hover { background:#fff; }
  .lm-privacy { grid-column:1/-1; font-size:.68rem; color:rgba(199,210,254,.55); margin-top:.35rem; }
  @media (max-width:680px){ .lm-inner { grid-template-columns:1fr; } .lm-form { flex-direction:column; } .lm-form input { min-width:0; width:100%; } }
`;
  style.id = 'bb-styles';
  document.head.appendChild(style);

  // 3. MutationObserver: block Zoho from re-injecting styles after clean-slate
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

  // 4. Replace body content entirely
  document.body.innerHTML = `<div class="scroll-progress"></div>
<nav class="nav">
  <a class="nav-brand" href="https://veltm-butler.zohosites.in/">Butler<em>Button</em></a>
  <ul class="nav-links">
    <li><a href="https://veltm-butler.zohosites.in/">Home</a></li><li><a href="https://veltm-butler.zohosites.in/trip-planning">Trip Planning</a></li><li><a href="https://veltm-butler.zohosites.in/concierge">Concierge</a></li>
    <li><a href="https://veltm-butler.zohosites.in/travel-advisor">Travel Advisor</a></li>
  </ul>
  <a class="nav-book" href="https://veltmtours.com/embed/butler-booking?popup=true" data-butler-button>Book Now. From $25</a>
</nav>

<section class="hero">
  <div class="hero-bg"></div>
  <div class="hero-grid"></div>
  <div class="hero-orb"></div>
  <div class="hero-ring"></div><div class="hero-ring hero-ring-2"></div>
  <div class="hero-content">
    <div class="hero-badge"><span class="hero-badge-dot"></span>Concierge. Butler Button</div>
    <h1 class="hero-h1" data-reveal>Not a Chatbot.<br>A Real Person Who<br><span>Already Knows Your Trip.</span></h1>
    <p class="hero-sub" data-reveal style="--delay:0.1s">ChatGPT doesn't know your return flight is at 6am. Siri can't rebook you when it's cancelled at 11pm. Your Butler already has your itinerary. That's the difference.</p>
    <div class="urgency-pill" data-reveal style="--delay:0.15s">&#9679; Available for May &amp; June trips. Launch pricing guaranteed through June 30</div>
    <div class="hero-actions" data-reveal style="--delay:0.2s">
      <a class="btn btn-indigo btn-lg" href="https://veltmtours.com/embed/butler-booking?popup=true" data-butler-button>Get Your Butler. From $25/Day</a>
    </div>
    <div class="cta-guarantee" data-reveal style="--delay:0.3s">&#10003; Cancel any time. Pay only for days used &nbsp;&middot;&nbsp; &#10003; Human response in &lt;4 min</div>
  </div>
</section>

<section class="section-products">
  <div class="section-head" data-reveal>
    <span class="eyebrow eyebrow-soft">Pricing</span>
    <h2 class="section-title-light">Transparent. No membership.</h2>
  </div>
  <div class="products-grid">
    <div class="pcard pcard--trip" data-reveal><div class="pcard__bar"></div><div class="pcard__tier">Trip Planning</div><div class="pcard__name">Your itinerary, built around you.</div><div class="pcard__price-row"><span class="pcard__price">$25</span><span class="pcard__unit">/ country</span></div><hr class="pcard__divider"><ul class="pcard__features"><li>One preference survey</li><li>200,000+ options scanned</li><li>Expert review in 24 hours</li></ul><a class="btn btn-outline-light btn-md" href="https://veltmtours.com/embed/butler-booking?popup=true" data-butler-button>Plan My Trip</a><div class="pcard__guarantee">&#10003; Full refund if cancelled before delivery &nbsp;&middot;&nbsp; &#10003; Expert review in 24 hours</div></div>
    <div class="pcard pcard--featured" data-reveal style="--delay:0.1s"><div class="pcard__badge">Most Popular</div><div class="pcard__bar"></div><div class="pcard__tier">Concierge. 8 Hour</div><div class="pcard__name">A real person who already knows your trip.</div><div class="pcard__price-row"><span class="pcard__price">$25</span><span class="pcard__unit">/ day</span></div><hr class="pcard__divider"><ul class="pcard__features"><li>Flight cancelled at 11pm. Rebooked, transported, hotel sorted in 40 min.</li><li>The restaurant gave away our table. New reservation, better spot, 6 min.</li><li>The ryokan that only takes Japanese-speaking guests. We wrote the intro.</li><li>Real-time flight monitoring: we see the delay before the airline tells you.</li></ul><a class="btn btn-indigo btn-md" href="https://veltmtours.com/embed/butler-booking?popup=true" data-butler-button>Get Concierge</a><div class="pcard__guarantee pcard__guarantee--light">&#10003; Cancel any time. Pay only for days used &nbsp;&middot;&nbsp; &#10003; Human response in &lt;4 min</div></div>
    <div class="pcard pcard--elite" data-reveal style="--delay:0.2s"><div class="pcard__bar"></div><div class="pcard__tier">Concierge. 24 Hour</div><div class="pcard__name">Round-the-clock. Any hour.</div><div class="pcard__price-row"><span class="pcard__price">$100</span><span class="pcard__unit">/ day</span></div><hr class="pcard__divider"><ul class="pcard__features"><li>Overnight rebooking while you sleep. Wake up to a new itinerary, not a problem.</li><li>The "full" hotel we got you into because our advisor knows the GM personally.</li><li>3am medical referral in a city you've never been. Doctor dispatched, interpreter on the line.</li><li>Real-time flight monitoring: we see the delay before the airline tells you.</li></ul><a class="btn btn-outline-light btn-md" href="https://veltmtours.com/embed/butler-booking?popup=true" data-butler-button>Go 24-Hour</a><div class="pcard__guarantee">&#10003; Cancel any time. Pay only for days used &nbsp;&middot;&nbsp; &#10003; Human response in &lt;4 min</div></div>
  </div>
</section>

<section class="section-stats">
  <div class="stats-inner">
    <div data-reveal><div class="stat-num">97<sup>%</sup></div><div class="stat-label">Disruptions resolved &lt;60 min</div><div class="stat-because">Because your advisor studies your itinerary before departure, so when your flight cancels at 11pm, they already know your next-day schedule.</div></div>
    <div data-reveal style="--delay:0.08s"><div class="stat-num">&lt;4<sup>min</sup></div><div class="stat-label">Avg response time 24/7</div><div class="stat-because">Because Butlers carry one client at a time. No chatbot, no queue, no on-hold.</div></div>
    <div data-reveal style="--delay:0.16s"><div class="stat-num">150<sup>+</sup></div><div class="stat-label">Countries covered</div><div class="stat-because">Because every Butler is a destination specialist, not a generalist.</div></div>
    <div data-reveal style="--delay:0.24s"><div class="stat-num">100<sup>%</sup></div><div class="stat-label">Human first contact</div><div class="stat-because">No chatbot, ever, on any channel. Your first reply is always a person who knows your trip.</div></div>
  </div>
  <div class="stats-footnote">Measured across Butler Button concierge engagements, Jan to Apr 2026. Internal operations log; methodology available on request.</div>
</section>

<section class="anti-ai-section">
  <div style="text-align:center" data-reveal>
    <span class="eyebrow eyebrow-soft">The Reality Check</span>
    <h2 class="section-title-light">What AI can't do when it counts.</h2>
  </div>
  <div class="ai-compare">
    <div class="ai-col ai-bad" data-reveal>
      <div class="ai-col-label">ChatGPT / AI Assistants</div>
      <h3>"Let me help you with that."</h3>
      <div class="ai-item">Doesn't know your itinerary</div>
      <div class="ai-item">Can't make a booking</div>
      <div class="ai-item">Can't call the airline</div>
      <div class="ai-item">Can't negotiate with a hotel</div>
      <div class="ai-item">Not monitoring your flights</div>
      <div class="ai-item">Can hallucinate restaurant details</div>
    </div>
    <div class="ai-col ai-bad" data-reveal style="--delay:0.1s">
      <div class="ai-col-label">Voice Assistants (Siri, Alexa)</div>
      <h3>"I found some results for that."</h3>
      <div class="ai-item">No context on your trip</div>
      <div class="ai-item">Search results, not solutions</div>
      <div class="ai-item">Can't navigate complex rebooking</div>
      <div class="ai-item">No local knowledge depth</div>
      <div class="ai-item">Stops at the query</div>
      <div class="ai-item">No accountability for outcomes</div>
    </div>
    <div class="ai-col ai-good" data-reveal style="--delay:0.2s">
      <div class="ai-col-label">Butler Button</div>
      <h3>Already knows your trip. Already on it.</h3>
      <div class="ai-item">Reads your itinerary before departure</div>
      <div class="ai-item">Books, calls, negotiates on your behalf</div>
      <div class="ai-item">Speaks to airlines in their language</div>
      <div class="ai-item">Monitors your flights proactively</div>
      <div class="ai-item">Responds in &lt;4 minutes, 24/7</div>
      <div class="ai-item">Accountable for every resolution</div>
    </div>
  </div>
</section>

<section class="diss-section">
  <div class="diss-inner" data-reveal>
    <span class="eyebrow eyebrow-soft">The Arithmetic</span>
    <h2 class="section-title-light" style="font-size:clamp(1.8rem,4vw,3rem)">What you're actually paying for at a five-star hotel.</h2>
    <p style="font-size:0.9rem;color:var(--text-mute);margin-bottom:0">Breaking down the $500/night concierge arithmetic.</p>
    <div class="diss-box">
      <h3>A five-star hotel. What $500/night buys:</h3>
      <div class="diss-line"><span class="diss-item">Room (the actual room)</span><span class="diss-cost cost-included">~$320</span></div>
      <div class="diss-line"><span class="diss-item">Brand &amp; location premium</span><span class="diss-cost cost-included">~$80</span></div>
      <div class="diss-line"><span class="diss-item">Lobby, spa &amp; facilities overhead</span><span class="diss-cost cost-included">~$60</span></div>
      <div class="diss-line"><span class="diss-item">Your share of the concierge team<small>Shared with 200+ guests. Business hours emphasis.</small></span><span class="diss-cost cost-real">~$40</span></div>
      <div class="diss-total">
        <span class="diss-total-label">What you actually paid for concierge access</span>
        <span class="diss-total-price">~$40</span>
      </div>
    </div>
    <p style="font-size:0.68rem;color:var(--text-dim);margin-top:0.5rem;opacity:0.7"><em>Illustrative breakdown. Actual rate composition varies by property, season, and market.</em></p>
    <div class="diss-vs">
      <div class="diss-vs-label">Butler Button</div>
      <div class="diss-vs-price"><span class="diss-vs-amount">$25</span><span class="diss-vs-per">/day</span></div>
      <div class="diss-vs-unit">Your own expert. 24/7. Already knows your itinerary.</div>
    </div>
  </div>
</section>

<section class="section-scenarios" id="scenarios">
  <div style="max-width:1080px;margin:0 auto">
    <div class="section-head" data-reveal>
      <span class="eyebrow eyebrow-soft">When Things Go Wrong</span>
      <h2 class="section-title-light">We go to work.</h2>
    </div>
    <div class="scenarios-grid">
      <a href="/concierge#scenarios" class="scard" data-reveal><div class="scard__where">Bangkok &middot; 11pm</div><div class="scard__situation">Flight cancelled. Three rebook options in minutes.</div><div class="scard__outcome">Hotel arranged. Client asleep by 1am.</div><div class="scard__tag">40 minutes total &#8594;</div></a>
      <a href="/concierge#scenarios" class="scard" data-reveal style="--delay:0.1s"><div class="scard__where">Rome &middot; Day 3</div><div class="scard__situation">Restaurant gave away the reservation without notice.</div><div class="scard__outcome">Alternative found. Same area, better kitchen.</div><div class="scard__tag">6 minutes &#8594;</div></a>
      <a href="/concierge#scenarios" class="scard" data-reveal style="--delay:0.2s"><div class="scard__where">Lisbon &middot; Midnight</div><div class="scard__situation">Late-night cancellation at the airport.</div><div class="scard__outcome">Full rebook, zero additional cost.</div><div class="scard__tag">14 minutes &#8594;</div></a>
    </div>
  </div>
</section>

<section class="lead-magnet">
  <div class="lm-inner" data-reveal>
    <div>
      <div class="lm-headline">Get the 3-city crisis guide</div>
      <div class="lm-sub">What to do when a flight cancels in Bangkok, a reservation disappears in Rome, and you need an unknown doctor in Lisbon. One-page PDF, delivered instantly.</div>
    </div>
    <form class="lm-form" action="https://veltmtours.com/subscribe?source=concierge-crisis-guide" method="post" onsubmit="this.querySelector('button').textContent='Check your email &#10003;';">
      <input type="email" name="email" placeholder="you@example.com" required>
      <button type="submit">Send me the PDF</button>
    </form>
    <p class="lm-privacy">One email only. No newsletter spam. Unsubscribe in one click.</p>
  </div>
</section>

<section class="ps-block">
  <div class="ps-inner" data-reveal>
    <p><strong>P.S.</strong> The most common thing clients say after their first rescue: "I didn't know I needed this until I needed it." Concierge from $25/day. Cancel any time. <a class="ps-cta" data-butler-button href="https://veltmtours.com/embed/butler-booking?popup=true">Get Your Butler &#8594;</a></p>
  </div>
</section>

<footer class="site-footer">
  <a class="footer-brand" href="https://veltm-butler.zohosites.in/">Butler<em>Button</em> by VELTM</a>
  <ul class="footer-links">
    <li><a href="https://veltm-butler.zohosites.in/">Home</a></li>
    <li><a href="https://veltm-butler.zohosites.in/trip-planning">Trip Planning</a></li>
    <li><a href="https://veltm-butler.zohosites.in/concierge">Concierge</a></li>
    <li><a href="#">Advisor</a></li>
    <li><a href="#">FAQ</a></li>
  </ul>
  <span class="footer-legal">&copy; 2026 VELTM Tours</span>
</footer>
<script src="https://lobodotstreehouse.github.io/butler-button-variants/js/veltm.js"></script>
<script>
(function() {
  var photos = [
    { place: 'Bali',         id: '1537996194471-e657df975ab4' },
    { place: 'Rome',         id: '1552832230-c0197dd311b5'    },
    { place: 'Maldives',     id: '1514282401047-d79a71a590e8' },
    { place: 'Machu Picchu', id: '1587595431973-160d0d94add1' },
    { place: 'Barcelona',    id: '1539037116277-4db20889f2d4' },
    { place: 'Dubai',        id: '1512453979798-5ea266f8880c' },
    { place: 'New York',     id: '1496442226666-8d4d0e62e6e9' },
  ];
  var pool = photos.slice();
  for (var i = pool.length - 1; i > 0; i--) {
    var j = Math.floor(Math.random() * (i + 1));
    var t = pool[i]; pool[i] = pool[j]; pool[j] = t;
  }
  function setBg(sel, pick) {
    var el = document.querySelector(sel);
    if (el && pick) {
      el.style.backgroundImage = 'url(https://images.unsplash.com/photo-' + pick.id + '?auto=format&fit=crop&w=1800&q=80)';
      el.setAttribute('data-destination', pick.place);
    }
  }
  setBg('.section-products', pool[0]);
  setBg('.anti-ai-section', pool[1]);
  setBg('.section-scenarios', pool[2]);
})();
</script>
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
`;
  document.body.style.cssText = 'background:#000;margin:0;padding:0;overflow-x:hidden';
  document.documentElement.style.visibility = '';

  // 5. Re-execute all inline <script> tags inside the new body content
  Array.from(document.body.querySelectorAll('script')).forEach(function(oldScript){
    var newScript = document.createElement('script');
    if(oldScript.src) { newScript.src = oldScript.src; newScript.async = false; }
    else { newScript.textContent = oldScript.textContent; }
    oldScript.parentNode.replaceChild(newScript, oldScript);
  });

})();
