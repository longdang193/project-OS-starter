---
artifact_type: plan
template_id: implementation-plan
contract_version: "1"
status: active
layer: change
name: one-authority-lifecycle-convergence
targets:
  - scripts/project_os_runtime/reconciliation.py
  - scripts/project_os_runtime/acceptance.py
  - scripts/project_os_runtime/attempt.py
  - scripts/project_os_runtime/plan_preparation.py
  - scripts/project_os_runtime/results.py
  - scripts/project_os_runtime/secretary_evidence.py
  - scripts/project_os_runtime/secretary_adapter.py
  - scripts/project_os_runtime/secretary_events.py
  - scripts/herdr_main_launcher.py
  - scripts/herdr_parallel_dispatch.py
  - scripts/dcode_project.py
  - .github/workflows/repo-contracts.yml
  - .github/workflows/runtime-contracts.yml
  - docs/operating_system/runtime/runtime-surfaces.md
  - tests/test_reconciliation.py
  - tests/test_project_os_reconciliation.py
  - tests/test_project_os_runtime.py
  - tests/test_evidence_release.py
  - tests/test_plan_preparation.py
  - tests/test_herdr_main_launcher.py
  - tests/test_dcode_project.py
  - tests/test_secretary_evidence.py
  - tests/test_secretary_adapter.py
  - tests/test_secretary_receipts.py
  - tests/test_secretary_live_runtime.py
  - tests/test_secretary_live_pilot.py
---

# One-Authority Lifecycle Convergence

## Goal

Review verdict is accepted with one scope correction: its architecture is
right, but execution must start from `origin/main` at `b41d3f8`, not current
checkout `HEAD` `a8a1fc5`, which contains unrelated overlay work and untracked
artifacts. Deliver one small convergence PR that makes lifecycle decisions
single-owner and deletes duplicate decision paths.

Target invariant:

> One reconciliation implementation. One acceptance authority. One
> runtime-retirement path. One evidence-disposal path. Everything else is
> canonical truth or disposable evidence.

Do not add a workflow database, reconciliation cache, GitHub mirror, cleanup
daemon, event bus, TTL sweeper, Secretary database, second acceptance ledger,
or global resource registry.

## Implementation Outcomes

### One phase reconciler

`reconcile(ReconciliationInput(...))` becomes the only lifecycle decision
implementation for `dispatch`, `verify`, `accept`, `integrate`, `retire`, and
`prune`. Existing callers translate compatibility inputs at the boundary only;
`_reconcile_snapshot()`, `_reconcile_legacy()`, `EvidenceSnapshot`, and
independent lifecycle eligibility logic disappear after migration.

Phase contracts remain explicit: dispatch is local and GitHub-independent;
verification requires terminal Worker plus published `TaskResult`; acceptance
requires current proof and explicit CoS `PASS`; integration requires current,
identity-bound structured GitHub evidence; retirement requires exact runtime
ownership, settlement, and no continuation; pruning requires canonical
consequence, released consumers, expired retention, and completed retirement.

### One acceptance and release authority

CoS owns semantic acceptance. Plan/Git owns canonical consequence. Controller
supplies ephemeral structured GitHub evidence and never persists copied status
booleans as truth. Only controller-authorized, binding-checked evidence release
can delete TaskResult, settlement receipt, or attempt evidence. Release is
restart-safe, exact-path, per-resource, and idempotent.

### One retirement path and truthful cleanup

The controller coordinates resource-specific runtime owners across two bounded
runtime stages. `dcode-project` performs worker descendant, role-view, and MCP
runtime cleanup before settlement because that proof is required to settle the
attempt. After terminal TaskResult publication, settlement, and no continuation,
Herdr launcher owns agent/pane retirement. Runtime retirement stays separate from
semantic evidence pruning. Direct MCP cleanup reports `removed`,
`already_absent`, `unverified`, or `remaining_path`; age-based stale cleanup
and silent `ignore_errors=True` deletion are removed.

### Reduced duplicate traffic and durable proof

Secretary consumes reconciled decisions and routes only cross-workstream or
human-attention consequences. CI workflows have single responsibilities.
Focused tests prove success, outage, stale evidence, publication failure,
restart recovery, duplicate release, exact retirement ownership, cleanup
failure, and preservation of shared sessions. One bounded live DeepAgents
lifecycle probe proves publication ordering through retirement and release;
raw probe traces remain disposable.

## Execution Approach

