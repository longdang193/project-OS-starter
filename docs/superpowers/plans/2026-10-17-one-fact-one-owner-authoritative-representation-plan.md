---
artifact_type: plan
template_id: implementation-plan
contract_version: "1"
status: active
layer: change
name: one-fact-one-owner-authoritative-representation
targets:
  - scripts/project_os_runtime/results.py
  - scripts/project_os_runtime/plan_preparation.py
  - scripts/project_os_runtime/lane.py
  - scripts/project_os_runtime/attempt.py
  - scripts/project_os_runtime/acceptance.py
  - scripts/herdr_main_launcher.py
  - scripts/herdr_parallel_dispatch.py
  - scripts/dcode_project.py
  - scripts/deepagents_result_contract.py
  - scripts/herdr_attempt_contract.py
  - scripts/benchmark_worker_contract.py
  - repo_config/starter-kit-manifest.json
  - .github/workflows/runtime-contracts.yml
  - scripts/validate_repo_contracts.py
  - scripts/deploy_agent_runtime.py
  - docs/operating_system/runtime/runtime-surfaces.md
  - tests/test_project_os_runtime.py
  - tests/test_plan_preparation.py
  - tests/test_herdr_parallel_dispatch.py
  - tests/test_dcode_project.py
  - tests/test_deepagents_result_contract.py
  - tests/test_herdr_attempt_contract.py
  - tests/test_worker_contract_benchmark.py
  - tests/test_evidence_release.py
  - tests/test_live_stability_probe.py
  - tests/test_secretary_live_pilot.py
  - tests/test_secretary_receipts.py
  - tests/test_validate_repo_contracts.py
  - tests/test_deploy_agent_runtime.py
  - artifacts/runtime-observation/2026-10-17-one-fact-one-owner-cos-canary.json
  - artifacts/runtime-observation/2026-10-17-one-fact-one-owner-report.md
  - docs/superpowers/plans/2026-10-17-one-fact-one-owner-authoritative-representation-plan.md
---

# One Fact, One Owner, One Authoritative Representation

## Review Basis

This plan adopts the supplied review of `main` at commit
`ef536b25a6b6ffa02410233937d718385cc38f2d` and the merged PR #96 runtime
state, then reconciles both with the current repository source, tests,
starter-kit manifest, runtime-boundary validators, and live-stability evidence.

The central diagnosis is confirmed:

- Worker execution evidence, runtime settlement, CoS acceptance, Plan
  consequence, Git consequence, and optional Secretary attention are valid
  separate ownership boundaries.
- `TaskResult.accepted` is nevertheless carried through
  `scripts/project_os_runtime/results.py`, `scripts/dcode_project.py`,
  `scripts/herdr_main_launcher.py`, and `scripts/herdr_parallel_dispatch.py`.
  The dispatcher uses `null` to infer an acceptance-pending state even though
  the Worker result is documented as non-authoritative.
- The live CoS canary recorded operational completion, verified grants,
  settlement, retirement, and cleanup, but stopped with semantic acceptance
  unset. This supports contract convergence, not removal of CoS acceptance.
- `accepted_prerequisites` is required in runtime binding even though
  `prepare_plan_lanes()` revalidates the same identities against Plan-owned
  acceptance consequences.
- `prepare_lane_inputs()`, `scripts/herdr_attempt_contract.py`, and the
  `shell_capabilities` projection are active compatibility surfaces in the
  repository and starter-kit validation, so each needs a caller inventory
  before deletion.
- `release_authorized_evidence()` contains a duplicated identical mismatch
  branch in `scripts/project_os_runtime/acceptance.py`.
- No production caller of `evaluate_acceptance()` exists in repository search;
  the runtime must not invent a new controller or make the dispatcher the
  acceptance owner. A real CoS/controller acceptance decision remains an
  explicit canary gate.

## Goal

Converge the active runtime contracts so each lifecycle fact has one owner and
one authoritative representation:

```text
Worker        owns reported execution result and verification evidence
Runtime       owns process/resource settlement, retirement, cleanup, and reuse
CoS           owns semantic PASS | FAIL | BLOCKED acceptance
Plan          owns accepted workflow consequence
Git/GitHub    own repository and remote consequences
Secretary     owns optional attention routing
```

Remove only proven compatibility duplication. Preserve attempt identity,
stale-plan protection, dependency readiness, bounded Worker ownership,
settlement and cleanup proof, positive retirement, review/integration gates,
no-refill behavior, and all fail-closed paths. Runtime capacity reuse never
authorizes controller-owned retry, continuation, acceptance, or Plan
advancement.

## Implementation Outcomes

### Worker results no longer self-describe semantic acceptance

`TaskResult` v1 contains execution status, progress, checkpoint,
verification, remaining work, continuation, and attempt identity, but no
`accepted` field in new writes. Readers tolerate a legacy `accepted` field for
transition compatibility, ignore it semantically, and never branch on it; no
TaskResult v2 is introduced unless repository evidence requires a versioned
breaking migration. Worker publication and launcher parsing remain bounded and
identity-checked. A settled completed attempt is runtime evidence with
acceptance still pending outside the Worker result. Only the existing CoS
`evaluate_acceptance()` / `AcceptanceDecision` boundary can produce `PASS`,
`FAIL`, or `BLOCKED` and advance Plan state.

