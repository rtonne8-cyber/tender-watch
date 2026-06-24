# TenderWatch — Claude Code operating rules

## Mission
Live dashboard of new T&D-relevant tender notices (UK/Ireland public procurement)
plus early trade-press signals. Zero manual portal-checking.

## Locked scope — do not relitigate
- Tier 1 (OCDS APIs): Find a Tender, Contracts Finder, eTenders Ireland.
- Tier 2 (RSS, headline+link only): PCS Scotland.
- Tier 3 (RSS, SIGNAL ONLY): Utility Week, Current±, reNEWS, Utility Dive.
  Tier 3 must NEVER render or score as a confirmed notice.
- PARKED, out of scope: NGET, SSEN-T, SPT, EirGrid, ESBN (login-gated, no public feed).
  Do not attempt to build these.
- Do NOT fold in the BD Pipeline Intelligence Agent. Different project.

## Hard rules (acceptance-test backed — breaking any = build fails)
1. scoring/relevance.py calls Haiku by EXPLICIT model string. Plain ANTHROPIC_API_KEY only.
   NEVER the Agent SDK. NEVER Sonnet. NEVER an unspecified/default model.
2. Each Tier 1 fetcher returns >=1 live record on a manual run.
3. Tier 3 records cannot render or score as confirmed notices — structurally separate.
4. Dashboard filters (source, tier, sector, threshold, deadline, new-since-last-visit)
   each work independently.
5. One broken source is logged and skipped — it does not fail the whole run.
6. Trigger is workflow_dispatch only. No cron. No scheduled runs.

## Build approach (this build)
- Claude Code does ALL the work. Codex is parked for v1.
- Keep the phase order: 1 -> 2 -> 3 -> 4. Do not reorder or merge phases.
- Work one phase at a time. Do not start the next phase until the current exit test passes.

## Stack & brand
- Python fetchers/scoring; JSON store; React/Vite dashboard; GitHub Pages; GitHub Actions.
- Dashboard brand: Green #00AB61, Teal #009A9B, Stone #B2B1A7, Arial.
