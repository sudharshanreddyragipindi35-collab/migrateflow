export type View = "new" | "live" | "review" | "preview" | "audit";
export interface WorkflowEvent { event_id: number; batch_id: string; timestamp: string; level: string; event_type: string; payload: Record<string, unknown>; }
export interface Escalation { escalation_id: string; source_context: { source_file?: string; source_column?: string }; suggestion: string | null; alternatives: string[]; confidence_evidence: Record<string, number>; reason_code: string; status: string; }
export interface RecordPreview { record_id: string; source_record_id: string; source_file: string; original: Record<string, unknown>; transformed: Record<string, unknown>; status: string; errors: string[]; provenance: Array<{ field: string; rule: string; reason: string }>; }
export interface PushResult { target_write_id: string; source_record_id: string; status: string; retry_count: number; }

