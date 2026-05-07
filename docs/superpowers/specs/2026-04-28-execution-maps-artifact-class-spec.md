---
layer: operating_system
artifact_type: spec
status: completed
parent_workstream: none
targets:
  - docs/superpowers/execution_maps/
  - docs/superpowers/specs/
  - docs/superpowers/plans/
  - docs/generated/planning_lineage.yaml
  - docs/operating_system/skill-planning-dispatch.md
  - docs/operating_system/governance/repo-governance.md
  - docs/operating_system/prompt_templates/
related_features: []
related_stages: []
---

# Execution Maps Artifact Class Spec

## Triage

Layer: operating_system  
Feature type: ADD  
Summary: Add `docs/superpowers/execution_maps/` as a separate artifact class for orchestration across a set of specs, with a strict boundary that keeps execution maps distinct from specs, plans, thread files, and generated lineage views.  
Reasoning: The planning system now has a clear ladder from thread sets to specs and from specs to plans, but it still lacks a dedicated human-authored artifact for multi-spec execution orchestration. That orchestration is too broad for a single plan, not design-oriented enough to belong in specs, and too cross-cutting to live in thread files.  
Invariants:

- execution maps are orchestration artifacts, not design specs
- execution maps are orchestration artifacts, not implementation plans
- execution maps must not duplicate structural lineage already derived in `docs/generated/planning_lineage.yaml`
- thread files remain canonical for slice meaning
- specs remain canonical for bounded design
- plans remain canonical for bounded execution of one approved slice

Dependencies:

- `docs/superpowers/specs/`
- `docs/superpowers/plans/`
- `docs/generated/planning_lineage.yaml`
- `docs/operating_system/skill-planning-dispatch.md`
- `docs/operating_system/governance/repo-governance.md`
- `docs/operating_system/prompt_templates/`

Affected stages:

- none

Affected features:

- none

Primary lens: cross-cutting

Affected docs:

- feature_source: none
- feature_yaml: none
- feature_lineage: none
- feature_history: none
- stage_source: none
- stage_contract: none
- feature_docs: none
- cross_cutting_docs:
  - `docs/operating_system/skill-planning-dispatch.md`
  - `docs/operating_system/governance/repo-governance.md`
- readme: none
- generated:
  - `docs/generated/planning_lineage.yaml`

Generated refresh required: no  
Capability IDs: none  
Invariant IDs: none  
Spec needed: yes  
Plan needed: yes

## Problem

The repo now has strong artifact surfaces for:

- thread decomposition
- bounded specs
- bounded implementation plans
- generated lineage/progress inspection

But there is still no dedicated artifact for:

- deciding execution waves across multiple specs
- deciding what runs in parallel
- identifying blocking dependencies across a spec set
- recording why one execution order was chosen over another

Today that orchestration pressure can drift into the wrong places:

1. workstream docs
2. thread files
3. oversized plans
4. ad hoc chat-only reasoning that leaves no reusable artifact

## Goal

Introduce `docs/superpowers/execution_maps/` as a distinct orchestration layer
between:

`spec set -> execution map -> bounded plans -> execution`

## Non-Goals

This spec does not move specs or plans out of their existing folders.

This spec does not turn execution maps into multi-spec implementation plans.

This spec does not make execution maps the owner of structural lineage that is
already derivable in `docs/generated/planning_lineage.yaml`.

This spec does not add a new generated surface for orchestration in the first
pass.

## Recommended Ladder

Use this precise structure:

```text
thread set
-> spec set
-> execution map
-> implementation plans
-> execution
```

Roles:

- `thread set`
  - what slices exist
- `spec set`
  - what designs are required
- `execution map`
  - how the approved spec set should be orchestrated
- `implementation plans`
  - concrete execution steps for one bounded spec or lane

## Recommended Folder

Add:

```text
docs/
└─ superpowers/
   ├─ specs/
   ├─ plans/
   └─ execution_maps/
      ├─ README.md
      └─ YYYY-MM-DD-<scope>-execution-map.md
```

## Recommended Artifact Definition

Execution maps should answer:

- which specs are in scope
- which specs depend on which others
- which specs can run in parallel
- which shared surfaces create coordination risk
- what execution waves or lanes should exist
- what bounded plans should be created next

Execution maps should not answer:

- detailed design of a spec
- exact implementation steps for a spec
- verification commands for each individual file edit
- rollback mechanics for each bounded change

Those belong in plans.

## Recommended Metadata

Suggested frontmatter:

```yaml
---
layer: change
artifact_type: execution_map
status: proposed | active | completed | superseded
parent_workstream: <id> | none
threads:
  - <thread-id>
specs:
  - docs/superpowers/specs/<file>.md
---
```

Optional later:

- `execution_waves`
- `parallel_lanes`

But keep the first version small.

## Recommended Body Shape

Suggested sections:

- scope
- dependency graph
- execution waves
- parallel lanes
- shared-surface risks
- plan breakdown
- orchestration notes

Example shape:

```md
# Sample Execution Map

## Scope
- specs in scope

## Dependency Graph
- spec-b depends on spec-a

## Execution Waves
### Wave 1
- spec-a
- spec-c

### Wave 2
- spec-b

## Parallel Lanes
### Lane A
- spec-a
- spec-b

### Lane B
- spec-c

## Shared-Surface Risks
- docs/operating_system/governance/repo-governance.md

## Recommended Plan Breakdown
- one plan for spec-a
- one plan for spec-b
- one plan for spec-c
```

## Boundary Against Other Artifacts

### Versus thread files

Thread files answer:
- what this slice is

Execution maps answer:
- how a set of spec-backed slices should move together

Thread files must not become execution maps.

### Versus specs

Specs answer:
- what should be built and why

Execution maps answer:
- in what order/waves/lane the approved specs should move

Execution maps must not restate spec design.

### Versus plans

Plans answer:
- how to implement one approved bounded slice

Execution maps answer:
- how multiple approved specs/plans should be orchestrated together

Execution maps must not become giant multi-spec plans.

### Versus generated planning lineage

`docs/generated/planning_lineage.yaml` answers:
- what links to what
- what the derived structural graph looks like

Execution maps answer:
- what humans decided about orchestration

Execution maps must not become another linkage registry.

## Prompt Implications

Add or refine prompts so the flow becomes:

1. `thread-set-to-spec-set-prompt.md`
   - produce the complete spec set
2. `spec-set-execution-map-prompt.md`
   - produce the orchestration artifact
3. `plan-prompt.md`
   - produce bounded plans from the chosen execution map lanes/waves

This is cleaner than trying to force one prompt to do all three jobs.

## Validator Direction

The first pass does not need heavy validator enforcement, but the direction
should be:

1. `artifact_type: execution_map` matches the folder
2. listed spec paths resolve
3. listed thread ids resolve when present
4. execution maps do not pretend to be plans by carrying plan-only metadata in
   later phases if needed

## Acceptance Criteria

- the repo defines `docs/superpowers/execution_maps/` as a distinct artifact class
- the artifact has a clear metadata shape
- the artifact has a clear body shape
- the artifact boundary is explicit against specs, plans, thread files, and generated lineage
- the prompt ladder has a place for spec-set orchestration

## Recommendation

Add `execution_maps/` as a real artifact class.

That gives orchestration a home without forcing:

- specs to carry planning-board logic
- plans to become multi-spec super-docs
- thread files to absorb cross-spec coordination

The key is to keep the boundary strict:

`execution maps orchestrate; they do not design, implement, or duplicate lineage`
