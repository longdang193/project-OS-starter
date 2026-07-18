---
layer: operating_system
artifact_type: plan
status: completed
template_id: implementation-plan
name: intent-to-execution-simplification
targets:
  - docs/intent/
  - docs/superpowers/
  - docs/operating_system/
  - .agents/skills/
  - repo_config/planning_artifact_schema.yaml
  - repo_config/starter-kit-manifest.json
  - scripts/
  - tests/
---

# Intent-To-Execution Simplification Plan

## Goal

Replace the document-heavy planning ladder with an adaptive intent-to-execution
model for personal projects:

`intent -> clarify only when needed -> plan only when needed -> execute -> verify -> finish`

Keep roadmap use optional. Remove execution maps, bounded change threads,
checkpoint result packs, spec-set and spec-authoring-map expectations, and
validator rules that force documents to exist only to connect other documents.

## Key Deliverables

### Adaptive Artifact Ownership

- intent may live in an approved user request, issue, optional roadmap item, or short approved scope
- brainstorming owns unresolved options and is saved only when requested
- specifications own durable behavior, interfaces, design decisions, invariants, acceptance criteria, and validation intent when needed
- implementation plans own ordered tasks, dependencies, execution approach, parallel-safe lanes, shared-write controls, required skills, exact targets, verification, and exit criteria when needed
- execution, verification, and authorized Git disposition remain owned by their existing skills
- code, configuration, tests, and validators remain executable truth

### Optional Roadmap

- `docs/intent/master-workstream-roadmap.md` remains available as an optional multi-outcome planning surface
- roadmap absence does not fail repository validation
- roadmap items do not require workstream, thread, checkpoint, spec, or plan children
- useful current intent from active workstream material is folded into the roadmap before obsolete registries are removed

### Removed Planning Layers

- no execution-map artifact, folder, schema, validator, test, prompt routing, starter-kit entry, or active governance reference remains
- no bounded-change-thread artifact, folder, schema, validator, test, or checkpoint requirement remains
- no checkpoint-result-pack template, validator, contract-runner entry, or active output folder remains
- no active spec-set or spec-authoring-map lifecycle expectation remains
- historical completed plans remain unchanged as evidence

### Lean Validation

- validators validate planning artifacts that exist instead of requiring an artifact ladder
- optional references such as `parent_spec` are checked only when present
- active specs and plans retain metadata and required-section validation
- completion proof remains evidence-based without child-artifact terminality

## Task/Wave Breakdown

### Task 1: Define The Lean Planning Contract

**Purpose:**
- establish one canonical adaptive route and artifact ownership model before deleting dependent surfaces

**Files:**
- Modify: `docs/operating_system/governance/repo-governance.md`
- Modify: `docs/operating_system/planning/planning-dispatch.md`
- Modify: `docs/operating_system/rules/doc-contracts-rule.md`
- Modify: `docs/operating_system/workflows/`
- Verify: `docs/operating_system/prompt_templates/task-intake-prompt.md`

**Preconditions:**
- approved ownership model and optional-roadmap decision remain unchanged

**Steps:**
- [x] Replace the artifact ladder with conditional routes for direct change, brainstorming, specification, implementation planning, execution, verification, and authorized branch finishing.
- [x] State that no artifact is required merely to connect two other artifacts.
- [x] Assign cross-task ordering, parallel lanes, shared-write ownership, and required execution skills to implementation plans.
- [x] Make roadmap use conditional on several coordinated outcomes rather than a repository prerequisite.
- [x] Remove execution-map, bounded-thread, checkpoint-pack, spec-set, and spec-authoring-map ownership language from active governance and workflows.

**Verification:**
- [x] `rg -n -i "execution[_ -]?map|bounded change thread|checkpoint result pack|complete spec set|spec-authoring map" docs/operating_system --glob '!**/historical/**'`
- [x] Inspect planning dispatch and governance together for one consistent ownership table.

