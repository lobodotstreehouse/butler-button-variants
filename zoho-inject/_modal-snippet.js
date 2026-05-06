/* ─────────────────────────────────────────────────────────────────
   Shared in-tab purchase modal (v3 modal pass).
   Replaces the click-to-WhatsApp IIFE (_bbWA) with a 3-step intake
   modal that POSTs to Zoho Forms then redirects to Stripe Checkout.

   Three blocks below: CSS, HTML, IIFE handler. Each one is pasted
   verbatim into the v3 inject files (_modal-snippet.js itself is
   not loaded at runtime; it is a single source of truth).

   Stripe Payment Links (locked in v2, reused here):
     trip = https://buy.stripe.com/fZu6oI8DF2cH7Ij9KP4Ni00
     8h   = https://buy.stripe.com/4gM6oI1bd04z6Efg9d4Ni01
     24h  = https://buy.stripe.com/14AaEY6vx2cH4w7e154Ni02

   Zoho Forms public submit URL (set by background agent task ab471a2):
     https://forms.zohopublic.in/VELTM/form/ButlerButtonTripIntake/formperma/__FORMPERMA__
   The string __FORMPERMA__ in this file is replaced once the form
   is created. Until then, the modal still works for preview: the
   Zoho POST fails silently and the redirect to Stripe still fires.
   ───────────────────────────────────────────────────────────────── */

