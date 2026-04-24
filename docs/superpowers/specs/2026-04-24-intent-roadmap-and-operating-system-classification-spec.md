---
layer: operating_system
artifact_type: spec
status: completed
parent_workstream: none
targets:
  - docs/intent/README.md
  - docs/intent/master-workstream-roadmap.md
  - docs/operating_system/planning-dispatch.md
  - docs/operating_system/repo-governance.md
  - .agents/skills/brainstorming/SKILL.md
  - .agents/skills/planning-dispatch/SKILL.md
  - .agents/skills/writing-plans/SKILL.md
related_features: []
related_stages: []
---

# Intent Roadmap And Operating-System Classification Spec

## Triage

Layer: operating_system
Feature type: CHANGE
Summary: Introduce a master intent-to-workstreams roadmap while preserving `operating_system` as a parallel classification branch rather than collapsing it into workstreams.
Reasoning: The repo already distinguishes `intent`, `operating_system`, `workstream`, and `change`, but it lacks one explicit top-down planning structure that starts from intent and routes major work either into product workstreams or into operating-system method work.
Invariants:

- `docs/intent/` remains the canonical source for project what-and-why.
- `operating_system` remains a first-class classification, not a fake workstream.
- Specs and plans remain bounded execution artifacts under `docs/superpowers/`.
- Canonical truth still flows downward from upstream owning layers.
- The new structure must reduce drift from original intent without creating a second competing source of truth.

Dependencies:

- `docs/intent/README.md`
- `docs/operating_system/planning-dispatch.md`
- `docs/operating_system/repo-governance.md`
- `.agents/skills/brainstorming/SKILL.md`
- `.agents/skills/planning-dispatch/SKILL.md`
- `.agents/skills/writing-plans/SKILL.md`

Affected stages:

- none directly

Affected features:

- none directly

Primary lens: cross-cutting

Affected docs:

- feature_source: none
- feature_yaml: none
- feature_lineage: none
- feature_history: none
- stage_source: none
- stage_contract: none
- feature_docs: none
- cross_cutting_docs: none
- operating_system_docs:
  - `docs/operating_system/planning-dispatch.md`
  - `docs/operating_system/repo-governance.md`
- readme: none
- generated: none

Generated refresh required: no
Capability IDs: none
Invariant IDs: none
Spec needed: yes
Plan needed: yes

## Problem

The repo already has a useful planning classification:

- `intent`
- `operating_system`
- `workstream`
- `change`

That gives us a layer model, but it does not yet give us a strong top-down
artifact that answers:

- how major work should derive from project intent
- how to keep long-running work aligned with original goals
- how to distinguish product workstreams from repo-method work

Without that bridge, specs and plans can still feel too local:

- they may be valid in isolation
- they may follow the planning gate correctly
- but they can still drift from the original purpose because the intermediate
  roadmap layer is weak or missing

At the same time, we should not solve that by forcing everything into
workstreams. Repo governance, validation, publication, planning method, agent
instruction behavior, and sync rules are not product workstreams. They are
`operating_system` work.

So the missing structure is not:

`intent -> workstream only`

It is:

`intent -> master roadmap -> workstream or operating_system -> change -> spec/plan`

## Goal

Create a clearer planning hierarchy that starts from intent, translates intent
into durable workstream direction, and explicitly preserves `operating_system`
as a parallel branch for repo-method work.

## Non-Goals

This spec does not remove the four-layer classification.

This spec does not turn `operating_system` into a workstream bucket.

This spec does not require every tiny change to create a new workstream doc.

This spec does not replace specs or implementation plans with roadmap prose.

This spec does not create a product feature registry in `docs/intent/`.

## Recommended Model

Use this hierarchy:

```text
docs/intent/
  -> canonical project purpose and outcome sources
  -> master workstream roadmap

master workstream roadmap
  -> durable product workstreams derived from intent
  -> explicit operating-system branch for repo-method work

workstream or operating_system branch
  -> bounded changes

bounded changes
  -> spec
  -> implementation plan
  -> execution
```

The key clarification is that `operating_system` is not downstream of a product
workstream. It is a sibling branch in the planning model.

## Canonical Classification Tree

The guide and workflow should make this tree explicit:

