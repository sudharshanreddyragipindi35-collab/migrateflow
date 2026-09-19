import { useCallback, useEffect, useState } from "react";
import { api } from "../api/client";
import type { Escalation } from "../types";

const FIELD_LABELS: Record<string, string> = {
  employee_id: "Employee ID",
  first_name: "First name",
  last_name: "Last name",
  email: "Email address",
  phone: "Phone number",
  date_of_birth: "Date of birth",
  hire_date: "Hire date",
  department: "Department",
  employment_status: "Employment status",
  manager_id: "Manager ID",
  source_system: "Source system",
};

function fieldLabel(field?: string) {
  if (!field) return "Value";
  return FIELD_LABELS[field] ?? field.replaceAll("_", " ").replace(/^./, (value) => value.toUpperCase());
}

function friendlyError(field: string | undefined, message: string) {
  if (field?.endsWith("_date") || field === "date_of_birth") {
    return `${fieldLabel(field)}: enter a real date in YYYY-MM-DD format, for example 2024-01-15.`;
  }
  if (field === "employee_id" && message.toLowerCase().includes("string")) {
    return "Employee ID: enter an ID as text, for example EM202.";
  }
  const detail = message.includes(":") ? message.split(":").slice(1).join(":").trim() : message;
  return `${fieldLabel(field)}: ${detail}`;
}

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
      setError(friendlyError(item.source_context.field, reason instanceof Error ? reason.message : "The correction could not be saved."));
    }
  }

  if (!batchId || (!items.length && !error)) {
    return <section><div className="section-heading"><div><p className="eyebrow">Supervision</p><h2>Review queue</h2></div></div><div className="empty"><h3>Nothing needs review</h3><p>Start mapping from Live run. Ambiguous mappings, duplicate conflicts, and records that fail validation twice will appear here.</p></div></section>;
  }

  return <section>
    <div className="section-heading"><div><p className="eyebrow">Supervision</p><h2>Review queue</h2></div><span>{items.length} open</span></div>
    {error && <p role="alert" className="error">{error}</p>}
    <div className="card-grid">{items.map((item) => {
      const context = item.source_context;
      const recordReview = context.kind?.startsWith("record_") ?? false;
      const can = (action: string) => item.allowed_actions.includes(action);
      const alternatives = [...new Set(item.alternatives.filter(Boolean))];
      const correctionOptions = [...new Set([item.suggestion, ...alternatives].filter((value): value is string => Boolean(value)))];
      const isDateCorrection = recordReview && (context.field?.endsWith("_date") || context.field === "date_of_birth");
      const correctionId = `correction-${item.escalation_id}`;
      const helpId = `correction-help-${item.escalation_id}`;
      const displayName = fieldLabel(recordReview ? context.field : context.source_column);
      return <article className="review-card" key={item.escalation_id}>
        <div className="card-top"><span>{context.source_file}{context.source_record_id ? ` - row ${context.source_record_id}` : ""}</span><strong>{recordReview ? "Action required" : item.reason_code.replaceAll("_", " ")}</strong></div>
        <h3>{displayName}</h3>
        <p>{recordReview ? "Current value" : "Recommended target"}: <code>{String(context.current_value ?? item.suggestion ?? "Missing")}</code></p>
        {context.errors?.length ? <ul className="review-errors">{context.errors.map((message) => <li key={message}>{friendlyError(context.field, message)}</li>)}</ul> : null}
        {!recordReview && <div className="confidence">{Object.entries(item.confidence_evidence).map(([key, value]) => <label key={key}><span>{key.replaceAll("_", " ")}</span><progress max="1" value={value} /><small>{Math.round(value * 100)}%</small></label>)}</div>}
        {recordReview && <p className="review-explanation">Automatic validation could not safely fix this value. Enter the verified value below, or reject the record if you cannot confirm it.</p>}
        {can("CORRECT") && <div className="correction-field"><label htmlFor={correctionId}>{recordReview ? `Corrected ${displayName}` : "Choose the correct target field"}</label>
          {recordReview && !alternatives.length
            ? <><input id={correctionId} aria-describedby={isDateCorrection ? helpId : undefined} type={isDateCorrection ? "date" : "text"} value={correction[item.escalation_id] ?? ""} onChange={(event) => setCorrection({ ...correction, [item.escalation_id]: event.target.value })} placeholder={isDateCorrection ? "YYYY-MM-DD" : `Example: ${context.field === "employee_id" ? "EM202" : `correct ${displayName.toLowerCase()}`}`} />{isDateCorrection && <p id={helpId} className="format-help"><strong>Required format: YYYY-MM-DD</strong><span>Example: 2024-01-15 means 15 January 2024.</span><span>If the correct date is unknown, reject the record. Never guess.</span></p>}</>
            : <select id={correctionId} value={correction[item.escalation_id] ?? ""} onChange={(event) => setCorrection({ ...correction, [item.escalation_id]: event.target.value })}><option value="">Select a correction</option>{correctionOptions.map((value) => <option key={value} value={value}>{value}</option>)}</select>}
        </div>}
        <div className="actions">{can("REJECT") && <button onClick={() => decide(item, "REJECT")}>{recordReview ? "Reject record" : "Reject"}</button>}{can("CORRECT") && <button className="primary" onClick={() => decide(item, "CORRECT")}>Save correction</button>}{can("APPROVE") && <button className="primary" onClick={() => decide(item, "APPROVE")}>Approve</button>}</div>
      </article>;
    })}</div>
  </section>;
}
