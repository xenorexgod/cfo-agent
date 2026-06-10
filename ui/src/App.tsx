import { useCallback, useState } from "react";
import { diligenceReadinessScore, freeUsableCash, overdueReceivables, riskRating } from "./calculations";
import { money, pct } from "./formatting";
import { RENDERERS, REPORTS, type ReportId, type ReportMeta } from "./reports";
import type { FinanceData } from "./types";
import { marked } from "marked";
import "./App.css";

const CATEGORY_LABELS: Record<string, string> = {
  overview: "Overview",
  operations: "Operations",
  strategy: "Strategy",
  governance: "Governance",
};

const CATEGORY_ORDER = ["overview", "operations", "strategy", "governance"];

function RiskBadge({ rating }: { rating: string }) {
  const cls = rating === "High" ? "badge-high" : rating === "Medium" ? "badge-medium" : "badge-controlled";
  return <span className={`badge ${cls}`}>{rating}</span>;
}

function MetricCard({ label, value, sub, accent }: { label: string; value: string; sub?: string; accent?: "green" | "red" | "amber" }) {
  return (
    <div className={`metric-card${accent ? ` accent-${accent}` : ""}`}>
      <div className="metric-label">{label}</div>
      <div className="metric-value">{value}</div>
      {sub && <div className="metric-sub">{sub}</div>}
    </div>
  );
}

function Dashboard({ data }: { data: FinanceData }) {
  const freeCash = freeUsableCash(data.cash);
  const overdue = overdueReceivables(data.receivables);
  const score = diligenceReadinessScore(data);
  const rating = riskRating(data);
  const collectionRate = data.monthly_revenue > 0 ? (data.collected_revenue / data.monthly_revenue) * 100 : 0;
  const cashStress = freeCash < data.cash.fixed_obligations_7d;
  const runwayDays = data.cash.monthly_fixed_obligations > 0 ? (freeCash / data.cash.monthly_fixed_obligations) * 30 : 0;

  return (
    <div className="dashboard">
      <div className="dashboard-header">
        <div>
          <h2 className="company-name">{data.company}</h2>
          <p className="report-period">{data.report_month} · {data.report_date}</p>
        </div>
        <RiskBadge rating={rating} />
      </div>

      <div className="metrics-grid">
        <MetricCard label="Billed Revenue" value={money(data.monthly_revenue)} sub={`Collected: ${money(data.collected_revenue)}`} />
        <MetricCard label="Collection Rate" value={pct(collectionRate)} accent={collectionRate >= 90 ? "green" : collectionRate >= 75 ? "amber" : "red"} />
        <MetricCard label="Monthly EBITDA" value={money(data.monthly_ebitda)} accent={data.monthly_ebitda > 0 ? "green" : "red"} />
        <MetricCard label="Free Usable Cash" value={money(freeCash)} sub={`${runwayDays.toFixed(0)} days runway`} accent={cashStress ? "red" : "green"} />
        <MetricCard label="Overdue Receivables" value={money(overdue)} accent={overdue > data.monthly_revenue * 0.5 ? "red" : overdue > 0 ? "amber" : "green"} />
        <MetricCard label="Diligence Score" value={`${score}/100`} accent={score >= 80 ? "green" : score >= 60 ? "amber" : "red"} />
      </div>

      <div className="centres-section">
        <h3 className="section-title">Centre Performance</h3>
        <div className="centres-grid">
          {data.centres.map((c) => {
            const ebitda = c.revenue - c.direct_costs;
            const occ = (c.occupied_seats / c.seat_capacity) * 100;
            return (
              <div key={c.name} className="centre-card">
                <div className="centre-name">{c.name}</div>
                <div className="centre-row"><span>Revenue</span><span>{money(c.revenue)}</span></div>
                <div className="centre-row"><span>EBITDA</span><span className={ebitda < 0 ? "text-red" : "text-green"}>{money(ebitda)}</span></div>
                <div className="centre-row"><span>Occupancy</span><span>{pct(occ)}</span></div>
                <div className="occ-bar"><div className="occ-fill" style={{ width: `${Math.min(occ, 100)}%`, background: occ >= c.break_even_occupancy_pct ? "var(--green)" : "var(--amber)" }} /></div>
                <div className="centre-breakeven">Break-even: {c.break_even_occupancy_pct}%</div>
              </div>
            );
          })}
        </div>
      </div>

      {data.governance_items && data.governance_items.length > 0 && (
        <div className="governance-section">
          <h3 className="section-title">Open Governance Items</h3>
          <ul className="governance-list">
            {data.governance_items.map((item, i) => (
              <li key={i} className="governance-item">{item}</li>
            ))}
          </ul>
        </div>
      )}
    </div>
  );
}

function ReportViewer({ data, reportId }: { data: FinanceData; reportId: ReportId }) {
  const renderer = RENDERERS[reportId];
  const markdown = renderer(data);
  const html = marked(markdown) as string;
  return (
    <div className="report-viewer">
      <div className="report-content" dangerouslySetInnerHTML={{ __html: html }} />
    </div>
  );
}

