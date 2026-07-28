#!/usr/bin/env python3
"""
Demo / meeting request handling for butler-button-variants.

The public pages post JSON to `/forms/request` (see tools/serve.py). Each
submission gets a unique request ID, then two mails go out:

  1. to the partnerships inbox (partners@butlerbutton.co by default), with the
     request ID in the subject and the requester on Reply-To, and
  2. an acknowledgement to the requester, carrying the same request ID, so
     both sides can quote one reference.

Standard library only, to keep requirements.txt empty.

Mail goes out through the VELTM Tours ZeptoMail account. Either transport works:

  * its HTTPS API  — set ZEPTOMAIL_TOKEN (the "Send Mail" token), or
  * its SMTP relay — set SMTP_HOST=smtp.zeptomail.com, SMTP_USER=emailapikey
                     and SMTP_PASSWORD=<the mail agent's SMTP token>.

The API is picked automatically when a token is present, since it needs only
outbound 443.

ZeptoMail verifies the SENDING domain, not the destination. That account is set
up for veltmtours.com, so MAIL_FROM lives there while BB_TEAM_EMAIL — a plain
recipient — stays on butlerbutton.co. No butlerbutton.co verification, and no
Veltm-side relay endpoint, is needed for this to work.

Run this module directly to check the configuration, optionally sending a live
test message:  python tools/request_forms.py [you@example.com]

See .env.example for the full variable list. With neither transport configured,
submissions are logged in full and the endpoint says mail is not set up, so the
front end can fall back to a pre-filled mailto.
"""
from __future__ import annotations

import json
import os
import re
import secrets
import smtplib
import sys
import threading
import time
import urllib.error
import urllib.request
from datetime import datetime, timezone
from email.message import EmailMessage
from email.utils import formataddr, formatdate, make_msgid

# ── Configuration ────────────────────────────────────────────────────────────

# Where submissions land. Recipients are unrestricted — ZeptoMail verifies the
# SENDING domain, not the destination — so this stays on butlerbutton.co.
TEAM_EMAIL = os.environ.get("BB_TEAM_EMAIL", "partners@butlerbutton.co")

# Who the mail is FROM. This must sit on a domain verified in the ZeptoMail
# account, which is veltmtours.com — butlerbutton.co is not set up there, so
# defaulting this to TEAM_EMAIL would get every send rejected.
_FROM_ENV = os.environ.get("MAIL_FROM") or os.environ.get("SMTP_FROM")
# The fallback is a plausible guess, not a known-good address. ZeptoMail
# verifies the domain but still rejects a sender the mail agent does not own,
# so an unset MAIL_FROM is called out in config_warnings() rather than left to
# fail at send time.
FROM_EMAIL = _FROM_ENV or "partners@veltmtours.com"
FROM_NAME = os.environ.get("MAIL_FROM_NAME") or os.environ.get("SMTP_FROM_NAME") or "Butler Button"
SITE_URL = os.environ.get("BB_SITE_URL", "https://butlerbutton.co")

# Domains the ZeptoMail account is allowed to send as. Used only to warn early;
# ZeptoMail is the real authority.
VERIFIED_SENDER_DOMAINS = tuple(
    d.strip().lower()
    for d in os.environ.get("BB_VERIFIED_SENDER_DOMAINS", "veltmtours.com").split(",")
    if d.strip()
)

# ZeptoMail HTTPS API. Regional hosts: .com (global), .eu, .in — override the
# whole URL if the account does not live in the default region.
ZEPTOMAIL_API_URL = os.environ.get("ZEPTOMAIL_API_URL", "https://api.zeptomail.com/v1.1/email")
ZEPTOMAIL_TOKEN = os.environ.get("ZEPTOMAIL_TOKEN", "").strip()
ZEPTOMAIL_TIMEOUT = int(os.environ.get("ZEPTOMAIL_TIMEOUT", "20"))

# ZeptoMail SMTP relay (or any other SMTP server).
SMTP_HOST = os.environ.get("SMTP_HOST", "")
SMTP_PORT = int(os.environ.get("SMTP_PORT", "587"))
SMTP_USER = os.environ.get("SMTP_USER", "")
SMTP_PASSWORD = os.environ.get("SMTP_PASSWORD", "")
# starttls (default) | ssl | none
SMTP_SECURITY = os.environ.get("SMTP_SECURITY", "starttls").lower()
SMTP_TIMEOUT = int(os.environ.get("SMTP_TIMEOUT", "20"))

