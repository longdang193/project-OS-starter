---
layer: change
artifact_type: plan
contract_version: "1"
status: completed
template_id: implementation-plan
name: launch-preparation-convergence
targets:
  - docs/superpowers/plans/2026-10-08-launch-preparation-convergence-plan.md
  - scripts/herdr_main_launcher.py
  - scripts/herdr_parallel_dispatch.py
  - scripts/project_os_runtime/lane.py
  - tests/test_herdr_main_launcher.py
  - tests/test_herdr_parallel_dispatch.py
  - tests/test_plan_preparation.py
  - tests/test_project_os_runtime.py
  - tests/test_deepagents_result_contract.py
  - tests/test_skill_chief_of_staff.py
  - docs/architecture.md
  - docs/operating_system/runtime/runtime-surfaces.md
---

# Launch Preparation Convergence Plan

## Verdict Review

Review verdict accepted. Original plan overstated production gaps and risked
adding a second normalized contract beside `PreparedLane`.

Revised direction:

- `PreparedLane` remains canonical normalized static launch contract.
- `LaunchPreflight` is ephemeral runtime evidence, not workflow truth.
- `prepare_plan_lanes()` remains plan-only; runtime discovery stays in launcher.
- Assignment identity stays stable across retries; attempt identity is fresh per
  real launch.
- TaskResult work starts with a current-production probe. Patch only verified
  gaps; PR #55 behavior is not reopened without evidence.
- Deterministic acceptance checks remain evidence inputs. CoS alone emits
  `PASS | FAIL | BLOCKED`.
- No new `acceptance_evidence.py` production module unless a real consumer is
  found during audit.
- Baseline measurement precedes runtime changes and uses the canonical
  plan-bound path, not manual probe commands.
- Target provisioning, lifecycle manifests, evidence DB, Secretary transport,
  and new budget/grant planners remain deferred.

The execution base is `origin/main` at
`ec92965bfd76cc5deec50a782855fcb4ed292a31`, which contains PR #56 semantic
acceptance correction and the completed organizational probe.

## Goal

Prove and converge the existing `PreparedLane → herdr_parallel_dispatch →
herdr_main_launcher` boundary. Reduce only production-path duplication and
late deterministic failures while preserving current ownership, result, and
acceptance contracts.

## Implementation Outcomes

### Canonical-path baseline

The approved plan-bound path is exercised from `prepare_plan_lanes()` through
`PreparedLane`, dispatcher command construction, launcher preflight, and
delivery. Each observed friction is classified as `canonical`, `manual`, or
`both`. Only canonical-path findings justify code changes.

### Ephemeral launch preflight

Launcher readiness checks aggregate independent root blockers with `PASS`,
`BLOCKED`, and `NOT_EVALUATED` states. Static `PreparedLane` fields are reused;
mutable facts are refreshed immediately before delivery. Dry-run never creates
or reuses a durable attempt.

### Verified result/evidence boundary

Current TaskResult publication and PR #56 acceptance behavior are regression
covered. Only concrete remaining gaps receive minimal patches. Invalid artifact
conditions and inspection mutation remain evidence failures, never alternate CoS
verdict authorities.

### Baseline/candidate evidence

The same representative canonical workload runs against baseline `ec92965` and
candidate head. Existing launcher performance evidence is reused. Metrics
separate production-path friction from manual probe friction.

## Execution Approach

- Mode: `inline sequential`
- Coordination: `git-tracked`
- Required skills: `skill-executing-plans`, `skill-backend-verification`, `skill-verification-before-completion`
- Isolation: `current workspace`
- Commit policy: `no commits during execution`
- Preauthorized local actions: edit plan-listed files after audit narrows scope, run focused tests and repository validation, capture local baseline evidence, and update task ledger
- User-approval actions: push, merge, publication, destructive recovery, discard, cleanup of preserved untracked artifacts, and external service writes
- Parallel ownership: none; audit, launcher, result, and acceptance evidence share contract boundaries
- Sequential fallback: baseline audit, preflight convergence, result/evidence regression, then measurement/docs/final verification

