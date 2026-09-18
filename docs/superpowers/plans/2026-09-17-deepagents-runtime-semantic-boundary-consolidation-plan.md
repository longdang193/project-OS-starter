---
layer: change
artifact_type: plan
status: completed
template_id: implementation-plan
contract_version: "1"
name: deepagents-runtime-semantic-boundary-consolidation
parent_spec: docs/superpowers/specs/2026-09-14-parallel-deepagents-dispatch-spec.md
targets:
  - scripts/project_os_runtime/__init__.py
  - scripts/project_os_runtime/attempt.py
  - scripts/project_os_runtime/results.py
  - scripts/project_os_runtime/capabilities.py
  - scripts/project_os_runtime/lane.py
  - scripts/project_os_runtime/admission.py
  - scripts/herdr_attempt_contract.py
  - scripts/deepagents_result_contract.py
  - scripts/herdr_main_launcher.py
  - scripts/herdr_parallel_dispatch.py
  - scripts/dcode_project.py
  - scripts/deploy_agent_runtime.py
  - scripts/validate_repo_contracts.py
  - repo_config/starter-kit-manifest.json
  - .github/workflows/runtime-contracts.yml
  - docs/operating_system/runtime/runtime-surfaces.md
  - tests/test_herdr_attempt_contract.py
  - tests/test_deepagents_result_contract.py
  - tests/test_dcode_project.py
  - tests/test_herdr_main_launcher.py
  - tests/test_herdr_parallel_dispatch.py
  - tests/test_deploy_agent_runtime.py
  - tests/test_validate_repo_contracts.py
  - tests/test_starter_kit_generation.py
  - tests/test_project_os_runtime.py
---

# Consolidate DeepAgents Runtime Semantic Boundaries

## Review Basis

Reviewed pasted verdicts against `origin/main` at `3b64fb1b657c3617631a389d92a7d5d1b69740df`.
Local `main` is `7fe01a3`, six commits behind that reviewed ref; execution must
first select an exact Git base. Existing runtime plans in this area are marked
`completed`, so this plan covers only verified residuals and consolidation.

Verified findings:

- Capability syntax and host executable checks are duplicated in
  `scripts/dcode_project.py`, `scripts/herdr_main_launcher.py`, and
  `scripts/herdr_parallel_dispatch.py`. Worker validation correctly has access
  to worker `PATH`; controller-side `shutil.which()` checks can disagree with it.
- `scripts/herdr_parallel_dispatch.py:run_lane()` fabricates a settlement
  mapping from `execution` and `cleanup` before calling shared settlement logic.
  This leaves lifecycle interpretation split between dispatcher and contract.
- `scripts/herdr_parallel_dispatch.py:_admit_lanes()` places dependency,
  resource, and capacity failures in both `rejected` and a more specific list.
  `run_parallel()` therefore needs `emitted_admission_ids` to suppress duplicate
  events. This is compatibility behavior, not a disjoint canonical model.
- `scripts/herdr_parallel_dispatch.py` imports launcher-private `_sha256_text`
  and uses a dynamic file-import fallback. The launcher and worker use similar
  fallback loading for shared contracts.
- `scripts/deploy_agent_runtime.py:_apply_pairs_staged()` copies and swaps the
  whole target root. `run()` plans and applies shared bundles and platform
  targets one at a time, and calls the swap even when no pairs changed.
- The shared manifest describes `scripts/herdr_parallel_dispatch.py` as a
  canonical runtime surface but does not distribute it. Directory entries are
  already supported by build and deployment code, so one package entry is safe.
- The orphaned dispatcher helpers and private aliases are referenced by tests,
  but production-only search finds no callers. Delete only after migration and
  an explicit compatibility audit.

Corrections to pasted verdicts:

- `parse_result_receipt()` at `3b64fb1` already returns parsed capability
  evidence. Receipt capability loss is historical residual, not new scope.
- `run_parallel()` emits each completed future inside `as_completed()` and the
  CLI uses `flush=True`; fast-lane streaming is already fixed and is not planned.
- The reported `758 passed, 1 skipped` count is not independently reproducible
  from an archive in this environment because project-root tests require a Git
  checkout. Direct `validate_repo_contracts.py --repo-root . --fast` passes at
  `3b64fb1`; do not use the reported count as acceptance evidence without CI
  output from that commit.

