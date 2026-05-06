/* ─────────────────────────────────────────────────────────────────
   Shared channel-block snippet (v3 channel pass).
   Reusable HTML + CSS injected into every page below the hero.
   Channels: WhatsApp, Video Call, Email.
   Placeholders:
     __WA__    = https://wa.me/18555031555
     __VID__   = https://calendly.com/butlerbutton/video   (TODO: confirm Calendly URL)
     __MAIL__  = mailto:concierge@butlerbutton.co          (TODO: confirm address)
   ───────────────────────────────────────────────────────────────── */

window.BB_CHANNELS_CSS = `
/* Channel block (v3) */
.bb-ch{padding:5.5rem 1.5rem;background:#0a0a0a;color:#fff;border-top:1px solid rgba(255,255,255,0.08);border-bottom:1px solid rgba(255,255,255,0.08)}
.bb-ch__wrap{max-width:1100px;margin:0 auto}
.bb-ch__eyebrow{font-size:0.8rem;font-weight:600;letter-spacing:0.14em;text-transform:uppercase;color:#a5b4fc;margin:0 0 1rem;text-align:center}
.bb-ch__h2{font-family:'Playfair Display',Georgia,serif;font-weight:600;font-size:clamp(1.85rem,3.6vw,2.7rem);letter-spacing:-0.02em;margin:0 0 0.7rem;text-align:center;color:#fff;line-height:1.1}
.bb-ch__sub{color:rgba(255,255,255,0.6);font-size:1.02rem;margin:0 auto 2.6rem;letter-spacing:-0.01em;text-align:center;max-width:560px;line-height:1.55}
.bb-ch__grid{display:grid;grid-template-columns:repeat(3,1fr);gap:1.1rem}
@media (max-width:820px){.bb-ch__grid{grid-template-columns:1fr;gap:0.9rem}}
.bb-ch__card{display:flex;flex-direction:column;padding:2rem 1.6rem;background:rgba(255,255,255,0.03);border:1px solid rgba(255,255,255,0.1);border-radius:14px;color:#fff;text-decoration:none;transition:background .25s ease,border-color .25s ease,transform .25s ease}
.bb-ch__card:hover{background:rgba(255,255,255,0.06);border-color:rgba(165,180,252,0.45);transform:translateY(-2px)}
.bb-ch__icon{width:42px;height:42px;display:flex;align-items:center;justify-content:center;background:rgba(99,102,241,0.18);border-radius:10px;margin-bottom:1.1rem;color:#c7d2fe}
.bb-ch__name{font-size:1.12rem;font-weight:600;letter-spacing:-0.01em;margin-bottom:0.4rem;color:#fff}
.bb-ch__desc{font-size:0.93rem;color:rgba(255,255,255,0.62);line-height:1.55;margin-bottom:1.2rem;letter-spacing:-0.005em;flex:1}
.bb-ch__cta{font-size:0.9rem;color:#a5b4fc;font-weight:500;letter-spacing:-0.01em;display:inline-flex;align-items:center;gap:0.35rem}
.bb-ch__cta::after{content:"\\2192";transition:transform .2s ease}
.bb-ch__card:hover .bb-ch__cta::after{transform:translateX(3px)}
.bb-ch__hours{margin-top:2.4rem;text-align:center;font-size:0.84rem;color:rgba(255,255,255,0.45);letter-spacing:-0.005em}
.bb-ch__hours strong{color:rgba(255,255,255,0.75);font-weight:500}
`;

window.BB_CHANNELS_HTML = `
<section class="bb-ch" id="reach">
  <div class="bb-ch__wrap">
    <p class="bb-ch__eyebrow">Reach your Butler</p>
    <h2 class="bb-ch__h2">Three ways in. One human team.</h2>
    <p class="bb-ch__sub">WhatsApp for in-the-moment requests, video for trip planning, email for long briefs. Same Butlers, same response window, you pick the surface.</p>
    <div class="bb-ch__grid">

      <a class="bb-ch__card" href="https://wa.me/18555031555" target="_blank" rel="noopener">
        <div class="bb-ch__icon">
          <svg width="22" height="22" viewBox="0 0 24 24" fill="currentColor" aria-hidden="true"><path d="M17.5 14.4c-.3-.1-1.7-.8-2-.9-.3-.1-.4-.1-.6.1-.2.3-.7.9-.9 1.1-.2.2-.3.2-.6.1-.3-.1-1.3-.5-2.4-1.5-.9-.8-1.5-1.8-1.7-2.1-.2-.3 0-.5.1-.6.1-.1.3-.3.4-.5.1-.2.2-.3.3-.5.1-.2 0-.4 0-.5-.1-.1-.6-1.5-.9-2-.2-.5-.4-.5-.6-.5h-.5c-.2 0-.5.1-.7.3-.3.3-1 1-1 2.4 0 1.4 1 2.8 1.2 3 .1.2 2 3.1 4.9 4.3.7.3 1.2.5 1.6.6.7.2 1.3.2 1.8.1.5-.1 1.7-.7 1.9-1.4.2-.7.2-1.2.2-1.4-.1-.1-.3-.2-.6-.3zM12 2C6.5 2 2 6.5 2 12c0 1.8.5 3.5 1.3 4.9L2 22l5.3-1.3C8.6 21.5 10.3 22 12 22c5.5 0 10-4.5 10-10S17.5 2 12 2z"/></svg>
        </div>
        <div class="bb-ch__name">WhatsApp</div>
        <div class="bb-ch__desc">For anything mid-trip or quick. Text us, replies inside 4 minutes during waking hours.</div>
        <span class="bb-ch__cta">Open WhatsApp</span>
      </a>

      <a class="bb-ch__card" href="https://calendly.com/butlerbutton/video" target="_blank" rel="noopener">
        <div class="bb-ch__icon">
          <svg width="22" height="22" viewBox="0 0 24 24" fill="currentColor" aria-hidden="true"><path d="M17 10.5V7a1 1 0 0 0-1-1H4a1 1 0 0 0-1 1v10a1 1 0 0 0 1 1h12a1 1 0 0 0 1-1v-3.5l4 4v-11l-4 4z"/></svg>
        </div>
        <div class="bb-ch__name">Video Call</div>
        <div class="bb-ch__desc">For planning a real itinerary. Book a 30-minute video session with your Butler.</div>
        <span class="bb-ch__cta">Schedule a call</span>
      </a>

      <a class="bb-ch__card" href="mailto:concierge@butlerbutton.co">
        <div class="bb-ch__icon">
          <svg width="22" height="22" viewBox="0 0 24 24" fill="currentColor" aria-hidden="true"><path d="M20 4H4a2 2 0 0 0-2 2v12a2 2 0 0 0 2 2h16a2 2 0 0 0 2-2V6a2 2 0 0 0-2-2zm0 4l-8 5-8-5V6l8 5 8-5z"/></svg>
        </div>
        <div class="bb-ch__name">Email</div>
        <div class="bb-ch__desc">For the long brief. Send the dossier, files, links. We reply inside the hour.</div>
        <span class="bb-ch__cta">Email concierge</span>
      </a>

    </div>
    <p class="bb-ch__hours"><strong>Coverage:</strong> 24/7 across 150+ countries. No app, no membership, no chatbots.</p>
  </div>
</section>
`;
