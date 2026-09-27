---
artifact_type: plan
template_id: implementation-plan
contract_version: "1"
status: proposed
layer: change
---

# README Adoption Gateway Plan

## Goal

Turn the top-level README into an adoption-oriented project map and make its
linked setup and usage documents executable for the three supported reader
journeys: understanding the project, evaluating this source repository, and
adopting Project OS in another repository.

Keep this change documentation-only. Do not change runtime behavior, contracts,
validators, generated agent surfaces, or dependency versions.

## Implementation Outcomes

### Executable onboarding

`docs/setup.md` and `docs/usage.md` contain runnable, source-backed onboarding
for repository evaluation and one clearly labeled reference runtime path.
Basic validation does not require benchmark-only dependencies or runtime
credentials.

### Accurate project map

`README.md` distinguishes understand, evaluate, and adopt paths; states Python
3.12 and tested platform boundaries; separates core validation from benchmark
validation; links canonical runtime and adoption documents; and reports
dispatcher failure semantics accurately, including non-null `failure_kind`.

### Adoption handoff

README links the existing adoption guide as the handoff for deploy, build,
validate, and consumer-repository checks already owned by repository scripts and
shared runtime docs. Documentation does not copy private credentials, internal
state, or duplicate runtime policy.

## Execution Approach

- Mode: `inline sequential`
- Coordination: `git-tracked`
- Required skills: `skill-private-public-repo-governance`, `skill-verification-before-completion`
- Isolation: `current workspace`
- Commit policy: `verified per-task checkpoint commits preauthorized`
- Preauthorized local actions: edit the named Markdown files, inspect canonical scripts/docs, run declared read-only help/validation/test commands, create lead checkpoint commits after accepting task proof and updating the ledger, and preserve unrelated untracked files
- User-approval actions: push, merge, publication, destructive cleanup, or changes outside the named documentation files
- Parallel ownership: `none`
- Sequential fallback: complete source-of-truth audit before editing README or linked docs

## Coordination State

- Coordination owner: `single lead controller`
- Coordination schema: `2`
- Branch: `main`
- Base commit: `d7f395e556ffe4c8b9076308f2f91357b0e1f759`
- Expected workspace: `main` clean in tracked files; preserve `.playwright-mcp/`, `db/`, `temp_evidence.json`, and any other unrelated untracked content
- Next action: complete Task 2 README map edits and contract preservation
- Blockers: `none`

| Task | State | Workspace | Executor | Depends On | Required Proof | Evidence |
| --- | --- | --- | --- | --- | --- | --- |
| Task 1 | `completed` | current | `codex` | none | setup/usage docs contain runnable paths and source map | links, diff, and plan validation passed; checkpoint follows |
| Task 2 | `active` | current | `codex` | Task 1 | README map preserves tested contract strings | started after Task 1 checkpoint |
| Task 3 | `pending` | current | `codex` | Task 2 | final docs, contract, test, and diff proof | pending |

## Task Breakdown

### Task 1: Build executable onboarding

**Purpose:**
- Establish documentation truth and replace setup/usage placeholders with runnable onboarding.

**Task Function:**
- Audit canonical command owners, then write setup and usage docs without duplicating runtime policy.

**Template Profile:**
- Controller-selected: `none (lead controller)`
- Selection basis: bounded source audit followed by two related documentation edits.

**Validator Profile:**
- Controller-selected: `none`
- Selection basis: source and command inspection are sufficient before edits.

**Specification Coverage:**
- Verdict requirement to make README an adoption gateway backed by executable setup/usage docs.
- Repository governance requirement to keep canonical runtime behavior in scripts and operating-system docs.

**Required Skills:**
- `skill-private-public-repo-governance`