- Mode: `inline sequential`
- Coordination: `git-tracked`
- Required skills: `skill-writing-plans`, `skill-executing-plans`, `skill-code-standards`, `skill-test-driven-development`, `skill-backend-verification`, `skill-systematic-debugging`, `skill-finishing-a-development-branch`, `skill-verification-before-completion`
- Isolation: `fresh dedicated worktree from origin/main at b41d3f8`; drafting checkout remains untouched
- Commit policy: `activation checkpoint changes proposed → active before Task 1; implementation commits follow task-local proof; each checkpoint records plan ledger state in the same commit; final status changes only after fresh verification`
- Preauthorized local actions: `edit listed repository files, add focused tests, update listed documentation/workflows, run listed local checks, and run one bounded local lifecycle probe against probe-created resources with proven ownership`
- User-approval actions: `approve and activate plan, create or update PR, push, merge, delete pre-existing or shared runtime resources, delete unrelated workspace artifacts, or dispose raw evidence before durable summary`
- Parallel ownership: `none; all lanes share lifecycle contracts and run sequentially`
- Sequential fallback: `Task 1 → Task 2 → Task 3 → Task 4 → Task 5 → Task 6`

## Coordination State

- Coordination owner: `single lead controller`
- Coordination schema: `2`
- Branch: `codex/one-authority-lifecycle-convergence`
- Base commit: `b41d3f8` (`origin/main`, verified 2026-10-10)
- Expected workspace: `fresh execution worktree; preserve current checkout changes and untracked .playwright-mcp/, db/, temp_evidence.json, and existing untracked plans`
- Next action: `obtain post-fix independent review and user-authorized exact-PR-head checks after committing/pushing current fix`
- Blockers: `post-fix code is uncommitted; remote checks and independent review do not bind current fix; plan remains active until those gates are authorized and pass`

| Task | State | Workspace | Executor | Depends On | Required Proof | Evidence |
| --- | --- | --- | --- | --- | --- | --- |
| Task 1 | `completed` | dedicated execution worktree | `codex` | none | baseline inventory, focused tests, CI defect proof | `origin/main` `b41d3f8`; activation `93e4a10`; baseline `376 passed` |
| Task 2 | `completed` | dedicated execution worktree | `codex` | Task 1 | one reconciler and phase regression matrix | `reconcile(ReconciliationInput(...))`; focused lifecycle suites passed |
| Task 3 | `completed` | dedicated execution worktree | `codex` | Task 2 | structured remote evidence and CoS acceptance proof | exact-head checks policy bound to `github://` or `repo-contract://`; `487 passed` focused suites |
| Task 4 | `completed` | dedicated execution worktree | `codex` | Task 2 | exact retirement path and runtime-owner proof | `retire_lane` plus `retire_settled_lane`; idempotency, mismatch, recovery tests passed |
| Task 5 | `completed` | dedicated execution worktree | `codex` | Tasks 3–4 | restart-safe release and truthful cleanup proof | acceptance release path; attempt-guard authorization survives replacement; stale sweeper and legacy disposal removed |
| Task 6 | `active` | dedicated execution worktree | `codex` | Tasks 1–5 | CI, docs, live lifecycle, final verification | workflow duplicate removed; repo/planning validators passed; post-fix live lifecycle passed; review/remote gate remains |

## Task Breakdown

### Task 1: Freeze migration boundaries and baseline truth

**Purpose:**
- Establish exact callers, tests, workflow duplication, generated owners, base
  SHA, and preserved unrelated workspace state before shared-contract edits.

**Task Function:**
- Repository truth and migration-safety audit.

**Template Profile:**
- Controller-selected: `none (lead controller)`
- Selection basis: `low ambiguity; source and test inventory is authoritative`

**Validator Profile:**
- Controller-selected: `none`
- Selection basis: `baseline inventory is directly reproducible`

**Specification Coverage:**
- Plan/Git own scope and checkpoints; source and tests override stale verdict
  assumptions; no unrelated overlay or untracked artifact enters PR scope.

**Required Skills:**
- `skill-code-standards`

**Files And Symbols:**
- Inspect: `scripts/project_os_runtime/reconciliation.py:_reconcile_legacy`, `_reconcile_snapshot`, `reconcile`
- Inspect: `scripts/project_os_runtime/acceptance.py`, `scripts/project_os_runtime/attempt.py`, `scripts/project_os_runtime/secretary_evidence.py`
- Inspect: `scripts/herdr_main_launcher.py:retire_lane`, `_discard_deepagents_receipt`
- Inspect: `scripts/dcode_project.py:_cleanup_stale_direct_mcp_runtimes`, `_direct_mcp_runtime`
- Inspect: `.github/workflows/repo-contracts.yml`, `.github/workflows/runtime-contracts.yml`
- Verify: `git status --short --branch`, `git diff --name-only b41d3f8`, `git grep` caller inventory

