---
artifact_type: plan
template_id: implementation-plan
status: active
layer: change
name: git-tracked-coordination-live-probe
parent_spec: docs/superpowers/specs/2026-08-06-plan-linked-harness-coordination.md
targets:
  - packages/harness-core/src/harness_core/coordination.py
related_features:
  - managed-harness
  - plan-coordination
coordination:
  target_branch: main
  base_ref: HEAD
  tasks:
    - id: coordination-proof
      depends_on: []
      execution_mode: single_work_lane
      allowed_paths: [packages/harness-core/src/harness_core/coordination.py]
      planned_write_paths: []
---

# Git-Tracked Coordination Live Probe

## Goal

Prove one launcher-managed, read-only coordination task binds Git-tracked plan
identity into an immutable packet and terminal run evidence.

## Implementation Outcomes

### Coordination Evidence

One terminal managed run records plan reference, task ID, digest, derived base,
and read-only workspace evidence without product changes.

## Execution Approach

- Mode: `single_work_lane`
- Required skills: `skill-backend-verification`
- Isolation: current workspace
- Commit policy: external authorization
- Parallel ownership: none
- Sequential fallback: none

## Task Breakdown

### Task 1: Dispatch Read-Only Coordination Proof

**Coordination ID:** `coordination-proof`

**Purpose:**
- Dispatch one bounded read-only managed task through active launcher runtime.

**Files And Symbols:**
- Inspect: `packages/harness-core/src/harness_core/coordination.py`

**Verification:**
- Packet records immutable plan binding and task-derived read-only paths.
- Terminal run evidence records no source change.

## Verification

- Run `coordination-status` before dispatch.
- Run launcher `doctor`, `capabilities`, and `preflight` before packet creation.
- Inspect final packet and run state after terminal closure.

## Completion Criteria

- One terminal run proves plan-bound launcher dispatch or preserves a factual
  pre-dispatch block without creating a packet.
