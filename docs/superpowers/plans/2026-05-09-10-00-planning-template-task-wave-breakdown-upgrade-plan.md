---
layer: operating_system
artifact_type: plan
status: completed
template_id: implementation-plan
name: planning-template-task-wave-breakdown-upgrade
parent_workstream: none
targets:
  - docs/operating_system/templates/master-workstream-roadmap-template.md
  - docs/operating_system/templates/registered-workstream-list-template.md
  - docs/operating_system/templates/bounded-change-thread-template.md
  - docs/operating_system/templates/complete-specification-set-template.md
  - docs/operating_system/templates/spec-authoring-map-template.md
  - docs/operating_system/templates/detailed-specification-template.md
  - docs/operating_system/templates/implementation-execution-map-template.md
  - docs/operating_system/templates/implementation-plan-template.md
  - docs/operating_system/templates/task-start-routing-guide.md
  - .agents/skills/skill-brainstorming/SKILL.md
  - .agents/skills/skill-writing-plans/SKILL.md
  - .agents/skills/skill-executing-plans/SKILL.md
  - repo_config/planning_artifact_schema.yaml
  - scripts/validate_planning_lifecycle.py
related_features: []
related_stages: []
---

# Planning Template Task/Wave Breakdown Upgrade Plan

## Goal

Upgrade planning-ladder templates so `Goal / Key Deliverables / Task/Wave Breakdown` remains validator-stable at top level while each artifact gets richer, artifact-appropriate subsection structure. Result should support stronger execution handoff for plans, clearer sequencing for maps and threads, and better decision/coverage rigor for specs without flattening roadmap or orchestration semantics into one generic block shape.

## Key Deliverables

### Artifact-family breakdown contract defined

Define one explicit template-family contract covering:

- roadmap artifacts -> phase-oriented structure
- thread and map artifacts -> wave-oriented structure
- detailed spec artifacts -> decision-oriented structure with stronger validation planning
- implementation plans -> task-oriented structure with files, steps, verification, and exit criteria

This deliverable must make clear which repeated subsection schema belongs to each template, which optional escalations are allowed, and which shared top-level section names stay unchanged.

### Template-by-template patch recommendations prepared

Produce exact patch recommendations for each targeted template, including:

- subsection structure to add or replace
- fields to enrich from flat bullets into structured repeated records
- sections that should stay artifact-specific instead of being over-normalized
- heading-shape corrections where current nesting is awkward or ambiguous

Recommendations should be specific enough that later implementation can patch files directly without redoing design analysis.

### Skill and validator compatibility impact bounded

Review skill guidance and validator/routing surfaces that depend on template wording or plan shape so the upgrade does not create hidden drift.

At minimum, bound impact on:

- `task-start-routing-guide.md`
- `skill-brainstorming`
- `skill-writing-plans`
- `skill-executing-plans`
- `repo_config/planning_artifact_schema.yaml`
- `scripts/validate_planning_lifecycle.py`

This deliverable must distinguish documentation-only changes from true enforcement changes.

### Section ownership and anti-redundancy contract defined

Define a single-source-of-truth contract for each template so every major section owns one distinct semantic role.

At minimum, recommendations must classify:

- which sections own artifact-level outcomes versus unit-level progression gates
- which sections own sequencing versus canonical inventory or registry data
- which sections own constraints versus decisions versus proof methods
- which sections should be narrowed, merged, or left unchanged to avoid repeating the same fact in multiple places

This deliverable must explicitly prevent duplication between sections such as deliverables versus exit criteria, waves versus lane membership, inventory versus traceability, and task-local verification versus final verification.

## Task/Wave Breakdown

### Task 1: Lock scope and current template contract baseline

**Purpose:**
- confirm exact template set, current top-level section contract, and operating-system ownership boundaries before recommending structural patches

**Files:**
- Inspect: `docs/operating_system/templates/master-workstream-roadmap-template.md`
- Inspect: `docs/operating_system/templates/registered-workstream-list-template.md`
- Inspect: `docs/operating_system/templates/bounded-change-thread-template.md`
- Inspect: `docs/operating_system/templates/complete-specification-set-template.md`
- Inspect: `docs/operating_system/templates/spec-authoring-map-template.md`
- Inspect: `docs/operating_system/templates/detailed-specification-template.md`
- Inspect: `docs/operating_system/templates/implementation-execution-map-template.md`
- Inspect: `docs/operating_system/templates/implementation-plan-template.md`
- Inspect: `docs/operating_system/templates/task-start-routing-guide.md`
- Inspect: `docs/operating_system/planning/planning-dispatch.md`
- Inspect: `docs/operating_system/lifecycle/doc-system-lifecycle.md`
- Inspect: `docs/operating_system/governance/repo-governance.md`

**Preconditions:**
- operating-system layer classification remains correct for planning-template governance work
- no product feature contract or stage contract ownership is required for this patch lane

