#!/usr/bin/env python3
"""Patch the 5 v3 inject scripts with the days-stepper feature from _modal-snippet.js."""

import re
import os

BASE = '/Users/openclaw/butler-button-variants/zoho-inject'

FILES = [
    'inject-home-v3.js',
    'inject-trip-planning-v3.js',
    'inject-concierge-v3.js',
    'inject-advisor-v3.js',
    'inject-supplier-code-v3.js',
]

# ------- CSS: 9 new rules inserted after .bb-modal__tier-desc line -------
CSS_ANCHOR = '.bb-modal__tier-desc{font-size:0.9rem;color:rgba(255,255,255,0.62);line-height:1.5;letter-spacing:-0.005em;grid-column:1 / -1;margin-top:0.15rem}'

# The new CSS rules to insert (no leading indent - will be prefixed by whatever
# indent the anchor line has)
NEW_CSS_RULES = [
    '.bb-modal__days{display:none;flex-wrap:wrap;align-items:center;gap:0.55rem;margin-top:0.85rem;grid-column:1 / -1;padding-top:0.85rem;border-top:1px dashed rgba(255,255,255,0.08)}',
    '.bb-modal__tier.is-selected[data-has-days="true"] .bb-modal__days{display:flex}',
    '.bb-modal__days-label{font-size:0.82rem;color:rgba(255,255,255,0.62);letter-spacing:-0.005em;margin-right:auto}',
    '.bb-modal__step-btn{appearance:none;border:1px solid rgba(255,255,255,0.15);background:rgba(255,255,255,0.04);color:#fff;width:30px;height:30px;border-radius:8px;font-size:1.05rem;cursor:pointer;display:inline-flex;align-items:center;justify-content:center;line-height:1;transition:background .15s ease,border-color .15s ease}',
    '.bb-modal__step-btn:hover{background:rgba(255,255,255,0.08);border-color:rgba(165,180,252,0.4)}',
    '.bb-modal__step-btn:disabled{opacity:0.35;cursor:not-allowed}',
    '.bb-modal__days-val{min-width:2.5ch;text-align:center;font-weight:600;color:#fff;font-size:1rem}',
    '.bb-modal__days-total{font-size:0.86rem;color:#a5b4fc;font-weight:500;letter-spacing:-0.005em;margin-left:0.4rem}',
]

# ------- HTML: 8h and 24h tier cards -------
# Old 8h card (no data-has-days, no days block)
OLD_8H = (
    '        <div class="bb-modal__tier" role="radio" tabindex="0" data-tier-card="8h" aria-checked="false">\n'
    '          <div class="bb-modal__tier-name">8-Hour Butler</div>\n'
    '          <div class="bb-modal__tier-price">$25<span class="bb-modal__tier-unit">per day</span></div>\n'
    '          <div class="bb-modal__tier-desc">A live Butler on WhatsApp during your day. Bookings, swaps, recommendations on demand.</div>\n'
    '        </div>'
)
NEW_8H = (
    '        <div class="bb-modal__tier" role="radio" tabindex="0" data-tier-card="8h" data-has-days="true" aria-checked="false">\n'
    '          <div class="bb-modal__tier-name">8-Hour Butler</div>\n'
    '          <div class="bb-modal__tier-price">$25<span class="bb-modal__tier-unit">per day</span></div>\n'
    '          <div class="bb-modal__tier-desc">A live Butler on WhatsApp during your day. Bookings, swaps, recommendations on demand.</div>\n'
    '          <div class="bb-modal__days">\n'
    '            <span class="bb-modal__days-label">How many days?</span>\n'
    '            <button type="button" class="bb-modal__step-btn" data-days-step="-1" aria-label="Decrease days">&minus;</button>\n'
    '            <span class="bb-modal__days-val" data-days-val>1</span>\n'
    '            <button type="button" class="bb-modal__step-btn" data-days-step="1" aria-label="Increase days">+</button>\n'
    '            <span class="bb-modal__days-total" data-days-total>$25</span>\n'
    '          </div>\n'
    '        </div>'
)