**Exit Criteria:**
- one canonical adaptive planning contract exists without a mandatory document ladder

### Task 2: Align Planning And Delivery Skills

**Purpose:**
- make reusable methods follow the lean contract without losing substantive brainstorming, specification, planning, execution, or verification guidance

**Files:**
- Modify: `.agents/skills/skill-brainstorming/SKILL.md`
- Modify: `.agents/skills/skill-spec-drafting/SKILL.md`
- Modify: `.agents/skills/skill-writing-plans/SKILL.md`
- Modify: `.agents/skills/skill-plan-document-reviewer/SKILL.md`
- Inspect: `.agents/skills/skill-executing-plans/SKILL.md`
- Inspect: `.agents/skills/skill-parallel-execution/SKILL.md`
- Inspect: `.agents/skills/skill-verification-before-completion/SKILL.md`
- Inspect: `.agents/skills/skill-finishing-a-development-branch/SKILL.md`

**Preconditions:**
- Task 1 ownership boundaries are canonical

**Steps:**
- [x] Remove execution-map output paths, handoffs, review checks, and routing.
- [x] Remove bounded-thread and checkpoint assumptions from skill inputs, metadata guidance, handoffs, and completion language.
- [x] Make `skill-writing-plans` own execution approach, required skills, dependency ordering, task right-sizing, parallel-safe lanes, and shared-file serialization.
- [x] Allow direct approved scope to enter execution without manufacturing a spec or plan when work is local, clear, and reversible.
- [x] Preserve the existing execution-to-verification-to-finishing skill boundary and explicit authorization gates.

**Verification:**
- [x] `python scripts/validate_skill_metadata.py`
- [x] `rg -n -i "execution[_ -]?map|bounded change thread|checkpoint result pack|parent_thread" .agents/skills`

**Exit Criteria:**
- planning and delivery skills support direct, spec-led, and plan-led execution without obsolete intermediate artifacts

### Task 3: Simplify Templates And Prompts

**Purpose:**
- remove obsolete lifecycle wording while preserving useful artifact formats and reusable invocation language

**Files:**
- Modify: `docs/operating_system/templates/implementation-plan-template.md`
- Modify: `docs/operating_system/templates/detailed-specification-template.md`
- Delete: `docs/operating_system/templates/checkpoint-result-pack.md`
- Modify: `docs/operating_system/prompt_templates/implementation-plan-prompt.md`
- Modify: `docs/operating_system/prompt_templates/task-intake-prompt.md`
- Inspect: `docs/operating_system/prompt_templates/`
- Verify: `scripts/validate_template_required_sections.py`

**Preconditions:**
- Task 2 defines final skill handoffs and plan ownership

**Steps:**
- [x] Remove execution-map and bounded-thread inputs from planning prompts.
- [x] Replace plan completion rules based on child-artifact terminality with implementation outcomes, completed required tasks, and fresh verification.
- [x] Remove checkpoint-result-pack creation guidance and template.
- [x] Keep specification and plan templates focused on their owned content; do not add a replacement lineage section.
- [x] Remove template-validator discovery for deleted artifact folders while retaining spec, plan, and optional-roadmap validation when those files exist.

**Verification:**
- [x] `python -m pytest -q tests/test_validate_template_required_sections.py`
- [x] `python scripts/validate_template_required_sections.py`
- [x] `python scripts/validate_prompt_metadata.py`

**Exit Criteria:**
- active templates and prompts contain no obsolete planning-layer dependency

### Task 4: Migrate Useful Intent And Remove Registries

**Purpose:**
- preserve useful current intent while deleting thread, checkpoint, execution-map, and mandatory workstream administration

**Files:**
- Modify: `docs/intent/master-workstream-roadmap.md`
- Delete: `docs/intent/workstreams/threads/`
- Delete: `docs/intent/workstreams/checkpoints/`
- Delete: `docs/superpowers/execution_maps/`
- Inspect: `docs/intent/workstreams/starter-adoption-experience.md`
- Inspect: `docs/intent/workstreams/README.md`
- Inspect: `docs/intent/workstream-coverage-and-progress-guide.md`