# auto (default) | zeptomail | smtp
MAIL_TRANSPORT = os.environ.get("BB_MAIL_TRANSPORT", "auto").strip().lower()

# When on, a failed send returns the provider's own reason in the JSON response
# instead of only writing it to the logs. Useful while wiring up credentials
# without shell access; leave it off in normal operation.
FORMS_DEBUG = os.environ.get("BB_FORMS_DEBUG", "").strip().lower() in ("1", "true", "yes", "on")

# Per-IP throttle: at most RATE_MAX submissions per RATE_WINDOW seconds.
RATE_MAX = int(os.environ.get("BB_FORMS_RATE_MAX", "5"))
RATE_WINDOW = int(os.environ.get("BB_FORMS_RATE_WINDOW", "600"))

MAX_BODY_BYTES = 16 * 1024

# ── Field definitions ────────────────────────────────────────────────────────

# name -> (label, max length)
FIELDS = {
    "name": ("Name", 120),
    "email": ("Email", 254),
    "phone": ("Phone / WhatsApp", 40),
    "company": ("Property or company", 160),
    "role": ("Role", 120),
    "location": ("City & country", 160),
    "property_type": ("Property type", 60),
    "rooms": ("Rooms or keys", 12),
    "preferred_date": ("Preferred date", 20),
    "preferred_time": ("Preferred time", 60),
    "timezone": ("Time zone", 60),
    "message": ("Notes", 2000),
    "page": ("Submitted from", 200),
}

COMMON = ["name", "email", "phone", "company", "role", "location"]
REQUIRED = ["name", "email", "company", "location"]
# Body-only fields that may keep their line breaks. Everything else is
# single-lined, because it can end up in a mail header.
MULTILINE = {"message"}

REQUEST_TYPES = {
    "demo": {
        "code": "DEMO",
        "label": "Demo request",
        "extra": ["property_type", "rooms"],
        "ack_subject": "We have your demo request",
        "ack_what": "your request for a Butler Button demo",
        "ack_next": (
            "One of our partnerships team will be in touch within one business "
            "day to set up a walkthrough built around your property."
        ),
    },
    "meeting": {
        "code": "MTG",
        "label": "15-minute meeting request",
        "extra": ["preferred_date", "preferred_time", "timezone"],
        "ack_subject": "We have your meeting request",
        "ack_what": "your request for a 15-minute meeting",
        "ack_next": (
            "One of our partnerships team will confirm a slot within one "
            "business day and send a calendar invite with a video link."
        ),
    },
}

EMAIL_RE = re.compile(r"^[^\s@,;:<>\"']+@[^\s@,;:<>\"']+\.[^\s@,;:<>\"']{2,}$")
CONTROL_RE = re.compile(r"[\x00-\x08\x0b\x0c\x0e-\x1f\x7f]")

# Unambiguous alphabet: no 0/O, 1/I, so IDs survive being read aloud.
ID_ALPHABET = "ABCDEFGHJKLMNPQRSTUVWXYZ23456789"


class EmailNotConfigured(RuntimeError):
    """Raised when no SMTP_HOST is set."""


# ── Helpers ──────────────────────────────────────────────────────────────────


def new_request_id(request_type: str) -> str:
    """`BB-DEMO-20260727-4KQ9TX` — sortable by day, random enough to be unique."""
    code = REQUEST_TYPES.get(request_type, {}).get("code", "REQ")
    day = datetime.now(timezone.utc).strftime("%Y%m%d")
    tail = "".join(secrets.choice(ID_ALPHABET) for _ in range(6))
    return f"BB-{code}-{day}-{tail}"


def _clean(value: object, limit: int, multiline: bool = False) -> str:
    """Strip control characters and cap length.

    Single-line by default: any field that can reach a mail header (a name in
    Reply-To, a company in the Subject) must not carry CR/LF, or a submitted
    value could inject headers of its own. Only `message` opts into newlines,
    and it is never used as a header.
    """
    if value is None:
        return ""
    text = value if isinstance(value, str) else str(value)
    text = text.replace("\r\n", "\n").replace("\r", "\n")
    text = CONTROL_RE.sub("", text)
    if multiline:
        text = re.sub(r"\n{3,}", "\n\n", text)
    else:
        text = " ".join(text.split())
    return text.strip()[:limit]