### Plan-owned prerequisite identity is derived once

`prepare_plan_lanes()` derives accepted prerequisite revision, candidate, and
Plan identity from persisted Plan acceptance consequences. `runtime.json`
contains runtime-owned launch facts only. No caller reconstructs and resubmits
the accepted prerequisite identity graph. The finalized `PreparedLane` retains
the derived prerequisite projection, including it in `execution_binding_digest`
so tampering or stale substitution still fails closed. The dispatcher
continues to verify the derived accepted revision against the consumer
worktree before launch.

### Compatibility surfaces have named removal evidence

`prepare_lane_inputs()`, `scripts/herdr_attempt_contract.py`, the
`shell_capabilities` projection, and
`runtime_completion_is_not_acceptance()` are independently evaluated. Each is
removed only when its own caller inventory proves it compatibility-only; an
active consumer may retain a candidate with that consumer and retention reason
recorded. The canonical `scripts/project_os_runtime` modules remain the
maintained owners.

### Acceptance and runtime evidence remain separate

Live evidence records retain separate launch, task-result, settlement, and
acceptance sources. The canary can report `completed + settled + retired +
acceptance pending` without being misclassified as accepted. A positive CoS
acceptance decision is required before topology rows are promoted.

## Scope Classification

- **In scope:** Worker-result acceptance-field removal; explicit pending
  handoff semantics; Plan-derived prerequisite binding; compatibility-surface
  inventory and deletion; duplicate mismatch-branch removal; focused tests,
  runtime documentation, starter-kit manifest, and validators; a post-change
  CoS canary gate.
- **Preserved:** CoS semantic acceptance; Plan/Git workflow truth; exact
  attempt/assignment/candidate identity; stale-result and stale-plan checks;
  dependency readiness; runtime settlement, cleanup, retirement, quarantine,
  and release authorization; sequential acquisition; no refill; optional
  Secretary semantics.
- **Deferred:** managed Secretary runtime retirement, polling/observation
  optimization, whole-plan freshness narrowing, scheduler/refill changes,
  and deterministic merge/integration optimization.
- **Out of scope:** new coordinator, workflow database, scheduler, persistent
  heartbeat, acceptance registry, Worker self-acceptance, provider changes,
  credential changes, upstream runtime installation, or public publication.

## Execution Approach

- Mode: `inline sequential`
- Coordination: `git-tracked`
- Required skills: `skill-writing-plans`, `skill-executing-plans`, `skill-chief-of-staff`, `skill-using-git-worktrees`, `skill-test-driven-development`, `skill-backend-verification`, `skill-code-standards`, `skill-requesting-code-review`, `skill-verification-before-completion`
- Isolation: dedicated task-owned worktree from the reviewed `main` commit; preserve the current `main` checkout
- Commit policy: local checkpoint commits are permitted only after task-local proof and lead-controller acceptance; no push, merge, publication, or branch disposition is authorized by this plan
- Preauthorized local actions: edit the task-owned implementation worktree within the declared targets, run focused and required repository validation, update this active plan ledger, and record sanitized task evidence
- User-approval actions: implementation edits, compatibility deletion, live runtime execution, provider or credential access, generated runtime deployment, commits, push, merge, publication, and destructive cleanup
- Parallel ownership: `none`; acceptance, runtime, Plan preparation, compatibility, and generated-surface changes share contracts and are serialized
- Sequential fallback: execute Tasks 1–6 in order; stop at any ownership, caller, base, or acceptance-evidence gate instead of starting a later deletion or measurement task

## Coordination State

- Coordination owner: `single lead controller`
- Coordination schema: `2`
- Branch: `codex/one-fact-one-owner`
- Base commit: `ef536b25a6b6ffa02410233937d718385cc38f2d`
- Expected workspace: `dedicated task-owned worktree from the reviewed base; leave local main untouched`
- Next action: `execute Task 4 proven compatibility-layer cleanup and generated-surface reconciliation`
- Blockers: `none; Task 1 acceptance boundary gate resolved through the existing lead-controller procedure`

| Task | State | Workspace | Executor | Depends On | Required Proof | Evidence |
| --- | --- | --- | --- | --- | --- | --- |
| Task 1 | `completed` | dedicated task worktree | `codex` | none | baseline tests, caller inventory, and CoS boundary gate | 335 baseline passed; native CoS boundary exercised with 3 focused acceptance/Plan tests |
| Task 2 | `completed` | task worktree | `codex` | Task 1 | TaskResult/settlement contract tests | 581 passed, 1 skipped; legacy acceptance ignored and stripped; dispatcher pending-acceptance path preserved |
| Task 3 | `completed` | task worktree | `codex` | Task 1 | Plan-derived prerequisite and launch-preflight tests | 131 passed; runtime callers cannot supply accepted prerequisite graph; artifact branch removed |
| Task 4 | `completed` | task worktree | `codex` | Tasks 2–3 | compatibility deletion, manifest, validator, and doc checks | 347 focused tests passed, 1 skipped; repo contracts and starter-kit validation passed |
| Task 5 | `pending` | sealed task worktree | `codex` | Task 4 | CoS canary with explicit acceptance decision or recorded gate stop | pending |
| Task 6 | `pending` | task worktree | `codex` | Task 5 | independent review and final repository verification | pending |

