---
layer: change
artifact_type: plan
status: completed
template_id: implementation-plan
contract_version: "1"
name: runtime-live-probe-double-owner
parent_spec: docs/superpowers/specs/2026-09-14-parallel-deepagents-dispatch-spec.md
targets:
  - scripts/herdr_main_launcher.py
  - scripts/herdr_parallel_dispatch.py
  - scripts/project_os_runtime
  - tests/test_herdr_main_launcher.py
  - tests/test_herdr_parallel_dispatch.py
  - tests/test_project_os_runtime.py
---

# Runtime Live Probe: Double Ownership

## Goal

Verify current runtime ownership boundaries with live Herdr/DeepAgents evidence
and avoid patching already-correct behavior.

## Implementation Outcomes

- Live lifecycle receipt proves worker exit, cleanup, descendant termination, and recovery state.
- Independent caller audits confirm one owner for admission, settlement, and pane lifecycle.
- Only evidence-backed behavior changes receive code and regression patches.

## Objective

Run disposable live probes against current Herdr/DeepAgents runtime, confirm or
reject double ownership of admission, settlement, retry, or cleanup, trace all
shared callers, and patch only evidence-backed defects.

## Constraints

- Base: `3b64fb1b657c3617631a389d92a7d5d1b69740df`.
- Preserve current uncommitted runtime-boundary changes.
- No commit, push, merge, deployment, or user-local runtime mutation.
- Use `skill-systematic-debugging`; use `skill-test-driven-development` for behavior changes.
- Each lane owns isolated worktree and returns root cause, caller trace, probe output, patch, and tests.

## Execution Approach

- Mode: `parallel-capable`
- Coordination: `git-tracked`
- Required skills: `skill-systematic-debugging`, `skill-test-driven-development`
- Isolation: two fresh worktrees from reviewed base with current uncommitted changes applied
- Commit policy: `no commits during execution`
- Acceptance: Codex compares lane evidence and integrates only proven shared-owner fixes

## Coordination State

- Coordination owner: `single lead controller`
- Coordination schema: `2`
- Branch: `codex/runtime-semantic-boundary`
- Base commit: `3b64fb1b657c3617631a389d92a7d5d1b69740df`
- Expected workspace: current runtime-boundary worktree plus two disposable probe worktrees
- Next action: none; live probe complete
- Blockers: none

| Task | State | Workspace | Executor | Depends On | Required Proof | Evidence |
| --- | --- | --- | --- | --- | --- | --- |
| Task 1 | `completed` | isolated probe A | `deepagents` | none | lifecycle probe, caller trace, regression proof | Worker exited and cleanup settled; Herdr report transport timed out; no code delta accepted |
| Task 2 | `completed` | isolated probe B | `deepagents` | none | independent sibling audit and source reproduction | No duplicate owner found; one admission/result; `231 passed`; no code delta |
| Task 3 | `completed` | current | `codex` | Tasks 1–2 | controller-owned live smoke and final validation | Live receipt confirmed; `231 passed`; repository diff clean |

## Parallel lanes

| Task | Owner | Scope | Proof |
| --- | --- | --- | --- |
| Probe A | Herdr MAIN AGENT | End-to-end launcher/worker/receipt lifecycle; patch confirmed shared-owner defect | live probe, caller trace, focused regression, compile, diff check |
| Probe B | Herdr MAIN AGENT | Independent sibling-path audit for duplicate admission/settlement/retry/cleanup ownership; patch only confirmed defect | live probe or source reproduction, caller trace, focused regression, compile, diff check |

## Task Breakdown

### Task 1: Probe A — End-to-End Ownership Trace

**Template Profile:**
- Controller-selected: `high`
- Selection basis: lifecycle ownership and root-cause depth

**Steps:**
- [x] Run live Herdr/DeepAgents lifecycle probe.
- [x] Trace admission, settlement, cleanup, retry, and acceptance callers.
- [x] Patch only a proven shared-owner defect.

### Task 2: Probe B — Independent Sibling Audit

**Template Profile:**
- Controller-selected: `normal`
- Selection basis: independent sibling-path audit

**Steps:**
- [x] Reproduce admission/result emission and inspect sibling paths.
- [x] Search for duplicate lifecycle owners.
- [x] Add regression proof only if behavior changes.

### Task 3: Controller Live Smoke

**Template Profile:**
- Controller-selected: `normal`
- Selection basis: bounded live verification

**Steps:**
- [x] Run read-only live smoke through Herdr/DeepAgents.
- [x] Confirm lifecycle receipt and no working-tree mutation.
- [x] Run focused tests, obsolete-helper scan, and diff checks.

## Acceptance

Codex compares both diffs, rejects speculative or overlapping fixes, integrates
only the smallest evidence-backed patch, then runs full runtime and repository
validation.

## Findings

- Probe A worker exited with cleanup removed, descendants terminated, and
  recovery false, but Herdr observation transport timed out and no report was
  accepted. No diff or patch integrated.
- Probe B independently found no duplicate owner. Source reproduction emitted
  one admission and one result; shared callers resolve to dispatcher admission,
  shared settlement, and launcher pane ownership. No diff or patch produced.
- Controller-owned live smoke passed through Herdr/DeepAgents: `231 passed`,
  worker exit `0`, cleanup removed, descendants terminated, recovery false.
- Existing runtime-boundary patch remains accepted. No new behavior change
  justified by live evidence; no regression patch added.

## Verification

- `py -3 -m pytest -q tests/test_project_os_runtime.py tests/test_herdr_parallel_dispatch.py tests/test_herdr_main_launcher.py` — `231 passed`.
- Live Herdr receipt — delivery confirmed, execution completed, lifecycle
  receipt confirmed, completion marker observed.
- Both isolated lane diffs compared; no lane-owned code changes.
- No obsolete helper definitions remain; `git diff --check` passed.

## Completion Criteria

- Independent lanes complete with accepted or explicitly rejected evidence.
- Live smoke passes with settled lifecycle receipt and no working-tree mutation.
- Repository planning and contract validators pass.
