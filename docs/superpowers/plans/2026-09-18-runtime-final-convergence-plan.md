---
layer: change
artifact_type: plan
status: proposed
template_id: implementation-plan
contract_version: "1"
name: runtime-final-convergence
parent_spec: docs/superpowers/specs/2026-09-14-parallel-deepagents-dispatch-spec.md
targets:
  - scripts/project_os_runtime/attempt.py
  - scripts/project_os_runtime/results.py
  - scripts/project_os_runtime/lane.py
  - scripts/project_os_runtime/admission.py
  - scripts/project_os_runtime/capabilities.py
  - scripts/herdr_parallel_dispatch.py
  - scripts/herdr_main_launcher.py
  - scripts/dcode_project.py
  - scripts/deepagents_result_contract.py
  - scripts/herdr_attempt_contract.py
  - scripts/deploy_agent_runtime.py
  - scripts/validate_repo_contracts.py
  - docs/operating_system/runtime/runtime-surfaces.md
  - docs/superpowers/specs/2026-09-14-parallel-deepagents-dispatch-spec.md
  - .github/workflows/runtime-contracts.yml
  - .github/workflows/repo-contracts.yml
  - tests/test_project_os_runtime.py
  - tests/test_deepagents_result_contract.py
  - tests/test_herdr_attempt_contract.py
  - tests/test_herdr_parallel_dispatch.py
  - tests/test_herdr_main_launcher.py
  - tests/test_dcode_project.py
  - tests/test_deploy_agent_runtime.py
  - tests/test_validate_repo_contracts.py
  - tests/test_starter_kit_generation.py
---

# Runtime Final Convergence

## Review Basis

Reviewed pasted verdict against exact `origin/main` at
`04d4fb6e00108e916fde449b39d333af9e80de13`.

Native source and test inspection verified the material findings. DeepAgents
delegation is not required for this review: the repository source, existing
tests, workflow definitions, and exact Git ref provide direct evidence. Use
DeepAgents only for an independent implementation audit after Task 1 if the
controller finds ambiguity in receipt-shape compatibility.

## Findings

### P0 — Settlement predicates disagree

Confirmed. `terminal_settlement_proven()` requires confirmed receipt state and
explicit `recovery_required is False`; `settlement_decision()` can settle a
nested receipt when those fields are absent. Production callers therefore have
two semantic predicates for resource retirement.

Preserve:

- correlation before settlement
- worker terminal states: `exited`, `failed`, `start_failed`
- cleanup state `removed`
- descendant states `terminated` or `not_started`
- capability or task-result failure does not reopen proven resource ownership

Smallest correction: one strict internal settlement decision, with compatibility
normalization for existing flat and nested receipt shapes. Missing state,
recovery, cleanup, descendant, or worker evidence remains unsettled.

### P1 — `PreparedLane` is not the production ingress boundary

Confirmed. `prepare_lane()` exists, but `_admit_lanes()` still owns required
field checks, grant binding, capability normalization, assignment derivation,
and mutable-dictionary mutation. Production launch paths can rebind the same
facts.

Smallest correction: prepare each raw descriptor once, carry an immutable
normalized lane through admission and launch, and retain a legacy projection
only at serialization or compatibility edges.

### P1 — Admission results lose canonical reasons too early

Confirmed. `_admit_lanes()` creates `AdmissionResult` values, then immediately
projects to legacy lists. `run_parallel()` also accepts already-partitioned
legacy lists. `BLOCKED` and `DEFERRED` reasons are not preserved in the legacy
projection, and duplicate classification is suppressed procedurally instead of
being impossible by contract.

Smallest correction: keep one canonical result per lane through orchestration;
project to legacy lists only at the output boundary.

### P1 — Deployment backups violate target ownership

Confirmed. `--backup` writes to `target_root/.backups/<timestamp>`, while
`_apply_pairs_staged()` can copy the entire target root even for pair-scoped
changes. One runtime stale scanner ignores `.backups`, but shared-asset scans
do not provide the same ownership boundary. Mixed or unowned roots can also
capture unrelated files.

