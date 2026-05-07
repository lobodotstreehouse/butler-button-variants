// =============================================================================
// LIVE HEADER IIFE — www.butlerbutton.co
// Captured: 2026-05-07 (UTC)
// Source: unauthenticated curl of https://www.butlerbutton.co/
// Live commit on GH Pages at time of capture: butler-button-variants @ a783dd2
//
// This is the routing IIFE that was live in the Zoho Sites header
// (Zoho Site ID 413198000000002010, sitebuilder-60059075182) immediately
// before the v3 cutover. Use this verbatim string to roll back if the v3
// deploy needs to be reverted.
//
// Roll-back recipe (single API call from the editor tab console):
//   $X.post({
//     url: '/zs-site/api/v1/sites/413198000000002010/headerfootercode',
//     headers: app.getHeaders(),
//     bodyJSON: { snippet: { headercode: <<the string in LIVE_HEADER below>>, footercode: '' } }
//   });
// then publish:
//   $X.post({ url: '/zs-site/api/v1/publish', headers: app.getHeaders(), bodyJSON: {} });
// =============================================================================

const LIVE_HEADER = `<script>(function(){var x=location.pathname.replace(/\\/+$/,"");var s=document.createElement("script");var b="https://lobodotstreehouse.github.io/butler-button-variants/zoho-inject/";if(x===""||x==="/index"){s.src=b+"inject-home-v2.js?v=18";}else if(x==="/trip-planning"){s.src=b+"inject-trip-planning-v2.js?v=18";}else if(x==="/concierge"){s.src=b+"inject-concierge-v2.js?v=18";}else if(x==="/travel-advisor"){s.src=b+"inject-advisor-v2.js?v=18";}else if(x==="/supplier-code"){s.src=b+"inject-supplier-code.js?v=16";}else{return;}document.head.appendChild(s);})();<\/script>`;

// Routing summary at time of capture:
//   ""  or "/index"      -> inject-home-v2.js?v=18
//   "/trip-planning"     -> inject-trip-planning-v2.js?v=18
//   "/concierge"         -> inject-concierge-v2.js?v=18
//   "/travel-advisor"    -> inject-advisor-v2.js?v=18
//   "/supplier-code"     -> inject-supplier-code.js?v=16
