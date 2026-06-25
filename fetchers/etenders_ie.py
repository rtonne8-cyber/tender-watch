"""Tier 1 fetcher: eTenders Ireland.

NOTE: eTenders Ireland does not expose a live OCDS API publicly (verified June
2026 — the only OCDS feed for Ireland is a static OCP Data Registry bulk archive
last covering 2023). The live substitute used here is the Office of Government
Procurement's official open-data CSV export, which is regenerated from eTenders
and re-downloaded fresh on every run.
"""

import csv
import io
import os
import sys
from datetime import datetime, timedelta, timezone

sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from fetchers.common import fetch_bytes

CSV_URL = "https://assets.gov.ie/static/documents/2fb1e069/Public_Procurement_Opendata_Dataset.csv"
SOURCE = "etenders_ie"
RECENT_DAYS = 120
MAX_RECORDS = 500


def _parse_date(value):
    if not value:
        return None
    try:
        return datetime.strptime(value.strip(), "%d/%m/%Y").replace(tzinfo=timezone.utc)
    except ValueError:
        return None


def _parse_amount(value):
    if not value:
        return None
    cleaned = value.replace(",", "").strip()
    try:
        return float(cleaned)
    except ValueError:
        return None


def fetch():
    raw = fetch_bytes(CSV_URL)
    text = raw.decode("cp1252")
    reader = csv.DictReader(io.StringIO(text))

    cutoff = datetime.now(timezone.utc) - timedelta(days=RECENT_DAYS)
    rows = []
    for row in reader:
        # Pipeline/tender stage only — this CSV mixes notice and award/
        # cancellation info in the same row (no separate OCDS-style stage
        # field), so a populated "Award Published" or "Cancelled Date"
        # means it's already past the stage this project tracks.
        if row.get("Award Published") or row.get("Cancelled Date"):
            continue
        published = _parse_date(row.get("Notice Published Date / Contract Created Date"))
        if published is None or published < cutoff:
            continue
        rows.append((published, row))

    rows.sort(key=lambda pair: pair[0], reverse=True)
    rows = rows[:MAX_RECORDS]

    records = []
    for published, row in rows:
        cpv_codes = sorted(
            {c for c in (row.get("Additional CPV Codes on CFT") or "").split(";") if c}
            | ({row["Main Cpv Code"]} if row.get("Main Cpv Code") else set())
        )
        deadline = _parse_date(row.get("Tender Submission Deadline"))
        records.append(
            {
                "id": f"{SOURCE}-{row.get('Tender ID')}",
                "source": SOURCE,
                "tier": 1,
                "title": row.get("Tender/Contract Name") or "(untitled)",
                "buyer": row.get("Contracting Authority") or "(unknown buyer)",
                "description": row.get("Main Cpv Code Description") or "",
                "cpv_codes": cpv_codes,
                "primary_cpv": row.get("Main Cpv Code") or None,
                "value_low": _parse_amount(row.get("Sum of Notice Estimated Value (\x80)")),
                "value_high": None,
                "currency": "EUR",
                "published_date": published.isoformat(),
                "deadline_date": deadline.isoformat() if deadline else None,
                "url": row.get("TED Notice Link") or "https://www.etenders.gov.ie/epps/cft/quickSearchAction.do",
            }
        )
    return records


if __name__ == "__main__":
    records = fetch()
    print(f"{SOURCE}: fetched {len(records)} records")
    if not records:
        print("ERROR: no records returned", file=sys.stderr)
        sys.exit(1)
    print("Sample record:")
    print(records[0])