def _header_safe(text: str) -> str:
    return " ".join(text.split())


def validate(payload: dict) -> tuple[dict, str | None]:
    """Return (cleaned, error_message). `error_message` is None when valid."""
    if not isinstance(payload, dict):
        return {}, "Malformed request."

    request_type = _clean(payload.get("request_type"), 20).lower()
    if request_type not in REQUEST_TYPES:
        return {}, "Unknown request type."

    # Honeypot: a real person never sees, let alone fills, this field.
    if _clean(payload.get("website"), 200):
        return {}, "spam"

    cleaned = {"request_type": request_type}
    for name, (_label, limit) in FIELDS.items():
        cleaned[name] = _clean(payload.get(name), limit, multiline=(name in MULTILINE))

    for name in REQUIRED:
        if not cleaned[name]:
            return {}, f"{FIELDS[name][0]} is required."

    if not EMAIL_RE.match(cleaned["email"]):
        return {}, "That email address does not look right."

    return cleaned, None


def fields_for(request_type: str) -> list[str]:
    spec = REQUEST_TYPES[request_type]
    return COMMON + list(spec["extra"]) + ["message"]


# ── Rate limiting ────────────────────────────────────────────────────────────

_hits: dict[str, list[float]] = {}
_hits_lock = threading.Lock()


def rate_limited(client_ip: str) -> bool:
    now = time.time()
    with _hits_lock:
        for ip in list(_hits):
            kept = [t for t in _hits[ip] if now - t < RATE_WINDOW]
            if kept:
                _hits[ip] = kept
            else:
                del _hits[ip]
        seen = _hits.setdefault(client_ip, [])
        if len(seen) >= RATE_MAX:
            return True
        seen.append(now)
        return False


# ── Message building ─────────────────────────────────────────────────────────


def _summary_rows(cleaned: dict) -> list[tuple[str, str]]:
    rows = []
    for name in fields_for(cleaned["request_type"]):
        value = cleaned.get(name, "")
        if value:
            rows.append((FIELDS[name][0], value))
    return rows


def _text_block(rows: list[tuple[str, str]]) -> str:
    width = max((len(label) for label, _ in rows), default=0)
    out: list[str] = []
    for label, value in rows:
        lines = value.split("\n")
        out.append(f"{label.ljust(width)}  {lines[0]}")
        out.extend(f"{' ' * (width + 2)}{line}" for line in lines[1:])
    return "\n".join(out)


def _esc(text: str) -> str:
    return (
        text.replace("&", "&amp;")
        .replace("<", "&lt;")
        .replace(">", "&gt;")
        .replace('"', "&quot;")
    )


def _html_rows(rows: list[tuple[str, str]]) -> str:
    out = []
    for label, value in rows:
        out.append(
            '<tr>'
            '<td style="padding:7px 16px 7px 0;color:#6E6E73;font-size:13px;'
            'vertical-align:top;white-space:nowrap;">' + _esc(label) + "</td>"
            '<td style="padding:7px 0;color:#1D1D1F;font-size:14px;'
            'vertical-align:top;">' + _esc(value).replace("\n", "<br>") + "</td>"
            "</tr>"
        )
    return "\n".join(out)


def _mail(subject: str, to: tuple[str, str], reply_to: tuple[str, str],
          text: str, html: str) -> dict:
    """A transport-neutral message. `to`/`reply_to` are (name, address)."""
    return {
        "subject": _header_safe(subject),
        "to_name": _header_safe(to[0]),
        "to_email": to[1],
        "reply_to_name": _header_safe(reply_to[0]),
        "reply_to_email": reply_to[1],
        "text": text,
        "html": html,
    }


def to_email_message(mail: dict) -> EmailMessage:
    """Render a neutral message as MIME, for the SMTP transport."""
    msg = EmailMessage()
    msg["Subject"] = mail["subject"]
    msg["From"] = formataddr((FROM_NAME, FROM_EMAIL))
    msg["To"] = formataddr((mail["to_name"], mail["to_email"])) if mail["to_name"] else mail["to_email"]
    msg["Reply-To"] = (
        formataddr((mail["reply_to_name"], mail["reply_to_email"]))
        if mail["reply_to_name"] else mail["reply_to_email"]
    )
    msg["Date"] = formatdate(localtime=True)
    msg["Message-ID"] = make_msgid(domain="butlerbutton.co")
    msg.set_content(mail["text"])
    msg.add_alternative(mail["html"], subtype="html")
    return msg


