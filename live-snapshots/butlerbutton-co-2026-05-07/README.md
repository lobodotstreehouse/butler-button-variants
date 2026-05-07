# Live butlerbutton.co snapshot — 2026-05-07

This directory captures the state of `https://www.butlerbutton.co/` immediately before the v3 cutover from `inject-*-v2.js` to `inject-*-v3.js`.

## Files

| File | What it is |
|------|------------|
| `HEADER_IIFE.js` | The routing IIFE that was live in the Zoho Sites header. Use the `LIVE_HEADER` string verbatim to roll back. |
| `home.html` | Unauthenticated curl of `/` |
| `trip-planning.html` | Unauthenticated curl of `/trip-planning` |
| `concierge.html` | Unauthenticated curl of `/concierge` |
| `travel-advisor.html` | Unauthenticated curl of `/travel-advisor` |
| `supplier-code.html` | Unauthenticated curl of `/supplier-code` |

## Why a snapshot

Carl asked to keep the live state recoverable before pushing v3. Zoho Sites does not retain header-code revision history through the API, so the only durable backup is this file. If the v3 cutover misbehaves, paste `LIVE_HEADER` from `HEADER_IIFE.js` into the Zoho header-code editor and publish.

## What is NOT in here

- Native Zoho page-body markup (irrelevant; the inject scripts replace `document.body.innerHTML` on every page load, so whatever is in the Zoho page editor is unused).
- SEO fields (title / description per page). These were not modified in the cutover and remain whatever Zoho stores natively.
- Custom CSS in the Zoho Site (the flash-fix CSS documented in `project_zoho_injection_technique.md`). Untouched by the cutover.

## Cutover diff

Before (v2):
```
""  or "/index"      -> inject-home-v2.js?v=18
"/trip-planning"     -> inject-trip-planning-v2.js?v=18
"/concierge"         -> inject-concierge-v2.js?v=18
"/travel-advisor"    -> inject-advisor-v2.js?v=18
"/supplier-code"     -> inject-supplier-code.js?v=16
```

After (v3):
```
""  or "/index"      -> inject-home-v3.js?v=1
"/trip-planning"     -> inject-trip-planning-v3.js?v=1
"/concierge"         -> inject-concierge-v3.js?v=1
"/travel-advisor"    -> inject-advisor-v3.js?v=1
"/supplier-code"     -> inject-supplier-code-v3.js?v=1
```