## Goal

Make capability verification, lifecycle settlement, lane preparation, and
admission classification single-owner semantics while preserving current
DeepAgents behavior, receipt formats, security boundaries, and bounded
foreground execution.

## Implementation Outcomes

### Capability and lifecycle facts stay independent

Pure capability normalization, requested/effective representation, digest, and
evidence comparison have one owner. Only `dcode-project` checks executable
availability in worker `PATH`. A capability or grant mismatch on a fully
retired attempt reports verification failure while preserving resource
settlement; only uncertain ownership or cleanup blocks reuse. Retired
classification is allowed only after `assignment_id`, `attempt_id`,
`task_sha256`, grant binding, and receipt correlation all match; mismatched
identity remains `RECOVERY_REQUIRED` regardless of cleanup-looking fields.

Evidence ordering is explicit: identity and attempt correlation precede
resource settlement; grant and capability verification follow settlement;
task-result evidence follows verification; CoS alone decides acceptance.

### Runtime entry points use one shared core

Shared attempt/result contracts and new immutable lane/admission types live
under `scripts/project_os_runtime/`. Existing script paths remain temporary
compatibility shims until caller and deployment checks prove removal safe.
Production CLI modules import the shared core, never each other's private
symbols, and work from both source checkout and deployed runtime layout.

### Deployment changes only owned content

Deployment computes every selected target plan before writing. If planning or
ownership checks fail, it writes nothing. Each zero-change plan is skipped;
each owned bundle applies atomically and rolls back locally on failure. If an
earlier bundle already succeeded, deployment reports which bundles were
applied. Unrelated user files survive all paths.

### Admission has one canonical state

Each lane has exactly one `AdmissionResult` state: `ADMITTED`, `DEFERRED`,
`BLOCKED`, or `REJECTED`. Legacy category lists remain derived output only.

## Non-Goals

- No scheduler, daemon, runtime ledger, database, heartbeat, retry service, or
  new durable result protocol.
- No change to `MAX_CONCURRENCY = 2`, foreground coordination, Plan plus Git
  workflow truth, CoS acceptance authority, or approved MCP security rules.
- No Codex/Tura lifecycle parity and no runtime-wide file split beyond the
  smallest shared package needed to remove duplicated semantics.
- No rewrite or deletion of completed plans, generated adapter outputs, or
  user-local runtime state.
- No DeepAgents delegation for implementation. DeepAgents remains system under
  test; direct source and test evidence remain authoritative.

## Execution Approach

- Mode: `inline sequential`
- Coordination: `git-tracked`
- Required skills: `skill-systematic-debugging`, `skill-test-driven-development`, `skill-backend-verification`, `skill-code-standards`, `skill-verification-before-completion`, `skill-plan-document-reviewer`
- Isolation: `fresh worktree` from reviewed base; preserve existing primary-checkout untracked `.playwright-mcp/`, `db/`, and prior plans
- Commit policy: `no commits during execution`
- Preauthorized local actions: edit listed source, test, manifest, workflow, and canonical documentation files; run focused tests and repository validators
- User-approval actions: push, merge, branch/worktree disposition, authentication, shared user-local deployment, destructive cleanup, and edits outside listed targets
- Parallel ownership: `none`; contract, deployment, and adapter imports share semantic boundaries
- Sequential fallback: capability/evidence contract → deployment preflight and ownership → package and lane migration → lifecycle/admission integration → cleanup and structural validation → final proof

## Coordination State

- Coordination owner: `single lead controller`
- Coordination schema: `2`
- Branch: `codex/runtime-semantic-boundary`
- Base commit: `3b64fb1b657c3617631a389d92a7d5d1b69740df`
- Expected workspace: fresh isolated worktree at reviewed base; primary checkout remains untouched
- Next action: none; final verification complete
- Blockers: none