OLD_24H = (
    '        <div class="bb-modal__tier" role="radio" tabindex="0" data-tier-card="24h" aria-checked="false">\n'
    '          <div class="bb-modal__tier-name">24-Hour Butler</div>\n'
    '          <div class="bb-modal__tier-price">$100<span class="bb-modal__tier-unit">per day</span></div>\n'
    '          <div class="bb-modal__tier-desc">Always-on Butler. 3am gate change? Sorted before you wake up.</div>\n'
    '        </div>'
)
NEW_24H = (
    '        <div class="bb-modal__tier" role="radio" tabindex="0" data-tier-card="24h" data-has-days="true" aria-checked="false">\n'
    '          <div class="bb-modal__tier-name">24-Hour Butler</div>\n'
    '          <div class="bb-modal__tier-price">$100<span class="bb-modal__tier-unit">per day</span></div>\n'
    '          <div class="bb-modal__tier-desc">Always-on Butler. 3am gate change? Sorted before you wake up.</div>\n'
    '          <div class="bb-modal__days">\n'
    '            <span class="bb-modal__days-label">How many days?</span>\n'
    '            <button type="button" class="bb-modal__step-btn" data-days-step="-1" aria-label="Decrease days">&minus;</button>\n'
    '            <span class="bb-modal__days-val" data-days-val>1</span>\n'
    '            <button type="button" class="bb-modal__step-btn" data-days-step="1" aria-label="Increase days">+</button>\n'
    '            <span class="bb-modal__days-total" data-days-total>$100</span>\n'
    '          </div>\n'
    '        </div>'
)

# ------- Handler changes -------
# 1. state: add days:1
OLD_STATE = "var state = { step: 1, tier: null, intake: {}, refId: null };"
NEW_STATE = "var state = { step: 1, tier: null, days: 1, intake: {}, refId: null };"

# 2. After genRef function, insert DAYS_MIN, DAYS_MAX, tierHasDays, setDays
# Anchor: the genRef function block
OLD_AFTER_GENREF = (
    "  function genRef() {\n"
    "    return 'bb_' + Date.now().toString(36) + '_' + Math.random().toString(36).slice(2,10);\n"
    "  }\n"
    "\n"
    "  function showStep(n) {"
)
NEW_AFTER_GENREF = (
    "  function genRef() {\n"
    "    return 'bb_' + Date.now().toString(36) + '_' + Math.random().toString(36).slice(2,10);\n"
    "  }\n"
    "\n"
    "  var DAYS_MIN = 1, DAYS_MAX = 30;\n"
    "\n"
    "  function tierHasDays(t) {\n"
    "    if (!t) return false;\n"
    "    var c = dlg.querySelector('[data-tier-card=\"' + t + '\"]');\n"
    "    return !!(c && c.getAttribute('data-has-days') === 'true');\n"
    "  }\n"
    "\n"
    "  function setDays(n, tier) {\n"
    "    if (!tier || !TIERS[tier]) return;\n"
    "    n = Math.max(DAYS_MIN, Math.min(DAYS_MAX, parseInt(n, 10) || 1));\n"
    "    state.days = n;\n"
    "    var card = dlg.querySelector('[data-tier-card=\"' + tier + '\"]');\n"
    "    if (!card) return;\n"
    "    var v = card.querySelector('[data-days-val]');\n"
    "    var t = card.querySelector('[data-days-total]');\n"
    "    if (v) v.textContent = String(n);\n"
    "    if (t) t.textContent = '$' + (TIERS[tier].price * n);\n"
    "    var dec = card.querySelector('[data-days-step=\"-1\"]');\n"
    "    var inc = card.querySelector('[data-days-step=\"1\"]');\n"
    "    if (dec) dec.disabled = (n <= DAYS_MIN);\n"
    "    if (inc) inc.disabled = (n >= DAYS_MAX);\n"
    "  }\n"
    "\n"
    "  function showStep(n) {"
)