def build_team_email(cleaned: dict, request_id: str, meta: dict) -> dict:
    spec = REQUEST_TYPES[cleaned["request_type"]]
    who = cleaned["company"] or cleaned["name"]
    subject = f"[{request_id}] {spec['label']} - {_header_safe(who)}"

    rows = _summary_rows(cleaned)
    meta_rows = [
        ("Request ID", request_id),
        ("Received", meta.get("received", "")),
        ("Page", cleaned.get("page") or "-"),
    ]

    text = (
        f"{spec['label']}\n"
        f"Request ID: {request_id}\n\n"
        f"{_text_block(rows)}\n\n"
        f"--\n{_text_block(meta_rows)}\n"
        f"Reply to this email to reach {cleaned['name']} directly.\n"
    )
    html = (
        f"""<!DOCTYPE html><html><body style="margin:0;padding:24px;background:#F5F5F7;
 font-family:-apple-system,BlinkMacSystemFont,'Segoe UI',Helvetica,Arial,sans-serif;">
<div style="max-width:600px;margin:0 auto;background:#fff;border-radius:14px;overflow:hidden;
 border:1px solid #E5E7EB;">
  <div style="background:linear-gradient(135deg,#4F46E5,#7C3AED);padding:22px 28px;color:#fff;">
    <div style="font-size:11px;letter-spacing:.16em;text-transform:uppercase;opacity:.8;">
      New {_esc(spec['label'].lower())}</div>
    <div style="font-size:20px;font-weight:600;margin-top:6px;">{_esc(who)}</div>
  </div>
  <div style="padding:24px 28px;">
    <table style="width:100%;border-collapse:collapse;">{_html_rows(rows)}</table>
  </div>
  <div style="padding:16px 28px 22px;border-top:1px solid #E5E7EB;color:#86868B;font-size:12px;
   line-height:1.6;">
    <table style="width:100%;border-collapse:collapse;">{_html_rows(meta_rows)}</table>
    <p style="margin:12px 0 0;">Reply to this email to reach
      {_esc(cleaned['name'])} directly.</p>
  </div>
</div></body></html>"""
    )
    return _mail(subject, (FROM_NAME, TEAM_EMAIL), (cleaned["name"], cleaned["email"]), text, html)