| Task | State | Workspace | Executor | Depends On | Required Proof | Evidence |
| --- | --- | --- | --- | --- | --- | --- |
| Task 1 | `completed` | worktree | `deepagents` | none | focused capability and settlement tests | Herdr Task 1 lane PASS; independent contract/debug lane PASS; independent dispatcher/debug lane PASS; fresh combined suite `411 passed`; `git diff --check` passed |
| Task 2 | `completed` | worktree | `deepagents` | Task 1 | deployment transaction tests | Herdr Task 2 lane PASS; fresh deployment suite `28 passed`; `py_compile` and `git diff --check` passed |
| Task 3 | `completed` | worktree | `deepagents` | Task 2 | package import, manifest, and deployed-layout smoke tests | Herdr recovery lane exited without marker; controller audit fixed shared-path manifest placement and stale stdlib assertion; focused suite `465 passed`; starter-kit exclusion, compile, JSON, and diff checks passed |
| Task 4 | `completed` | worktree | `deepagents` | Task 3 | lifecycle and admission regression tests | Two independent Herdr DeepAgents lanes completed; controller reconciled receipt-shape fixture drift and integrated canonical admission/settlement; focused runtime suite `118 passed`; broader runtime matrix `471 passed`; compile and `git diff --check` passed |
| Task 5 | `completed` | worktree | `deepagents` | Task 4 | orphan search and compatibility tests | Herdr Task 5 lane PASS; no production callers or documented compatibility consumers; focused runtime suite `420 passed`; compile and `git diff --check` passed |
| Task 6 | `completed` | worktree | `deepagents` | Task 5 | AST boundary validator, CI, and full verification | Herdr Task 6 retry PASS with completion marker; focused suite `439 passed`; independent runtime matrix `492 passed`; full validator `77 passed`; repo config, starter-kit exclusion, compile, sync, and diff checks passed |

## Task Breakdown

### Task 1: Centralize capability and evidence decisions

**Purpose:** Remove controller-side environment ownership and separate resource truth from capability verification.

**Task Function:** Change shared semantic contract and migrate direct callers without changing receipt schema.

**Template Profile:**
- Controller-selected: `normal`
- Selection basis: contract semantics, backend failure paths, and compatibility risk

**Specification Coverage:** Capability ownership, independent verification/resource facts, and preserved receipt correlation.

**Required Skills:** `skill-test-driven-development`, `skill-backend-verification`, `skill-code-standards`

**Files And Symbols:**
- Inspect: `scripts/herdr_attempt_contract.py:normalize_runtime_grant`, `terminal_settlement_proven`, `attempt_decision`
- Inspect: `scripts/dcode_project.py:_extract_local_capabilities`, `_resolve_worker_shell_capabilities`
- Modify: `scripts/herdr_attempt_contract.py` capability normalization/digest/evidence decisions
- Modify: `scripts/herdr_main_launcher.py:_normalize_local_capabilities`, `_verify_local_capabilities`, receipt projection
- Modify: `scripts/herdr_parallel_dispatch.py:_bind_requested_grant`, `_normalize_local_capabilities`, `_verify_local_capabilities`, `run_lane`
- Verify: `tests/test_dcode_project.py`, `tests/test_herdr_main_launcher.py`, `tests/test_herdr_parallel_dispatch.py`, `tests/test_herdr_attempt_contract.py`

**Dependencies:** Reviewed base `3b64fb1`; existing result receipt parser already preserves capability evidence.

**Authority:**
- Preauthorized local actions: edit listed contract, launcher, dispatcher, worker, and focused test files; run focused pytest commands
- Stop for: receipt schema changes, new runtime service, external environment writes, or behavior requiring parent-spec amendment

**Steps:**
- [x] Step 1: Add one pure normalization/digest/evidence comparison path; preserve original input only for diagnostics and canonicalize semantic identifiers for comparison.
- [x] Step 2: Remove `shutil.which()` capability admission checks from launcher and dispatcher; pass requested selectors through unchanged after pure validation.
- [x] Step 3: Keep worker `PATH` validation in `dcode-project`; emit explicit capability verification failure evidence without converting proven cleanup into occupied capacity, but require matching `assignment_id`, `attempt_id`, `task_sha256`, and receipt correlation before treating resources as retired.
- [x] Step 4: Make settlement, capability verification, and task-result acceptance independently observable in returned assignment evidence.

Settlement reuse must follow this order: identity and attempt correlation →
resource settlement → grant/capability verification → task result → CoS
acceptance. Add paired cases for same-attempt cleanup with capability mismatch
(`retired` plus verification failure) and stale/wrong-attempt cleanup-looking
evidence (`RECOVERY_REQUIRED`, capacity not released).