## Task Breakdown

### Task 1: Establish the ownership and caller inventory

**Purpose:**
- Prove the exact active write set, supported consumers, generated surfaces,
  and baseline behavior before deleting any compatibility representation.

**Task Function:**
- Establish source-first contract and dependency evidence.

**Template Profile:**
- Controller-selected: `none (lead controller)`
- Selection basis: low ambiguity; the lead owns scope and the deletion gate.

**Validator Profile (optional):**
- Controller-selected: `none`
- Selection basis: source-wide search, manifest inspection, and baseline tests.

**Specification Coverage:**
- One owner per lifecycle fact; no compatibility deletion without a named
  consumer inventory and removal condition.

**Required Skills:**
- `skill-using-git-worktrees`, `skill-systematic-debugging`

**Files And Symbols:**
- Inspect: `scripts/project_os_runtime/results.py:validate_task_result`, `encode_task_result`, `parse_task_result`
- Inspect: `scripts/herdr_main_launcher.py:_classify_deepagents_outcome`, `_build_assignment_result`
- Inspect: `scripts/herdr_parallel_dispatch.py:launch_preflight`, `run_lane`, `runtime_completion_is_not_acceptance`
- Inspect: `scripts/project_os_runtime/plan_preparation.py:_REQUIRED_BINDING_FIELDS`, `_accepted_prerequisites`, `prepare_lane_inputs`, `prepare_plan_lanes`
- Inspect: `scripts/project_os_runtime/lane.py:PreparedLane`, `prepare_lane`
- Inspect: `scripts/project_os_runtime/attempt.py:execution_binding_digest`
- Inspect: `scripts/project_os_runtime/acceptance.py:evaluate_acceptance`, `release_authorized_evidence`
- Inspect: `repo_config/starter-kit-manifest.json`, `scripts/validate_repo_contracts.py`, `scripts/deploy_agent_runtime.py`
- Verify: `tests/test_project_os_runtime.py`, `tests/test_plan_preparation.py`, `tests/test_herdr_parallel_dispatch.py`, `tests/test_dcode_project.py`, `tests/test_deepagents_result_contract.py`, `tests/test_validate_repo_contracts.py`, `tests/test_deploy_agent_runtime.py`

**Dependencies:**
- None.

**Authority:**
- Preauthorized local actions: create the isolated planning worktree, inspect source/configuration/tests, run read-only baseline checks, and record caller classifications in this plan
- Stop for: dirty or mismatched base, an active external consumer that requires the legacy field, an ownership conflict not resolvable without a specification change, or no identifiable/exercisable supported CoS/controller acceptance invocation boundary

**Steps:**
- [x] Step 1: Verify the worktree is based on `ef536b25a6b6ffa02410233937d718385cc38f2d` and preserve unrelated changes outside the task worktree.
- [x] Step 2: Run the focused baseline suite: `py -B -m pytest -q tests/test_project_os_runtime.py tests/test_plan_preparation.py tests/test_herdr_parallel_dispatch.py tests/test_dcode_project.py tests/test_deepagents_result_contract.py` (`335 passed in 16.89s`).
- [x] Step 3: Build a caller matrix for `accepted`, `accepted_prerequisites`, `prepare_lane_inputs`, `shell_capabilities`, `runtime_completion_is_not_acceptance`, and `scripts/herdr_attempt_contract.py`, including starter-kit and validator consumers.
- [x] Step 4: Confirm `evaluate_acceptance()` has no in-repo production caller, identify an exercisable supported CoS/controller invocation boundary for Task 5, and record the exact handoff; do not assign acceptance to the dispatcher. The existing native lead-controller procedure is the supported boundary, and its disposable acceptance-to-Plan proof passed with `3 passed`.
- [x] Step 5: Confirm no active production `artifact_ref` or `artifact_available` consumer requires preserving a second prerequisite identity graph.

**Verification:**
- [x] `git status --short --branch` and `git rev-parse HEAD`
- Expected: isolated task worktree at the reviewed base with only the task-owned plan untracked before implementation; observed `codex/one-fact-one-owner` at `ef536b25a6b6ffa02410233937d718385cc38f2d`.
- [x] `py -B -m pytest -q tests/test_project_os_runtime.py tests/test_plan_preparation.py tests/test_herdr_parallel_dispatch.py tests/test_dcode_project.py tests/test_deepagents_result_contract.py`
- Expected: baseline passes before contract edits; observed `335 passed in 16.89s`.
- [x] `rg -n "accepted|accepted_prerequisites|prepare_lane_inputs|shell_capabilities|herdr_attempt_contract|runtime_completion_is_not_acceptance" scripts tests docs repo_config`
- Expected: every match is classified as canonical, consumer, compatibility, fixture, or historical plan text; observed inventory below.
- [x] `rg -n "evaluate_acceptance\(" scripts --glob '*.py'`
- Expected: only the canonical definition/export path remains in production source; observed definition in `scripts/project_os_runtime/acceptance.py` and export in `scripts/project_os_runtime/__init__.py`, with callers only in tests.

