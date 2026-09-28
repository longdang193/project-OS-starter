---
artifact_type: plan
template_id: implementation-plan
contract_version: "1"
status: completed
layer: change
---

# README Execution Model Convergence Plan

## Goal

Update the README from a universal coordinated-lane description to an
accurate project orientation layer. Align its execution model, admission
states, runtime terminology, adoption routing, and source-of-truth links with
current planning and runtime contracts. Update linked high-level documentation
and README contract tests where the current wording is duplicated or
contradictory.

This plan is documentation and test maintenance only. It must not change
runtime behavior, dispatcher semantics, publication policy, generated agent
surfaces, dependency versions, or license state.

## Implementation Outcomes

### Accurate execution model

`README.md`, `docs/architecture.md`, and `docs/pipeline.md` distinguish direct
execution, single-executor work, and Git-tracked coordinated work. Git-tracked
plans and implementation lanes are described as conditional coordination tools,
not mandatory stages for every task.

### Accurate state and runtime language

README preserves the separate admission, runtime-fact, and acceptance
namespaces. It does not collapse `DEFERRED` or `REJECTED` into `BLOCKED`, and it
describes Herdr as coordination transport/diagnostic observation rather than a
peer executor.

### Maintainable onboarding surface

README routes readers to setup, usage, architecture, and adoption sources
without copying low-level runtime policy. Requirements include the optional
PowerShell 7 prerequisite where applicable. Adoption wording consistently
refers to the consuming repository.

### Source-backed verification

README-specific tests verify durable concepts and canonical links instead of
requiring duplicated runtime-policy sentences. Focused validators, tests, link
checks, and diff checks prove documentation convergence without touching
unrelated workspace state.

## Execution Approach

- Mode: `inline sequential`
- Coordination: `git-tracked`
- Required skills: `skill-private-public-repo-governance`, `skill-verification-before-completion`
- Isolation: `current workspace`
- Commit policy: `no commits during execution`
- Preauthorized local actions: inspect named source/docs/tests, edit named Markdown and test files, run declared read-only validation/test/link commands, and preserve unrelated untracked files
- User-approval actions: plan activation, publication, policy/configuration changes, license changes, push, merge, destructive cleanup, or edits outside named files
- Parallel ownership: `none`
- Sequential fallback: resolve repository/publication role before editing; update high-level docs before changing README assertions; run final verification last

## Coordination State

- Coordination owner: `single lead controller`
- Coordination schema: `2`
- Branch: `main`
- Base commit: `336dfa283f38ea65b6a3f0c333b528571ac6d499`
- Expected workspace: tracked files unchanged before execution; preserve existing untracked `.playwright-mcp/`, `db/`, and `temp_evidence.json`
- Next action: verified; await explicit branch disposition
- Blockers: `none`

| Task | State | Workspace | Executor | Depends On | Required Proof | Evidence |
| --- | --- | --- | --- | --- | --- | --- |
| Task 1 | `completed` | current | `codex` | none | role decision and source map | docs/intent identifies this checkout as private engineering source; public publication remains curated and scrubbed |
| Task 2 | `completed` | current | `codex` | Task 1 | high-level docs match planning truth | architecture, pipeline, and usage now distinguish direct, single-executor, and coordinated work |
| Task 3 | `completed` | current | `codex` | Task 2 | README and tests match canonical wording | README rewritten; focused README and onboarding tests pass |
| Task 4 | `completed` | current | `codex` | Task 3 | fresh validator, focused tests, links, and diff proof | full validator passed; 45 focused README/contract tests passed; 2 native workflow tests passed; links and diff checks passed |

## Task Breakdown

### Task 1: Resolve publication boundary and build source map

**Purpose:**
- Establish whether current repository is the private engineering source,
  public curated mirror, or public source/reference repository before changing
  README links or public-facing claims.

**Task Function:**
- Reconcile repository role, documentation visibility, execution-policy
  ownership, and existing README claims.

**Template Profile:**
- Controller-selected: `none (lead controller)`
- Selection basis: bounded source audit; no implementation ambiguity after role decision.

**Validator Profile (optional):**
- Controller-selected: `none`
- Selection basis: repository policy and source inspection provide required proof.

**Specification Coverage:**
- README remains a synthesized orientation layer.
- Public documentation must not depend on private operating-system materials.
- Publication policy and `repo_config/publication-config.json` remain authoritative
  for boundary classification.