**Verification:**
- [x] `py -3 -m pytest -q tests/test_herdr_attempt_contract.py tests/test_dcode_project.py tests/test_herdr_main_launcher.py tests/test_herdr_parallel_dispatch.py`
- Expected: controller and worker capability tests pass; correlated retired-plus-verification-failed evidence remains reusable only when ownership and cleanup are proven; stale or contradictory identity never releases capacity.

**Exit Criteria:** No production launcher/dispatcher capability availability check remains; one shared pure evidence decision path owns semantic comparison.

### Task 2: Harden deployment transaction boundaries

**Purpose:** Prevent no-op swaps and partial cross-target deployment while preserving unrelated user files.

**Task Function:** Strengthen existing planner/stager; do not add deployment service or database.

**Template Profile:**
- Controller-selected: `high`
- Selection basis: destructive-boundary risk, rollback behavior, and testability

**Specification Coverage:** Project OS owns only managed assets; deployment is preflighted, idempotent, and rollback-safe.

**Required Skills:** `skill-backend-verification`, `skill-test-driven-development`, `skill-code-standards`

**Files And Symbols:**
- Inspect: `scripts/deploy_agent_runtime.py:_apply_pairs_staged`, `_shared_asset_plan`, `_plan_deploy`, `run`
- Modify: `scripts/deploy_agent_runtime.py` target planning, no-op guard, and managed-root staging
- Verify: `tests/test_deploy_agent_runtime.py`

**Dependencies:** Task 1 complete; current marker ownership and directory manifest support remain canonical.

**Authority:**
- Preauthorized local actions: edit deployment code and deployment tests; use temporary test directories only
- Stop for: writes to real user-local runtime targets, ownership adoption, destructive cleanup, or target-root contract changes outside tests

**Steps:**
- [x] Step 1: Build plans and collect issues for shared docs, shared scripts, shared skills, and selected platforms before applying any pair.
- [x] Step 2: Return without staging when every plan has zero changes; skip each individual zero-change plan during mixed deployments.
- [x] Step 3: Permit whole-root replacement only when that exact root is Project OS marker-owned; otherwise mutate exact managed files or marker-owned subtrees.
- [x] Step 4: Apply each owned bundle atomically and roll back that bundle on failure; report bundles already applied if a later bundle fails. Do not add global rollback or a transaction journal.
- [x] Step 5: Keep unowned-collision and `--force` rules unchanged; add tests for preflight failure, no-op, unrelated sentinel preservation, local rollback, and applied-bundle reporting.

**Verification:**
- [x] `py -3 -m pytest -q tests/test_deploy_agent_runtime.py`
- Expected: no-op performs no replacement; any planning/ownership failure causes no write; managed files update and stale owned files remove without touching unrelated files; later apply failure reports earlier applied bundles and rolls back only failing bundle.

**Exit Criteria:** Deployment has one preflight barrier, true no-op behavior, and ownership-bounded staged writes under test.

### Task 3: Introduce shared runtime package and immutable lane preparation

**Purpose:** Remove dynamic production imports and normalize raw lane input exactly once.

**Task Function:** Extract existing contracts with compatibility shims, then add the smallest immutable lane boundary.

**Template Profile:**
- Controller-selected: `high`
- Selection basis: import/deployment migration, compatibility surface, and cross-platform runtime risk

**Required Skills:** `skill-test-driven-development`, `skill-backend-verification`, `skill-code-standards`

**Files And Symbols:**
- Create: `scripts/project_os_runtime/__init__.py`, `scripts/project_os_runtime/capabilities.py`, `scripts/project_os_runtime/attempt.py`, `scripts/project_os_runtime/results.py`, `scripts/project_os_runtime/lane.py`
- Modify: `scripts/herdr_attempt_contract.py`, `scripts/deepagents_result_contract.py` compatibility shims
- Modify: `scripts/herdr_main_launcher.py`, `scripts/herdr_parallel_dispatch.py`, `scripts/dcode_project.py` production imports
- Modify: `repo_config/starter-kit-manifest.json` shared script directory and dispatcher entry
- Verify: `tests/test_starter_kit_generation.py`, `tests/test_project_os_runtime.py`, focused runtime tests, temporary shared-runtime deployment smoke

