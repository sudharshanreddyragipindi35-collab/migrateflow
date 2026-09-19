import { useCallback, useEffect, useState } from "react";
import { api } from "../api/client";
import type { Escalation } from "../types";

export function ReviewQueue({ batchId, onCompleted }: { batchId: string; onCompleted: () => void }) {
  const [items, setItems] = useState<Escalation[]>([]);
  const [error, setError] = useState("");
  const [correction, setCorrection] = useState<Record<string, string>>({});
  const refresh = useCallback(async () => {
    if (!batchId) return;
    const all = await api.escalations(batchId);
    setItems(all.filter((item) => item.status === "OPEN"));
  }, [batchId]);

  useEffect(() => {
    if (!batchId) return;
    api.escalations(batchId)
      .then((all) => setItems(all.filter((item) => item.status === "OPEN")))
      .catch((reason: Error) => setError(reason.message));
  }, [batchId]);

  async function decide(item: Escalation, action: string) {
    const value = correction[item.escalation_id];
    if (action === "CORRECT" && !value) {
      setError("Enter or choose a corrected value before continuing.");
      return;
    }
    setError("");
    try {
      const workflow = await api.resolve(item.escalation_id, action, value);
      const recordReview = item.source_context.kind?.startsWith("record_") ?? false;
      if (workflow.status === "COMPLETED" && !recordReview) {
        await api.transform(batchId);
        const transformed = await api.status(batchId);
        if (transformed.status === "COMPLETED") {
          onCompleted();
          return;
        }
      } else if (workflow.status === "COMPLETED") {
        onCompleted();
        return;
      }
      await refresh();
    } catch (reason) {
      setError(reason instanceof Error ? reason.message : "Decision failed");
    }
  }

  if (!batchId || (!items.length && !error)) return <section><div className="section-heading"><div><p className="eyebrow">Supervision</p><h2>Review queue</h2></div></div><div className="empty"><h3>Nothing needs review</h3><p>Start mapping from Live run. Ambiguous mappings, duplicate conflicts, and records that fail validation twice will appear here.</p></div></section>;
  return <section><div className="section-heading"><div><p className="eyebrow">Supervision</p><h2>Review queue</h2></div><span>{items.length} open</span></div>{error && <p role="alert" className="error">{error}</p>}<div className="card-grid">{items.map((item) => {
    const context = item.source_context;
    const recordReview = context.kind?.startsWith("record_") ?? false;
    const can = (action: string) => item.allowed_actions.includes(action);
    const alternatives = [...new Set(item.alternatives.filter(Boolean))];
    const correctionOptions = [...new Set([item.suggestion, ...alternatives].filter((value): value is string => Boolean(value)))];
    return <article className="review-card" key={item.escalation_id}><div className="card-top"><span>{context.source_file}{context.source_record_id ? ` · row ${context.source_record_id}` : ""}</span><strong>{item.reason_code.replaceAll("_", " ")}</strong></div><h3>{recordReview ? context.field : context.source_column}</h3><p>{recordReview ? "Current value" : "Recommended target"}: <code>{String(context.current_value ?? item.suggestion ?? "Not available")}</code></p>{context.errors?.length ? <ul className="review-errors">{context.errors.map((message) => <li key={message}>{message}</li>)}</ul> : null}<div className="confidence">{Object.entries(item.confidence_evidence).map(([key, value]) => <label key={key}><span>{key.replaceAll("_", " ")}</span><progress max="1" value={value} /><small>{Math.round(value * 100)}%</small></label>)}</div>{can("CORRECT") && <label>Correction{recordReview && !alternatives.length ? <input value={correction[item.escalation_id] ?? ""} onChange={(event) => setCorrection({ ...correction, [item.escalation_id]: event.target.value })} placeholder={`Enter corrected ${context.field ?? "value"}`} /> : <select value={correction[item.escalation_id] ?? ""} onChange={(event) => setCorrection({ ...correction, [item.escalation_id]: event.target.value })}><option value="">Select a correction</option>{correctionOptions.map((value) => <option key={value} value={value}>{value}</option>)}</select>}</label>}<div className="actions">{can("REJECT") && <button onClick={() => decide(item, "REJECT")}>Reject</button>}{can("CORRECT") && <button onClick={() => decide(item, "CORRECT")}>Correct</button>}{can("APPROVE") && <button className="primary" onClick={() => decide(item, "APPROVE")}>Approve</button>}</div></article>;
  })}</div></section>;
}