- Do not add direct README links to `docs/operating_system/` until repository
  role and publication path permit them.

**Required Skills:**
- `skill-private-public-repo-governance`

**Files And Symbols:**
- Inspect: `README.md` sections `Requirements`, `Get Started`, `How It Works`, `Evaluation Path`, and `Local Adoption`
- Inspect: `docs/intent/constraints-and-non-goals.md`
- Inspect: `docs/operating_system/publication/public-repo-publication-policy.md`
- Inspect: `repo_config/publication-config.json`
- Inspect: `docs/operating_system/adoption/project-adoption-migration-guide.md`
- Verify: current tracked/untracked workspace state

**Dependencies:**
- User-approved plan; lead controller changes plan status from `proposed` to `active` before editing.

**Authority:**
- Preauthorized local actions: inspect named files, compare policy/configuration, and record the selected repository role in plan evidence
- Stop for: unresolved repository role, requested publication-policy change, license decision, or any need to expose private operating-system material through public README

**Steps:**
- [x] Step 1: Compare README link targets and claims against publication policy and configuration.
- [x] Step 2: Confirm the current checkout against the policy's two roles: private engineering source or curated public mirror. Treat `repo_config/publication-config.json` as path-boundary evidence, not repository-role authority.
- [x] Step 3: Define the README boundary: no links to `docs/operating_system/`, `docs/superpowers/`, `.agents/`, or other forbidden paths; identify public-safe canonical documents for execution, runtime, adoption, and validation claims.
- [x] Step 4: Record boundary decision and any deferred policy work in plan evidence before editing.

**Verification:**
- [x] Inspect all README relative links and classify each target as public-safe, source-only, or requiring policy decision.
- Expected: no unapproved private dependency enters README scope.

**Exit Criteria:**
- Repository role is explicit, README link boundary is known, and Task 2 can edit without inventing publication behavior.

### Task 2: Align high-level architecture and pipeline docs

**Purpose:**
- Remove the same universal coordinated-lane claim from the two primary README destinations.

**Task Function:**
- Rewrite high-level architecture language around conditional planning and execution selection while preserving existing state contracts.

**Template Profile:**
- Controller-selected: `none (lead controller)`
- Selection basis: three small documentation surfaces with one shared semantic correction.

**Validator Profile (optional):**
- Controller-selected: `none`
- Selection basis: focused source comparison and repository tests are sufficient.

**Specification Coverage:**
- Direct, single-executor, and Git-tracked coordinated work remain distinct.
- Git-tracked coordination applies when multi-task resume, delegation,
  parallel writers, or durable ownership requires it.
- Existing admission, runtime-fact, acceptance, recovery, and dispatcher
  semantics remain unchanged.

**Required Skills:**
- `skill-private-public-repo-governance`

**Files And Symbols:**
- Modify: `docs/architecture.md` main path and boundary explanation
- Modify: `docs/pipeline.md` stage description and task-level wording
- Modify: `docs/usage.md` reference task flow
- Inspect: `docs/operating_system/planning/planning-dispatch.md` selection table and coordinated-work rules
- Inspect: `docs/operating_system/procedures/personal-local-worktree-procedure.md` ordinary and coordinated work boundaries
- Inspect: `docs/architecture/project-OS-starter-guided-story.workflow.json` canonical coordinated workflow source
- Verify: `README.md` diagram and explanatory paragraphs after Task 3

**Dependencies:**
- Task 1 complete with approved documentation boundary.

**Authority:**
- Preauthorized local actions: edit only the named high-level Markdown sections and run source/doc checks
- Stop for: runtime contract changes, altered state definitions, generated projection edits, or unresolved conflict with canonical planning docs

**Steps:**
- [x] Step 1: Replace mandatory `Task → Git-Tracked Plan → Implementation Lanes` wording with a selection branch in architecture and usage docs.
- [x] Step 2: State that direct and single-executor work may omit Git-tracked coordination when planning rules allow.
- [x] Step 3: Clarify that Guided Story illustrates coordinated multi-agent work; leave its canonical workflow source and generated projections unchanged unless a separate approved scope authorizes regeneration.
- [x] Step 4: Preserve recovery and acceptance language, including runtime completion not proving acceptance.
- [x] Step 5: Check README destinations for matching universal-pipeline claims before moving to Task 3.

**Verification:**
- [x] Compare changed paragraphs against `docs/operating_system/planning/planning-dispatch.md` and `docs/operating_system/procedures/personal-local-worktree-procedure.md`.
- Expected: high-level docs describe one conditional model without weakening coordinated-work requirements.