Smallest correction: write backups outside managed targets; for mixed/unowned
roots snapshot only existing destinations in `pairs`; retain whole-root backup
only for marker-owned replace-root targets.

### P2 — Dependency validation is structural but incomplete

Confirmed. AST import checks exist, but import names are compared without
normalizing absolute, package, and relative spellings. Pure runtime modules do
not all forbid process dependencies. Preserve targeted prose checks for
ownership documentation; add normalized import-edge checks for code ownership.

### P2 — CI duplicates generic validation and omits new runtime tests

Confirmed. `runtime-contracts.yml` runs repository validation on Ubuntu while
`repo-contracts.yml` already owns repository validation. The runtime matrix does
not include `tests/test_project_os_runtime.py` or `tests/test_deploy_agent_runtime.py`.

Smallest correction: keep repository/starter validation in one Linux workflow;
use the OS matrix for runtime, deployment, and deployed-layout tests.

### P3 — Compatibility shims remain

Confirmed but not yet actionable. `scripts/herdr_attempt_contract.py` and
`scripts/deepagents_result_contract.py` are re-export shims and remain in the
starter manifest and tests. Do not remove them in this convergence pass unless
the compatibility audit proves zero production or external consumers.

## Goal

Make one normalized lane, one explicit lifecycle-evidence path, one settlement
definition, one admission state, shared capability semantics, and no backup
artifact inside managed runtime content while preserving receipt formats,
bounded concurrency, resource ownership, compatibility projections, worker PATH
validation, rollback behavior, and generated-surface governance.

## Non-goals

- no new scheduler, service, state store, result protocol, or global rollback journal
- no removal of compatibility shims without an explicit consumer audit
- no change to Herdr transport ownership or CoS acceptance authority
- no direct edits to generated adapter or Starter Kit output
- no weakening of validators to preserve obsolete names

## Execution Approach

- Mode: inline sequential
- Coordination: git-tracked
- Base: exact `origin/main` ref `04d4fb6e00108e916fde449b39d333af9e80de13`
- Required skills: `skill-systematic-debugging`, `skill-test-driven-development`,
  `skill-backend-verification`, `skill-code-standards`,
  `skill-verification-before-completion`
- Isolation: use a fresh worktree from the exact base before implementation
- Commit policy: no commits until task-local proof is accepted; no merge or push
  granted by this plan

## Coordination State

- Coordination owner: `single lead controller`
- Coordination schema: `2`
- Branch: `codex/runtime-final-convergence`
- Base commit: `04d4fb6e00108e916fde449b39d333af9e80de13`
- Expected workspace: `pending fresh isolated worktree from 04d4fb6`
- Next action: validate plan, then create isolated implementation worktree
- Blockers: `none`

| Task | State | Workspace | Executor | Depends On | Required Proof | Evidence |
| --- | --- | --- | --- | --- | --- | --- |
| Task 1 | pending | fresh worktree | codex | none | focused tests and backend proof | plan evidence |
| Task 2 | pending | fresh worktree | codex | Task 1 | focused tests and invariant audit | plan evidence |
| Task 3 | pending | fresh worktree | codex | Task 1 | backup and rollback tests | plan evidence |
| Task 4 | pending | fresh worktree | codex | Task 2 | validator tests | plan evidence |
| Task 5 | pending | fresh worktree | codex | Tasks 2–4 | workflow and matrix audit | plan evidence |
| Task 6 | pending | fresh worktree | codex | Tasks 1–5 | caller inventory | plan evidence |

## Task Breakdown

### Task 1: Unify lifecycle settlement

**Purpose:** Remove false retirement caused by divergent settlement predicates.

**Task Function:** Shared contract correction with regression proof.

**Template Profile:**
- Controller-selected: `high`
- Selection basis: high reasoning depth for shared lifecycle and ownership semantics.

**Required Skills:** `skill-systematic-debugging`, `skill-test-driven-development`, `skill-backend-verification`

**Files And Symbols:**
- Modify: `scripts/project_os_runtime/attempt.py:terminal_settlement_proven`,
  `settlement_decision`, `derive_lifecycle_state`, `attempt_decision`
