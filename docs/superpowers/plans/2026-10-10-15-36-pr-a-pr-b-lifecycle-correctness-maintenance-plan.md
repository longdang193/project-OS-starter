---
artifact_type: plan
template_id: implementation-plan
contract_version: "1"
status: active
layer: change
name: pr-a-pr-b-lifecycle-correctness-maintenance
targets:
  - scripts/project_os_runtime/acceptance.py
  - scripts/project_os_runtime/plan_preparation.py
  - scripts/project_os_runtime/reconciliation.py
  - scripts/project_os_runtime/attempt.py
  - scripts/project_os_runtime/secretary_evidence.py
  - scripts/project_os_runtime/secretary_adapter.py
  - scripts/project_os_runtime/secretary_events.py
  - scripts/dcode_project.py
  - scripts/herdr_main_launcher.py
  - scripts/herdr_parallel_dispatch.py
  - .github/workflows/repo-contracts.yml
  - .github/workflows/runtime-contracts.yml
  - docs/operating_system/runtime/runtime-surfaces.md
  - docs/operating_system/templates/implementation-plan-template.md
  - tests/test_evidence_release.py
  - tests/test_project_os_runtime.py
  - tests/test_plan_preparation.py
  - tests/test_reconciliation.py
  - tests/test_project_os_reconciliation.py
  - tests/test_dcode_project.py
  - tests/test_herdr_attempt_contract.py
  - tests/test_herdr_main_launcher.py
  - tests/test_herdr_parallel_dispatch.py
  - tests/test_secretary_evidence.py
  - tests/test_secretary_adapter.py
  - tests/test_secretary_events.py
  - tests/test_secretary_receipts.py
  - tests/test_secretary_live_runtime.py
  - tests/test_secretary_live_pilot.py
---

# Review verdict: accepted with execution corrections

The architecture is approved with the execution contract below. PR #71's
merged base for this plan is fixed at `c6ce63cccb6b0c66eab57fb7a3c4ed508852e7ee`.
`07d9046627bb102ed77904af0d6c86df19e41dec` is recorded only as the PR #71
head/convergence reference, not as the implementation base. The current
checkout's 9router overlay and untracked artifacts are not part of either PR.

# Implementation Plan

## Goal

Deliver two reviewable pull requests without reopening the one-authority
lifecycle architecture:

- **PR A — Correctness hardening:** make evidence release replay-safe, bind
  release to the exact physical artifact, require a Git-recorded Plan
  consequence before disposal, and make GitHub review evidence represent the
  effective policy outcome rather than review identity alone.
- **PR B — Maintenance/resource reduction:** compact terminal attempt history,
  reduce Secretary to a consequence/attention consumer, remove `next_action`
  only when production inventory proves it is derived-only, add measured
  exclusive Herdr-session provenance, separate CI ownership, and stop plan
  guidance from copying mutable remote status.

Preserve these authorities throughout: Plan owns scope and acceptance
criteria; Git owns local coordination consequences; GitHub owns PR/check/review
and merge state; CoS owns semantic acceptance; runtime owns process ownership
and retry exclusion; Secretary owns cross-workstream attention only.

## Implementation Outcomes

### PR A correctness hardening

`release_authorized_evidence()` and its attempt-guard path treat `removed` and
`already_absent` records as terminal no-ops. A `pending` record contains the
attempt identity, exact attempt-owned root and relative path, content or
artifact digest, and producer/schema identity; deletion is rejected and the
artifact is preserved on any binding, containment, symlink, type, or digest
mismatch.

Plan acceptance first persists an immutable pending release binding, then runs
the guarded worktree transition; disposal becomes eligible only after a
verified Git checkpoint contains the accepted Plan revision. Local Plan
acceptance remains usable when GitHub is unavailable. Remote integration requires an ephemeral effective
review-policy result, current-head applicability, and required checks; comment,
changes-requested, dismissed, or stale-head reviews do not satisfy approval.

The PR A regression matrix proves replacement-file safety, exact artifact
binding, uncommitted and wrong-commit retention, successful checkpoint release,
review-policy states, GitHub outage behavior, and idempotent replay. PR B owns
shared-session preservation, compaction, Secretary, `next_action`, session,
and CI-maintenance scenarios.

### PR B maintenance and resource reduction

Detailed release maps compact at the owner-controlled terminal boundary into a
minimal generation/tombstone that still rejects obsolete attempts. No TTL
sweeper or second cleanup database is introduced.

Secretary receives consequence and attention references plus the reconciled
result; it does not reimplement Plan/Git/Worker/settlement/GitHub lifecycle
semantics. `next_action` is removed only if non-test production inventory shows
that controllers already derive actions from phase and eligibility; otherwise
it is retained unchanged with the inventory recorded in the PR evidence.

Herdr records whether a session pre-existed, was created by the attempt, or is
shared/default. Session deletion is not enabled by default: three identical
representative runs first measure exclusive empty sessions after completion.
Deletion is implemented only when those runs show retained exclusive sessions;
shared/default sessions remain preserved. Worktree cleanup remains owned by the
branch-finishing flow, never runtime retirement.

Repository Contracts owns static/planning/config/generated-drift checks;
Runtime Contracts owns reconciliation, acceptance/release, Herdr, DeepAgents,
Secretary, and OS behavior; Benchmark owns performance only. Plan/template
guidance records durable identifiers and evidence references, not mutable prose
about current GitHub state.

## Activation And PR Topology