```text
intent
├─ workstreams
│  ├─ workstream-a
│  ├─ workstream-b
│  └─ ...
└─ operating_system
   ├─ planning and routing
   ├─ validation and sync
   ├─ publication and private/public governance
   ├─ instruction surfaces and agent workflow
   └─ other repo-method concerns
```

Then:

- `change` is a bounded slice inside either a workstream or the
  operating-system branch
- specs/plans are the design/execution artifacts for those bounded slices

## Intent-Owned Roadmap

The master roadmap should live under `docs/intent/`, because it is still about
translating project purpose into major work, not about repo mechanics.

Recommended new anchor:

- `docs/intent/master-workstream-roadmap.md`

Purpose of that doc:

- summarize the durable workstreams that serve the project intent
- link each workstream back to specific intent outcomes, promises, or
  constraints
- explicitly name what belongs to the operating-system branch instead of the
  product-workstream branch
- give future specs/plans a parent thread to attach to

It should not become:

- a duplicate of all specs/plans
- a release log
- a fake operating-system manual

## Workstream Docs

If the roadmap becomes useful, allow follow-on workstream docs under
`docs/intent/workstreams/` or a similarly explicit structure.

Example:

```text
docs/intent/
  README.md
  project-charter.md
  stakeholders.md
  success-outcomes.md
  constraints-and-non-goals.md
  master-workstream-roadmap.md
  workstreams/
    workstream-<id>.md
```

These workstream docs would:

- describe the durable thread
- point back to intent
- describe success signals
- define the scope of downstream specs/plans

They should still stay upstream of specs/plans, not turn into giant execution
logs.

## Operating-System Changes

`docs/operating_system/` should change in a lighter way.

It should not own the master roadmap.

Instead, it should:

- explain the classification model
- explain that the roadmap starts from intent
- explain that the next routing question is:
  - does this belong to a product workstream?
  - or does this belong to `operating_system`?
- explain that `change` is a bounded slice under either branch
- explain how specs/plans record `parent_workstream`

So the operating-system layer becomes the method guide for using the roadmap,
not the owner of the roadmap itself.

## Required Guidance Changes

### `docs/intent/README.md`

Should explain that intent docs are upstream source and that the master roadmap
translates purpose into durable work.

### `docs/intent/master-workstream-roadmap.md`

Should become the canonical top-down planning bridge from intent into major
work.

### `docs/operating_system/planning-dispatch.md`

Should be updated so its routing story becomes:

1. start from owning source
2. if starting from intent, check the master roadmap
3. decide whether the next branch is `workstream` or `operating_system`
4. then produce triage
5. then route to spec/plan

### `docs/operating_system/repo-governance.md`

Should point readers to the intent-owned roadmap and explain that
`operating_system` remains the repo-method branch rather than a product
workstream layer.

## Relationship To Existing Metadata

The existing metadata can keep working:

- `layer: intent | operating_system | workstream | change`
- `parent_workstream: <id> | none`

But the meaning should become more explicit:

- `parent_workstream` should refer to a real roadmap/workstream thread when the
  artifact is part of product-direction work
- operating-system changes may still use `parent_workstream: none` or a later
  operating-system threading scheme if we decide that is useful

Do not force `operating_system` artifacts into fake product workstream IDs.

## Why This Helps

Benefits:

- less drift from original project intent
- clearer distinction between product work and repo-method work
- fewer floating specs/plans with weak upstream anchors
- easier prioritization and pruning
- better onboarding because the planning tree becomes easier to explain

## Recommendation

Use the smallest strong move:

1. add the master roadmap under `docs/intent/`
2. preserve `operating_system` as a sibling branch in the planning model
3. update planning-dispatch and governance docs to make that tree explicit
4. keep specs/plans as bounded downstream artifacts

That gives us a stronger top-down planning system without collapsing unlike
kinds of work into the same bucket.

## Acceptance Criteria

- the repo has one intent-owned master roadmap that translates intent into
  durable workstreams
- the planning model explicitly preserves `operating_system` as a first-class
  classification branch
- planning guidance explains `intent -> workstream or operating_system ->
  change -> spec/plan`
- `docs/intent/` remains upstream purpose truth rather than becoming a process
  dump
- specs/plans gain a clearer upstream anchor without replacing existing source
  layers