- Modify: `scripts/project_os_runtime/results.py:_validate_payload`,
  `parse_result_receipt`
- Modify: `scripts/dcode_project.py:_reconcile_attempt_unlocked` and worker
  finalization evidence writer
- Verify: `scripts/deepagents_result_contract.py`,
  `scripts/herdr_attempt_contract.py`, `scripts/herdr_parallel_dispatch.py`,
  `scripts/herdr_main_launcher.py`
- Test: `tests/test_project_os_runtime.py`,
  `tests/test_deepagents_result_contract.py`,
  `tests/test_herdr_attempt_contract.py`,
  `tests/test_herdr_parallel_dispatch.py`, `tests/test_herdr_main_launcher.py`

**Dependencies:** Exact base selected; no other task required.

**Authority:**
- Preauthorized local actions: edit shared settlement code and focused tests; run declared checks.
- Stop for: new wire receipt fields, new lifecycle states, or changed ownership semantics.

**Steps:**
1. Model the pipeline explicitly: raw worker receipt → strict validation →
   normalized lifecycle evidence → correlation → `settlement_decision()`.
2. Require wire-level `recovery_required`; preserve raw receipt format and do
   not add normalized `state` to the wire payload.
3. Make parser, reconciliation, and worker finalization produce the same
   normalized evidence and call one strict decision path.
4. Keep legacy active guards fail-closed: correlated valid raw receipt may
   settle them; incomplete persisted evidence remains reconciliation-required.
   Preserve already-settled guards.
5. Make public compatibility helpers delegate to that path; do not create a
   second `SettlementDecision` class unless multiple real callers require it.
6. Keep correlation before settlement and preserve resource settlement when
   capability or task acceptance fails after retirement is proven.

**Verification:**
- `py -3 -m pytest -q tests/test_project_os_runtime.py tests/test_herdr_parallel_dispatch.py tests/test_herdr_main_launcher.py`
- Assert missing required evidence never returns `resource_settled=True`.
- Assert mismatched identity cannot consume settlement evidence.
- Assert failed capability/task acceptance leaves proven cleanup settled.

**Exit Criteria:** Every production caller reaches one strict settlement
definition and focused tests cover positive, malformed, stale, and uncertain
receipts.

### Task 2: Promote `PreparedLane` and canonical admission

**Purpose:** Remove mutable shadow normalization and keep one admission state per lane.

**Task Function:** Production boundary migration.

**Template Profile:**
- Controller-selected: `high`
- Selection basis: high reasoning depth for immutable ingress and admission invariants.

**Required Skills:** `skill-code-standards`, `skill-test-driven-development`, `skill-backend-verification`

**Files And Symbols:**
- Modify: `scripts/project_os_runtime/lane.py:PreparedLane, prepare_lane`
- Modify: `scripts/project_os_runtime/admission.py`
- Modify or verify: `scripts/project_os_runtime/capabilities.py`
- Modify: `scripts/herdr_parallel_dispatch.py:_admit_lanes, load_lane_descriptors,
  load_lane_descriptors_from_items, run_parallel, run_lane, _launcher_command`
- Verify: `scripts/project_os_runtime/capabilities.py`,
  `scripts/project_os_runtime/attempt.py`
- Test: `tests/test_project_os_runtime.py`,
  `tests/test_herdr_parallel_dispatch.py`, `tests/test_dcode_project.py`

**Dependencies:** Task 1 complete.

**Authority:**
- Preauthorized local actions: modify dispatcher/core boundary and focused tests; run declared checks.
- Stop for: legacy callers requiring undocumented mutable-dictionary mutation.

**Steps:**
1. Preflight raw identity before building `lanes_by_id`; reject duplicate IDs
   canonically and use input-index diagnostics for missing or unusable IDs.
2. Extend `PreparedLane` with every post-ingress fact: task text,
   repository/plan identity, executor/profile/session/pane, expected base,
   worktree, dependency state, write/resource sets, fixed contracts,
   authority, runtime grant, capabilities, name/codex home, prior-attempt
   fields, target, and remaining authority.
