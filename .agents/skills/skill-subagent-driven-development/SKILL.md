---
name: skill-subagent-driven-development
description: Use when an approved plan needs sequential fresh subagents under validated harness packets.
required_reads: []
distribution_tier: starter_kit
---
# Subagent-Driven Development

Use only when controller selects `sequential_agents` in a managed harness run
and host adapter capability is `enforced`. `skill-executing-plans` owns
ordinary direct execution.

## Controller Contract

- Controller classifies request, selects only `low`, `normal`, or `high`, and
  starts managed run through host-supplied `run_managed` adapter boundary.
- Run record owns immutable attempt packet, lanes, claims, change-set evidence,
  friction, outcomes, decisions, and state history under `.harness/runs/`.
- Packet owns allowed paths, planned write paths, resolved base commit,
  workspace, tools, checks, approval gates, required rules, and orchestration
  mode.
- One implementer runs at once in current workspace. No child-agent spawning.
- Implementer returns `claimed_result`, never `verified`.
- Harness records outcome after dispatch, claim collection, and verification.
  Controller alone calls `apply_controller_decision` to accept, retry,
  escalate, request approval, or block. Commit policy remains separate.
- Generic CLI has no platform agent adapter. It must return
  `execution_mode_unavailable`, not claim dispatch occurred.

## Per Task

1. Controller builds version-2 request with typed criteria and planned write
   paths, then starts run through enforced host adapter.
2. Harness authorizes planned protected paths, prepares workspace, dispatches,
   collects claim, snapshots actual changes, and records criterion evidence.
3. Implementer changes only lane paths, runs task-local proof, and reports
   claim, changed files, concerns, and normalized friction.
4. If review is required, controller obtains read-only reviewer evidence. Review
   cannot authorize protected paths; approval cannot prove semantic criteria.
5. Controller records one allowed decision. Retry, escalation, and approval
   resume create successor attempts; prior packets and evidence stay unchanged.

## Stop

Stop with managed `block` when host capability is unavailable, lane scope
overlaps another active writer, proof cannot run, or approval gate triggers.
Do not use manual controller glue to bypass recorded outcome or decision.
