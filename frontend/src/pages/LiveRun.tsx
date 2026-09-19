import { useEffect, useState } from "react";
import { api } from "../api/client";
import type { WorkflowEvent, WorkflowStatus } from "../types";
import { StatusPill } from "../components/StatusPill";

export function LiveRun({ batchId, onReview, onPreview }: { batchId: string; onReview: () => void; onPreview: () => void }) {
  const [events, setEvents] = useState<WorkflowEvent[]>([]);
  const [connection, setConnection] = useState("Connecting");
  const [busy, setBusy] = useState(false);
  const [error, setError] = useState("");
  const [workflowStatus, setWorkflowStatus] = useState<WorkflowStatus | null>(null);

  useEffect(() => {
    if (!batchId) return;
    api.status(batchId).then(setWorkflowStatus).catch(() => setWorkflowStatus(null));
  }, [batchId]);

  useEffect(() => {
    if (!batchId) return;
    const stream = new EventSource(api.eventUrl(batchId));
    stream.onopen = () => setConnection("Live");
    const add = (event: Event) => setEvents((current) => {
      const incoming = JSON.parse((event as MessageEvent).data) as WorkflowEvent;
      return current.some((item) => item.event_id === incoming.event_id) ? current : [...current, incoming];
    });
    ["node_started", "node_completed", "progress", "workflow_paused", "workflow_resumed", "reconciliation_completed", "record_validated", "push_result", "rollback", "workflow_failed"].forEach((type) => stream.addEventListener(type, add));
    stream.onerror = () => setConnection("Reconnecting");
    return () => stream.close();
  }, [batchId]);

  async function run() {
    setBusy(true);
    setError("");
    try {
      if (workflowStatus?.status === "PAUSED") {
        onReview();
        return;
      }
      if (workflowStatus?.status === "COMPLETED") {
        const records = await api.records(batchId);
        if (records.length) {
          onPreview();
          return;
        }
        await api.transform(batchId);
        const transformed = await api.status(batchId);
        if (transformed.status === "PAUSED") onReview(); else onPreview();
        return;
      }
      await api.propose(batchId);
      const workflow = await api.start(batchId);
      setWorkflowStatus(workflow);
      if (workflow.status === "PAUSED") {
        onReview();
      } else {
        await api.transform(batchId);
        const transformed = await api.status(batchId);
        if (transformed.status === "PAUSED") onReview(); else onPreview();
      }
    } catch (reason) {
      setError(reason instanceof Error ? reason.message : "Workflow start failed");
    } finally {
      setBusy(false);
    }
  }

  const latestWorkflowState = events.filter((event) => ["workflow_paused", "workflow_resumed"].includes(event.event_type)).at(-1);
  const paused = workflowStatus?.status === "PAUSED" || latestWorkflowState?.event_type === "workflow_paused";
  const actionLabel = workflowStatus?.status === "PAUSED" ? "Continue review" : workflowStatus?.status === "COMPLETED" ? "View results" : "Generate mappings and start";
  return <section><div className="section-heading"><div><p className="eyebrow">Workflow activity</p><h2>Live run</h2></div><StatusPill value={paused ? "PAUSED" : connection.toUpperCase()} /></div>{paused && <div className="pause-banner" role="status"><strong>Human decision required</strong><span>The workflow is safely paused. Review the open escalation to continue.</span></div>}{error && <p role="alert" className="error">{error}</p>}{!batchId ? <div className="empty"><h3>No active migration</h3><p>Create a migration to see stage progress and safe action summaries.</p></div> : <><div className="run-controls"><div><strong>Ready to analyze this batch</strong><p>Generate structured model proposals, apply deterministic policy, reconcile sources, and pause only when human review is required.</p></div><button className="primary" disabled={busy} onClick={run}>{busy ? "Analyzing securely…" : actionLabel}</button></div><ol className="timeline">{events.map((event) => <li key={event.event_id}><span>{new Date(event.timestamp).toLocaleTimeString()}</span><div><strong>{event.event_type.replaceAll("_", " ")}</strong><pre>{JSON.stringify(event.payload)}</pre></div></li>)}</ol></>}</section>;
}