**Dependencies:**
- None; use `origin/main` `b41d3f8` as source baseline.

**Authority:**
- Preauthorized local actions: `read repository files, run inventory and baseline checks, and record preserved unrelated workspace state`
- Stop for: `base SHA, source ownership, generated-file boundary, or required scope differs from this plan`

**Steps:**
- [x] Step 1: After user approval, create dedicated worktree from `origin/main` at `b41d3f8`, copy this Plan, change `status: proposed` to `status: active`, commit activation checkpoint, then begin Task 1.
- [x] Step 2: Inventory all direct and indirect callers of legacy reconciliation, legacy evidence disposal, retirement, and stale MCP cleanup; classify each symbol as `keep`, `translate`, or `delete`.
- [x] Step 3: Identify the existing attempt guard/settlement record that can own release authorization and the minimal retry tombstone; forbid any new release database or store.
- [x] Step 4: Run baseline focused tests and `python scripts/validate_repo_contracts.py`; record failures without unrelated fixes.

**Verification:**
- [x] `git grep -n -E '_reconcile_legacy|_reconcile_snapshot|release_attempt_evidence|_discard_deepagents_receipt|retire_lane|_cleanup_stale_direct_mcp_runtimes'`
- Expected: every active caller is classified as keep, translate, delete, or test-only evidence; deletion table names production callers and compatibility need.
- [x] `python -m pytest -q tests/test_reconciliation.py tests/test_project_os_reconciliation.py tests/test_evidence_release.py tests/test_herdr_main_launcher.py tests/test_dcode_project.py`
- Expected: baseline result recorded; failures attributable to pre-change state.

**Exit Criteria:**
- Base, workspace, callers, tests, CI duplication, and deletion boundaries are recorded in the task evidence.

### Task 2: Converge lifecycle decisions into one phase reconciler

**Purpose:**
- Make phase reconciliation canonical and migrate every current caller without
  retaining a second eligibility engine.

**Task Function:**
- Contract convergence and caller migration.

**Template Profile:**
- Controller-selected: `high`
- Selection basis: `shared API has high blast radius; resolve profile after Task 1 inventory`

**Validator Profile:**
- Controller-selected: `none`
- Selection basis: `lead controller assigns independent validation before activation`

**Specification Coverage:**
- One `ReconciliationInput` boundary; explicit phase semantics; only
  `reconcile(ReconciliationInput(...))` is public; temporary adapters contain
  zero decision logic; dispatch independent of GitHub and existing attempt;
  prune gated by retirement unless resource class is explicitly independent.
  Remove every snapshot-only type after caller migration.

**Required Skills:**
- `skill-code-standards`
- `skill-test-driven-development`
- `skill-backend-verification`

**Files And Symbols:**
- Modify: `scripts/project_os_runtime/reconciliation.py:reconcile`, phase helpers, `RemotePrEvidence`
- Modify: `scripts/project_os_runtime/acceptance.py:evaluate_acceptance`
- Modify: `scripts/project_os_runtime/attempt.py:derive_lifecycle_state`
- Modify: `scripts/project_os_runtime/secretary_evidence.py:reconcile evidence adapter`
- Modify: `scripts/herdr_parallel_dispatch.py:dispatch admission`
- Verify: `tests/test_reconciliation.py`, `tests/test_project_os_reconciliation.py`, `tests/test_project_os_runtime.py`

**Dependencies:**
- Task 1 complete.

**Authority:**
- Preauthorized local actions: `replace legacy lifecycle decisions with one phase reconciler, migrate listed callers, update focused regression tests, and preserve compatibility only as input translation`
- Stop for: `new lifecycle state store, new cache, changed acceptance owner, or unresolved caller outside listed surfaces`

**Steps:**
- [x] Step 1: Make `reconcile(ReconciliationInput(...))` the only canonical public form; temporary compatibility adapters may translate old inputs but contain zero decision logic.
- [x] Step 2: Delete `_reconcile_snapshot`, `_reconcile_legacy`, `EvidenceSnapshot`, and every snapshot-only type (`LocalEvidence`, `RuntimeEvidence`, `Eligibility`, `Contradiction`, `MissingEvidence`, `REMOTE_EVIDENCE_UNAVAILABLE`) unless Task 1 proves a type still belongs to the canonical contract.
- [x] Step 3: Encode and test dispatch, verify, accept, integrate, retire, and prune contracts, including integration eligibility versus merged completion.
- [x] Step 4: Update exports/imports and remove obsolete tests only after replacement coverage passes.