- The plan remains `proposed` until the user approves execution.
- After approval, the lead controller creates a PR A branch and dedicated
  worktree from `c6ce63cccb6b0c66eab57fb7a3c4ed508852e7ee`, places this plan in
  that worktree, selects a registered executor and template profile for Task 1
  (or records `none (lead controller)` when the controller owns the task),
  binds coordination state to the actual branch/worktree, validates the
  activated plan, changes `status: proposed` to `status: active`, marks Task 1
  `active`, and creates a coordination checkpoint commit containing that plan
  revision before implementation begins. The same executor/profile resolution
  and validation occurs before each later task becomes `active`.
- PR A contains Tasks 1–5. After its local ready gate and user-authorized
  push/PR/remote CI/merge, refresh `origin/main` and create a new PR B
  branch/worktree from the merged PR A commit. Carry the active plan forward;
  do not restart it from `proposed`.
- PR B contains Tasks 6–9 and ends at its own local ready gate and
  user-authorized push/PR/remote CI/merge. Never execute PR B work in the PR A
  worktree after PR A is merged.
- Each task ends with a coordination checkpoint that records task state,
  evidence references, and the next task. A checkpoint may include
  implementation changes, but its durable plan revision is verified before
  evidence-release eligibility is granted.

## Execution Approach

- Mode: `inline sequential`
- Coordination: `git-tracked`
- Required skills: `skill-executing-plans`, `skill-code-standards`, `skill-test-driven-development`, `skill-backend-verification`, `skill-systematic-debugging`, `skill-requesting-code-review`, `skill-verification-before-completion`
- Isolation: `PR A dedicated worktree from the fixed PR #71 merge commit; PR B new dedicated worktree from the merged PR A commit`
- Commit policy: `verified per-task checkpoint commits are preauthorized; one implementation PR for PR A and one for PR B`
- Preauthorized local actions: `inspect source and history, edit declared files, run declared validators/tests/benchmarks, create bounded checkpoint commits in the execution worktree, and prepare the two PRs`
- User-approval actions: `push, merge, branch retargeting, force-push, protection changes, destructive recovery, worktree deletion, and cleanup outside the execution worktree`
- Parallel ownership: `none; PR B depends on PR A and all tasks share lifecycle contracts`
- Sequential fallback: `activate → PR A Tasks 1–5 → local/remote gates and merge → PR B Tasks 6–9 → local/remote gates and merge`

## Coordination State

- Coordination owner: `single lead controller`
- Coordination schema: `2`
- Branch: `codex/pr-a-lifecycle-correctness` from `c6ce63cccb6b0c66eab57fb7a3c4ed508852e7ee`; PR B branch from the merged PR A commit; do not use local main a8a1fc5`
- Base commit: `PR A = c6ce63cccb6b0c66eab57fb7a3c4ed508852e7ee; PR #71 head reference only = 07d9046627bb102ed77904af0d6c86df19e41dec`
- Expected workspace: `C:\Users\HOANG PHI LONG DANG\.codex\worktrees\pr-a-lifecycle-correctness\project-OS-starter; PR B will use a new dedicated worktree; preserve the current main checkout's 9router overlay, untracked plans, db/, .playwright-mcp/, and temp_evidence.json`
- Next action: `implement Task 3 Git-recorded Plan consequence gating`
- Blockers: `push, merge, remote CI, and worktree transitions remain approval-gated`

| Task | State | Workspace | Executor | Depends On | Required Proof | Evidence |
| --- | --- | --- | --- | --- | --- | --- |
| Task 1 | `completed` | PR A worktree | `codex` | none | base/inventory/before-measurement proof | dc91924; baseline PASS |
| Task 2 | `completed` | PR A worktree | `codex` | Task 1 | PR A release replay and binding tests | pending checkpoint; 224 passed |
| Task 3 | `active` | PR A worktree | `codex` | Task 2 | Git consequence gating and release replay tests | pending |
| Task 4 | `pending` | PR A worktree | `unresolved` | Task 2 | effective review-policy tests | pending |
| Task 5 | `pending` | PR A worktree | `unresolved` | Tasks 3, 4 | PR A matrix, validators, review gate | pending |
| Task 6 | `pending` | PR B worktree | `unresolved` | Task 5 | compaction and obsolete-attempt tests | pending |
| Task 7 | `pending` | PR B worktree | `unresolved` | Task 6 | Secretary caller/invariant tests | pending |
| Task 8 | `pending` | PR B worktree | `unresolved` | Task 7 | next_action inventory and Herdr provenance measurement | pending |
| Task 9 | `pending` | PR B worktree | `unresolved` | Tasks 6–8 | CI/template split and PR B verification | pending |

## Task Breakdown

### Task 1: Freeze the PR #71 base, inventories, and baselines

**Purpose:**
- Establish source truth before edits and prevent the local 9router overlay or
  untracked artifacts from entering either PR.

**Task Function:**
- Establish baseline and change ownership.

**Template Profile:**
- Controller-selected: `none (lead controller)`
- Selection basis: `controller-owned activation, baseline, and coordination task`

**Validator Profile:**
- Controller-selected: `none`
- Selection basis: `lead controller owns baseline validation`

**Specification Coverage:**
- Verdict sections 4, 7, 9, and 15: preserve PR #71's one-authority lifecycle,
  keep worktree cleanup separate, split work into PR A then PR B, and capture
  before measurements before changing runtime behavior.

**Required Skills:**
- `skill-executing-plans`, `skill-code-standards`

**Files And Symbols:**
- Inspect: `c6ce63cccb6b0c66eab57fb7a3c4ed508852e7ee`; record
  `07d9046627bb102ed77904af0d6c86df19e41dec` only as the PR #71 head reference