def build_ack_email(cleaned: dict, request_id: str) -> dict:
    spec = REQUEST_TYPES[cleaned["request_type"]]
    subject = f"{spec['ack_subject']} - {request_id}"
    rows = _summary_rows(cleaned)
    first_name = cleaned["name"].split()[0] if cleaned["name"].split() else "there"

    text = (
        f"Hi {first_name},\n\n"
        f"Thank you - we have received {spec['ack_what']}.\n\n"
        f"Your request ID is {request_id}. Please quote it in any follow-up.\n\n"
        f"{spec['ack_next']}\n\n"
        f"Here is what you sent us:\n\n"
        f"{_text_block(rows)}\n\n"
        f"If anything above needs correcting, just reply to this email.\n\n"
        f"Butler Button\n"
        f"{TEAM_EMAIL}\n"
        f"{SITE_URL}\n"
    )
    html = (
        f"""<!DOCTYPE html><html><body style="margin:0;padding:24px;background:#F5F5F7;
 font-family:-apple-system,BlinkMacSystemFont,'Segoe UI',Helvetica,Arial,sans-serif;">
<div style="max-width:600px;margin:0 auto;background:#fff;border-radius:14px;overflow:hidden;
 border:1px solid #E5E7EB;">
  <div style="background:linear-gradient(135deg,#4F46E5,#7C3AED);padding:26px 28px;color:#fff;">
    <div style="font-size:11px;letter-spacing:.16em;text-transform:uppercase;opacity:.8;">
      Butler Button</div>
    <div style="font-size:22px;font-weight:600;margin-top:6px;">
      {_esc(spec['ack_subject'])}</div>
  </div>
  <div style="padding:26px 28px;color:#1D1D1F;font-size:15px;line-height:1.6;">
    <p style="margin:0 0 16px;">Hi {_esc(first_name)},</p>
    <p style="margin:0 0 20px;">Thank you - we have received
      {_esc(spec['ack_what'])}.</p>
    <div style="background:#EEF2FF;border-radius:12px;padding:16px 20px;margin:0 0 20px;">
      <div style="font-size:11px;letter-spacing:.16em;text-transform:uppercase;color:#6E6E73;">
        Your request ID</div>
      <div style="font-family:ui-monospace,SFMono-Regular,Menlo,monospace;font-size:17px;
       letter-spacing:.05em;color:#4F46E5;margin-top:5px;">{_esc(request_id)}</div>
    </div>
    <p style="margin:0 0 22px;">{_esc(spec['ack_next'])}</p>
    <div style="font-size:11px;letter-spacing:.16em;text-transform:uppercase;color:#86868B;
     margin-bottom:8px;">What you sent us</div>
    <table style="width:100%;border-collapse:collapse;">{_html_rows(rows)}</table>
    <p style="margin:22px 0 0;color:#6E6E73;font-size:13px;">
      If anything above needs correcting, just reply to this email.</p>
  </div>
  <div style="padding:16px 28px 22px;border-top:1px solid #E5E7EB;color:#86868B;font-size:12px;">
    Butler Button ·
    <a href="mailto:{_esc(TEAM_EMAIL)}" style="color:#4F46E5;">{_esc(TEAM_EMAIL)}</a> ·
    <a href="{_esc(SITE_URL)}" style="color:#4F46E5;">{_esc(SITE_URL)}</a>
  </div>
</div></body></html>"""
    )
    return _mail(subject, (cleaned["name"], cleaned["email"]), (FROM_NAME, TEAM_EMAIL), text, html)


# ── Delivery ─────────────────────────────────────────────────────────────────


def active_transport() -> str:
    """Which transport will be used: 'zeptomail', 'smtp', or '' if unconfigured."""
    if MAIL_TRANSPORT == "zeptomail":
        return "zeptomail" if ZEPTOMAIL_TOKEN else ""
    if MAIL_TRANSPORT == "smtp":
        return "smtp" if SMTP_HOST else ""
    # auto: prefer the API — it needs only outbound 443.
    if ZEPTOMAIL_TOKEN:
        return "zeptomail"
    return "smtp" if SMTP_HOST else ""


def transport_summary() -> str:
    which = active_transport()
    if which == "zeptomail":
        return f"ZeptoMail API {ZEPTOMAIL_API_URL}"
    if which == "smtp":
        relay = "ZeptoMail SMTP" if "zeptomail" in SMTP_HOST.lower() else "SMTP"
        return f"{relay} {SMTP_HOST}:{SMTP_PORT}"
    return "mail not configured"


def config_warnings() -> list[str]:
    """Configuration mistakes worth flagging before a real send fails."""
    warnings = []
    which = active_transport()
    if not which:
        warnings.append(
            "no mail transport configured - set ZEPTOMAIL_TOKEN (or SMTP_HOST); "
            "submissions will be logged but not emailed"
        )
    domain = FROM_EMAIL.rpartition("@")[2].lower()
    if VERIFIED_SENDER_DOMAINS and domain not in VERIFIED_SENDER_DOMAINS:
        warnings.append(
            f"MAIL_FROM is {FROM_EMAIL}, but ZeptoMail is verified for "
            f"{', '.join(VERIFIED_SENDER_DOMAINS)} - sends will likely be rejected"
        )
    elif not _FROM_ENV:
        warnings.append(
            f"MAIL_FROM is not set, so mail goes out as {FROM_EMAIL} - a guess. "
            "Set it to the address the ZeptoMail mail agent actually sends as, "
            "or sends will be rejected as an unrecognised sender"
        )
    if which == "smtp" and SMTP_HOST and "zeptomail" in SMTP_HOST.lower() and SMTP_USER != "emailapikey":
        warnings.append("ZeptoMail SMTP expects SMTP_USER=emailapikey")
    return warnings


# ── ZeptoMail HTTPS API ──────────────────────────────────────────────────────


def _zepto_auth_header() -> str:
    """ZeptoMail wants `Zoho-enczapikey <token>`; accept a token pasted either way."""
    token = ZEPTOMAIL_TOKEN
    return token if token.lower().startswith("zoho-enczapikey ") else f"Zoho-enczapikey {token}"