**Exit Criteria:**
- The implementation write set, deletion candidates, and supported consumers
  are recorded. The current Codex lead-controller session exercises the
  existing native CoS/controller boundary through the canonical
  `evaluate_acceptance()` and `apply_accepted_plan_transitions()` APIs; focused
  disposable proof passed with `3 passed`. Caller inventory: `accepted` is present in
  canonical result/launcher/dispatcher projections plus fixtures and tests;
  `accepted_prerequisites` is supplied through dispatcher runtime bindings and
  benchmark fixtures while Plan preparation, `PreparedLane`, and the digest own
  the derived identity; `prepare_lane_inputs()` has only the package export and
  tests; `shell_capabilities` is limited to canonical result/receipt projection
  and tests; `runtime_completion_is_not_acceptance()` is dispatcher/test-only;
  `scripts/herdr_attempt_contract.py` remains a manifest, validator, CI, deploy,
  and test compatibility surface; `artifact_ref`/`artifact_available` have no
  active production consumer beyond the Plan/dispatcher compatibility path.
  The boundary remains controller-owned and must not be moved into the
  dispatcher.

### Task 2: Remove Worker acceptance metadata and separate settlement from acceptance

**Purpose:**
- Make Worker results evidence-only while preserving runtime settlement and
  fail-closed ownership behavior.

**Task Function:**
- Converge the task-result schema and all runtime projections to one semantic
  acceptance owner.

**Template Profile:**
- Controller-selected: `none (lead controller)`
- Selection basis: material cross-module backend contract change executed inline by the lead controller.

**Validator Profile (optional):**
- Controller-selected: `none`
- Selection basis: validator must verify schema, failure, settlement, and stale-identity behavior independently.

**Specification Coverage:**
- Remove `TaskResult.accepted`; preserve `PASS | FAIL | BLOCKED` in CoS
  acceptance and keep settlement independent.
- Migrate TaskResult v1 with tolerant reads for legacy `accepted`, strict new
  writes without it, and no semantic branch on the legacy field.

**Required Skills:**
- `skill-test-driven-development`, `skill-backend-verification`, `skill-code-standards`

**Files And Symbols:**
- Modify: `scripts/project_os_runtime/results.py:validate_task_result`, `encode_task_result`, `parse_task_result`, and capability evidence projection
- Modify: `scripts/dcode_project.py:_worker_task_result_diagnostic`, task-result publication fallback, and result-receipt capability projection
- Modify: `scripts/herdr_main_launcher.py:_classify_deepagents_outcome`, `_build_assignment_result`, and task-result fallback projections
- Modify: `scripts/herdr_parallel_dispatch.py:run_lane` classification and result projection; delete `runtime_completion_is_not_acceptance`
- Inspect only: `scripts/project_os_runtime/acceptance.py:evaluate_acceptance`, `apply_accepted_plan_transitions`; do not move acceptance into runtime dispatch
- Verify: `tests/test_dcode_project.py`, `tests/test_deepagents_result_contract.py`, `tests/test_herdr_parallel_dispatch.py`, `tests/test_project_os_runtime.py`

**Dependencies:**
- Task 1 caller inventory confirms the repository and generated runtime are
  the supported TaskResult consumers.

**Authority:**
- Preauthorized local actions: edit the named result, launcher, dispatcher, and focused-test surfaces; run direct lifecycle tests; and update the task ledger after accepted proof
- Stop for: any attempt to infer CoS `PASS` from exit code or settlement, a required external TaskResult v1 consumer that cannot tolerate the migration, changed attempt identity, or unresolved cleanup/reuse behavior

**Steps:**
- [x] Step 1: Make new TaskResult writers omit `accepted`; make readers tolerate and discard legacy `accepted` without validation, branching, or semantic projection, and introduce no v2 unless repository evidence requires a versioned breaking migration.
- [x] Step 2: Remove `task_accepted` and Worker-owned acceptance projections from launcher assignments; retain authoritative task status, verification, attempt identity, and settlement evidence.
- [x] Step 3: Change dispatcher classification so a completed, settled, retired attempt has reusable capacity with a non-authoritative acceptance-pending handoff, while unresolved or malformed result evidence remains fail-closed and occupied; preserve controller-owned retry, continuation, acceptance, and Plan advancement.
- [x] Step 4: Preserve `evaluate_acceptance()` and `apply_accepted_plan_transitions()` as the only semantic acceptance-to-Plan path; add no dispatcher-owned acceptance decision.
- [x] Step 5: Update focused tests for completed/settled/pending, failed/settled, malformed, stale identity, timeout, and cleanup-recovery cases.