**Preconditions:**
- Tasks 1 through 3 establish replacement ownership and wording

**Steps:**
- [x] Extract only still-useful open or durable intent from current workstream and thread files into concise optional-roadmap items.
- [x] Do not copy completed thread narration or checkpoint proof into the roadmap; Git history and historical plans remain evidence.
- [x] Simplify or delete the workstream registry and coverage guide according to whether they retain unique roadmap value after thread removal.
- [x] Delete bounded-thread, checkpoint, and execution-map directories after useful current intent is preserved.
- [x] Remove absolute local filesystem links from any retained intent document.

**Verification:**
- [x] `rg -n -i "workstreams/threads|workstreams/checkpoints|execution_maps|checkpoint-result-pack" docs/intent docs/superpowers --glob '!docs/superpowers/plans/**'`
- [x] Inspect optional roadmap for concise outcomes without child-artifact completion requirements.

**Exit Criteria:**
- optional roadmap preserves useful intent; obsolete registries and result packs are gone

### Task 5: Reduce Planning Schema And Lifecycle Validation

**Purpose:**
- make executable validation match the lean artifact model

**Files:**
- Modify: `repo_config/planning_artifact_schema.yaml`
- Modify: `scripts/validate_planning_lifecycle.py`
- Delete: `scripts/validate_checkpoint_packs.py`
- Modify: `scripts/validate_repo_contracts.py`
- Modify: `scripts/validate_template_required_sections.py`
- Modify: `tests/test_validate_planning_lifecycle.py`
- Modify: `tests/test_validate_repo_contracts.py`

**Preconditions:**
- deleted artifact types and retained optional references are final

**Steps:**
- [x] Remove `execution_map` and `bounded_change_thread` artifact definitions, path globs, statuses, and required values.
- [x] Remove `parent_thread` from active spec and plan metadata guidance and validation; preserve `parent_spec` as optional plan linkage.
- [x] Refactor lifecycle validation to validate optional roadmap, existing specs, existing plans, and supplied references without requiring roadmap, workstream, thread, map, or checkpoint coverage.
- [x] Delete execution-map records, discovery, integrity checks, and unused lifecycle parameters.
- [x] Delete checkpoint-pack validation and remove its repository-contract registration.
- [x] Replace obsolete tests with focused tests proving roadmap absence is accepted, optional roadmap is validated when present, and invalid supplied spec/plan references still fail.

**Verification:**
- [x] `python -m pytest -q tests/test_validate_planning_lifecycle.py tests/test_validate_repo_contracts.py tests/test_validate_template_required_sections.py`
- [x] `python scripts/validate_planning_lifecycle.py`
- [x] `python scripts/validate_repo_contracts.py --fast`

**Exit Criteria:**
- validators enforce existing artifact correctness without enforcing artifact creation

### Task 6: Update Starter-Kit And Generated Surfaces

**Purpose:**
- prevent deleted planning machinery from returning through generation or local starter-kit synchronization

**Files:**
- Modify: `repo_config/starter-kit-manifest.json`
- Modify: `docs/operating_system/templates/agents/root-AGENTS.template.md` only if generated manifest or planning wording requires it
- Generate: `AGENTS.md`
- Generate: `.agents/rules/`
- Generate: `.codex/rules/`
- Generate: `generated_agents/`
- Generate: `generated_exports/project-OS-starter-kit/`
- Sync: `C:/Users/HOANG PHI LONG DANG/repos/project-OS-starter-kit/`

**Preconditions:**
- canonical skills, rules, prompts, schemas, validators, and manifests are final

