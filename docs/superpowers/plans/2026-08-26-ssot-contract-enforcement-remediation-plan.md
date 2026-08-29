---
template_id: implementation-plan
contract_version: "1"
name: SSOT contract enforcement remediation
artifact_type: plan
status: completed
layer: change
parent_spec: none
---

# SSOT Contract Enforcement Remediation Plan

## Goal

Remove confirmed drift between canonical planning policy, schemas, validators,
Switchyard configuration, and repository enforcement without adding a second
planning registry or broad documentation rewrite.

## Implementation Outcomes

### Canonical planning contracts enforce their declared rules

Implementation plans and specifications select a known template, task ledgers
accept only supported executors, and completed plans contain only completed
tasks with terminal coordination fields.

### Runtime policy and repository checks share one enforcement boundary

Switchyard policy validation runs without user-local runtime state, the
canonical repository contract command invokes it, and GitHub has one CI gate
for that command. README and version wording match current executable behavior.

## Execution Approach

- Mode: `inline sequential`
- Coordination: `git-tracked`
- Default task executor: `codex`
- Required skills: `skill-test-driven-development`, `skill-verification-before-completion`
- Isolation: `current workspace` on `codex/ssot-contract-enforcement`
- Commit policy: `no commits during execution`
- Preauthorized local actions: edits to listed files, focused tests, canonical contract checks, `git diff --check`
- User-approval actions: push, merge, publication, external writes, destructive cleanup, branch finishing
- Parallel ownership: none; tasks share schema and canonical runner surfaces
- Sequential fallback: complete tasks in ledger order if any shared-file dependency appears

## Coordination State

- Coordination owner: `single lead controller`
- Coordination schema: `1`
- Branch: `codex/ssot-contract-enforcement`
- Base commit: `1e4550ce9e55bcf9b7e44d3b523ed9c8deb42f34`
- Active task(s): `none`
- Expected workspace: `approved in-scope changes only`
- Next action: `none`
- Blockers: `none`

| Task | State | Workspace | Executor | Depends On | Required Proof | Evidence |
| --- | --- | --- | --- | --- | --- | --- |
| Task 1 | `completed` | current | `codex` | none | focused template tests and strict validator run | `27 passed` |
| Task 2 | `completed` | current | `codex` | Task 1 | lifecycle tests and invalid-fixture checks | `12 passed` |
| Task 3 | `completed` | current | `codex` | Task 1 | Switchyard static validation tests | `24 passed` |
| Task 4 | `completed` | current | `codex` | Task 2, Task 3 | workflow inspection and canonical command | `--fast passed` |
| Task 5 | `completed` | current | `codex` | Task 1, Task 2, Task 3, Task 4 | README/version inspection and final diff checks | `51 passed; canonical contracts passed; diff check passed` |

## Task Breakdown

### Task 1: Normalize template policy and selection enforcement

**Purpose:**
- Make template/profile policy internally consistent and close the live missing-`template_id` bypass.

**Task Function:**
- Update canonical planning metadata rules and regression coverage.

**Template Profile:**
- Controller-selected: `none (lead controller)`
- Selection basis: bounded edits with clear ownership; delegated profile selection adds no benefit.

**Validator Profile:**
- Controller-selected: `none`
- Selection basis: task-local tests and canonical contract command provide proof.

**Specification Coverage:**
- `template_id` is required for `spec` and `plan`, optional for `roadmap`.
- Executor and validator profiles are independent; no rank relationship is imposed.
- Canonical contract validation must enforce template selection.

**Required Skills:**
- `skill-test-driven-development`

**Files And Symbols:**
- Inspect: `repo_config/planning_artifact_schema.yaml`
- Inspect: `scripts/validate_template_required_sections.py:validate_documents`
- Inspect: `scripts/validate_repo_contracts.py:build_subprocess_steps`
- Modify: `repo_config/planning_artifact_schema.yaml`
- Modify: `docs/operating_system/templates/implementation-plan-template.md`
- Modify: `scripts/validate_repo_contracts.py:build_subprocess_steps`
- Modify: `docs/superpowers/plans/2026-07-18-mcp-memory-ui-ux-integration.md`
- Verify: `tests/test_validate_template_required_sections.py`
- Verify: `tests/test_validate_repo_contracts.py`

**Dependencies:**
- Clean workspace and base commit recorded above.

**Authority:**
- Preauthorized local actions: edit listed schema, template, runner, legacy plan, and tests; run focused checks.
- Stop for: additional legacy documents without a clear template mapping, generated-surface changes, or policy changes outside this plan.

