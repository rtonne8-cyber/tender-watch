import { useEffect, useMemo, useState } from "react";
import { filterSignals } from "./filters.js";

const SOURCE_LABELS = {
  utility_week: "Utility Week",
  electric_ie: "electric.ie",
  businessgreen: "BusinessGreen",
  energy_live_news: "Energy Live News",
};

function formatDate(value) {
  if (!value) return "—";
  const d = new Date(value);
  if (Number.isNaN(d.getTime())) return "—";
  return d.toLocaleDateString("en-GB", { day: "2-digit", month: "short", year: "numeric" });
}

// Tier 3 trade-press signals. Deliberately rendered from a separate fetch of
// signals.json, in its own section, with no score/tier columns — this is
// never the same data or component tree as the notices table.
export default function SignalsFeed() {
  const [signals, setSignals] = useState(null);
  const [error, setError] = useState(null);
  const [searchText, setSearchText] = useState("");

  useEffect(() => {
    fetch("./data/signals.json")
      .then((res) => {
        if (!res.ok) throw new Error(`HTTP ${res.status}`);
        return res.json();
      })
      .then((data) => setSignals(data))
      .catch((err) => setError(err.message));
  }, []);

  const filtered = useMemo(() => (signals ? filterSignals(signals, searchText) : []), [signals, searchText]);

  return (
    <section style={{ marginTop: 36 }}>
      <h2 style={{ color: "var(--tw-stone)", fontSize: 18, borderBottom: "2px solid var(--tw-stone)", paddingBottom: 8 }}>
        Trade press signals — not confirmed notices
      </h2>

      {signals && signals.length > 0 && (
        <input
          type="text"
          value={searchText}
          onChange={(e) => setSearchText(e.target.value)}
          placeholder="Search headlines…"
          style={{ width: 260, padding: "4px 6px", fontSize: 13, border: "1px solid var(--tw-stone)", marginBottom: 10 }}
        />
      )}

      {error && <p style={{ color: "crimson" }}>Failed to load signals: {error}</p>}
      {!signals && !error && <p>Loading…</p>}
      {signals && signals.length === 0 && <p>No signals available.</p>}
      {signals && signals.length > 0 && filtered.length === 0 && <p>No signals match your search.</p>}

      {filtered.length > 0 && (
        <ul style={{ listStyle: "none", padding: 0, fontSize: 14 }}>
          {filtered.map((s) => (
            <li key={s.id} style={{ padding: "6px 0", borderBottom: "1px solid #ece9e3" }}>
              <a href={s.link} target="_blank" rel="noreferrer" style={{ color: "var(--tw-teal)" }}>
                {s.headline}
              </a>
              <span style={{ color: "var(--tw-stone)", marginLeft: 8 }}>
                {SOURCE_LABELS[s.source] || s.source} · {formatDate(s.published_date)}
              </span>
            </li>
          ))}
        </ul>
      )}
    </section>
  );
}
