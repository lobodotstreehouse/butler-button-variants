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
/* ── Modal (v3, light theme) ────────────────────────────────────── */
.bb-modal{padding:0;border:none;background:transparent;max-width:none;max-height:none;width:100%;height:100%;color:#0f172a;overflow:visible}
.bb-modal::backdrop{background:rgba(5,5,8,0.62);backdrop-filter:blur(6px)}
.bb-modal[open]{display:flex;align-items:center;justify-content:center}
.bb-modal__shell{position:relative;width:min(680px,calc(100vw - 2rem));max-height:calc(100vh - 2rem);overflow-y:auto;background:#ffffff;border:1px solid rgba(15,23,42,0.08);border-radius:18px;padding:1.8rem 2rem 2.1rem;box-shadow:0 30px 80px -20px rgba(15,23,42,0.35),0 0 0 1px rgba(15,23,42,0.04)}
.bb-modal__header{display:flex;align-items:center;justify-content:space-between;margin-bottom:0.5rem}
.bb-modal__brand{font-size:0.86rem;font-weight:700;letter-spacing:0.18em;text-transform:uppercase;color:#4f46e5}
.bb-modal__close{appearance:none;background:transparent;border:none;color:#475569;font-size:1.7rem;line-height:1;cursor:pointer;padding:0.2rem 0.55rem;border-radius:8px;transition:background .15s ease,color .15s ease}
.bb-modal__close:hover{background:rgba(15,23,42,0.05);color:#0f172a}
.bb-modal__progress{display:flex;gap:0.45rem;margin:0.7rem 0 1.5rem}
.bb-modal__pip{height:4px;flex:1;background:rgba(15,23,42,0.08);border-radius:2px;transition:background .25s ease}
.bb-modal__pip.is-active{background:#4f46e5}
.bb-modal__pip.is-done{background:rgba(79,70,229,0.55)}
.bb-modal__title{font-family:'Playfair Display',Georgia,serif;font-weight:600;font-size:clamp(1.7rem,2.8vw,2.15rem);letter-spacing:-0.02em;line-height:1.15;margin:0 0 0.8rem;color:#0f172a}
.bb-modal__lede{color:#334155;font-size:1.05rem;font-weight:400;line-height:1.55;margin:0 0 1.3rem;letter-spacing:-0.005em}
.bb-modal__step[hidden]{display:none}

.bb-modal__form{display:grid;gap:1.05rem}
.bb-modal__row{display:grid;gap:0.45rem}
.bb-modal__row--2{grid-template-columns:1fr 1fr;gap:0.95rem}
@media (max-width:540px){.bb-modal__row--2{grid-template-columns:1fr}}
.bb-modal__label{font-size:0.86rem;font-weight:600;letter-spacing:0.04em;text-transform:uppercase;color:#334155}
.bb-modal__label--req::after{content:" *";color:#dc2626}
.bb-modal__input,.bb-modal__textarea{appearance:none;width:100%;background:#f8fafc;border:1px solid rgba(15,23,42,0.12);border-radius:10px;padding:0.78rem 0.95rem;color:#0f172a;font:inherit;font-size:1rem;letter-spacing:-0.005em;transition:border-color .15s ease,background .15s ease,box-shadow .15s ease}
.bb-modal__input:focus,.bb-modal__textarea:focus{outline:none;border-color:#4f46e5;background:#ffffff;box-shadow:0 0 0 3px rgba(79,70,229,0.18)}
.bb-modal__input::placeholder,.bb-modal__textarea::placeholder{color:#94a3b8}
.bb-modal__input:disabled{opacity:0.55;cursor:not-allowed;background:rgba(15,23,42,0.04)}
.bb-modal__textarea{min-height:88px;resize:vertical;line-height:1.5}
.bb-modal__skip{display:flex;align-items:center;gap:0.45rem;margin-top:0.35rem;font-size:0.92rem;color:#475569;cursor:pointer;user-select:none}
.bb-modal__skip input{accent-color:#4f46e5;width:15px;height:15px;cursor:pointer}
.bb-modal__skip:hover{color:#0f172a}
.bb-modal__error{font-size:0.88rem;color:#dc2626;margin-top:0.25rem;display:none;font-weight:500}
.bb-modal__row.has-error .bb-modal__error{display:block}
.bb-modal__row.has-error .bb-modal__input{border-color:#dc2626;background:#fef2f2}
.bb-modal__caption{font-size:0.92rem;color:#475569;line-height:1.55;margin:0.5rem 0 0;letter-spacing:-0.005em}
.bb-modal__actions{display:flex;justify-content:flex-end;gap:0.7rem;margin-top:1.4rem;align-items:center}
.bb-modal__btn{appearance:none;border:none;font:inherit;font-weight:600;font-size:1rem;letter-spacing:-0.005em;padding:0.85rem 1.45rem;border-radius:10px;cursor:pointer;transition:transform .15s ease,background .15s ease,color .15s ease,box-shadow .15s ease}
.bb-modal__btn--primary{background:#4f46e5;color:#ffffff;box-shadow:0 1px 2px rgba(15,23,42,0.06),0 4px 12px -4px rgba(79,70,229,0.4)}
.bb-modal__btn--primary:hover{background:#4338ca;transform:translateY(-1px);box-shadow:0 2px 4px rgba(15,23,42,0.08),0 8px 20px -6px rgba(79,70,229,0.5)}
.bb-modal__btn--primary:disabled{background:rgba(79,70,229,0.32);color:#ffffff;cursor:not-allowed;transform:none;box-shadow:none}
.bb-modal__btn--ghost{background:transparent;color:#475569;padding-left:0.8rem;padding-right:0.8rem;font-weight:500}
.bb-modal__btn--ghost:hover{color:#0f172a;background:rgba(15,23,42,0.05)}

.bb-modal__h3{font-family:'Playfair Display',Georgia,serif;font-weight:600;font-size:clamp(1.45rem,2.4vw,1.7rem);letter-spacing:-0.015em;margin:0 0 0.5rem;color:#0f172a;line-height:1.2}
.bb-modal__sub{color:#475569;font-size:1.02rem;margin:0 0 1.3rem;line-height:1.55;letter-spacing:-0.005em}
.bb-modal__tiers{display:grid;gap:0.8rem}
.bb-modal__tier{display:grid;grid-template-columns:1fr auto;gap:0.45rem 1.1rem;align-items:start;padding:1.15rem 1.25rem;background:#ffffff;border:1.5px solid rgba(15,23,42,0.1);border-radius:12px;cursor:pointer;transition:border-color .15s ease,background .15s ease,box-shadow .15s ease}
.bb-modal__tier:hover{background:#f8fafc;border-color:rgba(79,70,229,0.4)}
.bb-modal__tier.is-selected{border-color:#4f46e5;background:#eef2ff;box-shadow:0 0 0 3px rgba(79,70,229,0.12)}
.bb-modal__tier-name{font-size:1.12rem;font-weight:700;letter-spacing:-0.01em;color:#0f172a}
.bb-modal__tier-price{font-size:1.18rem;font-weight:700;color:#4f46e5;text-align:right;white-space:nowrap;line-height:1.1}
.bb-modal__tier-unit{font-size:0.82rem;color:#64748b;font-weight:500;display:block;margin-top:0.15rem}
.bb-modal__tier-desc{font-size:0.98rem;color:#475569;line-height:1.55;letter-spacing:-0.005em;grid-column:1 / -1;margin-top:0.2rem}
.bb-modal__days{display:none;flex-wrap:wrap;align-items:center;gap:0.6rem;margin-top:0.9rem;grid-column:1 / -1;padding-top:0.9rem;border-top:1px dashed rgba(15,23,42,0.12)}
.bb-modal__tier.is-selected[data-has-days="true"] .bb-modal__days{display:flex}
.bb-modal__days-label{font-size:0.95rem;color:#334155;font-weight:500;letter-spacing:-0.005em;margin-right:auto}
.bb-modal__step-btn{appearance:none;border:1.5px solid rgba(15,23,42,0.15);background:#ffffff;color:#0f172a;width:34px;height:34px;border-radius:8px;font-size:1.15rem;font-weight:600;cursor:pointer;display:inline-flex;align-items:center;justify-content:center;line-height:1;transition:background .15s ease,border-color .15s ease}
.bb-modal__step-btn:hover{background:#eef2ff;border-color:#4f46e5}
.bb-modal__step-btn:disabled{opacity:0.35;cursor:not-allowed}
.bb-modal__days-val{min-width:2.5ch;text-align:center;font-weight:700;color:#0f172a;font-size:1.1rem}
.bb-modal__days-total{font-size:1rem;color:#4f46e5;font-weight:700;letter-spacing:-0.005em;margin-left:0.4rem}

.bb-modal__summary{padding:1.15rem 1.25rem;background:#f8fafc;border:1px solid rgba(15,23,42,0.08);border-radius:12px;margin-bottom:1rem}
.bb-modal__summary-row{display:flex;justify-content:space-between;align-items:baseline;font-size:1rem;letter-spacing:-0.005em;padding:0.4rem 0;border-bottom:1px solid rgba(15,23,42,0.06)}
.bb-modal__summary-row:last-child{border-bottom:none;padding-top:0.7rem;font-weight:700;font-size:1.12rem}
.bb-modal__summary-key{color:#64748b;font-weight:500}
.bb-modal__summary-val{color:#0f172a;font-weight:500;text-align:right;max-width:60%;word-break:break-word}
.bb-modal__summary-row:last-child .bb-modal__summary-val{color:#4f46e5}
.bb-modal__legal{font-size:0.9rem;color:#64748b;line-height:1.6;margin:1.05rem 0 0;letter-spacing:-0.005em}

.bb-modal__hatch{margin-top:1.7rem;padding-top:1.3rem;border-top:1px solid rgba(15,23,42,0.08)}
.bb-modal__hatch>summary{font-size:0.95rem;font-weight:500;color:#475569;cursor:pointer;list-style:none;display:inline-flex;align-items:center;gap:0.4rem;letter-spacing:-0.005em}
.bb-modal__hatch>summary::-webkit-details-marker{display:none}
.bb-modal__hatch>summary::before{content:"+";font-size:1.05rem;color:#4f46e5;width:1rem;text-align:center;font-weight:600}
.bb-modal__hatch[open]>summary::before{content:"\\2013"}
.bb-modal__hatch>summary:hover{color:#0f172a}
.bb-modal__hatch-grid{display:grid;grid-template-columns:repeat(3,1fr);gap:0.65rem;margin-top:1rem}
@media (max-width:540px){.bb-modal__hatch-grid{grid-template-columns:1fr}}
.bb-modal__hatch-card{display:flex;flex-direction:column;gap:0.3rem;padding:0.95rem 1.05rem;background:#f8fafc;border:1px solid rgba(15,23,42,0.08);border-radius:10px;color:#0f172a;text-decoration:none;transition:border-color .15s ease,background .15s ease}
.bb-modal__hatch-card:hover{background:#eef2ff;border-color:rgba(79,70,229,0.4)}
.bb-modal__hatch-name{font-size:0.95rem;font-weight:600;letter-spacing:-0.005em;color:#0f172a}
.bb-modal__hatch-cta{font-size:0.84rem;color:#4f46e5;font-weight:500;letter-spacing:-0.005em}

.bb-modal__loading{display:none;align-items:center;gap:0.45rem;font-size:0.92rem;color:#475569}
.bb-modal[data-loading="true"] .bb-modal__loading{display:inline-flex}
.bb-modal[data-loading="true"] .bb-modal__btn{opacity:0.5;pointer-events:none}
.bb-modal__spinner{width:14px;height:14px;border-radius:50%;border:2.5px solid rgba(79,70,229,0.25);border-top-color:#4f46e5;animation:bbSpin 0.7s linear infinite}
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
      <p class="bb-modal__sub">All services paid up front. Your Butler will reach out within 4-minutes or less.</p>
      <div class="bb-modal__tiers" role="radiogroup" aria-label="Butler tiers">
        <div class="bb-modal__tier" role="radio" tabindex="0" data-tier-card="trip" aria-checked="false">
          <div class="bb-modal__tier-name">Trip Plan</div>
          <div class="bb-modal__tier-price">$25<span class="bb-modal__tier-unit">one-time</span></div>
          <div class="bb-modal__tier-desc">A real itinerary, written by a Butler who has been there. 24-hour turnaround.</div>
        </div>
        <div class="bb-modal__tier" role="radio" tabindex="0" data-tier-card="8h" data-has-days="true" aria-checked="false">
          <div class="bb-modal__tier-name">8-Hour Butler</div>
          <div class="bb-modal__tier-price">$25<span class="bb-modal__tier-unit">per day</span></div>
          <div class="bb-modal__tier-desc">A live Butler on WhatsApp during your day. Bookings, swaps, recommendations on demand.</div>
          <div class="bb-modal__days">
            <span class="bb-modal__days-label">How many days?</span>
            <button type="button" class="bb-modal__step-btn" data-days-step="-1" aria-label="Decrease days">&minus;</button>
            <span class="bb-modal__days-val" data-days-val>1</span>
            <button type="button" class="bb-modal__step-btn" data-days-step="1" aria-label="Increase days">+</button>
            <span class="bb-modal__days-total" data-days-total>$25</span>
          </div>
        </div>
        <div class="bb-modal__tier" role="radio" tabindex="0" data-tier-card="24h" data-has-days="true" aria-checked="false">
          <div class="bb-modal__tier-name">24-Hour Butler</div>
          <div class="bb-modal__tier-price">$100<span class="bb-modal__tier-unit">per day</span></div>
          <div class="bb-modal__tier-desc">Always-on Butler. 3am gate change? Sorted before you wake up.</div>
          <div class="bb-modal__days">
            <span class="bb-modal__days-label">How many days?</span>
            <button type="button" class="bb-modal__step-btn" data-days-step="-1" aria-label="Decrease days">&minus;</button>
            <span class="bb-modal__days-val" data-days-val>1</span>
            <button type="button" class="bb-modal__step-btn" data-days-step="1" aria-label="Increase days">+</button>
            <span class="bb-modal__days-total" data-days-total>$100</span>
          </div>
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

  var dlg = document.getElementById('bbModal');
  if (!dlg) return;
  // Set flag only after dlg is confirmed in DOM. If the IIFE runs once with
  // dlg=null (e.g. body re-apply race on home), this lets the next applyBody
  // run attach the listener properly instead of returning early forever.
  window._bbModal = true;

  var TIERS = {
    'trip': { name: 'Trip Plan', price: 25, unit: 'one-time', stripe: 'https://buy.stripe.com/fZu6oI8DF2cH7Ij9KP4Ni00' },
    '8h':   { name: '8-Hour Butler', price: 25, unit: 'per day', stripe: 'https://buy.stripe.com/4gM6oI1bd04z6Efg9d4Ni01' },
    '24h':  { name: '24-Hour Butler', price: 100, unit: 'per day', stripe: 'https://buy.stripe.com/14AaEY6vx2cH4w7e154Ni02' }
  };
  var FORMS_URL = 'https://forms.zohopublic.in/VELTM/form/ButlerButtonTripIntake/formperma/__FORMPERMA__/htmlRecords/submit';
  var form = document.getElementById('bbModal__form');
  var summary = document.getElementById('bbModal__summary');
  var DAYS_MIN = 1, DAYS_MAX = 30;
  var state = { step: 1, tier: null, days: 1, intake: {}, refId: null };

  function genRef() {
    return 'bb_' + Date.now().toString(36) + '_' + Math.random().toString(36).slice(2,10);
  }

  function tierHasDays(t) {
    if (!t) return false;
    var c = dlg.querySelector('[data-tier-card="' + t + '"]');
    return !!(c && c.getAttribute('data-has-days') === 'true');
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

  function setDays(n, tier) {
    if (!tier || !TIERS[tier]) return;
    n = Math.max(DAYS_MIN, Math.min(DAYS_MAX, parseInt(n, 10) || 1));
    state.days = n;
    var card = dlg.querySelector('[data-tier-card="' + tier + '"]');
    if (!card) return;
    var v = card.querySelector('[data-days-val]');
    var t = card.querySelector('[data-days-total]');
    if (v) v.textContent = String(n);
    if (t) t.textContent = '$' + (TIERS[tier].price * n);
    var dec = card.querySelector('[data-days-step="-1"]');
    var inc = card.querySelector('[data-days-step="1"]');
    if (dec) dec.disabled = (n <= DAYS_MIN);
    if (inc) inc.disabled = (n >= DAYS_MAX);
  }

  function selectTier(t) {
    state.tier = t;
    dlg.querySelectorAll('.bb-modal__tier').forEach(function(c){
      var matches = c.getAttribute('data-tier-card') === t;
      c.classList.toggle('is-selected', matches);
      c.setAttribute('aria-checked', matches ? 'true' : 'false');
    });
    if (t && tierHasDays(t)) {
      if (!state.days || state.days < 1) state.days = 1;
      setDays(state.days, t);
    } else {
      state.days = 1;
    }
    var nextBtn = dlg.querySelector('[data-step="2"] [data-action="next"]');
    if (nextBtn) nextBtn.disabled = !t;
  }

  function renderSummary() {
    var tier = TIERS[state.tier] || { name: '(none)', price: 0, unit: '' };
    var i = state.intake;
    var hasDays = state.tier && tierHasDays(state.tier);
    var qty = hasDays ? state.days : 1;
    var total = tier.price * qty;
    var tierLabel = tier.name + (hasDays ? ' x ' + qty + ' day' + (qty > 1 ? 's' : '') : '');
    var totalLabel = '$' + total + (hasDays ? ' (' + qty + ' x $' + tier.price + ')' : (tier.unit ? ' ' + tier.unit : ''));
    var rows = [
      ['Name', i.Name || '(provided)'],
      ['Email', i.Email || '(provided)'],
      ['Destination', i.Destination || 'To be confirmed with Butler'],
      ['Dates', i.Dates || 'To be confirmed with Butler'],
      ['Tier', tierLabel],
      ['Total', totalLabel]
    ];
    summary.innerHTML = rows.map(function(r){
      return '<div class="bb-modal__summary-row"><span class="bb-modal__summary-key">' + r[0] + '</span><span class="bb-modal__summary-val">' + String(r[1]).replace(/[<>&"']/g, function(m){return ({'<':'&lt;','>':'&gt;','&':'&amp;','"':'&quot;',"'":'&#39;'})[m];}) + '</span></div>';
    }).join('');
  }

  function openModal(tier) {
    state.tier = null;
    state.days = 1;
    state.intake = {};
    state.refId = genRef();
    if (form) form.reset();
    dlg.querySelectorAll('.bb-modal__row').forEach(function(r){ r.classList.remove('has-error'); });
    dlg.querySelectorAll('.bb-modal__skip input').forEach(function(c){ c.checked = false; });
    dlg.querySelectorAll('[data-skip]').forEach(function(c){
      var input = document.getElementById(c.getAttribute('data-skip'));
      if (input) { input.disabled = false; input.value = ''; }
    });
    dlg.querySelectorAll('[data-tier-card][data-has-days="true"]').forEach(function(card){
      var tk = card.getAttribute('data-tier-card');
      if (TIERS[tk]) {
        var v = card.querySelector('[data-days-val]');
        var tot = card.querySelector('[data-days-total]');
        if (v) v.textContent = '1';
        if (tot) tot.textContent = '$' + TIERS[tk].price;
        var dec = card.querySelector('[data-days-step="-1"]');
        if (dec) dec.disabled = true;
        var inc = card.querySelector('[data-days-step="1"]');
        if (inc) inc.disabled = false;
      }
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
    // Refresh dlg/form/summary references — applyBody can re-mount the dialog
    // (Zoho takeover recovery), which would orphan the closure-captured nodes.
    var freshDlg = document.getElementById('bbModal');
    if (freshDlg && freshDlg !== dlg) {
      dlg = freshDlg;
      form = document.getElementById('bbModal__form');
      summary = document.getElementById('bbModal__summary');
    }
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
    var stepBtn = e.target.closest('[data-days-step]');
    if (stepBtn) {
      e.preventDefault();
      e.stopPropagation();
      var stepCard = stepBtn.closest('[data-tier-card]');
      if (!stepCard) return;
      var stepTier = stepCard.getAttribute('data-tier-card');
      if (state.tier !== stepTier) selectTier(stepTier);
      var delta = parseInt(stepBtn.getAttribute('data-days-step'), 10) || 0;
      setDays((state.days || 1) + delta, stepTier);
      return;
    }
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

  // Delegate change to document so the listener survives applyBody re-mount.
  // (Binding to dlg captured the original node; Zoho takeover recovery
  // re-renders the dialog and orphans element-bound listeners.)
  document.addEventListener('change', function(e){
    if (!e.target || !e.target.closest) return;
    var inDlg = e.target.closest('#bbModal');
    if (!inDlg) return;
    var skip = e.target.closest('.bb-modal__skip input[data-skip]');
    if (!skip) return;
    var input = document.getElementById(skip.getAttribute('data-skip'));
    if (!input) return;
    if (skip.checked) { input.value = ''; input.disabled = true; }
    else { input.disabled = false; input.focus(); }
  });

  // Delegate submit to document for the SAME REASON. Binding to the form
  // node leaves the listener orphaned when applyBody re-mounts the form,
  // letting the native form submit fire and navigate the page (which is
  // what made the modal disappear on Continue).
  document.addEventListener('submit', function(e){
    if (!e.target || e.target.id !== 'bbModal__form') return;
    e.preventDefault();
    var liveForm = e.target;
    // Refresh closure-captured form so downstream code sees the live node.
    form = liveForm;
    var name = liveForm.querySelector('#bbm-name');
    var email = liveForm.querySelector('#bbm-email');
    var ok = true;
    [name, email].forEach(function(inp){
      var row = inp.closest('.bb-modal__row');
      var valid = inp.value.trim().length > 0 && (inp.type !== 'email' || /^[^@\\s]+@[^@\\s]+\\.[^@\\s]+$/.test(inp.value.trim()));
      row.classList.toggle('has-error', !valid);
      if (!valid) ok = false;
    });
    if (!ok) { var firstBad = liveForm.querySelector('.has-error .bb-modal__input'); if (firstBad) firstBad.focus(); return; }
    state.intake = {
      Name: name.value.trim(),
      Email: email.value.trim(),
      Destination: liveForm.querySelector('#bbm-dest').value.trim(),
      Dates: liveForm.querySelector('#bbm-dates').value.trim(),
      PartySize: liveForm.querySelector('#bbm-party').value.trim(),
      Brief: liveForm.querySelector('#bbm-brief').value.trim()
    };
    showStep(2);
  });

  function doCheckout() {
    if (!state.tier || !TIERS[state.tier]) return;
    dlg.setAttribute('data-loading','true');
    var hasDays = tierHasDays(state.tier);
    var qty = hasDays ? (state.days || 1) : 1;
    var refWithDays = state.refId + '_d' + qty;
    var payload = Object.assign({}, state.intake, {
      Tier: state.tier,
      Days: qty,
      ClientReferenceId: refWithDays,
      OriginPage: location.pathname
    });
    var fd = new FormData();
    Object.keys(payload).forEach(function(k){ fd.append(k, payload[k] || ''); });
    var doneCount = 0;
    var redirect = function() {
      var stripeURL = TIERS[state.tier].stripe
        + '?prefilled_email=' + encodeURIComponent(state.intake.Email || '')
        + '&client_reference_id=' + encodeURIComponent(refWithDays);
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