# 3. selectTier: add days logic
OLD_SELECT_TIER = (
    "  function selectTier(t) {\n"
    "    state.tier = t;\n"
    "    dlg.querySelectorAll('.bb-modal__tier').forEach(function(c){\n"
    "      var matches = c.getAttribute('data-tier-card') === t;\n"
    "      c.classList.toggle('is-selected', matches);\n"
    "      c.setAttribute('aria-checked', matches ? 'true' : 'false');\n"
    "    });\n"
    "    var nextBtn = dlg.querySelector('[data-step=\"2\"] [data-action=\"next\"]');\n"
    "    if (nextBtn) nextBtn.disabled = !t;\n"
    "  }"
)
NEW_SELECT_TIER = (
    "  function selectTier(t) {\n"
    "    state.tier = t;\n"
    "    dlg.querySelectorAll('.bb-modal__tier').forEach(function(c){\n"
    "      var matches = c.getAttribute('data-tier-card') === t;\n"
    "      c.classList.toggle('is-selected', matches);\n"
    "      c.setAttribute('aria-checked', matches ? 'true' : 'false');\n"
    "    });\n"
    "    if (t && tierHasDays(t)) {\n"
    "      if (!state.days || state.days < 1) state.days = 1;\n"
    "      setDays(state.days, t);\n"
    "    } else {\n"
    "      state.days = 1;\n"
    "    }\n"
    "    var nextBtn = dlg.querySelector('[data-step=\"2\"] [data-action=\"next\"]');\n"
    "    if (nextBtn) nextBtn.disabled = !t;\n"
    "  }"
)

# 4. renderSummary: update to show days
OLD_RENDER_SUMMARY = (
    "  function renderSummary() {\n"
    "    var tier = TIERS[state.tier] || { name: '(none)', price: 0, unit: '' };\n"
    "    var i = state.intake;\n"
    "    var rows = [\n"
    "      ['Name', i.Name || '(provided)'],\n"
    "      ['Email', i.Email || '(provided)'],\n"
    "      ['Destination', i.Destination || 'To be confirmed with Butler'],\n"
    "      ['Dates', i.Dates || 'To be confirmed with Butler'],\n"
    "      ['Tier', tier.name],\n"
    "      ['Total', '$' + tier.price + (tier.unit ? ' ' + tier.unit : '')]\n"
    "    ];\n"
    "    summary.innerHTML = rows.map(function(r){\n"
    "      return '<div class=\"bb-modal__summary-row\"><span class=\"bb-modal__summary-key\">' + r[0] + '</span><span class=\"bb-modal__summary-val\">' + String(r[1]).replace(/[<>&\"']/g, function(m){return ({'<':'&lt;','>':'&gt;','&':'&amp;','\"':'&quot;',\"'\":'&#39;'})[m];}) + '</span></div>';\n"
    "    }).join('');\n"
    "  }"
)
NEW_RENDER_SUMMARY = (
    "  function renderSummary() {\n"
    "    var tier = TIERS[state.tier] || { name: '(none)', price: 0, unit: '' };\n"
    "    var i = state.intake;\n"
    "    var hasDays = state.tier && tierHasDays(state.tier);\n"
    "    var qty = hasDays ? state.days : 1;\n"
    "    var total = tier.price * qty;\n"
    "    var tierLabel = tier.name + (hasDays ? ' x ' + qty + ' day' + (qty > 1 ? 's' : '') : '');\n"
    "    var totalLabel = '$' + total + (hasDays ? ' (' + qty + ' x $' + tier.price + ')' : (tier.unit ? ' ' + tier.unit : ''));\n"
    "    var rows = [\n"
    "      ['Name', i.Name || '(provided)'],\n"
    "      ['Email', i.Email || '(provided)'],\n"
    "      ['Destination', i.Destination || 'To be confirmed with Butler'],\n"
    "      ['Dates', i.Dates || 'To be confirmed with Butler'],\n"
    "      ['Tier', tierLabel],\n"
    "      ['Total', totalLabel]\n"
    "    ];\n"
    "    summary.innerHTML = rows.map(function(r){\n"
    "      return '<div class=\"bb-modal__summary-row\"><span class=\"bb-modal__summary-key\">' + r[0] + '</span><span class=\"bb-modal__summary-val\">' + String(r[1]).replace(/[<>&\"']/g, function(m){return ({'<':'&lt;','>':'&gt;','&':'&amp;','\"':'&quot;',\"'\":'&#39;'})[m];}) + '</span></div>';\n"
    "    }).join('');\n"
    "  }"
)