function Sidebar({ reports, active, onSelect }: { reports: ReportMeta[]; active: string; onSelect: (id: ReportId | "dashboard") => void }) {
  const grouped = CATEGORY_ORDER.map((cat) => ({
    cat,
    label: CATEGORY_LABELS[cat],
    items: reports.filter((r) => r.category === cat),
  }));

  return (
    <nav className="sidebar">
      <div className="sidebar-brand">
        <svg width="20" height="20" viewBox="0 0 40 40" fill="none" className="brand-icon">
          <rect x="4" y="4" width="14" height="14" rx="3" fill="currentColor" opacity="0.9" />
          <rect x="22" y="4" width="14" height="14" rx="3" fill="currentColor" opacity="0.6" />
          <rect x="4" y="22" width="14" height="14" rx="3" fill="currentColor" opacity="0.6" />
          <rect x="22" y="22" width="14" height="14" rx="3" fill="currentColor" opacity="0.3" />
        </svg>
        <span>CFO Agent</span>
      </div>
      <button className={`sidebar-item dashboard-item${active === "dashboard" ? " active" : ""}`} onClick={() => onSelect("dashboard")}>
        Dashboard
      </button>
      {grouped.map(({ cat, label, items }) => (
        <div key={cat} className="sidebar-group">
          <div className="sidebar-group-label">{label}</div>
          {items.filter((r) => r.id !== "executive_summary").map((r) => (
            <button key={r.id} className={`sidebar-item${active === r.id ? " active" : ""}`} onClick={() => onSelect(r.id)}>
              {r.label}
            </button>
          ))}
        </div>
      ))}
    </nav>
  );
}

function UploadScreen({ onLoad }: { onLoad: (data: FinanceData) => void }) {
  const [error, setError] = useState<string | null>(null);
  const [dragging, setDragging] = useState(false);

  const parse = useCallback(
    (text: string) => {
      try {
        const json = JSON.parse(text);
        onLoad(json as FinanceData);
      } catch {
        setError("Invalid JSON file. Please upload a valid CFO Agent data file.");
      }
    },
    [onLoad]
  );

  const handleFile = useCallback(
    (file: File) => {
      const reader = new FileReader();
      reader.onload = (e) => parse(e.target?.result as string);
      reader.readAsText(file);
    },
    [parse]
  );

  const handleDrop = useCallback(
    (e: React.DragEvent) => {
      e.preventDefault();
      setDragging(false);
      const file = e.dataTransfer.files[0];
      if (file) handleFile(file);
    },
    [handleFile]
  );

  const loadExample = useCallback(async () => {
    try {
      const res = await fetch("/suits_may_2026.json");
      const text = await res.text();
      parse(text);
    } catch {
      setError("Failed to load example file.");
    }
  }, [parse]);

  return (
    <div className="upload-screen">
      <div className="upload-card">
        <div className="upload-logo">
          <svg width="48" height="48" viewBox="0 0 40 40" fill="none">
            <rect x="4" y="4" width="14" height="14" rx="3" fill="var(--blue)" opacity="0.9" />
            <rect x="22" y="4" width="14" height="14" rx="3" fill="var(--blue)" opacity="0.6" />
            <rect x="4" y="22" width="14" height="14" rx="3" fill="var(--blue)" opacity="0.6" />
            <rect x="22" y="22" width="14" height="14" rx="3" fill="var(--blue)" opacity="0.3" />
          </svg>
        </div>
        <h1 className="upload-title">CFO Agent</h1>
        <p className="upload-subtitle">Financial reporting and governance for workspace operating companies</p>

        <div
          className={`drop-zone${dragging ? " dragging" : ""}`}
          onDragOver={(e) => { e.preventDefault(); setDragging(true); }}
          onDragLeave={() => setDragging(false)}
          onDrop={handleDrop}
        >
          <svg width="28" height="28" viewBox="0 0 24 24" fill="none" stroke="currentColor" strokeWidth="1.5">
            <path d="M21 15v4a2 2 0 0 1-2 2H5a2 2 0 0 1-2-2v-4" />
            <polyline points="17 8 12 3 7 8" />
            <line x1="12" y1="3" x2="12" y2="15" />
          </svg>
          <p className="drop-text">Drop your JSON data file here</p>
          <p className="drop-sub">or</p>
          <label className="file-btn">
            Browse file
            <input type="file" accept=".json" style={{ display: "none" }} onChange={(e) => { const f = e.target.files?.[0]; if (f) handleFile(f); }} />
          </label>
        </div>

        {error && <p className="upload-error">{error}</p>}

        <div className="upload-divider"><span>or try with sample data</span></div>
        <button className="example-btn" onClick={loadExample}>Load Suits Workspaces — May 2026</button>
      </div>
    </div>
  );
}

export default function App() {
  const [data, setData] = useState<FinanceData | null>(null);
  const [activeReport, setActiveReport] = useState<ReportId | "dashboard">("dashboard");

  if (!data) return <UploadScreen onLoad={(d) => { setData(d); setActiveReport("dashboard"); }} />;

  return (
    <div className="app-layout">
      <Sidebar reports={REPORTS} active={activeReport} onSelect={setActiveReport} />
      <main className="main-content">
        <div className="topbar">
          <div className="topbar-title">
            {activeReport === "dashboard"
              ? `${data.company} — ${data.report_month}`
              : REPORTS.find((r) => r.id === activeReport)?.label ?? activeReport}
          </div>
          <button className="load-btn" onClick={() => setData(null)}>
            <svg width="13" height="13" viewBox="0 0 24 24" fill="none" stroke="currentColor" strokeWidth="2.5">
              <path d="M21 15v4a2 2 0 0 1-2 2H5a2 2 0 0 1-2-2v-4" />
              <polyline points="17 8 12 3 7 8" />
              <line x1="12" y1="3" x2="12" y2="15" />
            </svg>
            Load new file
          </button>
        </div>
        <div className="content-area">
          {activeReport === "dashboard" ? (
            <Dashboard data={data} />
          ) : (
            <ReportViewer data={data} reportId={activeReport as ReportId} />
          )}
        </div>
      </main>
    </div>
  );
}
