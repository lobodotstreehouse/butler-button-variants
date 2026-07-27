#!/usr/bin/env python3
"""
Demo / meeting request handling for butler-button-variants.

The public pages post JSON to `/forms/request` (see tools/serve.py). Each
submission gets a unique request ID, then two mails go out:

  1. to the partnerships inbox (partners@butlerbutton.co by default), with the
     request ID in the subject and the requester on Reply-To, and
  2. an acknowledgement to the requester, carrying the same request ID, so
     both sides can quote one reference.

Standard library only, to keep requirements.txt empty. Configure SMTP via
environment variables (see SMTP_* below); with no SMTP_HOST set, submissions
are logged in full to stdout and the endpoint reports that mail is not
configured, so the front end can fall back to a pre-filled mailto.
"""
from __future__ import annotations

import os
import re
import secrets
import smtplib
import sys
import threading
import time
from datetime import datetime, timezone
from email.message import EmailMessage
from email.utils import formataddr, formatdate, make_msgid

# ── Configuration ────────────────────────────────────────────────────────────

TEAM_EMAIL = os.environ.get("BB_TEAM_EMAIL", "partners@butlerbutton.co")
FROM_EMAIL = os.environ.get("SMTP_FROM", TEAM_EMAIL)
FROM_NAME = os.environ.get("SMTP_FROM_NAME", "Butler Button")
SITE_URL = os.environ.get("BB_SITE_URL", "https://butlerbutton.co")

SMTP_HOST = os.environ.get("SMTP_HOST", "")
SMTP_PORT = int(os.environ.get("SMTP_PORT", "587"))
SMTP_USER = os.environ.get("SMTP_USER", "")
SMTP_PASSWORD = os.environ.get("SMTP_PASSWORD", "")
# starttls (default) | ssl | none
SMTP_SECURITY = os.environ.get("SMTP_SECURITY", "starttls").lower()
SMTP_TIMEOUT = int(os.environ.get("SMTP_TIMEOUT", "20"))

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


def _base_message(subject: str, to_addr: str, reply_to: str) -> EmailMessage:
    msg = EmailMessage()
    msg["Subject"] = _header_safe(subject)
    msg["From"] = formataddr((FROM_NAME, FROM_EMAIL))
    msg["To"] = to_addr
    msg["Reply-To"] = reply_to
    msg["Date"] = formatdate(localtime=True)
    msg["Message-ID"] = make_msgid(domain="butlerbutton.co")
    return msg


def build_team_email(cleaned: dict, request_id: str, meta: dict) -> EmailMessage:
    spec = REQUEST_TYPES[cleaned["request_type"]]
    who = cleaned["company"] or cleaned["name"]
    subject = f"[{request_id}] {spec['label']} - {_header_safe(who)}"

    rows = _summary_rows(cleaned)
    meta_rows = [
        ("Request ID", request_id),
        ("Received", meta.get("received", "")),
        ("Page", cleaned.get("page") or "-"),
    ]

    msg = _base_message(subject, TEAM_EMAIL, formataddr((cleaned["name"], cleaned["email"])))
    msg.set_content(
        f"{spec['label']}\n"
        f"Request ID: {request_id}\n\n"
        f"{_text_block(rows)}\n\n"
        f"--\n{_text_block(meta_rows)}\n"
        f"Reply to this email to reach {cleaned['name']} directly.\n"
    )
    msg.add_alternative(
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
</div></body></html>""",
        subtype="html",
    )
    return msg


def build_ack_email(cleaned: dict, request_id: str) -> EmailMessage:
    spec = REQUEST_TYPES[cleaned["request_type"]]
    subject = f"{spec['ack_subject']} - {request_id}"
    rows = _summary_rows(cleaned)

    msg = _base_message(subject, formataddr((cleaned["name"], cleaned["email"])), TEAM_EMAIL)
    first_name = cleaned["name"].split()[0] if cleaned["name"].split() else "there"

    msg.set_content(
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
    msg.add_alternative(
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
</div></body></html>""",
        subtype="html",
    )
    return msg


# ── Delivery ─────────────────────────────────────────────────────────────────


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


def deliver(team_msg: EmailMessage, ack_msg: EmailMessage) -> str | None:
    """Send both mails on one connection.

    Raises if the team mail cannot be sent — that one is the whole point of the
    endpoint. Returns a description of the acknowledgement failure (or None),
    since a bounced acknowledgement should not make the requester resubmit.
    """
    server = _connect()
    try:
        server.send_message(team_msg)
        try:
            server.send_message(ack_msg)
        except Exception as exc:  # noqa: BLE001
            return f"{type(exc).__name__}: {exc}"
    finally:
        try:
            server.quit()
        except Exception:  # noqa: BLE001
            pass
    return None


def _log(*parts: str) -> None:
    print("[forms]", *parts, file=sys.stderr, flush=True)


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

    team_msg = build_team_email(cleaned, request_id, meta)
    ack_msg = build_ack_email(cleaned, request_id)

    try:
        ack_error = deliver(team_msg, ack_msg)
    except EmailNotConfigured:
        # Nothing is silently dropped: dump the submission where the operator
        # can find it (Heroku logs) and let the page offer its mailto fallback.
        _log(request_id, "SMTP not configured - submission below")
        print(team_msg.get_body(preferencelist=("plain",)).get_content(), file=sys.stderr, flush=True)
        return 503, {
            "success": False,
            "error": "email_not_configured",
            "message": "Email delivery is not configured on this server.",
            "request_id": request_id,
        }
    except Exception as exc:  # noqa: BLE001
        _log(request_id, f"delivery failed: {type(exc).__name__}: {exc}")
        return 502, {
            "success": False,
            "error": "delivery_failed",
            "message": "We could not send your request just now.",
            "request_id": request_id,
        }

    if ack_error:
        _log(request_id, f"team mail sent, acknowledgement failed: {ack_error}")
    else:
        _log(request_id, f"{cleaned['request_type']} from {cleaned['email']} - both mails sent")

    return 200, {"success": True, "request_id": request_id}
