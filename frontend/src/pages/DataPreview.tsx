import { useEffect, useState } from "react";
import { api } from "../api/client";
import type { RecordPreview } from "../types";
import { StatusPill } from "../components/StatusPill";

export function DataPreview({ batchId, onPushed }: { batchId: string; onPushed: () => void }) {
  const [records, setRecords] = useState<RecordPreview[]>([]);
  const [filter, setFilter] = useState("ALL");
  const [error, setError] = useState("");
  const [busy, setBusy] = useState(false);
  useEffect(() => { if (batchId) api.records(batchId).then(setRecords).catch(() => setRecords([])); }, [batchId]);
  const visible = filter === "ALL" ? records : records.filter((record) => record.status === filter);
  const validCount = records.filter((record) => record.status === "VALID").length;

  async function push() {
    setBusy(true);
    setError("");
    try {
      await api.pushValid(batchId);
      onPushed();
    } catch (reason) {
      setError(reason instanceof Error ? reason.message : "Push failed");
    } finally {
      setBusy(false);
    }
  }

  return <section><div className="section-heading"><div><p className="eyebrow">Traceable changes</p><h2>Data preview</h2></div><div className="actions"><label>Filter <select value={filter} onChange={(event) => setFilter(event.target.value)}><option>ALL</option><option>VALID</option><option>WARNING</option><option>ESCALATION</option><option>REJECTED</option></select></label><button className="primary" disabled={!validCount || busy} onClick={push}>{busy ? "Pushing…" : `Push valid records (${validCount})`}</button></div></div>{error && <p role="alert" className="error">{error}</p>}<div className="table-wrap"><table><thead><tr><th>Status</th><th>Source</th><th>Original</th><th>Transformed</th><th>Evidence</th></tr></thead><tbody>{visible.map((record) => <tr key={record.record_id}><td><StatusPill value={record.status} /></td><td>{record.source_file} #{record.source_record_id}</td><td><code>{JSON.stringify(record.original)}</code></td><td><code>{JSON.stringify(record.transformed)}</code></td><td>{record.provenance.map((item) => item.rule).join(", ")}{record.errors.join(", ")}</td></tr>)}</tbody></table>{!visible.length && <div className="empty"><h3>No preview records</h3><p>Complete mapping and review first. Validated transformations will then appear here.</p></div>}</div></section>;
}
