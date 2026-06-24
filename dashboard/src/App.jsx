import { useEffect, useMemo, useState } from "react";
import SignalsFeed from "./SignalsFeed.jsx";
import { filterRecords, uniqueValues, readLastVisit, writeLastVisitNow } from "./filters.js";

const SOURCE_LABELS = {
  find_a_tender: "Find a Tender",
  contracts_finder: "Contracts Finder",
  etenders_ie: "eTenders Ireland",
};

const DEADLINE_OPTIONS = [
  { label: "Any deadline", value: "" },
  { label: "Within 7 days", value: "7" },
  { label: "Within 14 days", value: "14" },
  { label: "Within 30 days", value: "30" },
  { label: "Within 90 days", value: "90" },
];

function formatDate(value) {
  if (!value) return "—";
  const d = new Date(value);
  if (Number.isNaN(d.getTime())) return "—";
  return d.toLocaleDateString("en-GB", { day: "2-digit", month: "short", year: "numeric" });
}

function toggleInSet(set, value) {
  const next = new Set(set);
  if (next.has(value)) next.delete(value);
  else next.add(value);
  return next;
}

function CheckboxGroup({ label, options, selected, onToggle, formatOption }) {
  if (options.length === 0) return null;
  return (
    <div style={{ marginRight: 20 }}>
      <div style={{ fontWeight: "bold", fontSize: 12, color: "var(--tw-ink)", marginBottom: 4 }}>{label}</div>
      {options.map((opt) => (
        <label key={opt} style={{ display: "block", fontSize: 13 }}>
          <input type="checkbox" checked={selected.has(opt)} onChange={() => onToggle(opt)} /> {formatOption ? formatOption(opt) : opt}
        </label>
      ))}
    </div>
  );
}