**Exit Criteria:**
- Architecture, pipeline, and usage docs agree with planning dispatch and no longer imply every task needs a plan or implementation lane.

### Task 3: Update README and README contract tests

**Purpose:**
- Make README concise, accurate, and useful as an orientation/adoption gateway.

**Task Function:**
- Rewrite public-facing explanations and test durable concepts without making README a runtime-policy SSOT.

**Template Profile:**
- Controller-selected: `none (lead controller)`
- Selection basis: bounded documentation rewrite after source-of-truth audit.

**Validator Profile (optional):**
- Controller-selected: `none`
- Selection basis: tests and link inspection provide deterministic proof.

**Specification Coverage:**
- Requirements include Git, Python 3.12+, core dependencies, benchmark-only
  dependencies, and PowerShell 7 only where optional DeepAgents setup needs it.
- README explains Herdr as coordination transport/diagnostics, not a peer
  executor.
- Admission wording preserves `ADMITTED | DEFERRED | BLOCKED | REJECTED`.
- README routes understand, evaluate, and adopt journeys clearly.
- Low-level MCP syntax, secret handling, runtime version ownership, profile
  selectors, and lifecycle receipts remain in owning documents.
- Adoption wording uses `consuming repository` consistently.
- No module-name or proposed-capability expansion enters README.

**Required Skills:**
- `skill-private-public-repo-governance`

**Files And Symbols:**
- Modify: `README.md` sections `Requirements`, `Get Started`, `How It Works`, `Evaluation Path`, `Local Adoption`, and `Open-Source Ecosystem`
- Modify: `tests/test_starter_kit_generation.py` README contract assertions
- Modify: `tests/test_native_personal_local_workflow.py` README-specific assertions and focused test selection
- Inspect: `docs/setup.md`, `docs/usage.md`, `docs/architecture.md`, `docs/pipeline.md`
- Inspect: `docs/operating_system/runtime/runtime-surfaces.md` for canonical runtime ownership links

**Dependencies:**
- Task 2 complete; Task 1 boundary decision is recorded in Coordination State evidence.

**Authority:**
- Preauthorized local actions: edit README and named README-specific test assertions, add source-backed links, and run focused documentation checks
- Stop for: publication-policy edits, license changes, new runtime claims, changed runtime semantics, or generated-surface edits

**Steps:**
- [x] Step 1: Replace README pipeline diagram and “bounded implementation lanes” claim with conditional execution-selection wording.
- [x] Step 2: Replace admission failure sentence with four-state admission wording and separate runtime/acceptance namespaces.
- [x] Step 3: Split requirements into optional `Codex`, `DeepAgents`, or `Tura` executor setup; optional Herdr coordinated transport/diagnostics; and optional PowerShell 7 (`pwsh`) for DeepAgents setup.
- [x] Step 4: Add adoption routing only through approved public-safe documents such as `docs/setup.md`, `docs/usage.md`, or `docs/configuration.md`; do not add README links to private operating-system paths.
- [x] Step 5: Remove duplicated low-level runtime-policy bullets and replace them with durable concepts or bare canonical filenames; do not add private operating-system links to README.
- [x] Step 6: Trim ecosystem entries that imply support without a maintained support matrix.
- [x] Step 7: Update `tests/test_starter_kit_generation.py` and `tests/test_native_personal_local_workflow.py` assertions deliberately; preserve or replace current README literals for `native-personal-local`, `Codex, DeepAgents, or Tura`, `planning-dispatch.md`, and the setup-script version-owner phrase.

**Verification:**
- [x] Run README-focused tests after edits.
- Expected: tests validate orientation concepts, canonical links, and adoption wording without forcing low-level policy duplication.

**Exit Criteria:**
- README matches architecture and pipeline docs, preserves required durable onboarding, and does not claim unsupported execution or publication behavior.

### Task 4: Run final documentation verification

**Purpose:**
- Prove documentation convergence and preserve unrelated workspace state.

**Task Function:**
- Run fresh repository-native validation, focused tests, link checks, and diff inspection.

**Template Profile:**
- Controller-selected: `none (lead controller)`
- Selection basis: deterministic documentation verification.

**Validator Profile (optional):**
- Controller-selected: `none`
- Selection basis: repository validators and focused tests are authoritative.