3. Represent preparation failures as `REJECTED(reason)` with no prepared lane
   and no launch attempt.
4. Freeze nested collections and mappings at preparation; compute assignment,
   task hash, grant digest, and capability digest once. `_launcher_command()`
   must not need the raw descriptor.
5. Move request normalization, git/py defaults, case normalization, digest
   calculation, and evidence comparison to `capabilities.py`; leave only
   worker-local PATH/`shutil.which` availability in `dcode_project.py`.
6. Add a canonical admission batch containing prepared lanes plus exactly one
   `AdmissionResult` per lane. Keep `legacy_admission_lists()` only as an
   output projection.
7. Convert legacy partitioned input once at ingress and reject contradictory
   classifications instead of suppressing duplicate events later.
8. Delete dispatcher copies of required-field, grant, capability, comparison,
   assignment, and task-hash normalization after all callers use core semantics.

**Verification:**
- `py -3 -m pytest -q tests/test_project_os_runtime.py tests/test_herdr_parallel_dispatch.py tests/test_dcode_project.py`
- Assert one admission event and one result per lane, including blocked,
  deferred, rejected, duplicate, and legacy-input cases.
- Assert launch command receives immutable prepared facts and cannot rebind
  grant or capability semantics.
- Assert `Node`/`node`, `[]`→`git,py`, malformed evidence, contradictory
  evidence, unavailable executable, and post-retirement capability failure.
- Assert post-retirement capability failure leaves resources retired while
  verification is failed and acceptance is unavailable or unverified.
- Search production code for removed private normalization helpers.

**Exit Criteria:** Dispatcher production flow is raw descriptor → `PreparedLane`
→ canonical admission → launch; legacy lists exist only at serialization edges.

### Task 3: Move deployment backups outside targets

**Purpose:** Prevent recovery artifacts and unrelated files from entering managed roots.

**Task Function:** Deployment safety correction.

**Template Profile:**
- Controller-selected: `high`
- Selection basis: high reasoning depth for backup ownership and rollback safety.

**Required Skills:** `skill-systematic-debugging`, `skill-test-driven-development`, `skill-backend-verification`

**Files And Symbols:**
- Modify: `scripts/deploy_agent_runtime.py:_apply_pairs_staged`, `run`,
  backup-root calculation, shared-asset planning
- Test: `tests/test_deploy_agent_runtime.py`

**Dependencies:** Task 1 complete; execute sequentially before Task 4.

**Authority:**
- Preauthorized local actions: change backup placement and snapshot scope; update focused tests.
- Stop for: global transaction journals, unrelated deployment behavior, or destructive cleanup of pre-existing backup directories.

**Steps:**
1. Choose one Project OS-owned backup root outside every managed target,
   derived from the deployment owner and target identity.
2. Enforce `backup_root != target_root` and ensure `backup_root` is not below
   `target_root`.
3. For `replace_root=False`, snapshot only existing destination paths in
   `pairs`, preserving relative layout and rollback data.
4. For marker-owned `replace_root=True` targets, retain whole-root backup only
   when the target is fully owned; still write it outside the target.
5. Keep existing preflight, no-op, per-bundle atomic apply, local rollback, and
   applied-bundle reporting behavior.
6. Exclude legacy `target_root/.backups/**` from stale-file deletion during
   migration. Do not migrate, adopt, remove, or reinterpret existing user data.

**Verification:**
- `py -3 -m pytest -q tests/test_deploy_agent_runtime.py`
- Backup path is outside target root.
- Mixed/unowned roots back up only affected existing destinations.
- Rollback restores changed files and preserves unrelated sentinels.
- A pre-existing legacy `.backups` entry survives subsequent deploy.
- No-op deploy creates no staging, swap, or backup artifacts.

**Exit Criteria:** New backups cannot be discovered as managed target content,
and rollback remains proven for partial failure.

### Task 4: Strengthen dependency-boundary validation

**Purpose:** Make ownership rules resilient to import spelling variants and
prevent pure core modules from gaining process dependencies.

