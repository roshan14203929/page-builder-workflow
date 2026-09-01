#!/usr/bin/env python3
"""Measure MediChannel conclusion/footer geometry in a deterministic viewport."""

from __future__ import annotations

import asyncio
import json
import sys
import threading
from pathlib import Path

from playwright.async_api import async_playwright

from render_page import local_server, options


async def main(args: dict[str, str]) -> int:
    if not args.get("root"):
        raise ValueError("Usage: measure-footer.py --root <site-dir> [--width 988]")
    root = Path(args["root"]).resolve()
    width, height = int(args.get("width", "988")), int(args.get("height", "800"))
    entry = args.get("entry", "index.html")
    server = local_server(root, entry)
    thread = threading.Thread(target=server.serve_forever, daemon=True)
    thread.start()
    try:
        async with async_playwright() as playwright:
            browser = await playwright.chromium.launch(headless=True)
            try:
                page = await browser.new_page(viewport={"width": width, "height": height}, device_scale_factor=1)
                response = await page.goto(f"http://127.0.0.1:{server.server_port}/{entry}", wait_until="networkidle")
                if response is None or not response.ok:
                    status = response.status if response is not None else "unknown"
                    raise ValueError(f"Preview returned HTTP {status}.")
                await page.emulate_media(reduced_motion="reduce")
                await page.evaluate("() => document.fonts?.ready")
                measurements = await page.evaluate("""() => {
                  const conclusionEl = document.querySelector('.cst-conclusion');
                  const backToTopEl = document.querySelector('.cst-back-to-top');
                  return {
                    scrollHeight: document.documentElement.scrollHeight,
                    conclusionOffsetTop: conclusionEl?.offsetTop,
                    conclusionOffsetHeight: conclusionEl?.offsetHeight,
                    conclusionBottom: conclusionEl ? conclusionEl.offsetTop + conclusionEl.offsetHeight : null,
                    backToTopOffsetTop: backToTopEl?.offsetTop,
                    backToTopOffsetHeight: backToTopEl?.offsetHeight,
                  };
                }""")
                print(json.dumps({"viewport": {"width": width, "height": height}, "measurements": measurements}, indent=2))
                return 0
            finally:
                await browser.close()
    finally:
        server.shutdown()
        server.server_close()


if __name__ == "__main__":
    try:
        raise SystemExit(asyncio.run(main(options(sys.argv[1:]))))
    except Exception as error:
        raise SystemExit(str(error))