**Verification:**
- [x] `python -m pytest -q tests/test_reconciliation.py tests/test_project_os_reconciliation.py tests/test_project_os_runtime.py tests/test_plan_preparation.py`
- Expected: one `ReconciliationInput` API works; compatibility adapters, if retained, only translate; legacy positional and keyword decision paths are absent; regression matrix phase gates pass.
- [x] `python -m pytest -q tests/test_herdr_parallel_dispatch.py tests/test_secretary_evidence.py`
- Expected: dispatch and Secretary consume phase results without rebuilding lifecycle truth.

**Exit Criteria:**
- One reconciliation implementation and one canonical API remain; no legacy lifecycle type exists solely for the removed snapshot engine; all production callers use it; phase behavior is covered by focused tests.

### Task 3: Enforce structured GitHub evidence and one acceptance authority

**Purpose:**
- Ensure integration decisions use fresh identity-bound remote facts and only CoS
  `PASS` plus canonical Plan/Git transition can authorize semantic completion.

**Task Function:**
- Acceptance authority and remote-evidence hardening.

**Template Profile:**
- Controller-selected: `normal`
- Selection basis: `structured evidence and acceptance are high-risk contract surfaces`

**Validator Profile:**
- Controller-selected: `none`
- Selection basis: `lead controller assigns independent validation before activation`

**Specification Coverage:**
- `RemotePrEvidence` carries repository, PR, base, exact head, required checks,
  review identity/head, mergeability, merged state, availability, and source.
  Required-check policy is sourced from current GitHub branch/ruleset
  requirements when retrievable, otherwise from an explicit repository/task
  contract. The reconciler verifies the required set is contained in observed
  current successful checks, not merely that supplied checks passed. Remove
  compatibility booleans after production callers migrate.

**Required Skills:**
- `skill-backend-verification`
- `skill-code-standards`

**Files And Symbols:**
- Modify: `scripts/project_os_runtime/reconciliation.py:_integrate`, `RemotePrEvidence`
- Modify: `scripts/project_os_runtime/acceptance.py:evaluate_acceptance`, `authorize_evidence_release`
- Modify: `scripts/project_os_runtime/plan_preparation.py:apply_accepted_plan_transitions`
- Modify: `scripts/project_os_runtime/secretary_evidence.py`
- Verify: `tests/test_project_os_reconciliation.py`, `tests/test_reconciliation.py`, `tests/test_plan_preparation.py`, `tests/test_evidence_release.py`
- Verify: `docs/operating_system/runtime/runtime-surfaces.md`

**Dependencies:**
- Task 2 complete.

**Authority:**
- Preauthorized local actions: `derive integration from ephemeral structured remote evidence, enforce exact candidate and review freshness, and route semantic acceptance through CoS and canonical Plan transition`
- Stop for: `persisted GitHub mirror, copied status becoming authoritative, Worker self-acceptance, or merge execution without native expected-head protection`

**Steps:**
- [x] Step 1: Bind required-check and review policy from GitHub branch/ruleset requirements when available, otherwise from explicit repository/task contract; compare policy against exact current observations.
- [x] Step 2: Require remote availability, repository identity, PR number, base identity, exact candidate head, required checks, valid review for that head, and current mergeability.
- [x] Step 3: Keep `integration_eligible` distinct from merged/completed state; re-read mutable GitHub facts before consequential merge action.
- [x] Step 4: Remove `checks_passed`, `review_valid`, and `mergeable` compatibility fields once production callers migrate; do not preserve precedence rules indefinitely.
- [x] Step 5: Make Secretary consume phase result, task reference, blocking references, and consequence instead of reconstructing acceptance or GitHub state; update runtime ownership documentation.

**Verification:**
- [x] `python -m pytest -q tests/test_project_os_reconciliation.py tests/test_reconciliation.py tests/test_plan_preparation.py tests/test_evidence_release.py`
- Expected: unavailable remote, stale review, missing required check from policy, changed head, and unmerged-but-eligible cases fail or classify correctly; supplied subset of passing checks cannot bypass missing required checks.
- [x] `python -m pytest -q tests/test_secretary_evidence.py tests/test_secretary_adapter.py tests/test_secretary_receipts.py`
- Expected: Secretary emits attention only from canonical decision consequences and cannot accept or release evidence.