- Inspect: `scripts/project_os_runtime/acceptance.py::release_authorized_evidence`
- Inspect: `scripts/project_os_runtime/plan_preparation.py::apply_accepted_plan_transitions`
- Inspect: `scripts/dcode_project.py::record_release_authorization`
- Inspect: `scripts/project_os_runtime/reconciliation.py::RemotePrEvidence`
- Inspect: `.github/workflows/repo-contracts.yml`, `.github/workflows/runtime-contracts.yml`
- Verify: `git status --short --untracked-files=all`, `git diff --check`, repository validators, focused baseline tests, and the existing benchmark/measurement command

**Dependencies:**
- None. The PR A worktree must already be created from the fixed base during activation.

**Authority:**
- Preauthorized local actions: `read Git/source/test/config state and run baseline validators/tests without modifying the current checkout`
- Stop for: `a base other than the merged PR #71 lifecycle result, a required source surface missing from that base, or any request to absorb the local overlay`

**Steps:**
- [x] Step 1: Record the fixed merged PR #71 SHA
  `c6ce63cccb6b0c66eab57fb7a3c4ed508852e7ee`; record
  `07d9046627bb102ed77904af0d6c86df19e41dec` only as the PR #71 head
  reference; do not substitute local `main`.
- [x] Step 2: Verify the activated PR A worktree is clean and contains the
  coordination checkpoint; do not copy current untracked files.
- [x] Step 3: Inventory every production caller and test of
  `release_authorized_evidence`, `apply_accepted_plan_transitions`,
  `RemotePrEvidence`, `next_action`, and Herdr session retirement. Check
  `release_attempt_evidence` only to confirm whether it is historical/dead; if
  it has no production caller, remove it from the implementation target set
  and do not recreate compatibility code.
- [x] Step 4: Freeze a metric-to-command/workload/provenance table and capture
  before measurements with the existing harness using reproducible workloads:
  coordination overhead, release/attempt records, retained temporary bytes,
  Secretary activations, Herdr subprocess calls, empty sessions, incorrect
  cleanup events, and fresh-controller recovery time. Mark unsupported metrics
  `UNAVAILABLE`, `NOT_APPLICABLE`, or `BLOCKED_CAPABILITY` rather than
  inventing telemetry, and record whether each result is live or synthetic.
- [x] Step 5: Run the baseline validator and focused runtime tests; save only
  command summaries, baseline outputs, and durable findings in task evidence.

**Verification:**
- [x] `git status --short --untracked-files=all` is empty in the execution worktree.
- [x] `python scripts/validate_repo_contracts.py` and the focused baseline test
  selection pass on the PR #71 base.
- [x] `git diff --check` reports no whitespace errors.
- [x] Before-measurement outputs include the exact command, workload, revision,
  and environment needed for the later candidate comparison.
- [x] The metric table covers every metric named by Tasks 8–9 and records the
  evidence source and support status for each metric.

**Task 1 Evidence:**
- Base `c6ce63cccb6b0c66eab57fb7a3c4ed508852e7ee`; activated baseline revision
  `dc91924cecd43880c892477b1ef28e4415adb9fc`; branch
  `codex/pr-a-lifecycle-correctness`; Windows `10.0.19045.0`; Python `3.13.5`.
- Production inventory found no caller of
  `scripts/project_os_runtime/results.py::release_attempt_evidence`; it is
  removed from the implementation target set. Canonical release callers are
  `acceptance.py::release_authorized_evidence` and
  `plan_preparation.py::apply_accepted_plan_transitions`.
- `python scripts/validate_repo_contracts.py`: PASS. Focused baseline command
  covering the Task 1 runtime/release/reconciliation/Herdr/Secretary files:
  `656 passed in 14.24s`.
- `python scripts/benchmark_secretary_architecture.py 1`: deterministic-fake,
  `live=false`, `latency_ms=null`, and `token_usage=null`; usable only for
  synthetic coordination/Secretary comparison, not live resource or recovery
  evidence.
- `python scripts/benchmark_worker_contract.py offline --fixtures
  tests/fixtures/worker_contract_benchmark/manifest.json --output
  worker-baseline.jsonl` plus `report`: six tasks, median handoff reduction
  `11.17%`, aggregate reduction `10.89%`; offline synthetic evidence only.
- Retained temporary bytes, Herdr subprocess calls, empty sessions, and
  fresh-controller recovery time are `BLOCKED_CAPABILITY`; incorrect cleanup
  remains a direct lifecycle-regression metric rather than a live benchmark
  claim.

**Exit Criteria:**
- The exact base, owned files, production callers, baseline commands, and
  preserved unrelated workspace state are recorded; no implementation starts
  from local `main`.

### Task 2: Make evidence release terminal-safe and physically bound

**Purpose:**
- Prevent a replay of a completed release from deleting a replacement file and
  prevent pending authorization from following a changed path or artifact.

**Task Function:**
- Harden the canonical evidence-disposal boundary.

**Template Profile:**
- Controller-selected: `none (lead controller)`
- Selection basis: `controller-owned implementation and task-checkpoint work`

**Validator Profile:**
- Controller-selected: `none`
- Selection basis: `focused regression proof is task-local`

**Specification Coverage:**
- Verdict sections 1 and 15: immutable terminal release records and exact
  attempt/path/content identity.

**Required Skills:**
- `skill-code-standards`, `skill-test-driven-development`, `skill-backend-verification`

**Files And Symbols:**
- Modify: `scripts/project_os_runtime/acceptance.py::release_authorized_evidence`
- Modify: `scripts/dcode_project.py::record_release_authorization`,
  `_claim_attempt_unlocked`, and the attempt-guard persistence helpers
- Inspect only: `scripts/project_os_runtime/results.py::release_attempt_evidence`
  as a historical/dead-path check; modify it only if Task 1 proves a current
  production caller exists and adds it back to the owned target set.
