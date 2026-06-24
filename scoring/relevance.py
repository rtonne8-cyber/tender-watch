"""Two-pass T&D-sector relevance scoring.

Pass 1 (free): CPV allowlist + keyword regex pre-filter.
Pass 2 (paid, ambiguous band only): Claude Haiku relevance gate.

Hard rule (see CLAUDE.md): this module calls a single explicit Haiku model
string below, via the plain `anthropic` Python SDK and a plain
ANTHROPIC_API_KEY environment variable. Only that one model string belongs
in this file.
"""

import json
import os
import re
import sys
from datetime import datetime, timezone
from pathlib import Path

import yaml
from anthropic import Anthropic

HAIKU_MODEL = "claude-haiku-4-5-20251001"

CPV_SCORE = 90
KEYWORD_MATCH_SCORE_FLOOR = 40  # ambiguous band floor before the Haiku gate
KEYWORDS_PATH = Path(__file__).parent / "keywords.yaml"


def _load_keywords():
    with open(KEYWORDS_PATH, "r", encoding="utf-8") as f:
        data = yaml.safe_load(f)
    cpv_allowlist = set(data.get("cpv_allowlist", []))
    patterns = [re.compile(p, re.IGNORECASE) for p in data.get("keywords", [])]
    return cpv_allowlist, patterns


_CPV_ALLOWLIST, _KEYWORD_PATTERNS = _load_keywords()


def _cpv_match(record):
    return bool(_CPV_ALLOWLIST.intersection(record.get("cpv_codes") or []))


def _keyword_match(record):
    text = f"{record.get('title', '')} {record.get('description', '')}"
    return any(p.search(text) for p in _KEYWORD_PATTERNS)


def _haiku_gate(record, client):
    prompt = (
        "You are screening a UK/Ireland public procurement notice for relevance "
        "to the electricity transmission & distribution (T&D) engineering sector "
        "(substations, transmission/distribution networks, switchgear, cabling, "
        "grid connections, protection, EHV/HV plant). Respond with ONLY a JSON "
        "object: {\"relevant\": true|false, \"score\": <0-100 integer>}.\n\n"
        f"Title: {record.get('title')}\n"
        f"Buyer: {record.get('buyer')}\n"
        f"Description: {(record.get('description') or '')[:800]}"
    )
    response = client.messages.create(
        model=HAIKU_MODEL,
        max_tokens=50,
        messages=[{"role": "user", "content": prompt}],
    )
    text = response.content[0].text.strip()
    try:
        parsed = json.loads(text)
        return int(parsed.get("score", 0))
    except (json.JSONDecodeError, ValueError, TypeError):
        print(f"  [haiku] unparseable response, defaulting to 0: {text!r}", file=sys.stderr)
        return 0


def score_records(records, anthropic_api_key=None):
    """Score a list of normalised tender records. Returns only records that
    clear the relevance bar, each with score/score_method/scored_at added."""
    api_key = anthropic_api_key or os.environ.get("ANTHROPIC_API_KEY")
    client = Anthropic(api_key=api_key) if api_key else None

    scored = []
    now = datetime.now(timezone.utc).isoformat()

    for record in records:
        if _cpv_match(record):
            record["score"] = CPV_SCORE
            record["score_method"] = "cpv_match"
        elif _keyword_match(record):
            if client is None:
                print(
                    f"  [skip] {record['id']}: ambiguous but no ANTHROPIC_API_KEY set",
                    file=sys.stderr,
                )
                continue
            score = _haiku_gate(record, client)
            if score < KEYWORD_MATCH_SCORE_FLOOR:
                continue
            record["score"] = score
            record["score_method"] = "haiku_gate"
        else:
            continue  # not relevant, discard

        record["scored_at"] = now
        scored.append(record)

    return scored
