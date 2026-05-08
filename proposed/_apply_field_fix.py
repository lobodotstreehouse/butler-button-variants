#!/usr/bin/env python3
"""Replace static-Stripe-link doCheckout in proposed/*.html with an
Edge-Function-backed version matching production (zoho-inject/_modal-snippet.js).
"""
import pathlib

ROOT = pathlib.Path(__file__).parent
FILES = [
    ROOT / "home.html",
    ROOT / "concierge.html",
    ROOT / "travel-advisor.html",
    ROOT / "trip-planning.html",
    ROOT / "supplier-code.html",
]

OLD = """  function doCheckout() {
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
  }"""

NEW = """  // Edge Function endpoint (matches zoho-inject/_modal-snippet.js).
  var BB_API = window.BB_API || {
    url:  'https://glhbwpfkykycexyygwjj.supabase.co/functions/v1/butler-booking-api',
    anon: 'eyJhbGciOiJIUzI1NiIsInR5cCI6IkpXVCJ9.eyJpc3MiOiJzdXBhYmFzZSIsInJlZiI6ImdsaGJ3cGZreWt5Y2V4eXlnd2pqIiwicm9sZSI6ImFub24iLCJpYXQiOjE3NDM5NDYzMTcsImV4cCI6MjA1OTUyMjMxN30.k1acAq6Khe47kwZThROWypCfj-S4-zTVIBFOxy86DFU'
  };
  var TIER_API = { 'trip':'trip_planning', '8h':'8hrs', '24h':'24hrs' };

  function parseCountries(s) {
    if (!s) return [];
    return s.split(/\\s*(?:,|\\/|&|\\bthen\\b|\\band\\b|\\bor\\b)\\s*/i)
      .map(function(t){ return t.trim().replace(/^the\\s+/i, ''); })
      .filter(function(t){ return t.length > 1 && t.length < 60; });
  }

  function doCheckout() {
    if (!state.tier || !TIERS[state.tier]) return;
    var hasDays = tierHasDays(state.tier);
    var qty = hasDays ? (state.days || 1) : 1;
    var refWithDays = state.refId + '_d' + qty;
    var i = state.intake;

    var countryNames = parseCountries(i.Destination || '');
    if (!countryNames.length) {
      alert('Please add the country (or countries) for your trip in the destination field \\u2014 e.g. \"Japan\" or \"Italy, France\".');
      showStep(1);
      var dest = document.getElementById('bbm-dest');
      if (dest) {
        dest.focus();
        var row = dest.closest('.bb-modal__row');
        if (row) row.classList.add('has-error');
      }
      return;
    }

    dlg.setAttribute('data-loading','true');
    var partyNum = parseInt(i.PartySize, 10);

    var body = {
      service_type: TIER_API[state.tier],
      customer_name: i.Name || '',
      customer_email: i.Email || '',
      country_names: countryNames,
      number_of_pax: (partyNum > 0 ? partyNum : 1),
      trip_purpose: i.Brief || '',
      special_requirements:
        (i.Dates ? 'Dates/notes: ' + i.Dates + '\\n' : '') +
        (i.Brief ? i.Brief + '\\n' : '') +
        '[ref ' + refWithDays + ' from ' + location.host + location.pathname + ']',
      date_flexibility: 'tentative',
      tentative_days: qty,
      source: 'butlerbutton.co (proposed preview)'
    };

    fetch(BB_API.url, {
      method: 'POST',
      headers: {
        'Content-Type': 'application/json',
        'apikey': BB_API.anon,
        'Authorization': 'Bearer ' + BB_API.anon
      },
      body: JSON.stringify(body)
    })
      .then(function(res){
        return res.json().then(function(data){ return { ok: res.ok, data: data }; });
      })
      .then(function(r){
        if (!r.ok || !r.data || !r.data.success || !r.data.checkout_url) {
          throw new Error((r.data && (r.data.error || r.data.message)) || 'Booking failed');
        }
        window.location.assign(r.data.checkout_url);
      })
      .catch(function(err){
        dlg.removeAttribute('data-loading');
        try { console.error('[bb-modal] checkout error', err); } catch(e){}
        var msg = (err && err.message) ? err.message : 'Something went wrong.';
        alert('Sorry \\u2014 we could not start checkout: ' + msg);
      });
  }"""


def main():
    for f in FILES:
        text = f.read_text()
        if "BB_API" in text and "service_type: TIER_API" in text:
            print(f"SKIP (already patched): {f.name}")
            continue
        if OLD not in text:
            print(f"FAIL (old block not found): {f.name}")
            continue
        f.write_text(text.replace(OLD, NEW))
        print(f"OK: {f.name}")


if __name__ == "__main__":
    main()
