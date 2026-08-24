#!/usr/bin/env python3
"""
Download OMIM entries via the official JSON API (https://omim.org/help/api).

Auth: set OMIM_API_KEY in env/.env (HTTP header ``ApiKey``). Optional URLs for
documentation live in OMIM_API_BASE_URL, OMIM_API_DOCS_URL, OMIM_API_HTML_URL.

Pipeline:
  1. Paginate ``/entry/search`` (SOLR) to collect MIM numbers.
  2. Batch-fetch ``/entry`` with ``include=text:description`` (max 20 MIMs per
     request when includes are present — see API limits).

Rate limits: on HTTP 429 the client sleeps with exponential backoff and retries.

Usage:
  python scripts/acquire.py --output tmp/omim_raw.json
"""

from __future__ import annotations

import argparse
import hashlib
import json
import os
import sys
import time
from pathlib import Path

import requests
from dotenv import load_dotenv

REPO_ROOT = Path(__file__).resolve().parent.parent
CACHE_DIR = REPO_ROOT / "tmp" / "cache" / "entry_batches"


def _optional_sleep_after_http() -> None:
    """Pace requests if ``OMIM_SLEEP_SECONDS`` is set (reduces 429 during large pulls)."""
    raw = os.environ.get("OMIM_SLEEP_SECONDS", "").strip()
    if not raw:
        return
    try:
        sec = float(raw)
    except ValueError:
        return
    if sec > 0:
        time.sleep(sec)


def _load_env() -> None:
    """Load credentials from ``env/.env`` and/or repo-root ``.env`` (later overrides).

    Uses ``override=True`` so file values win over a stale or empty key
    exported in the shell (python-dotenv defaults to ``override=False``, which skips
    loading the key from disk when the variable is already set).
    """
    for path in (REPO_ROOT / "env" / ".env", REPO_ROOT / ".env"):
        if path.is_file():
            load_dotenv(path, override=True)
    load_dotenv(override=True)


def _api_key() -> str:
    """Prefer OMIM_API_KEY; fall back to legacy API_KEY (same GitHub secret / root .env)."""
    for name in ("OMIM_API_KEY", "API_KEY"):
        key = os.environ.get(name)
        if key and str(key).strip():
            return str(key).strip()
    print(
        "ERROR: No API key found. Set OMIM_API_KEY or legacy API_KEY "
        "(root .env as used by omim2obo, or env/.env).",
        file=sys.stderr,
    )
    sys.exit(1)


def _base_url() -> str:
    u = os.environ.get("OMIM_API_BASE_URL", "").strip()
    if not u:
        # Same host legacy OmimClient uses; no new secret/setting required.
        u = "https://api.omim.org/api"
    return u.rstrip("/")


def _headers() -> dict[str, str]:
    return {
        "ApiKey": _api_key(),
        "Accept": "application/json",
        "Accept-Encoding": "gzip",
    }


def _unwrap_omim_payload(data: dict) -> dict:
    """OMIM JSON often nests under an ``omim`` key."""
    if "omim" in data and isinstance(data["omim"], dict):
        return data["omim"]
    return data


def _coerce_entry_list(el: object) -> list[dict]:
    """Normalize ``entryList``: list of dicts, ``{entry: [...]}``, or ``[{entry: {...}}]``."""
    if el is None:
        return []
    if isinstance(el, list):
        out: list[dict] = []
        for x in el:
            if not isinstance(x, dict):
                continue
            inner = x.get("entry")
            if isinstance(inner, dict):
                out.append(inner)
            elif "mimNumber" in x:
                out.append(x)
        return out
    if isinstance(el, dict):
        raw = el.get("entry")
        if raw is None:
            return []
        if isinstance(raw, list):
            return _coerce_entry_list(raw)
        if isinstance(raw, dict):
            return [raw]
    return []


def _normalize_entry_list(container: dict | list | None) -> list[dict]:
    if container is None:
        return []
    if isinstance(container, list):
        return [x for x in container if isinstance(x, dict)]
    el = container.get("entryList") or container.get("listResponse")
    return _coerce_entry_list(el)


