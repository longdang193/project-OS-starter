# Live Stability Probe Procedure

## Preconditions

1. Confirm the task worktree is based on the protocol's exact `base_revision`.
2. Confirm the protocol digest and workload digests are unchanged.
3. Confirm the recorder is evidence-only and receives results from existing
   controller, Worker, or CoS owners.
4. Run the focused protocol and recorder tests before sealing the checkpoint.
5. Record the sealed checkpoint commit, protocol digest, recorder/test digest,
   environment identity, and base revision.

## Evidence Streams

- Write exactly 18 topology rows to
  `artifacts/runtime-observation/2026-10-17-live-stability-topology-raw.jsonl`.
  Pass only this file to `benchmark_operational_comparison.py`.
- Preserve live canary summaries separately in
  `artifacts/runtime-observation/2026-10-17-live-stability-cos-canary.json`;
  do not promote operational completion to topology acceptance.
- Write exactly six fail-closed records to
  `artifacts/runtime-observation/2026-10-17-live-stability-failclosed.jsonl`.
  Validate these with bounded lifecycle tests and report logic; do not widen
  the passive topology aggregator to accept them.

## Execution Gate

Run one direct, one Worker, and one two-lane CoS canary before the remaining
topology trials. Each canary must prove attribution, the expected accepted
artifact, identity stability, settled ownership, cleanup, and no unexpected
Plan mutation. A runtime receipt with `task_result.accepted = null` is
operational evidence only; it is not semantic acceptance. Stop and preserve
separate canary evidence if acceptance is unproven, or if ownership or cleanup
becomes uncertain.

`BLOCKED_CAPABILITY` is a valid result. It records unavailable metrics and
must never be converted into an accepted result or synthetic success.

## Verdicts

Report these independently:

- `plan_execution_status`: `verified`, `blocked`, or `failed`.
- `live_stability_status`: `proven_read_only`, `inconclusive`, or `failed`.
- `optimization_disposition`: `freeze`, `inconclusive`, or
  `follow_up_required`.

Without a separately authorized write probe, the strongest possible claim is
live read-only execution/coordination stability. Do not claim full governed
write-lifecycle stability.

## Prohibitions

The recorder must not select arms, decompose work, retry, continue, accept,
settle, release ownership, mutate Plan state, or become a second task database.
Do not install providers, add credentials, change permissions, or implement a
production optimization as part of this probe.
