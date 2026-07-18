---
layer: operating_system
artifact_type: plan
status: completed
template_id: implementation-plan
name: planning-artifact-ssot-and-symmetry-cleanup
parent_workstream: none
targets:
  - repo_config/planning_artifact_schema.yaml
  - docs/operating_system/templates/detailed-specification-template.md
  - docs/superpowers/execution_maps/
  - docs/superpowers/plans/brainstorming/
  - scripts/validate_planning_lifecycle.py
  - scripts/validate_template_required_sections.py
  - .agents/skills/
  - docs/operating_system/rules/
---

# Planning Artifact SSOT And Symmetry Cleanup Plan

## Goal

Make brainstorming reports, specifications, implementation plans, and execution maps structurally consistent while giving each artifact one semantic owner and reducing mandatory planning administration.

Keep current folder topology. Do not add persistent lineage, a new planning registry, another validator, or a historical-artifact migration program.

## Key Deliverables

### Canonical ownership contract

- brainstorming reports own exploration, alternatives, recommendation, and unresolved questions
- specifications own approved behavior, interfaces, decisions, invariants, acceptance criteria, and validation intent
- implementation plans own exact tasks, files, commands, dependencies, and verification
- execution maps optionally own cross-plan sequencing, waves, lanes, and shared-surface risk

### Reduced execution-map administration

- execution maps become optional
- one execution-map shape replaces the three-map lifecycle requirement
- obsolete sample maps tied to removed planning-lineage behavior are deleted
- existing validator remains the only executable planning-lifecycle owner

### Aligned skills and governance

- planning skills teach the same artifact ownership contract
- rules state hard non-duplication invariants only
- workflow owns artifact transitions
- prompts remain concise reusable wording

## Task/Wave Breakdown

### Task 1: Lock planning artifact ownership

**Purpose:**
- establish one canonical ownership statement before changing templates or validators

**Files:**
- Modify: `docs/operating_system/governance/repo-governance.md`
- Modify: `docs/operating_system/planning/planning-dispatch.md`
- Modify: `docs/operating_system/rules/doc-contracts-rule.md`
- Modify: `docs/operating_system/prompt_templates/design-spec-prompt.md`
- Modify: `docs/operating_system/prompt_templates/implementation-plan-prompt.md`

**Preconditions:**
- current corrected planning topology remains unchanged

**Steps:**
- [x] define artifact ownership once in repo governance
- [x] make planning dispatch route to brainstorm, spec, plan, or optional execution map without requiring a full ladder
- [x] add hard rule that an artifact must not duplicate another artifact's canonical content
- [x] update change workflow transitions to match the ownership contract
- [x] keep prompts wording-only and remove wording that assigns implementation sequencing to specs

**Verification:**

**Exit Criteria:**
- one non-contradictory ownership contract governs all later edits

### Task 2: Remove plan sequencing from specification contract

**Purpose:**
- restore specification SSOT for design decisions instead of implementation order

**Files:**
- Modify: `docs/operating_system/templates/detailed-specification-template.md`
- Modify: `scripts/validate_template_required_sections.py`
- Modify: `tests/test_validate_template_required_sections.py`
- Modify: `.agents/skills/skill-spec-drafting/SKILL.md`
- Modify: `.agents/skills/skill-writing-plans/SKILL.md`
- Modify: `.agents/skills/skill-plan-document-reviewer/SKILL.md`

**Preconditions:**
- Task 1 ownership language approved in source

**Steps:**
- [x] replace required `Task/Wave Breakdown` with a design-analysis section that owns current-state evidence, alternatives where needed, and decision closure
- [x] keep exact tasks, file maps, commands, and execution waves exclusively in implementation plans
- [x] update template validator expectations and focused fixtures
- [x] update spec-drafting skill required sections and examples
- [x] update plan-writing skill to consume approved decisions without restating design analysis
- [x] update plan reviewer to flag sequencing inside specs and design duplication inside plans
- [x] grandfather completed specs and avoid mass historical rewrites