**Verification:**
- [x] `py -B -m pytest -q tests/test_dcode_project.py tests/test_deepagents_result_contract.py tests/test_herdr_parallel_dispatch.py tests/test_herdr_main_launcher.py tests/test_project_os_runtime.py tests/test_evidence_release.py tests/test_plan_preparation.py`
- Expected: no Worker result contains `accepted`; settled failures retire only after existing cleanup/descendant proof; incomplete ownership remains occupied; CoS acceptance APIs remain unchanged and authoritative.
- [x] Add or retain a regression in `tests/test_evidence_release.py` proving a legacy `TaskResult` with `accepted=true` cannot authorize evidence release and has no semantic effect.
- [x] `rg -n "task_result.*accepted|task_accepted|accepted.*task_result|runtime_completion_is_not_acceptance" scripts tests -g '*.py'`
- Expected: no active runtime or test consumer remains; accepted Plan-consequence fields remain only in acceptance/Plan-preparation paths.

**Exit Criteria:**
- TaskResult, launcher, dispatcher, worker wrapper, and tests agree that
  runtime completion is evidence and not semantic acceptance.

### Task 3: Derive accepted prerequisites from Plan truth

**Purpose:**
- Remove the caller-supplied duplicate acceptance identity graph from
  runtime bindings while retaining dependency readiness and launch freshness.

**Task Function:**
- Make Plan preparation the sole derivation owner for accepted prerequisite
  identities.

**Template Profile:**
- Controller-selected: `none (lead controller)`
- Selection basis: contract migration across preparation, lane normalization,
  attempt digest, dispatcher preflight, fixtures, and tests.

**Validator Profile (optional):**
- Controller-selected: `none`
- Selection basis: validator must check derived identity and launch-bound Git behavior independently.

**Specification Coverage:**
- Remove caller-owned runtime `accepted_prerequisites` input; preserve the
  derived accepted revision, candidate, Plan identity, dependency readiness,
  base-ancestry checks, and the derived projection in `PreparedLane` and
  `execution_binding_digest`.

**Required Skills:**
- `skill-test-driven-development`, `skill-backend-verification`, `skill-code-standards`

**Files And Symbols:**
- Modify: `scripts/project_os_runtime/plan_preparation.py:_REQUIRED_BINDING_FIELDS`, `_BINDING_FIELDS`, `_accepted_prerequisites`, `_worker_brief`, `_prepare_plan_lanes`, `prepare_plan_lanes`
- Modify: `scripts/project_os_runtime/lane.py:PreparedLane`, `prepare_lane`, and mapping fields
- Modify: `scripts/project_os_runtime/attempt.py:execution_binding_digest`
- Modify: `scripts/herdr_parallel_dispatch.py:launch_preflight` prerequisite verification
- Modify: `scripts/benchmark_worker_contract.py` and `tests/fixtures/worker_contract_benchmark/manifest.json`
- Verify: `tests/test_plan_preparation.py`, `tests/test_herdr_parallel_dispatch.py`, `tests/test_worker_contract_benchmark.py`
- Update: `docs/operating_system/runtime/runtime-surfaces.md:Plan Dispatch`

**Dependencies:**
- Task 1 confirms no supported non-Git artifact reference requires a separate
  runtime-owned prerequisite field.
- Task 2 preserves the accepted Plan consequence shape used for derivation.

**Authority:**
- Preauthorized local actions: edit the named Plan-preparation, lane, attempt-digest, dispatcher, fixture, test, and runtime-guidance surfaces; run focused dependency and launch tests
- Stop for: missing persisted accepted consequence, changed dependency readiness semantics, any need for a new registry/digest/state store, or an active artifact reference that cannot be derived from Plan truth

**Steps:**
- [x] Step 1: Remove `accepted_prerequisites` from required runtime binding fields and from the documented `runtime.json` contract.
- [x] Step 2: Change `_accepted_prerequisites()` to derive each dependency binding from the selected Plan graph and persisted accepted consequence; retain exact candidate/revision/Plan checks.
- [x] Step 3: Remove the unused `artifact_ref`/`artifact_available` compatibility branch after Task 1 confirms no active consumer; retain revision reachability as the launch-bound Git proof.
- [x] Step 4: Keep the derived accepted prerequisite identity in `PreparedLane` and in the execution-binding digest input; remove only the caller-supplied runtime copy while retaining the Plan revision/source and task/dependency inputs that protect freshness.
- [x] Step 5: Migrate benchmark fixtures and tests to pass only runtime-owned launch facts and assert that callers cannot override derived prerequisite identities.

**Verification:**
- [x] `py -B -m pytest -q tests/test_plan_preparation.py tests/test_herdr_parallel_dispatch.py tests/test_worker_contract_benchmark.py`
- Expected: dependent lanes receive the exact accepted prerequisite derived from Plan evidence; missing, stale, contradictory, or unreachable consequences block before launch; zero-prerequisite lanes remain valid.
- [x] `rg -n "accepted_prerequisites|artifact_ref|artifact_available" scripts tests docs/operating_system/runtime/runtime-surfaces.md -g '*.py' -g '*.md' -g '*.json'`
- Expected: no runtime caller supplies the removed graph; any remaining accepted-prerequisite text is a derived internal projection or explicit historical plan evidence.

**Exit Criteria:**
- Plan preparation is the only owner that reconstructs accepted prerequisite
  identity, and dispatcher preflight consumes only that derived projection.