window.BB_MODAL_CSS = `
/* ── Modal (v3) ─────────────────────────────────────────────────── */
.bb-modal{padding:0;border:none;background:transparent;max-width:none;max-height:none;width:100%;height:100%;color:#fff;overflow:visible}
.bb-modal::backdrop{background:rgba(5,5,8,0.78);backdrop-filter:blur(6px)}
.bb-modal[open]{display:flex;align-items:center;justify-content:center}
.bb-modal__shell{position:relative;width:min(640px,calc(100vw - 2rem));max-height:calc(100vh - 2rem);overflow-y:auto;background:#0c0c10;border:1px solid rgba(255,255,255,0.08);border-radius:16px;padding:1.6rem 1.8rem 2rem;box-shadow:0 30px 80px -20px rgba(0,0,0,0.6),0 0 0 1px rgba(165,180,252,0.06)}
.bb-modal__header{display:flex;align-items:center;justify-content:space-between;margin-bottom:0.4rem}
.bb-modal__brand{font-size:0.78rem;font-weight:600;letter-spacing:0.16em;text-transform:uppercase;color:#a5b4fc}
.bb-modal__close{appearance:none;background:transparent;border:none;color:rgba(255,255,255,0.55);font-size:1.55rem;line-height:1;cursor:pointer;padding:0.2rem 0.5rem;border-radius:6px;transition:background .15s ease,color .15s ease}
.bb-modal__close:hover{background:rgba(255,255,255,0.06);color:#fff}
.bb-modal__progress{display:flex;gap:0.45rem;margin:0.55rem 0 1.4rem}
.bb-modal__pip{height:3px;flex:1;background:rgba(255,255,255,0.08);border-radius:2px;transition:background .25s ease}
.bb-modal__pip.is-active{background:#a5b4fc}
.bb-modal__pip.is-done{background:rgba(165,180,252,0.55)}
.bb-modal__title{font-family:'Playfair Display',Georgia,serif;font-weight:600;font-size:clamp(1.45rem,2.6vw,1.95rem);letter-spacing:-0.02em;line-height:1.15;margin:0 0 0.7rem;color:#fff}
.bb-modal__lede{color:rgba(255,255,255,0.65);font-size:0.96rem;line-height:1.55;margin:0 0 1.2rem;letter-spacing:-0.005em}
.bb-modal__step[hidden]{display:none}

.bb-modal__form{display:grid;gap:0.95rem}
.bb-modal__row{display:grid;gap:0.4rem}
.bb-modal__row--2{grid-template-columns:1fr 1fr;gap:0.85rem}
@media (max-width:540px){.bb-modal__row--2{grid-template-columns:1fr}}
.bb-modal__label{font-size:0.78rem;font-weight:500;letter-spacing:0.04em;text-transform:uppercase;color:rgba(255,255,255,0.55)}
.bb-modal__label--req::after{content:" *";color:#f87171}
.bb-modal__input,.bb-modal__textarea{appearance:none;width:100%;background:rgba(255,255,255,0.04);border:1px solid rgba(255,255,255,0.1);border-radius:10px;padding:0.7rem 0.85rem;color:#fff;font:inherit;font-size:0.96rem;letter-spacing:-0.005em;transition:border-color .15s ease,background .15s ease}
.bb-modal__input:focus,.bb-modal__textarea:focus{outline:none;border-color:#a5b4fc;background:rgba(255,255,255,0.07)}
.bb-modal__input::placeholder,.bb-modal__textarea::placeholder{color:rgba(255,255,255,0.32)}
.bb-modal__input:disabled{opacity:0.45;cursor:not-allowed}
.bb-modal__textarea{min-height:84px;resize:vertical;line-height:1.5}
.bb-modal__skip{display:flex;align-items:center;gap:0.4rem;margin-top:0.3rem;font-size:0.82rem;color:rgba(255,255,255,0.5);cursor:pointer;user-select:none}
.bb-modal__skip input{accent-color:#a5b4fc;width:14px;height:14px;cursor:pointer}
.bb-modal__skip:hover{color:rgba(255,255,255,0.75)}
.bb-modal__error{font-size:0.8rem;color:#fca5a5;margin-top:0.2rem;display:none}
.bb-modal__row.has-error .bb-modal__error{display:block}
.bb-modal__row.has-error .bb-modal__input{border-color:#f87171}
.bb-modal__caption{font-size:0.82rem;color:rgba(255,255,255,0.5);line-height:1.5;margin:0.4rem 0 0;letter-spacing:-0.005em}
.bb-modal__actions{display:flex;justify-content:flex-end;gap:0.7rem;margin-top:1.3rem}
.bb-modal__btn{appearance:none;border:none;font:inherit;font-weight:500;font-size:0.96rem;letter-spacing:-0.005em;padding:0.78rem 1.3rem;border-radius:10px;cursor:pointer;transition:transform .15s ease,background .15s ease,color .15s ease}
.bb-modal__btn--primary{background:#a5b4fc;color:#0a0a14}
.bb-modal__btn--primary:hover{background:#c7d2fe;transform:translateY(-1px)}
.bb-modal__btn--primary:disabled{background:rgba(165,180,252,0.35);cursor:not-allowed;transform:none}
.bb-modal__btn--ghost{background:transparent;color:rgba(255,255,255,0.7);padding-left:0.7rem;padding-right:0.7rem}
.bb-modal__btn--ghost:hover{color:#fff;background:rgba(255,255,255,0.05)}

.bb-modal__h3{font-family:'Playfair Display',Georgia,serif;font-weight:600;font-size:1.35rem;letter-spacing:-0.015em;margin:0 0 0.4rem;color:#fff}
.bb-modal__sub{color:rgba(255,255,255,0.6);font-size:0.94rem;margin:0 0 1.2rem;line-height:1.5;letter-spacing:-0.005em}
.bb-modal__tiers{display:grid;gap:0.7rem}
.bb-modal__tier{display:grid;grid-template-columns:1fr auto;gap:0.4rem 1rem;align-items:start;padding:1.05rem 1.15rem;background:rgba(255,255,255,0.03);border:1px solid rgba(255,255,255,0.1);border-radius:12px;cursor:pointer;transition:border-color .15s ease,background .15s ease}
.bb-modal__tier:hover{background:rgba(255,255,255,0.05);border-color:rgba(165,180,252,0.35)}
.bb-modal__tier.is-selected{border-color:#a5b4fc;background:rgba(165,180,252,0.07)}
.bb-modal__tier-name{font-size:1.05rem;font-weight:600;letter-spacing:-0.01em;color:#fff}
.bb-modal__tier-price{font-size:1.02rem;font-weight:600;color:#a5b4fc;text-align:right;white-space:nowrap}
.bb-modal__tier-unit{font-size:0.78rem;color:rgba(255,255,255,0.5);font-weight:400;display:block}
.bb-modal__tier-desc{font-size:0.9rem;color:rgba(255,255,255,0.62);line-height:1.5;letter-spacing:-0.005em;grid-column:1 / -1;margin-top:0.15rem}

.bb-modal__summary{padding:1.05rem 1.15rem;background:rgba(255,255,255,0.03);border:1px solid rgba(255,255,255,0.1);border-radius:12px;margin-bottom:0.9rem}
.bb-modal__summary-row{display:flex;justify-content:space-between;align-items:baseline;font-size:0.94rem;letter-spacing:-0.005em;padding:0.32rem 0;border-bottom:1px solid rgba(255,255,255,0.06)}
.bb-modal__summary-row:last-child{border-bottom:none;padding-top:0.6rem;font-weight:600;font-size:1.05rem}
.bb-modal__summary-key{color:rgba(255,255,255,0.55)}
.bb-modal__summary-val{color:#fff;text-align:right;max-width:60%;word-break:break-word}
.bb-modal__legal{font-size:0.78rem;color:rgba(255,255,255,0.4);line-height:1.55;margin:1rem 0 0;letter-spacing:-0.005em}

.bb-modal__hatch{margin-top:1.6rem;padding-top:1.2rem;border-top:1px solid rgba(255,255,255,0.06)}
.bb-modal__hatch>summary{font-size:0.86rem;color:rgba(255,255,255,0.55);cursor:pointer;list-style:none;display:inline-flex;align-items:center;gap:0.35rem;letter-spacing:-0.005em}
.bb-modal__hatch>summary::-webkit-details-marker{display:none}
.bb-modal__hatch>summary::before{content:"+";font-size:1rem;color:#a5b4fc;width:1rem;text-align:center}
.bb-modal__hatch[open]>summary::before{content:"\\2013"}
.bb-modal__hatch>summary:hover{color:#fff}
.bb-modal__hatch-grid{display:grid;grid-template-columns:repeat(3,1fr);gap:0.6rem;margin-top:0.95rem}
@media (max-width:540px){.bb-modal__hatch-grid{grid-template-columns:1fr}}
.bb-modal__hatch-card{display:flex;flex-direction:column;gap:0.25rem;padding:0.85rem 0.95rem;background:rgba(255,255,255,0.03);border:1px solid rgba(255,255,255,0.08);border-radius:10px;color:#fff;text-decoration:none;transition:border-color .15s ease,background .15s ease}
.bb-modal__hatch-card:hover{background:rgba(255,255,255,0.05);border-color:rgba(165,180,252,0.35)}
.bb-modal__hatch-name{font-size:0.86rem;font-weight:500;letter-spacing:-0.005em}
.bb-modal__hatch-cta{font-size:0.76rem;color:#a5b4fc;letter-spacing:-0.005em}

.bb-modal__loading{display:none;align-items:center;gap:0.4rem;font-size:0.82rem;color:rgba(255,255,255,0.6)}
.bb-modal[data-loading="true"] .bb-modal__loading{display:inline-flex}
.bb-modal[data-loading="true"] .bb-modal__btn{opacity:0.5;pointer-events:none}
.bb-modal__spinner{width:13px;height:13px;border-radius:50%;border:2px solid rgba(165,180,252,0.25);border-top-color:#a5b4fc;animation:bbSpin 0.7s linear infinite}
@keyframes bbSpin{to{transform:rotate(360deg)}}
`;

