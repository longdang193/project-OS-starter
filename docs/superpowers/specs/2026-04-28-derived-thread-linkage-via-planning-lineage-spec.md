---
layer: change
artifact_type: spec
status: completed
parent_thread: starter-adoption-experience.adoption-prompt-discoverability-without-duplication
targets:
  - docs/intent/workstreams/
  - docs/intent/workstreams/threads/
  - docs/generated/planning_lineage.yaml
  - docs/operating_system/planning-dispatch.md
  - docs/operating_system/repo-governance.md
  - docs/operating_system/prompt_templates/
  - scripts/planning_lineage_support.py
  - scripts/generate_planning_lineage.py
  - scripts/validate_adoption_shape.py
  - tests/test_validate_adoption_shape.py
related_features: []
related_stages: []
---

# Derived Thread Linkage Via Planning Lineage Spec

## Triage

Layer: operating_system  
Feature type: MODIFY  
Summary: Keep bounded change thread files free of linked spec/plan fields and derive all downstream linkage only through `parent_thread`, exposing the result in `docs/generated/planning_lineage.yaml`.  
Reasoning: The repo has already committed to the rule that canonical truth should flow downward from upstream layers and downstream layers should derive views from it rather than re-entering it. Putting `linked_spec` and `linked_plan` back into thread files would reintroduce a sync-managed duplicate fact into an upstream source layer.  
Invariants:

- thread files remain canonical for thread meaning, not derived downstream linkage
- specs and plans remain canonical for their own metadata
- `parent_thread` is the only product-side thread linkage field required on downstream artifacts
- `docs/generated/planning_lineage.yaml` is the inspection surface for assembled thread/spec/plan linkage
- validator enforcement should prevent manual re-entry of derived thread linkage

Dependencies:

- `docs/intent/workstreams/`
- `docs/intent/workstreams/threads/`
- `docs/generated/planning_lineage.yaml`
- `docs/operating_system/planning-dispatch.md`
- `docs/operating_system/repo-governance.md`
- `docs/operating_system/prompt_templates/`
- `scripts/planning_lineage_support.py`
- `scripts/generate_planning_lineage.py`
- `scripts/validate_adoption_shape.py`
- `tests/test_validate_adoption_shape.py`

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
  - `docs/operating_system/planning-dispatch.md`
  - `docs/operating_system/repo-governance.md`
- readme: none
- generated:
  - `docs/generated/planning_lineage.yaml`

Generated refresh required: yes  
Capability IDs: none  
Invariant IDs: none  
Spec needed: yes  
Plan needed: yes

## Problem

Once thread files exist, it is tempting to add convenience fields such as:

- `linked_spec`
- `linked_plan`

That is operationally attractive, but it creates a new duplication boundary:

1. the thread file becomes responsible for storing facts already derivable from
   spec/plan metadata
2. `parent_thread` in specs/plans and `linked_*` in thread files can drift
3. thread files stop being purely upstream source and become partly assembled
   views

That would weaken the repo’s planning-lineage model.

## Goal

Adopt the strict derived-linkage option:

- thread files do not store `linked_spec` or `linked_plan`
- specs and plans link upward through `parent_thread`
- plans also link to specs through `parent_spec`
- the assembled linkage is exposed only through
  `docs/generated/planning_lineage.yaml`

## Non-Goals

This spec does not remove the thread layer.

This spec does not remove the generated planning-lineage surface.

This spec does not prevent stub generation or other scaffold tooling in the
future, as long as those tools write canonical downstream metadata rather than
derived linkage back into thread files.

This spec does not require `operating_system` thread branches yet.

## Recommended Source / Derived Boundary

### Canonical source layers

Keep these as source-owned:

- `docs/intent/master-workstream-roadmap.md`
- `docs/intent/workstreams/*.md`
- `docs/intent/workstreams/threads/<workstream-id>/*.md`
- `docs/superpowers/specs/*.md`
- `docs/superpowers/plans/*.md`

### Derived inspection layer

Use this as the assembled planning linkage view:

- `docs/generated/planning_lineage.yaml`

The rule is:

`thread files describe the slice; generated lineage describes what came out of the slice.`

## Recommended Thread Metadata

Thread files should stay minimal:

```yaml
---
thread_id: <workstream-id>.<thread-slug>
status: proposed | active | blocked | completed
---
```

Thread bodies should stay focused on:

- goal
- why now
- dependencies
- shared surfaces
- notes

They should not carry:

- `linked_spec`
- `linked_plan`
- manually curated downstream artifact lists

## Recommended Downstream Metadata

### Spec

```yaml
---
layer: change
artifact_type: spec
status: proposed | active | completed | superseded
parent_thread: <thread-id>
targets:
  - <path>
related_features: []
related_stages: []
---
```

### Plan

```yaml
---
layer: change
artifact_type: plan
status: proposed | active | completed | superseded
parent_thread: <thread-id>
parent_spec: <repo-relative spec path>
targets:
  - <path>
related_features: []
related_stages: []
---
```

That is enough to reconstruct:

`thread -> spec -> plan`

without storing those links in the thread file itself.

## Generated Planning Lineage Responsibilities

`docs/generated/planning_lineage.yaml` should expose:

- roadmap root
- registered workstreams
- thread files
- linked specs derived from `parent_thread`
- linked plans derived from `parent_thread`
- plan-to-spec relationships derived from `parent_spec`
- roll-up completion summaries

This becomes the canonical place to inspect:

- whether a thread already produced a spec
- whether a thread already produced a plan
- whether plan/spec lineage is consistent

## Validator Responsibilities

The validator should enforce the strict source/derived boundary.

### Required checks

1. thread files must not define:
   - `linked_spec`
   - `linked_plan`
2. specs must carry `parent_thread` when they are product-side `change`
   artifacts
3. plans must carry:
   - `parent_thread`
   - `parent_spec`
4. generated planning lineage must stay in sync with the derived graph

### Redundancy checks

The validator should reject:

- thread files that manually restate derived downstream linkage
- any attempt to turn the thread file into a second assembled artifact index

## Prompt And Guidance Implications

Prompt docs should teach this boundary clearly:

- thread-building prompts produce thread source files only
- spec prompts produce canonical spec metadata with `parent_thread`
- plan prompts produce canonical plan metadata with `parent_thread` and
  `parent_spec`
- users should inspect `docs/generated/planning_lineage.yaml` when they want
  the assembled thread/spec/plan view

Guidance docs should say plainly:

`If you want to know what spec or plan came out of a thread, look at the generated planning-lineage view rather than re-entering those links into the thread file.`

## Acceptance Criteria

- thread files stay free of `linked_spec` and `linked_plan`
- generated planning lineage exposes thread/spec/plan linkage cleanly
- validator rejects manual re-entry of derived linkage on thread files
- prompt and governance docs explain that derived linkage belongs in the
  generated planning-lineage view

## Recommendation

Adopt the strict derived-linkage model.

It is less convenient than storing generated links directly in thread files, but
it is the cleaner architecture:

- source files stay canonical
- downstream linkage stays derived
- drift risk stays lower
- the generated planning-lineage view becomes the single assembled inspection
  surface