### Task 4: Remove proven compatibility layers and reconcile generated surfaces

**Purpose:**
- Delete compatibility-only code after the consumer inventory and keep the
  canonical runtime, starter-kit, validators, and docs synchronized.

**Task Function:**
- Perform bounded deletion and source/generated-surface reconciliation.

**Template Profile:**
- Controller-selected: `none (lead controller)`
- Selection basis: deletion-heavy cross-surface change with starter-kit and validator impact.

**Validator Profile (optional):**
- Controller-selected: `none`
- Selection basis: independent review must confirm no deleted compatibility consumer remains.

**Specification Coverage:**
- Remove only surfaces proven compatibility-only; delete the duplicated
  acceptance release mismatch branch.
- Gate each compatibility candidate independently: remove it when its own
  caller inventory proves it obsolete, or retain it with a named active
  consumer and retention reason. The duplicate mismatch branch is removable
  unconditionally after regression proof.

**Required Skills:**
- `skill-code-standards`, `skill-backend-verification`

**Files And Symbols:**
  - Delete after inventory: `scripts/herdr_attempt_contract.py` only if no active consumer remains
  - Delete after migration: `scripts/project_os_runtime/plan_preparation.py:prepare_lane_inputs` only if no active consumer remains
- Modify exports: `scripts/project_os_runtime/__init__.py`, `scripts/deepagents_result_contract.py`
  - Modify canonical capability projection: `scripts/project_os_runtime/results.py:_capability_evidence`, `scripts/dcode_project.py:_publish_result_receipt`
- Modify duplicate branch: `scripts/project_os_runtime/acceptance.py:release_authorized_evidence`
- Modify consumers/validators: `repo_config/starter-kit-manifest.json`, `scripts/validate_repo_contracts.py`, `scripts/deploy_agent_runtime.py` only if inventory identifies a stale assertion, and matching tests
  - Migrate or delete wrapper-only tests: `tests/test_herdr_attempt_contract.py`; verify canonical coverage in `tests/test_project_os_runtime.py`
  - Update: `.github/workflows/runtime-contracts.yml` whenever the attempt wrapper or its contract tests are removed or renamed
- Verify: `docs/operating_system/runtime/runtime-surfaces.md`, `tests/test_validate_repo_contracts.py`, `tests/test_deploy_agent_runtime.py`, `tests/test_plan_preparation.py`, `tests/test_dcode_project.py`, `tests/test_deepagents_result_contract.py`

**Dependencies:**
- Tasks 1–3 complete; all deletion candidates have a named removal condition.

**Authority:**
- Preauthorized local actions: delete only inventoried compatibility files/symbols, update canonical exports/manifest/validators/docs/tests, and run repository contract and starter-kit checks
- Stop for: any unclassified caller, required public/starter-kit compatibility promise, generated-output drift, or a validator change that weakens rather than removes stale architecture

**Steps:**
- [x] Step 1: Retain `scripts/herdr_attempt_contract.py` because its manifest, validator, deployment, CI, and test consumers remain active; no wrapper deletion is authorized.
- [x] Step 2: Migrate `prepare_lane_inputs()` tests and exports to `prepare_plan_lanes()`; remove the adapter and its runtime-surface documentation.
- [x] Step 3: Make canonical `capabilities` the only receipt capability projection; remove `shell_capabilities` emission, comparison, and compatibility parsing while retaining internal capability resolution for worker launch.
- [x] Step 4: Delete the unreachable duplicate `if mismatch is not None` branch in `release_authorized_evidence()` without changing release binding, quarantine, digest, or idempotency behavior.
- [x] Step 5: Update canonical documentation and validate a fresh starter-kit build using the inspected CLI flags.

**Verification:**
- [ ] `py -B -m pytest -q tests/test_plan_preparation.py tests/test_dcode_project.py tests/test_deepagents_result_contract.py tests/test_validate_repo_contracts.py tests/test_deploy_agent_runtime.py tests/test_project_os_runtime.py tests/test_evidence_release.py`
- Expected: migrated consumers pass; deleted files/symbols are not imported; evidence release remains fail-closed, same-attempt, digest-checked, and idempotent.
- [ ] `py -B scripts/validate_repo_contracts.py --repo-root .`
- Expected: runtime ownership, dependency, manifest, and generated-surface contracts pass; any retained compatibility candidate has a named active consumer and retention reason recorded.
- [ ] `py -B scripts/build_starter_kit.py --help` and `py -B scripts/validate_starter_kit.py --help`
- Expected: exact current CLI flags are recorded before the build/validation commands are run.
- [ ] Run `py -B scripts/build_starter_kit.py --repo-root . --output-root <task-owned-temp>` and `py -B scripts/validate_starter_kit.py --repo-root . --output-root <task-owned-temp>` using the inspected flags.
- Expected: the built starter-kit output validates against the canonical manifest and contains no stale deleted compatibility surface.
- [ ] If `scripts/herdr_attempt_contract.py` is removed, run the supported Windows and Ubuntu `runtime-contracts.yml` CI matrix after publication.
- [ ] `git diff --check`
- Expected: no whitespace errors.

