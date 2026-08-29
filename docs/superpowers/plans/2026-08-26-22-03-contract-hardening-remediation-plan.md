---
layer: change
artifact_type: plan
status: completed
template_id: implementation-plan
contract_version: "1"
name: contract-hardening-remediation
targets:
  - scripts/validate_planning_lifecycle.py
  - scripts/deploy_agent_runtime.py
  - scripts/validate_agent_runtime_drift.py
  - scripts/validate_repo_contracts.py
  - scripts/build_starter_kit.py
  - scripts/validate_starter_kit.py
  - docs/operating_system/templates/implementation-plan-template.md
  - docs/operating_system/templates/agents/root-AGENTS.template.md
  - docs/operating_system/rules/frontend-ui-rule.md
  - docs/operating_system/planning/planning-dispatch.md
  - docs/operating_system/governance/precedence.md
  - tests/test_validate_planning_lifecycle.py
  - tests/test_deploy_agent_runtime.py
  - tests/test_validate_agent_runtime_drift.py
  - tests/test_validate_repo_contracts.py
  - tests/test_starter_kit_generation.py
  - tests/test_native_personal_local_workflow.py
  - scripts/sync_agent_adapters.py
  - tests/test_sync_agent_adapters.py
  - docs/operating_system/runtime/runtime-surfaces.md
  - docs/operating_system/provider_capabilities.yaml
  - docs/operating_system/procedures/runtime-adapter-procedure.md
  - docs/operating_system/procedures/starter-kit-procedure.md
  - docs/operating_system/governance/repo-governance.md
  - repo_config/starter-kit-manifest.json
  - AGENTS.md
  - .agents/rules/**
  - generated_agents/**
  - generated_exports/project-OS-starter-kit/**
  - docs/superpowers/plans/2026-08-26-22-03-contract-hardening-remediation-plan.md
---

# Contract Hardening Remediation

## Goal

Close justified contract gaps identified in the clean-audit verdict without
reopening Switchyard architecture or adding new registries, governance layers,
or lifecycle frameworks.

## Implementation Outcomes

### Planning contracts have one executable validator

Current proposed and active plans reject unknown execution modes, coordination
values, executors, and profiles. Historical completed and superseded plans remain
valid evidence. Git coordination is selected from parsed values. Active-task
state is owned only by the task ledger.

### Runtime and starter boundaries are safe

Shared skills use source-identified destination ownership markers. Repository
validation checks declared adapter mappings against actual runtime surfaces.
Consume-only starter output contains no factory-only regeneration instructions.

### Canonical policy and projections agree

Canonical routing, Wayfinding, Impeccable, and precedence wording is corrected,
then provider projections are regenerated and verified through existing checks.

## Execution Approach

- Mode: `inline sequential`
- Coordination: `git-tracked`
- Default task executor: `codex`
- Required skills: `skill-code-standards`, `skill-test-driven-development`, `skill-verification-before-completion`
- Isolation: `current workspace`
- Commit policy: `no commits during execution`
- Preauthorized local actions: edits to listed files, focused pytest commands, repository validators, all-platform adapter sync checks, starter-kit build and validation
- User-approval actions: commits, pushes, merges, publication, external runtime writes, destructive cleanup, and legacy skill adoption
- Parallel ownership: `none`
- Sequential fallback: complete tasks in ledger order in current workspace

## Coordination State

- Coordination owner: `single lead controller`
- Coordination schema: `1`
- Branch: `main`
- Base commit: `a9bb93abcb34b7381dec16ec44746117c6aaf390`
- Expected workspace: `declared task files changed; no unrelated changes`
- Next action: `await authorized branch disposition`
- Blockers: `none`

| Task | State | Workspace | Executor | Depends On | Required Proof | Evidence |
| --- | --- | --- | --- | --- | --- | --- |
| Task 1 | `completed` | current | `codex` | none | `python -m pytest tests/test_validate_planning_lifecycle.py tests/test_native_personal_local_workflow.py -q` | `29 passed; planning validator passed` |
| Task 2 | `completed` | current | `codex` | none | `python -m pytest tests/test_deploy_agent_runtime.py -q` | `12 passed; marker ownership tests pass` |
| Task 3 | `completed` | current | `codex` | none | `python -m pytest tests/test_validate_agent_runtime_drift.py tests/test_validate_repo_contracts.py tests/test_sync_agent_adapters.py -q` | `41 passed; runtime mapping and drift tests pass` |
| Task 4 | `completed` | current | `codex` | Task 3 | `python scripts/sync_agent_adapters.py --all-platforms --check` | `12 passed; projections clean` |
| Task 5 | `completed` | current | `codex` | Task 4 | `python -m pytest tests/test_starter_kit_generation.py -q` | `8 passed; starter build and validation pass` |
| Task 6 | `completed` | current | `codex` | Task 1, Task 2, Task 3, Task 4, Task 5 | `python scripts/validate_repo_contracts.py` | `90 passed; adapter drift, starter validation, repository contracts, and diff checks pass` |

Allowed states: `pending`, `active`, `blocked`, `completed`. Only one task may
be active because execution is sequential.

Plan lifecycle:

- Before execution authorization: `status: proposed`.
- After authorization, before activating Task 1: change status to `active`.
- During Tasks 1–5 and final verification: keep status `active`.
- After fresh final verification returns `verified`: change status to `completed`.

## Task Breakdown

### Task 1: Harden planning lifecycle validation

**Purpose:**
- Make plan execution fields executable contracts and remove duplicate active-task state.

**Task Function:**
- Implement parser-backed planning validation and update its regression tests.

**Template Profile:**
- Controller-selected: `none (lead controller)`
- Selection basis: bounded local parser and test changes with no external dependency.

**Validator Profile:**
- Controller-selected: `none`
- Selection basis: focused pytest proof is sufficient.

**Specification Coverage:**
- Validate `Mode`, `Coordination`, optional `Default task executor`, `Template Profile`, and `Validator Profile` values.
- Require the current execution contract only for `proposed` and `active` plans.
- Preserve completed and superseded historical plans; validate modern fields only when they exist.
- Parse global fields only inside `## Execution Approach` and task profiles only inside each `### Task N` section.
- Run Git coordination checks from parsed `Coordination` value.
- Remove legacy active-task summary because the task ledger owns active state.
- Include `low` in every profile enum.

**Required Skills:**
- `skill-code-standards`, `skill-test-driven-development`

**Files And Symbols:**
- Inspect and modify `scripts/validate_planning_lifecycle.py`: `validate_git_coordination`, `validate_artifact`, and new execution-approach parsing helpers.
- Modify `docs/operating_system/templates/implementation-plan-template.md`.
- Modify `tests/test_validate_planning_lifecycle.py` and `tests/test_native_personal_local_workflow.py`.
- Modify this plan file during self-migration from summary-based to ledger-only active state.

**Dependencies:**
- Base commit `a9bb93abcb34b7381dec16ec44746117c6aaf390` and clean workspace.

**Authority:**
- Preauthorized local actions: edit listed planning files and run focused pytest.
- Stop for: changed plan contract, unrelated planning artifacts, or required changes outside listed files.

**Steps:**
- [ ] Before activating Task 1, change this plan from `proposed` to `active`; keep its legacy coordination shape only until validator and template migration lands.
- [ ] Add section-aware parsers: global execution fields under `## Execution Approach`; task profiles under each `### Task N`.
- [ ] Apply required modern execution fields only to `proposed` and `active` plans; preserve completed and superseded historical plans without requiring newly introduced fields.
- [ ] For historical plans, validate modern fields when present and never infer active state from legacy summary text.
- [ ] Accept `inline sequential`, `subagent-ready`, and `parallel-capable` for `Mode`; accept `none` and `git-tracked` for `Coordination`; accept `codex`, `deepagents`, and `tura` for plan-level executor.
- [ ] Reuse `get_allowed_values(root, "executor", "plan")` for executor validation and derive profile names from existing role/schema ownership instead of adding a second permanent enum list.
- [ ] Validate task profiles as `none (lead controller)`, `low`, `normal`, `high`, or `xhigh`; validate optional validator profiles as `none`, `low`, `normal`, `high`, or `xhigh`.
- [ ] Select Git coordination validation from parsed `Coordination`, remove legacy summary requirements from validator/template, and migrate this plan in the same task.
- [ ] Add typo-bypass, section-scope, historical-plan, and self-migration tests.

**Verification:**
- [ ] `python -m pytest tests/test_validate_planning_lifecycle.py tests/test_native_personal_local_workflow.py -q`
- Expected: all focused tests pass, including malformed-value rejection and ledger-only active-state behavior.

**Exit Criteria:**
- Unknown execution values fail for current plans; historical completed/superseded plans remain valid; valid Git coordination retains current behavior; no legacy active-task summary references remain in maintained planning template/tests/validator paths or this plan.

### Task 2: Add shared-skill ownership markers

**Purpose:**
- Let deployments update and remove repo-owned skills while preserving unrelated user-owned skills.

**Task Function:**
- Implement marker-aware shared-skill reconciliation and migration behavior.

**Template Profile:**
- Controller-selected: `none (lead controller)`
- Selection basis: bounded filesystem reconciliation change with focused tests.

**Validator Profile:**
- Controller-selected: `none`
- Selection basis: deterministic temporary-directory tests cover ownership boundaries.

**Specification Coverage:**
- Use `.project-os-managed` as explicit destination ownership marker.
- Update marker-owned skills without routine `--force`.
- Preserve and refuse unmarked collisions.
- Remove marker-owned skills whose canonical source disappeared.
- Keep `--force` only as explicit legacy adoption path.

**Required Skills:**
- `skill-code-standards`, `skill-test-driven-development`

**Files And Symbols:**
- Inspect and modify `scripts/deploy_agent_runtime.py`: `_shared_skill_owned_files`, `_shared_skill_stale_files`, `_check_shared_skills`, `_plan_shared_skill_deploy`, and shared-skill deployment flow.
- Modify `tests/test_deploy_agent_runtime.py`.
- Modify `docs/operating_system/procedures/runtime-adapter-procedure.md`.

**Dependencies:**
- none; sequential mode controls scheduling.

**Authority:**
- Preauthorized local actions: edit listed files and run temporary-directory tests.
- Stop for: actual home-directory deployment, legacy adoption, or destructive cleanup.

**Steps:**
- [ ] Reserve `.project-os-managed` as JSON deployment metadata with `schema: 1`, resolved `source_root`, and `source_rel` fields; exclude it from source content comparisons.
- [ ] Treat a destination skill as owned only when marker identity matches the current repository root and `.agents/skills/<skill>` source path.
- [ ] Reconcile marker-owned files without `--force`; report unmarked name collisions without overwriting or deleting them.
- [ ] Auto-adopt an unmarked skill only when its content is byte-identical to the canonical source.
- [ ] Add dedicated `--adopt-shared-skill <name>` handling for intentional adoption of a differing legacy skill; do not reuse global `--force`, which also weakens provider runtime overwrite checks.
- [ ] Discover marker-owned destination skills independently of current source names so removed canonical skills can be deleted only by their owning repository.
- [ ] Add tests for update, source deletion, unmarked preservation, identical adoption, differing adoption refusal, dedicated adoption, cross-repository marker mismatch, and drift checking.

**Verification:**
- [ ] `python -m pytest tests/test_deploy_agent_runtime.py -q`
- Expected: all ownership, collision, migration, stale-file, and drift tests pass.

**Exit Criteria:**
- Repo-owned shared skills reconcile without `--force`; markers identify repository ownership; unmarked external skills remain untouched; source deletion removes only skills owned by the current repository.

### Task 3: Propagate all-platform repository drift checks

**Purpose:**
- Make repository contract validation cover every actual adapter mapping and documented runtime surface without changing direct local Codex defaults.

**Task Function:**
- Wire explicit all-platform selection through existing validators and tests.

**Template Profile:**
- Controller-selected: `none (lead controller)`
- Selection basis: small command-construction change using existing adapter discovery.

**Validator Profile:**
- Controller-selected: `none`
- Selection basis: command-list assertions plus focused pytest proof.

**Specification Coverage:**
- Repository validation invokes runtime drift with `--all-platforms --skip-deploy-check`.
- `validate_agent_runtime_drift.py --all-platforms` passes `--all-platforms` to sync.
- Direct validator default remains Codex-only.
- Explicit platform selection resolves against declared mapping platforms, including the existing `gemini`/`antigravity` alias.
- `runtime-surfaces.md` describes only outputs produced by current mappings and deployment code.
- Unconsumed stale `provider_capabilities.yaml` claims are retired rather than preserved as false capability metadata.

**Required Skills:**
- `skill-code-standards`, `skill-test-driven-development`

**Files And Symbols:**
- Modify `scripts/validate_agent_runtime_drift.py`: `main` command construction.
- Modify `scripts/validate_repo_contracts.py`: `build_subprocess_steps`.
- Modify `tests/test_validate_agent_runtime_drift.py` and `tests/test_validate_repo_contracts.py`.
- Modify `scripts/sync_agent_adapters.py`: mapping loading and explicit platform selection.
- Modify `tests/test_sync_agent_adapters.py`.
- Modify `docs/operating_system/runtime/runtime-surfaces.md`.
- Remove unconsumed `docs/operating_system/provider_capabilities.yaml` and remove it from `repo_config/starter-kit-manifest.json`.
- Modify `docs/operating_system/procedures/runtime-adapter-procedure.md` generated-drift commands.

**Dependencies:**
- none; existing adapter mapping files are the starting source of truth.

**Authority:**
- Preauthorized local actions: edit listed files and run focused validators/tests.
- Stop for: adding platform configuration, changing deploy target policy, or changing direct default behavior.

**Steps:**
- [ ] Append `--all-platforms` to the sync command only when runtime drift receives `--all-platforms`.
- [ ] Add `--all-platforms` to the repository contract validator's runtime drift step while retaining `--skip-deploy-check`.
- [ ] Load mapping metadata before filtering explicit platforms; match declared `platform` values and support the existing `gemini` alias for the declared `antigravity` mapping.
- [ ] Change repository-level documentation to use `python scripts/sync_agent_adapters.py --all-platforms --check`.
- [ ] Reconcile `docs/operating_system/runtime/runtime-surfaces.md` with outputs actually produced by mappings and deployment code; remove claims for unmapped rules, settings, and hooks.
- [ ] Delete unconsumed `docs/operating_system/provider_capabilities.yaml` and remove its starter-kit copy entry.
- [ ] Add tests proving propagation, direct Codex default selection, declared-platform filtering, and alias behavior.

**Verification:**
- [ ] `python -m pytest tests/test_validate_agent_runtime_drift.py tests/test_validate_repo_contracts.py -q`
- Expected: command construction includes all-platform sync for repository validation and direct default remains Codex-only.

**Exit Criteria:**
- `validate_repo_contracts.py` cannot certify generated adapter state after checking only Codex mappings; explicit platform selection follows declared mapping identity; runtime documentation matches executable outputs.

### Task 4: Correct canonical policy wording and regenerate projections

**Purpose:**
- Remove stale routing language and separate source authority from runtime precedence.

**Task Function:**
- Update canonical policy text, tests, and generated projections.

**Template Profile:**
- Controller-selected: `none (lead controller)`
- Selection basis: bounded documentation change with deterministic regeneration.

**Validator Profile:**
- Controller-selected: `none`
- Selection basis: existing text-contract tests and all-platform drift check.

**Specification Coverage:**
- Generic Impeccable fallback wording.
- Clear persistent-state ownership boundary.
- Separate accessibility routing from visual/UX design-skill routing.
- Wayfinding wording states `template-validated map`.
- Precedence document separates source authority and runtime delivery precedence.
- Generated projections remain derived outputs.

**Required Skills:**
- `skill-code-standards`

**Files And Symbols:**
- Modify `docs/operating_system/rules/frontend-ui-rule.md`.
- Modify `docs/operating_system/templates/agents/root-AGENTS.template.md`.
- Modify `docs/operating_system/planning/planning-dispatch.md`.
- Modify `docs/operating_system/governance/precedence.md`.
- Modify `docs/operating_system/governance/repo-governance.md` so private-factory and consume-only contexts are distinct and truthful.
- Modify `tests/test_native_personal_local_workflow.py`.
- Regenerate `AGENTS.md`, `.agents/rules/*`, `generated_agents/claude/CLAUDE.md`, and `generated_agents/antigravity/GEMINI.md` through the sync command.

**Dependencies:**
- Task 3 complete; canonical sources must change before generated projections.

**Authority:**
- Preauthorized local actions: edit canonical docs, regenerate projections, and run drift/text tests.
- Stop for: direct edits to generated projections, new design-system authority, or new persistent Impeccable state.

**Steps:**
- [ ] Replace the `ui-ux-pro-max`-specific fallback with generic selected-design-skill fallback wording.
- [ ] Prohibit persistent `PRODUCT.md`, `DESIGN.md`, and Impeccable-managed state unless separate ownership, lifecycle, and cleanup contracts exist.
- [ ] Distinguish material accessibility work routed through `frontend-ui-rule` from material visual/UX judgment routed through selected design skills.
- [ ] Change Wayfinding wording to `template-validated map`.
- [ ] Split `precedence.md` into source authority and runtime delivery precedence, then state generated conflict is drift.
- [ ] Make `repo-governance.md` dual-context truthful: private factory instructions remain private, while shipped consume-only guidance assigns downstream ownership to the adopted project.
- [ ] Regenerate all maintained projections.

**Verification:**
- [ ] `python scripts/sync_agent_adapters.py --all-platforms`
- [ ] `python scripts/sync_agent_adapters.py --all-platforms --check`
- [ ] `python -m pytest tests/test_native_personal_local_workflow.py -q`
- Expected: canonical wording tests pass and all generated projections report no drift.

**Exit Criteria:**
- Canonical docs contain no stale fallback or overstated validation language; generated projections match canonical sources.

### Task 5: Make consume-only starter output truthful

**Purpose:**
- Prevent exported starter repositories from instructing users to run omitted factory tooling or preserve factory-only ownership assumptions.

**Task Function:**
- Rewrite exported root instruction headers and remove validator exemptions.

**Template Profile:**
- Controller-selected: `none (lead controller)`
- Selection basis: bounded export transformation with temporary fixture tests.

**Validator Profile:**
- Controller-selected: `none`
- Selection basis: starter build and content-scan tests provide direct proof.

**Specification Coverage:**
- Rewrite exported `AGENTS.md`, `CLAUDE.md`, and `GEMINI.md` headers as consume-only instructions.
- Preserve instruction bodies.
- Omit factory-only starter build instructions and root templates from consume-only output.
- Reject factory commands, generated-export maintenance instructions, and source-only adapter references across shipped starter docs and skills.
- Keep factory scripts and adapter directories forbidden.

**Required Skills:**
- `skill-code-standards`, `skill-test-driven-development`

**Files And Symbols:**
- Modify `scripts/build_starter_kit.py`: `build_starter_kit` and new root-instruction rewrite helper.
- Modify `scripts/validate_starter_kit.py`: `_scan_forbidden_content` exemptions.
- Modify `tests/test_starter_kit_generation.py`.
- Modify `repo_config/starter-kit-manifest.json`: omit `docs/operating_system/procedures/starter-kit-procedure.md`, `docs/operating_system/templates/agents/root-AGENTS.template.md`, and retired `docs/operating_system/provider_capabilities.yaml`.
- Modify `docs/operating_system/governance/repo-governance.md` through Task 4 so the required shipped governance document is truthful in both contexts.

**Dependencies:**
- Task 4 complete so exported root files and shipped governance docs contain current canonical wording.

**Authority:**
- Preauthorized local actions: edit listed starter scripts/tests and build temporary starter output.
- Stop for: copying factory tooling, changing starter distribution scope, or deleting source files.

**Steps:**
- [x] Strip factory generated headers from exported root instruction files only.
- [x] Add one truthful consume-only header stating origin, absent adapter tooling, and direct-edit ownership.
- [x] Preserve copied instruction bodies byte-for-byte after header replacement.
- [x] Remove header-specific exemptions from starter forbidden-content validation.
- [x] Add forbidden-content checks for `scripts/build_starter_kit.py`, `scripts/validate_starter_kit.py`, `scripts/deploy_agent_runtime.py`, `scripts/sync_agent_adapters.py`, and `generated_exports/project-OS-starter-kit` in shipped human-facing content.
- [x] Add tests for rewritten headers, preserved bodies, omitted factory-only docs/templates, forbidden script references, and existing path exclusions.

**Verification:**
- [x] `python -m pytest tests/test_starter_kit_generation.py -q`
- [x] `python scripts/build_starter_kit.py`
- [x] `python scripts/validate_starter_kit.py`
- Expected: starter build and validation pass; root files contain no impossible sync command or factory path reference.

**Exit Criteria:**
- Consume-only starter output is self-contained and truthful across root instructions, shipped docs, and skills without shipping adapter-generation machinery or factory-only runbooks.

### Task 6: Run final integration verification

**Purpose:**
- Prove cross-task consistency and identify unrelated failures without changing unrelated code.

**Task Function:**
- Execute final generated-surface, focused-regression, and repository-contract checks.

**Template Profile:**
- Controller-selected: `none (lead controller)`
- Selection basis: verification-only task using existing commands.

**Validator Profile:**
- Controller-selected: `none`
- Selection basis: final verification skill owns acceptance review.

**Specification Coverage:**
- All implementation outcomes and task-local proof requirements.

**Required Skills:**
- `skill-verification-before-completion`

**Files And Symbols:**
- Verify all files changed by Tasks 1–5.
- Verify generated projections and starter output using existing repository commands.

**Dependencies:**
- Tasks 1–5 completed with accepted task-local proof.

**Authority:**
- Preauthorized local actions: read-only validation, tests, generated drift checks, and starter-kit validation.
- Stop for: unrelated test failures, changed base ancestry, unexpected files, or unresolved generated drift.

**Steps:**
- [x] Run all-platform generated adapter drift check.
- [x] Run focused regression suite covering planning, deployment, runtime drift, starter export, repository contracts, and documentation contracts.
- [x] Run full repository contract validation.
- [x] Review `git diff --check`, changed-file list, and generated-surface ownership.
- [x] Confirm plan status is `active` during execution and do not transition to `completed` until verification skill returns `verified`.

**Verification:**
- [x] `python scripts/sync_agent_adapters.py --all-platforms --check`
- [x] `python -m pytest tests/test_validate_planning_lifecycle.py tests/test_deploy_agent_runtime.py tests/test_validate_agent_runtime_drift.py tests/test_sync_agent_adapters.py tests/test_starter_kit_generation.py tests/test_validate_repo_contracts.py tests/test_native_personal_local_workflow.py -q`
- [x] `python scripts/build_starter_kit.py`
- [x] `python scripts/validate_starter_kit.py`
- [x] `python scripts/validate_repo_contracts.py`
- [x] `git diff --check`
- [x] `git diff --name-only`
- Expected: commands pass, no generated drift remains, and only declared files changed.

**Exit Criteria:**
- Every justified issue has executable proof, generated outputs reconcile, full repository validation passes, and no unrelated architecture change is included.

## Verification

Task-local proof runs after each task. Final proof runs only after Tasks 1–5
pass. Final verification rebuilds and validates the starter output freshly.
Existing Switchyard checks remain part of `validate_repo_contracts.py` and must
remain green; no Switchyard policy changes belong to this plan.

## Completion Criteria

- Planning validator rejects typo-based lifecycle bypasses.
- Historical completed and superseded plans remain valid evidence.
- Task ledger is sole active-task source of truth.
- Source-identified marker-owned shared skills update and delete safely; unmarked skills remain untouched.
- Repository contract validation checks all adapter mappings and runtime-surface claims.
- Starter output contains no impossible factory regeneration instruction or factory-only runbook.
- Canonical wording and generated projections reconcile.
- Plan lifecycle follows `proposed → active → completed` only after fresh verified proof.
- Focused and full validation commands, starter rebuild, and starter validation pass.
