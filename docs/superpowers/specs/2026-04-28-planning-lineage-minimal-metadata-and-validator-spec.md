---
layer: change
artifact_type: spec
status: completed
parent_thread: starter-adoption-experience.prompt-template-metadata-and-validation
targets:
  - docs/intent/master-workstream-roadmap.md
  - docs/intent/workstreams/
  - docs/intent/workstreams/threads/
  - docs/superpowers/specs/
  - docs/superpowers/plans/
  - docs/generated/
  - docs/operating_system/planning-dispatch.md
  - docs/operating_system/repo-governance.md
  - scripts/validate_adoption_shape.py
  - tests/test_validate_adoption_shape.py
related_features: []
related_stages: []
---

# Planning Lineage Minimal Metadata And Validator Spec

## Triage

Layer: operating_system  
Feature type: MODIFY  
Summary: Replace redundant planning-lineage metadata with a nearest-parent model, then enforce the lineage contract through validation and a generated roll-up surface.  
Reasoning: The planning ladder now exists in the repo, but the metadata is at risk of repeating the same upstream fact in multiple downstream layers. That creates drift pressure and violates the operating principle that canonical truth should flow downward while downstream layers derive views from it.  
Invariants:

- canonical truth flows downward from intent to roadmap to workstream to thread
- downstream artifacts store only their nearest necessary lineage parent
- full ancestry is derived, not manually restated
- completion rolls upward from plans to specs/threads/workstreams/roadmap
- generated lineage/progress views do not become a second manual truth layer
- validator enforcement should prevent both missing lineage and redundant lineage

Dependencies:

- `docs/intent/master-workstream-roadmap.md`
- `docs/intent/workstreams/`
- `docs/intent/workstreams/threads/`
- `docs/superpowers/specs/`
- `docs/superpowers/plans/`
- `docs/generated/`
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
  - `docs/intent/master-workstream-roadmap.md`
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

The repo now has a meaningful planning ladder:

`intent -> master workstream roadmap -> registered workstreams -> bounded change thread files -> specs -> implementation plans`

But the current metadata shape still risks repeating the same lineage fact in
more than one place.

Examples of redundancy pressure:

1. workstreams may not need to restate the single roadmap relationship in every
   file
2. thread files can express their workstream parent through both folder path and
   frontmatter
3. specs and plans currently rely on `parent_workstream`, but once a thread
   becomes explicit, the workstream should be derivable from the thread
4. future lineage rollout could easily drift into storing the full ancestry
   chain manually on every downstream artifact

That would be the wrong model. It would create maintenance burden and make
validator enforcement harder than necessary.

## Goal

Adopt a minimal planning-lineage metadata model where each artifact stores only
its own identity plus its nearest necessary parent, then derive full ancestry
and progress roll-up through validation and generated views.

## Non-Goals

This spec does not add the deferred `operating_system` thread branch yet.

This spec does not redesign unrelated feature/stage metadata systems.

This spec does not turn the generated lineage view into a manual source-of-truth
file.

This spec does not require percent-complete style fields across planning docs.

## Canonical Lineage Principle

Use this rule:

`Each layer stores only its own identity plus its nearest necessary parent. Everything else is derived.`

That means:

- upstream planning truth is authored once
- downstream artifacts do not restate the whole ancestry chain
- validators check references and derive consistency
- generated views assemble the full chain for inspection

## Recommended Minimal Metadata Model

### 1. Master roadmap

No extra lineage metadata is required beyond the file itself being the canonical
planning root.

Canonical file:

- `docs/intent/master-workstream-roadmap.md`

### 2. Registered workstream

Recommended long-term frontmatter:

```yaml
---
workstream_id: <id>
status: active | proposed | paused | completed
---
```

Recommendation:

- keep `workstream_id`
- keep `status`
- deprecate `parent_intent` if the repo continues to use one canonical roadmap

Rationale:

- the registry location plus roadmap model already establish the upstream
  relationship
- repeating the same roadmap link in every workstream file is low-value
  duplication

### 3. Bounded change thread file

Recommended long-term frontmatter:

```yaml
---
thread_id: <workstream-id>.<thread-slug>
status: proposed | active | blocked | completed
---
```

Recommendation:

- keep `thread_id`
- keep `status`
- derive parent workstream from the folder path:
  - `docs/intent/workstreams/threads/<workstream-id>/`
- deprecate `parent_workstream` on thread files after migration

Rationale:

- the path already expresses the parent workstream relationship
- requiring both path and frontmatter for the same parent creates unnecessary
  redundancy

### 4. Spec

