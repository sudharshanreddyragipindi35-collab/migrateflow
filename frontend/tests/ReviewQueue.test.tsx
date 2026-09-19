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

    expect(await screen.findByPlaceholderText("Enter corrected hire_date")).toHaveAttribute("type", "date");
    expect(screen.getByText(/If the correct date is unknown, reject the record instead of guessing/i)).toBeInTheDocument();
  });
});