**Specification Coverage:** One internal shared core, one-way CLI dependencies, canonical `PreparedLane`, and global dispatcher deployment.

**Dependencies:** Tasks 1–2 complete; package directory must be deployable through existing recursive `sharedPaths` handling.

**Authority:**
- Preauthorized local actions: add package files, update compatibility imports, manifest, and focused tests; run source/deployed-layout smoke checks
- Stop for: PyPI packaging, installer framework, dependency addition, or removal of compatibility shims before caller audit

**Steps:**
- [x] Step 1: Move existing attempt and result contract implementations into package modules without semantic edits; reduce `herdr_attempt_contract.py` and `deepagents_result_contract.py` to explicit public re-exports only.
- [x] Step 2: Put pure capability semantics in `project_os_runtime/capabilities.py`: identifier/request normalization, default expansion, digest, and worker-evidence comparison. It must not inspect `PATH`, call `shutil.which()`, invoke subprocesses, or execute workers.
- [x] Step 3: Add frozen `PreparedLane` and pure `prepare_lane(raw_descriptor)` containing assignment identity, task hash, grant binding, capabilities, worktree/target, and remaining authority.
- [x] Step 4: Replace dispatcher-to-launcher private `_sha256_text` import and production `spec_from_file_location()` fallbacks with package/public imports; retain test isolation loaders where needed.
- [x] Step 5: Add `scripts/project_os_runtime` and `scripts/herdr_parallel_dispatch.py` to shared runtime deployment. Prove all three entry paths from outside the repository and without repository `PYTHONPATH`.

**Verification:**
- [x] `py -3 -m pytest -q tests/test_starter_kit_generation.py tests/test_deepagents_result_contract.py tests/test_herdr_attempt_contract.py tests/test_herdr_main_launcher.py tests/test_herdr_parallel_dispatch.py`
- [x] `py -3 -m pytest -q tests/test_project_os_runtime.py tests/test_deploy_agent_runtime.py`
- [x] `py -3 scripts/build_starter_kit.py --repo-root . --output-root generated_exports`
- Expected: temporary shared deployment contains `project_os_runtime`, `herdr_main_launcher.py`, `herdr_parallel_dispatch.py`, and `dcode_project.py`; generated starter kit does not contain shared runtime files; compatibility imports reference equivalent implementations; no production CLI imports another CLI's private symbol.

**Exit Criteria:** Raw descriptor normalization has one owner; package and dispatcher are distributed together; deployed CLI smoke passes outside source repository.

### Task 4: Replace overlapping admission and local settlement reconstruction

**Purpose:** Give each lane one admission result and make dispatcher consume shared lifecycle evidence directly.

**Task Function:** Change internal representations while deriving legacy output only at compatibility edges.

**Template Profile:**
- Controller-selected: `high`
- Selection basis: state-machine correctness, compatibility migration, and sibling-failure preservation

**Required Skills:** `skill-test-driven-development`, `skill-backend-verification`, `skill-code-standards`

**Files And Symbols:**
- Create: `scripts/project_os_runtime/admission.py`
- Modify: `scripts/project_os_runtime/attempt.py` public settlement/attempt decision functions
- Verify: `scripts/herdr_attempt_contract.py`, `scripts/deepagents_result_contract.py` remain re-export shims only
- Modify: `scripts/project_os_runtime/lane.py`, `scripts/herdr_parallel_dispatch.py:_admit_lanes`, `run_lane`, `run_parallel`
- Verify: `tests/test_herdr_attempt_contract.py`, `tests/test_herdr_parallel_dispatch.py`

**Specification Coverage:** Independent lifecycle/resource/task evidence and disjoint `ADMITTED | DEFERRED | BLOCKED | REJECTED` classification.

**Dependencies:** Task 3 complete; existing external category output remains supported during migration.

**Authority:**
- Preauthorized local actions: edit admission/attempt contracts, dispatcher, package, and focused tests; run deterministic fake-process tests
- Stop for: changing CLI event names without compatibility derivation, acceptance ownership changes, or new retry/ledger behavior