export default function App() {
  const [records, setRecords] = useState(null);
  const [error, setError] = useState(null);

  const [sources, setSources] = useState(() => new Set());
  const [tiers, setTiers] = useState(() => new Set());
  const [sectors, setSectors] = useState(() => new Set());
  const [minScore, setMinScore] = useState(0);
  const [deadlineWithinDays, setDeadlineWithinDays] = useState(null);
  const [newSinceLastVisit, setNewSinceLastVisit] = useState(false);
  const [lastVisitTimestamp] = useState(() => readLastVisit());

  useEffect(() => {
    fetch("./data/tenders.json")
      .then((res) => {
        if (!res.ok) throw new Error(`HTTP ${res.status}`);
        return res.json();
      })
      .then((data) => setRecords(data))
      .catch((err) => setError(err.message));

    writeLastVisitNow();
  }, []);

  const sourceOptions = useMemo(() => (records ? uniqueValues(records, "source") : []), [records]);
  const tierOptions = useMemo(() => (records ? uniqueValues(records, "tier") : []), [records]);
  const sectorOptions = useMemo(() => (records ? uniqueValues(records, "sector") : []), [records]);

  const filtered = useMemo(() => {
    if (!records) return [];
    return filterRecords(records, {
      sources,
      tiers,
      sectors,
      minScore,
      deadlineWithinDays,
      newSinceLastVisit,
      lastVisitTimestamp,
    });
  }, [records, sources, tiers, sectors, minScore, deadlineWithinDays, newSinceLastVisit, lastVisitTimestamp]);

  return (
    <div style={{ maxWidth: 1100, margin: "0 auto", padding: "24px 16px" }}>
      <header style={{ borderBottom: "3px solid var(--tw-green)", paddingBottom: 12, marginBottom: 20 }}>
        <h1 style={{ margin: 0, color: "var(--tw-teal)", fontSize: 26 }}>TenderWatch</h1>
        <p style={{ margin: "4px 0 0", color: "var(--tw-stone)" }}>
          T&amp;D-relevant tender notices — UK &amp; Ireland public procurement
        </p>
      </header>

      {error && <p style={{ color: "crimson" }}>Failed to load data: {error}</p>}
      {!records && !error && <p>Loading…</p>}

      {records && (
        <>
          <div style={{ display: "flex", flexWrap: "wrap", alignItems: "flex-start", marginBottom: 16, padding: 12, background: "#fff", border: "1px solid #e2e2dd" }}>
            <CheckboxGroup
              label="Source"
              options={sourceOptions}
              selected={sources}
              onToggle={(v) => setSources((s) => toggleInSet(s, v))}
              formatOption={(v) => SOURCE_LABELS[v] || v}
            />
            <CheckboxGroup label="Tier" options={tierOptions} selected={tiers} onToggle={(v) => setTiers((s) => toggleInSet(s, v))} />
            <CheckboxGroup label="Sector" options={sectorOptions} selected={sectors} onToggle={(v) => setSectors((s) => toggleInSet(s, v))} />

            <div style={{ marginRight: 20 }}>
              <div style={{ fontWeight: "bold", fontSize: 12, marginBottom: 4 }}>Min score: {minScore}</div>
              <input type="range" min="0" max="100" value={minScore} onChange={(e) => setMinScore(Number(e.target.value))} />
            </div>

            <div style={{ marginRight: 20 }}>
              <div style={{ fontWeight: "bold", fontSize: 12, marginBottom: 4 }}>Deadline</div>
              <select
                value={deadlineWithinDays ?? ""}
                onChange={(e) => setDeadlineWithinDays(e.target.value ? Number(e.target.value) : null)}
              >
                {DEADLINE_OPTIONS.map((opt) => (
                  <option key={opt.label} value={opt.value}>
                    {opt.label}
                  </option>
                ))}
              </select>
            </div>

            <div>
              <label style={{ fontSize: 13 }}>
                <input type="checkbox" checked={newSinceLastVisit} onChange={(e) => setNewSinceLastVisit(e.target.checked)} /> New since last
                visit
              </label>
            </div>
          </div>

          {filtered.length === 0 && <p>No records match the current filters.</p>}

          {filtered.length > 0 && (
            <table style={{ width: "100%", borderCollapse: "collapse", fontSize: 14 }}>
              <thead>
                <tr style={{ background: "var(--tw-green)", color: "white", textAlign: "left" }}>
                  <th style={{ padding: "8px 10px" }}>Title</th>
                  <th style={{ padding: "8px 10px" }}>Buyer</th>
                  <th style={{ padding: "8px 10px" }}>Source</th>
                  <th style={{ padding: "8px 10px" }}>Tier</th>
                  <th style={{ padding: "8px 10px" }}>Sector</th>
                  <th style={{ padding: "8px 10px" }}>Score</th>
                  <th style={{ padding: "8px 10px" }}>Deadline</th>
                </tr>
              </thead>
              <tbody>
                {[...filtered]
                  .sort((a, b) => b.score - a.score)
                  .map((r) => (
                    <tr key={r.id} style={{ borderBottom: "1px solid #e2e2dd" }}>
                      <td style={{ padding: "8px 10px" }}>
                        <a href={r.url} target="_blank" rel="noreferrer" style={{ color: "var(--tw-teal)" }}>
                          {r.title}
                        </a>
                      </td>
                      <td style={{ padding: "8px 10px" }}>{r.buyer}</td>
                      <td style={{ padding: "8px 10px" }}>{SOURCE_LABELS[r.source] || r.source}</td>
                      <td style={{ padding: "8px 10px" }}>{r.tier}</td>
                      <td style={{ padding: "8px 10px" }}>{r.sector}</td>
                      <td style={{ padding: "8px 10px", fontWeight: "bold" }}>{r.score}</td>
                      <td style={{ padding: "8px 10px" }}>{formatDate(r.deadline_date)}</td>
                    </tr>
                  ))}
              </tbody>
            </table>
          )}
        </>
      )}

      <SignalsFeed />
    </div>
  );
}