def _zepto_payload(mail: dict) -> dict:
    payload = {
        "from": {"address": FROM_EMAIL, "name": FROM_NAME},
        "to": [{"email_address": {"address": mail["to_email"], "name": mail["to_name"]}}],
        "subject": mail["subject"],
        "textbody": mail["text"],
        "htmlbody": mail["html"],
    }
    if mail["reply_to_email"]:
        payload["reply_to"] = [
            {"address": mail["reply_to_email"], "name": mail["reply_to_name"]}
        ]
    return payload


def _send_via_zeptomail(mail: dict) -> None:
    """POST one message. Raises on any non-2xx response."""
    req = urllib.request.Request(
        ZEPTOMAIL_API_URL,
        data=json.dumps(_zepto_payload(mail)).encode("utf-8"),
        method="POST",
        headers={
            "Authorization": _zepto_auth_header(),
            "Content-Type": "application/json",
            "Accept": "application/json",
        },
    )
    try:
        with urllib.request.urlopen(req, timeout=ZEPTOMAIL_TIMEOUT) as res:
            if not 200 <= res.status < 300:
                raise RuntimeError(f"ZeptoMail returned HTTP {res.status}")
    except urllib.error.HTTPError as exc:
        detail = ""
        try:
            body = json.loads(exc.read() or b"{}")
            detail = body.get("message") or body.get("error", {}).get("message") or ""
            # Surface the sub-code (e.g. an unverified from-address) when present.
            sub = (body.get("error", {}).get("details") or [{}])[0].get("message")
            if sub and sub not in detail:
                detail = f"{detail} ({sub})".strip()
        except Exception:  # noqa: BLE001
            pass
        raise RuntimeError(f"ZeptoMail HTTP {exc.code}{': ' + detail if detail else ''}") from exc


# ── SMTP ─────────────────────────────────────────────────────────────────────


def _connect() -> smtplib.SMTP:
    if not SMTP_HOST:
        raise EmailNotConfigured("SMTP_HOST is not set")
    if SMTP_SECURITY == "ssl":
        server: smtplib.SMTP = smtplib.SMTP_SSL(SMTP_HOST, SMTP_PORT, timeout=SMTP_TIMEOUT)
    else:
        server = smtplib.SMTP(SMTP_HOST, SMTP_PORT, timeout=SMTP_TIMEOUT)
        if SMTP_SECURITY == "starttls":
            server.starttls()
    if SMTP_USER:
        server.login(SMTP_USER, SMTP_PASSWORD)
    return server


def _deliver_smtp(team_mail: dict, ack_mail: dict) -> str | None:
    server = _connect()
    try:
        server.send_message(to_email_message(team_mail))
        try:
            server.send_message(to_email_message(ack_mail))
        except Exception as exc:  # noqa: BLE001
            return f"{type(exc).__name__}: {exc}"
    finally:
        try:
            server.quit()
        except Exception:  # noqa: BLE001
            pass
    return None


# ── Dispatch ─────────────────────────────────────────────────────────────────


def deliver(team_mail: dict, ack_mail: dict) -> str | None:
    """Send both mails via the configured transport.

    Raises if the team mail cannot be sent — that one is the whole point of the
    endpoint. Returns a description of the acknowledgement failure (or None),
    since a bounced acknowledgement should not make the requester resubmit.
    """
    which = active_transport()
    if which == "zeptomail":
        _send_via_zeptomail(team_mail)
        try:
            _send_via_zeptomail(ack_mail)
        except Exception as exc:  # noqa: BLE001
            return f"{type(exc).__name__}: {exc}"
        return None
    if which == "smtp":
        return _deliver_smtp(team_mail, ack_mail)
    raise EmailNotConfigured("set ZEPTOMAIL_TOKEN, or SMTP_HOST for the SMTP relay")


def _log(*parts: str) -> None:
    print("[forms]", *parts, file=sys.stderr, flush=True)


def _redact(text: str) -> str:
    """Never let a credential ride out in a response, however it got there."""
    for secret in (ZEPTOMAIL_TOKEN, SMTP_PASSWORD):
        if secret and len(secret) > 6:
            text = text.replace(secret, "***")
    return text


