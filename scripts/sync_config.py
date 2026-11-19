#!/usr/bin/env python3
"""Fetch one FongMi configuration and prepare it for GitHub Pages."""
from __future__ import annotations

import json
import re
import sys
import urllib.error
import urllib.request
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
UPSTREAM_FILE = ROOT / "upstream.txt"
OUTPUT_FILE = ROOT / "site" / "tv.json"
USER_AGENT = "okhttp/5.5.1"


def fail(message: str) -> None:
    print(f"Sync stopped: {message}", file=sys.stderr)
    raise SystemExit(1)


def main() -> None:
    url = UPSTREAM_FILE.read_text(encoding="utf-8").strip()
    if not url.startswith(("http://", "https://")):
        fail("upstream.txt must contain one http:// or https:// URL")

    request = urllib.request.Request(
        url,
        headers={
            "User-Agent": USER_AGENT,
            "Accept": "application/json, text/plain, */*",
            "Cache-Control": "no-cache",
        },
    )
    try:
        with urllib.request.urlopen(request, timeout=40) as response:
            status = response.status
            final_url = response.geturl()
            raw = response.read(8_000_001)
    except (urllib.error.URLError, TimeoutError) as exc:
        fail(f"upstream request failed: {exc}")

    if status != 200:
        fail(f"upstream returned HTTP {status}")
    if len(raw) > 8_000_000:
        fail("upstream response is larger than 8 MB")
    if not raw:
        fail("upstream returned an empty response")

    try:
        text = raw.decode("utf-8-sig").strip()
    except UnicodeDecodeError as exc:
        fail(f"upstream response is not UTF-8 text: {exc}")

    # FongMi supports this encrypted text format. Pass it through unchanged
    # after checking its shape; FongMi decrypts it when it loads tv.json.
    compact = re.sub(r"\s+", "", text)
    if compact.startswith("2423"):
        if len(compact) % 2 or not re.fullmatch(r"2423[0-9a-fA-F]+", compact):
            fail("response starts like an encrypted config but is not valid hex text")
        output = compact + "\n"
        kind = "FongMi encrypted config"
    else:
        try:
            config = json.loads(text)
        except json.JSONDecodeError as exc:
            fail(f"response is not a JSON config (often a navigation page): {exc}")
        if not isinstance(config, dict):
            fail("JSON root must be an object")
        if "urls" in config:
            fail("upstream is a multi-repository navigation list; choose a single config URL")
        if not any(key in config for key in ("sites", "lives", "spider", "parses")):
            fail("JSON does not look like a FongMi single-repository config")
        output = json.dumps(config, ensure_ascii=False, indent=2) + "\n"
        kind = "FongMi single-repository JSON"

    OUTPUT_FILE.parent.mkdir(parents=True, exist_ok=True)
    OUTPUT_FILE.write_text(output, encoding="utf-8")
    print(f"Prepared {kind}: HTTP {status}; final response URL: {final_url}")
    print(f"Wrote {OUTPUT_FILE.relative_to(ROOT)} ({len(output.encode('utf-8'))} bytes)")


if __name__ == "__main__":
    main()
