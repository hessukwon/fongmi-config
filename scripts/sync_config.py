#!/usr/bin/env python3
"""Fetch and validate one FongMi configuration for GitHub Pages."""
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
MAX_BYTES = 8 * 1024 * 1024


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
        with urllib.request.urlopen(request, timeout=30) as response:
            status = response.status
            final_url = response.geturl()
            content_type = response.headers.get("Content-Type", "")
            charset = response.headers.get_content_charset()
            raw = response.read(MAX_BYTES + 1)
    except (urllib.error.URLError, TimeoutError, OSError) as exc:
        fail(f"could not fetch upstream: {exc}")

    if status < 200 or status >= 300:
        fail(f"upstream returned HTTP {status}")
    if len(raw) > MAX_BYTES:
        fail(f"upstream response exceeds {MAX_BYTES} bytes")
    if not raw.strip():
        fail("upstream response is empty")

    # Keep FongMi's encrypted 2423 payload byte-for-byte after validating its form.
    if raw.startswith(b"2423"):
        encrypted = raw.decode("ascii", errors="strict").strip()
        if not re.fullmatch(r"2423[0-9a-fA-F]+", encrypted):
            fail("upstream 2423 payload is not valid hexadecimal content")
        output = encrypted + "\n"
    else:
        # Some Chinese config servers serve JSON in GBK/GB18030 without a charset.
        try:
            if raw.startswith((b"\xff\xfe", b"\xfe\xff")):
                text = raw.decode("utf-16")
            else:
                text = raw.decode(charset or "utf-8-sig")
        except (LookupError, UnicodeDecodeError):
            try:
                text = raw.decode("gb18030")
            except UnicodeDecodeError as exc:
                fail(f"upstream response is not recognizable text: {exc}")

        stripped = text.lstrip("\ufeff\r\n \t")
        if stripped.startswith("<!doctype html") or stripped.startswith("<html"):
            fail(f"upstream returned HTML instead of a config (final URL: {final_url}; {content_type})")
        try:
            data = json.loads(text)
        except json.JSONDecodeError as exc:
            fail(f"upstream is neither a 2423 payload nor valid JSON: {exc}")
        if not isinstance(data, dict):
            fail("upstream JSON root must be an object")
        if "urls" in data:
            fail("upstream returned a depot/navigation list with a top-level urls array")
        if not any(key in data for key in ("sites", "lives", "spider", "parses")):
            fail("JSON does not look like a FongMi config (expected sites/lives/spider/parses)")
        output = json.dumps(data, ensure_ascii=False, separators=(",", ":")) + "\n"

    OUTPUT_FILE.parent.mkdir(parents=True, exist_ok=True)
    OUTPUT_FILE.write_text(output, encoding="utf-8")
    print(f"Validated config: HTTP {status}; final URL {final_url}; {len(raw)} bytes")
    print(f"Wrote {OUTPUT_FILE.relative_to(ROOT)}")


if __name__ == "__main__":
    main()