## Coordination State

- Coordination owner: `single lead controller`
- Coordination schema: `2`
- Branch: `codex/launch-preparation-convergence`
- Base commit: `ec92965bfd76cc5deec50a782855fcb4ed292a31`
- Expected workspace: `preserve existing untracked .playwright-mcp/, db/, and temp_evidence.json; plan is task-owned`
- Next action: `await authorized branch disposition; no commit, push, merge, or cleanup authorized`
- Blockers: `none`

| Task | State | Workspace | Executor | Depends On | Required Proof | Evidence |
| --- | --- | --- | --- | --- | --- | --- |
| Task 1 | `completed` | current | `codex` | none | canonical-path audit and baseline evidence | 370 baseline tests; canonical gap identified |
| Task 2 | `completed` | current | `codex` | Task 1 | preflight convergence tests | 75 dispatcher tests pass |
| Task 3 | `completed` | current | `codex` | Task 1 | result/acceptance/read-boundary regressions | 110 result/CoS/dispatcher tests pass |
| Task 4 | `completed` | current | `codex` | Tasks 2–3 | candidate measurement, docs, and final proof | baseline/candidate grant proof and canonical worker-owned TaskResult proof complete |

## Task Breakdown

### Task 1: Audit canonical launch path and freeze baseline

**Purpose:**
- Establish current behavior before changing runtime code and separate real
  production friction from manual probe friction.

**Task Function:**
- Source-first path audit, contract probe, and baseline measurement.

**Template Profile:**
- Controller-selected: `none (lead controller)`
- Selection basis: current-source alignment and direct repository evidence.

**Validator Profile (optional):**
- Controller-selected: `none`
- Selection basis: focused existing tests and recorded command output.

**Specification Coverage:**
- Verdict required revisions 1, 2, 6, and 9.
- Verify `prepare_plan_lanes() → PreparedLane → dispatcher → _launcher_command() → herdr_main_launcher`.
- Record which values are already derived and which are reconstructed later.
- Verify PR #55 TaskResult bindings and PR #56 acceptance guard before patching.

**Required Skills:**
- `skill-backend-verification`

**Files And Symbols:**
- Inspect: `scripts/project_os_runtime/plan_preparation.py:prepare_plan_lanes`
- Inspect: `scripts/project_os_runtime/lane.py:PreparedLane`, `prepare_lane`
- Inspect: `scripts/herdr_parallel_dispatch.py:_launcher_command`, `run_parallel`
- Inspect: `scripts/herdr_main_launcher.py:resolve_launch`, `_build_assignment_result`, `_classify_deepagents_outcome`
- Inspect: `scripts/dcode_project.py` only for current TaskResult binding evidence
- Verify: existing launcher, dispatch, plan, result, and CoS tests
- Record: task-local audit note in this plan's Evidence cell or a disposable
  local evidence file; do not create workflow truth outside plan/Git

**Dependencies:**
- Dedicated branch and base are set.
- Existing untracked files remain untouched.

**Authority:**
- Preauthorized local actions: read source/tests, run canonical-path dry-run and focused tests, capture baseline metrics, and update this plan ledger
- Stop for: missing external runtime capability, destructive cleanup, branch/base drift, or design gap requiring new authority

**Steps:**
- [x] Step 1: Trace one approved plan-bound dispatch from plan parsing through
  `PreparedLane`, command construction, launcher preflight, and result parsing.
- [x] Step 2: Run existing canonical-path tests and a bounded dry-run. Classify
  each suspected issue as `canonical`, `manual`, or `both`.
- [x] Step 3: Verify current TaskResult binding/publication and CoS semantic
  acceptance behavior. Record concrete gaps only.
- [x] Step 4: Capture baseline on `ec92965` for total preparation time, launcher
  phase evidence, pre-worker subprocesses, deterministic failures after Worker
  start, time to first useful Worker action when available, human corrections,
  malformed results, false acceptance, and Worker duration.
- [x] Step 5: Narrow plan targets and Task 2/3 write surface to audited gaps.

