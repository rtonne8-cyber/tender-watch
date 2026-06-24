# TenderWatch — Build Brief v2 (Claude Code only)

> **Revision note (v1 → v2).** Build approach consolidated to **Claude Code only** for this build.
> All work previously allocated to Codex CLI (fetchers, boilerplate, scaffolding) now runs through
> Claude Code. Codex is parked for v1 — reversible. No hard gate changes; phase order 1→4 unchanged;
> record schema and two-pass scoring logic carried verbatim from v1.

---

## 1. Objective & definition of done

**Objective.** A live dashboard that aggregates new T&D-relevant tender notices from UK/Ireland public
procurement feeds plus early trade-press signals — zero manual portal-checking.

**Definition of done.** All four phases pass their exit tests **and** all five hard gates are green on a
clean manual run, with `data/tenders.json` populated by real records and the dashboard deployed to GitHub
Pages. Tested by the acceptance sweep in §6.

---

## 2. Source spec reference

- Source spec: `TenderWatch_Build_Brief.md` (built June 2026), chat *"Tender tracking dashboard for sector monitoring."*
- Project reference summary: `Initial_Context` (mission, source tiers, schema, scoring logic, scaffold, decisions log).

Not restated below except where the build approach changes. Treat the spec as authoritative on scope; treat
this brief as authoritative on **how Claude Code executes it**.

---

## 3. Environment & constraints

| Dimension | Setting |
|---|---|
| Build machine | **Lenovo laptop** — Claude Code lives here; do all build/dev here. |
| Run target | **GitHub Actions (cloud)** — *not* the corporate PC. No-admin constraint does not bite at runtime. |
| Hosting | GitHub Pages (static dashboard). |
| Trigger model | **`workflow_dispatch` only. No cron, no scheduled runs.** Hard gate. |
| Stack | Python (fetchers + scoring), JSON data store, React/Vite dashboard. |
| Sync | OneDrive across iPad / corporate PC / Lenovo. Keep the working repo path short; never live-edit the same file on two machines. |
| Brand (dashboard output) | Corporate Green `#00AB61` / Teal `#009A9B` / Stone `#B2B1A7`, Arial. BD/market-intelligence work product. |
| Separation | TenderWatch stays separate from the BD Pipeline Intelligence Agent. Do not fold them together. |

---

## 4. Repo / folder scaffold

Carried from v1, re-annotated so **Claude Code owns every component**.

```
tender-watch/
├── .github/workflows/refresh.yml      (workflow_dispatch only, no cron)   — Claude Code
├── fetchers/                          — Claude Code
│   ├── fts.py
│   ├── contracts_finder.py
│   ├── etenders_ie.py
│   ├── pcs_scotland.py
│   ├── news_signals.py
│   └── feeds.yaml
├── scoring/                           — Claude Code
│   ├── relevance.py   (Haiku hard gate, explicit model string)
│   └── keywords.yaml
├── data/tenders.json                  — live store
├── dashboard/  (Vite React, src/App.jsx core)   — Claude Code
├── CLAUDE.md
└── README.md
```

### CLAUDE.md payload (create this first)

This file is the build's guardrail. It keeps Claude Code on the locked scope across sessions and stops it
breaking a gate. Create it before Phase 1, keep it open, and re-anchor on it at the start of every phase.

```markdown
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
```

---

## 5. Phased build plan (with Claude Code driving)

Drive each phase the same way: **(a)** start in **plan mode** and have Claude Code read `CLAUDE.md` first;
**(b)** scope the prompt to that phase only; **(c)** approve the plan; **(d)** build; **(e)** run the
**gate-check command** before moving on; **(f)** commit. Do not let it run ahead into the next phase.

### Phase 1 — Tier 1 + scoring + dashboard skeleton
- **Goal.** Three OCDS fetchers (Find a Tender, Contracts Finder, eTenders IE) → record schema → two-pass
  scoring (CPV allowlist + keyword regex pre-filter, then Haiku gate on the ambiguous band) →
  `data/tenders.json` → minimal React/Vite dashboard renders scored records.
