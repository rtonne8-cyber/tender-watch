const DAY_MS = 24 * 60 * 60 * 1000;

// Six independent predicates, ANDed together. Each checks only its own
// field on the record — no filter's logic depends on another's state.
export function filterRecords(records, filters, now = Date.now()) {
  const {
    sources = null, // Set<string> | null (null = no filter)
    tiers = null, // Set<number> | null
    sectors = null, // Set<string> | null
    minScore = null, // number | null
    deadlineWithinDays = null, // number | null
    newSinceLastVisit = false,
    lastVisitTimestamp = null, // ms epoch | null
  } = filters;

  return records.filter((r) => {
    if (sources && sources.size > 0 && !sources.has(r.source)) return false;
    if (tiers && tiers.size > 0 && !tiers.has(r.tier)) return false;
    if (sectors && sectors.size > 0 && !sectors.has(r.sector)) return false;
    if (minScore != null && (r.score ?? 0) < minScore) return false;

    if (deadlineWithinDays != null) {
      if (!r.deadline_date) return false;
      const deadline = new Date(r.deadline_date).getTime();
      if (Number.isNaN(deadline)) return false;
      if (deadline - now > deadlineWithinDays * DAY_MS) return false;
    }

    if (newSinceLastVisit && lastVisitTimestamp != null) {
      const scoredAt = new Date(r.scored_at).getTime();
      if (Number.isNaN(scoredAt) || scoredAt <= lastVisitTimestamp) return false;
    }

    return true;
  });
}

export function uniqueValues(records, field) {
  return Array.from(new Set(records.map((r) => r[field]).filter((v) => v != null))).sort();
}

const LAST_VISIT_KEY = "tenderwatch_last_visit";

export function readLastVisit() {
  const raw = localStorage.getItem(LAST_VISIT_KEY);
  return raw ? Number(raw) : null;
}

export function writeLastVisitNow() {
  localStorage.setItem(LAST_VISIT_KEY, String(Date.now()));
}
