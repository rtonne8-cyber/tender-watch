"""Tier 3 fetcher: trade-press RSS signals.

These are SIGNALS, never confirmed notices. This module has no dependency on
the relevance scorer and produces a record shape with no score/cpv/tier
fields, so a signal can never be mistaken for (or slotted into) a tender
record.
"""

import hashlib
import os
import sys

import feedparser
import yaml

sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from fetchers.common import fetch_bytes

FEEDS_PATH = os.path.join(os.path.dirname(__file__), "feeds.yaml")
MAX_PER_FEED = 50


def _load_feeds():
    with open(FEEDS_PATH, "r", encoding="utf-8") as f:
        return yaml.safe_load(f)["feeds"]


def _record_id(source, entry):
    guid = entry.get("id") or entry.get("link", "")
    digest = hashlib.sha1(guid.encode("utf-8")).hexdigest()[:12]
    return f"{source}-{digest}"


def _fetch_one(name, url):
    raw = fetch_bytes(url)
    parsed = feedparser.parse(raw)
    if not parsed.entries and parsed.bozo:
        raise RuntimeError(f"not a parseable feed (bozo): {parsed.get('bozo_exception')}")
    records = []
    for entry in parsed.entries[:MAX_PER_FEED]:
        records.append(
            {
                "id": _record_id(name, entry),
                "source": name,
                "headline": entry.get("title", "(untitled)"),
                "link": entry.get("link"),
                "published_date": entry.get("published") or entry.get("updated"),
            }
        )
    return records


def fetch_all():
    """Fetch every configured feed. A broken feed is logged and skipped."""
    all_records = []
    summary = {}
    for feed in _load_feeds():
        name, url = feed["name"], feed["url"]
        try:
            records = _fetch_one(name, url)
            summary[name] = {"fetched": len(records), "status": "ok"}
            all_records.extend(records)
        except Exception as exc:  # noqa: BLE001 - one broken feed must not kill the run
            print(f"[news_signals] {name} failed, skipping: {exc}", file=sys.stderr)
            summary[name] = {"fetched": 0, "status": f"error: {exc}"}
    return all_records, summary


if __name__ == "__main__":
    records, summary = fetch_all()
    print(f"Tier 3 signals: fetched {len(records)} total")
    for name, stats in summary.items():
        print(f"  {name}: fetched={stats['fetched']} status={stats['status']}")
    if not records:
        print("ERROR: no signal records returned from any feed", file=sys.stderr)
        sys.exit(1)
    print("Sample record:")
    print(records[0])
