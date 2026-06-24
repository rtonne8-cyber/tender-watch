"""Orchestrator: fetch all Tier 3 trade-press signals, write data/signals.json.

Deliberately separate from run.py and the relevance scorer (see CLAUDE.md) —
signals are never scored and never enter the tenders.json notices path.
"""

import json
from pathlib import Path

from fetchers.news_signals import fetch_all

DATA_PATH = Path(__file__).parent / "data" / "signals.json"


def run():
    records, summary = fetch_all()

    DATA_PATH.parent.mkdir(parents=True, exist_ok=True)
    with open(DATA_PATH, "w", encoding="utf-8") as f:
        json.dump(records, f, indent=2, ensure_ascii=False)

    print(f"Wrote {len(records)} signal records to {DATA_PATH}")
    for name, stats in summary.items():
        print(f"  {name}: fetched={stats['fetched']} status={stats['status']}")

    return records, summary


if __name__ == "__main__":
    run()