**Exit Criteria:**
- CoS is sole semantic acceptance authority; structured GitHub evidence is ephemeral and exact-head-bound; Plan/Git records consequence.

### Task 4: Wire one runtime-retirement path

**Purpose:**
- Converge runtime finalization into one lifecycle contract with producer cleanup
  required for settlement and post-settlement Herdr agent/pane retirement,
  without waiting for semantic acceptance or deleting evidence.

**Task Function:**
- Runtime finalization and ownership proof.

**Template Profile:**
- Controller-selected: `normal`
- Selection basis: `process/pane runtime cleanup has destructive ownership risk`

**Validator Profile:**
- Controller-selected: `none`
- Selection basis: `lead controller assigns independent validation before activation`

**Specification Coverage:**
- `dcode-project` cleanup of worker descendants, role views, and MCP runtime
  occurs before settlement and supplies positive cleanup proof. Valid terminal
  TaskResult publication, including failed outcome, plus settlement and no
  continuation precede Herdr agent/pane retirement. Exact attempt binding owns
  retirement; resource-specific owners retire their own resources; shared/
  general Herdr sessions remain preserved unless exclusive, empty, task-created,
  and consumer-free. Worktree disposal belongs to
  `skill-finishing-a-development-branch`, after review/merge/final disposition.

**Required Skills:**
- `skill-backend-verification`
- `skill-systematic-debugging`

**Files And Symbols:**
- Modify: `scripts/herdr_main_launcher.py:retire_lane`, terminal/no-continuation finalization, agent/pane retirement result publication
- Modify: `scripts/project_os_runtime/attempt.py:derive_lifecycle_state`
- Modify: `scripts/dcode_project.py` worker descendants, role views, and MCP runtime ownership only
- Inspect: `skill-finishing-a-development-branch` worktree disposition boundary; do not move worktree cleanup into this task
- Verify: `tests/test_herdr_main_launcher.py`, `tests/test_herdr_attempt_contract.py`, `tests/test_dcode_project.py`, `tests/test_project_os_runtime.py`

**Dependencies:**
- Task 2 complete; Task 3 is a sibling lane and is not a retirement dependency.

**Authority:**
- Preauthorized local actions: `call existing ownership-safe resource owners for probe-created resources with proven ownership, preserve pre-settlement cleanup proof, call Herdr retirement after settlement/no-continuation, publish retirement proof, and add exact-resource/race/idempotency tests`
- Stop for: `shared or pre-existing session/pane/process cleanup, worktree deletion, foreign temp directories, uncertain ownership, age-based cleanup, or runtime retirement coupled to semantic evidence deletion`

**Steps:**
- [x] Step 1: Preserve `dcode-project` pre-settlement cleanup and settlement proof; treat `status=failed` as terminal publication when recovery evidence is durable.
- [x] Step 2: After TaskResult and settlement receipt publication, call Herdr agent/pane retirement only when no continuation is required; use `dcode-project` for its pre-settlement resources and controller for sequencing; never remove worktrees here.
- [x] Step 3: Feed retirement proof into `retire` and `prune` phase facts; keep TaskResult and receipt retained until evidence release.
- [x] Step 4: Test repeated retirement, wrong pane/process identity, missing ownership, restart recovery, and shared-session preservation.

**Verification:**
- [x] `python -m pytest -q tests/test_herdr_main_launcher.py tests/test_herdr_attempt_contract.py tests/test_dcode_project.py tests/test_project_os_runtime.py`
- Expected: dcode cleanup proves settlement; exact Herdr agent/pane resources retire after settlement; failed terminal publication can release runtime capacity when recovery evidence is durable; uncertain ownership fails closed; shared session stays; repeated cleanup is idempotent; worktree and evidence remain available.
- [x] Deterministic lifecycle regression records TaskResult → receipt → retirement.

**Exit Criteria:**
- Production terminal flow has one runtime-finalization contract with pre-settlement producer cleanup and post-settlement resource-specific retirement, publishing durable retirement proof before any prune decision; worktree disposition remains a later finishing workflow.

### Task 5: Converge evidence disposal and truthful temporary cleanup

**Purpose:**
- Keep one controller-authorized release contract, make retries restart-safe, and
  expose cleanup failures without turning temporary cleanup into semantic success.

**Task Function:**
- Evidence-release convergence and failure truthfulness.

**Template Profile:**
- Controller-selected: `normal`
- Selection basis: `deletion and retry semantics require exact binding review`