# 5. openModal: add reset of all card days values
OLD_OPEN_MODAL_RESET = (
    "    dlg.querySelectorAll('[data-skip]').forEach(function(c){\n"
    "      var input = document.getElementById(c.getAttribute('data-skip'));\n"
    "      if (input) { input.disabled = false; input.value = ''; }\n"
    "    });\n"
    "    selectTier(tier && TIERS[tier] ? tier : null);"
)
NEW_OPEN_MODAL_RESET = (
    "    dlg.querySelectorAll('[data-skip]').forEach(function(c){\n"
    "      var input = document.getElementById(c.getAttribute('data-skip'));\n"
    "      if (input) { input.disabled = false; input.value = ''; }\n"
    "    });\n"
    "    dlg.querySelectorAll('[data-tier-card][data-has-days=\"true\"]').forEach(function(card){\n"
    "      var tk = card.getAttribute('data-tier-card');\n"
    "      if (TIERS[tk]) {\n"
    "        var v = card.querySelector('[data-days-val]');\n"
    "        var tot = card.querySelector('[data-days-total]');\n"
    "        if (v) v.textContent = '1';\n"
    "        if (tot) tot.textContent = '$' + TIERS[tk].price;\n"
    "        var dec = card.querySelector('[data-days-step=\"-1\"]');\n"
    "        if (dec) dec.disabled = true;\n"
    "        var inc = card.querySelector('[data-days-step=\"1\"]');\n"
    "        if (inc) inc.disabled = false;\n"
    "      }\n"
    "    });\n"
    "    selectTier(tier && TIERS[tier] ? tier : null);"
)

# 6. click handler: add [data-days-step] routing BEFORE [data-tier-card]
OLD_CLICK_NEXT = (
    "    var next = e.target.closest('[data-action=\"next\"]');\n"
    "    if (next) { e.preventDefault(); if (state.tier) { renderSummary(); showStep(3); } return; }\n"
    "    var card = e.target.closest('[data-tier-card]');"
)
NEW_CLICK_NEXT = (
    "    var next = e.target.closest('[data-action=\"next\"]');\n"
    "    if (next) { e.preventDefault(); if (state.tier) { renderSummary(); showStep(3); } return; }\n"
    "    var stepBtn = e.target.closest('[data-days-step]');\n"
    "    if (stepBtn) {\n"
    "      e.preventDefault();\n"
    "      e.stopPropagation();\n"
    "      var stepCard = stepBtn.closest('[data-tier-card]');\n"
    "      if (!stepCard) return;\n"
    "      var stepTier = stepCard.getAttribute('data-tier-card');\n"
    "      if (state.tier !== stepTier) selectTier(stepTier);\n"
    "      var delta = parseInt(stepBtn.getAttribute('data-days-step'), 10) || 0;\n"
    "      setDays((state.days || 1) + delta, stepTier);\n"
    "      return;\n"
    "    }\n"
    "    var card = e.target.closest('[data-tier-card]');"
)