**Verification:**
- [x] `py -B -m pytest tests/test_plan_preparation.py tests/test_project_os_runtime.py tests/test_herdr_attempt_contract.py tests/test_deepagents_result_contract.py tests/test_herdr_parallel_dispatch.py tests/test_herdr_main_launcher.py tests/test_skill_chief_of_staff.py -q`
- Expected: baseline suite passes on the dedicated branch before implementation.
- [x] `py -B scripts/herdr_parallel_dispatch.py --help` and bounded dry-run
  using an existing fixture or approved plan input.
- Expected: command path and evidence shape are observable without Worker
  mutation; external runtime absence is recorded, not hidden.

**Exit Criteria:**
- Canonical path and current identities are documented from source evidence.
- Baseline metrics exist or each unavailable metric has a concrete reason.
- Task 2 and Task 3 targets exclude unverified files.

**Evidence:**
- `prepare_plan_lanes()` creates `PreparedLane` with assignment ID, task hash,
  normalized grant, grant digest, capabilities, worktree, target selector,
  remaining authority, plan provenance, and binding digest.
- `_launcher_command()` consumes those values on canonical prepared lanes;
  fallback derivation only affects unbound/manual descriptors.
- PR #55 TaskResult binding and PR #56 CoS acceptance behavior are present and
  covered by existing tests.
- Baseline focused suite: `370 passed in 2.74s`. Real Herdr/Worker latency and
  time-to-first-action unavailable in this environment; no external runtime
  probe was claimed.

### Task 2: Converge ephemeral launcher preflight

**Purpose:**
- Remove only verified duplicate preparation while keeping `PreparedLane` as
  normalized SSOT and mutable checks fresh at launch.

**Task Function:**
- Launcher readiness projection and blocker dependency semantics.

**Template Profile:**
- Controller-selected: `none (lead controller)`
- Selection basis: shared launcher behavior and contract risk require direct
  integration.

**Validator Profile (optional):**
- Controller-selected: `none`
- Selection basis: launcher/dispatcher regression tests directly exercise the
  changed boundary.

**Specification Coverage:**
- Verdict required revisions 3–6.
- Add ephemeral `LaunchPreflight` only if audit proves a missing projection;
  it references `PreparedLane` and does not copy stable contract authority.
- Keep runtime discovery out of `plan_preparation.py`.
- Independent root blockers report `PASS`, `BLOCKED`, or `NOT_EVALUATED`; do
  not emit cascade errors after prerequisite failure.
- Stable `assignment_id`; fresh `attempt_id` per real launch.
- Attempt-scoped result path is finalized with real attempt, not dry-run.
- Refresh HEAD, worktree, target ownership, pane availability, remaining time,
  externally mutable allowance, dependency readiness, and prerequisite identity
  immediately before delivery.

**Required Skills:**
- `skill-backend-verification`

**Files And Symbols:**
- Inspect: `scripts/herdr_main_launcher.py:resolve_launch`, `_git_identity`, `_resolve_target_selector`
- Inspect: `scripts/herdr_parallel_dispatch.py:_launcher_command`, `run_parallel`
- Modify: only audited launcher/dispatcher symbols; `scripts/project_os_runtime/lane.py` only if a real projection boundary needs a type
- Verify: `tests/test_herdr_main_launcher.py`, `tests/test_herdr_parallel_dispatch.py`

**Dependencies:**
- Task 1 audit confirms production-path duplication or late deterministic
  failure.
- `PreparedLane` contract and `resolve_attempt_budget()` remain unchanged
  unless audit proves a compatibility-preserving extension necessary.

**Authority:**
- Preauthorized local actions: edit audited launcher/dispatcher files and focused tests; run dry-run and preflight checks
- Stop for: new normalized contract, runtime discovery in `plan_preparation.py`, target provisioning, attempt reuse, or broad CLI redesign

**Steps:**
- [x] Step 1: Define check dependency graph and stable blocker codes from audit
  findings. Mark dependent checks `NOT_EVALUATED`.