**Validator Profile:**
- Controller-selected: `none`
- Selection basis: `lead controller assigns independent validation before activation`

**Specification Coverage:**
- Keep `authorize_evidence_release()` and `release_authorized_evidence()` as
  production path. Bind plan/task, assignment, attempt, candidate SHA,
  acceptance checkpoint, retirement proof, consumer releases, retention, and
  exact evidence references. Reuse the existing attempt guard/settlement record
  as release-record owner; do not create a separate release database. Each
  producing owner removes its own resource; controller coordinates one release
  decision and returns aggregate per-resource results.

**Required Skills:**
- `skill-backend-verification`
- `skill-systematic-debugging`

**Files And Symbols:**
- Modify: `scripts/project_os_runtime/acceptance.py:authorize_evidence_release`, `release_authorized_evidence`
- Modify: `scripts/dcode_project.py:_attempt_guard_path`, `_read_attempt_guard`, `_write_attempt_guard`, `_claim_attempt`, `_settle_attempt` for release authorization reference and minimal tombstone ownership
- Inspect: `scripts/dcode_project.py:_claim_attempt_unlocked` settled-attempt replacement semantics and `tests/test_dcode_project.py:test_attempt_guard_settlement_preserves_binding_and_allows_replacement`
- Delete or retire: `scripts/project_os_runtime/results.py:release_attempt_evidence`, `scripts/herdr_main_launcher.py:_discard_deepagents_receipt`
- Modify: `scripts/dcode_project.py:_direct_mcp_runtime`, delete `_cleanup_stale_direct_mcp_runtimes`
- Verify: `tests/test_evidence_release.py`, `tests/test_deepagents_result_contract.py`, `tests/test_herdr_main_launcher.py`, `tests/test_dcode_project.py`

**Dependencies:**
- Tasks 3 and 4 complete.

**Authority:**
- Preauthorized local actions: `implement one controller release decision with resource-specific producer cleanup, reuse the attempt/settlement record for restart-safe release state, remove dead disposal/sweeper paths after caller proof, and update focused cleanup/replay tests`
- Stop for: `missing validated release decision treated as already absent, silent deletion failure, destructive cleanup outside exact ownership, or raw evidence deletion before durable summary`

**Steps:**
- [x] Step 1: Bind release authorization to the existing dcode-project attempt/settlement guard with `assignment_id`, `attempt_id`, `candidate_sha`, `acceptance_checkpoint_sha`, `release_authorized`, and released-resource results; preserve pending release state when settled-attempt replacement occurs and across restart; do not create a new store.
- [x] Step 2: Return per-resource `removed`, `already_absent`, `unverified`, or unresolved results; each producer removes only resources it owns; retain minimal tombstone state only while recovery is possible.
- [x] Step 3: Make repeated release with the same validated decision succeed idempotently; missing target without prior validated decision remains unresolved.
- [x] Step 4: Replace direct MCP `ignore_errors=True` recursive deletion with exact-path structured outcome and settlement evidence.
- [x] Step 5: Remove legacy receipt disposal and age-based MCP sweeper only after `git grep` proves no production caller remains.

**Verification:**
- [x] `python -m pytest -q tests/test_evidence_release.py tests/test_deepagents_result_contract.py tests/test_herdr_main_launcher.py tests/test_dcode_project.py`
- Expected: release requires current CoS/Plan/retirement proof, retries are idempotent, partial failure is visible, and cleanup status is truthful.
- [x] Replacement-plus-restart regression covering `_claim_attempt_unlocked`, `_settle_attempt`, pending release authorization, and delayed resource disposal.
- Expected: settled-attempt replacement cannot erase pending release state before all owned resources reach `removed` or validated `already_absent`.
- [x] `git grep -n -E 'release_attempt_evidence|_discard_deepagents_receipt|_cleanup_stale_direct_mcp_runtimes' -- scripts tests`
- Expected: no production caller; remaining historical fixture references are explicitly classified or removed.

**Exit Criteria:**
- One evidence-disposal path remains; temporary cleanup failure is visible and separately actionable; no age-based or silent cleanup remains.

### Task 6: Align CI/docs and run final lifecycle proof

**Purpose:**
- Make CI responsibilities non-duplicative, document canonical ownership, and
  produce local-ready evidence plus a clearly separated user-authorized
  exact-PR-head verification stage.

**Task Function:**
- Final integration, live proof, and release-readiness verification.

