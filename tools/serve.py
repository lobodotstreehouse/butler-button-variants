#!/usr/bin/env python3
"""
Local dev server for butler-button-variants.

- Serves the workspace as static files (like `python3 -m http.server`).
- Adds a `/api/*` reverse proxy to the Veltm Supabase Edge Functions,
  injecting permissive CORS headers so the pages work from a Codespace
  (`*.app.github.dev`) or any other origin during local preview.

Usage:
    python3 tools/serve.py [port]   # default 8000
"""
from __future__ import annotations

import sys
import urllib.request
import urllib.error
from http.server import SimpleHTTPRequestHandler, ThreadingHTTPServer

SUPABASE_BASE = "https://glhbwpfkykycexyygwjj.supabase.co/functions/v1"
API_PREFIX = "/api/"

CORS_HEADERS = {
    "Access-Control-Allow-Origin": "*",
    "Access-Control-Allow-Methods": "GET, POST, OPTIONS",
    "Access-Control-Allow-Headers": "Content-Type, Authorization, apikey, x-client-info",
    "Access-Control-Max-Age": "86400",
}


class Handler(SimpleHTTPRequestHandler):
    def _send_cors(self) -> None:
        for k, v in CORS_HEADERS.items():
            self.send_header(k, v)

    def do_OPTIONS(self) -> None:  # noqa: N802
        if self.path.startswith(API_PREFIX):
            self.send_response(204)
            self._send_cors()
            self.end_headers()
            return
        super().do_OPTIONS() if hasattr(super(), "do_OPTIONS") else self._default_options()

    def _default_options(self) -> None:
        self.send_response(204)
        self._send_cors()
        self.end_headers()

    def do_POST(self) -> None:  # noqa: N802
        if self.path.startswith(API_PREFIX):
            self._proxy("POST")
            return
        self.send_error(405, "Method Not Allowed")

    def do_GET(self) -> None:  # noqa: N802
        if self.path.startswith(API_PREFIX):
            self._proxy("GET")
            return
        super().do_GET()

    def _proxy(self, method: str) -> None:
        target = SUPABASE_BASE + "/" + self.path[len(API_PREFIX):]
        length = int(self.headers.get("Content-Length") or 0)
        body = self.rfile.read(length) if length > 0 else None

        req = urllib.request.Request(target, data=body, method=method)
        for h in ("Content-Type", "Authorization", "apikey", "x-client-info"):
            v = self.headers.get(h)
            if v:
                req.add_header(h, v)
        # The Edge Function is CORS-locked to butlerbutton.co + www; spoof the
        # Origin so server-to-server proxy calls from this dev box are accepted
        # the same way as a real browser on production.
        req.add_header("Origin", "https://butlerbutton.co")
        req.add_header("Referer", "https://butlerbutton.co/")

        try:
            with urllib.request.urlopen(req, timeout=30) as resp:
                payload = resp.read()
                self.send_response(resp.status)
                ct = resp.headers.get("Content-Type", "application/json")
                self.send_header("Content-Type", ct)
                self._send_cors()
                self.send_header("Content-Length", str(len(payload)))
                self.end_headers()
                self.wfile.write(payload)
        except urllib.error.HTTPError as e:
            payload = e.read() or b""
            self.send_response(e.code)
            self.send_header("Content-Type", e.headers.get("Content-Type", "application/json"))
            self._send_cors()
            self.send_header("Content-Length", str(len(payload)))
            self.end_headers()
            self.wfile.write(payload)
        except Exception as e:  # noqa: BLE001
            msg = f'{{"success":false,"error":"proxy_error","message":{repr(str(e))}}}'.encode()
            self.send_response(502)
            self.send_header("Content-Type", "application/json")
            self._send_cors()
            self.send_header("Content-Length", str(len(msg)))
            self.end_headers()
            self.wfile.write(msg)


def main() -> None:
    port = int(sys.argv[1]) if len(sys.argv) > 1 else 8000
    httpd = ThreadingHTTPServer(("0.0.0.0", port), Handler)
    print(f"Serving on http://0.0.0.0:{port}  (proxy: {API_PREFIX}* -> {SUPABASE_BASE}/*)")
    try:
        httpd.serve_forever()
    except KeyboardInterrupt:
        pass


if __name__ == "__main__":
    main()