**Specification Coverage:**
- Changed docs agree with canonical planning and runtime sources.
- Relative README links resolve within approved scope.
- README tests no longer enforce duplicated low-level policy.
- No runtime, generated, publication-config, or unrelated workspace files changed.

**Required Skills:**
- `skill-verification-before-completion`

**Files And Symbols:**
- Verify: `README.md`
- Verify: `docs/architecture.md`
- Verify: `docs/pipeline.md`
- Verify: `tests/test_starter_kit_generation.py`
- Verify: `tests/test_native_personal_local_workflow.py`
- Verify: `scripts/validate_repo_contracts.py` output
- Verify: tracked diff and preserved untracked paths

**Dependencies:**
- Task 3 complete.

**Authority:**
- Preauthorized local actions: run declared validators, focused tests, link/path inspections, `git diff --check`, and update this plan evidence
- Stop for: failed required check, stale source claim, unexpected tracked file, public-boundary violation, or scope deviation

**Steps:**
- [x] Step 1: Run `python scripts/validate_repo_contracts.py`.
- [x] Step 2: Run focused README/planning tests, including `tests/test_starter_kit_generation.py`, `tests/test_validate_repo_contracts.py`, and README-owning tests from `tests/test_native_personal_local_workflow.py`; exclude unrelated baseline failures only with an explicit `-k` filter and record them.
- [x] Step 3: Run `git diff --check`.
- [x] Step 4: Verify relative links for every changed Markdown file and enforce the README forbidden-path boundary.
- [x] Step 5: Inspect diff for runtime-policy duplication, accidental public/private boundary changes, and unrelated files.
- [x] Step 6: Inspect `git diff -- README.md docs/architecture.md docs/pipeline.md docs/usage.md tests/test_starter_kit_generation.py tests/test_native_personal_local_workflow.py` for semantic proof.
- [x] Step 7: Record fresh evidence, deviations, blockers, and follow-up in this plan.

**Verification:**
- [x] `python scripts/validate_repo_contracts.py`
- [x] `python -m pytest -q tests/test_starter_kit_generation.py tests/test_validate_repo_contracts.py`
- [x] `python -m pytest -q tests/test_native_personal_local_workflow.py -k "test_three_runtime_personal_local_workflow_is_documented or test_deepagents_default_version_has_single_runtime_owner"`
- [x] `git diff --check`
- [x] `git diff -- README.md docs/architecture.md docs/pipeline.md docs/usage.md tests/test_starter_kit_generation.py tests/test_native_personal_local_workflow.py`
- [x] Relative-link/path check for every changed Markdown file and README forbidden-path check
- Evidence: full validator passed; `45 passed` in README/contract tests; `2 passed, 14 deselected` in native workflow tests; relative links and README boundary passed.
- Expected: required checks pass; only approved Markdown/tests change; unrelated untracked files remain untouched.

**Exit Criteria:**
- Documentation is source-backed, publication-safe under the resolved repository role, semantically aligned, and verified with fresh output.

## Verification

- [x] `python scripts/validate_repo_contracts.py`
- [x] `python -m pytest -q tests/test_starter_kit_generation.py tests/test_validate_repo_contracts.py`
- [x] `python -m pytest -q tests/test_native_personal_local_workflow.py -k "test_three_runtime_personal_local_workflow_is_documented or test_deepagents_default_version_has_single_runtime_owner"`
- [x] `git diff --check`
- [x] `git diff -- README.md docs/architecture.md docs/pipeline.md docs/usage.md tests/test_starter_kit_generation.py tests/test_native_personal_local_workflow.py`
- [x] Relative-link/path inspection for every changed Markdown file and README forbidden-path check
- [x] Final tracked diff inspection with unrelated untracked files preserved

## Completion Criteria

The plan is ready for completion verification when:

1. repository/publication role is explicitly resolved or the plan records a
   concrete blocker and no boundary-dependent edit is made
2. README, architecture, pipeline, and usage docs use the same conditional
   execution model
3. admission wording preserves all four admission states and separate runtime
   and acceptance namespaces
4. Herdr, PowerShell, adoption, and consuming-repository wording is accurate
5. low-level runtime policy has one owning documentation source
6. README-specific tests verify durable concepts and canonical links
7. validators, focused tests, link checks, and diff checks pass
8. no unrelated files, generated surfaces, publication config, or runtime code
   changed

The plan may be marked `completed` only after fresh verification confirms every
criterion and records evidence here.