**Files And Symbols:**
- Modify: `docs/setup.md`, `docs/usage.md`
- Inspect: `README.md`
- Inspect: `docs/setup.md`, `docs/usage.md`, `docs/configuration.md`, `docs/architecture.md`, `docs/pipeline.md`
- Inspect: `docs/operating_system/adoption/project-adoption-migration-guide.md`
- Inspect: `docs/operating_system/runtime/runtime-surfaces.md`
- Inspect: `scripts/herdr_parallel_dispatch.py:run_parallel` and final status calculation around `failure_kind`
- Inspect: `scripts/setup_deepagents_runtime.ps1`, `scripts/build_starter_kit.py`, `scripts/validate_starter_kit.py`, `scripts/deploy_agent_runtime.py`
- Inspect: `.github/workflows/repo-contracts.yml`, `.github/workflows/runtime-contracts.yml`
- Verify: `git status --short --branch`, `git log -1 --oneline`, and script `--help` output

**Dependencies:**
- Current base remains `main` at `d7f395e`.
- Existing untracked files remain preserved and are not documentation candidates.

**Authority:**
- Preauthorized local actions: read the named files, edit `docs/setup.md` and `docs/usage.md`, run `--help` and read-only Git/source commands, create the initial lead checkpoint containing this plan, and record command ownership in this plan
- Stop for: tracked workspace changes, changed base commit, missing canonical command owner, or scope requiring runtime/code edits

**Steps:**
- [x] Step 1: Confirm base commit and tracked workspace state; record preserved untracked paths; create the initial lead checkpoint containing this plan without staging unrelated files.
- [x] Step 2: Map each README claim to a canonical script, workflow, or operating-system document.
- [x] Step 3: Confirm setup prerequisites, core versus benchmark dependencies, tested CI platforms, adoption commands, and dispatcher exit semantics from source.
- [x] Step 4: Replace `docs/setup.md` and `docs/usage.md` placeholders with prerequisites, core/full validation paths, optional runtime setup, one reference usage flow, evidence handling, and links to canonical docs.

**Verification:**
- [x] `git status --short --branch` and targeted `rg`/`--help` inspection.
- Expected: every planned command has an existing owner, setup/usage docs are actionable, and no unrelated tracked change is present.

**Exit Criteria:**
- Source map is complete, setup/usage docs are actionable, and no runtime behavior change is required.

### Task 2: Reframe README as project map

**Purpose:**
- Make README the concise entry point while preserving accurate architecture and governance claims.

**Task Function:**
- Reorganize and tighten public-facing onboarding content around reader intent and canonical links.

**Template Profile:**
- Controller-selected: `none (lead controller)`
- Selection basis: one-file documentation edit with source-backed claims.

**Validator Profile:**
- Controller-selected: `none`
- Selection basis: final repository checks validate the combined documentation surface.

**Specification Coverage:**
- README distinguishes understand, evaluate, and adopt journeys.
- README separates core validation, full tests, and benchmark dependencies.
- README states Python 3.12 and CI-tested Ubuntu/Windows boundaries without claiming macOS support.
- README describes dispatcher nonzero status for rejected/blocked admission, unresolved results, or non-null `failure_kind`.
- README keeps the existing contract phrases required by `tests/test_native_personal_local_workflow.py` and `tests/test_starter_kit_generation.py` while removing duplicated numeric version values.

**Required Skills:**
- `skill-private-public-repo-governance`

**Files And Symbols:**
- Modify: `README.md`
- Reference: `.github/workflows/repo-contracts.yml`, `.github/workflows/runtime-contracts.yml`, `scripts/herdr_parallel_dispatch.py`, `scripts/setup_deepagents_runtime.ps1`, `docs/operating_system/adoption/project-adoption-migration-guide.md`

**Dependencies:**
- Task 1 complete so README links land on executable docs.

**Authority:**
- Preauthorized local actions: edit `README.md`, update links and public-facing explanations, and run Markdown/source checks
- Stop for: new product claims, changed runtime semantics, license policy decisions, or generated-surface edits