- **Exit test.** ≥1 real **scored** record per Tier 1 source rendering on the dashboard.
- **Drive it.**
  > Read CLAUDE.md. Build **Phase 1 only**: the three Tier 1 OCDS fetchers, the full record schema, the
  > two-pass scoring module, and a minimal dashboard skeleton that lists scored records. Scoring must call
  > Haiku by explicit model string via ANTHROPIC_API_KEY — no Agent SDK, no Sonnet. Do **not** build Tier 2
  > or Tier 3. Do **not** add cron. Produce a plan first; I'll approve before you write code.
- **Gate-check before moving on.**
  ```bash
  grep -i "claude-haiku" scoring/relevance.py          # must match — Gate 1
  python fetchers/fts.py && python fetchers/contracts_finder.py && python fetchers/etenders_ie.py
  # each must print/emit >=1 live record — Gate 2
  ```

### Phase 2 — Tier 2 (PCS Scotland)
- **Goal.** Add `pcs_scotland.py` (RSS, headline + link only). Records are tier-filterable independently.
- **Exit test.** Tier 2 can be isolated by the tier filter without disturbing Tier 1.
- **Drive it.**
  > Read CLAUDE.md. **Phase 2 only**: add the PCS Scotland RSS fetcher, headline + link only, tagged Tier 2.
  > It must be independently filterable in the dashboard. Do not alter the Tier 1 fetchers or scoring. Plan first.
- **Gate-check.** Toggle the tier filter; confirm Tier 2 isolates cleanly (Gate 4, partial).

### Phase 3 — Tier 3 (signal layer) — highest-stakes gate
- **Goal.** `news_signals.py` + `feeds.yaml` (Utility Week, Current±, reNEWS, Utility Dive), RSS, signal only.
- **Exit test.** Structurally distinct — a Tier 3 item can **never** render or score as a confirmed notice.
- **Drive it.**
  > Read CLAUDE.md. **Phase 3 only**: add the Tier 3 signal layer (news RSS via feeds.yaml). These are
  > **signals, never confirmed notices.** They must be structurally separate in the data model and the UI,
  > must not pass through the notice scoring path, and must not appear in the notices list. After building,
  > prove to me that a Tier 3 item cannot surface as a notice. Plan first.
- **Gate-check.** Attempt to surface a Tier 3 item as a notice — it must be impossible by construction, not
  just hidden (Gate 3). This is the gate most likely to be fudged; verify the data model, not only the view.

### Phase 4 — Hardening + handback
- **Goal.** Broken-feed resilience; the `new-since-last-visit` filter; all six filters independent; README;
  full acceptance sweep.
- **Exit test.** A broken feed is logged and skipped; the run completes and the other sources still populate.
- **Drive it.**
  > Read CLAUDE.md. **Phase 4 only**: harden the run. Simulate a broken feed (bad URL) and confirm it is
  > logged and skipped while every other source completes. Verify all six dashboard filters work
  > independently. Write the README. Then run the full acceptance sweep in the brief and report each gate
  > pass/fail. Plan first.
- **Gate-check.** Inject a bad feed URL; confirm logged + skipped + run completes (Gate 5). Then run the
  full §6 sweep.

---

## 6. Acceptance tests

| # | Gate | Phase | How it's run |
|---|---|---|---|
| 1 | `scoring/relevance.py` calls Haiku by explicit model string; plain `ANTHROPIC_API_KEY`, no Agent SDK, no Sonnet | 1 | `grep -i "claude-haiku" scoring/relevance.py` matches; grep confirms no Agent SDK import and no Sonnet string |
| 2 | Each Tier 1 fetcher returns ≥1 live record | 1 | Manual run of each of the three fetchers |
| 3 | Tier 3 records cannot render/score as confirmed notices | 3 | Data-model + UI check: a Tier 3 item cannot enter the notices path |
| 4 | Dashboard filters (source, tier, sector, threshold, deadline, new-since-last-visit) work independently | 1–4 | Toggle each filter in isolation |
| 5 | One broken source is logged/skipped and does not fail the run | 4 | Inject a bad feed URL; confirm run completes |