**Task 4 Evidence:**
- `py -B -m pytest -q tests/test_plan_preparation.py tests/test_dcode_project.py tests/test_deepagents_result_contract.py tests/test_validate_repo_contracts.py tests/test_deploy_agent_runtime.py tests/test_project_os_runtime.py tests/test_evidence_release.py` — 347 passed, 1 skipped.
- `py -B scripts/validate_repo_contracts.py --repo-root .` — passed, including planning lifecycle and generated-surface checks.
- `py -B scripts/build_starter_kit.py --help` and `py -B scripts/validate_starter_kit.py --help` — current flags inspected.
- Fresh build and validation under `C:\tmp\project-os-one-fact-one-owner-starter-kit-2adb2cecada549238f1623f1c1a806fd` — passed.
- `git diff --check` — passed.

**Exit Criteria:**
- Compatibility-only surfaces are gone or explicitly retained with a named
  active consumer; canonical sources, starter-kit configuration, validators,
  tests, and runtime documentation agree.

### Task 5: Re-run the CoS canary through the explicit acceptance gate

**Purpose:**
- Prove that operationally settled Worker evidence can be handed to the
  existing CoS acceptance boundary without using Worker-owned acceptance.

**Task Function:**
- Execute a bounded representative trace and capture acceptance ownership
  evidence.

**Template Profile:**
- Controller-selected: `none (lead controller)`
- Selection basis: live runtime execution requires environment-specific capability and explicit runtime authority.

**Validator Profile (optional):**
- Controller-selected: `none`
- Selection basis: validator must independently inspect sanitized canary evidence and acceptance provenance.

**Specification Coverage:**
- Runtime settlement is not semantic acceptance; only a real CoS/controller
  `AcceptanceDecision` may promote the canary or advance Plan state.

**Required Skills:**
- `skill-backend-verification`, `skill-disposable-artifact-cleanup`

**Files And Symbols:**
- Execute: `scripts/herdr_parallel_dispatch.py:run_parallel` with the existing two-lane bounded canary protocol
- Inspect: `scripts/project_os_runtime/acceptance.py:evaluate_acceptance`, `validate_acceptance_decision`, `apply_accepted_plan_transitions`
- Inspect: `scripts/run_live_stability_probe.py:record_cos_result`, `validate_owner_result`
- Inspect: `scripts/secretary_live_pilot.py:validate_receipt` and `scripts/project_os_runtime/secretary_receipts.py:validate_live_receipt`
- Produce: `artifacts/runtime-observation/2026-10-17-one-fact-one-owner-cos-canary.json` and `artifacts/runtime-observation/2026-10-17-one-fact-one-owner-report.md`
- Verify: `tests/test_herdr_parallel_dispatch.py`, `tests/test_live_stability_probe.py`, `tests/test_secretary_live_pilot.py`, `tests/test_secretary_receipts.py`

**Dependencies:**
- Tasks 2–4 complete and sealed at a reviewed implementation checkpoint.

**Authority:**
- Preauthorized local actions: run the existing bounded read-only canary, write sanitized task-owned evidence, inspect acceptance/settlement records, and remove only positively retired task-owned resources
- Stop for: missing provider/target/credential capability, absent real CoS acceptance producer, unresolved cleanup or retirement, stale identity, or any need to manufacture an accepted row or alter external state

**Steps:**
- [ ] Step 1: Pin the canary protocol to the implementation checkpoint and record provider/profile identity without credentials or raw provider output.
- [ ] Step 2: Run exactly two predeclared independent read-only lanes with no refill and preserve separate task-result, settlement, and acceptance sources.
- [ ] Step 3: Confirm each lane can reach `execution completed`, `resource settled`, `capacity retired`, and `TaskResult reported_completed` without a Worker `accepted` field.
- [ ] Step 4: Supply result evidence to the existing CoS/controller acceptance boundary and record the returned `PASS`, `FAIL`, or `BLOCKED` `AcceptanceDecision` with exact attempt, candidate, Plan, and evidence bindings.
- [ ] Step 5: If no real acceptance producer is available, record `acceptance_pending` and stop the matrix; do not convert runtime completion into semantic acceptance.
- [ ] Step 6: Validate sanitized evidence, prove retirement/cleanup, and remove task-owned disposable resources only after positive retirement evidence.

**Verification:**
- [ ] `py -B -m pytest -q tests/test_herdr_parallel_dispatch.py tests/test_live_stability_probe.py tests/test_secretary_live_pilot.py tests/test_secretary_receipts.py`
- Expected: pending acceptance is represented separately from settled execution; accepted rows require a real CoS decision and exact source binding; blocked or incomplete canaries remain non-observed.
- [ ] `py -B scripts/validate_repo_contracts.py --repo-root .`
- Expected: live/runtime boundary guidance and contract validators pass.

**Exit Criteria:**
- A sanitized canary proves the post-change boundary, or the evidence records
  an explicit acceptance-producer blocker and no topology economics claim is
  made.

### Task 6: Independent review and final verification

**Purpose:**
- Reconcile the complete change against the one-owner invariant and prevent
  deletion of a safety contract disguised as compatibility cleanup.

