# TenderWatch

A live dashboard of new T&D (electricity transmission & distribution) relevant
tender notices from UK/Ireland public procurement, plus early trade-press
signals — built to remove manual portal-checking.

## Architecture

Three tiers, deliberately structurally separate:

- **Tier 1 — confirmed notices, OCDS APIs.** [Find a Tender](https://www.find-tender.service.gov.uk/)
  and [Contracts Finder](https://www.contractsfinder.service.gov.uk/) (UK), and
  [eTenders Ireland](https://www.etenders.gov.ie/) (via the Office of
  Government Procurement's open-data CSV — eTenders has no public live OCDS
  API; the CSV is the genuine live substitute, refreshed on every run).
  Two-pass relevance scoring: a free CPV-allowlist/keyword pre-filter, then a
  Claude Haiku gate on the ambiguous band (`scoring/relevance.py` —
  always an explicit `claude-haiku-*` model string via the plain `anthropic`
  SDK and `ANTHROPIC_API_KEY`, never the Agent SDK, never Sonnet).
- **Tier 2 — PCS Scotland — parked, not built.** No public RSS/API exists for
  PCS Scotland notices (only a generic News RSS is documented; the actual
  notices search is a heavy classic ASP.NET WebForms postback app with a
  multi-MB ViewState and no stable feed). Revisit if a real feed surfaces.
- **Tier 3 — trade-press signals, RSS.** Utility Week, reNEWS, Utility Dive,
  and Energy Live News (substituting for Current±, which is discontinued).
  Signals only — `data/signals.json` has a completely different schema (no
  `score`/`cpv_codes`/`tier`) from `data/tenders.json`, is written by a
  separate orchestrator (`run_signals.py`) that never imports the relevance
  scorer, and renders in its own dashboard section. A Tier 3 item cannot
  become a notice — by construction, not by UI hiding.

Every fetcher wraps its source in its own try/except: one broken source is
logged and skipped, the run never fails wholesale.

## Repo layout

```
fetchers/          Tier 1 OCDS fetchers + Tier 3 RSS fetcher + shared HTTP helpers
scoring/           Two-pass relevance scorer + CPV/keyword/sector config
run.py             Orchestrator: Tier 1 fetchers -> scoring -> data/tenders.json
run_signals.py     Orchestrator: Tier 3 RSS -> data/signals.json
data/              tenders.json (confirmed notices) + signals.json (Tier 3 only)
dashboard/         Vite + React dashboard
.github/workflows/refresh.yml   workflow_dispatch only — no cron, no schedule
CLAUDE.md          Build guardrails / locked scope / hard rules
```

## Setup

```bash
pip install -r requirements.txt
cp .env.example .env   # add your ANTHROPIC_API_KEY
cd dashboard && npm install
```

## Running locally

```bash
python run.py            # Tier 1 fetch + score -> data/tenders.json
python run_signals.py    # Tier 3 fetch -> data/signals.json
cd dashboard && npm run dev   # copies both data files into public/, starts Vite
```

Without `ANTHROPIC_API_KEY` set, records that only clear the keyword
pre-filter (not the CPV allowlist) are skipped rather than scored — set the
key to get full coverage.

## Dashboard filters

Six independent filters on the notices table (none apply to the Tier 3
signals section, which is intentionally separate): source, tier, sector,
minimum score, deadline-within-N-days, and new-since-last-visit (tracked via
`localStorage`). Filter logic lives in `dashboard/src/filters.js` as a pure
`filterRecords()` function; `dashboard/scripts/verify-filters.mjs` is a
standalone independence check against synthetic data (`node
dashboard/scripts/verify-filters.mjs`).

## CI

`.github/workflows/refresh.yml` runs on `workflow_dispatch` only — no cron, no
scheduled runs, by design (deliberate low-volume manual trigger, not an
oversight). It installs dependencies, runs both orchestrators, and commits the
refreshed `data/*.json` using the `ANTHROPIC_API_KEY` repo secret.

## Out of scope / parked

- **PCS Scotland (Tier 2)** — no public feed found; parked, not abandoned.
- **NGET, SSEN-T, SPT, EirGrid, ESBN** — login-gated portals, no public feed.
  Not attempted.
- **The BD Pipeline Intelligence Agent** — a different project; deliberately
  kept separate.