**Verification:**
- [x] `python -m pytest -q tests/test_validate_template_required_sections.py`
- [x] `python scripts/validate_template_required_sections.py`
- [x] `rg -n "Task/Wave Breakdown" docs/operating_system/templates/detailed-specification-template.md .agents/skills/skill-spec-drafting/SKILL.md`

**Exit Criteria:**
- new specifications cannot require implementation sequencing

### Task 3: Collapse execution maps to one optional artifact

**Purpose:**
- remove symmetry-for-symmetry administration and keep only distinct cross-plan orchestration

**Files:**
- Modify: `repo_config/planning_artifact_schema.yaml`
- Modify: `docs/superpowers/execution_maps/README.md`
- Modify: `scripts/validate_planning_lifecycle.py`
- Modify: `tests/test_validate_planning_lifecycle.py`
- Delete: `docs/superpowers/execution_maps/2026-04-28-sample-complete-spec-set-map.md`
- Delete: `docs/superpowers/execution_maps/2026-04-28-sample-spec-authoring-map.md`
- Delete: `docs/superpowers/execution_maps/2026-04-28-sample-execution-map.md`

**Preconditions:**
- specifications and plans have distinct ownership after Task 2

**Steps:**
- [x] remove `complete_spec_set` and `spec_authoring` taxonomy values
- [x] remove `map_type` when the remaining artifact has only one meaning
- [x] keep current `parent_workstream`, `threads`, and optional `specs` references only as explicit orchestration scope
- [x] remove three-map-per-workstream coverage checks and bootstrap-map expectations
- [x] validate execution-map reference integrity only when a map exists
- [x] document creation threshold: multiple plans with real dependencies, shared surfaces, or parallel lanes
- [x] delete obsolete sample maps rather than rewriting removed planning-lineage scenarios

**Verification:**
- [x] `python -m pytest -q tests/test_validate_planning_lifecycle.py`
- [x] `python scripts/validate_planning_lifecycle.py`
- [x] `rg -n "complete_spec_set|spec_authoring|map_type|missing .* execution map" repo_config/planning_artifact_schema.yaml docs/superpowers/execution_maps scripts/validate_planning_lifecycle.py tests/test_validate_planning_lifecycle.py`

**Exit Criteria:**
- workstreams require no execution map by default and existing maps are validated only as optional orchestration artifacts

### Task 4: Clarify brainstorming authority without moving it

**Purpose:**
- keep current detailed-report workflow while preventing brainstorm recommendations from becoming competing specification truth

**Files:**
- Modify: `docs/operating_system/templates/brainstorming-detailed-report-template.md`
- Modify: `docs/superpowers/plans/brainstorming/README.md`
- Modify: `.agents/skills/skill-brainstorming/SKILL.md`
- Inspect: `scripts/new_brainstorming_report.ps1`
- Inspect: `scripts/brainstorming_capture.ps1`

**Preconditions:**
- no committed brainstorming report bundles require migration

**Steps:**
- [x] state that brainstorming reports are exploratory evidence, not approved design truth
- [x] require accepted recommendations to be restated in an approved specification or direct approved scope
- [x] prohibit full implementation sequencing and duplicate invariant/interface contracts in brainstorm reports
- [x] align README manifest claims with actual script behavior: bundle identity and captured evidence artifacts only
- [x] keep current path and scripts unless inspection reveals another active contradiction
- [x] do not add brainstorming to planning lifecycle schema or validator

**Verification:**
- [x] `rg -n "exploratory|approved specification|implementation plan|manifest" docs/operating_system/templates/brainstorming-detailed-report-template.md docs/superpowers/plans/brainstorming/README.md .agents/skills/skill-brainstorming/SKILL.md`
- [x] `pwsh -NoProfile -ExecutionPolicy Bypass -File scripts/new_brainstorming_report.ps1 -ReportId planning-artifact-contract-smoke`
- [x] inspect generated manifest and report scaffold, then remove smoke bundle after verification

**Exit Criteria:**
- brainstorm reports remain optional and cannot compete with specification or plan SSOT

### Task 5: Reconcile planning skills and reusable prompts

**Purpose:**
- ensure most-used planning methods retain full authoring detail while sharing one ownership model

