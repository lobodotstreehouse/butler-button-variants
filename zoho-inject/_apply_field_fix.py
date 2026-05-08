#!/usr/bin/env python3
"""
Patch doCheckout() in _modal-snippet.js and all inject-*-v3.js files so the
POST body matches the butler-booking-api Edge Function contract.

  - tier            -> service_type
  - name            -> customer_name
  - email           -> customer_email
  - destination     -> country_names (parsed)
  - party_size      -> number_of_pax
  - brief           -> trip_purpose
  - dates+brief+ref -> special_requirements
  - adds date_flexibility:'tentative' + tentative_days for 8hrs/24hrs validation

Idempotent: skips files whose doCheckout already contains 'service_type:'.
"""
import pathlib

ROOT = pathlib.Path(__file__).parent
FILES = [
    ROOT / "_modal-snippet.js",
    ROOT / "inject-home-v3.js",
    ROOT / "inject-advisor-v3.js",
    ROOT / "inject-concierge-v3.js",
    ROOT / "inject-trip-planning-v3.js",
    ROOT / "inject-supplier-code-v3.js",
]

OLD_BLOCK = """  function doCheckout() {
    if (!state.tier || !TIERS[state.tier]) return;
    var tierCfg = TIERS[state.tier];
    dlg.setAttribute('data-loading','true');
    var hasDays = tierHasDays(state.tier);
    var qty = hasDays ? (state.days || 1) : 1;
    var refWithDays = state.refId + '_d' + qty;
    var i = state.intake;

    var body = {
      tier: tierCfg.api,
      days: qty,
      name: i.Name || '',
      email: i.Email || '',
      destination: i.Destination || '',
      dates: i.Dates || '',
      party_size: i.PartySize || '',
      brief: i.Brief || '',
      client_reference_id: refWithDays,
      origin_page: location.pathname
    };

    var clearLoading = function(){ dlg.removeAttribute('data-loading'); };

    fetch(API_CFG.url, {
      method: 'POST',
      headers: {
        'Content-Type': 'application/json',
        'apikey': API_CFG.anon,
        'Authorization': 'Bearer ' + API_CFG.anon
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
        clearLoading();
        try { console.error('[bb-modal] checkout error', err); } catch(e){}
        var msg = (err && err.message) ? err.message : 'Something went wrong.';
        alert('Sorry \\u2014 we could not start checkout: ' + msg + '\\n\\nPlease WhatsApp us so we can sort it: +1 855 503 1555');
      });
  }"""

NEW_BLOCK = """  // Best-effort split of free-text destination into country tokens.
  // The Edge Function looks each name up in virtual_executive_countries
  // (exact match, is_active=true). If the user types cities ("Tokyo, Kyoto")
  // the lookup will fail and the server returns a clear 400 we surface below.
  function parseCountries(s) {
    if (!s) return [];
    return s.split(/\\s*(?:,|\\/|&|\\bthen\\b|\\band\\b|\\bor\\b)\\s*/i)
      .map(function(t){ return t.trim().replace(/^the\\s+/i, ''); })
      .filter(function(t){ return t.length > 1 && t.length < 60; });
  }

  function doCheckout() {
    if (!state.tier || !TIERS[state.tier]) return;
    var tierCfg = TIERS[state.tier];
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
      service_type: tierCfg.api,
      customer_name: i.Name || '',
      customer_email: i.Email || '',
      country_names: countryNames,
      number_of_pax: (partyNum > 0 ? partyNum : 1),
      trip_purpose: i.Brief || '',
      special_requirements:
        (i.Dates ? 'Dates/notes: ' + i.Dates + '\\n' : '') +
        (i.Brief ? i.Brief + '\\n' : '') +
        '[ref ' + refWithDays + ' from butlerbutton.co' +
        (location.pathname ? ' ' + location.pathname : '') + ']',
      date_flexibility: 'tentative',
      tentative_days: qty,
      source: 'butlerbutton.co'
    };

    var clearLoading = function(){ dlg.removeAttribute('data-loading'); };

    fetch(API_CFG.url, {
      method: 'POST',
      headers: {
        'Content-Type': 'application/json',
        'apikey': API_CFG.anon,
        'Authorization': 'Bearer ' + API_CFG.anon
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
        clearLoading();
        try { console.error('[bb-modal] checkout error', err); } catch(e){}
        var msg = (err && err.message) ? err.message : 'Something went wrong.';
        alert('Sorry \\u2014 we could not start checkout: ' + msg + '\\n\\nPlease WhatsApp us so we can sort it: +1 855 503 1555');
      });
  }"""


def main():
    for f in FILES:
        text = f.read_text()
        if "service_type: tierCfg.api" in text:
            print(f"SKIP (already patched): {f.name}")
            continue
        if OLD_BLOCK not in text:
            print(f"FAIL (old block not found): {f.name}")
            continue
        n = text.count(OLD_BLOCK)
        if n != 1:
            print(f"FAIL (block found {n} times, expected 1): {f.name}")
            continue
        f.write_text(text.replace(OLD_BLOCK, NEW_BLOCK))
        print(f"OK: {f.name}")


if __name__ == "__main__":
    main()