**Steps:**
- [ ] Step 1: Add a compact Requirements and Get Started section near the top.
- [ ] Step 2: Add three paths: understand, evaluate, and adopt.
- [ ] Step 3: Separate core validation from full benchmark validation and include dependency installation.
- [ ] Step 4: Correct runtime status wording and retain the required phrase `version pinned by \`scripts/setup_deepagents_runtime.ps1\`` without copying numeric version values.
- [ ] Step 5: Keep architecture, scope, non-goals, and license status concise and link deeper detail to canonical docs.
- [ ] Step 6: Preserve existing README contract phrases: `native-personal-local`, `Codex, DeepAgents, or Tura`, `planning-dispatch.md`, `--role <profile>`, `DeepAgents MCP is opt-in through explicit Herdr selection`, `project-local folders`, `Shared operating-system docs, reusable scripts, and skills stay under`, and the `docs/intent/` adoption guidance.

**Verification:**
- [ ] Compare every new README command/link with Task 1 source map and run README contract tests.
- Expected: README acts as a project map, not a second runtime manual.

**Exit Criteria:**
- README provides accurate first-step routing, preserves tested contract phrases, and has no stale or unsupported operational claims.

### Task 3: Run final documentation verification

**Purpose:**
- Prove documentation convergence without weakening or changing runtime validators.

**Task Function:**
- Reconcile changed docs, command references, public-boundary constraints, and preserved workspace state.

**Template Profile:**
- Controller-selected: `none (lead controller)`
- Selection basis: fresh, repository-native verification for a documentation-only change.

**Validator Profile:**
- Controller-selected: `none`
- Selection basis: final checks are deterministic and local.

**Specification Coverage:**
- Documentation links, commands, source-of-truth references, generated-surface boundaries, and scope claims are current.
- No runtime behavior or unrelated workspace state changed.

**Required Skills:**
- `skill-verification-before-completion`

**Files And Symbols:**
- Verify: `README.md`, `docs/setup.md`, `docs/usage.md`
- Verify: changed-file diff and preserved untracked paths

**Dependencies:**
- Task 2 complete.

**Authority:**
- Preauthorized local actions: run declared validators, focused documentation tests, diff checks, link/path inspections, and update this plan’s evidence ledger
- Stop for: failed required check, stale source claim, unexpected tracked file, or scope deviation requiring approval

**Steps:**
- [ ] Step 1: Run focused documentation/link/source checks and `git diff --check`.
- [ ] Step 2: Run `python scripts/validate_repo_contracts.py`.
- [ ] Step 3: Run README/setup/usage contract tests, excluding the known pre-existing `test_cos_ssot_invariants_stay_symmetric` failure on `main`.
- [ ] Step 4: Confirm no adapter, generated runtime, adoption-guide, or unrelated files changed; confirm preserved untracked files remain untouched.
- [ ] Step 5: Record baseline failure, fresh evidence, deviations, and remaining follow-up in this plan before handoff.

**Verification:**
- [ ] `python scripts/validate_repo_contracts.py`
- [ ] `python -m pytest -q tests/test_validate_repo_contracts.py tests/test_starter_kit_generation.py tests/test_starter_lifecycle_contract.py tests/test_native_personal_local_workflow.py -k "not test_cos_ssot_invariants_stay_symmetric"`
- [ ] `git diff --check`
- Expected: required checks pass; documentation-only diff contains only approved Markdown and this plan; the known unrelated symmetry failure remains documented rather than hidden.

**Exit Criteria:**
- Final docs are source-backed, actionable, public-boundary safe, and verified with fresh repository evidence.

## Verification

- `python scripts/validate_repo_contracts.py`
- `python -m pytest -q tests/test_validate_repo_contracts.py tests/test_starter_kit_generation.py tests/test_starter_lifecycle_contract.py tests/test_native_personal_local_workflow.py -k "not test_cos_ssot_invariants_stay_symmetric"`
- `git diff --check`
- Manual link/path audit for all changed Markdown documents.

## Completion Criteria

The plan is ready for completion verification when:

1. README, setup, usage, and the linked existing adoption path are executable and agree.
2. Core validation, benchmark validation, and optional runtime setup are clearly separated.
3. Dispatcher status semantics and platform claims match current source and CI.
4. No private governance, credentials, runtime state, or unsupported product claim is exposed.
5. Required focused checks pass; the pre-existing symmetry failure is recorded; unrelated untracked workspace content remains preserved.
6. `skill-verification-before-completion` confirms fresh evidence and no unresolved scope deviation.