window.BB_MODAL_HTML = `
<dialog class="bb-modal" id="bbModal" aria-labelledby="bbModal__title">
  <div class="bb-modal__shell">
    <div class="bb-modal__header">
      <div class="bb-modal__brand">Butler Button</div>
      <button class="bb-modal__close" type="button" aria-label="Close" data-action="close">&times;</button>
    </div>
    <div class="bb-modal__progress" role="progressbar" aria-valuemin="1" aria-valuemax="3" aria-valuenow="1">
      <span class="bb-modal__pip is-active" data-pip="1"></span>
      <span class="bb-modal__pip" data-pip="2"></span>
      <span class="bb-modal__pip" data-pip="3"></span>
    </div>
    <h2 id="bbModal__title" class="bb-modal__title">Your trip, planned by a real human.</h2>

    <section class="bb-modal__step" data-step="1">
      <p class="bb-modal__lede">Just two things are required: a name and an email so we can reach you. Everything else helps your Butler hit the ground running, but you can leave it for later.</p>
      <form class="bb-modal__form" id="bbModal__form" novalidate>
        <div class="bb-modal__row">
          <label class="bb-modal__label bb-modal__label--req" for="bbm-name">Your name</label>
          <input class="bb-modal__input" id="bbm-name" name="Name" type="text" autocomplete="name" required>
          <span class="bb-modal__error">Please tell us what to call you.</span>
        </div>
        <div class="bb-modal__row">
          <label class="bb-modal__label bb-modal__label--req" for="bbm-email">Email</label>
          <input class="bb-modal__input" id="bbm-email" name="Email" type="email" autocomplete="email" required>
          <span class="bb-modal__error">A real email, please. We will reach you here.</span>
        </div>
        <div class="bb-modal__row">
          <label class="bb-modal__label" for="bbm-dest">Destination(s)</label>
          <input class="bb-modal__input" id="bbm-dest" name="Destination" type="text" placeholder="Tokyo, then Kyoto. Or somewhere with a beach.">
          <label class="bb-modal__skip"><input type="checkbox" data-skip="bbm-dest"> Not sure yet, my Butler can help me figure this out.</label>
        </div>
        <div class="bb-modal__row">
          <label class="bb-modal__label" for="bbm-dates">Dates or month</label>
          <input class="bb-modal__input" id="bbm-dates" name="Dates" type="text" placeholder="June 12 to 24. Or roughly fall.">
          <label class="bb-modal__skip"><input type="checkbox" data-skip="bbm-dates"> Not sure yet, my Butler can help me figure this out.</label>
        </div>
        <div class="bb-modal__row">
          <label class="bb-modal__label" for="bbm-party">Party size</label>
          <input class="bb-modal__input" id="bbm-party" name="PartySize" type="number" min="1" max="50" placeholder="How many travellers?">
        </div>
        <div class="bb-modal__row">
          <label class="bb-modal__label" for="bbm-brief">Anything else?</label>
          <textarea class="bb-modal__textarea" id="bbm-brief" name="Brief" placeholder="Honeymoon, dietary restrictions, dream stay, whatever helps."></textarea>
        </div>
        <p class="bb-modal__caption">If you skipped destination or dates, we will reach out by email or WhatsApp to lock them in before your Butler starts work.</p>
        <div class="bb-modal__actions">
          <button class="bb-modal__btn bb-modal__btn--primary" type="submit">Continue &rarr;</button>
        </div>
      </form>
    </section>

    <section class="bb-modal__step" data-step="2" hidden>
      <h3 class="bb-modal__h3">Pick your Butler tier.</h3>
      <p class="bb-modal__sub">All tiers are paid up front. Your Butler reaches you on WhatsApp within minutes of payment.</p>
      <div class="bb-modal__tiers" role="radiogroup" aria-label="Butler tiers">
        <div class="bb-modal__tier" role="radio" tabindex="0" data-tier-card="trip" aria-checked="false">
          <div class="bb-modal__tier-name">Trip Plan</div>
          <div class="bb-modal__tier-price">$25<span class="bb-modal__tier-unit">one-time</span></div>
          <div class="bb-modal__tier-desc">A real itinerary, written by a Butler who has been there. 24-hour turnaround.</div>
        </div>
        <div class="bb-modal__tier" role="radio" tabindex="0" data-tier-card="8h" aria-checked="false">
          <div class="bb-modal__tier-name">8-Hour Butler</div>
          <div class="bb-modal__tier-price">$25<span class="bb-modal__tier-unit">per day</span></div>
          <div class="bb-modal__tier-desc">A live Butler on WhatsApp during your day. Bookings, swaps, recommendations on demand.</div>
        </div>
        <div class="bb-modal__tier" role="radio" tabindex="0" data-tier-card="24h" aria-checked="false">
          <div class="bb-modal__tier-name">24-Hour Butler</div>
          <div class="bb-modal__tier-price">$100<span class="bb-modal__tier-unit">per day</span></div>
          <div class="bb-modal__tier-desc">Always-on Butler. 3am gate change? Sorted before you wake up.</div>
        </div>
      </div>
      <div class="bb-modal__actions">
        <button class="bb-modal__btn bb-modal__btn--ghost" type="button" data-action="back">&larr; Back</button>
        <button class="bb-modal__btn bb-modal__btn--primary" type="button" data-action="next" disabled>Continue &rarr;</button>
      </div>
    </section>

    <section class="bb-modal__step" data-step="3" hidden>
      <h3 class="bb-modal__h3">Ready to lock it in.</h3>
      <p class="bb-modal__sub">A quick check, then we hand you off to Stripe.</p>
      <div class="bb-modal__summary" id="bbModal__summary"></div>
      <p class="bb-modal__legal">Payment is processed by Stripe (Apple Pay, Google Pay, Link, and cards accepted). Your Butler will message you on WhatsApp within minutes of payment. Refundable if we cannot match a Butler.</p>
      <div class="bb-modal__actions">
        <button class="bb-modal__btn bb-modal__btn--ghost" type="button" data-action="back">&larr; Back</button>
        <span class="bb-modal__loading"><span class="bb-modal__spinner"></span>Sending you to checkout&hellip;</span>
        <button class="bb-modal__btn bb-modal__btn--primary" type="button" data-action="checkout">Continue to secure checkout &rarr;</button>
      </div>
    </section>

    <details class="bb-modal__hatch">
      <summary>Or talk to us first</summary>
      <div class="bb-modal__hatch-grid">
        <a class="bb-modal__hatch-card" href="https://wa.me/18555031555" target="_blank" rel="noopener">
          <span class="bb-modal__hatch-name">WhatsApp</span>
          <span class="bb-modal__hatch-cta">Open chat &rarr;</span>
        </a>
        <a class="bb-modal__hatch-card" href="https://veltmtoursofficial.zohobookings.in/#/veltmtourspvtltd" target="_blank" rel="noopener">
          <span class="bb-modal__hatch-name">Video Call</span>
          <span class="bb-modal__hatch-cta">Schedule a call &rarr;</span>
        </a>
        <a class="bb-modal__hatch-card" href="mailto:contact@butlerbutton.co">
          <span class="bb-modal__hatch-name">Email</span>
          <span class="bb-modal__hatch-cta">Email us &rarr;</span>
        </a>
      </div>
    </details>
  </div>
</dialog>
`;