def _search_page(
    session: requests.Session,
    base: str,
    *,
    search: str,
    filter_expr: str | None,
    start: int,
    limit: int,
) -> tuple[list[dict], int, str | None]:
    """Return (entries from search hit list, totalResults, omim.version if present)."""
    params: list[tuple[str, str | int]] = [
        ("search", search),
        ("start", start),
        ("limit", limit),
        ("format", "json"),
        ("sort", "number asc"),
    ]
    if filter_expr:
        params.append(("filter", filter_expr))
    r = session.get(f"{base}/entry/search", params=params, timeout=120)
    if r.status_code == 429:
        raise RuntimeError("429")
    if r.status_code == 401:
        print("ERROR: 401 Unauthorized — check OMIM_API_KEY.", file=sys.stderr)
        sys.exit(1)
    r.raise_for_status()
    data = r.json()
    top_version = None
    if isinstance(data.get("omim"), dict):
        top_version = data["omim"].get("version")
    omim = _unwrap_omim_payload(data)
    sr = omim.get("searchResponse") or omim
    entries = _normalize_entry_list(sr if isinstance(sr, dict) else None)
    total = int(sr.get("totalResults") or 0) if isinstance(sr, dict) else 0
    ver = top_version if top_version is not None else omim.get("version")
    _optional_sleep_after_http()
    return entries, total, str(ver) if ver is not None else None


def _fetch_entry_batch(
    session: requests.Session,
    base: str,
    mim_numbers: list[str],
    *,
    use_cache: bool,
) -> list[dict]:
    """Fetch full entry payload for up to ``len(mim_numbers)`` MIMs (includes => max 20)."""
    if not mim_numbers:
        return []
    key_src = ",".join(sorted(mim_numbers))
    digest = hashlib.sha256(key_src.encode()).hexdigest()[:24]
    cache_path = CACHE_DIR / f"{digest}.json"
    if use_cache and cache_path.exists():
        with open(cache_path, encoding="utf-8") as f:
            cached = json.load(f)
        raw = cached.get("entry")
        if isinstance(raw, list):
            return [x for x in raw if isinstance(x, dict)]
        if isinstance(raw, dict):
            return [raw]
        return []

    params: list[tuple[str, str]] = [
        ("mimNumber", ",".join(mim_numbers)),
        ("include", "text:description"),
        ("include", "text:clinicalFeatures"),
        ("format", "json"),
    ]
    r = session.get(f"{base}/entry", params=params, timeout=120)
    if r.status_code == 429:
        raise RuntimeError("429")
    r.raise_for_status()
    data = r.json()
    omim = _unwrap_omim_payload(data)
    er = omim.get("entryResponse") or omim
    if isinstance(er, dict):
        entries = _normalize_entry_list(er)
    elif isinstance(er, list):
        entries = _normalize_entry_list(er)
    else:
        entries = []
    if not entries:
        entries = _normalize_entry_list(omim)

    cache_path.parent.mkdir(parents=True, exist_ok=True)
    with open(cache_path, "w", encoding="utf-8") as f:
        json.dump({"entry": entries}, f)

    _optional_sleep_after_http()
    return entries


def _retry_loop(fn, *, max_retries: int) -> object:
    delay = 30.0
    for attempt in range(max_retries):
        try:
            return fn()
        except RuntimeError as e:
            if str(e) != "429" and "429" not in str(e):
                raise
        print(f"  rate limited (429); sleeping {delay:.0f}s ...", file=sys.stderr)
        time.sleep(delay)
        delay = min(delay * 1.5, 600.0)
    raise RuntimeError("too many 429 responses")


def _429_max_retries() -> int:
    """How many times to retry after HTTP 429 per request (env ``OMIM_429_MAX_RETRIES``)."""
    raw = os.environ.get("OMIM_429_MAX_RETRIES", "").strip()
    if not raw:
        return 24
    try:
        n = int(raw)
    except ValueError:
        print("ERROR: OMIM_429_MAX_RETRIES must be an integer", file=sys.stderr)
        sys.exit(1)
    if n < 1:
        print("ERROR: OMIM_429_MAX_RETRIES must be >= 1", file=sys.stderr)
        sys.exit(1)
    return n


