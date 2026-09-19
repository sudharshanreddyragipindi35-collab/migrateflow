# MigrateFlow Demo Script

## 0:00 to 0:35 Problem and boundary

Open the New Migration view. Explain that MigrateFlow reconciles employee exports while deterministic policy retains execution authority. Point out the local-model and PII-safe indicators. Do not describe hidden reasoning; focus on visible evidence and actions.

## 0:35 to 1:05 Multiple source files

Drag in `employees_india.csv`, `employee_master.xlsx`, and `new_joiners.csv` together. Show the filename and size list and the employee target contract. Create the batch and move to Live Run.

## 1:05 to 1:45 Automatic mapping and pause

Generate mapping proposals using Ollama or the labelled deterministic fallback. Start the workflow. Show obvious aliases such as Employee ID, Work Email, and Department applying automatically. Pause on the one genuine ambiguity: `start_date` includes a day/month form that cannot be interpreted safely. Highlight the yellow paused banner and event timeline.

## 1:45 to 2:30 Human correction and resume

Open Review Queue. Show masked context, recommendation, alternatives, confidence components, and the reason code. Select `hire_date`, choose Correct, and submit. Return to Live Run and show that the same batch thread resumed and completed. Mention that a repeated decision is rejected safely and every human action is audited.

## 2:30 to 3:15 Cleanup and validation

Open Data Preview. Filter between Valid and Escalation. Compare original and transformed values, including trimmed text and lowercased email. Point out field provenance and the record whose ambiguous date remains unchanged instead of being guessed. Explain that missing required values remain explicit failures.

## 3:15 to 4:05 Push retry and rollback

Open Integration Audit. Push valid records with demo failures enabled. Show the deliberate retryable result for `retry.noah@example.test`, select Retry failed, and confirm success with retry count one. Open the audit chronology or JSON export. Choose Rollback batch, acknowledge the confirmation, and show only this batch moving to Rolled Back.

## 4:05 to 4:30 Evidence and close

Open `/docs` briefly to show the API contract. Finish with the implementation checklist and final validation report: backend and frontend quality gates, supervised end-to-end test, Docker health check, PII and injection tests, and evaluation metrics.