**Template Profile:**
- Controller-selected: `normal`
- Selection basis: `final proof spans source, CI, runtime, and disposable evidence`

**Validator Profile:**
- Controller-selected: `none`
- Selection basis: `lead controller assigns independent validation before activation`

**Specification Coverage:**
- Repository Contracts owns schema/planning/static invariants; Runtime Contracts
  owns runtime behavior and OS matrix; Benchmark owns performance only. Raw
  traces are disposable after durable summary.

**Required Skills:**
- `skill-backend-verification`
- `skill-verification-before-completion`

**Files And Symbols:**
- Modify: `.github/workflows/repo-contracts.yml` single `concurrency` block and focused validator tests
- Modify: `.github/workflows/runtime-contracts.yml` remove unjustified duplicate behavior tests only
- Modify: `docs/operating_system/runtime/runtime-surfaces.md`
- Verify: `tests/test_validate_repo_contracts.py`, workflow YAML, all listed focused suites

**Dependencies:**
- Tasks 1–5 complete.

**Authority:**
- Preauthorized local actions: `update listed workflows/docs, run full repository validators and focused suites, perform one bounded happy-path lifecycle probe only against probe-created resources with proven ownership, and summarize then remove probe-only raw evidence`
- Stop for: `CI policy or required-check ownership changes outside repository files, external GitHub writes, unresolved live runtime ownership, or inability to prove publication ordering`

**Steps:**
- [x] Step 1: Remove duplicate top-level `concurrency` from Repository Contracts and keep one cancellation policy; narrow overlapping tests by workflow responsibility, including duplicate `tests/test_secretary_adapter.py` entry.
- [x] Step 2: Update runtime ownership docs and record no-new-infrastructure exclusions.
- [x] Step 3: Run one managed happy-path probe: worker terminal → dcode cleanup/settlement proof → TaskResult → receipt → no continuation → Herdr retirement → CoS acceptance → canonical consequence → exact evidence release. Post-fix probe `b84fe5801ceb44c1a37044e21e60da6f` exited `0` with `TaskResult=reported_completed`, cleanup `removed`, retirement `removed` with `process_retirement_proven=true`, CoS decision `PASS`, plan transition `authorized=true`, and evidence release `payload_released=true`; pane/session stayed preserved.
- [x] Step 4: Run final focused tests, repository contract validation, plan validation, and local workflow commands; record remote exact-PR-head checks as a separate user-authorized stage.

**Verification:**
- [x] `python scripts/validate_repo_contracts.py`
- Expected: repository contracts, generated surfaces, plan metadata, and workflow invariants pass.
- [x] `python scripts/validate_planning_lifecycle.py --plan docs/superpowers/plans/2026-10-10-one-authority-lifecycle-convergence-plan.md`
- Expected: proposed draft validates now; status is `active` during Tasks 1–6; status becomes `completed` only after final fresh verification.
- [x] `python -m pytest -q tests/test_reconciliation.py tests/test_project_os_reconciliation.py tests/test_project_os_runtime.py tests/test_evidence_release.py tests/test_plan_preparation.py tests/test_herdr_main_launcher.py tests/test_dcode_project.py tests/test_secretary_evidence.py tests/test_secretary_adapter.py tests/test_secretary_receipts.py tests/test_secretary_live_runtime.py tests/test_secretary_live_pilot.py`
- Expected: all required regression cases pass on fresh execution worktree.
- [x] Local-ready summary proves TaskResult before receipt, receipt validation, no continuation, runtime retirement, CoS acceptance, canonical Plan consequence, evidence release, and no probe-owned resources remain. Remote completion separately requires user-authorized push/PR plus exact-head Repository Contracts, Runtime Contracts, Benchmark, and independent review evidence.

**Exit Criteria:**
- CI, docs, source, tests, and generated surfaces agree; local verification is fresh; raw probe artifacts are removed after durable summary; no required scope deviation remains. Remote checks remain pending until user authorizes push/PR.

## Verification

- `python scripts/validate_repo_contracts.py`
- `python scripts/validate_planning_lifecycle.py --plan docs/superpowers/plans/2026-10-10-one-authority-lifecycle-convergence-plan.md`
- `python -m pytest -q tests/test_reconciliation.py tests/test_project_os_reconciliation.py tests/test_project_os_runtime.py tests/test_evidence_release.py tests/test_plan_preparation.py tests/test_herdr_main_launcher.py tests/test_dcode_project.py tests/test_secretary_evidence.py tests/test_secretary_adapter.py tests/test_secretary_receipts.py tests/test_secretary_live_runtime.py tests/test_secretary_live_pilot.py`
- `git grep -n -E '_reconcile_legacy|_reconcile_snapshot|release_attempt_evidence|_discard_deepagents_receipt|_cleanup_stale_direct_mcp_runtimes' -- scripts tests`
- Local-ready proof covers workflow commands; after user-authorized push/PR, GitHub must expose Repository Contracts, Runtime Contracts, and Benchmark on the exact PR head, with independent review before `active → completed`.
- One bounded live lifecycle summary with raw evidence released after durable capture.

