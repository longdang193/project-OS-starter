---
layer: operating_system
artifact_type: spec
status: completed
parent_workstream: none
targets:
  - docs/intent/master-workstream-roadmap.md
  - docs/intent/workstreams/
  - docs/operating_system/planning-dispatch.md
  - docs/operating_system/repo-governance.md
  - docs/superpowers/specs/
  - docs/superpowers/plans/
related_features: []
related_stages: []
---

# Workstream Coverage And Bounded Change Governance Spec

## Triage

Layer: operating_system
Feature type: ADD
Summary: Define a precise governance model for roadmap coverage, registered workstreams, bounded change threads, progress tracking, and safe parallel execution.
Reasoning: The repo already has a master roadmap, registered workstreams, prompt templates, and validator-backed `parent_workstream` linkage. What is still missing is the explicit model that says how the roadmap is considered complete, how workstreams advance toward the end goal, where progress should be tracked, and how teams can execute in parallel without drifting.
Invariants:

- `docs/intent/master-workstream-roadmap.md` remains the strategic coverage layer, not a progress board.
- Registered workstreams under `docs/intent/workstreams/` should collectively cover the roadmap's major delivery threads.
- `operating_system` remains a parallel branch, not a fake product workstream.
- A bounded change thread is the practical execution unit beneath a workstream or the `operating_system` branch.
- Specs and plans should attach to bounded change threads rather than to vague, unbounded workstream intent.
- Parallel execution should happen across bounded change threads with clear ownership and dependency awareness.

Dependencies:

- `docs/intent/master-workstream-roadmap.md`
- `docs/intent/workstreams/`
- `docs/operating_system/planning-dispatch.md`
- `docs/operating_system/repo-governance.md`
- `docs/superpowers/specs/`
- `docs/superpowers/plans/`

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

The current planning system already has useful pieces:

- intent docs
- a master workstream roadmap
- a registry of named workstreams
- prompt templates for routing, gaps, fit review, and divergence review
- validator-backed `parent_workstream` linkage for specs and plans

But it still lacks a precise execution model for the space between
workstreams and specs/plans.

Today, the repo does not state clearly enough:

1. how to know whether the master roadmap is fully covered by registered
   workstreams
2. how a broad workstream turns into practical, executable slices
3. where progress should be tracked without turning the roadmap into a noisy
   execution diary
4. how to decide when multiple threads can advance in parallel safely
5. how to distinguish:
   - coverage tracking
   - workstream progress tracking
   - execution tracking
   - divergence review

Without that model, teams can easily:

- create workstreams that are too vague to execute
- confuse workstreams with specs or plans
- run parallel work directly against broad workstreams and collide
- lose sight of whether the roadmap is complete enough to reach the end goal
- drift between upstream intent and downstream execution

## Goal

Define the precise planning and execution ladder as:

`intent -> master workstream roadmap -> complete set of registered workstreams -> bounded change threads -> specs -> implementation plans -> execution`

Then define:

- what each layer owns
- where coverage and progress are tracked
- what the safe parallel execution unit is
- how divergence should be reviewed

## Non-Goals

This spec does not turn the master roadmap into a task board.

This spec does not require every workstream to explode into many child docs
immediately.

This spec does not add validator enforcement yet for J2BD completeness or
workstream progress.

This spec does not replace specs or implementation plans with workstream docs.

## Recommended Design

### 1. Adopt The Precise Ladder

Use this model consistently:

```text
intent
-> master workstream roadmap
-> registered workstreams
-> bounded change threads
-> specs
-> implementation plans
-> execution
```

Definitions:

- `master workstream roadmap`
  - strategic map of the major threads required to reach the end goal
- `registered workstreams`
  - the concrete named set of durable product-direction threads that together
    cover the roadmap
- `bounded change threads`
  - the discrete next slices of work under a workstream or the
    `operating_system` branch that can be designed, planned, and executed
- `specs`
  - bounded design artifacts for one change thread
- `implementation plans`
  - execution artifacts for one approved spec or bounded change