def main() -> None:
    _load_env()

    parser = argparse.ArgumentParser(description="Acquire OMIM entries via api.omim.org")
    parser.add_argument("--output", type=Path, required=True, help="Output JSON path")
    parser.add_argument(
        "--page-size",
        type=int,
        default=500,
        help="Page size for /entry/search pagination",
    )
    parser.add_argument(
        "--detail-batch",
        type=int,
        default=20,
        help="MIM numbers per /entry request (max 20 when includes are used)",
    )
    parser.add_argument(
        "--no-cache",
        action="store_true",
        help="Do not read/write tmp/cache/entry_batches",
    )
    parser.add_argument(
        "--max-mims",
        type=int,
        default=None,
        metavar="N",
        help="Cap: first N MIMs after search (early stop; env OMIM_MAX_MIMS if unset)",
    )
    args = parser.parse_args()

    max_mims: int | None = args.max_mims
    if max_mims is None:
        env_raw = os.environ.get("OMIM_MAX_MIMS", "").strip()
        if env_raw:
            try:
                max_mims = int(env_raw)
            except ValueError:
                print("ERROR: OMIM_MAX_MIMS must be an integer", file=sys.stderr)
                sys.exit(1)

    if max_mims is not None and max_mims < 1:
        print(
            "ERROR: --max-mims / OMIM_MAX_MIMS must be >= 1",
            file=sys.stderr,
        )
        sys.exit(1)

    base = _base_url()
    search_q = os.environ.get("OMIM_SEARCH_QUERY", "*").strip()
    filter_q = os.environ.get("OMIM_SEARCH_FILTER", "").strip() or None

    session = requests.Session()
    session.headers.update(_headers())
    max_429 = _429_max_retries()

    print(
        f"Listing MIM numbers via search (query={search_q!r} filter={filter_q!r}) ...",
        file=sys.stderr,
    )
    if max_mims is not None:
        print(f"  stopping search after {max_mims} distinct MIM numbers", file=sys.stderr)

    mim_order: list[str] = []
    seen: set[str] = set()
    start = 0
    total = None
    api_version: str | None = None
    stop_search = False
    while not stop_search:
        entries, page_total, page_ver = _retry_loop(
            lambda: _search_page(
                session,
                base,
                search=search_q,
                filter_expr=filter_q,
                start=start,
                limit=args.page_size,
            ),
            max_retries=max_429,
        )
        if api_version is None and page_ver:
            api_version = page_ver
        if total is None:
            total = page_total
            print(f"  totalResults (reported): {total}", file=sys.stderr)

        for ent in entries:
            raw = ent.get("mimNumber")
            if raw is None:
                continue
            m = str(raw).strip()
            if m and m not in seen:
                seen.add(m)
                mim_order.append(m)
            if max_mims is not None and len(mim_order) >= max_mims:
                stop_search = True
                break

        if stop_search:
            break
        if not entries:
            break
        start += len(entries)
        if total is not None and start >= total:
            break
        if len(entries) < args.page_size:
            break

    print(f"  unique MIM numbers collected: {len(mim_order)}", file=sys.stderr)

    use_cache = not args.no_cache
    all_entries: dict[str, dict] = {}
    batch_n = max(1, min(20, args.detail_batch))

    for i in range(0, len(mim_order), batch_n):
        chunk = mim_order[i : i + batch_n]
        rows = _retry_loop(
            lambda c=chunk: _fetch_entry_batch(
                session, base, c, use_cache=use_cache
            ),
            max_retries=max_429,
        )
        for ent in rows:
            raw = ent.get("mimNumber")
            if raw is None:
                continue
            mid = str(raw).strip()
            if mid:
                all_entries[mid] = ent
        if (i // batch_n) % 50 == 0:
            done = min(i + batch_n, len(mim_order))
            total_n = len(mim_order)
            print(f"  detail fetch progress: {done}/{total_n}", file=sys.stderr)

    release_id = api_version or "unknown"

    out_doc = {
        "release_id": release_id,
        "api_base_url": base,
        "api_docs_url": os.environ.get("OMIM_API_DOCS_URL", ""),
        "api_html_url": os.environ.get("OMIM_API_HTML_URL", ""),
        "search_query": search_q,
        "search_filter": filter_q,
        "entities": all_entries,
    }

    args.output.parent.mkdir(parents=True, exist_ok=True)
    with open(args.output, "w", encoding="utf-8") as f:
        json.dump(out_doc, f, indent=2)

    print(f"Wrote {args.output} ({len(all_entries)} entries)", file=sys.stderr)


if __name__ == "__main__":
    main()