**Task Function:** Structural validator extension.

**Template Profile:**
- Controller-selected: `high`
- Selection basis: high reasoning depth for normalized AST ownership rules.

**Required Skills:** `skill-code-standards`, `skill-test-driven-development`

**Files And Symbols:**
- Modify: `scripts/validate_repo_contracts.py:_imported_module_names`,
  `validate_runtime_dependency_boundaries`
- Reconcile: `docs/operating_system/runtime/runtime-surfaces.md`,
  `docs/superpowers/specs/2026-09-14-parallel-deepagents-dispatch-spec.md`
- Test: `tests/test_validate_repo_contracts.py`

**Dependencies:** Task 2 package boundaries settled.

**Authority:**
- Preauthorized local actions: use stdlib `ast` only; update validator and focused tests.
- Stop for: adding a dependency graph service or changing unrelated repository policy.

**Steps:**
1. Normalize `import`, `from scripts import`, and relative imports to canonical
   repository module names.
2. Enforce adapter/core ownership edges and forbid `subprocess`/`shutil` in
   `capabilities.py`, `attempt.py`, `lane.py`, and `admission.py`.
3. Keep `results.py` as the controlled filesystem/publication exception.
4. Retain targeted prose checks for runtime ownership documentation; remove
   only exact private-symbol checks replaced by structural assertions.
5. Update canonical ownership docs and parent spec so `project_os_runtime`
   owns preparation, admission, evidence, and settlement; dispatcher owns
   scheduling/invocation/delivery; launcher owns Herdr transport/observation;
   `dcode-project` owns worker execution, PATH availability, descendants,
   cleanup, and receipt publication; shims only forward.

**Verification:**
- `py -3 -m pytest -q tests/test_validate_repo_contracts.py`
- Fixtures cover absolute, package, relative, and forbidden stdlib imports.
- `py -3 scripts/validate_repo_contracts.py --repo-root . --fast`

**Exit Criteria:** Equivalent import spellings produce identical validation
results and forbidden ownership edges fail with actionable paths.

### Task 5: Reassign CI responsibility

**Purpose:** Remove duplicate generic validation and add cross-platform proof
for the new runtime boundary.

**Task Function:** CI contract maintenance.

**Template Profile:**
- Controller-selected: `normal`
- Selection basis: ordinary CI command ownership and matrix maintenance.

**Required Skills:** `skill-verification-before-completion`

**Files And Symbols:**
- Modify: `.github/workflows/runtime-contracts.yml`,
  `.github/workflows/repo-contracts.yml`
- Verify: `scripts/build_starter_kit.py`, `scripts/validate_starter_kit.py`,
  `scripts/sync_agent_adapters.py`
- Test: `tests/test_starter_kit_generation.py`,
  `tests/test_deploy_agent_runtime.py`, runtime/deployment suites

**Dependencies:** Tasks 2–4 complete.

**Authority:**
- Preauthorized local actions: change job ownership and declared test commands; run workflow audits.
- Stop for: required-check names or branch-protection changes not represented in the repo.

**Steps:**
1. Remove duplicated repository-contract execution from the runtime workflow.
2. Keep repository validation, adapter drift, and disposable Starter Kit
   build/validation in the Linux repository workflow.
3. Add `tests/test_project_os_runtime.py`,
   `tests/test_deploy_agent_runtime.py`, and deployed-layout import smoke to
   the Linux/Windows runtime matrix. Place smoke coverage in
   `tests/test_deploy_agent_runtime.py`: deploy approved shared scripts to a
   temporary runtime root, run outside the repository with source-tree
   `PYTHONPATH` cleared, invoke deployed `--help` entry points, and verify
   `project_os_runtime` imports resolve from deployed scripts. No real
   Herdr/DeepAgents execution is needed.
4. Preserve Python version, permissions, fail-fast behavior, and runtime test
   commands unless proof requires a narrow update.

**Verification:**
- Local workflow command audit against current scripts.
- `py -3 -m pytest -q tests/test_starter_kit_generation.py`
- CI Linux and Windows jobs pass with no duplicated repository job and provide
  actual deployed-layout smoke evidence.

