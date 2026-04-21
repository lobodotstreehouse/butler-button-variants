(function(){
  'use strict';

  document.querySelectorAll('style, link[rel="stylesheet"]').forEach(function(el){ el.remove(); });

  var style = document.createElement('style');
  style.textContent = `
/* ── RESET & BASE ────────────────────────────────────────────────── */
*, *::before, *::after { box-sizing: border-box; margin: 0; padding: 0; }
html { scroll-behavior: smooth; }
body {
  font-family: -apple-system, BlinkMacSystemFont, 'SF Pro Display',
               'Helvetica Neue', Helvetica, Arial, sans-serif;
  background: #000; color: #f5f5f7;
  overflow-x: hidden; -webkit-font-smoothing: antialiased;
}
img { display: block; max-width: 100%; }
a { text-decoration: none; color: inherit; }

/* ── TOKENS ──────────────────────────────────────────────────────── */
:root {
  --indigo:    #4f46e5;
  --indigo-lt: #818cf8;
  --amex-blue: #016FD0;
  --amex-gold: #B8A36A;
  --amex-black:#111;
  --dark:      #000;
  --dark-2:    #0a0a12;
  --dark-3:    #111;
  --text-mute: #86868b;
  --text-dim:  #3a3a3c;
}

/* ── SCROLL PROGRESS ─────────────────────────────────────────────── */
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

/* ── REVEAL ──────────────────────────────────────────────────────── */
@media (prefers-reduced-motion: no-preference) {
  [data-reveal] {
    opacity: 0; transform: translateY(32px);
    transition:
      opacity   0.75s cubic-bezier(0.22, 1, 0.36, 1) var(--delay, 0s),
      transform 0.75s cubic-bezier(0.22, 1, 0.36, 1) var(--delay, 0s);
  }
  [data-reveal].visible { opacity: 1; transform: none; }
}

/* ── NAV ─────────────────────────────────────────────────────────── */
.nav {
  position: fixed; top: 0; left: 0; right: 0; z-index: 500;
  padding: 1.1rem 5vw;
  display: flex; align-items: center; justify-content: space-between;
  background: rgba(0,0,0,0.78);
  backdrop-filter: blur(20px); -webkit-backdrop-filter: blur(20px);
  border-bottom: 1px solid rgba(255,255,255,0.05);
}
.nav-brand { font-size: 1rem; font-weight: 700; letter-spacing: -0.02em; }
.nav-brand em { color: var(--indigo-lt); font-style: normal; }
.nav-links { display: flex; gap: 2rem; list-style: none; }
.nav-links a { font-size: 0.82rem; color: rgba(255,255,255,0.5); letter-spacing: -0.01em; transition: color 0.2s; }
.nav-links a:hover { color: #f5f5f7; }
.nav-book {
  padding: 8px 22px; background: var(--indigo); color: #fff;
  border-radius: 980px; font-size: 0.82rem; font-weight: 500;
  transition: background 0.2s, transform 0.15s;
}
.nav-book:hover { background: #4338ca; transform: scale(1.02); }
@media (max-width: 700px) { .nav-links { display: none; } }

/* ── BUTTONS ─────────────────────────────────────────────────────── */
.btn {
  display: inline-block; cursor: pointer; border: none;
  border-radius: 980px; font-weight: 500; letter-spacing: -0.01em;
  transition: transform 0.18s, box-shadow 0.18s, background 0.18s;
}
.btn:active { transform: scale(0.97) !important; }
.btn-lg { padding: 16px 40px; font-size: 1.05rem; }
.btn-md { padding: 12px 28px; font-size: 0.9rem; }
.btn-indigo { background: var(--indigo); color: #fff; }
.btn-indigo:hover { background: #4338ca; box-shadow: 0 8px 32px rgba(79,70,229,0.45); transform: scale(1.02); }
.btn-ghost { background: transparent; color: #f5f5f7; border: 1px solid rgba(255,255,255,0.22); }
.btn-ghost:hover { background: rgba(255,255,255,0.06); border-color: rgba(255,255,255,0.38); }

/* ── EYEBROW ─────────────────────────────────────────────────────── */
.eyebrow {
  display: block; font-size: 0.72rem; font-weight: 600;
  letter-spacing: 0.16em; text-transform: uppercase; margin-bottom: 1.2rem;
}
.eyebrow-soft { color: var(--indigo-lt); }
.eyebrow-mute { color: var(--text-mute); }

/* ── HERO ────────────────────────────────────────────────────────── */
.hero {
  min-height: 90vh;
  display: flex; flex-direction: column;
  align-items: center; justify-content: center;
  text-align: center; position: relative; overflow: clip;
  padding: 9rem 5vw 5rem;
}
.hero-bg {
  position: absolute; inset: 0;
  background: radial-gradient(ellipse 90% 70% at 50% 65%, #0d0a2e 0%, #000 68%);
}
.hero-grid {
  position: absolute; inset: 0;
  background-image: radial-gradient(circle, rgba(99,102,241,0.15) 1px, transparent 1px);
  background-size: 40px 40px;
  mask-image: radial-gradient(ellipse 70% 60% at 50% 60%, black 30%, transparent 80%);
  -webkit-mask-image: radial-gradient(ellipse 70% 60% at 50% 60%, black 30%, transparent 80%);
}
.hero-orb {
  position: absolute; width: 700px; height: 700px; border-radius: 50%;
  background: radial-gradient(circle, rgba(79,70,229,0.14) 0%, transparent 65%);
  top: 50%; left: 50%; transform: translate(-50%, -48%);
  animation: orb-pulse 6s ease-in-out infinite;
}
@keyframes orb-pulse {
  0%, 100% { opacity: 0.5; transform: translate(-50%,-48%) scale(1); }
  50%       { opacity: 1;   transform: translate(-50%,-48%) scale(1.1); }
}
.hero-content { position: relative; z-index: 2; max-width: 960px; width: 100%; }
.hero-badge {
  display: inline-flex; align-items: center; gap: 0.5rem;
  padding: 6px 14px 6px 8px;
  background: rgba(79,70,229,0.14); border: 1px solid rgba(129,140,248,0.25);
  border-radius: 980px; font-size: 0.75rem; color: var(--indigo-lt);
  letter-spacing: 0.04em; margin-bottom: 2rem;
}
.hero-badge-dot {
  width: 6px; height: 6px; border-radius: 50%;
  background: var(--indigo-lt); animation: dot-blink 2s ease-in-out infinite;
}
@keyframes dot-blink { 0%,100%{opacity:1} 50%{opacity:0.3} }
.hero-h1 {
  font-size: clamp(2.6rem, 7vw, 5.6rem);
  font-weight: 700; letter-spacing: -0.04em; line-height: 1.02;
  color: #f5f5f7; margin-bottom: 1.4rem;
}
.hero-h1 span { color: var(--indigo-lt); }
.hero-sub {
  font-size: clamp(1rem, 1.8vw, 1.18rem);
  color: rgba(255,255,255,0.58); max-width: 700px; margin: 0 auto 2rem;
  line-height: 1.6; letter-spacing: -0.01em;
}
.hero-tier-pills {
  display: flex; justify-content: center; align-items: center;
  gap: 0.6rem; flex-wrap: wrap; margin-bottom: 2rem;
}
.tier-pill {
  display: inline-flex; align-items: center; gap: 0.45rem;
  padding: 6px 14px; border-radius: 980px;
  font-size: 0.75rem; font-weight: 600; letter-spacing: 0.02em;
}
.tier-pill-amex-p {
  background: rgba(1,111,208,0.14); border: 1px solid rgba(1,111,208,0.35);
  color: #6CB4F0;
}
.tier-pill-amex-c {
  background: rgba(255,255,255,0.05); border: 1px solid rgba(255,255,255,0.18);
  color: rgba(255,255,255,0.65);
}
.tier-pill-bb {
  background: rgba(79,70,229,0.2); border: 1px solid rgba(129,140,248,0.35);
  color: var(--indigo-lt);
}
.tier-pill-dot { width: 5px; height: 5px; border-radius: 50%; }
.tier-pill-amex-p .tier-pill-dot { background: #016FD0; }
.tier-pill-amex-c .tier-pill-dot { background: rgba(255,255,255,0.55); }
.tier-pill-bb .tier-pill-dot { background: var(--indigo-lt); }
.hero-actions { display: flex; gap: 1rem; justify-content: center; flex-wrap: wrap; }
.cta-guarantee { margin-top: 1rem; font-size: 0.78rem; color: rgba(245,245,247,0.55); text-align: center; }

/* ── TIER STRIP ──────────────────────────────────────────────────── */
.tier-section {
  background: var(--dark-2);
  padding: clamp(4rem, 9vw, 8rem) 5vw;
  border-top: 1px solid rgba(255,255,255,0.05);
}
.tier-head { text-align: center; margin-bottom: 3rem; }
.tier-head h2 {
  font-size: clamp(1.8rem, 3.5vw, 2.8rem);
  font-weight: 700; letter-spacing: -0.035em; color: #f5f5f7; margin-bottom: 0.5rem;
}
.tier-head p { font-size: 1rem; color: var(--text-mute); max-width: 520px; margin: 0 auto; }
.tier-cards {
  display: grid; grid-template-columns: repeat(3, 1fr);
  gap: 1.5rem; max-width: 1100px; margin: 0 auto;
}
.tier-card {
  border-radius: 22px; padding: 0;
  overflow: hidden; position: relative;
  border: 1px solid rgba(255,255,255,0.08);
  display: flex; flex-direction: column;
}
.tier-card--platinum { background: linear-gradient(160deg, #0d2040 0%, #0a1830 100%); border-color: rgba(1,111,208,0.3); }
.tier-card--centurion { background: linear-gradient(160deg, #1a1a1a 0%, #0d0d0d 100%); border-color: rgba(255,255,255,0.12); }
.tier-card--bb        { background: linear-gradient(160deg, #1e1b4b 0%, #2e2878 100%); border-color: rgba(129,140,248,0.3); }

/* Credit card visual */
.card-visual {
  padding: 1.8rem 1.8rem 1.2rem;
  background: rgba(255,255,255,0.03);
  border-bottom: 1px solid rgba(255,255,255,0.06);
}
.card-art {
  width: 100%; aspect-ratio: 85.6/54;
  border-radius: 10px;
  display: flex; flex-direction: column; justify-content: space-between;
  padding: 14px 16px 12px;
  position: relative; overflow: hidden;
}
.card-art--platinum {
  background: linear-gradient(135deg, #016FD0 0%, #0147A0 100%);
}
.card-art--centurion {
  background: linear-gradient(135deg, #1a1a1a 0%, #2d2d2d 40%, #111 100%);
  border: 1px solid rgba(255,255,255,0.12);
}
.card-art--bb {
  background: linear-gradient(135deg, #4f46e5 0%, #3730a3 100%);
}
.card-art-shine {
  position: absolute; inset: 0;
  background: linear-gradient(135deg, rgba(255,255,255,0.1) 0%, transparent 50%);
}
.card-art-top { display: flex; align-items: center; justify-content: space-between; }
.card-art-chip {
  width: 28px; height: 20px; border-radius: 3px;
  background: linear-gradient(135deg, #e8c87a, #c9a84c);
  opacity: 0.9;
}
.card-art-network {
  font-size: 0.6rem; font-weight: 800; letter-spacing: 0.12em;
  color: rgba(255,255,255,0.85);
}
.card-art-network--amex { color: rgba(255,255,255,0.9); }
.card-art-network--bb { color: rgba(255,255,255,0.8); }
.card-art-bottom { }
.card-art-tier {
  font-size: 0.58rem; font-weight: 700; letter-spacing: 0.22em;
  text-transform: uppercase;
}
.card-art--platinum .card-art-tier { color: rgba(255,255,255,0.85); }
.card-art--centurion .card-art-tier { color: rgba(255,255,255,0.7); letter-spacing: 0.28em; }
.card-art--bb .card-art-tier { color: rgba(255,255,255,0.8); }
.card-art-fee {
  font-size: 0.55rem; color: rgba(255,255,255,0.5); margin-top: 2px;
  letter-spacing: 0.06em;
}

/* Card body */
.card-body { padding: 1.4rem 1.8rem 1.8rem; flex: 1; display: flex; flex-direction: column; }
.card-name {
  font-size: 0.72rem; font-weight: 700; letter-spacing: 0.14em;
  text-transform: uppercase; margin-bottom: 0.8rem;
}
.tier-card--platinum .card-name { color: #6CB4F0; }
.tier-card--centurion .card-name { color: rgba(255,255,255,0.55); }
.tier-card--bb .card-name { color: var(--indigo-lt); }
.card-what {
  list-style: none; margin-bottom: 1.4rem; flex: 1;
}
.card-what li {
  display: flex; align-items: flex-start; gap: 0.5rem;
  font-size: 0.87rem; color: rgba(245,245,247,0.72);
  line-height: 1.45; padding: 0.45rem 0;
  border-bottom: 1px solid rgba(255,255,255,0.05);
}
.card-what li:last-child { border-bottom: none; }
.card-what .w-ok { color: var(--indigo-lt); flex-shrink: 0; margin-top: 1px; }
.card-what .w-no { color: #ef4444; flex-shrink: 0; margin-top: 1px; }
.card-what .w-warn { color: #f59e0b; flex-shrink: 0; margin-top: 1px; }
.card-verdict {
  font-size: 0.78rem; font-style: italic;
  color: rgba(245,245,247,0.42); line-height: 1.5;
  border-top: 1px solid rgba(255,255,255,0.06); padding-top: 0.9rem;
}
.tier-card--bb .card-verdict { color: rgba(129,140,248,0.55); font-style: normal; font-weight: 500; }

@media (max-width: 900px) {
  .tier-cards { grid-template-columns: 1fr; max-width: 480px; }
}

/* ── MATH SECTION ────────────────────────────────────────────────── */
.math-section {
  background: #000;
  padding: clamp(4rem, 9vw, 8rem) 5vw;
  border-top: 1px solid rgba(255,255,255,0.04);
}
.math-head { text-align: center; margin-bottom: 3rem; }
.math-head h2 {
  font-size: clamp(1.8rem, 3.5vw, 2.8rem);
  font-weight: 700; letter-spacing: -0.035em; color: #f5f5f7; margin-bottom: 0.5rem;
}
.math-head p { font-size: 1rem; color: var(--text-mute); max-width: 540px; margin: 0 auto; }
.math-grid {
  display: grid; grid-template-columns: repeat(3, 1fr);
  gap: 1.5rem; max-width: 1100px; margin: 0 auto;
}
.math-card {
  border-radius: 20px; padding: 2rem 1.8rem;
  border: 1px solid rgba(255,255,255,0.08);
}
.math-card--bb {
  background: linear-gradient(155deg, #1e1b4b 0%, #2e2878 100%);
  border-color: rgba(129,140,248,0.28);
}
.math-card--platinum { background: rgba(1,111,208,0.06); border-color: rgba(1,111,208,0.18); }
.math-card--centurion { background: rgba(255,255,255,0.03); border-color: rgba(255,255,255,0.08); }
.math-tier {
  font-size: 0.65rem; font-weight: 700; letter-spacing: 0.16em;
  text-transform: uppercase; margin-bottom: 0.4rem;
}
.math-card--bb .math-tier { color: var(--indigo-lt); }
.math-card--platinum .math-tier { color: #6CB4F0; }
.math-card--centurion .math-tier { color: var(--text-mute); }
.math-scenario { font-size: 0.85rem; color: rgba(245,245,247,0.55); margin-bottom: 1.4rem; line-height: 1.5; }
.math-lines { list-style: none; margin-bottom: 1.2rem; }
.math-lines li {
  display: flex; justify-content: space-between; align-items: baseline;
  padding: 0.5rem 0; border-bottom: 1px dashed rgba(255,255,255,0.07);
  font-size: 0.9rem;
}
.math-lines li .ml-label { color: rgba(245,245,247,0.65); }
.math-lines li .ml-val { font-weight: 600; color: #f5f5f7; }
.math-card--platinum .math-lines li .ml-val { color: rgba(245,245,247,0.75); }
.math-card--centurion .math-lines li .ml-val { color: rgba(245,245,247,0.65); }
.math-total {
  display: flex; justify-content: space-between; align-items: baseline;
  padding-top: 1rem; border-top: 1px solid rgba(255,255,255,0.1);
}
.math-total .mt-label {
  font-size: 0.68rem; font-weight: 700; letter-spacing: 0.12em;
  text-transform: uppercase; color: rgba(245,245,247,0.6);
}
.math-total .mt-val {
  font-size: clamp(2rem, 3.5vw, 2.6rem);
  font-weight: 700; letter-spacing: -0.04em; line-height: 1;
}
.math-card--bb .math-total .mt-val { color: var(--indigo-lt); }
.math-card--platinum .math-total .mt-val { color: rgba(245,245,247,0.72); }
.math-card--centurion .math-total .mt-val { color: rgba(245,245,247,0.55); }
.math-note { font-size: 0.7rem; color: rgba(245,245,247,0.35); margin-top: 0.6rem; line-height: 1.5; }
.math-verdict {
  max-width: 1100px; margin: 2.5rem auto 0;
  text-align: center; font-size: clamp(1rem, 2vw, 1.2rem);
  color: #f5f5f7; font-weight: 600; letter-spacing: -0.015em; line-height: 1.6;
}
.math-verdict strong { color: var(--indigo-lt); }
.math-verdict em { color: var(--text-mute); font-style: normal; font-weight: 400; }
@media (max-width: 900px) { .math-grid { grid-template-columns: 1fr; max-width: 480px; } }

/* ── 11PM TEST ───────────────────────────────────────────────────── */
.scenarios-section {
  background: var(--dark-2);
  padding: clamp(4rem, 9vw, 8rem) 5vw;
  border-top: 1px solid rgba(255,255,255,0.04);
}
.scenarios-head { text-align: center; margin-bottom: 3rem; }
.scenarios-head h2 {
  font-size: clamp(1.8rem, 3.5vw, 2.8rem);
  font-weight: 700; letter-spacing: -0.035em; color: #f5f5f7; margin-bottom: 0.5rem;
}
.scenarios-head p { font-size: 1rem; color: var(--text-mute); max-width: 540px; margin: 0 auto; }
.scenario-grid {
  display: grid; grid-template-columns: repeat(3, 1fr);
  gap: 1.5rem; max-width: 1100px; margin: 0 auto;
}
.scenario-card {
  border-radius: 20px; overflow: hidden;
  border: 1px solid rgba(255,255,255,0.07);
}
.scenario-situation {
  padding: 1.4rem 1.6rem 1rem;
  background: rgba(255,255,255,0.03);
  border-bottom: 1px solid rgba(255,255,255,0.06);
}
.scenario-situation h3 {
  font-size: 0.95rem; font-weight: 700; color: #f5f5f7;
  letter-spacing: -0.02em; margin-bottom: 0.5rem; line-height: 1.3;
}
.scenario-situation p {
  font-size: 0.8rem; color: rgba(245,245,247,0.5);
  line-height: 1.55;
}
.scenario-responses { }
.scenario-resp {
  padding: 1.1rem 1.6rem;
  border-bottom: 1px solid rgba(255,255,255,0.05);
}
.scenario-resp:last-child { border-bottom: none; }
.resp-label {
  font-size: 0.62rem; font-weight: 700; letter-spacing: 0.14em;
  text-transform: uppercase; margin-bottom: 0.45rem;
}
.resp-label--amex { color: #6CB4F0; }
.resp-label--bb   { color: var(--indigo-lt); }
.resp-label--centurion { color: rgba(255,255,255,0.45); }
.resp-text {
  font-size: 0.83rem; line-height: 1.55; letter-spacing: -0.005em;
  font-style: italic;
}
.resp-text--amex { color: rgba(245,245,247,0.5); }
.resp-text--bb   { color: rgba(245,245,247,0.85); }
.resp-text--centurion { color: rgba(245,245,247,0.42); }
.scenario-resp--bb { background: rgba(79,70,229,0.06); }
@media (max-width: 900px) { .scenario-grid { grid-template-columns: 1fr; max-width: 480px; } }

/* ── COMPARE TABLE (4-col) ───────────────────────────────────────── */
.compare-section {
  background: #000;
  padding: clamp(4rem, 9vw, 8rem) 5vw;
  border-top: 1px solid rgba(255,255,255,0.04);
}
.compare-head { text-align: center; margin-bottom: 2.5rem; }
.compare-head h2 {
  font-size: clamp(1.8rem, 3.5vw, 2.8rem);
  font-weight: 700; letter-spacing: -0.035em; color: #f5f5f7; margin-bottom: 0.5rem;
}
.compare-head p { font-size: 1rem; color: var(--text-mute); max-width: 540px; margin: 0 auto; }
.compare-table {
  max-width: 1100px; margin: 0 auto;
  border: 1px solid rgba(255,255,255,0.08); border-radius: 18px; overflow: hidden;
}
.compare-row {
  display: grid; grid-template-columns: 1.6fr 1.1fr 1.1fr 1.1fr;
  border-bottom: 1px solid rgba(255,255,255,0.05);
}
.compare-row:last-child { border-bottom: none; }
.compare-cell {
  padding: 1rem 1.1rem; font-size: 0.87rem; line-height: 1.4;
  color: rgba(245,245,247,0.7); letter-spacing: -0.005em;
  display: flex; align-items: center;
}
.compare-row.header .compare-cell {
  font-size: 0.65rem; font-weight: 700; letter-spacing: 0.12em;
  text-transform: uppercase; background: rgba(255,255,255,0.03);
}
.compare-row.header .compare-cell--feat { color: rgba(255,255,255,0.4); }
.compare-row.header .compare-cell--bb { color: var(--indigo-lt); background: rgba(79,70,229,0.15); }
.compare-row.header .compare-cell--platinum { color: #6CB4F0; background: rgba(1,111,208,0.08); }
.compare-row.header .compare-cell--centurion { color: rgba(255,255,255,0.4); }

.compare-cell--feat { font-weight: 600; color: #f5f5f7; font-size: 0.9rem; }
.compare-cell--bb { color: var(--indigo-lt); font-weight: 600; background: rgba(79,70,229,0.06); }
.compare-cell--platinum { color: rgba(245,245,247,0.55); }
.compare-cell--centurion { color: rgba(245,245,247,0.42); }

.cm { font-weight: 700; margin-right: 0.4rem; flex-shrink: 0; }
.cm-ok   { color: var(--indigo-lt); }
.cm-no   { color: #ef4444; }
.cm-warn { color: #f59e0b; }

@media (max-width: 820px) {
  .compare-row { grid-template-columns: 1fr 1fr; }
  .compare-row.header { display: none; }
  .compare-cell--feat { grid-column: 1 / -1; background: rgba(255,255,255,0.03); }
}
@media (max-width: 480px) {
  .compare-row { grid-template-columns: 1fr; }
  .compare-cell--feat { grid-column: auto; }
}

/* ── CK CLARIFIER ────────────────────────────────────────────────── */
.ck-section {
  background: var(--dark-2);
  padding: clamp(3rem, 7vw, 6rem) 5vw;
  border-top: 1px solid rgba(255,255,255,0.04);
}
.ck-inner {
  max-width: 860px; margin: 0 auto;
  background: rgba(255,255,255,0.03);
  border: 1px solid rgba(255,255,255,0.08); border-radius: 18px;
  padding: 2.4rem 2.8rem;
}
.ck-inner h3 {
  font-size: clamp(1.2rem, 2.5vw, 1.6rem);
  font-weight: 700; letter-spacing: -0.03em; color: #f5f5f7;
  margin-bottom: 0.8rem;
}
.ck-inner p {
  font-size: 0.97rem; color: rgba(245,245,247,0.65);
  line-height: 1.7; letter-spacing: -0.005em; margin-bottom: 0.7rem;
}
.ck-inner p:last-child { margin-bottom: 0; }
.ck-inner strong { color: #f5f5f7; }
.ck-divider {
  height: 1px; background: rgba(255,255,255,0.06);
  margin: 1.2rem 0;
}
@media (max-width: 700px) { .ck-inner { padding: 1.6rem 1.4rem; } }

/* ── CTA PHOTO SECTION ───────────────────────────────────────────── */
.cta-photo-section {
  position: relative; overflow: hidden;
  padding: clamp(5rem, 12vw, 10rem) 5vw;
  display: flex; align-items: center; justify-content: center;
  text-align: center;
  min-height: 56vh;
  border-top: 1px solid rgba(255,255,255,0.04);
}
.cta-photo-bg {
  position: absolute; inset: 0;
  background-size: cover; background-position: center;
  filter: brightness(0.32) saturate(0.8);
  transition: transform 8s ease-out;
}
.cta-photo-section:hover .cta-photo-bg { transform: scale(1.04); }
.cta-photo-overlay {
  position: absolute; inset: 0;
  background: linear-gradient(180deg, rgba(0,0,0,0.4) 0%, rgba(0,0,0,0.6) 100%);
}
.cta-photo-content {
  position: relative; z-index: 2; max-width: 700px;
}
.cta-photo-content h2 {
  font-size: clamp(2rem, 5vw, 3.8rem);
  font-weight: 700; letter-spacing: -0.04em; line-height: 1.08;
  color: #f5f5f7; margin-bottom: 1.2rem;
}
.cta-photo-content p {
  font-size: clamp(0.95rem, 1.6vw, 1.1rem);
  color: rgba(255,255,255,0.62); margin-bottom: 2rem; line-height: 1.6;
}
.cta-guarantee { font-size: 0.78rem; color: rgba(245,245,247,0.45); margin-top: 1rem; }

/* ── PS BLOCK ────────────────────────────────────────────────────── */
.ps-block {
  background: #0a0a0a;
  border-top: 1px solid rgba(255,255,255,0.04);
  padding: clamp(3rem, 6vw, 5rem) 5vw;
}
.ps-inner {
  max-width: 860px; margin: 0 auto;
  border-left: 3px solid var(--indigo-lt);
  padding: 1.2rem 1.8rem; background: rgba(129,140,248,0.05);
}
.ps-inner p {
  font-size: 1.02rem; color: rgba(245,245,247,0.82);
  line-height: 1.7; letter-spacing: -0.005em; margin-bottom: 0.7rem;
}
.ps-inner strong { color: var(--indigo-lt); }
.ps-cta {
  display: inline-block; margin-top: 0.4rem;
  font-size: 0.88rem; font-weight: 600; color: var(--indigo-lt);
  border-bottom: 1px solid rgba(129,140,248,0.4); padding-bottom: 2px;
  transition: color 0.2s, border-color 0.2s;
}
.ps-cta:hover { color: #fff; border-color: #fff; }

/* ── FOOTER ──────────────────────────────────────────────────────── */
.site-footer {
  background: #000; border-top: 1px solid rgba(255,255,255,0.05);
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

  var bodyHTML = `
<div class="scroll-progress"></div>

<nav class="nav" id="main-nav">
  <a class="nav-brand" href="/">Butler<em>Button</em></a>
  <ul class="nav-links">
    <li><a href="/">Home</a></li>
    <li><a href="/trip-planning">Trip Planning</a></li>
    <li><a href="/concierge">Concierge</a></li>
    <li><a href="/travel-advisor">Travel Advisor</a></li>
  </ul>
  <a class="nav-book" href="https://veltmtours.com/embed/butler-booking?popup=true" data-butler-button>Book Now. From $25</a>
</nav>

<!-- HERO -->
<section class="hero">
  <div class="hero-bg"></div>
  <div class="hero-grid"></div>
  <div class="hero-orb"></div>
  <div class="hero-content">
    <div class="hero-badge"><span class="hero-badge-dot"></span>Direct comparison. Three tiers. Real numbers.</div>
    <h1 class="hero-h1" data-reveal>The Black Card has a concierge.<br><span>So does $25.</span></h1>
    <p class="hero-sub" data-reveal style="--delay:0.08s">In a head-to-head test, The Points Guy found the Amex Platinum concierge &ldquo;performed the worst&rdquo; of all cards tested. The Centurion card costs $15,000 to join. Here is what both actually do when it matters.</p>
    <div class="hero-tier-pills" data-reveal style="--delay:0.14s">
      <span class="tier-pill tier-pill-amex-p"><span class="tier-pill-dot"></span>Amex Platinum $695/yr</span>
      <span class="tier-pill tier-pill-amex-c"><span class="tier-pill-dot"></span>Amex Centurion ~$5,000/yr</span>
      <span class="tier-pill tier-pill-bb"><span class="tier-pill-dot"></span>Butler Button $25/day</span>
    </div>
    <div class="hero-actions" data-reveal style="--delay:0.2s">
      <a class="btn btn-indigo btn-lg" href="https://veltmtours.com/embed/butler-booking?popup=true" data-butler-button>Start Planning. $25/Trip</a>
      <a class="btn btn-ghost btn-lg" href="https://veltmtours.com/embed/butler-booking?popup=true" data-butler-button>Get Concierge. From $25/Day</a>
    </div>
    <div class="cta-guarantee" data-reveal style="--delay:0.28s">&#10003; Full refund before delivery &nbsp;&middot;&nbsp; &#10003; Human response in &lt;4 min &nbsp;&middot;&nbsp; &#10003; Cancel any time</div>
  </div>
</section>

<!-- TIER STRIP -->
<section class="tier-section">
  <div class="tier-head" data-reveal>
    <span class="eyebrow eyebrow-mute">Three tiers, three realities</span>
    <h2>What each card actually gives you.</h2>
    <p>Not the brochure. The real product.</p>
  </div>
  <div class="tier-cards">

    <!-- Amex Platinum -->
    <div class="tier-card tier-card--platinum" data-reveal>
      <div class="card-visual">
        <div class="card-art card-art--platinum">
          <div class="card-art-shine"></div>
          <div class="card-art-top">
            <div class="card-art-chip"></div>
            <div class="card-art-network card-art-network--amex">AMEX</div>
          </div>
          <div class="card-art-bottom">
            <div class="card-art-tier">Platinum Card</div>
            <div class="card-art-fee">$695 annual fee</div>
          </div>
        </div>
      </div>
      <div class="card-body">
        <div class="card-name">Amex Platinum</div>
        <ul class="card-what">
          <li><span class="w-ok">&#10003;</span>Restaurant and show reservations</li>
          <li><span class="w-ok">&#10003;</span>Flight and hotel bookings via Amex Travel portal</li>
          <li><span class="w-warn">&#9888;</span>Third-party call center. Agents rotate. No persistent profile.</li>
          <li><span class="w-warn">&#9888;</span>Response times vary. 15 to 45 minutes during peak hours reported by cardholders.</li>
          <li><span class="w-no">&#10007;</span>Starts cold on every call. No context about your specific trip.</li>
          <li><span class="w-no">&#10007;</span>Cannot negotiate with local vendors, hotels, or non-English contacts on your behalf.</li>
          <li><span class="w-no">&#10007;</span>Concierge is bundled. You pay $695 whether you travel once or twelve times.</li>
        </ul>
        <div class="card-verdict">"A reservations line dressed up as a concierge. Solid for dinner bookings in cities it knows. Not built for what actually goes wrong."</div>
      </div>
    </div>

    <!-- Amex Centurion -->
    <div class="tier-card tier-card--centurion" data-reveal style="--delay:0.08s">
      <div class="card-visual">
        <div class="card-art card-art--centurion">
          <div class="card-art-shine"></div>
          <div class="card-art-top">
            <div class="card-art-chip"></div>
            <div class="card-art-network card-art-network--amex">AMEX</div>
          </div>
          <div class="card-art-bottom">
            <div class="card-art-tier">Centurion Card&trade;</div>
            <div class="card-art-fee">~$5,000/yr + $10,000 initiation. Invitation only.</div>
          </div>
        </div>
      </div>
      <div class="card-body">
        <div class="card-name">Amex Centurion</div>
        <ul class="card-what">
          <li><span class="w-ok">&#10003;</span>Dedicated personal advisor who knows your name and preferences</li>
          <li><span class="w-ok">&#10003;</span>Access to exclusive events, hard-to-get reservations, private dining</li>
          <li><span class="w-ok">&#10003;</span>By invitation only. Genuinely premium tier.</li>
          <li><span class="w-warn">&#9888;</span>Annual fee estimated $5,000/yr + initiation. Not purchasable.</li>
          <li><span class="w-warn">&#9888;</span>Your advisor works banker's hours. Escalation paths vary in practice.</li>
          <li><span class="w-no">&#10007;</span>Still phone and digital only. Cannot coordinate on the ground in remote locations.</li>
          <li><span class="w-no">&#10007;</span>Your advisor is in New York. Your problem is in Nairobi at midnight.</li>
        </ul>
        <div class="card-verdict">"The best phone concierge money can buy. When you need someone to physically coordinate in-country, it hits a wall."</div>
      </div>
    </div>

    <!-- Butler Button -->
    <div class="tier-card tier-card--bb" data-reveal style="--delay:0.16s">
      <div class="card-visual">
        <div class="card-art card-art--bb">
          <div class="card-art-shine"></div>
          <div class="card-art-top">
            <div class="card-art-chip"></div>
            <div class="card-art-network card-art-network--bb">BUTLER</div>
          </div>
          <div class="card-art-bottom">
            <div class="card-art-tier">Butler Button</div>
            <div class="card-art-fee">$25/day. No annual fee. Cancel any time.</div>
          </div>
        </div>
      </div>
      <div class="card-body">
        <div class="card-name">Butler Button</div>
        <ul class="card-what">
          <li><span class="w-ok">&#10003;</span>Human advisor reads your full itinerary before you depart</li>
          <li><span class="w-ok">&#10003;</span>Same person, start to finish. No cold starts.</li>
          <li><span class="w-ok">&#10003;</span>Response in &lt;4 minutes. 24 hours, including nights and weekends.</li>
          <li><span class="w-ok">&#10003;</span>On-the-ground coordination. Local vendors, hotels, transport, language barriers handled.</li>
          <li><span class="w-ok">&#10003;</span>$25/trip plan. $25/day concierge. $100/day for 24-hour coverage. Pay only for what you use.</li>
          <li><span class="w-ok">&#10003;</span>150+ languages. 195 countries. Preferred pricing at 500+ properties.</li>
          <li><span class="w-ok">&#10003;</span>No invitation required. No annual fee. Start today.</li>
        </ul>
        <div class="card-verdict">Built for the moment something actually goes wrong.</div>
      </div>
    </div>

  </div>
</section>

<!-- MATH -->
<section class="math-section">
  <div class="math-head" data-reveal>
    <span class="eyebrow eyebrow-soft">The real cost</span>
    <h2>What you actually spend. Per trip.</h2>
    <p>Nine days in Tokyo. One family. All the help you need.</p>
  </div>
  <div class="math-grid">
    <div class="math-card math-card--bb" data-reveal>
      <div class="math-tier">Butler Button</div>
      <div class="math-scenario">9-day Tokyo trip. Two adults.</div>
      <ul class="math-lines">
        <li><span class="ml-label">Trip plan (1 country)</span><span class="ml-val">$25</span></li>
        <li><span class="ml-label">8-Hour Concierge &times; 9 days</span><span class="ml-val">$225</span></li>
      </ul>
      <div class="math-total"><span class="mt-label">Total cost, this trip</span><span class="mt-val">$250</span></div>
      <div class="math-note">Pay per trip. Nothing owed between trips.</div>
    </div>
    <div class="math-card math-card--platinum" data-reveal style="--delay:0.08s">
      <div class="math-tier">Amex Platinum</div>
      <div class="math-scenario">9-day Tokyo trip. Two adults.</div>
      <ul class="math-lines">
        <li><span class="ml-label">Annual fee (whether you travel or not)</span><span class="ml-val">$695</span></li>
        <li><span class="ml-label">Divided across 3 trips/year</span><span class="ml-val">~$232</span></li>
        <li><span class="ml-label">Wait time during peak hours</span><span class="ml-val">15-45 min</span></li>
      </ul>
      <div class="math-total"><span class="mt-label">Fee attributed to this trip</span><span class="mt-val">$232+</span></div>
      <div class="math-note">Paid regardless of usage. Concierge is one feature among dozens included in the fee.</div>
    </div>
    <div class="math-card math-card--centurion" data-reveal style="--delay:0.16s">
      <div class="math-tier">Amex Centurion</div>
      <div class="math-scenario">9-day Tokyo trip. Two adults.</div>
      <ul class="math-lines">
        <li><span class="ml-label">Estimated annual fee (cardholder reports)</span><span class="ml-val">~$5,000</span></li>
        <li><span class="ml-label">Divided across 3 trips/year</span><span class="ml-val">~$1,667</span></li>
        <li><span class="ml-label">Initiation fee (one-time, reported)</span><span class="ml-val">~$10,000</span></li>
      </ul>
      <div class="math-total"><span class="mt-label">Fee attributed to this trip</span><span class="mt-val">$1,667+</span></div>
      <div class="math-note">By invitation only. Amex does not publicly disclose Centurion fees. All figures from published cardholder accounts.</div>
    </div>
  </div>
  <p class="math-verdict" data-reveal style="--delay:0.2s">
    <strong>$250 vs. $1,667</strong> for the same trip.
    <em>What the savings cover: a business-class upgrade, three nights at a better hotel, or just staying in your pocket.</em>
  </p>
</section>

<!-- 11PM TEST -->
<section class="scenarios-section">
  <div class="scenarios-head" data-reveal>
    <span class="eyebrow eyebrow-mute">The 11pm test</span>
    <h2>What actually happens when it matters.</h2>
    <p>Three real scenarios. Three honest responses from each tier.</p>
  </div>
  <div class="scenario-grid">

    <div class="scenario-card" data-reveal>
      <div class="scenario-situation">
        <h3>Flight cancelled in Marrakech. No English at the check-in counter.</h3>
        <p>11:40pm. Your connection is gone. The next flight is in 36 hours. Your riad closes at midnight.</p>
      </div>
      <div class="scenario-responses">
        <div class="scenario-resp">
          <div class="resp-label resp-label--amex">Amex Platinum says</div>
          <div class="resp-text resp-text--amex">"I can look into rebooking options for you. Can I put you on hold for a few minutes?"</div>
        </div>
        <div class="scenario-resp">
          <div class="resp-label resp-label--centurion">Amex Centurion says</div>
          <div class="resp-text resp-text--centurion">"I'll call the airline on your behalf and look at alternatives. This may take some time."</div>
        </div>
        <div class="scenario-resp scenario-resp--bb">
          <div class="resp-label resp-label--bb">Butler Button says</div>
          <div class="resp-text resp-text--bb">"We called the airline in Arabic. You're rebooked on the 6am Royal Air Maroc. Your riad is holding the room with a late checkout. Hotel breakfast confirmed."</div>
        </div>
      </div>
    </div>

    <div class="scenario-card" data-reveal style="--delay:0.08s">
      <div class="scenario-situation">
        <h3>Your suite was given away. Conference starts at 7am. It's 10:45pm.</h3>
        <p>You booked months ago. The hotel says they're sold out. There is nothing on the standard booking sites.</p>
      </div>
      <div class="scenario-responses">
        <div class="scenario-resp">
          <div class="resp-label resp-label--amex">Amex Platinum says</div>
          <div class="resp-text resp-text--amex">"I can confirm your original reservation details and escalate to the hotel's customer service team."</div>
        </div>
        <div class="scenario-resp">
          <div class="resp-label resp-label--centurion">Amex Centurion says</div>
          <div class="resp-text resp-text--centurion">"I'll contact the property manager directly and see what we can do. I'll follow up with you shortly."</div>
        </div>
        <div class="scenario-resp scenario-resp--bb">
          <div class="resp-label resp-label--bb">Butler Button says</div>
          <div class="resp-text resp-text--bb">"We called the GM's direct line. You have a corner king, one floor up. Breakfast is comped and they're sending an apology bottle to the room."</div>
        </div>
      </div>
    </div>

    <div class="scenario-card" data-reveal style="--delay:0.16s">
      <div class="scenario-situation">
        <h3>Your child has a tree nut allergy. The restaurant just told you the dish contains hazelnuts.</h3>
        <p>You're already seated. It's the only reservation you could get. The kitchen cannot accommodate.</p>
      </div>
      <div class="scenario-responses">
        <div class="scenario-resp">
          <div class="resp-label resp-label--amex">Amex Platinum says</div>
          <div class="resp-text resp-text--amex">"I can search for other restaurants in the area with availability tonight."</div>
        </div>
        <div class="scenario-resp">
          <div class="resp-label resp-label--centurion">Amex Centurion says</div>
          <div class="resp-text resp-text--centurion">"I'll check our preferred partner list and see if I can get you a table somewhere comparable."</div>
        </div>
        <div class="scenario-resp scenario-resp--bb">
          <div class="resp-label resp-label--bb">Butler Button says</div>
          <div class="resp-text resp-text--bb">"We flagged this when we reviewed your itinerary. You have three nut-free alternatives pre-vetted and a table already held at the second one. Head there now."</div>
        </div>
      </div>
    </div>

  </div>
</section>

<!-- COMPARE TABLE -->
<section class="compare-section">
  <div class="compare-head" data-reveal>
    <span class="eyebrow eyebrow-mute">Side by side</span>
    <h2>Feature by feature.</h2>
    <p>All three tiers. Every dimension that matters.</p>
  </div>
  <div class="compare-table" data-reveal>
    <div class="compare-row header">
      <div class="compare-cell compare-cell--feat">Feature</div>
      <div class="compare-cell compare-cell--bb">Butler Button</div>
      <div class="compare-cell compare-cell--platinum">Amex Platinum</div>
      <div class="compare-cell compare-cell--centurion">Amex Centurion</div>
    </div>
    <div class="compare-row">
      <div class="compare-cell compare-cell--feat">Pay only when you travel</div>
      <div class="compare-cell compare-cell--bb"><span class="cm cm-ok">&#10003;</span>$25/day. Nothing between trips.</div>
      <div class="compare-cell compare-cell--platinum"><span class="cm cm-no">&#10007;</span>$695/yr regardless</div>
      <div class="compare-cell compare-cell--centurion"><span class="cm cm-no">&#10007;</span>~$5,000/yr regardless</div>
    </div>
    <div class="compare-row">
      <div class="compare-cell compare-cell--feat">Human response time</div>
      <div class="compare-cell compare-cell--bb"><span class="cm cm-ok">&#10003;</span>&lt;4 min guaranteed</div>
      <div class="compare-cell compare-cell--platinum"><span class="cm cm-warn">&#9888;</span>15 to 45 min (reported)</div>
      <div class="compare-cell compare-cell--centurion"><span class="cm cm-ok">&#10003;</span>Dedicated line, faster</div>
    </div>
    <div class="compare-row">
      <div class="compare-cell compare-cell--feat">Reads your itinerary before you leave</div>
      <div class="compare-cell compare-cell--bb"><span class="cm cm-ok">&#10003;</span>Always</div>
      <div class="compare-cell compare-cell--platinum"><span class="cm cm-no">&#10007;</span>Starts cold every call</div>
      <div class="compare-cell compare-cell--centurion"><span class="cm cm-warn">&#9888;</span>Knows your preferences, not your trip specifics</div>
    </div>
    <div class="compare-row">
      <div class="compare-cell compare-cell--feat">Same person, start to finish</div>
      <div class="compare-cell compare-cell--bb"><span class="cm cm-ok">&#10003;</span>Yes</div>
      <div class="compare-cell compare-cell--platinum"><span class="cm cm-no">&#10007;</span>Random agent each call</div>
      <div class="compare-cell compare-cell--centurion"><span class="cm cm-ok">&#10003;</span>Dedicated advisor</div>
    </div>
    <div class="compare-row">
      <div class="compare-cell compare-cell--feat">Local language negotiation</div>
      <div class="compare-cell compare-cell--bb"><span class="cm cm-ok">&#10003;</span>150+ languages</div>
      <div class="compare-cell compare-cell--platinum"><span class="cm cm-no">&#10007;</span>English-language call center</div>
      <div class="compare-cell compare-cell--centurion"><span class="cm cm-no">&#10007;</span>English-language advisor</div>
    </div>
    <div class="compare-row">
      <div class="compare-cell compare-cell--feat">On-the-ground coordination</div>
      <div class="compare-cell compare-cell--bb"><span class="cm cm-ok">&#10003;</span>Local contacts, vendors, transport</div>
      <div class="compare-cell compare-cell--platinum"><span class="cm cm-no">&#10007;</span>Phone and digital only</div>
      <div class="compare-cell compare-cell--centurion"><span class="cm cm-no">&#10007;</span>Phone and digital only</div>
    </div>
    <div class="compare-row">
      <div class="compare-cell compare-cell--feat">Trip planning included</div>
      <div class="compare-cell compare-cell--bb"><span class="cm cm-ok">&#10003;</span>$25 per country</div>
      <div class="compare-cell compare-cell--platinum"><span class="cm cm-no">&#10007;</span>Not included. Amex Travel portal upsell.</div>
      <div class="compare-cell compare-cell--centurion"><span class="cm cm-warn">&#9888;</span>Recommendations, not full plans</div>
    </div>
    <div class="compare-row">
      <div class="compare-cell compare-cell--feat">Preferred pricing at hotels</div>
      <div class="compare-cell compare-cell--bb"><span class="cm cm-ok">&#10003;</span>500+ properties, 10 to 59% off</div>
      <div class="compare-cell compare-cell--platinum"><span class="cm cm-warn">&#9888;</span>Amex Fine Hotels network</div>
      <div class="compare-cell compare-cell--centurion"><span class="cm cm-warn">&#9888;</span>Broader than Platinum, still limited</div>
    </div>
    <div class="compare-row">
      <div class="compare-cell compare-cell--feat">Books flights and hotels directly</div>
      <div class="compare-cell compare-cell--bb"><span class="cm cm-ok">&#10003;</span>Yes, through your Butler</div>
      <div class="compare-cell compare-cell--platinum"><span class="cm cm-no">&#10007;</span>No. Redirected to AmexTravel.com separately</div>
      <div class="compare-cell compare-cell--centurion"><span class="cm cm-no">&#10007;</span>No. Redirected to AmexTravel.com separately</div>
    </div>
    <div class="compare-row">
      <div class="compare-cell compare-cell--feat">Available without an invitation</div>
      <div class="compare-cell compare-cell--bb"><span class="cm cm-ok">&#10003;</span>Start today</div>
      <div class="compare-cell compare-cell--platinum"><span class="cm cm-ok">&#10003;</span>Apply directly</div>
      <div class="compare-cell compare-cell--centurion"><span class="cm cm-no">&#10007;</span>Invitation only</div>
    </div>
    <div class="compare-row">
      <div class="compare-cell compare-cell--feat">Cost, this 9-day trip</div>
      <div class="compare-cell compare-cell--bb"><span class="cm cm-ok">&#10003;</span><strong>$250 total</strong></div>
      <div class="compare-cell compare-cell--platinum"><span class="cm cm-no">&#10007;</span>~$232 attributed from annual fee</div>
      <div class="compare-cell compare-cell--centurion"><span class="cm cm-no">&#10007;</span>~$1,667 attributed from annual fee</div>
    </div>
  </div>
</section>

<!-- CK CLARIFIER -->
<section class="ck-section">
  <div class="ck-inner" data-reveal>
    <h3>What Concierge Key actually is.</h3>
    <div class="ck-divider"></div>
    <p>Concierge Key (CK) is American Airlines' invitation-only status for their highest-value flyers. It is not a concierge service. It is airline status.</p>
    <p>What CK gives you: a dedicated AA phone line, airport escort from check-in to gate, priority upgrades on AA metal, and a relationship manager inside American's customer service team. If your AA flight is disrupted, CK is the fastest path to a fix.</p>
    <p>What CK does not give you: hotel selection, restaurant reservations, trip planning, local fixers, language support, or any coordination outside of American Airlines flights.</p>
    <p><strong>If you have Concierge Key status, Butler Button is not a competitor. It is the part of your travel stack that CK was never designed to cover.</strong> Many of our clients hold CK status. They use CK for their AA flights. They use Butler Button for everything that happens once they land.</p>
  </div>
</section>

<!-- CTA PHOTO SECTION -->
<section class="cta-photo-section" id="cta-photo">
  <div class="cta-photo-bg" id="cta-bg"></div>
  <div class="cta-photo-overlay"></div>
  <div class="cta-photo-content">
    <h2 data-reveal>You already know what five-star travel feels like.<br>Now get the service that matches it.</h2>
    <p data-reveal style="--delay:0.1s">No annual fee. No waitlist. No invitation required. The same human who planned your trip handles it when anything changes.</p>
    <div data-reveal style="--delay:0.18s">
      <a class="btn btn-indigo btn-lg" href="https://veltmtours.com/embed/butler-booking?popup=true" data-butler-button>Start Planning. From $25 &#8594;</a>
    </div>
    <div class="cta-guarantee" data-reveal style="--delay:0.26s">Full refund before delivery &nbsp;&middot;&nbsp; Cancel any time &nbsp;&middot;&nbsp; 195 countries covered</div>
  </div>
</section>

<!-- PS BLOCK -->
<section class="ps-block">
  <div class="ps-inner" data-reveal>
    <p><strong>P.S.</strong> The Centurion card gets you a person who remembers your name. Butler Button gets you a person who read your full itinerary before you boarded. If you had to pick one for your next trip, you know which one would actually help at 11pm.</p>
    <a class="ps-cta" href="https://veltmtours.com/embed/butler-booking?popup=true" data-butler-button>Try Butler Button. From $25 &#8594;</a>
  </div>
</section>

<footer class="site-footer">
  <a class="footer-brand" href="/">Butler<em>Button</em> by VELTM</a>
  <ul class="footer-links">
    <li><a href="/">Home</a></li>
    <li><a href="/trip-planning">Trip Planning</a></li>
    <li><a href="/concierge">Concierge</a></li>
    <li><a href="/travel-advisor">Travel Advisor</a></li>
  </ul>
  <span class="footer-legal">&copy; 2026 VELTM Tours &nbsp;&middot;&nbsp; Fees as reported at time of writing. Verify current rates at americanexpress.com.</span>
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
  // CTA photo background
  var photos = [
    '1448318440207-ef1893eb8ac0',
    '1439337153520-7082a56a81f4',
    '1437936251057-dfbf79980ce5',
    '1440339738560-7ea831bf5244',
    '1446034295857-c39f8844fad4'
  ];
  var bg = document.getElementById('cta-bg');
  if (bg) {
    var pick = photos[Math.floor(Math.random() * photos.length)];
    bg.style.backgroundImage = 'url(https://images.unsplash.com/photo-' + pick + '?auto=format&fit=crop&w=1800&q=80)';
  }
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
  }, { threshold: 0.1 });
  document.querySelectorAll('[data-reveal]').forEach(function(el){ io.observe(el); });
})();
</script>
`;

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
