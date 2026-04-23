(function(){
  'use strict';

  document.querySelectorAll('style, link[rel="stylesheet"]').forEach(function(el){ el.remove(); });

  var style = document.createElement('style');
  style.textContent = [
    '*, *::before, *::after { box-sizing: border-box; margin: 0; padding: 0; }',
    'html { scroll-behavior: smooth; }',
    'body {',
    '  font-family: -apple-system, BlinkMacSystemFont, "SF Pro Display",',
    '               "Helvetica Neue", Helvetica, Arial, sans-serif;',
    '  background: #000; color: #f5f5f7;',
    '  overflow-x: hidden;',
    '  -webkit-font-smoothing: antialiased;',
    '  -moz-osx-font-smoothing: grayscale;',
    '}',
    'img { display: block; max-width: 100%; }',
    'a { text-decoration: none; color: inherit; }',

    /* SCROLL PROGRESS */
    '.scroll-progress {',
    '  position: fixed; top: 0; left: 0; right: 0; height: 2px;',
    '  background: #4f46e5; z-index: 2000;',
    '  transform-origin: left; transform: scaleX(0);',
    '}',
    '@media (prefers-reduced-motion: no-preference) {',
    '  @supports (animation-timeline: scroll()) {',
    '    .scroll-progress {',
    '      animation: grow-bar linear both;',
    '      animation-duration: auto;',
    '      animation-timeline: scroll(root block);',
    '    }',
    '  }',
    '}',
    '@keyframes grow-bar { from { transform: scaleX(0); } to { transform: scaleX(1); } }',

    /* REVEAL */
    '@media (prefers-reduced-motion: no-preference) {',
    '  [data-reveal] {',
    '    opacity: 0; transform: translateY(36px);',
    '    transition: opacity 0.8s cubic-bezier(0.22,1,0.36,1) var(--delay,0s),',
    '                transform 0.8s cubic-bezier(0.22,1,0.36,1) var(--delay,0s);',
    '  }',
    '  [data-reveal].visible { opacity: 1; transform: none; }',
    '}',

    /* TOKENS */
    ':root {',
    '  --indigo:     #4f46e5;',
    '  --indigo-lt:  #818cf8;',
    '  --dark-3:     #111;',
    '  --text-mute:  #86868b;',
    '  --text-mid:   #6e6e73;',
    '  --font-display: Georgia,"Times New Roman",serif;',
    '}',

    /* NAV */
    '.nav {',
    '  position: fixed; top: 0; left: 0; right: 0; z-index: 500;',
    '  padding: 1.1rem 5vw;',
    '  display: flex; align-items: center; justify-content: space-between;',
    '  transition: background 0.4s ease, backdrop-filter 0.4s ease;',
    '}',
    '.nav.bg {',
    '  background: rgba(0,0,0,0.72);',
    '  backdrop-filter: blur(20px); -webkit-backdrop-filter: blur(20px);',
    '  border-bottom: 1px solid rgba(255,255,255,0.04);',
    '}',
    '.nav-brand { font-size: 1rem; font-weight: 700; letter-spacing: -0.02em; color: #f5f5f7; }',
    '.nav-brand em { color: var(--indigo-lt); font-style: normal; }',
    '.nav-links { display: flex; gap: 2rem; list-style: none; }',
    '.nav-links a { font-size: 0.82rem; color: rgba(255,255,255,0.55); letter-spacing: -0.01em; transition: color 0.2s; }',
    '.nav-links a:hover { color: #f5f5f7; }',
    '.nav-book {',
    '  padding: 8px 22px; background: var(--indigo); color: #fff;',
    '  border-radius: 980px; font-size: 0.82rem; font-weight: 500;',
    '  transition: background 0.2s, transform 0.15s;',
    '}',
    '.nav-book:hover { background: #4338ca; transform: scale(1.02); }',
    '@media (max-width: 700px) { .nav-links { display: none; } }',

    /* HERO */
    '.hero {',
    '  position: relative; overflow: hidden;',
    '  min-height: 92vh;',
    '  display: flex; flex-direction: column; justify-content: flex-end;',
    '  padding: 0 5vw 5rem;',
    '}',
    '.hero-img {',
    '  position: absolute; inset: 0;',
    '  background-image: url("https://images.unsplash.com/photo-1558618666-fcd25c85cd64?auto=format&fit=crop&w=1600&q=85");',
    '  background-size: cover; background-position: center 30%;',
    '}',
    '.hero-overlay {',
    '  position: absolute; inset: 0;',
    '  background: linear-gradient(to top, rgba(0,0,0,0.92) 0%, rgba(0,0,0,0.55) 50%, rgba(0,0,0,0.25) 100%);',
    '}',
    '.hero-content { position: relative; z-index: 2; max-width: 800px; }',
    '.hero-breadcrumb {',
    '  display: flex; gap: 0.5rem; align-items: center;',
    '  font-size: 0.72rem; color: rgba(255,255,255,0.45); letter-spacing: 0.04em;',
    '  margin-bottom: 1.5rem;',
    '}',
    '.hero-breadcrumb span { color: rgba(255,255,255,0.25); }',
    '.hero-eyebrow {',
    '  display: block; font-size: 0.72rem; font-weight: 600;',
    '  letter-spacing: 0.16em; text-transform: uppercase;',
    '  color: var(--indigo-lt); margin-bottom: 1.2rem;',
    '}',
    '.hero-h1 {',
    '  font-size: clamp(2.8rem, 7vw, 5.5rem);',
    '  font-weight: 700; letter-spacing: -0.04em; line-height: 1.0;',
    '  color: #f5f5f7; margin-bottom: 1.25rem;',
    '}',
    '.hero-sub {',
    '  font-size: clamp(1rem, 1.8vw, 1.15rem);',
    '  color: rgba(255,255,255,0.62); line-height: 1.65; letter-spacing: -0.01em;',
    '  max-width: 520px; margin-bottom: 2rem;',
    '}',
    '.hero-meta {',
    '  display: flex; gap: 1.5rem; flex-wrap: wrap;',
    '  font-size: 0.78rem; color: rgba(255,255,255,0.45); letter-spacing: -0.01em;',
    '}',
    '.hero-meta strong { color: rgba(255,255,255,0.75); }',

    /* TOC */
    '.toc-strip {',
    '  background: #0a0a12;',
    '  border-top: 1px solid rgba(255,255,255,0.06);',
    '  border-bottom: 1px solid rgba(255,255,255,0.06);',
    '  padding: 0 5vw;',
    '  overflow-x: auto; -webkit-overflow-scrolling: touch;',
    '  scrollbar-width: none;',
    '}',
    '.toc-strip::-webkit-scrollbar { display: none; }',
    '.toc-list {',
    '  display: flex; gap: 0; list-style: none;',
    '  white-space: nowrap; min-width: max-content;',
    '}',
    '.toc-list a {',
    '  display: block; padding: 1.1rem 1.4rem;',
    '  font-size: 0.78rem; color: rgba(255,255,255,0.45);',
    '  letter-spacing: -0.01em;',
    '  border-bottom: 2px solid transparent;',
    '  transition: color 0.2s, border-color 0.2s;',
    '}',
    '.toc-list a:hover { color: #f5f5f7; }',
    '.toc-list a.active { color: #f5f5f7; border-bottom-color: var(--indigo); }',

    /* ARTICLE LAYOUT */
    '.article-wrap {',
    '  max-width: 720px; margin: 0 auto;',
    '  padding: clamp(4rem,8vw,6rem) 5vw;',
    '}',

    /* PULL QUOTE */
    '.pull-quote {',
    '  background: #0a0a12;',
    '  border-left: 3px solid var(--indigo);',
    '  padding: 3rem 5vw;',
    '}',
    '.pull-quote-inner { max-width: 720px; margin: 0 auto; }',
    '.pull-quote blockquote {',
    '  font-family: var(--font-display);',
    '  font-size: clamp(1.25rem, 2.5vw, 1.7rem);',
    '  font-style: italic; line-height: 1.55;',
    '  color: #f5f5f7; margin-bottom: 1.25rem;',
    '}',
    '.pull-quote cite {',
    '  font-style: normal; font-size: 0.8rem;',
    '  color: var(--text-mute); letter-spacing: -0.01em;',
    '  display: flex; align-items: center; gap: 0.5rem;',
    '}',
    '.pull-quote cite::before {',
    '  content: ""; display: inline-block;',
    '  width: 24px; height: 1px; background: var(--indigo);',
    '}',

    /* ARTICLE SECTIONS */
    '.article-section { padding: clamp(4rem,8vw,6rem) 5vw; border-top: 1px solid rgba(255,255,255,0.06); }',
    '.article-section:first-of-type { border-top: none; }',
    '.section-inner { max-width: 720px; margin: 0 auto; }',
    '.section-eyebrow {',
    '  display: block; font-size: 0.72rem; font-weight: 600;',
    '  letter-spacing: 0.16em; text-transform: uppercase;',
    '  color: var(--indigo); margin-bottom: 1rem;',
    '}',
    '.section-h2 {',
    '  font-size: clamp(1.8rem, 4vw, 2.8rem);',
    '  font-weight: 700; letter-spacing: -0.035em; line-height: 1.12;',
    '  color: #f5f5f7; margin-bottom: 2rem;',
    '}',
    '.article-body p {',
    '  font-size: 1.08rem; line-height: 1.88;',
    '  color: rgba(245,245,247,0.82); letter-spacing: -0.01em;',
    '  margin-bottom: 1.75rem;',
    '}',
    '.article-body p:last-child { margin-bottom: 0; }',

    /* SECTION IMAGE */
    '.section-img {',
    '  width: 100%; aspect-ratio: 16/9; object-fit: cover;',
    '  border-radius: 12px; margin: 2.5rem 0;',
    '}',
    '.section-img-caption {',
    '  font-size: 0.75rem; color: var(--text-mute);',
    '  letter-spacing: -0.005em; line-height: 1.5;',
    '  margin-top: -1.75rem; margin-bottom: 2rem;',
    '  text-align: center; font-style: italic;',
    '}',

    /* ARTICLE PULL SENTENCE */
    '.article-pull {',
    '  font-family: var(--font-display);',
    '  font-size: clamp(1.15rem, 2vw, 1.45rem);',
    '  font-style: italic; line-height: 1.6;',
    '  color: rgba(245,245,247,0.92);',
    '  border-top: 1px solid rgba(129,140,248,0.25);',
    '  border-bottom: 1px solid rgba(129,140,248,0.25);',
    '  padding: 1.75rem 0; margin: 2.5rem 0;',
    '}',

    /* BACK TO TOP */
    '.back-to-top {',
    '  display: inline-flex; align-items: center; gap: 0.4rem;',
    '  font-size: 0.75rem; color: var(--text-mute); margin-top: 2.5rem;',
    '  transition: color 0.2s;',
    '}',
    '.back-to-top:hover { color: var(--indigo-lt); }',

    /* RELATED NAV */
    '.related-nav {',
    '  margin-top: 2rem; padding-top: 1.5rem;',
    '  border-top: 1px solid rgba(255,255,255,0.06);',
    '  display: flex; gap: 1.5rem; align-items: center; flex-wrap: wrap;',
    '}',
    '.related-label { font-size: 0.68rem; color: var(--text-mute); letter-spacing: 0.08em; text-transform: uppercase; }',
    '.related-link { font-size: 0.82rem; color: var(--indigo-lt); }',
    '.related-link:hover { text-decoration: underline; }',

    /* STATS STRIP */
    '.section-stats {',
    '  background: #000;',
    '  padding: clamp(4rem,8vw,6rem) 5vw;',
    '  border-top: 1px solid rgba(255,255,255,0.06);',
    '  border-bottom: 1px solid rgba(255,255,255,0.06);',
    '}',
    '.stats-inner {',
    '  max-width: 860px; margin: 0 auto;',
    '  display: grid; grid-template-columns: repeat(3,1fr);',
    '  gap: 2rem; text-align: center;',
    '}',
    '.stat-num {',
    '  font-size: clamp(3rem,6vw,4.5rem);',
    '  font-weight: 700; letter-spacing: -0.045em; line-height: 1;',
    '  color: #f5f5f7; margin-bottom: 0.5rem;',
    '}',
    '.stat-num sup { font-size: 0.5em; vertical-align: super; color: var(--indigo-lt); }',
    '.stat-label { font-size: 0.82rem; color: var(--text-mute); letter-spacing: -0.01em; }',
    '@media (max-width: 600px) { .stats-inner { grid-template-columns: 1fr; gap: 2.5rem; } }',

    /* CTA SECTION */
    '.section-cta {',
    '  background: #0a0a12;',
    '  padding: clamp(5rem,10vw,8rem) 5vw;',
    '  text-align: center;',
    '}',
    '.cta-inner { max-width: 680px; margin: 0 auto; }',
    '.cta-eyebrow {',
    '  display: block; font-size: 0.72rem; font-weight: 600;',
    '  letter-spacing: 0.16em; text-transform: uppercase;',
    '  color: var(--indigo-lt); margin-bottom: 1.2rem;',
    '}',
    '.cta-h2 {',
    '  font-size: clamp(2rem,5vw,3.5rem);',
    '  font-weight: 700; letter-spacing: -0.04em; line-height: 1.05;',
    '  color: #f5f5f7; margin-bottom: 1.25rem;',
    '}',
    '.cta-sub {',
    '  font-size: 1.05rem; color: rgba(255,255,255,0.55);',
    '  line-height: 1.7; letter-spacing: -0.01em; margin-bottom: 2.5rem;',
    '}',
    '.btn {',
    '  display: inline-block; cursor: pointer; border: none;',
    '  border-radius: 980px; font-weight: 500; letter-spacing: -0.01em;',
    '  transition: transform 0.18s ease, box-shadow 0.18s ease, background 0.18s ease;',
    '  text-decoration: none; font-size: 1.05rem;',
    '  padding: 16px 40px;',
    '}',
    '.btn-indigo { background: var(--indigo); color: #fff; }',
    '.btn-indigo:hover { background: #4338ca; box-shadow: 0 8px 32px rgba(79,70,229,0.45); transform: scale(1.02); }',
    '.cta-guarantee { margin-top: 1rem; font-size: 0.78rem; color: rgba(245,245,247,0.45); letter-spacing: .005em; }',

    /* CARL BIO */
    '.bio-section {',
    '  background: #000;',
    '  padding: clamp(4rem,8vw,6rem) 5vw;',
    '  border-top: 1px solid rgba(255,255,255,0.06);',
    '}',
    '.bio-inner { max-width: 720px; margin: 0 auto; display: flex; gap: 2rem; align-items: flex-start; }',
    '.bio-avatar {',
    '  flex-shrink: 0; width: 64px; height: 64px; border-radius: 50%;',
    '  background: linear-gradient(135deg,#4f46e5,#7c3aed);',
    '  display: flex; align-items: center; justify-content: center;',
    '  font-size: 1.2rem; font-weight: 700; color: #fff; letter-spacing: -0.02em;',
    '}',
    '.bio-name { font-size: 0.95rem; font-weight: 600; color: #f5f5f7; margin-bottom: 0.2rem; }',
    '.bio-title { font-size: 0.78rem; color: var(--indigo-lt); margin-bottom: 0.85rem; letter-spacing: -0.01em; }',
    '.bio-text { font-size: 0.9rem; color: rgba(245,245,247,0.65); line-height: 1.75; letter-spacing: -0.01em; }',
    '@media (max-width: 600px) { .bio-inner { flex-direction: column; } }',

    /* NEWSLETTER */
    '.newsletter-section {',
    '  background: #0a0a12; padding: 3rem 5vw;',
    '  border-top: 1px solid rgba(255,255,255,0.06);',
    '}',
    '.newsletter-inner { max-width: 480px; margin: 0 auto; text-align: center; }',
    '.newsletter-label { font-size: 0.85rem; color: rgba(255,255,255,0.5); margin-bottom: 1.2rem; line-height: 1.6; }',
    '.newsletter-form { display: flex; gap: 0.5rem; }',
    '.newsletter-input {',
    '  flex: 1; padding: 10px 16px;',
    '  background: rgba(255,255,255,0.06); border: 1px solid rgba(255,255,255,0.12);',
    '  border-radius: 980px; color: #f5f5f7; font-size: 0.88rem;',
    '  outline: none; font-family: inherit;',
    '  transition: border-color 0.2s;',
    '}',
    '.newsletter-input::placeholder { color: rgba(255,255,255,0.3); }',
    '.newsletter-input:focus { border-color: rgba(129,140,248,0.5); }',
    '.newsletter-btn {',
    '  padding: 10px 20px; background: var(--indigo); color: #fff;',
    '  border: none; border-radius: 980px; font-size: 0.82rem; font-weight: 500;',
    '  cursor: pointer; transition: background 0.2s; white-space: nowrap;',
    '  font-family: inherit;',
    '}',
    '.newsletter-btn:hover { background: #4338ca; }',
    '@media (max-width: 480px) { .newsletter-form { flex-direction: column; } }',

    /* FOOTER */
    '.footer {',
    '  background: #000; padding: 3rem 5vw 2rem;',
    '  border-top: 1px solid rgba(255,255,255,0.06);',
    '  text-align: center;',
    '}',
    '.footer-brand {',
    '  font-size: 1rem; font-weight: 700; letter-spacing: -0.02em;',
    '  color: #f5f5f7; display: block; margin-bottom: 1.5rem;',
    '}',
    '.footer-brand em { color: var(--indigo-lt); font-style: normal; }',
    '.footer-links {',
    '  display: flex; gap: 1.5rem; justify-content: center;',
    '  flex-wrap: wrap; list-style: none; margin-bottom: 1.5rem;',
    '}',
    '.footer-links a { font-size: 0.82rem; color: rgba(255,255,255,0.4); transition: color 0.2s; }',
    '.footer-links a:hover { color: #f5f5f7; }',
    '.footer-legal { font-size: 0.72rem; color: rgba(255,255,255,0.22); }'
  ].join('\n');
  document.head.appendChild(style);

  // Wipe body content
  document.body.innerHTML = '';
  document.title = 'Nashville, All Ten of You \u2014 Butler Button';
  var meta = document.createElement('meta');
  meta.name = 'description';
  meta.content = 'Ten people. Three generations. Five grandchildren three doors from their grandparents. Carl Remi has already handled everything else.';
  document.head.appendChild(meta);

  document.body.innerHTML = [
    '<div class="scroll-progress"></div>',

    // NAV
    '<nav class="nav" id="main-nav">',
    '  <a class="nav-brand" href="/">Butler<em>Button</em></a>',
    '  <ul class="nav-links">',
    '    <li><a href="/trip-planning">Trip Planning</a></li>',
    '    <li><a href="/concierge">Concierge</a></li>',
    '    <li><a href="/travel-advisor">Travel Advisor</a></li>',
    '  </ul>',
    '  <a class="nav-book" href="https://veltmtours.com/embed/butler-booking?popup=true">Get Started</a>',
    '</nav>',

    // HERO
    '<section class="hero" id="top">',
    '  <div class="hero-img"></div>',
    '  <div class="hero-overlay"></div>',
    '  <div class="hero-content">',
    '    <div class="hero-breadcrumb">',
    '      <a href="/">Home</a><span>/</span>',
    '      <span>Butler Button Stories</span><span>/</span>',
    '      <span>Multi-Generational Travel</span>',
    '    </div>',
    '    <span class="hero-eyebrow">Nashville &nbsp;&middot;&nbsp; Multi-Generational Travel</span>',
    '    <h1 class="hero-h1">The Nashville Trip<br>Where Buzz Finally<br>Just Shows Up</h1>',
    '    <p class="hero-sub">Ten people. Three generations. Five grandchildren three doors down from their grandparents. Carl Remi has already handled everything else.</p>',
    '    <div class="hero-meta">',
    '      <span><strong>10</strong> travelers</span>',
    '      <span><strong>3</strong> generations</span>',
    '      <span><strong>Carl Remi</strong> &middot; Butler Button Travel Curator</span>',
    '    </div>',
    '  </div>',
    '</section>',

    // TOC
    '<nav class="toc-strip" aria-label="Article sections">',
    '  <ul class="toc-list">',
    '    <li><a href="#overview" class="toc-link">Overview</a></li>',
    '    <li><a href="#arrival" class="toc-link">The Arrival</a></li>',
    '    <li><a href="#broadway" class="toc-link">A Day on Lower Broadway</a></li>',
    '    <li><a href="#dinner" class="toc-link">The Private Chef Dinner</a></li>',
    '    <li><a href="#buzz" class="toc-link">What Buzz Noticed</a></li>',
    '    <li><a href="#plan" class="toc-link">Plan Your Trip</a></li>',
    '  </ul>',
    '</nav>',

    // CARL PULL QUOTE
    '<div class="pull-quote" id="overview">',
    '  <div class="pull-quote-inner">',
    '    <blockquote>',
    '      &ldquo;The moment I look for in a multi-generational trip is the first dinner &mdash; when the whole family sits down and nobody reaches for a phone. In Nashville, we make that happen with a private chef who comes to the house, a long table set on the back porch, and absolutely nothing left for anyone to coordinate. That dinner tends to run three hours. Families always tell me afterward that it was the night they\u2019ll remember.&rdquo;',
    '    </blockquote>',
    '    <cite>Carl Remi &nbsp;&middot;&nbsp; Butler Button Travel Curator</cite>',
    '  </div>',
    '</div>',

    // SECTION: THE ARRIVAL
    '<section class="article-section" id="arrival">',
    '  <div class="section-inner">',
    '    <span class="section-eyebrow" data-reveal>The Arrival</span>',
    '    <h2 class="section-h2" data-reveal style="--delay:.08s">Nashville greets you<br>before you reach the city.</h2>',
    '    <div class="article-body">',
    '      <p data-reveal style="--delay:.12s">Somewhere on the interstate, the skyline appears &mdash; low and wide, with the Batman Building catching the afternoon light &mdash; and the grandkids start pressing their faces against the van windows. The driver, who Carl arranged and who has been doing this run for nine years, knows to point out the pedestrian bridge and tell the kids they\u2019ll walk it tomorrow.</p>',
    '      <img class="section-img" src="https://images.unsplash.com/photo-1564013799919-ab600027ffc6?auto=format&fit=crop&w=1400&q=85" alt="The East Nashville house Carl Remi chose for the Buzz family" loading="lazy">',
    '      <p class="section-img-caption">The East Nashville house Carl Remi chose for the Buzz family &mdash; floor plan arranged so three generations share a building without sharing a schedule.</p>',
    '      <p data-reveal>By the time the family pulls up to the rental house in East Nashville, the mood has already shifted from airport to vacation. The house is the kind of place that earns its own conversation. A wide front porch with rocking chairs. A backyard with room to run. Bedrooms arranged so that Buzz and his wife have the quiet corner suite while the grandchildren\u2019s rooms cluster around a shared common space that becomes, within about twenty minutes of arrival, the de facto headquarters of the trip.</p>',
    '      <p data-reveal>Nobody had to negotiate this. Carl chose the house specifically because of how the floor plan works for three generations.</p>',
    '      <div class="article-pull" data-reveal>The welcome packet on the kitchen counter is one page. It lists the next day\u2019s schedule, the chef\u2019s arrival time for the private dinner, and Carl\u2019s cell number. There are no passwords to find, no keys to sort out, no instructions about the garbage.</div>',
    '      <p data-reveal>Those details were sent to the property manager three days before arrival. The first hour of this trip belongs entirely to the family.</p>',
    '    </div>',
    '    <div class="related-nav">',
    '      <span class="related-label">Related</span>',
    '      <a class="related-link" href="/trip-planning">Nashville Travel</a>',
    '      <a class="related-link" href="#">Butler Button Stories</a>',
    '      <a class="back-to-top" href="#top">&#8593; Back to Top</a>',
    '    </div>',
    '  </div>',
    '</section>',

    // SECTION: BROADWAY
    '<section class="article-section" id="broadway">',
    '  <div class="section-inner">',
    '    <span class="section-eyebrow" data-reveal>A Day on Lower Broadway</span>',
    '    <h2 class="section-h2" data-reveal style="--delay:.08s">He walks slowly and talks the way people do when they actually love a subject.</h2>',
    '    <div class="article-body">',
    '      <p data-reveal style="--delay:.12s">The guided honky-tonk history tour begins at ten in the morning, which is exactly the right time &mdash; early enough to beat the afternoon crowds on Broadway, late enough for the youngest grandchildren to have eaten breakfast without incident. The guide, Marcus, has been leading these walks for twelve years and grew up two miles from the Ryman. He does not use a microphone or carry a flag.</p>',
    '      <img class="section-img" src="https://images.unsplash.com/photo-1571019613454-1cb2f99b2d8b?auto=format&fit=crop&w=1400&q=85" alt="Lower Broadway at midday" loading="lazy">',
    '      <p class="section-img-caption">Lower Broadway at midday &mdash; the Ryman at the far end, the family taking it all in.</p>',
    '      <p data-reveal>He takes the family into Tootsie\u2019s Orchid Lounge before the band sets up, so they can see the walls &mdash; decades of photographs and signed memorabilia layered over each other the way geological strata accumulate. He tells them about Kris Kristofferson washing dishes nearby while he was writing songs. He shows them where the back door of the Ryman lets out, forty feet from Tootsie\u2019s back door, and explains what that proximity meant to a generation of musicians who were always broke and always between sets.</p>',
    '      <p data-reveal>The grandkids listen in a way they do not always listen.</p>',
    '      <div class="article-pull" data-reveal>By early afternoon the family splinters in the best possible way. Buzz and his son walk into Ernest Tubb Record Shop and spend an hour in the vinyl bins. The daughter-in-law takes the older grandchildren up to the Ryman for the self-guided tour. The youngest two, who have reached their historical-context limit, get ice cream with their grandmother on the riverfront.</div>',
    '      <p data-reveal>Nobody has to coordinate a pickup time &mdash; Marcus has a van and knows where everyone is. At four o\u2019clock, all ten of them are back at the house.</p>',
    '    </div>',
    '    <div class="related-nav">',
    '      <span class="related-label">Related</span>',
    '      <a class="related-link" href="/trip-planning">Nashville Travel</a>',
    '      <a class="related-link" href="#">Butler Button Stories</a>',
    '      <a class="back-to-top" href="#top">&#8593; Back to Top</a>',
    '    </div>',
    '  </div>',
    '</section>',

    // SECTION: PRIVATE CHEF DINNER
    '<section class="article-section" id="dinner">',
    '  <div class="section-inner">',
    '    <span class="section-eyebrow" data-reveal>The Private Chef Dinner</span>',
    '    <h2 class="section-h2" data-reveal style="--delay:.08s">The dinner that runs<br>three hours.</h2>',
    '    <div class="article-body">',
    '      <p data-reveal style="--delay:.12s">Chef Adrienne arrives at the house at four-thirty with two coolers and a folding knife roll. She does not need the kitchen explained to her &mdash; she has cooked here before, and Carl always sends the same house. By five o\u2019clock the back porch smells like garlic and something slow-braised, and the grandchildren have already migrated to the kitchen doorway to watch.</p>',
    '      <img class="section-img" src="https://images.unsplash.com/photo-1414235077428-338989a2e8c0?auto=format&fit=crop&w=1400&q=85" alt="The private chef dinner that ran three hours" loading="lazy">',
    '      <p class="section-img-caption">The private chef dinner that ran three hours. Nobody reached for a phone.</p>',
    '      <p data-reveal>She lets them. She hands the youngest one a sprig of fresh thyme to smell and asks her what it reminds her of. The answer, apparently, is Christmas.</p>',
    '      <p data-reveal>The table is set long &mdash; all ten seats, mismatched candlesticks from the rental house sideboard, a string of lights that someone draped over the pergola earlier in the afternoon. Nobody remembers whose idea the lights were. It does not matter.</p>',
    '      <div class="article-pull" data-reveal>Buzz\u2019s son gives a toast that is longer than he planned. The oldest grandchild, who is seventeen and has spent most of the trip with wireless earbuds in, puts them on the table and leaves them there.</div>',
    '      <p data-reveal>Adrienne brings out a cast-iron skillet of peach cobbler and vanilla ice cream that melts faster than anyone can eat it, and nobody minds. The youngest grandchild falls asleep in her grandmother\u2019s lap before the plates are cleared. Nobody moves her.</p>',
    '    </div>',
    '    <div class="related-nav">',
    '      <span class="related-label">Related</span>',
    '      <a class="related-link" href="/trip-planning">Nashville Travel</a>',
    '      <a class="related-link" href="#">Butler Button Stories</a>',
    '      <a class="back-to-top" href="#top">&#8593; Back to Top</a>',
    '    </div>',
    '  </div>',
    '</section>',

    // SECTION: WHAT BUZZ NOTICED
    '<section class="article-section" id="buzz">',
    '  <div class="section-inner">',
    '    <span class="section-eyebrow" data-reveal>What Buzz Noticed</span>',
    '    <h2 class="section-h2" data-reveal style="--delay:.08s">The trip runs so smoothly<br>it becomes invisible.</h2>',
    '    <div class="article-body">',
    '      <p data-reveal style="--delay:.12s">The thing about a trip that has been arranged well is that you only notice the arrangement in retrospect. During the trip itself, it simply feels like a good trip. The car appears. The table is ready. The rooms are the right distance from each other &mdash; close enough for a grandchild to pad down the hall at seven in the morning, far enough for Buzz and his wife to sleep past eight for the first time in two years.</p>',
    '      <img class="section-img" src="https://images.unsplash.com/photo-1516627145497-ae6968895b74?auto=format&fit=crop&w=1400&q=85" alt="The morning walk on the Greenway" loading="lazy">',
    '      <p class="section-img-caption">The morning walk on the Greenway. The grandfather\u2019s idea. No itinerary required.</p>',
    '      <p data-reveal>Buzz noticed the silences most. Not uncomfortable ones &mdash; the opposite. The kind of silence that happens when a family has been together long enough that they don\u2019t need to fill every moment with conversation. His wife reading on the porch while his son played cards with three of the grandkids inside. The walk he and his daughter-in-law took along the Shelby Bottoms Greenway on the last morning, just the two of them, which they had never done before.</p>',
    '      <div class="article-pull" data-reveal>None of these moments were on the itinerary. They were made possible by the itinerary &mdash; by the fact that nobody had to manage anything, that every logistical question had already been answered, that the trip ran so smoothly it became invisible.</div>',
    '      <p data-reveal>That invisibility is what Carl designs for. When a Butler Button trip works the way it is supposed to, the family never thinks about the planning at all. They just remember Nashville.</p>',
    '    </div>',
    '    <div class="related-nav">',
    '      <span class="related-label">Related</span>',
    '      <a class="related-link" href="/trip-planning">Nashville Travel</a>',
    '      <a class="related-link" href="#">Butler Button Stories</a>',
    '      <a class="back-to-top" href="#top">&#8593; Back to Top</a>',
    '    </div>',
    '  </div>',
    '</section>',

    // STATS
    '<section class="section-stats">',
    '  <div class="stats-inner">',
    '    <div data-reveal>',
    '      <div class="stat-num">10<sup>+</sup></div>',
    '      <div class="stat-label">Years planning Nashville itineraries</div>',
    '    </div>',
    '    <div data-reveal style="--delay:.1s">',
    '      <div class="stat-num">3</div>',
    '      <div class="stat-label">Generations, one seamlessly arranged trip</div>',
    '    </div>',
    '    <div data-reveal style="--delay:.2s">',
    '      <div class="stat-num">0</div>',
    '      <div class="stat-label">Logistics left for the family to manage</div>',
    '    </div>',
    '  </div>',
    '</section>',

    // CTA
    '<section class="section-cta" id="plan">',
    '  <div class="cta-inner">',
    '    <span class="cta-eyebrow" data-reveal>Ready to Plan?</span>',
    '    <h2 class="cta-h2" data-reveal style="--delay:.08s">Your journey starts<br>with a conversation.</h2>',
    '    <p class="cta-sub" data-reveal style="--delay:.14s">The Nashville trip has been on Buzz\u2019s list for a while. Not because it\u2019s hard to get to, or expensive to imagine, but because getting ten people across three generations to the same city at the same time, in the right rooms, with the right experiences already arranged &mdash; that part is genuinely complicated. It is exactly the kind of complexity that Butler Button exists to absorb.</p>',
    '    <p class="cta-sub" data-reveal style="--delay:.18s">Carl Remi is available to talk through what this trip looks like for your family. There is no pitch, no package to choose from. There is just a conversation about what a great trip looks like for the specific people going on it.</p>',
    '    <a class="btn btn-indigo" href="https://veltmtours.com/embed/butler-booking?popup=true" data-reveal style="--delay:.22s">Talk to an Advisor &rarr;</a>',
    '    <div class="cta-guarantee" data-reveal style="--delay:.28s">&#10003; No commitment &nbsp;&middot;&nbsp; &#10003; Real conversation &nbsp;&middot;&nbsp; &#10003; Built around your family</div>',
    '  </div>',
    '</section>',

    // CARL BIO
    '<section class="bio-section">',
    '  <div class="bio-inner" data-reveal>',
    '    <div class="bio-avatar">CR</div>',
    '    <div>',
    '      <div class="bio-name">Carl Remi</div>',
    '      <div class="bio-title">Butler Button Travel Curator</div>',
    '      <p class="bio-text">Carl Remi has spent more than a decade designing trips for families who want to actually be on vacation &mdash; not managing one. He specializes in the logistics that never make the itinerary: the room cluster that keeps grandparents close without sacrificing anyone\u2019s privacy, the transfer timing that accounts for a three-year-old\u2019s nap schedule, the local guide who knows which honky-tonk has the best sightlines for a table of ten. Nashville is a city he returns to every year, and his recommendations have never once come from a press trip.</p>',
    '    </div>',
    '  </div>',
    '</section>',

    // NEWSLETTER
    '<section class="newsletter-section">',
    '  <div class="newsletter-inner" data-reveal>',
    '    <p class="newsletter-label">Travel insights from Butler Button advisors &mdash; weekly ideas from specialists who\u2019ve been there.</p>',
    '    <form class="newsletter-form" onsubmit="return false;">',
    '      <input class="newsletter-input" type="email" placeholder="Your email address" aria-label="Email address">',
    '      <button class="newsletter-btn" type="submit">Subscribe</button>',
    '    </form>',
    '  </div>',
    '</section>',

    // FOOTER
    '<footer class="footer">',
    '  <a class="footer-brand" href="/">Butler<em>Button</em> by VELTM</a>',
    '  <ul class="footer-links">',
    '    <li><a href="/">Home</a></li>',
    '    <li><a href="/trip-planning">Trip Planning</a></li>',
    '    <li><a href="/concierge">Concierge</a></li>',
    '    <li><a href="/travel-advisor">Travel Advisor</a></li>',
    '    <li><a href="/supplier-code">Supplier Code of Conduct</a></li>',
    '    <li><a href="https://help.veltmtours.com/portal/en/kb/">Help Center</a></li>',
    '  </ul>',
    '  <span class="footer-legal">&copy; 2026 VELTM Tours</span>',
    '</footer>'
  ].join('\n');

  // JS BEHAVIORS
  (function() {
    var noMotion = window.matchMedia('(prefers-reduced-motion: reduce)').matches;

    // Nav bg on scroll
    var nav = document.getElementById('main-nav');
    window.addEventListener('scroll', function() {
      nav.classList.toggle('bg', window.scrollY > 60);
    }, { passive: true });

    // Reveal observer
    if (!noMotion) {
      var revealObs = new IntersectionObserver(function(entries) {
        entries.forEach(function(e) {
          if (e.isIntersecting) {
            e.target.classList.add('visible');
            revealObs.unobserve(e.target);
          }
        });
      }, { rootMargin: '0px 0px -7% 0px', threshold: 0.08 });
      document.querySelectorAll('[data-reveal]').forEach(function(el) { revealObs.observe(el); });
    } else {
      document.querySelectorAll('[data-reveal]').forEach(function(el) { el.classList.add('visible'); });
    }

    // Active TOC link on scroll
    var sections = ['arrival', 'broadway', 'dinner', 'buzz', 'plan'];
    var tocLinks = document.querySelectorAll('.toc-link');
    var secEls = sections.map(function(id) { return document.getElementById(id); });
    function updateToc() {
      var scrollY = window.scrollY + 140;
      var current = '';
      secEls.forEach(function(el, i) {
        if (el && el.offsetTop <= scrollY) current = sections[i];
      });
      tocLinks.forEach(function(a) {
        a.classList.toggle('active', a.getAttribute('href') === '#' + current);
      });
    }
    window.addEventListener('scroll', updateToc, { passive: true });

    // Butler Button popup
    document.addEventListener('click', function(e) {
      var a = e.target.closest('a[href*="butler-booking"]');
      if (!a) return;
      e.preventDefault();
      var popup = window.open(a.href, 'butler-booking', 'width=520,height=700,left=' + Math.round((screen.width-520)/2) + ',top=' + Math.round((screen.height-700)/2));
      if (!popup) window.location.href = a.href;
    });
  })();

})();
