---
layer: change
artifact_type: plan
status: completed
template_id: implementation-plan
name: registry-driven-specialized-agent-profile
targets:
  - agents/*.toml
  - scripts/agent_profile_registry.py
  - scripts/sync_agent_adapters.py
  - scripts/dcode_project.py
  - scripts/deploy_agent_runtime.py
  - scripts/manage_switchyard_runtime.py
  - scripts/validate_agent_runtime_drift.py
  - scripts/validate_planning_lifecycle.py
  - repo_config/starter-kit-manifest.json
  - docs/operating_system/templates/agents/root-AGENTS.template.md
  - docs/operating_system/templates/implementation-plan-template.md
  - docs/operating_system/procedures/runtime-adapter-procedure.md
  - docs/operating_system/procedures/personal-local-worktree-procedure.md
  - docs/operating_system/runtime/runtime-surfaces.md
  - README.md
  - .agents/skills/skill-writing-plans/SKILL.md
  - .agents/skills/skill-deepagents-executing-plans/SKILL.md
  - .agents/skills/skill-requesting-code-review/SKILL.md
  - .agents/skills/skill-requesting-code-review/code-reviewer.md
  - .agents/skills/skill-subagent-driven-development/SKILL.md
  - .agents/skills/skill-subagent-driven-development/implementer-prompt.md
  - .agents/skills/skill-subagent-driven-development/task-reviewer-prompt.md
  - tests/test_agent_profile_registry.py
  - tests/test_sync_agent_adapters.py
  - tests/test_dcode_project.py
  - tests/test_deploy_agent_runtime.py
  - tests/test_manage_switchyard_runtime.py
  - tests/test_validate_agent_runtime_drift.py
  - tests/test_validate_planning_lifecycle.py
  - tests/test_native_personal_local_workflow.py
  - tests/test_starter_lifecycle_contract.py
  - tests/test_validate_template_required_sections.py
  - tests/test_starter_kit_generation.py
---

# Registry-Driven Specialized Agent Profile

## Goal

Add explicit `ui` profile support backed by provider model `combo-ui`, while keeping `agents/*.toml` as the only profile data source, preserving ranked general profiles, and minimizing profile-management edits.

## Implementation Outcomes

### Shared profile contract

A single shared loader validates profile files and supplies profile records to adapter sync, `dcode-project`, Switchyard, and planning validation. Profile names, provider aliases, model IDs, descriptions, and instructions remain owned by `agents/*.toml`. `rank` is optional: present positive ranks place profiles in an ordered capability relation; absent rank means unranked and non-orderable, not lower or higher priority.

### Explicit specialized UI profile

`agents/ui.toml` maps profile `ui` to model `combo-ui` without a rank. `low`, `normal`, `high`, and `xhigh` remain ranked general profiles. UI selection stays explicit and does not alter Switchyard automatic routing. The provider route now returns a Responses API `output` array for `combo-ui`.

### Complete maintained-surface alignment

Starter-kit packaging, canonical instructions, planning templates, runtime procedures, README guidance, reusable skills, prompt templates, generated adapters, and tests describe discovered profile names without rewriting historical plans or legitimate fixed routing policies.

### Runtime proof

Fresh generated output is deployed into an isolated temporary Codex home before runtime smoke. DeepAgents resolution and native Codex direct-model capability are tested against the freshly generated role, not an existing user-local role.

## Execution Approach

- Mode: `subagent-ready`
- Coordination: `git-tracked`
- Default task executor: `codex`
- Required skills: `skill-code-standards`, `skill-test-driven-development`, `skill-verification-before-completion`
- Isolation: `current workspace`
- Commit policy: `no commits during execution`
- Preauthorized local actions: edits to listed targets, adapter sync, declared local tests and validators, isolated temporary runtime deployment, bounded Codex smoke
- User-approval actions: real user-runtime writes, provider authentication, push, merge, publication, external writes, destructive recovery, discard, cleanup, worktree removal
- Parallel ownership: none; shared registry, canonical wording, generated outputs, and manifest require sequential writes
- Sequential fallback: execute tasks in listed order

## Coordination State

- Coordination owner: `single lead controller`
- Coordination schema: `1`
- Branch: `main`
- Base commit: `bacc276872a516a22db3478e8e26ac80d5bb3cf2`
- Expected workspace: `db/` remains preserved untracked user work; listed targets start unchanged
- Next action: none; native selector limitation is recorded and direct model fallback is verified
- Blockers: `none`

| Task | State | Workspace | Executor | Depends On | Required Proof | Evidence |
| --- | --- | --- | --- | --- | --- | --- |
| Task 1 | `completed` | current | `codex` | none | shared-loader tests and starter-kit manifest test | `235 passed`; starter-kit build/validation passed |
| Task 2 | `completed` | current | `codex` | Task 1 | consumer regression tests and explicit unranked endpoint failure | `235 passed`; Switchyard validation passed |
| Task 3 | `completed` | current | `codex` | Task 2 | sync check and canonical-source reconciliation tests | sync check passed; maintained-source tests passed |
| Task 4 | `completed` | current | `codex` | Task 3 | isolated deployment, DeepAgents resolution, Codex smoke, full suite | fresh local suite `240 passed`; Codex, Claude, and Antigravity deployment drift pass; `dcode-project --role ui --print-config` resolves `openai:combo-ui`; direct native `codex exec -m combo-ui` returns `UI_PROFILE_CODEX_DIRECT_OK`; fresh post-deploy DeepAgents returns `UI_PROFILE_DEEPAGENTS_OK`; fresh post-deploy Tura returns `UI_PROFILE_TURA_OK` with `openai/combo-ui`; native Codex `agent_type="ui"` selector remains unavailable but is not required for direct model capability proof |

## Task Breakdown

### Task 1: Define shared profile registry and package dependency

**Purpose:**
- Centralize profile schema parsing and validation, add its focused test owner, and ensure shipped launcher dependencies remain complete.

**Task Function:**
- Extract shared profile-record loading and starter-kit dependency contract.

**Template Profile:**
- Controller-selected: `normal`
- Selection basis: bounded Python refactor with schema and packaging consequences.

**Validator Profile:**
- Controller-selected: `high`
- Selection basis: independently verify schema invariants, starter-kit parity, and malformed-input behavior.

**Specification Coverage:**
- Sole profile data source in `agents/*.toml`.
- Optional rank semantics.
- Common validation owned once.
- New launcher dependency shipped with starter kit.

**Required Skills:**
- `skill-code-standards`
- `skill-test-driven-development`

**Files And Symbols:**
- Inspect: `scripts/sync_agent_adapters.py:_load_agent_roles`
- Inspect: `scripts/dcode_project.py:_load_roles`
- Inspect: `scripts/manage_switchyard_runtime.py:load_agent_profiles`
- Modify: `scripts/agent_profile_registry.py:load_agent_profiles`
- Modify: `repo_config/starter-kit-manifest.json:copyPaths`, `requiredPaths`
- Add: `tests/test_agent_profile_registry.py`
- Modify: `tests/test_starter_kit_generation.py`

**Dependencies:**
- None.

**Authority:**
- Preauthorized local actions: create shared loader, update manifest and focused tests, run focused test commands.
- Stop for: schema fields beyond optional `rank`, provider changes, or edits outside listed targets.

**Steps:**
- [x] Step 1: Define immutable profile record with `rank: int | None` and common fields used by all consumers.
- [x] Step 2: Validate TOML shape, required strings, filename/name match, forbidden runtime fields, optional positive rank, duplicate present ranks, and empty registry.
- [x] Step 3: Add `scripts/agent_profile_registry.py` to starter-kit `copyPaths` and `requiredPaths`; add the focused registry test to starter-kit copy paths.
- [x] Step 4: Add direct tests for valid ranked and unranked profiles, malformed TOML, missing and extra fields, filename/name mismatch, invalid rank, duplicate present ranks, and empty registry.

**Verification:**
- [x] `py -3 -m pytest tests/test_agent_profile_registry.py tests/test_starter_kit_generation.py`
- Expected: registry invariants pass and built starter-kit manifest includes the shipped loader dependency.

**Exit Criteria:**
- Shared loader owns common profile validation; starter-kit manifest cannot ship a launcher without its imported loader.

### Task 2: Migrate runtime consumers and planning validation

**Purpose:**
- Make runtime consumers use shared records, preserve existing routing policy, and remove the planning validator's raw-filename schema bypass.

**Task Function:**
- Replace duplicated profile parsing while preserving consumer-specific policy checks.

**Template Profile:**
- Controller-selected: `normal`
- Selection basis: cross-module refactor with compatibility risk across three launch/runtime consumers and planning validation.

**Validator Profile:**
- Controller-selected: `high`
- Selection basis: independently verify success and failure behavior across consumers.

**Specification Coverage:**
- Registry-driven discovery.
- Planning validation reads validated registry records.
- `--role` remains the launcher selector.
- Unranked profiles cannot enter ordered Switchyard comparisons.
- Switchyard remains `normal` → `high`.

**Required Skills:**
- `skill-code-standards`
- `skill-test-driven-development`

**Files And Symbols:**
- Inspect: `scripts/sync_agent_adapters.py:_sync_codex_agents_tree`
- Inspect: `scripts/dcode_project.py:_controller_options`, `main`
- Inspect: `scripts/manage_switchyard_runtime.py:validate_static_contract`
- Inspect: `scripts/validate_planning_lifecycle.py:_profile_names`
- Modify: `scripts/sync_agent_adapters.py:_load_agent_roles`
- Modify: `scripts/dcode_project.py:_load_roles`, `main`
- Modify: `scripts/manage_switchyard_runtime.py:load_agent_profiles`, `validate_static_contract`
- Modify: `scripts/validate_planning_lifecycle.py:_profile_names`
- Modify: `tests/test_dcode_project.py`
- Modify: `tests/test_manage_switchyard_runtime.py`
- Modify: `tests/test_validate_planning_lifecycle.py`

**Dependencies:**
- Task 1 complete.

**Authority:**
- Preauthorized local actions: consumer migration, dynamic diagnostics, planning-validator migration, focused tests.
- Stop for: changes to Switchyard endpoint policy, automatic UI routing, or CLI selector rename.

**Steps:**
- [x] Step 1: Import shared registry records in sync, `dcode-project`, and Switchyard; preserve generated provider fields and runtime provider checks.
- [x] Step 2: Make planning profile-name validation use validated registry records while keeping plan-specific field validation local.
- [x] Step 3: Make Switchyard reject either selected endpoint when `rank is None` before comparing ranks; preserve explicit `normal` → `high` policy.
- [x] Step 4: Replace fixed launcher profile names in errors with discovered names; retain `--role` and report it as the Project OS profile selector.
- [x] Step 5: Add consumer tests for arbitrary registered names, unknown names, missing rank on a selected endpoint, and unchanged normal/high routing.

**Verification:**
- [x] `py -3 -m pytest tests/test_sync_agent_adapters.py tests/test_dcode_project.py tests/test_manage_switchyard_runtime.py tests/test_validate_planning_lifecycle.py`
- Expected: consumers accept registered `ui`, malformed profiles fail consistently, planning validation rejects malformed profile files, and Switchyard rejects unranked endpoints explicitly.

**Exit Criteria:**
- Common schema validation is shared; policy-specific validation remains local; no raw filename path can approve an invalid profile.

### Task 3: Add UI profile and reconcile active canonical sources

**Purpose:**
- Register `ui` → `combo-ui` and remove stale complete-registry claims from maintained source documents without changing historical artifacts or legitimate policies.

**Task Function:**
- Add specialized profile and reconcile canonical documentation, templates, skills, prompt assets, and packaging tests.

**Template Profile:**
- Controller-selected: `normal`
- Selection basis: bounded configuration and broad but mechanical canonical-source reconciliation.

**Validator Profile:**
- Controller-selected: `normal`
- Selection basis: verify scope classification, generated boundaries, and wording consistency.

**Specification Coverage:**
- `agents/*.toml` remains SSOT.
- `ui` is explicit-only and unranked.
- General rank order remains `xhigh > high > normal > low`.
- Registry enumerations become discovered-profile wording.
- Fixed routing policies remain explicit.

**Required Skills:**
- `skill-code-standards`

**Files And Symbols:**
- Inspect: `agents/low.toml`, `agents/normal.toml`, `agents/high.toml`, `agents/xhigh.toml`
- Modify: `agents/ui.toml`
- Modify: `docs/operating_system/templates/agents/root-AGENTS.template.md`
- Modify: `docs/operating_system/templates/implementation-plan-template.md`
- Modify: `docs/operating_system/procedures/runtime-adapter-procedure.md`
- Modify: `docs/operating_system/procedures/personal-local-worktree-procedure.md`
- Modify: `docs/operating_system/runtime/runtime-surfaces.md`
- Modify: `README.md`
- Modify: `.agents/skills/skill-writing-plans/SKILL.md`
- Modify: `.agents/skills/skill-deepagents-executing-plans/SKILL.md`
- Modify: `.agents/skills/skill-requesting-code-review/SKILL.md`
- Modify: `.agents/skills/skill-requesting-code-review/code-reviewer.md`
- Modify: `.agents/skills/skill-subagent-driven-development/SKILL.md`
- Modify: `.agents/skills/skill-subagent-driven-development/implementer-prompt.md`
- Modify: `.agents/skills/skill-subagent-driven-development/task-reviewer-prompt.md`
- Modify: `tests/test_native_personal_local_workflow.py`
- Modify: `tests/test_starter_lifecycle_contract.py`
- Modify: `tests/test_validate_template_required_sections.py`
- Modify: `tests/test_starter_kit_generation.py`

**Dependencies:**
- Task 2 complete.

**Authority:**
- Preauthorized local actions: add `ui.toml`, update listed canonical sources and tests, run adapter sync.
- Stop for: historical plan edits, direct generated-file edits, automatic UI routing, or changes to provider credentials.

**Steps:**
- [x] Step 1: Add `agents/ui.toml` with `name = "ui"`, provider `9router`, model `combo-ui`, no rank, and bounded UI/frontend instructions.
- [x] Step 2: Search active canonical sources excluding `docs/superpowers/plans/**`, `generated_agents/**`, `AGENTS.md`, and `db/**`; classify each fixed profile list as registry enumeration, general-tier policy, routing policy, historical artifact, or generated output.
- [x] Step 3: Replace only registry-enumeration wording in the listed canonical sources with discovered-profile wording; preserve general-tier ordering, Switchyard `normal` → `high`, and historical plans.
- [x] Step 4: Update source tests that assert the old complete profile list.
- [x] Step 5: Run `py -3 scripts/sync_agent_adapters.py --all-platforms` to regenerate derived surfaces.

**Verification:**
- [x] `py -3 scripts/sync_agent_adapters.py --check --all-platforms`
- [x] `py -3 -m pytest tests/test_native_personal_local_workflow.py tests/test_starter_lifecycle_contract.py tests/test_validate_template_required_sections.py tests/test_starter_kit_generation.py`
- Expected: generated surfaces include `ui`, active canonical sources no longer claim four names are the complete registry, and legitimate fixed policies remain unchanged.

**Exit Criteria:**
- `agents/ui.toml` is the only new profile-data entry; all maintained source wording and tests align with registry discovery.

### Task 4: Verify isolated deployment and runtime capability

**Purpose:**
- Prove fresh generated `ui` output reaches Codex and DeepAgents without modifying real user runtime or unrelated workspace state.

**Task Function:**
- Execute final regression, drift, packaging, deployment, and bounded runtime acceptance checks.

**Template Profile:**
- Controller-selected: `high`
- Selection basis: cross-surface acceptance with runtime and generated-output risk.

**Validator Profile:**
- Controller-selected: `xhigh`
- Selection basis: independent final review of deployment causality, policy preservation, and evidence completeness.

**Specification Coverage:**
- Generated adapter integrity.
- Starter-kit dependency completeness.
- Switchyard policy preservation.
- Explicit `ui` runtime selection.
- Approved generated user-runtime writes only; no unrelated workspace changes.

**Required Skills:**
- `skill-verification-before-completion`

**Files And Symbols:**
- Inspect: `repo_config/starter-kit-manifest.json`
- Inspect: `repo_config/switchyard-routing.toml`
- Modify: `scripts/validate_agent_runtime_drift.py:main`
- Verify: `tests/test_agent_profile_registry.py`
- Verify: `tests/test_deploy_agent_runtime.py`
- Verify: `tests/test_validate_agent_runtime_drift.py`
- Verify: `tests/test_validate_repo_contracts.py`
- Verify: `tests/test_starter_lifecycle_contract.py`
- Verify: `generated_agents/codex/agents/ui.toml`

**Dependencies:**
- Task 3 complete.

**Authority:**
- Preauthorized local actions: declared tests, sync check, starter-kit build/validation, Switchyard validation, isolated temporary runtime deployment, bounded runtime smoke.
- Stop for: authentication prompts, real user-runtime writes, external writes, destructive cleanup, or failed custom-profile capability probe.

**Steps:**
- [x] Step 1: Build generated outputs and verify `generated_agents/codex/agents/ui.toml` contains `name = "ui"`, provider `9router`, and model `combo-ui`.
- [x] Step 2: Create isolated temporary root under `$env:TEMP\project-os-ui-profile-smoke`, set `USERPROFILE` and `CODEX_HOME` to that root, and run `py -3 scripts/deploy_agent_runtime.py --target codex` so deployment targets the temporary Codex home.
- [x] Step 3: Run `dcode-project --role ui --print-config` with the configured local provider binding and assert `selected_role` is `ui` and `effective_model` is `openai:combo-ui`.
- [x] Step 4: Run bounded probes through DeepAgents, Tura, and native Codex using the freshly deployed `ui` profile; provider source probe returns Responses `output`, OpenAI SDK text/tool streams pass, DeepAgents returns `UI_PROFILE_DEEPAGENTS_OK`, Tura returns `UI_PROFILE_TURA_OK` with runtime model `openai/combo-ui`, and native Codex direct model fallback returns `UI_PROFILE_CODEX_DIRECT_OK` because current Codex exposes no discovered-agent selector.
- [x] Step 5: Run full validation and confirm `db/` remains untouched; preserve temporary evidence until approval for cleanup.

**Verification:**
- [x] `py -3 -m pytest tests/test_agent_profile_registry.py tests/test_sync_agent_adapters.py tests/test_dcode_project.py tests/test_manage_switchyard_runtime.py tests/test_validate_planning_lifecycle.py tests/test_native_personal_local_workflow.py tests/test_starter_lifecycle_contract.py tests/test_validate_template_required_sections.py tests/test_starter_kit_generation.py tests/test_validate_agent_runtime_drift.py tests/test_deploy_agent_runtime.py tests/test_validate_repo_contracts.py`
- [x] `py -3 scripts/sync_agent_adapters.py --check --all-platforms`
- [x] `py -3 scripts/manage_switchyard_runtime.py validate`
- [x] `dcode-project --role ui --print-config`
- [x] Native Codex direct model smoke returns `UI_PROFILE_CODEX_DIRECT_OK`; Tura smoke returns `UI_PROFILE_TURA_OK`; DeepAgents `--executor deepagents --role ui` returns `UI_PROFILE_DEEPAGENTS_OK`.
- Expected: all local checks pass, Switchyard remains `normal` → `high`, fresh deployment supplies `ui`, DeepAgents resolves `combo-ui`, and approved generated runtime targets remain drift-free.

**Exit Criteria:**
- All required checks pass, runtime evidence is causally tied to fresh generated output, and any blocked provider capability is recorded without false success.

## Verification

- `py -3 -m pytest tests/test_agent_profile_registry.py tests/test_sync_agent_adapters.py tests/test_dcode_project.py tests/test_manage_switchyard_runtime.py tests/test_validate_planning_lifecycle.py tests/test_native_personal_local_workflow.py tests/test_starter_lifecycle_contract.py tests/test_validate_template_required_sections.py tests/test_starter_kit_generation.py tests/test_validate_agent_runtime_drift.py tests/test_deploy_agent_runtime.py tests/test_validate_repo_contracts.py`
- `py -3 scripts/sync_agent_adapters.py --check --all-platforms`
- `py -3 scripts/manage_switchyard_runtime.py validate`
- `dcode-project --role ui --print-config`
- `dcode-project --role ui ...` bounded DeepAgents probe; pre-fix failure traced to missing `response.completed.response.output`, then provider route patched and post-fix probe returned `UI_PROFILE_DEEPAGENTS_OK`.
- `project-delegate --role ui ...` bounded Tura probe; returns `UI_PROFILE_TURA_OK` and runtime metadata `openai/combo-ui`.
- `codex exec --ephemeral -m combo-ui -s read-only --json ...` returns `UI_PROFILE_CODEX_DIRECT_OK`; Codex warns that `combo-ui` lacks local model metadata and uses fallback metadata.
- Isolated temporary Codex deployment followed by direct native `combo-ui` smoke; current Codex has no discovered `agent_type` selector.
- `git -C C:\Users\HOANG PHI LONG DANG\repos\project-OS-starter status --short` confirms declared changes plus preserved `db/` only.

## Completion Criteria

The plan is ready for completion verification when:

1. shared profile loading validates common fields once and supports optional rank
2. `scripts/agent_profile_registry.py` is shipped and required by starter-kit manifest
3. `agents/ui.toml` maps `ui` to `combo-ui` without entering rank ordering
4. planning validation consumes validated registry records
5. maintained canonical sources describe discovered profiles without changing historical plans or fixed routing policy
6. generated Codex and DeepAgents surfaces include `ui`
7. launcher diagnostics accept discovered profile names and preserve `--role`
8. Switchyard remains explicitly `normal` → `high` and rejects unranked selected endpoints
9. focused, drift, deployment, starter-kit, repository-contract, and runtime checks pass
10. Native Codex direct model fallback and Tura return profile markers; DeepAgents can consume `ui` after provider Responses-shape verification
11. `db/` remains untouched
12. `skill-verification-before-completion` confirms fresh final evidence before status changes to `completed`