**Steps:**
- [ ] Step 1: Inventory all `docs/superpowers/specs/*.md` and `docs/superpowers/plans/*.md`; add `template_id` to each missing document only when its template is unambiguous. Current known migration: `2026-07-18-mcp-memory-ui-ux-integration.md` uses `implementation-plan`.
- [ ] Step 2: Add artifact-specific `required_fields: [template_id]` to `spec` and `plan`; leave `roadmap` optional. Reuse existing `get_required_fields()` behavior; do not add an exception allowlist.
- [ ] Step 3: Remove contradictory validator-profile sentences from the implementation-plan template. Keep only independent profile selection and the complete validator enum `none|low|normal|high|xhigh`.
- [ ] Step 4: Pass `--require-template-selection` when `validate_repo_contracts.py` invokes `validate_template_required_sections.py`.
- [ ] Step 5: Add regression coverage for missing selection, artifact-specific required fields, and absence of retired rank-policy wording.

**Verification:**
- [ ] `py -3 -m pytest tests/test_validate_template_required_sections.py tests/test_validate_repo_contracts.py -q`
- Expected: focused tests pass; missing `template_id` fails strict validation; roadmap remains allowed without it.

**Exit Criteria:**
- Every existing spec and plan has an unambiguous template selection, canonical validation runs strict selection, and template policy has one interpretation.

### Task 2: Enforce executor and completed-plan lifecycle invariants

**Purpose:**
- Prevent invalid task routing and stale coordination state from passing lifecycle validation.

**Task Function:**
- Extend lifecycle parsing and validation from syntax checks to terminal-state invariants.

**Template Profile:**
- Controller-selected: `none (lead controller)`
- Selection basis: bounded parser and fixture changes; no delegation benefit.

**Validator Profile:**
- Controller-selected: `none`
- Selection basis: focused lifecycle tests cover success and failure paths.

**Specification Coverage:**
- Ledger executor values are exactly `codex`, `deepagents`, or `tura`.
- A completed plan has only completed ledger tasks, no blockers, no active tasks, and `Next action: none`.

**Required Skills:**
- `skill-test-driven-development`

**Files And Symbols:**
- Inspect: `scripts/planning_artifact_schema.py:get_allowed_values`
- Inspect: `scripts/validate_planning_lifecycle.py:validate_git_coordination`
- Modify: `repo_config/planning_artifact_schema.yaml`
- Modify: `scripts/validate_planning_lifecycle.py:validate_git_coordination`
- Modify: `tests/test_validate_planning_lifecycle.py`
- Modify: `docs/superpowers/plans/2026-08-25-17-08-switchyard-auto-routing-sidecar-experiment-plan.md`
- Modify: `docs/superpowers/plans/2026-08-25-23-35-switchyard-routing-ssot-decision-evidence-plan.md`
- Modify: `docs/superpowers/plans/2026-08-25-23-51-three-runtime-task-executor-selection-plan.md`
- Modify: `docs/superpowers/plans/2026-08-25-wayfinder-gap-first-plan.md`
- Modify: `docs/superpowers/plans/2026-08-25-tura-bounded-worker-conformance-and-upgrade-plan.md`

**Dependencies:**
- Task 1 complete; schema and template policy are stable.

**Authority:**
- Preauthorized local actions: edit listed schema, validator, stale completed-plan coordination fields, and tests; run focused checks.
- Stop for: new coordination states, new executor names, or changes to Git checkpoint policy.

**Steps:**
- [ ] Step 1: Add one canonical executor enum under planning schema allowed values and make lifecycle validation consume it through `get_allowed_values()`.
- [ ] Step 2: Reject empty or unknown `Executor` cells with file and task identity in the finding.
- [ ] Step 3: For `status: completed`, reject any `pending`, `active`, or `blocked` ledger row; require normalized `Active task(s): none`, `Blockers: none`, and exact `Next action: none`.
- [ ] Step 4: Reconcile known completed plans so their coordination state matches terminal status; do not alter historical task evidence.
- [ ] Step 5: Add invalid executor, pending-task, stale-next-action, and valid completed-plan fixtures.

**Verification:**
- [ ] `py -3 -m pytest tests/test_validate_planning_lifecycle.py -q`
- Expected: invalid executor and nonterminal completed plans fail; valid active and completed fixtures pass.

**Exit Criteria:**
- Lifecycle validator enforces executor and terminal coordination invariants from canonical schema values, with regression tests for each failure mode.

### Task 3: Add CI-safe Switchyard policy validation