Recommended frontmatter:

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

Recommendation:

- add `parent_thread`
- derive `parent_workstream` from the referenced thread
- deprecate `parent_workstream` on specs after migration

Rationale:

- the thread is the nearest necessary planning parent
- the workstream is already available through thread lineage

### 5. Plan

Recommended frontmatter:

```yaml
---
layer: change
artifact_type: plan
status: proposed | active | completed | superseded
parent_thread: <thread-id>
parent_spec: <spec-path-or-id>
targets:
  - <path>
related_features: []
related_stages: []
---
```

Recommendation:

- add `parent_thread`
- add `parent_spec`
- derive `parent_workstream` from the referenced thread
- deprecate `parent_workstream` on plans after migration

Rationale:

- the thread is the execution parent
- the spec is the design parent
- the workstream should not be restated redundantly once thread lineage exists

## Derived Lineage View

Add one generated inspection surface:

- `docs/generated/planning_lineage.yaml`

This file should assemble:

- roadmap root
- registered workstreams
- bounded change thread files
- linked specs
- linked plans
- upward progress roll-up

This file is:

- generated
- derived
- validator-aware
- useful for inspection and drift review

This file is not:

- a hand-maintained source
- a second canonical planning system

## Completion Roll-Up Model

Truth flows downward, but completion rolls upward.

Use this conceptual roll-up:

- completed plan(s) provide evidence for downstream execution completion
- completed required spec/plan work closes a bounded change thread
- completed required threads advance a workstream
- completed required workstreams advance roadmap completion

Completion guidance:

- threads carry local status because they are execution-capable planning units
- workstreams carry roll-up status because they are durable delivery threads
- roadmap completion remains strategic, not task-board detail

## Validator Responsibilities

The validator should control both lineage presence and redundancy boundaries.

### Phase 1: Presence and path structure

Validator should enforce:

1. every workstream file has:
   - `workstream_id`
   - `status`
2. every thread file has:
   - `thread_id`
   - `status`
3. every spec has:
   - `parent_thread`
4. every plan has:
   - `parent_thread`
   - `parent_spec`
5. thread files live under:
   - `docs/intent/workstreams/threads/<workstream-id>/`
6. `thread_id` matches the filename/path convention

### Phase 2: Reference consistency

Validator should enforce:

1. `parent_thread` resolves to a real thread file
2. `parent_spec` resolves to a real spec
3. plan and referenced spec agree on `parent_thread`
4. thread folder workstream matches the thread identity convention
5. no spec or plan floats without a valid thread parent

### Phase 3: Redundancy control

After migration, validator should enforce:

1. specs must not carry `parent_workstream`
2. plans must not carry `parent_workstream`
3. thread files must not carry `parent_workstream`
4. workstream files may warn on `parent_intent` if the single-roadmap model
   remains stable

This phase is important because without it, the repo can drift back into
re-entering upstream truth manually.

## Migration Strategy

Use a phased migration rather than a single hard cutover.

### Stage A: Introduce new lineage fields

- add `parent_thread` to specs
- add `parent_thread` and `parent_spec` to plans
- keep current fields temporarily while transition is in flight

### Stage B: Make generated lineage view available

- generate `docs/generated/planning_lineage.yaml`
- use it as the assembled inspection surface

### Stage C: Enforce reference consistency

- validator requires new fields
- validator confirms references resolve cleanly

### Stage D: Remove redundant lineage fields

- deprecate and then reject redundant `parent_workstream` usage on thread/spec/plan artifacts
- optionally deprecate `parent_intent` on workstreams if single-roadmap model is still true

## Prompt And Governance Implications

Prompt and governance docs should evolve to speak in the same minimal-lineage
language:

- workstream prompts should lead into explicit thread selection or creation
- spec prompts should assume a chosen thread
- plan prompts should assume a chosen thread and a chosen spec
- divergence/review prompts should inspect the derived lineage view rather than
  asking humans to reconstruct ancestry by hand

## Acceptance Criteria

- the repo defines a minimal nearest-parent planning metadata model
- specs and plans have a clear path to `parent_thread`
- plans have a clear path to `parent_spec`
- redundant lineage fields have a defined deprecation path
- a generated planning-lineage view is defined as the derived inspection surface
- validator phases are defined for presence, consistency, and redundancy control

## Recommendation

Adopt the minimal-lineage model and let the validator own both:

1. missing-parent prevention
2. redundant-parent prevention

That preserves the repo’s core design principle:

`canonical truth flows downward from upstream layers, and downstream layers derive views from it rather than re-entering it`