**Exit Criteria:** Each contract has one owning workflow and each new runtime
surface has platform-sensitive automated coverage.

### Task 6: Compatibility audit and deferred shim decision

**Purpose:** Avoid removing compatibility surfaces without consumer proof.

**Task Function:** Read-only release gate.

**Template Profile:**
- Controller-selected: `review`
- Selection basis: read-only compatibility consumer audit.

**Required Skills:** `skill-systematic-debugging`, `skill-verification-before-completion`

**Files And Symbols:**
- Verify: `scripts/herdr_attempt_contract.py`,
  `scripts/deepagents_result_contract.py`, `repo_config/starter-kit-manifest.json`
- Verify callers: production code, deployed runtime layout, tests, docs

**Dependencies:** Tasks 1–5 complete.

**Authority:**
- Preauthorized local actions: inspect callers, manifests, generated layouts, tests, and docs.
- Stop for: shim deletion unless zero production/external consumers and compatibility window are explicitly approved.

**Steps:**
1. Search production, generated, deployed, test, and documentation callers.
2. Record whether shims remain required by starter-kit or external compatibility.
3. If removal gate is unmet, preserve shims and record deferral.
4. If gate is met, create a separate scoped change for shim, manifest, docs,
   and tests; do not mix it into correctness changes.

**Verification:**
- Caller inventory has exact paths and consumer class.
- No shim deletion occurs without explicit compatibility disposition.

**Exit Criteria:** Shim state is evidence-backed, not inferred from local grep.

## Implementation Outcomes

1. Raw receipts, normalized lifecycle evidence, persisted guards, and final settlement use one explicit strict path.
2. Admission and launch consume immutable prepared lanes and canonical results.
3. Capability normalization and comparison have one shared owner; worker-local availability remains local.
4. Backup artifacts stay outside managed targets and mixed-root snapshots stay scoped; legacy backups survive migration.
5. Dependency validation normalizes equivalent imports and rejects forbidden runtime edges; canonical docs match ownership.
6. CI assigns each contract to one workflow and covers runtime/deployment/import smoke cross-platform.
7. Compatibility shims remain unless an explicit consumer audit proves safe removal.

## Verification

Run from a fresh worktree at exact base plus accepted changes:

```powershell
py -3 -m pytest -q tests/test_project_os_runtime.py tests/test_deepagents_result_contract.py tests/test_herdr_attempt_contract.py tests/test_herdr_parallel_dispatch.py tests/test_herdr_main_launcher.py tests/test_dcode_project.py tests/test_deploy_agent_runtime.py tests/test_validate_repo_contracts.py tests/test_starter_kit_generation.py
py -3 scripts/validate_repo_contracts.py --repo-root .
py -3 scripts/validate_repo_config.py --repo-root .
py -3 scripts/sync_agent_adapters.py --all-platforms --check
$kitParent = Join-Path $env:TEMP ("project-os-starter-kit-runtime-convergence-" + [guid]::NewGuid().ToString("N"))
py -3 scripts/build_starter_kit.py --output-root $kitParent
py -3 scripts/validate_starter_kit.py --output-root $kitParent
git diff --check
```

Backend proof must include direct settlement, admission, deployment backup,
rollback, and failure-path assertions. Generated surfaces remain derived from
canonical sources. No commit, push, merge, or cleanup is part of this plan.

## Completion Criteria

1. One strict receipt → evidence → settlement path governs all production callers.
2. One immutable prepared lane and one canonical admission result govern
   production dispatch.
3. Shared capability semantics govern normalization and comparison; worker-local
   availability remains local.
4. Backups stay outside managed targets, mixed roots snapshot only affected
   destinations, and legacy backups survive migration.
5. Import-boundary validation catches equivalent syntax variants and canonical
   ownership docs match implementation.
6. CI owns each contract once and runs runtime/deployment/import smoke on Linux
   and Windows.
7. Compatibility shims remain or are removed only by explicit consumer proof.
8. Fresh final verification passes on the reviewed Git base.