**Purpose:**
- Validate committed routing policy and agent profiles without reading user-local Codex or Switchyard runtime state.

**Task Function:**
- Split static repository-contract validation from local runtime drift checking while reusing existing loaders and invariants.

**Template Profile:**
- Controller-selected: `none (lead controller)`
- Selection basis: narrow Python change with existing unit-test seams.

**Validator Profile:**
- Controller-selected: `none`
- Selection basis: direct CLI and unit tests provide proof.

**Specification Coverage:**
- `repo_config/switchyard-routing.toml` is a canonical consumed configuration source.
- Static validation covers policy shape, profile references, provider compatibility, model separation, and route constraints.
- Runtime `check`, `deploy`, and `smoke` retain user-local behavior and remain outside CI-safe validation.

**Required Skills:**
- `skill-test-driven-development`

**Files And Symbols:**
- Inspect: `scripts/manage_switchyard_runtime.py:load_routing_policy`
- Inspect: `scripts/manage_switchyard_runtime.py:load_agent_profiles`
- Inspect: `scripts/manage_switchyard_runtime.py:resolve_routing_contract`
- Inspect: `scripts/manage_switchyard_runtime.py:_parser`
- Inspect: `scripts/manage_switchyard_runtime.py:main`
- Modify: `scripts/manage_switchyard_runtime.py`
- Modify: `tests/test_manage_switchyard_runtime.py`
- Modify: `scripts/validate_repo_contracts.py:build_subprocess_steps`
- Modify: `docs/operating_system/governance/repo-governance.md`

**Dependencies:**
- Task 1 complete; canonical runner changes are available for integration.

**Authority:**
- Preauthorized local actions: edit listed manager, runner, governance, and tests; run static validation with temporary fixtures.
- Stop for: user-local config reads in the new command, runtime deployment, network calls, or generated output writes.

**Steps:**
- [ ] Step 1: Extract shared static checks from `resolve_routing_contract()` so both runtime resolution and CI-safe validation use the same policy/profile invariants.
- [ ] Step 2: Add `validate` CLI command accepting committed manifest and profile paths, with no Codex config, `$HOME`, Switchyard home, server, or network dependency.
- [ ] Step 3: Add tests for missing profiles, low automatic endpoints, provider mismatch, duplicate model IDs, invalid policy values, and valid repository configuration.
- [ ] Step 4: Add the `validate` command to `build_subprocess_steps()`; keep `check` and `smoke` out of the canonical contract command.
- [ ] Step 5: Add `repo_config/switchyard-routing.toml` to the governance configuration inventory and state that manager validation owns its rules.

**Verification:**
- [ ] `py -3 -m pytest tests/test_manage_switchyard_runtime.py tests/test_validate_repo_contracts.py -q`
- [ ] `py -3 scripts/manage_switchyard_runtime.py validate --manifest repo_config/switchyard-routing.toml`
- Expected: static validation passes from a clean environment; no user-local paths or generated outputs are required.

**Exit Criteria:**
- Switchyard policy has one CI-safe validation path, the canonical runner invokes it, and local runtime drift checks retain their existing boundary.

### Task 4: Restore hosted contract enforcement

**Purpose:**
- Make canonical contract validation run on every relevant GitHub change.

**Task Function:**
- Add one minimal workflow around the existing repository contract command.

**Template Profile:**
- Controller-selected: `none (lead controller)`
- Selection basis: one declarative workflow using existing requirements and command.

**Validator Profile:**
- Controller-selected: `none`
- Selection basis: workflow review plus local command proof.

**Specification Coverage:**
- GitHub pull requests and pushes to the default branch run the canonical repository contract command.
- CI installs the existing dependency set and does not require secrets, user-local runtime state, or deployment services.

**Required Skills:**
- `none`

**Files And Symbols:**
- Inspect: `requirements.txt`
- Inspect: `scripts/validate_repo_contracts.py`
- Modify: `.github/workflows/repo-contracts.yml`
- Verify: `.github/workflows/repo-contracts.yml`

**Dependencies:**
- Tasks 2 and 3 complete; canonical command must pass locally first.

**Authority:**
- Preauthorized local actions: add one workflow file and inspect its commands.
- Stop for: secret configuration, external service setup, branch protection changes, or additional CI jobs.

**Steps:**
- [ ] Step 1: Create one workflow for `push` and `pull_request` events on the default branch.
- [ ] Step 2: Use Python 3.12, install `requirements.txt`, and run `py -3 scripts/validate_repo_contracts.py` equivalent through the runner's Python executable.
- [ ] Step 3: Keep permissions least-privilege and omit secrets, runtime deployment, and network-dependent Switchyard operations.
- [ ] Step 4: Review workflow YAML and run the same command locally.

