# Live Stability Probe Report

## Scope

- Base revision: `2254a69990a1b013c17df88183d9972cf866f3c5`
- Protocol: `live-stability-probe-2026-10-17`
- Protocol digest: `6b542222c09a9a4dafaf3a543c8f0fbc1c1607d22a675405d5c59a7f2a2102e0`
- Topology evidence: `2026-10-17-live-stability-topology-raw.jsonl`
- Fail-closed evidence: `2026-10-17-live-stability-failclosed.jsonl`
- CoS canary evidence: `2026-10-17-live-stability-cos-canary.json`

## Verdicts

| Verdict | Result | Basis |
| --- | --- | --- |
| `plan_execution_status` | `verified` | Protocol, recorder, evidence capture, fail-closed checks, and report generation completed with fresh checks. |
| `live_stability_status` | `inconclusive` | The two-lane CoS canary completed operationally, but semantic acceptance was `null`; the 18-trial topology matrix remains stopped and unmeasured. |
| `optimization_disposition` | `inconclusive` | No measured topology comparison exists, so no optimization hypothesis is justified. |

## Topology Evidence

The topology stream contains exactly 18 unique rows: three repetitions for
each arm under each warm/cold condition. Those rows are the earlier valid
capability-blocked admissions and remain separate from the later canary
evidence. No synthetic accepted row was emitted.

The later two-lane CoS canary used the configured `9router`/`responses`
binding, completed both read-only lane observations, verified the runtime
grant, produced authoritative receipts, terminated descendants, and removed
generated role views. Its task results reported completion with settled
checkpoints, but semantic acceptance remained `null`. The canary gate
therefore correctly stopped the remaining matrix. This proves only an
operational read-only CoS canary, not accepted topology evidence.

The canary artifact records provider identity and configuration sources only;
no credential value or raw provider output is retained.

## Fail-Closed Evidence

Six separate deterministic probes were recorded for stale Plan revision, base
drift, attempt/receipt mismatch, timeout or silence, execution failure with
successful retirement, and cleanup failure. The focused lifecycle and receipt
tests passed with `220 passed`. The fail-closed stream is not passed to the
topology aggregator.

## Claim Boundary

This run does not prove full governed write-lifecycle stability. In particular,
it does not positively exercise Worker write, candidate creation, semantic
acceptance, accepted Plan transition, settlement, or evidence release. The
optional disposable write probe remains deferred and separately authorized.

No production optimization is implemented or recommended from this evidence.