- [x] Step 2: Reuse `PreparedLane` stable fields and add only an ephemeral
  readiness projection if required.
- [x] Step 3: Keep preparation side-effect-free; refresh mutable facts at the
  launch boundary and generate fresh attempt identity there.
- [x] Step 4: Preserve existing evidence sections, redaction, dry-run behavior,
  and existing-target-only `auto` semantics.
- [x] Step 5: Add regression cases for audited failures plus valid preparation.

**Verification:**
- [x] `py -B -m pytest tests/test_herdr_main_launcher.py tests/test_herdr_parallel_dispatch.py -q`
- Expected: root blockers are reported without misleading cascades; valid
  prepared lanes reach existing launch path; dry-run cannot authorize later
  launch without fresh checks.

**Exit Criteria:**
- No duplicate normalized launch SSOT exists.
- Static and mutable facts remain separate.
- Assignment stability and fresh attempt identity are tested.

**Evidence:**
- `scripts/herdr_parallel_dispatch.py` now exposes ephemeral `LaunchPreflight`
  and `LaunchCheck` projections only; `PreparedLane` remains unchanged as
  normalized SSOT.
- Canonical bound lanes report independent root blockers; dependent checks are
  `NOT_EVALUATED` after missing worktree prerequisite.
- Unbound/manual lanes retain compatibility behavior and do not claim plan-bound
  freshness evidence.
- Dispatcher suite: `75 passed in 0.93s`.

### Task 3: Close verified result, acceptance, and read-boundary gaps

**Purpose:**
- Regression-prove current result and acceptance contracts, patch only concrete
  remaining gaps, and add mutation detection without creating a verdict owner.

**Task Function:**
- Verify-first backend contract hardening and evidence fixture design.

**Template Profile:**
- Controller-selected: `none (lead controller)`
- Selection basis: PR #55/#56 behavior is recent and must be preserved unless
  direct evidence proves a defect.

**Validator Profile (optional):**
- Controller-selected: `none`
- Selection basis: direct result/launcher/skill regression tests.

**Specification Coverage:**
- Verdict required revisions 7 and 8.
- Verify current `dcode-project` result path and bindings before editing it.
- Do not add `scripts/acceptance_evidence.py` without a real production consumer.
- Deterministic checks emit evidence state only; CoS emits `PASS | FAIL | BLOCKED`.
- Snapshot/hash fixture detects inspection mutation and does not claim prevention.

**Required Skills:**
- `skill-backend-verification`

**Files And Symbols:**
- Inspect: `scripts/project_os_runtime/results.py:publish_task_result`, `validate_task_result`, `parse_task_result`
- Inspect: `scripts/dcode_project.py` attempt guard, result setup, cleanup,
  and fallback publication
- Inspect: `scripts/herdr_main_launcher.py:_read_deepagents_task_result`, `_classify_deepagents_outcome`
- Inspect: `.agents/skills/skill-chief-of-staff/SKILL.md` semantic acceptance
  and inspection boundary
- Modify: only files implicated by Task 1 audit; likely relevant tests and
  possibly `scripts/dcode_project.py` if a concrete gap remains
- Verify: `tests/test_deepagents_result_contract.py`, `tests/test_herdr_main_launcher.py`, `tests/test_skill_chief_of_staff.py`

**Dependencies:**
- Task 1 current-production probe.
- Task 2 only if launcher integration changes result evidence.

**Authority:**
- Preauthorized local actions: add regression fixtures and minimal audited contract fixes; run direct temporary-directory probes
- Stop for: second acceptance authority, generalized evidence subsystem, schema rewrite, or runtime-generated semantic verdict

**Steps:**
- [x] Step 1: Prove valid Worker-owned TaskResult, identity mismatch, missing
  result, and cleanup/settlement behavior on current production path.
- [x] Step 2: Patch only concrete publication/binding gap; otherwise add tests
  only and leave PR #55 code unchanged.
- [x] Step 3: Add bounded deterministic evidence fixture where valid runtime
  completion plus invalid artifact condition is insufficient for CoS acceptance.
