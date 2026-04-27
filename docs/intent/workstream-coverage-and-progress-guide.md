# Workstream Coverage And Progress Guide

Use this guide to keep the planning ladder precise, check whether the roadmap
is fully covered, track workstream progress, and advance work in parallel
without drifting.

## The Precise Ladder

Use this model consistently:

```text
intent
-> master workstream roadmap
-> complete set of registered workstreams
-> bounded change threads
-> specs
-> implementation plans
-> execution
```

Definitions:

- `intent`
  - the end goal, outcomes, constraints, and non-goals
- `master workstream roadmap`
  - the strategic map of the major threads required to reach the end goal
- `registered workstreams`
  - the concrete named set of durable product-direction threads that together
    cover the roadmap
- `bounded change threads`
  - the discrete execution-capable slices beneath a workstream or the
    `operating_system` branch
- `specs`
  - bounded design artifacts for one change thread
- `implementation plans`
  - bounded execution artifacts for one approved spec or change

## What Each Layer Tracks

Keep these responsibilities separate.

### 1. Coverage tracking

Lives in:

- [master-workstream-roadmap.md](C:/Users/HOANG%20PHI%20LONG%20DANG/repos/project-OS-starter/docs/intent/master-workstream-roadmap.md)

Answers:

- do we have all major threads needed to reach the end goal?
- are any major jobs to be done still unowned?
- are some registered workstreams overlapping or too vague?

Do not turn the roadmap into a progress board.

### 2. Workstream progress tracking

Lives in:

- [docs/intent/workstreams/](C:/Users/HOANG%20PHI%20LONG%20DANG/repos/project-OS-starter/docs/intent/workstreams)

Answers:

- how far along is this durable thread?
- what is done?
- what remains?
- what bounded change threads should advance next?

### 3. Execution tracking

Lives in:

- [docs/superpowers/specs/](C:/Users/HOANG%20PHI%20LONG%20DANG/repos/project-OS-starter/docs/superpowers/specs)
- [docs/superpowers/plans/](C:/Users/HOANG%20PHI%20LONG%20DANG/repos/project-OS-starter/docs/superpowers/plans)

Answers:

- what bounded slices have been designed?
- what slices have plans?
- what has been executed?

### 4. Divergence review

Uses:

- the roadmap
- the registered workstreams
- downstream specs/plans/execution

Answers:

- does actual execution still align with the roadmap and workstreams?
- what has gone missing, stale, or off-roadmap?

## Coverage Review

The registered workstreams should collectively cover the master roadmap.

Use this question:

`Does the current set of registered workstreams completely and specifically cover the roadmap well enough to reach the end goal?`

Review for:

- missing major delivery threads
- duplicate or overlapping workstreams
- workstreams that are too vague to guide downstream work
- product work that really belongs in `operating_system`
- operating-system work incorrectly forced into product workstreams

Good output from a coverage review:

- confirm the set is complete enough for now
- add a missing workstream
- merge overlapping workstreams
- split a vague workstream
- reclassify a thread into `operating_system`

## Registered Workstream Progress

Each workstream doc should stay small, but it should be able to answer:

- why this thread exists
- what jobs to be done or outcomes it serves
- what success looks like
- what does not belong here
- what bounded change threads are open
- what bounded change threads are already completed
- what specs/plans are linked
- what gaps remain

Recommended progress concepts for workstream docs:

- `workstream purpose`
- `jobs to be done`
- `success signals`
- `depends on`
- `open bounded change threads`
- `completed bounded change threads`
- `linked specs`
- `linked plans`
- `open gaps`
- `last alignment review`

The exact structure can stay lightweight, but those ideas should be present.

## Bounded Change Threads

A workstream is not the unit of execution.

The practical execution unit is the **bounded change thread**:

- one discrete gap
- one discrete improvement slice
- one discrete design/execution thread

Each bounded change thread may produce:

- a spec
- an implementation plan
- direct execution when already bounded and clear

Use bounded change threads when:

- you want to design or execute a specific next slice
- you want safe parallel progress
- you want to avoid vague workstream-wide efforts

## Parallel Execution Rules

Parallel work is encouraged across bounded change threads, not directly across
broad workstreams.

Healthy parallel conditions:

- ownership is clear
- dependencies are explicit
- shared source-of-truth surfaces are minimized or coordinated
- each slice is independently understandable
- each slice has its own spec/plan when needed

Unsafe parallel patterns:

- two broad efforts under the same workstream with no boundary
- multiple threads editing the same workstream/governance/source docs without
  coordination
- parallel work where one slice depends on unfinished decisions in another

Use this simple rule:

`Parallelize bounded change threads, not vague workstream intent.`

## Three Distinct Review Types

Keep these reviews separate:

1. `coverage review`
   - do the registered workstreams fully cover the roadmap/end goal?

2. `progress review`
   - how far along is each workstream?

3. `divergence review`
   - does execution still match roadmap/workstream intent?

Do not collapse them into one fuzzy status ritual.

## Prompt And Artifact Routing

Use these prompts when helpful:

- roadmap completeness questions:
  - [roadmap-gap-prompt.md](C:/Users/HOANG%20PHI%20LONG%20DANG/repos/project-OS-starter/docs/operating_system/prompt_templates/roadmap-gap-prompt.md)
- route roadmap into the right workstream:
  - [roadmap-to-workstream-prompt.md](C:/Users/HOANG%20PHI%20LONG%20DANG/repos/project-OS-starter/docs/operating_system/prompt_templates/roadmap-to-workstream-prompt.md)
- route a workstream into the next bounded design slice:
  - [workstream-to-spec-prompt.md](C:/Users/HOANG%20PHI%20LONG%20DANG/repos/project-OS-starter/docs/operating_system/prompt_templates/workstream-to-spec-prompt.md)
- review roadmap/workstream vs execution:
  - [roadmap-vs-execution-divergence-prompt.md](C:/Users/HOANG%20PHI%20LONG%20DANG/repos/project-OS-starter/docs/operating_system/prompt_templates/roadmap-vs-execution-divergence-prompt.md)

## Anti-Patterns

- using the master roadmap as a task board
- treating a workstream as if it were already a spec or plan
- running parallel work directly against a broad workstream with no bounded
  change split
- tracking progress only in scattered specs/plans with no workstream roll-up
- assuming roadmap coverage is complete just because some workstreams exist
