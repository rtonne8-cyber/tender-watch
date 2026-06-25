// Standalone independence check for filterRecords — NOT part of the build,
// run manually via `node dashboard/scripts/verify-filters.mjs`. Uses a
// synthetic record set; never touches data/tenders.json.
import assert from "node:assert/strict";
import { filterRecords, filterSignals } from "../src/filters.js";

const NOW = Date.parse("2026-06-24T00:00:00Z");

const records = [
  { id: "A", source: "find_a_tender", tier: 1, sector: "Substations & Switchgear", score: 90, deadline_date: "2026-07-01", scored_at: "2026-06-20T00:00:00Z", title: "132kV Substation Refurbishment", buyer: "Dundee City Council", description: "" },
  { id: "B", source: "contracts_finder", tier: 1, sector: "Transmission & Distribution Networks", score: 60, deadline_date: "2026-08-01", scored_at: "2026-06-22T00:00:00Z", title: "Overhead Line Maintenance Framework", buyer: "Surrey County Council", description: "" },
  { id: "C", source: "etenders_ie", tier: 1, sector: "Engineering & Consultancy", score: 45, deadline_date: "2026-12-01", scored_at: "2026-06-10T00:00:00Z", title: "Electrical Consultancy Services", buyer: "Dublin Port Company", description: "" },
  { id: "D", source: "pcs_scotland", tier: 2, sector: "General T&D", score: 75, deadline_date: "2026-06-28", scored_at: "2026-06-23T00:00:00Z", title: "Substation Civils Package", buyer: "SP Energy Networks", description: "" },
];

const ids = (rs) => rs.map((r) => r.id).sort().join(",");

// 1. source filter, all other dimensions inactive
assert.equal(ids(filterRecords(records, { sources: new Set(["find_a_tender"]) }, NOW)), "A");

// 2. tier filter, isolates Tier 2 without disturbing Tier 1 (the original
// Phase 2 exit test, now provable even though PCS Scotland is parked)
assert.equal(ids(filterRecords(records, { tiers: new Set([2]) }, NOW)), "D");
assert.equal(ids(filterRecords(records, { tiers: new Set([1]) }, NOW)), "A,B,C");

// 3. sector filter
assert.equal(ids(filterRecords(records, { sectors: new Set(["Engineering & Consultancy"]) }, NOW)), "C");

// 4. score threshold
assert.equal(ids(filterRecords(records, { minScore: 70 }, NOW)), "A,D");

// 5. deadline-within-N-days
assert.equal(ids(filterRecords(records, { deadlineWithinDays: 7 }, NOW)), "A,D");

// 6. new-since-last-visit
assert.equal(
  ids(filterRecords(records, { newSinceLastVisit: true, lastVisitTimestamp: Date.parse("2026-06-21T00:00:00Z") }, NOW)),
  "B,D"
);

// Independence: combining a filter with an *inactive* (empty-Set) dimension
// must give the identical result as that filter alone — an empty Set must
// never act as "no records match".
assert.equal(
  ids(filterRecords(records, { sources: new Set(["contracts_finder"]), tiers: new Set() }, NOW)),
  ids(filterRecords(records, { sources: new Set(["contracts_finder"]) }, NOW))
);

// Independence: two simultaneously active filters intersect, not interfere —
// tier=1 AND minScore=70 should yield exactly {A}, not {A,B,C} or {A,D}.
assert.equal(ids(filterRecords(records, { tiers: new Set([1]), minScore: 70 }, NOW)), "A");

// 7. search text (case-insensitive substring over title/buyer/description)
assert.equal(ids(filterRecords(records, { searchText: "substation" }, NOW)), "A,D");
assert.equal(ids(filterRecords(records, { searchText: "DUBLIN" }, NOW)), "C"); // case-insensitive, matches buyer

// Independence: search combined with tier intersects, not interferes —
// tier=1 AND search="substation" should yield exactly {A}, not {A,D} or {A,B,C}.
assert.equal(ids(filterRecords(records, { tiers: new Set([1]), searchText: "substation" }, NOW)), "A");

// filterSignals: separate function for the Tier 3 schema (headline only),
// confirms it doesn't depend on or interact with filterRecords' state.
const signals = [
  { id: "S1", headline: "NGET confirms new grid capacity at Bramford" },
  { id: "S2", headline: "Solar farm planning approval granted in Kent" },
];
assert.equal(filterSignals(signals, "grid").map((s) => s.id).join(","), "S1");
assert.equal(filterSignals(signals, "").length, 2); // empty search = no filter

console.log("All 7 notice filter-independence checks + filterSignals checks passed.");