**Steps:**
- [x] Step 1: Confirm top-level required section contract across targeted templates and record any existing mismatches or awkward heading hierarchies.
- [x] Step 2: Confirm current planning-ladder roles from roadmap through plan so recommendations preserve artifact semantics instead of forcing one generic middle-section pattern.
- [x] Step 3: Confirm this change remains `parent_workstream: none` operating-system work and name exact cross-cutting targets for downstream implementation.

**Verification:**
- [x] Top-level section inventory exists for all targeted templates.
- [x] Artifact-role summary exists for roadmap, workstream list, thread, spec-set, spec-map, detailed spec, execution map, and plan.

**Exit Criteria:**
- template inventory and ownership boundaries are stable enough to support patch recommendations without re-triage

### Task 2: Define artifact-family subsection schemas

**Purpose:**
- produce reusable structural rules for each planning-artifact family before making file-by-file recommendations

**Files:**
- Inspect: `docs/operating_system/templates/master-workstream-roadmap-template.md`
- Inspect: `docs/operating_system/templates/bounded-change-thread-template.md`
- Inspect: `docs/operating_system/templates/spec-authoring-map-template.md`
- Inspect: `docs/operating_system/templates/detailed-specification-template.md`
- Inspect: `docs/operating_system/templates/implementation-execution-map-template.md`
- Inspect: `docs/operating_system/templates/implementation-plan-template.md`
- Modify: `docs/superpowers/plans/2026-05-09-10-00-planning-template-task-wave-breakdown-upgrade-plan.md`

**Preconditions:**
- Task 1 baseline inventory complete
- current shared top-level section names remain preferred unless enforcement evidence requires aliasing

**Steps:**
- [x] Step 1: Define canonical subsection shape for roadmap artifacts, favoring `Phase` blocks with goal, enables/dependencies, and exit criteria instead of task checklists.
- [x] Step 2: Define canonical subsection shape for thread and map artifacts, favoring `Wave` blocks with purpose, sequencing rationale, dependency handling, and exit criteria.
- [x] Step 3: Define canonical subsection shape for detailed specs, favoring stronger decision blocks, invariants, and validation-plan structure rather than flat bullets.
- [x] Step 4: Define canonical subsection shape for implementation plans, favoring `Task` blocks with purpose, files, preconditions, steps, verification, and exit criteria, with `Wave` escalation allowed only when orchestration truly requires it.
- [x] Step 5: Define section-ownership rules for artifact families so outcomes, sequencing, inventories, decisions, constraints, and proof sections do not restate the same fact.

**Verification:**
- [x] Each artifact family has one recommended repeated-block schema.
- [x] Recommendations preserve top-level `Task/Wave Breakdown` wording while allowing artifact-appropriate subsection labels.
- [x] Section-ownership rules distinguish artifact-level deliverables from unit-level gates and canonical inventories from sequencing prose.

**Exit Criteria:**
- family-level structure rules are explicit enough to drive template-by-template edits without reinventing semantics per file

### Task 3: Draft template-by-template patch recommendations

**Purpose:**
- convert family-level rules into exact template recommendations for each target file

**Files:**
- Inspect: `docs/operating_system/templates/master-workstream-roadmap-template.md`
- Inspect: `docs/operating_system/templates/registered-workstream-list-template.md`
- Inspect: `docs/operating_system/templates/bounded-change-thread-template.md`
- Inspect: `docs/operating_system/templates/complete-specification-set-template.md`
- Inspect: `docs/operating_system/templates/spec-authoring-map-template.md`
- Inspect: `docs/operating_system/templates/detailed-specification-template.md`
- Inspect: `docs/operating_system/templates/implementation-execution-map-template.md`
- Inspect: `docs/operating_system/templates/implementation-plan-template.md`
- Modify: `docs/superpowers/plans/2026-05-09-10-00-planning-template-task-wave-breakdown-upgrade-plan.md`

**Preconditions:**
- Task 2 subsection schemas approved internally for recommendation use

**Steps:**
- [x] Step 1: For roadmap and registered-workstream templates, recommend richer phase/registry fields, heading cleanup, and traceability expansion without turning them into execution plans.
- [x] Step 2: For bounded-change-thread, complete-specification-set, and spec-authoring-map templates, recommend wave-level structures with explicit coverage, dependencies, merge points, and handoff readiness.
- [x] Step 3: For detailed-specification template, recommend structured decision blocks, richer invariants, and proof-oriented validation-plan records.
- [x] Step 4: For implementation-execution-map and implementation-plan templates, recommend lane/task structures with shared-surface awareness, verification expectations, and artifact-specific execution detail.
- [x] Step 5: Record which sections should stay artifact-specific and which flat bullets should become structured repeated records.
- [x] Step 6: Record where section boundaries must be tightened to avoid redundancy, including deliverables versus exit criteria, waves versus lane membership, inventory versus coverage or traceability, and local versus final verification.