- Verify: `tests/test_evidence_release.py`, `tests/test_project_os_runtime.py`,
  `tests/test_dcode_project.py`

**Dependencies:**
- Task 1 production caller inventory.

**Authority:**
- Preauthorized local actions: `modify only the canonical release path and its focused tests; preserve the existing one-authority lifecycle and resource states`
- Stop for: `a second release owner, a new cleanup database, TTL cleanup, or a deletion path that cannot prove exact artifact identity`

**Steps:**
- [x] Step 1: Normalize the release record so each resource stores
  `attempt_id`, `evidence_ref`, `attempt_root`, `relative_path`,
  `content_sha256` or artifact identity, and producer/schema identity.
- [x] Step 2: In `release_authorized_evidence`, return the recorded terminal
  result immediately for `removed` and `already_absent`; do not inspect,
  resolve, or unlink the current filesystem path on that branch.
- [x] Step 3: Permit filesystem mutation only for `pending`, after verifying
  the binding matches the current attempt, the resolved path remains inside the
  exact attempt root, the path is a regular non-symlink file, and its digest or
  artifact identity still matches.
- [x] Step 4: Return `replacement_detected` or `binding_mismatch` with the
  resource preserved and unresolved; record `removed`, `already_absent`, or
  `unverified` exactly once for the authorized resource.
- [x] Step 5: Preserve compatibility for legacy records only through a bounded
  migration/read path; never infer a new physical binding from a replayed path.

**Verification:**
- [x] Terminal `removed` plus replacement file leaves the replacement.
- [x] Terminal `already_absent` plus replacement file leaves the replacement.
- [x] Pending changed path, changed digest, wrong attempt, symlink, non-file,
  and out-of-root path all preserve the artifact.
- [x] Valid pending exact artifact is removed once; a repeat is a terminal
  no-op and performs no filesystem mutation.
- [x] `python -m pytest -q tests/test_evidence_release.py
  tests/test_project_os_runtime.py tests/test_plan_preparation.py
  tests/test_dcode_project.py`: `224 passed in 7.41s`.
- [x] `python scripts/validate_repo_contracts.py --repo-root . --fast --plan
  docs/superpowers/plans/2026-10-10-15-36-pr-a-pr-b-lifecycle-correctness-maintenance-plan.md`:
  PASS; `git diff --check`: PASS.

**Exit Criteria:**
- Focused release and attempt-guard tests pass, and no production release path
  can delete a replacement artifact after a terminal record.

### Task 3: Gate evidence disposal on a Git-recorded Plan consequence

**Purpose:**
- Ensure an atomic Plan write is not treated as durable coordination truth until
  a verified Git checkpoint contains the accepted revision.

**Task Function:**
- Separate accepted transition, checkpoint verification, and evidence disposal.

**Template Profile:**
- Controller-selected: `none (lead controller)`
- Selection basis: `controller-owned Git/release contract implementation and checkpoint work`

**Validator Profile:**
- Controller-selected: `none`
- Selection basis: `direct boundary and replay tests cover the gate`

**Specification Coverage:**
- Verdict sections 2, 4, and 15: Git owns Plan consequences; GitHub remains
  independent for local acceptance; release follows checkpoint C2.

**Required Skills:**
- `skill-code-standards`, `skill-test-driven-development`, `skill-backend-verification`

**Files And Symbols:**
- Modify: `scripts/project_os_runtime/plan_preparation.py::apply_accepted_plan_transitions`
  and `_apply_plan_transitions_locked`
- Modify: `scripts/project_os_runtime/acceptance.py::authorize_evidence_release`
  and `release_authorized_evidence`
- Verify: `tests/test_plan_preparation.py`, `tests/test_evidence_release.py`,
  `tests/test_project_os_reconciliation.py`
- Document: `docs/operating_system/runtime/runtime-surfaces.md`

**Dependencies:**
- Task 2 exact release record and attempt binding. Task 3 is independent of
  Task 4; it does not wait for remote review-policy normalization.

**Authority:**
- Preauthorized local actions: `edit Plan/release contracts and add a direct Git checkpoint verifier; keep GitHub out of local Plan acceptance`
- Stop for: `release after an uncommitted write, acceptance of a commit that does not contain the expected Plan revision, or a generic durability database`

**Steps:**
- [ ] Step 1: Extend the canonical Git consequence with `owner: git`,
  `commit_sha`, `coordination_ref`, `plan_path`, and
  `expected_plan_revision`; leave `commit_sha` unset in the pre-commit record.
- [ ] Step 2: Persist the immutable pending release binding before the guarded
  Plan transition, or atomically with the transition under the existing owner
  lock. The low-level Plan writer remains Git-agnostic and does not create
  commits or invoke Git.
- [ ] Step 3: Perform the accepted Plan transition without unlinking evidence;
  add restart/failure proof for both the persisted-pending-before-transition
  boundary and the transition-before-checkpoint boundary. Then have the
  controller/lead create the task checkpoint commit and
  verify that the checkpoint contains the expected Plan revision and is
  reachable from `coordination_ref`.
- [ ] Step 4: Supply or derive the durable checkpoint SHA only after the commit
  exists, update the pending consequence with that SHA, and make release
  eligible only after the verifier succeeds. Never require a future SHA before
  commit creation.
- [ ] Step 5: Keep pending evidence when the Plan is modified but uncommitted,
  the commit is unrelated, the revision differs, or the checkpoint is
  unreachable; complete the post-checkpoint replay idempotently without GitHub.

**Verification:**
- [ ] CoS `PASS` plus an uncommitted Plan edit preserves evidence.
- [ ] A commit missing the expected Plan revision preserves evidence.
- [ ] The correct reachable checkpoint releases the exact artifact once.
- [ ] Replaying after a completed release is a no-op; a GitHub outage does not
  block local Plan acceptance or local retirement.
