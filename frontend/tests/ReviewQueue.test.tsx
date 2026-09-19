import { render, screen } from "@testing-library/react";
import { describe, expect, it, vi } from "vitest";
import { ReviewQueue } from "../src/pages/ReviewQueue";

describe("ReviewQueue", () => {
  it("uses a date picker and explains the safe unknown-date action", async () => {
    const response = new Response(JSON.stringify([{
      escalation_id: "date-review",
      source_context: {
        kind: "record_validation",
        record_id: "record-1",
        source_file: "employees.csv",
        source_record_id: "3",
        field: "hire_date",
        current_value: null,
        errors: ["hire_date: Input should be a valid date"],
      },
      suggestion: null,
      alternatives: [],
      confidence_evidence: { validation_attempts: 0 },
      reason_code: "VALIDATION_FAILED_TWICE",
      allowed_actions: ["CORRECT", "REJECT"],
      status: "OPEN",
    }]), { status: 200, headers: { "Content-Type": "application/json" } });
    vi.stubGlobal("fetch", vi.fn().mockResolvedValue(response));

    render(<ReviewQueue batchId="batch-1" onCompleted={() => undefined} />);

    expect(await screen.findByLabelText("Corrected Hire date")).toHaveAttribute("type", "date");
    expect(screen.getByText("Required format: YYYY-MM-DD")).toBeInTheDocument();
    expect(screen.getByText("Example: 2024-01-15 means 15 January 2024.")).toBeInTheDocument();
    expect(screen.getByText(/If the correct date is unknown, reject the record/i)).toBeInTheDocument();
    expect(screen.getByRole("button", { name: "Save correction" })).toBeInTheDocument();
    expect(screen.getByRole("button", { name: "Reject record" })).toBeInTheDocument();
  });

  it("explains a model recovery fallback without technical jargon", async () => {
    const response = new Response(JSON.stringify([{
      escalation_id: "mapping-review",
      source_context: { source_file: "employees.xlsx", source_column: "Emp ID" },
      suggestion: "employee_id",
      alternatives: ["manager_id"],
      confidence_evidence: { name_similarity: 1, model_proposal: 0.9 },
      reason_code: "MODEL_RECOVERY_FALLBACK",
      allowed_actions: ["APPROVE", "CORRECT", "REJECT"],
      status: "OPEN",
    }]), { status: 200, headers: { "Content-Type": "application/json" } });
    vi.stubGlobal("fetch", vi.fn().mockResolvedValue(response));

    render(<ReviewQueue batchId="batch-2" onCompleted={() => undefined} />);

    expect(await screen.findByText("Confirm safe fallback mapping")).toBeInTheDocument();
    expect(screen.getByText(/Ollama did not return a complete structured response/i)).toBeInTheDocument();
    expect(screen.getByText(/Confirm or correct it before continuing/i)).toBeInTheDocument();
  });
});