- [x] Step 4: Add isolated before/after hash fixture proving inspection
  mutation invalidates evidence; document detection versus prevention.

**Verification:**
- [x] `py -B -m pytest tests/test_deepagents_result_contract.py tests/test_herdr_main_launcher.py tests/test_skill_chief_of_staff.py -q`
- Expected: invalid/missing TaskResult stays unknown; valid runtime evidence
  cannot bypass semantic acceptance; mutation is detected.
- [x] Direct temporary-directory probe covers publication, parse, settlement,
  cleanup, and evidence classification.
- Expected: no new acceptance verdict source or workflow ledger.

**Exit Criteria:**
- Current result contract is either unchanged with regression proof or minimally
  corrected from an audited concrete gap.
- Acceptance remains CoS-owned.
- Read-boundary evidence is accurate and bounded.

**Evidence:**
- No verified PR #55 result-publication gap; `dcode_project.py` and result
  schema were not reopened.
- Existing result/launcher/CoS tests plus local mutation-detection fixture pass:
  `110 passed in 1.09s`.
- No `acceptance_evidence.py` production module added.

### Task 4: Measure, document, and verify

**Purpose:**
- Compare candidate against baseline, reconcile maintained docs, and close plan
  only from fresh evidence.

**Task Function:**
- Canonical-path measurement, documentation reconciliation, and final proof.

**Template Profile:**
- Controller-selected: `none (lead controller)`
- Selection basis: final integration and acceptance require one ledger owner.

**Validator Profile (optional):**
- Controller-selected: `none`
- Selection basis: verification skill owns fresh final proof.

**Specification Coverage:**
- Verdict required revisions 9 and 10.
- Use baseline `ec92965` and candidate head with same canonical workload.
- Reuse launcher performance evidence; add no telemetry service or benchmark DB.
- Distinguish `canonical`, `manual`, and `both` friction in results.
- Narrow docs and targets to actual changed surfaces.

**Required Skills:**
- `skill-verification-before-completion`

**Files And Symbols:**
- Inspect/modify: `docs/architecture.md`, `docs/operating_system/runtime/runtime-surfaces.md`
- Verify: changed source/tests, plan ledger, Git state, and repository validators

**Dependencies:**
- Tasks 1–3 complete.
- All preserved untracked artifacts remain untouched.

**Authority:**
- Preauthorized local actions: run baseline/candidate measurements, update listed docs and plan ledger, run focused and repository validation
- Stop for: failed required proof, scope expansion, branch/base drift, or unrelated cleanup

**Steps:**
- [x] Step 1: Run same representative workload against baseline and candidate;
  capture preparation time, pre-worker subprocesses, post-start deterministic
  failures, time to first useful action, human corrections, malformed results,
  false acceptance, and Worker duration.
- [x] Step 2: Update docs to describe `PreparedLane → LaunchPreflight →
  launcher`, ownership, fail-closed evidence, and deferred work.
- [x] Step 3: Run focused tests and both repository validation scopes.
- [x] Step 4: Inspect changed-file list, generated drift, whitespace, preserved
  untracked files, and plan/Git reconciliation.
- [x] Step 5: Run verification-before-completion. Mark plan `completed` only
  from `verified` evidence.

**Verification:**
- [x] `py -B -m pytest tests/test_plan_preparation.py tests/test_project_os_runtime.py tests/test_herdr_attempt_contract.py tests/test_deepagents_result_contract.py tests/test_herdr_main_launcher.py tests/test_herdr_parallel_dispatch.py tests/test_skill_chief_of_staff.py -q`
- Expected: focused suite passes.
- [x] `py -B scripts/validate_repo_contracts.py --repo-root . --scope preflight --plan docs/superpowers/plans/2026-10-08-launch-preparation-convergence-plan.md`
- Expected: preflight repository contracts pass.
- [x] `py -B scripts/validate_repo_contracts.py --repo-root . --scope audit`
- Expected: audit repository contracts pass.
- [x] `py -B scripts/validate_planning_lifecycle.py --plan docs/superpowers/plans/2026-10-08-launch-preparation-convergence-plan.md`
- Expected: active plan metadata, ledger, and required sections pass.
- [x] `git diff --check; git status --short --branch`
- Expected: no whitespace errors; branch/base and preserved untracked files
  reconcile with plan.