- [ ] The Plan writer has no Git side effect; controller-owned checkpoint
  orchestration is separately covered.
- [ ] A restart after pending-binding persistence and a restart after the Plan
  transition both recover the same pending release without evidence loss.

**Exit Criteria:**
- The transition path returns a durable pending release until a direct Git
  checkpoint proof passes, and the runtime documentation describes the new
  lifecycle order.

### Task 4: Make remote review evidence represent effective policy

**Purpose:**
- Distinguish review identity from approval policy satisfaction at the GitHub
  evidence boundary while retaining current-head and required-check guards.

**Task Function:**
- Normalize and validate ephemeral remote integration evidence.

**Template Profile:**
- Controller-selected: `unresolved`
- Selection basis: `pending until Planning Dispatch resolves the executor profile`

**Validator Profile:**
- Controller-selected: `none`
- Selection basis: `remote policy matrix is independently testable`

**Specification Coverage:**
- Verdict section 3: effective review state, current-head applicability,
  review-not-required policy, and GitHub availability boundaries.

**Required Skills:**
- `skill-code-standards`, `skill-test-driven-development`, `skill-backend-verification`

**Files And Symbols:**
- Modify: `scripts/project_os_runtime/reconciliation.py::RemotePrEvidence`
  and `_integrate`; consume effective policy computed by the GitHub evidence
  adapter rather than deriving it in the reconciler.
- Modify: `scripts/project_os_runtime/secretary_evidence.py::build_evidence_snapshot`
  only as the compatibility adapter for normalized remote evidence
- Verify: `tests/test_reconciliation.py`, `tests/test_secretary_evidence.py`,
  `tests/test_project_os_reconciliation.py`

**Dependencies:**
- Task 2 release binding. This task is independent of Task 3's local Git
  checkpoint contract.

**Authority:**
- Preauthorized local actions: `modify the remote evidence model, adapter normalization, and focused tests only`
- Stop for: `reconstructing GitHub review history inside the reconciler or making GitHub availability mandatory for local Plan acceptance`

**Steps:**
- [ ] Step 1: Add normalized fields for `review_policy_source`,
  `review_policy_satisfied`, `effective_review_state`, `review_required`,
  `review_identity`, and `reviewed_head_sha` while preserving the existing
  current-head/check identity fields.
- [ ] Step 2: Make the GitHub evidence adapter produce one effective state from the current
  review policy: `APPROVED`, `CHANGES_REQUESTED`, `DISMISSED`, `COMMENTED`, or
  `NONE`; when review is not required, set policy satisfaction true with a
  non-empty policy source explaining why.
- [ ] Step 3: Make integration eligibility require remote availability, policy
  satisfaction, expected repository/PR/base/head identity, current required
  checks, and mergeability. Do not treat comment-only, dismissed,
  changes-requested, or stale-head approval as satisfying policy.
- [ ] Step 4: Preserve remote outage as an integration blocker only; local
  acceptance, checkpoint verification, and retirement remain runnable.

**Verification:**
- [ ] Comment-only review fails policy.
- [ ] Changes-requested review fails policy.
- [ ] Dismissed review fails policy.
- [ ] Approval bound to a stale head fails policy.
- [ ] Current effective approval and required checks pass.
- [ ] Review-not-required policy passes with its source; remote unavailable
  blocks integration without blocking local acceptance.

**Exit Criteria:**
- Integration consumes effective policy evidence from the adapter and no longer
  infers approval from review identity alone.

### Task 5: Close PR A with the focused matrix and review gate

**Purpose:**
- Prove the P0 correctness changes together without adding CI optimization or
  Secretary/session deletion work.

**Task Function:**
- Integrate and verify the correctness PR.

**Template Profile:**
- Controller-selected: `unresolved`
- Selection basis: `pending until Planning Dispatch resolves the executor profile`

**Validator Profile:**
- Controller-selected: `review-1`
- Selection basis: `independent review of release, Git, and remote-policy boundaries`

**Specification Coverage:**
- Verdict sections 4, 15, and the required regression matrix.

**Required Skills:**
- `skill-requesting-code-review`, `skill-verification-before-completion`

**Files And Symbols:**
- Verify: all PR A files and tests from Tasks 2–4
- Verify: `docs/operating_system/runtime/runtime-surfaces.md`
- Verify: `.github/workflows/runtime-contracts.yml` only for existing runtime
  coverage; do not change CI ownership in PR A

**Dependencies:**
- Tasks 2, 3, and 4 complete with focused proof.

**Authority:**
- Preauthorized local actions: `run the PR A regression matrix, validators, diff checks, and independent review; update only PR A evidence`
- Stop for: `any failed safety regression, missing direct Git proof, changed lifecycle ownership, or unrelated CI/Secretary/session edits`

**Steps:**
- [ ] Step 1: Run only the PR A matrix: terminal replay, replacement files,
  path/digest mismatch, uncommitted and wrong-checkpoint Plan consequences,
  current effective review states, review-not-required policy, remote outage,
  and obsolete replay rejection. PR B compaction, Secretary, `next_action`,
  session, and CI scenarios are reserved for PR B.
- [ ] Step 2: Run the local ready gate: `python scripts/validate_repo_contracts.py`,
  the affected runtime tests on the available local platform, `git diff --check`,
  and the focused diff/target review.
- [ ] Step 3: Request independent review against the PR A acceptance criteria;
  if review changes implementation, rerun affected proof and review the new
  code head rather than carrying forward a superseded PASS.
- [ ] Step 4: Create the final PR A checkpoint commit only after fresh proof;
  record its candidate SHA and evidence references, not mutable remote status.
