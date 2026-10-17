# CoS Acceptance Handoff Canary Report

## Result

- Status: `PASS` for the bounded local read-only controller boundary.
- Implementation checkpoint: `07fe73c4c8ecd206b1cdd96471125828a5125fd9`.
- Evidence: `artifacts/runtime-observation/2026-10-17-cos-acceptance-handoff-canary.json`.
- Protocol: `artifacts/runtime-observation/2026-10-17-live-stability-probe-protocol.json`.
- Protocol digest: `6b542222c09a9a4dafaf3a543c8f0fbc1c1607d22a675405d5c59a7f2a2102e0`.

## Accepted Controller Boundary

The controller producer `scripts/project_os_runtime/acceptance_handoff.py:handoff_acceptance`
inspected two attempt-bound lane artifacts, called the existing
`evaluate_acceptance()` and `validate_acceptance_decision()` boundary, and
forwarded the validated `PASS` to the existing guarded Plan transition API.
The temporary Plan moved `Task 1` from `active` to `completed` and prepared
dependent `Task 2` from `pending` to `active`. The live-probe writer accepted
the resulting `AcceptanceDecision(PASS)` as an observed `cos_two_lane` row with
zero validation errors. This is controller-boundary evidence over settled
artifacts; it is not a claim that a provider or Herdr worker was launched.

## Recovery and Resources

The persisted `cos-acceptance-handoff/v1` record was replayed after the Plan
transition. Replay was authorized as idempotent (`replayed: true`) while the
already-completed task prevented a second transition; the canary records one
attempt identity. The canonical
`secretary-resource-inventory/v1` reduced duplicate observations to one
workspace and one pane, both settled (`removed` or `already_absent`) with
reuse unblocked. A conflicting workspace observation was quarantined and kept
reuse blocked. These are supplied owner observations; physical cleanup is not
proven by this local canary.

## Fail-Closed Cases

The canary rejected stale head, missing evidence, receipt mismatch,
verification failure, artifact freshness mismatch, stale attempt, and
dependent-plan mismatch without changing the active task. The dependent-plan
case demonstrates that a decision can be
`PASS` while the dependent consequence remains unauthorized when its binding
does not match. A missing CoS producer was rejected by
`record_cos_result()` because no real `AcceptanceDecision(PASS)` was present.

## Boundaries and Deferrals

- Semantic acceptance remains owned by CoS; runtime owns settlement and
  resource disposition; Worker acceptance metadata is not used.
- No provider credentials, raw provider output, or write-lifecycle resources
  were used or retained.
- Provider/Herdr execution, physical cleanup, and process-level controller
  restart remain unproven capability boundaries and must not be inferred from
  this fixture-backed controller canary.
- Disposable write-lifecycle qualification and accepted-outcome topology
  benchmarking remain separate follow-up plans, as required by the approved
  scope.