**Verification:**
- [x] Every targeted template has concrete patch guidance.
- [x] Recommendations distinguish must-change structure from optional polish.
- [x] Each template recommendation includes a single-source-of-truth note for any section pair at risk of duplication.

**Exit Criteria:**
- downstream editor could patch each template directly from recommendations with minimal additional analysis

### Task 4: Bound routing, skill, and validator follow-up

**Purpose:**
- ensure template recommendations account for dependent guidance and enforcement surfaces without inventing unnecessary schema churn

**Files:**
- Inspect: `docs/operating_system/templates/task-start-routing-guide.md`
- Inspect: `.agents/skills/skill-brainstorming/SKILL.md`
- Inspect: `.agents/skills/skill-writing-plans/SKILL.md`
- Inspect: `.agents/skills/skill-executing-plans/SKILL.md`
- Inspect: `repo_config/planning_artifact_schema.yaml`
- Inspect: `scripts/validate_planning_lifecycle.py`
- Modify: `docs/superpowers/plans/2026-05-09-10-00-planning-template-task-wave-breakdown-upgrade-plan.md`

**Preconditions:**
- template-level recommendations complete

**Steps:**
- [x] Step 1: Identify which skills need stronger wording about artifact-specific subsection shapes, especially detailed spec, execution map, and implementation plan consumption or authoring.
- [x] Step 2: Determine whether `task-start-routing-guide.md` should explicitly describe phase vs wave vs task vs decision structures as part of canonical ladder expectations.
- [x] Step 3: Check whether `planning_artifact_schema.yaml` needs no change, metadata-only clarification, or future extension, keeping body-shape changes separate from frontmatter schema unless clearly necessary.
- [x] Step 4: Check whether `scripts/validate_planning_lifecycle.py` enforces only top-level section presence or also depends on inner wording that must be updated.
- [x] Step 5: Classify follow-up as documentation-only, validator-compatible, or staged-enforcement so implementation sequencing stays safe.

**Verification:**
- [x] Skill/routing follow-up list exists.
- [x] Validator/schema impact is explicitly classified rather than assumed.

**Exit Criteria:**
- implementation lane can patch templates first, then dependent skill/validator surfaces in safe order

### Task 5: Package implementation-ready edit order and verification lane

**Purpose:**
- turn recommendations into execution-ready follow-up slices with safe order and validation coverage

**Files:**
- Inspect: `docs/operating_system/templates/*.md`
- Inspect: `.agents/skills/*.md`
- Inspect: `repo_config/planning_artifact_schema.yaml`
- Inspect: `scripts/validate_planning_lifecycle.py`
- Modify: `docs/superpowers/plans/2026-05-09-10-00-planning-template-task-wave-breakdown-upgrade-plan.md`

**Preconditions:**
- Tasks 1-4 complete

**Steps:**
- [x] Step 1: Define execution order for template patches, skill guidance updates, and validator/routing alignment so dependent text never points to not-yet-landed structure.
- [x] Step 2: Separate work into bounded follow-up slices such as template-only patch, skill/routing patch, and validator-enforcement patch if needed.
- [x] Step 3: Name verification commands and review checks for each slice, including whether repo-contract validation is sufficient or targeted planning-lifecycle checks must also run.
- [x] Step 4: Record rollback posture for documentation-first adoption in case enforcement updates must wait for compatibility reasons.

**Verification:**
- [x] Implementation order is explicit.
- [x] Verification lane names exact commands or review checks needed before claiming completion.

**Exit Criteria:**
- plan can hand off directly to implementation without another planning pass

## Verification

- [x] review targeted templates for current subsection drift, heading inconsistencies, and section-level duplication risks
- [x] confirm template recommendations preserve required top-level sections from `required_sections`
- [x] confirm each template recommendation assigns one canonical owner for artifact outcomes, sequencing, inventories, constraints, decisions, and proof sections
- [x] inspect `repo_config/planning_artifact_schema.yaml` for frontmatter impact before proposing schema edits
- [x] inspect `scripts/validate_planning_lifecycle.py` for any inner-section assumptions before recommending enforcement changes
- [x] run `.\.venv\Scripts\python.exe scripts/validate_repo_contracts.py --fast` after implementation if template or skill files are edited

## Completion Criteria

A plan item is considered complete when:

1. all Key Deliverables are satisfied
2. all downstream/child items are terminal
3. every child item is `completed` or `dropped`
4. target templates, routing guidance, dependent skills, and validator checks are aligned with the new subsection contract without unresolved critical drift

Canonical source-of-truth:

<LINK>
- `docs/operating_system/governance/repo-governance.md`
- `scripts/validate_planning_lifecycle.py`
</LINK>