- [ ] Step 5: After user-authorized push, use remote PR-head CI for Repository
  Contracts, Ubuntu Runtime, Windows Runtime, and Benchmark gates; bind final
  review to that exact PR head before merge.

**Verification:**
- [ ] Every row in the PR A regression matrix passes.
- [ ] Focused runtime tests, repository validator, and diff check pass.
- [ ] Independent review returns no unresolved correctness finding.
- [ ] Local ready-gate proof and remote PR-head proof are recorded separately.

**Exit Criteria:**
- PR A is review-ready and its checkpoint proves terminal no-op behavior,
  exact binding, Git-recorded consequence gating, and effective review policy.

### Task 6: Compact terminal attempt and release history

**Purpose:**
- Reduce retained attempt-guard state after recovery value expires without
  weakening replay rejection.

**Task Function:**
- Implement owner-controlled terminal compaction.

**Template Profile:**
- Controller-selected: `unresolved`
- Selection basis: `pending until Planning Dispatch resolves the executor profile`

**Validator Profile:**
- Controller-selected: `none`
- Selection basis: `attempt and replay tests are task-local`

**Specification Coverage:**
- Verdict section 5: compact after terminal recovery value expires and reject
  obsolete traffic from the current generation.

**Required Skills:**
- `skill-code-standards`, `skill-test-driven-development`, `skill-backend-verification`

**Files And Symbols:**
- Modify: `scripts/dcode_project.py::record_release_authorization`,
  `_claim_attempt_unlocked`, `_reconcile_attempt_unlocked`, and guard schema
- Modify: `scripts/project_os_runtime/attempt.py` only for the canonical
  generation/tombstone contract
- Verify: `tests/test_dcode_project.py`, `tests/test_herdr_attempt_contract.py`,
  `tests/test_evidence_release.py`

**Dependencies:**
- Task 5

The controller may start this task only after PR A is merged and the new PR B
worktree is created from that merge commit; evidence-release replay behavior
remains the baseline.

**Authority:**
- Preauthorized local actions: `compact only at the owner-controlled terminal boundary and preserve the minimal generation/replay tombstone`
- Stop for: `TTL-based cleanup, deleting state while recovery/replay/consumer obligations remain, or restoring full historical maps to process an obsolete message`

**Steps:**
- [ ] Step 1: Define the compaction predicate as runtime retirement complete,
  canonical consequence committed, required consumers released, all owned
  resources terminal, no recovery required, and no legitimate replay able to
  mutate state.
- [ ] Step 2: Make the attempt-generation invariant explicit: every active
  attempt carries the current generation, every terminal tombstone records the
  highest retired generation, and any lower/obsolete attempt or release message
  is rejected without reconstructing deleted history.
- [ ] Step 3: Replace detailed per-attempt release maps only after that
  predicate with current generation, last terminal generation, and release
  completion/tombstone fields.
- [ ] Step 4: Preserve legacy guard records until a verified terminal boundary
  is reached, then compact them through the same owner path.

**Verification:**
- [ ] Active, unsettled, recovery-required, and consumer-held records are not
  compacted.
- [ ] A compacted terminal record rejects obsolete attempt traffic.
- [ ] Current-generation replay remains idempotent without restoring full maps.
- [ ] The existing attempt/release tests and focused new compaction tests pass.

**Exit Criteria:**
- Terminal guard growth is bounded by the current generation/tombstone contract
  and correctness remains independent of TTL timing.

### Task 7: Reduce Secretary to consequence and attention consumption

**Purpose:**
- Remove duplicate lifecycle validation from Secretary while preserving
  cross-workstream attention routing and replay safety.

**Task Function:**
- Narrow the Secretary input contract.

**Template Profile:**
- Controller-selected: `unresolved`
- Selection basis: `pending until Planning Dispatch resolves the executor profile`

**Validator Profile:**
- Controller-selected: `none`
- Selection basis: `Secretary behavior has focused adapter and live-runtime tests`

**Specification Coverage:**
- Verdict section 8: Worker emits one result/evidence reference, CoS emits one
  semantic decision, and Secretary emits only changed project-level attention.

**Required Skills:**
- `skill-code-standards`, `skill-test-driven-development`, `skill-backend-verification`

**Files And Symbols:**
- Modify: `scripts/project_os_runtime/secretary_evidence.py::build_evidence_snapshot`
- Modify: `scripts/project_os_runtime/secretary_adapter.py::CommunicationEnvelope`,
  `ControllerSessionAdapter`, and delivery/compaction boundary
- Modify: `scripts/project_os_runtime/secretary_events.py::EventHint`,
  `coalesce_event_hints`, and `reconcile_event_hint`
- Verify: `tests/test_secretary_evidence.py`, `tests/test_secretary_adapter.py`,
  `tests/test_secretary_events.py`, `tests/test_secretary_receipts.py`,
  `tests/test_secretary_live_runtime.py`, `tests/test_secretary_live_pilot.py`

**Dependencies:**
- Task 6

PR A remote/local evidence contracts are inherited from the merged PR A commit.

**Authority:**
- Preauthorized local actions: `change Secretary inputs and adapters while keeping lifecycle decisions in reconciliation/acceptance/runtime owners`
- Stop for: `Secretary revalidating Plan/Git/Worker/settlement/GitHub lifecycle semantics or adding a second task ledger`

**Steps:**
- [ ] Step 1: Inventory all Secretary callers, producers, and tests before
  changing the input contract; record which callers provide lifecycle evidence
  versus project-level attention.
- [ ] Step 2: Define the Secretary input as task reference, canonical
  consequence reference, reconciled result, blocking references, and project
  consequence/attention delta.