**Task Function:**
- Perform independent change review and final evidence reconciliation.

**Template Profile:**
- Controller-selected: `none (lead controller)`
- Selection basis: independent review scope is determined after the implementation diff exists.

**Validator Profile (optional):**
- Controller-selected: `none`
- Selection basis: final validator selection is independent of the executor profile.

**Specification Coverage:**
- All implementation outcomes, preserved invariants, scope boundaries, and
  final verification requirements.

**Required Skills:**
- `skill-requesting-code-review`, `skill-verification-before-completion`

**Files And Symbols:**
- Review: all Task 2–5 modified paths and their callers
- Verify: `scripts/validate_repo_contracts.py`, `scripts/validate_planning_lifecycle.py`, starter-kit validation, focused tests, and the full test suite
- Reconcile: this plan's Coordination State, task ledger, canary evidence, and deferred measurement handoff

**Dependencies:**
- Task 5 complete or explicitly blocked with sanitized evidence and blocker
  recorded.

**Authority:**
- Preauthorized local actions: inspect the final diff, run repository/planning/starter-kit validators, run tests, and record review findings in this plan
- Stop for: unresolved high-risk review finding, changed base or scope, missing fresh proof, or any claim that depends on unmeasured topology economics

**Steps:**
- [ ] Step 1: Request one independent review focused on ownership boundaries, stale-result protection, settlement/cleanup safety, Plan-derived prerequisite identity, and compatibility deletion.
- [ ] Step 2: Resolve actionable findings without expanding the plan; rerun affected focused proof.
- [ ] Step 3: Run final repository, planning, starter-kit, and full test validation.
- [ ] Step 4: Record all deviations, blockers, and deferred performance/Secretary questions in the plan before any branch disposition.

**Verification:**
- [ ] `py -B -m pytest -q`
- Expected: full repository suite passes, or every unrelated pre-existing failure is recorded with its command and scope.
- [ ] `py -B scripts/validate_planning_lifecycle.py --plan docs/superpowers/plans/2026-10-17-one-fact-one-owner-authoritative-representation-plan.md`
- Expected: the plan satisfies the implementation-plan contract and task ledger rules.
- [ ] `git diff --check` and `git status --short --branch`
- Expected: clean diff formatting and explicit final workspace state.

**Exit Criteria:**
- Independent review and fresh verification confirm the implementation removes
  duplicated semantic representations without weakening acceptance, settlement,
  identity, freshness, cleanup, or release safety.

## Deferred Measurement Handoff

After Task 5 produces a real accepted CoS canary, create a separate approved
measurement plan for matched direct-controller, single-Worker, and two-lane CoS
trials. Measure accepted-outcome latency, observation subprocesses, receipt
checks, diagnostic calls, and completion-detection delay under the same workload
and environment. Do not optimize polling, scheduler behavior, review/integration
activation, or whole-plan freshness in this plan. If Task 5 remains
`acceptance_pending`, the measurement plan stays blocked.

## Verification

- `py -B -m pytest -q tests/test_project_os_runtime.py tests/test_plan_preparation.py tests/test_herdr_parallel_dispatch.py tests/test_dcode_project.py tests/test_deepagents_result_contract.py tests/test_evidence_release.py tests/test_live_stability_probe.py tests/test_secretary_live_pilot.py tests/test_secretary_receipts.py`
- `py -B scripts/validate_repo_contracts.py --repo-root .`
- `py -B scripts/validate_planning_lifecycle.py --plan docs/superpowers/plans/2026-10-17-one-fact-one-owner-authoritative-representation-plan.md`
- `py -B scripts/build_starter_kit.py --help`
- `py -B scripts/validate_starter_kit.py --help`
- `py -B scripts/build_starter_kit.py --repo-root . --output-root <task-owned-temp>`
- `py -B scripts/validate_starter_kit.py --repo-root . --output-root <task-owned-temp>`
- `py -B -m pytest -q`
- `git diff --check`

## Completion Criteria

The plan is ready for completion verification when:

1. `TaskResult` contains no Worker-owned semantic acceptance field and every
   runtime consumer treats settlement and acceptance as separate facts.
2. CoS `AcceptanceDecision` remains the only semantic outcome that can advance
   Plan state, with exact identity and freshness validation intact.
3. Accepted prerequisite identity is derived from Plan evidence rather than
   reconstructed in runtime input.
4. Compatibility surfaces are removed only where caller, manifest, validator,
   and supported-runtime inventories prove they are no longer required.
5. Focused backend, lifecycle, release, starter-kit, planning, and full-suite
   proof is fresh and recorded.
6. The CoS canary either produces a real, exact-bound acceptance decision or
   records an explicit acceptance-producer blocker without promoting synthetic
   topology evidence.
7. Deferred managed-Secretary, polling, scheduler, freshness, and integration
   optimization questions remain outside this plan and have no unmeasured
   implementation claim here.

The plan may be marked `completed` only after
`skill-verification-before-completion` returns verified evidence. Branch
disposition, push, merge, publication, and worktree cleanup remain separately
authorized actions.
