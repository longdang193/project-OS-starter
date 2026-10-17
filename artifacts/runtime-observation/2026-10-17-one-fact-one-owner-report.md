# One Fact, One Owner CoS Canary Report

## Scope

- Checkpoint: `c7dc1cf39d27a49d42f9a3c9641f8391c6806e5c`
- Protocol: `one-fact-one-owner-cos-canary-2026-10-17`
- Protocol digest: `bb1f8e7c5eca765123b06cc8394c7f07d306d4f65526cfaa509138a0209f21a6`
- Runner: `scripts/herdr_parallel_dispatch.py`
- Workload: two predeclared independent read-only lanes, concurrency `2`, no refill

## Operational Evidence

| Lane | Exit | Task result | Settlement | Capacity | Grant | Cleanup | Worker `accepted` |
| --- | ---: | --- | --- | --- | --- | --- | --- |
| `cos-canary-a` | `0` | `reported_completed` | `confirmed` | `retired` | `verified` | `removed` | absent |
| `cos-canary-b` | `0` | `reported_completed` | `confirmed` | `retired` | `verified` | `removed` | absent |

Both lanes reported the exact checkpoint head `c7dc1cf39d27a49d42f9a3c9641f8391c6806e5c`. The bound lifecycle projections recorded terminated descendants, removed role views, and no recovery requirement, with assignment, task, grant, capability, and source digests preserved per lane. The canonical serialized TaskResult omitted `accepted`; because the parser strips legacy fields, this artifact does not claim to prove the raw unnormalized Worker payload.

## Acceptance Boundary

The bounded dispatch run produced operational completion and `acceptance_pending` for both lanes. It did not produce a real CoS/controller `AcceptanceDecision` with exact Plan, candidate, attempt, and evidence bindings. The matrix is therefore stopped; runtime completion is not promoted to semantic acceptance, no accepted row is emitted, and no Plan state is advanced.

This is an explicit acceptance-producer blocker, not a runtime failure. The next action is to run the same settled evidence through the existing native lead-controller/CoS acceptance boundary when a real producer can supply the exact controller, Plan, candidate, attempt, and evidence bindings; do not add acceptance logic to the dispatcher or synthesize an accepted result.

## Cleanup

Positive retirement evidence exists for both task-owned worktrees and panes. The task-owned Herdr sessions and worktrees will be stopped and removed before final verification; no unrelated sessions or worktrees are touched.
