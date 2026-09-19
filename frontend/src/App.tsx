import { useState } from "react";
import { DataPreview } from "./pages/DataPreview";
import { IntegrationAudit } from "./pages/IntegrationAudit";
import { LiveRun } from "./pages/LiveRun";
import { NewMigration } from "./pages/NewMigration";
import { ReviewQueue } from "./pages/ReviewQueue";
import type { View } from "./types";

const navigation: Array<[View, string, string]> = [
  ["new", "+", "New migration"], ["live", "o", "Live run"], ["review", "◇", "Review queue"],
  ["preview", "▤", "Data preview"], ["audit", "↗", "Integration audit"],
];

export function App() {
  const [view, setView] = useState<View>("new");
  const [batchId, setBatchId] = useState("");
  const content = {
    new: <NewMigration onCreated={(id) => { setBatchId(id); setView("live"); }} />,
    live: <LiveRun batchId={batchId} />, review: <ReviewQueue batchId={batchId} />,
    preview: <DataPreview batchId={batchId} />, audit: <IntegrationAudit batchId={batchId} />,
  }[view];
  return <div className="shell"><aside className="sidebar"><a className="brand" href="#main" aria-label="MigrateFlow home"><span>M</span><strong>MigrateFlow</strong></a><nav aria-label="Primary navigation">{navigation.map(([id, icon, label]) => <button key={id} className={view === id ? "active" : ""} aria-current={view === id ? "page" : undefined} onClick={() => setView(id)}><span>{icon}</span>{label}{id === "review" && <b>!</b>}</button>)}</nav><div className="sidebar-foot"><span className="secure-dot" />Local model path<p>PII-safe context</p></div></aside><main id="main"><header><div><span className="secure-dot" /> Supervised mode</div>{batchId ? <code>{batchId.slice(0, 8)}</code> : <span>No active batch</span>}</header><div className="content">{content}</div></main></div>;
}