**Steps:**
- [x] Step 1: Add `AdmissionResult(lane_id, state, reason)` and batch conversion helpers; ensure one lane cannot occupy multiple canonical states.
- [x] Step 2: Derive legacy `admitted`, `deferred`, `blocked`, and `rejected` lists only when constructing external result payloads; remove event deduplication state.
- [x] Step 3: Add public settlement decision in `project_os_runtime/attempt.py` consuming `lifecycle_receipt`; remove dispatcher synthesis of `worker_state` from presentation `execution` fields. Legacy contract modules only re-export this implementation.
- [x] Step 4: Keep task-result acceptance and continuation separate from resource settlement; test grant mismatch, capability failure, cleanup uncertainty, and acceptance pending.

**Verification:**
- [x] `py -3 -m pytest -q tests/test_herdr_attempt_contract.py tests/test_herdr_parallel_dispatch.py`
- Expected: each lane produces one admission event; settled resources remain retired when task acceptance or capability verification is unresolved. Confirmed by `118 passed` focused and `471 passed` broader runtime matrix.

**Exit Criteria:** Dispatcher no longer owns duplicate lifecycle/admission semantics, and canonical admission states are mutually exclusive.

### Task 5: Remove orphaned compatibility surface

**Purpose:** Delete obsolete helpers only after production callers and compatibility consumers are proven absent.

**Task Function:** Caller audit and minimal deletion.

**Template Profile:**
- Controller-selected: `normal`
- Selection basis: low implementation complexity, high hidden-consumer risk

**Required Skills:** `skill-code-standards`, `skill-test-driven-development`

**Files And Symbols:**
- Inspect: production and test references to `validate_plan_authority`, `validate_git_checkpoint`, `attempt_expired`, `validate_acceptance`, `dispatch_launcher_record`, `validate_local_capabilities`, `_grant_digest`, `_normalize_attempt`, `_resolve_attempt_budget`
- Modify: `scripts/herdr_parallel_dispatch.py`, `scripts/herdr_attempt_contract.py`, compatibility tests
- Verify: all runtime tests and repository-wide search

**Specification Coverage:** Smaller maintenance surface without breaking documented public boundaries.

**Dependencies:** Task 4 complete; package imports and admission compatibility are stable.

**Authority:**
- Preauthorized local actions: remove only caller-free helpers and update tests that exercised obsolete APIs; run repository search and focused tests
- Stop for: any non-test production caller, documented external API dependency, or hidden import discovered by deployed smoke

**Steps:**
- [x] Step 1: Run production-only and full-text caller audit; classify test-only, historical-document, compatibility, and production uses. No production callers found; remaining historical references are plan text and canonical public helpers such as `grant_digest`, `normalize_attempt`, and `resolve_attempt_budget`.
- [x] Step 2: Delete only proven orphaned helpers and private aliases; preserve public compatibility shims still required by deployed consumers.
- [x] Step 3: Replace tests that preserve deleted pseudo-APIs with tests at production boundaries.

**Verification:**
- [x] `rg -n "validate_plan_authority|validate_git_checkpoint|attempt_expired|validate_acceptance|dispatch_launcher_record|validate_local_capabilities|_grant_digest|_normalize_attempt|_resolve_attempt_budget" scripts tests docs` — no obsolete definitions or test references; remaining matches are canonical non-obsolete names and plan/history text.
- [x] `py -3 -m pytest -q tests/test_dcode_project.py tests/test_deepagents_result_contract.py tests/test_herdr_attempt_contract.py tests/test_herdr_main_launcher.py tests/test_herdr_parallel_dispatch.py tests/test_project_os_runtime.py` — `420 passed`.
- [x] `py -3 -m compileall -q scripts` and `git diff --check`.
- Expected: no unintended production caller remains; focused runtime tests pass.

**Exit Criteria:** Compatibility surface contains only documented or deployed consumers; obsolete test-only APIs are gone.

### Task 6: Enforce dependency boundaries structurally and simplify CI

**Purpose:** Make import ownership executable without pretending prose scanning proves architecture.

**Task Function:** Add stdlib AST checks and retain prose checks only for prose contracts.

**Template Profile:**
- Controller-selected: `normal`
- Selection basis: validator correctness, CI scope, and no-dependency constraint

