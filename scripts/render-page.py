#!/usr/bin/env python3
"""Render a local candidate with Chromium and record browser diagnostics."""

from __future__ import annotations

import asyncio
import json
import mimetypes
import sys
from datetime import datetime, timezone
from http.server import BaseHTTPRequestHandler, ThreadingHTTPServer
from pathlib import Path
from typing import Any
from urllib.parse import unquote, urlsplit

from playwright.async_api import async_playwright


MIME = {".html": "text/html", ".css": "text/css", ".js": "text/javascript", ".svg": "image/svg+xml", ".png": "image/png", ".jpg": "image/jpeg", ".jpeg": "image/jpeg", ".webp": "image/webp", ".woff2": "font/woff2"}


def now() -> str:
    return datetime.now(timezone.utc).isoformat(timespec="milliseconds").replace("+00:00", "Z")


def options(values: list[str]) -> dict[str, str]:
    return {values[index].removeprefix("--"): values[index + 1] for index in range(0, len(values), 2)}


def local_server(root: Path, entry: str) -> ThreadingHTTPServer:
    class Handler(BaseHTTPRequestHandler):
        def do_GET(self) -> None:  # noqa: N802
            try:
                pathname = unquote(urlsplit(self.path).path)
                file = (root / ((entry if pathname == "/" else pathname.lstrip("/")))).resolve()
                if file != root and root not in file.parents:
                    raise ValueError("Unsafe path")
                if file.is_dir():
                    file /= entry
                body = file.read_bytes()
                self.send_response(200)
                self.send_header("content-type", MIME.get(file.suffix.lower()) or mimetypes.guess_type(str(file))[0] or "application/octet-stream")
                self.send_header("cache-control", "no-store")
                self.end_headers()
                self.wfile.write(body)
            except Exception:
                self.send_response(404)
                self.end_headers()

        def log_message(self, _format: str, *_args: object) -> None:
            return

    server = ThreadingHTTPServer(("127.0.0.1", 0), Handler)
    server.daemon_threads = True
    return server


async def _render(args: dict[str, str]) -> int:
    if not args.get("root") or not args.get("output"):
        raise ValueError("Usage: render-page.py --root <site-dir> --output <png> [--width 1440] [--height 900] [--scale 1] [--entry index.html]")
    root, output = Path(args["root"]).resolve(), Path(args["output"]).resolve()
    width, height = int(args.get("width", "1440")), int(args.get("height", "900"))
    scale = float(args.get("scale", "1"))
    entry = args.get("entry", "index.html")
    if not 240 <= width <= 10000:
        raise ValueError("Invalid viewport width.")
    if not 240 <= height <= 10000:
        raise ValueError("Invalid viewport height.")
    if not 0.5 <= scale <= 4:
        raise ValueError("Invalid device scale factor; use a value between 0.5 and 4.")
    server = local_server(root, entry)
    import threading
    thread = threading.Thread(target=server.serve_forever, daemon=True)
    thread.start()
    console_errors: list[str] = []
    failed_requests: list[dict[str, str]] = []
    try:
        async with async_playwright() as playwright:
            browser = await playwright.chromium.launch(headless=True)
            try:
                page = await browser.new_page(viewport={"width": width, "height": height}, device_scale_factor=scale)
                page.on("console", lambda message: console_errors.append(message.text) if message.type == "error" else None)

                def request_failed(request: Any) -> None:
                    failure = request.failure
                    if isinstance(failure, dict):
                        error = failure.get("errorText", "request failed")
                    else:
                        error = failure or "request failed"
                    failed_requests.append({"url": request.url, "error": error})

                page.on("requestfailed", request_failed)
                response = await page.goto(f"http://127.0.0.1:{server.server_port}/{entry}", wait_until="networkidle")
                if response is None or not response.ok:
                    status = response.status if response is not None else "unknown"
                    raise ValueError(f"Preview returned HTTP {status}.")
                await page.emulate_media(reduced_motion="reduce")
                await page.evaluate("() => document.fonts?.ready")
                full_page = args.get("full-page") != "false"
                if full_page:
                    # The guidelines require loading="lazy" below the fold, and a
                    # lazy image never decodes if it is never scrolled into view --
                    # the stitched screenshot then captures blank boxes and the
                    # visual diff blames the page for a harness artefact. Walk the
                    # document, then wait for every image to actually decode.
                    await page.evaluate("""async () => {
                      const step = window.innerHeight;
                      for (let y = 0; y < document.documentElement.scrollHeight; y += step) {
                        window.scrollTo(0, y);
                        await new Promise(r => requestAnimationFrame(() => r()));
                      }
                      window.scrollTo(0, 0);
                    }""")
                    await page.wait_for_function(
                        "() => Array.from(document.images).every(i => i.complete && i.naturalWidth > 0)",
                        timeout=60000,
                    )
                    await page.wait_for_load_state("networkidle")
                output.parent.mkdir(parents=True, exist_ok=True)
                await page.screenshot(path=str(output), full_page=full_page, animations="disabled")
                diagnostics = await page.evaluate("""() => ({
                  title: document.title,
                  scrollWidth: document.documentElement.scrollWidth,
                  clientWidth: document.documentElement.clientWidth,
                  scrollHeight: document.documentElement.scrollHeight,
                  h1Count: document.querySelectorAll('h1').length,
                  landmarks: ['header', 'nav', 'main', 'footer'].filter((name) => document.querySelector(name)),
                  emptyLinks: [...document.querySelectorAll('a')].filter((element) => !(element.textContent || '').trim() && !element.getAttribute('aria-label')).length,
                  unnamedButtons: [...document.querySelectorAll('button')].filter((element) => !(element.textContent || '').trim() && !element.getAttribute('aria-label') && !element.getAttribute('aria-labelledby')).length,
                  unlabeledInputs: [...document.querySelectorAll('input,select,textarea')].filter((element) => !element.labels?.length && !element.getAttribute('aria-label') && !element.getAttribute('aria-labelledby')).length,
                  imagesMissingAlt: [...document.querySelectorAll('img')].filter((element) => !element.hasAttribute('alt')).length,
                  duplicateIds: [...document.querySelectorAll('[id]')].map((element) => element.id).filter((id, index, ids) => ids.indexOf(id) !== index),
                })""")
            finally:
                await browser.close()
        structural_failures = diagnostics["h1Count"] != 1 or diagnostics["emptyLinks"] > 0 or diagnostics["unnamedButtons"] > 0 or diagnostics["unlabeledInputs"] > 0 or diagnostics["imagesMissingAlt"] > 0 or bool(diagnostics["duplicateIds"])
        report = {"status": "FAIL" if console_errors or failed_requests or diagnostics["scrollWidth"] > diagnostics["clientWidth"] + 1 or structural_failures else "PASS", "checkedAt": now(), "viewport": {"width": width, "height": height, "scale": scale}, "output": str(output), "diagnostics": diagnostics, "consoleErrors": console_errors, "failedRequests": failed_requests}
        pretty = json.dumps(report, indent=2) + "\n"
        compact = json.dumps(report, separators=(",", ":")) + "\n"
        Path(f"{output}.json").write_text(pretty, encoding="utf-8")
        sys.stdout.write(compact)
        return 0 if report["status"] == "PASS" else 2
    finally:
        server.shutdown()
        server.server_close()


if __name__ == "__main__":
    try:
        raise SystemExit(asyncio.run(_render(options(sys.argv[1:]))))
    except Exception as error:
        raise SystemExit(str(error))