**Steps:**
- [x] Remove deleted scripts and directories from starter-kit required paths, allowlists, and empty-directory creation.
- [x] Regenerate adapters from canonical sources; never edit generated copies directly.
- [x] Rebuild and validate generated starter-kit output.
- [x] Sync validated output to the local starter-kit repository.
- [x] Confirm deleted planning layers do not exist in generated or synchronized output.

**Verification:**
- [x] `python scripts/sync_agent_adapters.py`
- [x] `powershell -ExecutionPolicy Bypass -File scripts/verify_agent_adapters.ps1`
- [x] `python scripts/build_starter_kit.py`
- [x] `python scripts/validate_starter_kit.py`
- [x] `pwsh -NoProfile -ExecutionPolicy Bypass -File scripts/sync_local_starter_kit_repo.ps1`

**Exit Criteria:**
- generated and local starter-kit surfaces match the lean canonical model

### Task 7: Reconcile References And Prove Cleanup

**Purpose:**
- remove stale active references without rewriting historical completed plans

**Files:**
- Inspect: `.agents/`
- Inspect: `docs/`
- Inspect: `repo_config/`
- Inspect: `scripts/`
- Inspect: `tests/`
- Inspect: `generated_agents/`
- Inspect: `C:/Users/HOANG PHI LONG DANG/repos/project-OS-starter-kit/`

**Preconditions:**
- Tasks 1 through 6 complete

**Steps:**
- [x] Search canonical and generated active surfaces for deleted artifact names, paths, metadata fields, scripts, and lifecycle claims.
- [x] Grandfather references inside completed historical plans unless they act as current instructions or break validation.
- [x] Confirm no new registry, lineage, handoff pack, or orchestration layer was introduced as replacement.
- [x] Review diff for accidental deletion of substantive brainstorming, spec, plan, execution, verification, or finishing methods.
- [x] Run focused checks, broad repository contracts, and whitespace checks.

**Verification:**
- [x] `rg -n -i "execution[_ -]?map|execution_maps|bounded change thread|bounded_change_thread|workstreams/threads|workstreams/checkpoints|checkpoint result pack|checkpoint-result-pack|validate_checkpoint_packs|complete spec set|spec-authoring map|parent_thread" .agents docs repo_config scripts tests generated_agents AGENTS.md --glob '!docs/superpowers/plans/**'`
- [x] `python scripts/validate_repo_contracts.py`
- [x] `python -m pytest -q`
- [x] `git diff --check`

**Exit Criteria:**
- active repository and starter-kit surfaces expose only the adaptive intent-to-execution model, with historical evidence preserved and all checks passing

## Verification

- `python scripts/validate_skill_metadata.py`
- `python scripts/validate_prompt_metadata.py`
- `python scripts/validate_template_required_sections.py`
- `python scripts/sync_agent_adapters.py`
- `powershell -ExecutionPolicy Bypass -File scripts/verify_agent_adapters.ps1`
- `python scripts/validate_planning_lifecycle.py`
- `python scripts/validate_repo_contracts.py`
- `python -m pytest -q`
- `python scripts/build_starter_kit.py`
- `python scripts/validate_starter_kit.py`
- `pwsh -NoProfile -ExecutionPolicy Bypass -File scripts/sync_local_starter_kit_repo.ps1`
- `git diff --check`

## Completion Criteria

This plan is complete when:

1. optional roadmap is the only retained intent-level planning document type
2. roadmap absence no longer fails validation
3. execution maps, bounded change threads, checkpoint result packs, spec-set expectations, and spec-authoring-map expectations are removed from active canonical, generated, validator, and starter-kit surfaces
4. useful current intent is preserved without copying historical execution evidence into new documents
5. specs and plans remain optional, substantive artifacts with clear ownership
6. direct, spec-led, and plan-led execution all route into existing execution, verification, and authorized branch-finishing skills
7. no replacement orchestration or lineage layer is introduced
8. focused tests, full repository contracts, full test suite, adapter checks, starter-kit validation, synchronization, stale-reference search, and diff checks pass with fresh evidence