Overall pass = all five green on one clean `workflow_dispatch` run.

---

## 7. Data & secrets handling

- `ANTHROPIC_API_KEY` via environment variable (local) and GitHub Actions **secret** (cloud). **Never hard-coded.**
- No client-sensitive data in the repo. Sources are public procurement (OCDS APIs) and public RSS — open data; respect each source's terms and rate limits.
- Tier 2/3 stored as headline + link only, as specified — do not scrape or store full article bodies.

---

## 8. Autonomy & cost flags

- **Autonomy: manual by design.** `workflow_dispatch` only — no cron. This is a deliberate decision to keep run volume low, not an oversight.
- **Scoring cost (programmatic pool).** Haiku via `ANTHROPIC_API_KEY`, two-pass with a free pre-filter; ~sub-£1/month at expected volume. Not worth optimising unless volume scales by orders of magnitude.
- **Build cost (interactive pool).** Consolidating to Claude Code means all fetcher/boilerplate work now consumes your Claude Code interactive quota rather than Codex's ChatGPT Plus quota. *Assumption: immaterial at this build size — four phases, one small repo (**Confidence: High**).* Reintroduce the Codex split only if a future iteration scales sources by an order of magnitude.
- **Resilience.** One broken source logged and skipped (Gate 5); the run never fails wholesale.

---

## 9. Handback format

At the end of each phase, have Claude Code return a short Markdown block:

- **Files created/changed** — paths.
- **Gate results** — each relevant gate, pass/fail, with the command output that proves it.
- **Run summary** — record counts by tier/source; any feed skipped and why.
- **Live data sample** — a few records from `data/tenders.json`.

Final handback (end of Phase 4) = the full §6 sweep result + the deployed GitHub Pages URL.

---

## 10. Decisions log (delta)

- **v1 → v2: build consolidated to Claude Code only.** Rationale: de-risk the first build by driving one
  tool rather than two while learning. The Codex split was an efficiency optimisation (offload boilerplate
  to ChatGPT Plus quota), not a correctness requirement. **Reversible** — reintroduce the split if Claude
  Code interactive usage becomes a constraint at larger scale. Breaks no hard gate; phase order unchanged.
- All prior v1 decisions stand: manual trigger over cron (deliberate); Agent SDK rejected for scoring
  (plain API key only); TenderWatch kept separate from the BD Pipeline Intelligence Agent.

---

## Claude Code guidance note (paste-ready)

> **Build: TenderWatch (v2, Claude Code only).** Build target: Lenovo; run target: GitHub Actions (cloud),
> GitHub Pages hosting. Stack: Python fetchers/scoring, JSON store, React/Vite dashboard.
>
> First, create `CLAUDE.md` from the payload in §4 and read it. Then build in four phases, one at a time,
> **plan mode first**, not starting the next until the current exit test passes:
>
> 1. Tier 1 OCDS fetchers + record schema + two-pass scoring (Haiku, explicit model string, `ANTHROPIC_API_KEY`, no Agent SDK, no Sonnet) + dashboard skeleton. *Exit:* ≥1 scored record per Tier 1 source.
> 2. Tier 2 PCS Scotland RSS (headline+link), independently tier-filterable. *Exit:* Tier 2 isolates.
> 3. Tier 3 signal layer (news RSS, `feeds.yaml`) — signals only, never confirmed notices, structurally separate. *Exit:* a Tier 3 item cannot surface as a notice.
> 4. Hardening: broken-feed logged/skipped without failing the run; all six filters independent; README; full acceptance sweep.
>
> **Hard gates (do not break):** Haiku explicit model string (`grep`-checked); ≥1 live record per Tier 1
> fetcher; Tier 3 never a notice; six filters independent; one broken source logged/skipped;
> `workflow_dispatch` only, no cron. Do not touch parked portals; do not fold in the BD Pipeline Intelligence Agent.
>
> Hand back per phase: files changed, gate results with proof, run summary, and a `data/tenders.json` sample.
