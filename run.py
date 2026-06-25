"""Orchestrator: run all Tier 1 fetchers, score the results, write data/tenders.json.

A broken source is logged and skipped — it must never fail the whole run.
"""

import json
import sys
from pathlib import Path

from fetchers import contracts_finder, etenders_ie, fts
from history import record_run
from scoring.relevance import score_records

DATA_PATH = Path(__file__).parent / "data" / "tenders.json"

TIER1_FETCHERS = [
    ("find_a_tender", fts.fetch),
    ("contracts_finder", contracts_finder.fetch),
    ("etenders_ie", etenders_ie.fetch),
]


def run():
    all_records = []
    summary = {}

    for name, fetch_fn in TIER1_FETCHERS:
        try:
            records = fetch_fn()
            summary[name] = {"fetched": len(records), "status": "ok"}
            all_records.extend(records)
        except Exception as exc:  # noqa: BLE001 - one broken source must not kill the run
            print(f"[run] {name} failed, skipping: {exc}", file=sys.stderr)
            summary[name] = {"fetched": 0, "status": f"error: {exc}"}

    scored = score_records(all_records)
    for name in summary:
        summary[name]["scored"] = sum(1 for r in scored if r["source"] == name)

    DATA_PATH.parent.mkdir(parents=True, exist_ok=True)
    with open(DATA_PATH, "w", encoding="utf-8") as f:
        json.dump(scored, f, indent=2, ensure_ascii=False)

    print(f"Wrote {len(scored)} scored records to {DATA_PATH}")
    for name, stats in summary.items():
        print(f"  {name}: fetched={stats['fetched']} scored={stats.get('scored', 0)} status={stats['status']}")

    record_run("tenders", {"scored_count": len(scored), "sources": summary})

    return scored, summary


if __name__ == "__main__":
    run()
