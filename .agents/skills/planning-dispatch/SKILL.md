---
name: planning-dispatch
description: Apply at the start of any task requiring planning, design, or implementation — enforces the triage gate and routing decision tree. Determines the correct next skill and ensures feature source (`docs/features/*/feature.source.yaml`) and generated contracts are checked before any spec or plan is written.
---
# Planning Dispatch

## When to Apply

Apply this skill at the start of any task involving planning, design, or implementation routing.

It decides:

- what to read first
- whether the work is a managed feature change
- which skill should handle the next step

## Core Principle

> Plan before building.  
> Classify before planning.  
> Classify by reading the current feature contract first, and by naming affected stages when the work is stage-heavy.

Read in this order:

1. `code/`
2. `docs/features/*/feature.source.yaml` and generated `docs/features/*/<feature_id>.yaml`
3. `docs/stages/<stage_id>.source.yaml` and generated `docs/stages/<stage_id>.yaml` when stage-aware work is central to the task
4. `docs/operating_system/stage-lifecycle.md` when architectural or pipeline stages are central to the work
5. `docs/features/<feature_id>/*`
5. `docs/generated/*`
6. `docs/*.md`
7. `README.md`

When one feature folder is in scope, refine step 4 to the minimum truthful set:

- `feature.source.yaml` first
- generated `<feature_id>.yaml` only when the assembled current contract is needed
- `lineage.generated.yaml` only for ownership, evidence, or drift work
- `history.md` only for narrative context
- do not read the full feature folder by default

## Ownership Clarification

This skill does **not** write specs or plans. It routes work.

- **`brainstorming`** explores options, presents design, writes the spec, then hands off
- **`planning-dispatch`** produces the triage block and routes to the next skill
- **`writing-plans`** writes the implementation plan from a confirmed design/spec

## Pre-Planning Triage Gate

Before writing a spec or plan, produce triage. This is the gate.

### Step 1 — Find the current feature source

- [ ] Check `docs/features/*/feature.source.yaml` for the owning feature source
- [ ] Use generated `docs/features/*/<feature_id>.yaml` and `lineage.generated.yaml` for current-state and evidence lookup only
- [ ] Identify affected stages when the work is pipeline-heavy, boundary-heavy, or architecture-heavy
- [ ] Use `docs/generated/*` only for lookup if needed
- [ ] Read `docs/*.md` only if explanation or rationale is needed
- [ ] If related feature exists: this is usually `MODIFY` or `REPLACE`
- [ ] If not: this is `ADD`

### Step 2 — Produce Triage Block

Required:

```text
Feature type: ADD | MODIFY | REPLACE
Summary: <1 sentence>
Reasoning: <why this classification>
Invariants:
  - <must hold true>
Dependencies:
  - <if known>
Affected stages:
  - <stage_id> | none
Affected features:
  - <feature_id> | none
Primary lens: stage | feature | mixed | cross-cutting
Affected docs:
  feature_source: `docs/features/<feature_id>/feature.source.yaml` | none
  feature_yaml: `docs/features/<feature_id>/<feature_id>.yaml` | none
  feature_lineage: `docs/features/<feature_id>/lineage.generated.yaml` | none
  feature_history: `docs/features/<feature_id>/history.md` | none
  stage_source: `docs/stages/<stage_id>.source.yaml` | none
  stage_contract: `docs/stages/<stage_id>.yaml` | none
  feature_docs:
    - `docs/features/<feature_id>/<doc>.md`
  cross_cutting_docs:
    - `docs/<doc>.md`
    - `docs/operating_system/<doc>.md`
  readme: `README.md` | none
  generated:
    - `docs/generated/<file>` | none
Generated refresh required: yes | no
Capability IDs:
  - <capability_id> | none
Invariant IDs:
  - <invariant_id> | none
Spec needed: yes | no
Plan needed: yes | no
````

`<feature_id>` is placeholder notation in the triage template. The real
generated contract path uses the concrete feature id as the filename.

Optional for risky work:

```text
Rollback trigger:
Rollback method:
Migration needed: yes | no
Risk level: low | medium | high
```

### Triage Gate Rules

- a spec cannot be written without triage
- a plan cannot be written without triage
- if an affected feature exists, its `docs/features/<feature_id>/feature.source.yaml` and generated contract path must be identified before proceeding
- stage-heavy work must name affected stages before proceeding
- stage-heavy work must name both the stage source and generated stage contract paths before proceeding
- triage should name the exact doc targets, not just whether docs are needed
- generated files are never the source of truth; use them only to find the source
- `scripts/sync_architecture_docs.py` is the canonical architecture sync/check workflow; narrower metadata commands are bounded helpers rather than parallel default paths

## Routing Decision Tree

After triage, route to the correct skill:

```text
Exploring an idea or comparing approaches
└── brainstorming

Design is clear enough; implementation plan needed
└── writing-plans

Approved plan exists; execute with checkpoints
└── executing-plans

Multiple independent workstreams
└── dispatching-parallel-agents
```

## Scenario Reference

### New Feature Request

1. Check `docs/features/*/feature.source.yaml`
2. Classify as `ADD`
3. Produce triage
4. Create or plan creation of the new `feature.source.yaml`
5. Dispatch: brainstorming → writing-plans → execution
6. Refresh `docs/generated/*` after source changes

### Existing Feature Change

1. Find the existing `docs/features/<feature_id>/feature.source.yaml`
2. Classify as `MODIFY` or `REPLACE`
3. Produce triage
4. Update existing feature source or create replacement feature source
5. Dispatch as needed
6. Refresh `docs/generated/*` after source changes

### Cross-Cutting Operating-System or Method Change

1. Confirm no managed feature contract is the primary lifecycle owner yet
2. Use `Affected features: none` if this is truly cross-cutting
3. Name affected stages plus `stage_source` / `stage_contract` paths if the work is stage-aware by design
4. Keep docs under cross-cutting paths rather than inventing a fake feature
5. Note whether the work is likely to produce a reusable memory update during closeout
6. Dispatch as needed


### Bounded Hygiene Or Drift Cleanup

1. Confirm the change is really hygiene, drift cleanup, or local cleanup rather than a hidden feature change
2. Use `Affected features: none` when no managed feature owns the lifecycle
3. Keep the primary lens as `feature` or `cross-cutting`, whichever is more truthful
4. Name the exact cross-cutting docs or rules that own the cleanup
5. Do not force a fake feature contract just to satisfy the planning template
6. Still require explicit triage before spec or plan work
### Bug Fix

1. Check affected feature source
2. If behavior changes meaningfully, follow `MODIFY`
3. If not, fix code and update docs only if needed

### Exploration Before Commitment

1. Use `brainstorming`
2. Once direction is clear, produce triage
3. Then route to spec/plan as needed

## Anti-Patterns

- planning before reading current feature source
- skipping stage classification when the work is obviously stage-heavy
- skipping triage
- writing a plan before the design is clear
- using generated files as the source of truth
- forgetting to refresh `docs/generated/*` after source-layer changes
- creating or updating feature contracts after implementation instead of before or with it

## Related Skills

- **`doc-system-lifecycle`**: governs the 5-layer doc system, naming, frontmatter, and generated discovery
- **`brainstorming`**: explores ideas and writes the spec
- **`writing-plans`**: writes the implementation plan
- **`executing-plans`**: executes an approved plan
- **`subagent-driven-development`**: recommended execution path when task-by-task delegation is helpful

