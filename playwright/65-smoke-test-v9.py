"""Live butlerbutton.co smoke test at ?v=7 (post-cutover).
5 routes x 2 viewports. For each:
  - Full-page screenshot
  - CTA inventory + tier breakdown
  - Modal walk: CTA -> step 1 -> step 2 -> step 3 -> capture redirect URL
  - Stop at the Stripe redirect URL. NEVER click pay (permanent no-pay rule).
  - Verify inject script loaded from ?v=7 and contains butler-booking-api
  - Console error / 4xx response triage
"""
import json, sys
from pathlib import Path
from playwright.sync_api import sync_playwright

ROUTES = [
    ("/", "trip"),
    ("/trip-planning", "trip"),
    ("/concierge", "8h"),
    ("/travel-advisor", "8h"),       # advisor has only trip + 8h
    ("/supplier-code", "__none__"),
]
VIEWPORTS = [(1440, 900, "desktop"), (375, 812, "mobile")]
OUT = Path("/tmp/smoke_v3_v7")
OUT.mkdir(parents=True, exist_ok=True)

results = []

with sync_playwright() as pw:
    b = pw.chromium.launch(headless=True)
    for route, expected_tier in ROUTES:
        for w, h, vlabel in VIEWPORTS:
            tag = f"{(route.strip('/').replace('/','_') or 'home')}__{vlabel}"
            r = {"route": route, "viewport": vlabel, "tag": tag}
            ctx = b.new_context(viewport={"width": w, "height": h})
            p = ctx.new_page()
            page_errors, console_errors, bad_responses = [], [], []
            p.on("pageerror", lambda e: page_errors.append(str(e)))
            p.on("console", lambda m: console_errors.append(m.text) if m.type == "error" else None)
            p.on("response", lambda resp: bad_responses.append(f"{resp.status} {resp.url}") if resp.status >= 400 else None)

            try:
                p.goto("https://www.butlerbutton.co" + route, wait_until="networkidle", timeout=60000)
                p.wait_for_timeout(3500)
            except Exception as e:
                r["goto_error"] = str(e)
                results.append(r); ctx.close(); continue

            p.screenshot(path=str(OUT / f"{tag}_01_loaded.png"), full_page=True)

            # Verify the loaded inject script is the v=7 butler-booking-api one
            inject_check = p.evaluate(r"""async () => {
              const scripts = Array.from(document.querySelectorAll('script[src*="inject-"]'));
              const src = scripts.length ? scripts[0].src : null;
              if (!src) return { src: null };
              try {
                const r = await fetch(src);
                const t = await r.text();
                return {
                  src,
                  is_v9: src.includes('?v=9'),
                  has_butler_booking_api: t.includes('butler-booking-api'),
                  has_buy_stripe_link: /buy\.stripe\.com\/[a-zA-Z0-9]{8,}/.test(t),
                  has_parseCountries: t.includes('parseCountries'),
                };
              } catch (e) { return { src, error: String(e) }; }
            }""")
            r["inject_check"] = inject_check

            ctas = p.evaluate(r"""() => {
              const els = Array.from(document.querySelectorAll('[data-butler-button]'));
              return els.map(e => ({tier: e.getAttribute('data-tier'), visible: !!e.offsetParent}));
            }""")
            r["cta_count"] = len(ctas)
            r["cta_visible_count"] = sum(1 for c in ctas if c["visible"])
            r["cta_tiers"] = sorted(set(c["tier"] for c in ctas if c["tier"]))

            if expected_tier == "__none__":
                r["mode"] = "no-cta-by-design"
                r["assert_no_cta_pass"] = (r["cta_count"] == 0)
            else:
                r["mode"] = "modal-walk"
                if r["cta_visible_count"] == 0:
                    r["click_skip"] = "no visible CTA"
                else:
                    cta = p.locator(f"[data-butler-button][data-tier='{expected_tier}']").first
                    try:
                        cta.scroll_into_view_if_needed()
                        p.wait_for_timeout(300)
                        cta.click()
                        p.wait_for_timeout(700)
                    except Exception as e:
                        r["cta_click_err"] = str(e)

                    modal_state = p.evaluate(r"""() => {
                      const d = document.getElementById('bbModal');
                      if (!d) return { exists: false };
                      return { exists: true, open: d.hasAttribute('open') };
                    }""")
                    r["modal_after_cta"] = modal_state

                    if modal_state.get("exists") and modal_state.get("open"):
                        p.screenshot(path=str(OUT / f"{tag}_02_modal_open.png"), full_page=False)

                        # Step 1: fill form. NEW form requires Destination (parseCountries)
                        p.locator("#bbm-name").fill("Smoke Test")
                        p.locator("#bbm-email").fill("smoke@example.com")
                        try:
                            p.locator("#bbm-dest").fill("Japan")
                        except Exception:
                            pass
                        try:
                            p.locator("#bbm-party").fill("2")
                        except Exception:
                            pass
                        p.locator("#bbModal__form button[type='submit']").first.click()
                        p.wait_for_timeout(500)

                        visible = p.evaluate(r"""() => Array.from(document.querySelectorAll('.bb-modal__step'))
                          .filter(s => !s.hidden).map(s => s.getAttribute('data-step'))""")
                        r["step_after_form"] = visible

                        if "2" in visible:
                            try:
                                p.locator(f"[data-tier-card='{expected_tier}']").first.click()
                                p.wait_for_timeout(200)
                            except Exception:
                                pass
                            try:
                                p.locator(".bb-modal__step[data-step='2'] [data-action='next']").first.click()
                                p.wait_for_timeout(400)
                            except Exception as e:
                                r["step2_err"] = str(e)

                            visible2 = p.evaluate(r"""() => Array.from(document.querySelectorAll('.bb-modal__step'))
                              .filter(s => !s.hidden).map(s => s.getAttribute('data-step'))""")
                            r["step_after_next"] = visible2

                            if "3" in visible2:
                                p.screenshot(path=str(OUT / f"{tag}_03_step3.png"), full_page=False)
                                try:
                                    # Capture redirect URL but never click pay
                                    with p.expect_navigation(wait_until="commit", timeout=15000) as nav_info:
                                        p.locator(".bb-modal__step[data-step='3'] [data-action='checkout']").first.click()
                                    nav = nav_info.value
                                    r["nav_target"] = nav.url
                                    # Hard stop: do not load Stripe page, do not enter card info
                                    p.evaluate("() => { try { window.stop(); } catch(e){} }")
                                except Exception as e:
                                    r["checkout_err"] = str(e)
                                    r["nav_target"] = p.url

            r["pageerror_count"] = len(page_errors)
            r["console_error_count"] = len(console_errors)
            r["bad_response_count"] = len(bad_responses)
            r["pageerrors"] = page_errors[:5]
            r["console_errors"] = console_errors[:5]
            r["bad_responses"] = bad_responses[:10]
            results.append(r)
            ctx.close()
    b.close()

(OUT / "results.json").write_text(json.dumps(results, indent=2))
print("\n=== SMOKE TEST SUMMARY ===")
for r in results:
    inj = r.get("inject_check", {})
    is_v9 = inj.get("is_v9", False)
    has_api = inj.get("has_butler_booking_api", False)
    line = f"{r['route']:<18} {r['viewport']:<7} | v7={'Y' if is_v9 else 'N'} api={'Y' if has_api else 'N'} | mode={r.get('mode','?'):<18}"
    if r.get("mode") == "no-cta-by-design":
        line += f" no_cta={'YES' if r.get('assert_no_cta_pass') else 'NO'}"
    else:
        nav = r.get("nav_target", "")
        nav_ok = nav.startswith("https://checkout.stripe.com/") or nav.startswith("https://buy.stripe.com/")
        line += f" step1={r.get('step_after_form')} step3={r.get('step_after_next')} nav={'OK' if nav_ok else 'FAIL'}"
        if nav: line += f" -> {nav[:60]}..."
    line += f" | err pe={r.get('pageerror_count')} ce={r.get('console_error_count')} 4xx={r.get('bad_response_count')}"
    print(line)
print(f"\nFull JSON: {OUT}/results.json")
