import { useEffect, useState } from "react";
import SignalsFeed from "./SignalsFeed.jsx";

const SOURCE_LABELS = {
  find_a_tender: "Find a Tender",
  contracts_finder: "Contracts Finder",
  etenders_ie: "eTenders Ireland",
};

function formatDate(value) {
  if (!value) return "—";
  const d = new Date(value);
  if (Number.isNaN(d.getTime())) return "—";
  return d.toLocaleDateString("en-GB", { day: "2-digit", month: "short", year: "numeric" });
}

export default function App() {
  const [records, setRecords] = useState(null);
  const [error, setError] = useState(null);

  useEffect(() => {
    fetch("./data/tenders.json")
      .then((res) => {
        if (!res.ok) throw new Error(`HTTP ${res.status}`);
        return res.json();
      })
      .then((data) => setRecords(data))
      .catch((err) => setError(err.message));
  }, []);

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
      {records && records.length === 0 && <p>No scored records yet.</p>}

      {records && records.length > 0 && (
        <table style={{ width: "100%", borderCollapse: "collapse", fontSize: 14 }}>
          <thead>
            <tr style={{ background: "var(--tw-green)", color: "white", textAlign: "left" }}>
              <th style={{ padding: "8px 10px" }}>Title</th>
              <th style={{ padding: "8px 10px" }}>Buyer</th>
              <th style={{ padding: "8px 10px" }}>Source</th>
              <th style={{ padding: "8px 10px" }}>Tier</th>
              <th style={{ padding: "8px 10px" }}>Score</th>
              <th style={{ padding: "8px 10px" }}>Deadline</th>
            </tr>
          </thead>
          <tbody>
            {records
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
                  <td style={{ padding: "8px 10px", fontWeight: "bold" }}>{r.score}</td>
                  <td style={{ padding: "8px 10px" }}>{formatDate(r.deadline_date)}</td>
                </tr>
              ))}
          </tbody>
        </table>
      )}

      <SignalsFeed />
    </div>
  );
}