window.BB_MODAL_HANDLER = `
<script>
(function(){
  if (window._bbModal) return;
  window._bbModal = true;

  var TIERS = {
    'trip': { name: 'Trip Plan', price: 25, unit: 'one-time', stripe: 'https://buy.stripe.com/fZu6oI8DF2cH7Ij9KP4Ni00' },
    '8h':   { name: '8-Hour Butler', price: 25, unit: 'per day', stripe: 'https://buy.stripe.com/4gM6oI1bd04z6Efg9d4Ni01' },
    '24h':  { name: '24-Hour Butler', price: 100, unit: 'per day', stripe: 'https://buy.stripe.com/14AaEY6vx2cH4w7e154Ni02' }
  };
  var FORMS_URL = 'https://forms.zohopublic.in/VELTM/form/ButlerButtonTripIntake/formperma/__FORMPERMA__/htmlRecords/submit';

  var dlg = document.getElementById('bbModal');
  if (!dlg) return;
  var form = document.getElementById('bbModal__form');
  var summary = document.getElementById('bbModal__summary');
  var state = { step: 1, tier: null, intake: {}, refId: null };

  function genRef() {
    return 'bb_' + Date.now().toString(36) + '_' + Math.random().toString(36).slice(2,10);
  }

  function showStep(n) {
    state.step = n;
    dlg.querySelectorAll('.bb-modal__step').forEach(function(s){
      s.hidden = (parseInt(s.getAttribute('data-step'),10) !== n);
    });
    dlg.querySelectorAll('.bb-modal__pip').forEach(function(p){
      var i = parseInt(p.getAttribute('data-pip'),10);
      p.classList.toggle('is-active', i === n);
      p.classList.toggle('is-done', i < n);
    });
    var pr = dlg.querySelector('.bb-modal__progress');
    if (pr) pr.setAttribute('aria-valuenow', String(n));
  }

  function selectTier(t) {
    state.tier = t;
    dlg.querySelectorAll('.bb-modal__tier').forEach(function(c){
      var matches = c.getAttribute('data-tier-card') === t;
      c.classList.toggle('is-selected', matches);
      c.setAttribute('aria-checked', matches ? 'true' : 'false');
    });
    var nextBtn = dlg.querySelector('[data-step="2"] [data-action="next"]');
    if (nextBtn) nextBtn.disabled = !t;
  }

  function renderSummary() {
    var tier = TIERS[state.tier] || { name: '(none)', price: 0, unit: '' };
    var i = state.intake;
    var rows = [
      ['Name', i.Name || '(provided)'],
      ['Email', i.Email || '(provided)'],
      ['Destination', i.Destination || 'To be confirmed with Butler'],
      ['Dates', i.Dates || 'To be confirmed with Butler'],
      ['Tier', tier.name],
      ['Total', '$' + tier.price + (tier.unit ? ' ' + tier.unit : '')]
    ];
    summary.innerHTML = rows.map(function(r){
      return '<div class="bb-modal__summary-row"><span class="bb-modal__summary-key">' + r[0] + '</span><span class="bb-modal__summary-val">' + String(r[1]).replace(/[<>&"']/g, function(m){return ({'<':'&lt;','>':'&gt;','&':'&amp;','"':'&quot;',"'":'&#39;'})[m];}) + '</span></div>';
    }).join('');
  }

  function openModal(tier) {
    state.tier = null;
    state.intake = {};
    state.refId = genRef();
    if (form) form.reset();
    dlg.querySelectorAll('.bb-modal__row').forEach(function(r){ r.classList.remove('has-error'); });
    dlg.querySelectorAll('.bb-modal__skip input').forEach(function(c){ c.checked = false; });
    dlg.querySelectorAll('[data-skip]').forEach(function(c){
      var input = document.getElementById(c.getAttribute('data-skip'));
      if (input) { input.disabled = false; input.value = ''; }
    });
    selectTier(tier && TIERS[tier] ? tier : null);
    showStep(1);
    if (typeof dlg.showModal === 'function') {
      try { dlg.showModal(); } catch(e) { dlg.setAttribute('open',''); }
    } else {
      dlg.setAttribute('open','');
    }
    setTimeout(function(){
      var first = dlg.querySelector('input,button,select,textarea');
      if (first) first.focus();
    }, 50);
  }

  function closeModal() {
    if (typeof dlg.close === 'function') {
      try { dlg.close(); } catch(e) { dlg.removeAttribute('open'); }
    } else {
      dlg.removeAttribute('open');
    }
  }

  document.addEventListener('click', function(e){
    var trig = e.target.closest('[data-butler-button]');
    if (trig) {
      e.preventDefault();
      var t = trig.getAttribute('data-tier');
      openModal(t);
      return;
    }
    if (e.target.closest('[data-action="close"]')) { e.preventDefault(); closeModal(); return; }
    if (e.target === dlg) { closeModal(); return; }
    var back = e.target.closest('[data-action="back"]');
    if (back) { e.preventDefault(); showStep(Math.max(1, state.step - 1)); return; }
    var next = e.target.closest('[data-action="next"]');
    if (next) { e.preventDefault(); if (state.tier) { renderSummary(); showStep(3); } return; }
    var card = e.target.closest('[data-tier-card]');
    if (card) { e.preventDefault(); selectTier(card.getAttribute('data-tier-card')); return; }
    if (e.target.closest('[data-action="checkout"]')) { e.preventDefault(); doCheckout(); return; }
  });

  document.addEventListener('keydown', function(e){
    if (!dlg.open) return;
    if (e.key === 'Escape') { closeModal(); return; }
    if (e.key === 'Enter' && state.step === 2 && state.tier) {
      var card = e.target.closest('[data-tier-card]');
      if (card) { e.preventDefault(); selectTier(card.getAttribute('data-tier-card')); }
    }
  });

  dlg.addEventListener('change', function(e){
    var skip = e.target.closest('.bb-modal__skip input[data-skip]');
    if (!skip) return;
    var input = document.getElementById(skip.getAttribute('data-skip'));
    if (!input) return;
    if (skip.checked) { input.value = ''; input.disabled = true; }
    else { input.disabled = false; input.focus(); }
  });

  if (form) {
    form.addEventListener('submit', function(e){
      e.preventDefault();
      var name = form.querySelector('#bbm-name');
      var email = form.querySelector('#bbm-email');
      var ok = true;
      [name, email].forEach(function(inp){
        var row = inp.closest('.bb-modal__row');
        var valid = inp.value.trim().length > 0 && (inp.type !== 'email' || /^[^@\\s]+@[^@\\s]+\\.[^@\\s]+$/.test(inp.value.trim()));
        row.classList.toggle('has-error', !valid);
        if (!valid) ok = false;
      });
      if (!ok) { var firstBad = form.querySelector('.has-error .bb-modal__input'); if (firstBad) firstBad.focus(); return; }
      state.intake = {
        Name: name.value.trim(),
        Email: email.value.trim(),
        Destination: form.querySelector('#bbm-dest').value.trim(),
        Dates: form.querySelector('#bbm-dates').value.trim(),
        PartySize: form.querySelector('#bbm-party').value.trim(),
        Brief: form.querySelector('#bbm-brief').value.trim()
      };
      showStep(2);
    });
  }

  function doCheckout() {
    if (!state.tier || !TIERS[state.tier]) return;
    dlg.setAttribute('data-loading','true');
    var payload = Object.assign({}, state.intake, {
      Tier: state.tier,
      ClientReferenceId: state.refId,
      OriginPage: location.pathname
    });
    var fd = new FormData();
    Object.keys(payload).forEach(function(k){ fd.append(k, payload[k] || ''); });
    var doneCount = 0;
    var redirect = function() {
      var stripeURL = TIERS[state.tier].stripe
        + '?prefilled_email=' + encodeURIComponent(state.intake.Email || '')
        + '&client_reference_id=' + encodeURIComponent(state.refId);
      window.location.assign(stripeURL);
    };
    var done = function() { doneCount += 1; if (doneCount === 1) redirect(); };
    var timeout = setTimeout(done, 1800);
    if (FORMS_URL.indexOf('__FORMPERMA__') === -1) {
      fetch(FORMS_URL, { method: 'POST', body: fd, mode: 'no-cors' })
        .then(function(){ clearTimeout(timeout); done(); })
        .catch(function(){ clearTimeout(timeout); done(); });
    } else {
      clearTimeout(timeout);
      done();
    }
  }
})();
<\/script>
`;