# 7. doCheckout: add refWithDays and Days in payload
OLD_DO_CHECKOUT = (
    "  function doCheckout() {\n"
    "    if (!state.tier || !TIERS[state.tier]) return;\n"
    "    dlg.setAttribute('data-loading','true');\n"
    "    var payload = Object.assign({}, state.intake, {\n"
    "      Tier: state.tier,\n"
    "      ClientReferenceId: state.refId,\n"
    "      OriginPage: location.pathname\n"
    "    });\n"
    "    var fd = new FormData();\n"
    "    Object.keys(payload).forEach(function(k){ fd.append(k, payload[k] || ''); });\n"
    "    var doneCount = 0;\n"
    "    var redirect = function() {\n"
    "      var stripeURL = TIERS[state.tier].stripe\n"
    "        + '?prefilled_email=' + encodeURIComponent(state.intake.Email || '')\n"
    "        + '&client_reference_id=' + encodeURIComponent(state.refId);\n"
    "      window.location.assign(stripeURL);\n"
    "    };"
)
NEW_DO_CHECKOUT = (
    "  function doCheckout() {\n"
    "    if (!state.tier || !TIERS[state.tier]) return;\n"
    "    dlg.setAttribute('data-loading','true');\n"
    "    var hasDays = tierHasDays(state.tier);\n"
    "    var qty = hasDays ? (state.days || 1) : 1;\n"
    "    var refWithDays = state.refId + '_d' + qty;\n"
    "    var payload = Object.assign({}, state.intake, {\n"
    "      Tier: state.tier,\n"
    "      Days: qty,\n"
    "      ClientReferenceId: refWithDays,\n"
    "      OriginPage: location.pathname\n"
    "    });\n"
    "    var fd = new FormData();\n"
    "    Object.keys(payload).forEach(function(k){ fd.append(k, payload[k] || ''); });\n"
    "    var doneCount = 0;\n"
    "    var redirect = function() {\n"
    "      var stripeURL = TIERS[state.tier].stripe\n"
    "        + '?prefilled_email=' + encodeURIComponent(state.intake.Email || '')\n"
    "        + '&client_reference_id=' + encodeURIComponent(refWithDays);\n"
    "      window.location.assign(stripeURL);\n"
    "    };"
)

def apply_css_patch(content, anchor, new_rules):
    """Insert new CSS rules after the anchor line, matching its indentation."""
    lines = content.split('\n')
    result = []
    for line in lines:
        result.append(line)
        stripped = line.lstrip()
        if stripped == anchor:
            # detect indentation of the anchor line
            indent = line[:len(line) - len(stripped)]
            for rule in new_rules:
                result.append(indent + rule)
    return '\n'.join(result)

def replace_once(content, old, new, label):
    count = content.count(old)
    if count == 0:
        raise ValueError(f"Pattern not found: {label}")
    if count > 1:
        raise ValueError(f"Pattern found {count} times (expected 1): {label}")
    return content.replace(old, new)

# 8. openModal top: add state.days = 1 reset
OLD_OPEN_MODAL_TOP = (
    "  function openModal(tier) {\n"
    "    state.tier = null;\n"
    "    state.intake = {};\n"
    "    state.refId = genRef();"
)
NEW_OPEN_MODAL_TOP = (
    "  function openModal(tier) {\n"
    "    state.tier = null;\n"
    "    state.days = 1;\n"
    "    state.intake = {};\n"
    "    state.refId = genRef();"
)

PATCHES = [
    (OLD_STATE, NEW_STATE, 'state declaration'),
    (OLD_OPEN_MODAL_TOP, NEW_OPEN_MODAL_TOP, 'openModal top state.days reset'),
    (OLD_AFTER_GENREF, NEW_AFTER_GENREF, 'genRef + insert DAYS_MIN/tierHasDays/setDays'),
    (OLD_SELECT_TIER, NEW_SELECT_TIER, 'selectTier'),
    (OLD_RENDER_SUMMARY, NEW_RENDER_SUMMARY, 'renderSummary'),
    (OLD_OPEN_MODAL_RESET, NEW_OPEN_MODAL_RESET, 'openModal reset'),
    (OLD_CLICK_NEXT, NEW_CLICK_NEXT, 'click handler days-step routing'),
    (OLD_DO_CHECKOUT, NEW_DO_CHECKOUT, 'doCheckout'),
    (OLD_8H, NEW_8H, '8h HTML card'),
    (OLD_24H, NEW_24H, '24h HTML card'),
]

for fname in FILES:
    fpath = os.path.join(BASE, fname)
    with open(fpath, 'r') as f:
        content = f.read()

    # CSS patch
    content = apply_css_patch(content, CSS_ANCHOR, NEW_CSS_RULES)

    # All other string patches
    for old, new, label in PATCHES:
        content = replace_once(content, old, new, label + f' in {fname}')

    with open(fpath, 'w') as f:
        f.write(content)

    print(f"Patched: {fname}")

print("All done.")