def handle(payload: dict, client_ip: str = "") -> tuple[int, dict]:
    """Validate, mail, and return (http_status, json_response)."""
    cleaned, error = validate(payload)
    if error == "spam":
        # Say nothing useful to a bot; a real submission never lands here.
        return 200, {"success": True, "request_id": new_request_id("demo")}
    if error:
        return 400, {"success": False, "error": "invalid_request", "message": error}

    if client_ip and rate_limited(client_ip):
        return 429, {
            "success": False,
            "error": "rate_limited",
            "message": "Too many requests from this address. Please try again shortly.",
        }

    request_id = new_request_id(cleaned["request_type"])
    received = datetime.now(timezone.utc).strftime("%Y-%m-%d %H:%M UTC")
    meta = {"received": received, "ip": client_ip}

    team_mail = build_team_email(cleaned, request_id, meta)
    ack_mail = build_ack_email(cleaned, request_id)

    try:
        ack_error = deliver(team_mail, ack_mail)
    except EmailNotConfigured as exc:
        # Nothing is silently dropped: dump the submission where the operator
        # can find it (Heroku logs) and let the page offer its mailto fallback.
        _log(request_id, f"mail not configured ({exc}) - submission below")
        print(team_mail["text"], file=sys.stderr, flush=True)
        return 503, {
            "success": False,
            "error": "email_not_configured",
            "message": "Email delivery is not configured on this server.",
            "request_id": request_id,
        }
    except Exception as exc:  # noqa: BLE001
        _log(request_id, f"delivery failed via {active_transport()}: {type(exc).__name__}: {exc}")
        print(team_mail["text"], file=sys.stderr, flush=True)
        response = {
            "success": False,
            "error": "delivery_failed",
            "message": "We could not send your request just now.",
            "request_id": request_id,
        }
        if FORMS_DEBUG:
            response["detail"] = _redact(f"{type(exc).__name__}: {exc}")
        return 502, response

    if ack_error:
        _log(request_id, f"team mail sent, acknowledgement failed: {ack_error}")
    else:
        _log(request_id,
             f"{cleaned['request_type']} from {cleaned['email']} - both mails sent "
             f"via {active_transport()}")

    return 200, {"success": True, "request_id": request_id}


# ── Self-check ───────────────────────────────────────────────────────────────


def _selftest(recipient: str | None) -> int:
    """`python tools/request_forms.py [you@example.com]`

    Prints the resolved mail configuration, and with an address, sends a real
    test message through it. Handy for confirming a deployment without having
    to submit the form.
    """
    print("Mail configuration")
    print(f"  transport : {transport_summary()}")
    print(f"  from      : {FROM_NAME} <{FROM_EMAIL}>")
    print(f"  team inbox: {TEAM_EMAIL}")
    print(f"  token set : {'yes' if ZEPTOMAIL_TOKEN else 'no'}")
    for warning in config_warnings():
        print(f"  WARNING   : {warning}")

    if not recipient:
        print("\nPass an email address to send a live test message.")
        return 0 if active_transport() else 1

    sample = {
        "request_type": "demo", "name": "Config Test", "email": recipient,
        "company": "Butler Button self-check", "location": "-",
        "phone": "", "role": "", "property_type": "", "rooms": "",
        "preferred_date": "", "preferred_time": "", "timezone": "",
        "message": "This is a self-check message from tools/request_forms.py.",
        "page": "selftest",
    }
    request_id = new_request_id("demo")
    received = datetime.now(timezone.utc).strftime("%Y-%m-%d %H:%M UTC")
    team = build_team_email(sample, request_id, {"received": received, "ip": "selftest"})
    ack = build_ack_email(sample, request_id)
    # Keep the self-check out of the real inbox: both copies go to the tester.
    team["to_email"], team["to_name"] = recipient, "Config Test"

    print(f"\nSending {request_id} to {recipient} ...")
    try:
        ack_error = deliver(team, ack)
    except Exception as exc:  # noqa: BLE001
        print(f"FAILED: {type(exc).__name__}: {exc}")
        return 1
    print("Sent." + (f" (acknowledgement copy failed: {ack_error})" if ack_error else ""))
    return 0


if __name__ == "__main__":
    sys.exit(_selftest(sys.argv[1] if len(sys.argv) > 1 else None))