- [ ] Step 3: Keep full evidence validation at the owning boundary and pass
  only references and normalized outcomes across the Secretary boundary.
- [ ] Step 4: Preserve delivery idempotency, released-controller protection,
  activation tombstones, and shared-session behavior.
- [ ] Step 5: Update live and in-memory adapters so a normal successful task
  produces zero Secretary messages unless project attention changes.

**Verification:**
- [ ] Cross-workstream attention changes still route once.
- [ ] Duplicate delivery and released-controller replay remain rejected or
  idempotent according to the existing contract.
- [ ] A normal successful task produces one assignment, one Worker result, one
  CoS decision, and zero Secretary messages.

**Exit Criteria:**
- Secretary no longer owns or duplicates lifecycle eligibility and all focused
  adapter/live tests pass.

### Task 8: Inventory `next_action` and measure Herdr session provenance

**Purpose:**
- Separate derived-state inventory from Herdr provenance measurement; enable
  exclusive-session deletion only through an explicit evidence gate.

**Task Function:**
- Perform caller inventory and measurement-gated runtime maintenance.

**Template Profile:**
- Controller-selected: `unresolved`
- Selection basis: `pending until Planning Dispatch resolves the executor profile`

**Validator Profile:**
- Controller-selected: `none`
- Selection basis: `caller inventory and representative runtime measurements`

**Specification Coverage:**
- Verdict sections 6 and 9: remove `next_action` only after production proof;
  preserve shared/default sessions; delete exclusive empty sessions only when
  measured accumulation justifies it.

**Required Skills:**
- `skill-systematic-debugging`, `skill-test-driven-development`, `skill-backend-verification`

**Files And Symbols:**
- Inspect: all non-test callers of `scripts/project_os_runtime/reconciliation.py::ReconciliationResult.next_action`
- Modify if inventory is derived-only: `scripts/project_os_runtime/reconciliation.py::ReconciliationResult`, `_result`, and `to_dict`
- Modify: `scripts/herdr_main_launcher.py::resolve_launch`, `retire_lane`, and
  session/pane/process ownership result builders only for provenance and,
  conditionally, evidence-backed deletion
- Modify: `scripts/herdr_parallel_dispatch.py::run_lane` and completion evidence
- Verify: `tests/test_reconciliation.py`, `tests/test_project_os_reconciliation.py`,
  `tests/test_herdr_main_launcher.py`, `tests/test_herdr_parallel_dispatch.py`,
  `tests/test_herdr_attempt_contract.py`

**Dependencies:**
- Task 7

The PR A review gate is inherited from the merged PR A commit.

**Authority:**
- Preauthorized local actions: `run the production caller inventory and three identical representative measurements; implement only the evidence-backed branch`
- Stop for: `a production caller that requires next_action, a shared/default session deletion, repeated polling added solely for cleanup, or a non-zero cleanup result without exact ownership proof`

**Steps:**
- [ ] Step 1: Complete the non-test `git grep` inventory for `next_action` and
  decide that contract independently: retain it with a caller contract test if
  production consumers exist; otherwise remove it from the result contract and
  diagnostic-only tests.
- [ ] Step 2: Record Herdr session provenance at creation: pre-existing,
  attempt-created, or shared/default; reuse the existing retirement inventory
  rather than adding a polling loop.
- [ ] Step 3: Run three identical representative workloads and record the
  before/after count of exclusive empty sessions left after completion, with
  the Task 1 baseline and exact workload/revision/environment.
- [ ] Step 4: If all three candidate counts are zero, retain session
  preservation and land provenance/measurement only. If any count is non-zero,
  add deletion only when
  the session was created exclusively by the attempt, all owned children and
  panes/agents retired, the session is empty, and no other consumer exists.
- [ ] Step 5: Treat session deletion as optional and measurement-gated; do not
  enable it merely because provenance exists.
- [ ] Step 6: If live Herdr measurement is unavailable, record
  `BLOCKED_CAPABILITY`, complete provenance tests and the independent
  `next_action` decision, preserve all sessions, and defer deletion without
  blocking PR B. If live probes require resources outside the execution
  worktree, stop for explicit user approval before creating or cleaning them.

**Verification:**
- [ ] The `next_action` decision is backed by a complete non-test caller list.
- [ ] Shared/default sessions remain preserved in every run.
- [ ] Exclusive-session deletion, when enabled, has direct ownership and empty
  session tests; otherwise the zero-retention measurement is recorded.
- [ ] No extra repeated observation loop is introduced.
- [ ] Candidate measurements are comparable with Task 1 before measurements;
  unsupported metrics are explicitly marked rather than fabricated.
- [ ] `BLOCKED_CAPABILITY` is an accepted measurement outcome that leaves
  preservation unchanged and does not block unrelated `next_action` work.

**Exit Criteria:**
- Derived-state removal and session cleanup are each justified by concrete
  caller/measurement evidence, not architectural preference.

### Task 9: Finish CI ownership, plan guidance, and PR B verification

**Purpose:**
- Reduce duplicate CI and documentation churn after the runtime changes are
  proven correct.

**Task Function:**
- Align maintained contracts and perform final cross-surface verification.

**Template Profile:**
- Controller-selected: `unresolved`
- Selection basis: `pending until Planning Dispatch resolves the executor profile`

**Validator Profile:**
- Controller-selected: `review-2`
- Selection basis: `independent review of CI ownership, documentation, and maintenance scope`

**Specification Coverage:**
- Verdict sections 10–14 and 15: CI split, source-of-truth matrix, durable
  references in plans, mechanical GitHub integration boundary, and retention
  hierarchy.

**Required Skills:**
- `skill-code-standards`, `skill-requesting-code-review`, `skill-verification-before-completion`