**Required Skills:** `skill-code-standards`, `skill-verification-before-completion`

**Files And Symbols:**
- Modify: `scripts/validate_repo_contracts.py:validate_runtime_boundary_guidance`
- Modify: `tests/test_validate_repo_contracts.py`
- Modify: `.github/workflows/runtime-contracts.yml`
- Modify: `docs/operating_system/runtime/runtime-surfaces.md`
- Verify: `.github/workflows/repo-contracts.yml`, full runtime matrix commands

**Specification Coverage:** Runtime core cannot import subprocess/CLI adapters; adapters cannot import sibling private symbols; platform-independent validation runs once.

**Dependencies:** Tasks 1–5 complete; package layout and compatibility policy settled.

**Authority:**
- Preauthorized local actions: edit validator, validator tests, workflow, and canonical runtime documentation; run local validators and test commands
- Stop for: replacing actual documentation contracts with AST checks, adding dependencies, or changing unrelated CI jobs

**Steps:**
- [x] Step 1: Parse production imports with stdlib `ast` and reject forbidden dependency edges by module path, not literal private symbol names.
- [x] Step 2: Keep targeted SSOT/prose checks for ownership statements and required documentation markers.
- [x] Step 3: Move platform-independent repository validation and starter-generation checks to the existing single Linux repository-contract job; leave runtime, deployment, and deployed-import tests in Linux/Windows matrix.
- [x] Step 4: Update runtime surfaces to name package ownership, dcode worker validation, Herdr transport/observation, and globally deployed dispatcher.

**Verification:**
- [x] `py -3 -m pytest -q tests/test_validate_repo_contracts.py tests/test_starter_kit_generation.py`
- [x] `py -3 scripts/validate_repo_contracts.py --repo-root . --fast`
- [x] `py -3 scripts/validate_repo_config.py --repo-root .`
- [x] Full runtime matrix: `492 passed`.
- [x] Full repository validator: `77 passed`.
- [x] Starter-kit build and shared-runtime exclusion smoke passed.
- [x] `py -3 -m compileall -q scripts`, adapter sync check, and `git diff --check` passed.
- Expected: structural boundary regressions fail with actionable paths; current repository contracts pass; CI runs repository/starter validation once and cross-platform runtime/deployment/import proof in the matrix.

**Exit Criteria:** Architecture checks inspect dependency structure, documentation checks remain targeted, and workflow ownership is non-duplicated.

## Verification

- [x] `py -3 -m pytest -q tests/test_dcode_project.py tests/test_deepagents_result_contract.py tests/test_herdr_attempt_contract.py tests/test_herdr_main_launcher.py tests/test_herdr_parallel_dispatch.py tests/test_deploy_agent_runtime.py tests/test_validate_repo_contracts.py tests/test_starter_kit_generation.py tests/test_project_os_runtime.py` — `492 passed`.
- [x] `py -3 scripts/validate_repo_contracts.py --repo-root .` — `77 passed` and contract validation passed.
- [x] `py -3 scripts/validate_repo_config.py --repo-root .` — passed.
- [x] `py -3 scripts/build_starter_kit.py --repo-root . --output-root <temp>` — built; shared runtime exclusion passed.
- [x] `py -3 scripts/sync_agent_adapters.py --all-platforms --check` — passed.
- [x] Deployed-layout smoke and prior source/deployed import proof — passed in Tasks 3 and 4.

## Completion Criteria

The plan is ready for completion verification when:

1. Capability availability has one worker-boundary owner and verification/resource facts remain separate.
2. Deployment preflight, no-op, ownership, and rollback tests pass without touching unrelated files.
3. Shared package and immutable `PreparedLane` work from source and deployed layouts; dispatcher deployment contradiction is resolved; generated starter kit remains free of shared runtime files.
4. Lifecycle settlement consumes receipt evidence directly and admission states are mutually exclusive internally.
5. Orphaned helpers are removed only after caller audit, with no unrecorded compatibility break.
6. Structural import checks, targeted prose checks, docs, CI, manifest, and generated starter output agree.
7. Final verification runs fresh on the reviewed Git base and records any environment-sensitive deviations.

Plan completed after behavior decisions, exact execution base, and fresh final
verification returned verified.