## Review Remediation

- Review turn 1: `FAIL` at PR head `86aadda71770f5f6dc76780a9c4d740b13ef6b6a`.
- Fixed exact evidence scope: release deletes only bound `evidence_ref`; replay requires durable complete resource proof.
- Fixed release persistence path: accepted plan transition passes `release_record`; controller may persist release resources through existing attempt guard.
- Fixed retirement wiring: terminal settled DeepAgents assignments call `retire_settled_lane`; unresolved retirement keeps capacity occupied.
- Fixed phase recommendation: incomplete eligible phases return `reconcile <phase>`, never downstream action.
- Required rerun: focused lifecycle tests, full suite, repository/planning validators, exact-head CI, independent review.
- Review turn 2: `PASS` at PR head `7a476a30c8da6f60f66d204f0f164058ad2addbe`.
- Review turn 3: `FAIL` at PR head `a6636f9b1c7fdc5336fdf39565ef8ec94d978cc8`; code findings remain cleared, but completion proof is insufficient because live lifecycle capability is unavailable and review evidence must bind current head.
- Current-head review turn 4: `FAIL` at `5831959deda28001b8e5367fa133d8c057ef82fb`; found terminal retirement false-failure when worker already exited and evidence release bypassing canonical retirement proof. Fixed in `scripts/herdr_main_launcher.py`, `scripts/project_os_runtime/acceptance.py`, and `scripts/project_os_runtime/plan_preparation.py`; focused regression proof passes. Review remains stale for post-fix changes.
- Post-fix local proof: full suite `1107 passed, 1 skipped`; managed DeepAgents attempt `b84fe5801ceb44c1a37044e21e60da6f` plus local acceptance boundary probe produced `PASS`, authorized canonical transition, and exact evidence release. Probe-owned raw evidence was removed after capture; no shared session was removed.
- Current proof: local suite `1105 passed, 1 skipped`; exact-head Repository Contracts, Runtime Contracts, and Benchmark passed; deterministic lifecycle coverage passed. Live lifecycle proof remains required by completion criterion 8.
- Live probe update: managed `dcode-project` capability resolved on 2026-10-10. Probe attempt `5a62099b7eeb43daaf8d0a99e15f65e4` produced bound `TaskResult` with `status=completed`, confirmed settlement cleanup, and no continuation; `retire_settled_lane` returned `retirement_unresolved` with `process ownership identity is unavailable` because pane `w1:p1` retained only pre-existing `powershell.exe`. Do not mark plan complete from this partial proof.

## Completion Criteria

The plan is ready for completion verification when:

1. one phase reconciler owns all lifecycle eligibility and callers no longer rebuild it
2. CoS is the only semantic acceptance authority and Plan/Git owns canonical consequence
3. structured GitHub evidence is fresh, exact-head-bound, ephemeral, and unavailable remote blocks integration only
4. one runtime-retirement contract coordinates resource-specific owners for exact task-owned resources after terminal settlement/no-continuation; shared sessions remain safe and worktree disposal stays with `skill-finishing-development-branch`
5. one controller-authorized evidence-release decision is restart-safe, exact-path, per-resource, and idempotent; existing attempt/settlement record owns retry state
6. direct MCP cleanup is truthful and age-based sweeping is gone
7. Secretary is derived attention only and CI workflows have single responsibilities
8. focused regression tests, repository validation, plan validation, and one live happy-path lifecycle proof are fresh and passing; failure/restart cases use deterministic tests
9. raw traces and disposable evidence are summarized durably, then removed; no unrelated checkout artifact enters PR
10. no new database, cache, daemon, event bus, TTL sweeper, acceptance ledger, or global registry was introduced
11. local readiness is complete before remote verification; `active → completed` waits for user-authorized exact-PR-head checks and independent review

The plan may be marked `completed` only after
`skill-verification-before-completion` returns `verified` against fresh
repository evidence. PR creation, push, merge, and external cleanup remain
outside this proposed plan's authority.