**Files And Symbols:**
- Modify: `.github/workflows/repo-contracts.yml`
- Modify: `.github/workflows/runtime-contracts.yml`
- Modify: `docs/operating_system/runtime/runtime-surfaces.md`
- Modify: `docs/operating_system/templates/implementation-plan-template.md`
- Verify: `tests/test_validate_repo_contracts.py`,
  `tests/test_validate_planning_lifecycle.py`, `tests/test_starter_lifecycle_contract.py`,
  and the full affected runtime test set

**Dependencies:**
- Tasks 6–8 complete and PR A remains green.

**Authority:**
- Preauthorized local actions: `move only duplicate behavioral tests to the owning workflow, update canonical plan/template guidance, and run final verification`
- Stop for: `path-based CI filtering before ownership is clean, mutable current-status prose in plans/templates, generated-surface edits without canonical input changes, or unrelated workflow redesign`

**Steps:**
- [ ] Step 1: Keep Repository Contracts limited to planning lifecycle,
  repository schemas/config, generated drift, and static/invariant validators.
- [ ] Step 2: Keep Runtime Contracts limited to reconciliation,
  acceptance/release, Herdr, DeepAgents, Secretary, and OS behavior; keep
  Benchmark limited to performance contract tests.
- [ ] Step 3: Update plan/template guidance to record PR numbers, candidate
  SHAs, policy sources, and evidence references, while rejecting prose that
  claims a mutable current PR/check/review state as durable truth.
- [ ] Step 4: Run the local ready gate: full repository validator, the full
  affected suite available on the local platform, diff check, and the existing
  Secretary/worker benchmark command. Compare only metrics marked supported in
  the Task 1 table; retain `UNAVAILABLE`, `NOT_APPLICABLE`, or
  `BLOCKED_CAPABILITY` outcomes for the rest. Use direct lifecycle regression
  tests for cleanup correctness, and do not present deterministic-fake
  benchmarks as live resource or operating-cost evidence.
- [ ] Step 5: Request independent review for PR B; if findings change code,
  rerun affected proof and bind the final review to the new code head.
- [ ] Step 6: Create the PR B checkpoint commit with durable candidate
  evidence, then after user-authorized push record remote PR-head CI for
  Repository Contracts, Ubuntu Runtime, Windows Runtime, and Benchmark gates.

**Verification:**
- [ ] `python scripts/validate_repo_contracts.py` passes.
- [ ] The local ready gate passes on the available platform; remote PR-head CI
  supplies Ubuntu and Windows results after authorized push.
- [ ] `git diff --check` passes.
- [ ] Benchmark comparison uses identical workloads and keeps incorrect cleanup
  events at zero where the direct lifecycle tests support that claim; unsupported
  live-resource metrics are explicitly deferred.
- [ ] CI workflow ownership has no duplicate Secretary/Herdr behavioral test
  ownership without an explicit contract reason.
- [ ] Independent review returns no unresolved PR B finding.
- [ ] Final review and remote CI are bound to the same final PR B code head.

**Exit Criteria:**
- PR B is review-ready, CI ownership is explicit, plan guidance is durable,
  and the before/after measurement supports the maintenance change without a
  correctness regression.

## Verification

- [ ] PR A focused matrix passes before any PR B implementation begins.
- [ ] PR A independent review passes against terminal release, exact binding,
  Git checkpoint, local outage, and review-policy criteria.
- [ ] PR B compaction, Secretary, `next_action`, session-provenance, and CI
  ownership tests pass after the PR A checkpoint.
- [ ] `python scripts/validate_repo_contracts.py` passes from the execution
  worktree.
- [ ] Local ready gates pass on the available platform for PR A and PR B;
  remote PR-head CI supplies Ubuntu and Windows runtime results after each
  user-authorized push.
- [ ] `git diff --check` passes.
- [ ] Identical before/after measurements compare every metric marked supported
  in the Task 1 table, including coordination overhead per accepted change,
  retained attempt/release records, retained temporary bytes, Secretary
  activations, Herdr subprocess calls, empty sessions, incorrect cleanup
  events, and fresh-controller recovery time. Unsupported or blocked metrics
  retain their explicit status and are not used for cost claims.
- [ ] Final independent review for each PR is bound to that PR's final code
  head, and no review PASS from a superseded candidate is reused.

## Completion Criteria

- PR A and PR B remain separate, ordered, and reviewable; PR B does not start
  until PR A is merged and the PR B worktree is created from that exact merge
  commit.
- Terminal evidence release never mutates a replacement artifact.
- Pending evidence release is bound to the exact attempt, path, root, and
  content/artifact identity.
- Evidence survives until the accepted Plan consequence is present in a
  verified Git checkpoint.
- Remote integration uses effective review-policy evidence and current-head
  applicability; local Plan acceptance remains Git-owned.
- Attempt history compacts only after all recovery and consumer obligations are
  gone, with obsolete traffic rejected from the compacted generation.
- Secretary consumes consequence/attention references rather than acting as a
  second lifecycle engine.
- `next_action` and session deletion decisions are backed by production
  inventory and representative measurements.
- Shared/default Herdr sessions and Git worktrees remain protected by their
  existing owners.
- CI, runtime documentation, and plan/template guidance name durable owners
  without copying mutable GitHub status.

## Risks And Non-Goals

- Do not reopen PR #71’s one-authority architecture.
- Do not add a generic durability database, cleanup daemon, event bus, TTL
  sweeper, global resource registry, or second task ledger.
- Do not delete shared/default Herdr sessions or worktrees from runtime code.
- Do not claim lower operating cost without identical before/after workload
  evidence.
- Do not merge, push, retarget, or clean unrelated workspace artifacts as part
  of plan execution.
