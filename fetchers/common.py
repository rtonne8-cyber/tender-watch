"""Shared HTTP and record-normalisation helpers for Tier 1/2 fetchers."""

import sys
import time

import requests

USER_AGENT = (
    "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 "
    "(KHTML, like Gecko) Chrome/124.0 Safari/537.36 TenderWatch/1.0"
)

DEFAULT_TIMEOUT = 30
MAX_RETRIES = 3


def fetch_json(url, params=None, timeout=DEFAULT_TIMEOUT, retries=MAX_RETRIES):
    """GET a JSON endpoint with retries. Raises on final failure."""
    last_exc = None
    for attempt in range(1, retries + 1):
        try:
            resp = requests.get(
                url,
                params=params,
                headers={"User-Agent": USER_AGENT, "Accept": "application/json"},
                timeout=timeout,
            )
            resp.raise_for_status()
            return resp.json()
        except Exception as exc:  # noqa: BLE001 - log and retry
            last_exc = exc
            print(f"  [retry {attempt}/{retries}] {url} -> {exc}", file=sys.stderr)
            if attempt < retries:
                time.sleep(2 * attempt)
    raise RuntimeError(f"Failed to fetch {url} after {retries} attempts: {last_exc}")


def fetch_ocds_releases(url, params, max_records=500, max_pages=10):
    """Page through an OCDS releases endpoint via its links.next cursor."""
    releases = []
    payload = fetch_json(url, params=params)
    releases.extend(payload.get("releases", []))
    pages = 1
    next_url = (payload.get("links") or {}).get("next")
    while next_url and len(releases) < max_records and pages < max_pages:
        payload = fetch_json(next_url)
        page_releases = payload.get("releases", [])
        if not page_releases:
            break
        releases.extend(page_releases)
        next_url = (payload.get("links") or {}).get("next")
        pages += 1
    return releases[:max_records]


def fetch_bytes(url, timeout=60, retries=MAX_RETRIES):
    """GET raw bytes (e.g. a CSV) with a browser-like UA and retries."""
    last_exc = None
    for attempt in range(1, retries + 1):
        try:
            resp = requests.get(
                url,
                headers={"User-Agent": USER_AGENT},
                timeout=timeout,
            )
            resp.raise_for_status()
            return resp.content
        except Exception as exc:  # noqa: BLE001
            last_exc = exc
            print(f"  [retry {attempt}/{retries}] {url} -> {exc}", file=sys.stderr)
            if attempt < retries:
                time.sleep(2 * attempt)
    raise RuntimeError(f"Failed to fetch {url} after {retries} attempts: {last_exc}")


def normalise_ocds_release(release, source, tier=1, url_builder=None):
    """Map a single OCDS release dict to the internal tender record schema."""
    tender = release.get("tender", {}) or {}
    classification = tender.get("classification", {}) or {}
    value = tender.get("value", {}) or {}
    tender_period = tender.get("tenderPeriod", {}) or {}
    buyer = release.get("buyer", {}) or {}

    cpv_codes = []
    if classification.get("scheme") == "CPV" and classification.get("id"):
        cpv_codes.append(classification["id"])
    for item in tender.get("items", []) or []:
        for extra in item.get("additionalClassifications", []) or []:
            if extra.get("scheme") == "CPV" and extra.get("id"):
                cpv_codes.append(extra["id"])
    cpv_codes = sorted(set(cpv_codes))

    record_id = f"{source}-{release.get('id') or release.get('ocid')}"
    notice_url = url_builder(release) if url_builder else None

    return {
        "id": record_id,
        "source": source,
        "tier": tier,
        "title": tender.get("title") or release.get("description", "")[:120] or "(untitled)",
        "buyer": buyer.get("name") or "(unknown buyer)",
        "description": tender.get("description") or release.get("description") or "",
        "cpv_codes": cpv_codes,
        "value_low": value.get("amount"),
        "value_high": None,
        "currency": value.get("currency"),
        "published_date": release.get("date"),
        "deadline_date": tender_period.get("endDate"),
        "url": notice_url,
    }