**Verification:**
- [ ] `py -3 scripts/validate_repo_contracts.py --fast`
- [ ] Inspect `.github/workflows/repo-contracts.yml` for trigger, Python version, dependency install, and canonical command.
- Expected: workflow is self-contained and canonical contract command passes locally.

**Exit Criteria:**
- Repository contains one documented, secret-free GitHub gate for canonical contract validation.

### Task 5: Align README and runtime-version wording

**Purpose:**
- Remove low-risk documentation claims that contradict current repository layout or installer behavior.

**Task Function:**
- Replace duplicated inventory claims with governance pointers and describe DeepAgents version accurately.

**Template Profile:**
- Controller-selected: `none (lead controller)`
- Selection basis: bounded documentation cleanup after executable contracts settle.

**Validator Profile:**
- Controller-selected: `none`
- Selection basis: source inspection and final contract checks.

**Specification Coverage:**
- README does not list nonexistent `configs/` or imply generated surfaces are limited to `AGENTS.md`.
- DeepAgents `0.1.59` is described as default/tested while override remains supported.
- Broad runtime-guidance deduplication remains out of scope.

**Required Skills:**
- `none`

**Files And Symbols:**
- Inspect: `README.md`
- Inspect: `docs/configuration.md`
- Inspect: `docs/operating_system/procedures/runtime-adapter-procedure.md`
- Inspect: `docs/operating_system/procedures/personal-local-worktree-procedure.md`
- Inspect: `docs/operating_system/runtime/runtime-surfaces.md`
- Inspect: `scripts/setup_deepagents_runtime.ps1`
- Inspect: `docs/operating_system/governance/repo-governance.md`
- Modify: `README.md`
- Modify: `docs/configuration.md`
- Modify: `docs/operating_system/procedures/runtime-adapter-procedure.md`
- Modify: `docs/operating_system/procedures/personal-local-worktree-procedure.md`
- Modify: `docs/operating_system/runtime/runtime-surfaces.md`

**Dependencies:**
- Tasks 1–4 complete; final wording must reflect finished enforcement paths.

**Authority:**
- Preauthorized local actions: edit README inventory and version wording; run final checks.
- Stop for: broad documentation consolidation, generated adapter changes, or publication edits.

**Steps:**
- [ ] Step 1: Replace the stale canonical/generated inventory with a short pointer to repository governance ownership.
- [ ] Step 2: Change “pins `deepagents-code 0.1.59`” to “defaults/tests `deepagents-code 0.1.59`” while preserving setup instructions.
- [ ] Step 3: Search README and active operating-system docs for remaining claims that say the overrideable version is immutable; update only concrete contradictions.

**Verification:**
- [ ] `rg -n "configs/|pins.*0\.1\.59" README.md docs/configuration.md docs/operating_system`
- Expected: no stale README inventory or overstated pin claim remains; unrelated runtime guidance stays unchanged.

**Exit Criteria:**
- README matches governance and executable setup behavior without introducing a second ownership source.

## Deferred Scope

- Do not add `wayfinding_map` to `planning_artifact_schema.yaml`; governance and the Wayfinder skill explicitly keep maps provisional.
- Do not add Wayfinder closure-state parsing until a persisted map requires executable lifecycle enforcement. Trigger: first production map or a demonstrated closure-state failure.
- Do not mass-deduplicate runtime guidance; fix only proven contradictions.
- Do not remove `DeepAgentsCodeVersion` override unless reproducibility policy separately requires a hard pin.

## Verification

- `py -3 -m pytest tests/test_validate_template_required_sections.py tests/test_validate_planning_lifecycle.py tests/test_manage_switchyard_runtime.py tests/test_validate_repo_contracts.py -q`
- `py -3 scripts/validate_repo_contracts.py`
- `git diff --check`
- Inspect `.github/workflows/repo-contracts.yml` and confirm no generated or user-local runtime outputs changed.

## Completion Criteria

1. Tasks 1–5 pass their declared proof and ledger evidence is recorded.
2. Canonical template, planning schema, lifecycle validator, Switchyard validator, governance inventory, README, and workflow agree.
3. Existing legacy planning documents are migrated or explicitly stopped with evidence; no silent bypass remains.
4. No Wayfinder schema expansion, broad runtime deduplication, or hard version pin is introduced.
5. Final verification is fresh, `git diff --check` passes, and no unrecorded scope deviation remains.