### 2. Separate Coverage From Progress

Use different layers for different questions:

- **Coverage tracking**
  - lives in the master roadmap
  - answers: "Do we have all major threads needed to reach the end goal?"

- **Workstream progress tracking**
  - lives in each registered workstream doc
  - answers: "How far along is this durable thread?"

- **Execution tracking**
  - lives in specs, plans, and completion state of bounded change threads
  - answers: "What concrete slices have been designed, planned, or executed?"

This avoids turning a strategic roadmap into a low-level progress log.

### 3. Define Registered Workstream Completeness

The registered workstreams should collectively satisfy the master roadmap.

That means the set should be reviewed for:

- missing major delivery threads
- duplicate or overlapping threads
- workstreams that are too vague to guide downstream work
- work that really belongs in `operating_system`

The working question becomes:

`Does the current set of registered workstreams completely and specifically cover the master roadmap well enough to reach the end goal?`

### 4. Introduce Bounded Change Threads As The Execution Unit

Parallel execution should not use broad workstreams directly as the unit of
work.

Instead, a workstream advances through bounded change threads:

- one discrete gap
- one discrete improvement slice
- one discrete design/execution thread

Each bounded change thread may then produce:

- a spec
- an implementation plan
- direct execution when already bounded and clear

This makes workstreams execution-capable without making them noisy or unstable.

### 5. Track Progress In Workstream Docs

Workstream docs should become the stable progress surface for each durable
thread.

Recommended content to add over time:

- workstream purpose
- jobs to be done / desired outcomes
- success signals
- out-of-scope notes
- dependencies on other workstreams
- open bounded change threads
- completed bounded change threads
- linked specs and plans
- open gaps
- last alignment review date

The exact field shape can stay lightweight at first, but the repo should define
these as the intended progress concepts.

### 6. Define Safe Parallel Progress Rules

Parallel work is encouraged, but the unit of parallelism should be the bounded
change thread, not the broad workstream.

Healthy parallel execution conditions:

- the bounded changes have clear ownership
- dependencies are explicit
- shared source-of-truth surfaces are minimized or coordinated
- each parallel slice is independently understandable
- each slice has its own spec/plan when needed

Unsafe parallel execution patterns:

- two broad, ambiguous efforts under the same workstream with no boundary
- multiple threads editing the same workstream/governance/source docs without
  coordination
- parallel work where one slice depends materially on unfinished decisions in
  another

### 7. Distinguish Three Review Types

The repo should explicitly distinguish:

1. **Coverage review**
   - do the registered workstreams fully cover the roadmap/end goal?

2. **Progress review**
   - how far along is each workstream?

3. **Divergence review**
   - does actual execution still align with the roadmap/workstreams?

These should not be conflated into one fuzzy "status review."

## Suggested Documentation Outcomes

This governance model likely wants:

- a guide for roadmap coverage and workstream completeness
- a guide or section for bounded change thread usage
- a guide or section for workstream progress tracking
- a guide or cadence for divergence review

The first pass can be guidance-first rather than validator-first.

## Acceptance Criteria

- The precise planning ladder is documented using:
  - roadmap
  - registered workstreams
  - bounded change threads
  - specs
  - implementation plans
  - execution
- Coverage, workstream progress, execution progress, and divergence review are
  clearly separated.
- The docs state that parallel work should be organized around bounded change
  threads rather than broad workstreams.
- The guidance preserves `operating_system` as a parallel branch instead of
  forcing all work into product workstreams.

## Risks

If the model is too abstract, teams may continue to skip from workstreams
straight to execution.

If bounded change threads are described too formally too early, the system
could become heavier than needed.

If progress tracking is pushed back into the master roadmap, that doc will
become noisy and drift-prone.

## Recommendation

Adopt this governance model as the next maturity step.

The repo already has the roadmap, the registry, the prompts, and the validator
hooks. The missing piece is the precise execution bridge: a complete set of
registered workstreams feeding bounded change threads that can advance in
parallel without losing alignment with the end goal.
