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
  **Stage-scoped to pipeline/planning + active tender notices only** — award,
  contract, and implementation/termination stages are explicitly excluded
  (`fts.py`/`contracts_finder.py` request `stages=planning,tender`; Find a
  Tender's API silently drops results on a comma-joined multi-stage value
  despite documenting it, so it fetches each stage separately and merges;
  `etenders_ie.py`'s CSV mixes notice and award info in the same row, so rows
  with a populated `Award Published` or `Cancelled Date` are skipped).
- **Tier 2 — PCS Scotland — parked, not built.** No public RSS/API exists for
  PCS Scotland notices (only a generic News RSS is documented; the actual
  notices search is a heavy classic ASP.NET WebForms postback app with a
  multi-MB ViewState and no stable feed). Revisit if a real feed surfaces.
- **Tier 3 — trade-press signals, RSS, UK & Ireland scoped.** Utility Week,
  electric.ie, BusinessGreen, and Energy Live News. (Current± is
  discontinued; reNEWS and Utility Dive were dropped — both are global/US
  trade press and produced false-positive matches on foreign stories.)
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

Seven independent filters on the notices table — source, tier, sector,
minimum score, deadline-within-N-days, new-since-last-visit (tracked via
`localStorage`), and free-text search (title/buyer/description) — plus a
separate, independent search box on the Tier 3 signals section (headline
only; `filterSignals()`, not `filterRecords()`, since signals have a
different schema). Filter logic lives in `dashboard/src/filters.js`;
`dashboard/scripts/verify-filters.mjs` is a standalone independence check
against synthetic data (`node dashboard/scripts/verify-filters.mjs`).

## Run history

`history.py` (tier-agnostic, imported by both orchestrators) appends a
timestamped summary to `data/run_history.json` (capped at 25 entries) after
each run. The dashboard shows a "Last updated" timestamp in the header and a
collapsible run-history list — both purely informational, no effect on
scoring or the notices/signals data itself.

## Triggering a refresh without GitHub

`Refresh-TenderWatch.bat` (and a matching Desktop shortcut) triggers
`gh workflow run refresh.yml`, polls until it starts, streams live
job-by-job progress via `gh run watch`, and opens the dashboard automatically
on success. Requires `gh auth login` once per machine.

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
