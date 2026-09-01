#!/usr/bin/env python3
"""Local-only static preview server for generated candidates and releases."""

from __future__ import annotations

import mimetypes
import sys
from http.server import BaseHTTPRequestHandler, ThreadingHTTPServer
from pathlib import Path
from urllib.parse import unquote, urlsplit


MIME = {
    ".html": "text/html; charset=utf-8", ".css": "text/css; charset=utf-8",
    ".js": "text/javascript; charset=utf-8", ".json": "application/json; charset=utf-8",
    ".svg": "image/svg+xml", ".png": "image/png", ".jpg": "image/jpeg",
    ".jpeg": "image/jpeg", ".webp": "image/webp", ".woff2": "font/woff2",
}


def safe_path(root: Path, url: str) -> Path:
    pathname = unquote(urlsplit(url).path)
    candidate = (root / ("index.html" if pathname == "/" else pathname.lstrip("/"))).resolve()
    if candidate != root and root not in candidate.parents:
        raise ValueError("Path escapes preview root.")
    return candidate


def main() -> None:
    root = Path(sys.argv[1] if len(sys.argv) > 1 else ".").resolve()
    requested_port = int(sys.argv[2] if len(sys.argv) > 2 else 4173)

    class Handler(BaseHTTPRequestHandler):
        def do_GET(self) -> None:  # noqa: N802
            try:
                file = safe_path(root, self.path)
                if file.is_dir():
                    file /= "index.html"
                body = file.read_bytes()
                content_type = MIME.get(file.suffix.lower()) or mimetypes.guess_type(str(file))[0] or "application/octet-stream"
                self.send_response(200)
                self.send_header("content-type", content_type)
                self.send_header("cache-control", "no-store")
                self.send_header("x-content-type-options", "nosniff")
                self.end_headers()
                self.wfile.write(body)
            except Exception:
                self.send_response(404)
                self.send_header("content-type", "text/plain; charset=utf-8")
                self.end_headers()
                self.wfile.write(b"Not found\n")

        def log_message(self, _format: str, *_args: object) -> None:
            return

    server = ThreadingHTTPServer(("127.0.0.1", requested_port), Handler)
    print(f"Serving {root} at http://127.0.0.1:{server.server_port}", flush=True)
    server.serve_forever()


if __name__ == "__main__":
    main()
