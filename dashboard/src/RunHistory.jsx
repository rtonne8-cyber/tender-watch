const KIND_LABELS = {
  tenders: "Tier 1/2 notices",
  signals: "Tier 3 signals",
};

function formatTimestamp(value) {
  const d = new Date(value);
  if (Number.isNaN(d.getTime())) return value;
  return d.toLocaleString("en-GB", {
    day: "2-digit",
    month: "short",
    year: "numeric",
    hour: "2-digit",
    minute: "2-digit",
  });
}

function summaryLine(entry) {
  if (entry.kind === "tenders") return `${entry.summary.scored_count} scored notice(s)`;
  if (entry.kind === "signals") return `${entry.summary.count} signal(s)`;
  return "";
}

// Presentational only — App.jsx owns the fetch of data/run_history.json so
// the "Last updated" header line and this list share one request. Purely
// informational; run_history.json never feeds into scoring or the
// notices/signals data itself.
export default function RunHistory({ history }) {
  if (!history || history.length === 0) return null;

  return (
    <details style={{ marginTop: 28, fontSize: 13, color: "var(--tw-ink)" }}>
      <summary style={{ cursor: "pointer", fontWeight: "bold", color: "var(--tw-teal)" }}>
        Run history ({history.length})
      </summary>
      <ul style={{ listStyle: "none", padding: 0, marginTop: 8 }}>
        {history.map((entry, i) => (
          <li key={i} style={{ padding: "4px 0", borderBottom: "1px solid #ece9e3" }}>
            <strong>{formatTimestamp(entry.timestamp)}</strong> — {KIND_LABELS[entry.kind] || entry.kind}:{" "}
            {summaryLine(entry)}
          </li>
        ))}
      </ul>
    </details>
  );
}

export function formatLastUpdated(history) {
  if (!history || history.length === 0) return null;
  const d = new Date(history[0].timestamp);
  if (Number.isNaN(d.getTime())) return null;
  return d.toLocaleString("en-GB", {
    day: "2-digit",
    month: "short",
    year: "numeric",
    hour: "2-digit",
    minute: "2-digit",
  });
}