**Files:**
- Modify: `.agents/skills/skill-spec-drafting/SKILL.md`
- Modify: `.agents/skills/skill-writing-plans/SKILL.md`
- Modify: `.agents/skills/skill-plan-document-reviewer/SKILL.md`
- Modify: `.agents/skills/skill-brainstorming/SKILL.md`
- Modify: `docs/operating_system/prompt_templates/task-intake-prompt.md`
- Modify: `docs/operating_system/prompt_templates/design-spec-prompt.md`
- Modify: `docs/operating_system/prompt_templates/implementation-plan-prompt.md`

**Preconditions:**
- Tasks 1 through 4 establish final contracts

**Steps:**
- [x] preserve substantive checklists, examples, preconditions, and handoff rules
- [x] remove remaining references to three-map symmetry or mandatory execution maps
- [x] make execution-map routing conditional on cross-plan complexity
- [x] keep prompts concise and move reusable methods into skills
- [x] ensure documentation-maintenance skill checks semantic ownership, not document-count symmetry
- [x] avoid global `MUST-READ` lists and use conditional references

**Verification:**
- [x] `python scripts/validate_agent_metadata_schema.py`
- [x] `rg -n "complete_spec_set|spec_authoring|mandatory execution map|MUST-READ" .agents/skills docs/operating_system/prompt_templates`

**Exit Criteria:**
- planning skills remain detailed and no skill teaches a conflicting artifact contract

### Task 6: Regenerate and prove repository-wide consistency

**Purpose:**
- update derived agent surfaces and starter output from canonical planning changes

**Files:**
- Regenerate: `generated_agents/`
- Regenerate: `.agents/rules/`
- Regenerate: `.codex/rules/`
- Regenerate: `AGENTS.md`
- Regenerate: `generated_exports/project-OS-starter-kit/`
- Sync: `C:/Users/HOANG PHI LONG DANG/repos/project-OS-starter-kit`

**Preconditions:**
- Tasks 1 through 5 complete

**Steps:**
- [x] regenerate all provider adapters
- [x] verify adapter drift
- [x] run focused planning and template tests
- [x] run full repository tests and contracts
- [x] rebuild and validate starter kit
- [x] sync local starter-kit folder
- [x] run publication dry run because operating-system docs and starter output changed
- [x] search active sources for retired map taxonomy and stale ownership wording

**Verification:**
- [x] `python scripts/sync_agent_adapters.py --all-platforms`
- [x] `pwsh -NoProfile -ExecutionPolicy Bypass -File scripts/sync_agent_adapters.ps1`
- [x] `pwsh -NoProfile -ExecutionPolicy Bypass -File scripts/verify_agent_adapters.ps1`
- [x] `python -m pytest --basetemp .tmp-tests/planning-artifact-ssot -q`
- [x] `python scripts/validate_repo_contracts.py`
- [x] `python scripts/build_starter_kit.py`
- [x] `python scripts/validate_starter_kit.py`
- [x] `pwsh -NoProfile -ExecutionPolicy Bypass -File scripts/sync_local_starter_kit_repo.ps1`
- [x] `pwsh -NoProfile -ExecutionPolicy Bypass -File scripts/publish_public_repo.ps1`
- [x] `git diff --check`

**Exit Criteria:**
- canonical, generated, starter-kit, and publication surfaces agree on one low-administration planning model

## Verification

- `python -m pytest --basetemp .tmp-tests/planning-artifact-ssot -q`
- `python scripts/validate_repo_contracts.py`
- `python scripts/sync_agent_adapters.py --all-platforms --check`
- `python scripts/validate_starter_kit.py`
- `git diff --check`

## Completion Criteria

1. specs no longer require implementation waves or task sequencing
2. execution maps are optional and have one artifact shape
3. three-map lifecycle coverage and obsolete samples are removed
4. brainstorming remains optional, exploratory, and outside lifecycle validation
5. planning skills preserve full authoring methods while teaching one ownership model
6. no new folder, registry, lineage generator, or validator is introduced
7. all focused and broad verification passes with fresh evidence