**Exit Criteria:**
- Baseline/candidate evidence identifies production-path effect.
- Docs match tested behavior and no deferred subsystem was added.
- Fresh verification returns `verified`, or plan remains active with exact
  blocker evidence.

**Evidence:**
- Candidate full suite: `947 passed, 1 skipped in 46.86s`.
- Preflight validation, audit validation, planning lifecycle, template, compile,
  and whitespace checks pass.
- Live read-only canonical probe ran through `project-os` / `w1:p2`: preflight
  `167.294 ms`, target discovery `0.004 ms`, launch preparation `81.609 ms`,
  observation `61081.751 ms`, pane run `79.801 ms`, total `61420.361 ms`.
- Baseline `ec92965` produced Worker exit `0`, cleanup removed, launcher exit
  `2`, `grant_verification=unverified`, and `verification_failure=grant_mismatch`.
- Candidate after tuple/list normalization produced Worker exit `0`, cleanup
  removed, launcher exit `2`, `grant_verification=verified`, and no grant
  verification failure. Both probes had `task_result.state=unverified` because
  read-only work supplied no settled checkpoint. No repository file changes
  occurred.
- Baseline/candidate runtime comparison proves grant-verification improvement;
  that read-only probe pair does not prove semantic acceptance. No performance
  claim is made from this single probe pair.
- Result-producing probes explicitly named
  `scripts.project_os_runtime.results.publish_task_result` and supplied a
  `HEAD` checkpoint plus test reference. The Worker still exited `0` without
  publishing; the 120-second candidate attempt ended with wrapper-generated
  `task_result.state=unverified`, `checkpoint=null`, and empty references.
- Follow-up canonical launcher probe used exact one-expression `py -c`
  publication with no shell operators. Attempt `69a696828741404bbefe83304cc444c1`
  exited `0`; TaskResult state `reported_completed`, producer
  `deepagents-worker`, exact assignment/attempt/task/grant bindings, checkpoint
  revision `probe`, verification reference
  `scripts.project_os_runtime/results.py`, empty remaining work, cleanup
  `removed`, and settled lifecycle receipt. This closes publication proof; no
  production result-contract patch was justified.

## Verification

- Canonical path traced, static/test baseline captured, and baseline/candidate
  live grant evidence compared. Follow-up canonical launcher probe proves
  semantic Worker-owned TaskResult publication and settlement.
- Focused tests prove preflight dependency semantics, stable assignment/fresh
  attempt identity, current TaskResult contract, semantic acceptance separation,
  and mutation detection.
- Direct backend/runtime proof covers applicable success, failure, settlement,
  cleanup, and idempotency paths.
- Both `validate_repo_contracts.py` scopes pass.
- Planning lifecycle validation passes.
- Final Git state matches branch, base, task ledger, changed-file scope, and
  preserved untracked artifacts. No commit, push, merge, or cleanup performed.

## Completion Criteria

The plan is ready for completion verification when:

1. Canonical production-path friction is distinguished from manual probe friction.
2. `PreparedLane` remains the only normalized static launch SSOT.
3. Any `LaunchPreflight` is ephemeral, references prepared facts, and reports
   root blockers without cascades.
4. Runtime discovery stays out of `plan_preparation.py`.
5. Assignment identity remains stable and attempt identity is fresh.
6. Current PR #55/#56 result and acceptance behavior is regression-proven;
   patches exist only for audited gaps.
7. Deterministic evidence never emits CoS verdicts or creates workflow truth.
8. Snapshot/hash proof detects inspection mutation without overstating prevention.
9. Baseline/candidate metrics use same canonical workload and classify friction.
10. Required tests, validators, docs, and Git evidence reconcile.

A checked box records progress, not proof.
