"""Shared run-history logger, used by both run.py and run_signals.py.

Generic and tier-agnostic — just appends a tagged summary entry, capped at
MAX_ENTRIES. Has no notion of tender relevance, so importing it from the
Tier 3 path doesn't reintroduce a shared dependency (see CLAUDE.md).
"""

import json
from datetime import datetime, timezone
from pathlib import Path

HISTORY_PATH = Path(__file__).parent / "data" / "run_history.json"
MAX_ENTRIES = 25


def record_run(kind, summary):
    entry = {
        "timestamp": datetime.now(timezone.utc).isoformat(),
        "kind": kind,
        "summary": summary,
    }

    history = []
    if HISTORY_PATH.exists():
        try:
            history = json.loads(HISTORY_PATH.read_text(encoding="utf-8"))
        except (json.JSONDecodeError, OSError):
            history = []

    history.insert(0, entry)
    history = history[:MAX_ENTRIES]

    HISTORY_PATH.parent.mkdir(parents=True, exist_ok=True)
    HISTORY_PATH.write_text(json.dumps(history, indent=2, ensure_ascii=False), encoding="utf-8")
    return entry
