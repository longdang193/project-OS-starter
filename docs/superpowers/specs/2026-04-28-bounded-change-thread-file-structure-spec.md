---
layer: operating_system
artifact_type: spec
status: completed
parent_workstream: none
targets:
  - docs/intent/workstreams/
  - docs/intent/workstream-coverage-and-progress-guide.md
  - docs/operating_system/prompt_templates/
  - docs/operating_system/skill-planning-dispatch.md
  - docs/operating_system/governance/repo-governance.md
  - docs/superpowers/specs/
  - docs/superpowers/plans/
related_features: []
related_stages: []
---

# Bounded Change Thread File Structure Spec

## Triage

Layer: operating_system
Feature type: ADD
Summary: Add an explicit bounded-change thread folder structure and lightweight thread-file schema beneath registered workstreams, plus the prompt adjustments needed to use that structure naturally.
Reasoning: The repo now has a clear conceptual ladder from master roadmap to workstreams to bounded change threads to specs/plans, but bounded change threads still live mostly as a concept or as sections inside workstream docs. Making them explicit files would make the worktree itself teach the planning process, make parallel execution units visible, and give specs/plans a clearer upstream parent.
Invariants:

- The master roadmap remains strategic and does not become a thread tracker.
- Registered workstreams remain the durable product-direction layer.
- Bounded change threads stay lightweight and execution-oriented.
- Specs and plans remain downstream artifacts rather than being replaced by thread files.
- The first pass should not require a full `operating_system` thread branch yet.
- Prompt updates should make the new thread layer explicit without duplicating every existing prompt.

Dependencies:

- `docs/intent/workstreams/`
- `docs/intent/workstream-coverage-and-progress-guide.md`
- `docs/operating_system/prompt_templates/`
- `docs/operating_system/skill-planning-dispatch.md`
- `docs/operating_system/governance/repo-governance.md`
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
  - `docs/operating_system/prompt_templates/`
  - `docs/operating_system/skill-planning-dispatch.md`
  - `docs/operating_system/governance/repo-governance.md`
- readme: none
- generated: none

Generated refresh required: no
Capability IDs: none
Invariant IDs: none
Spec needed: yes
Plan needed: yes

## Problem

The current governance model says:

`master workstream roadmap -> registered workstreams -> bounded change threads -> specs -> implementation plans`

But the filesystem still expresses only some of that ladder directly:

- roadmap file exists
- registered workstream files exist
- specs and plans exist
- bounded change threads are still mostly implicit

That leaves a few problems:

1. the worktree does not yet make the execution bridge obvious
2. bounded change threads are harder to review as durable units
3. specs/plans do not yet have a clearly visible upstream thread file to attach
   to
4. prompt outputs for bounded change decomposition still feel underspecified
5. parallel work lanes are conceptually clearer than they are structurally

## Goal

Make bounded change threads explicit in the worktree with a lightweight thread
file structure that sits between registered workstreams and downstream
specs/plans.

## Non-Goals

This spec does not add the full `operating_system` thread branch yet.

This spec does not move specs or plans out of `docs/superpowers/`.

This spec does not add validator enforcement in the first pass unless the shape
proves stable enough later.

This spec does not turn bounded change threads into large narrative documents.

## Recommended Folder Structure

Add a `threads/` subtree under `docs/intent/workstreams/`.

Recommended shape:

```text
docs/
└─ intent/
   └─ workstreams/
      ├─ README.md
      ├─ <workstream-id>.md
      └─ threads/
         ├─ README.md
         └─ <workstream-id>/
            ├─ 01-<thread-slug>.md
            ├─ 02-<thread-slug>.md
            └─ ...
```

The key point is:

- one registered workstream file per durable thread
- one folder of bounded change thread files beneath each registered workstream

## Recommended Thread File Shape

Keep thread files lightweight.

Suggested frontmatter:

```yaml
---
thread_id: <workstream-id>.<thread-slug>
parent_workstream: <workstream-id>
status: proposed | active | blocked | completed
---
```

Suggested body sections:

- goal
- why now
- dependencies
- shared surfaces
- linked spec
- linked plan
- notes

Thread files should answer:

- what specific slice this is
- what it touches
- what it depends on
- whether it is still open
- what spec/plan came out of it

## Ownership Model

Use these layers distinctly:

- `master-workstream-roadmap.md`
  - strategic coverage only
- `workstreams/<workstream-id>.md`
  - durable thread identity and progress roll-up
- `workstreams/threads/<workstream-id>/*.md`
  - execution-capable bounded change units
- `docs/superpowers/specs/*.md`
  - bounded design for one thread
- `docs/superpowers/plans/*.md`
  - bounded execution for one approved spec

## Prompt Adjustments

The current prompt pack should be adjusted so the new thread layer becomes
explicit.

### Existing prompts that should change

#### `bounded-change-thread-build-prompt.md`

Today it mainly implies a decomposition output.
It should explicitly say the expected output is a proposed set of thread files
or a thread breakdown that maps directly into thread files.

#### `workstream-to-spec-prompt.md`

It should no longer jump straight from workstream to spec by default.
It should either:

- assume a bounded change thread is already chosen
- or tell the user to use the bounded-change-thread build prompt first

#### `parallel-bounded-change-planning-prompt.md`

It should name thread files directly as the planning unit when they exist.

### New prompt adjustments to README / flow

The README should express the ladder more concretely:

`intent -> master roadmap -> registered workstream set -> bounded change thread files -> specs -> plans -> execution`

## Suggested Guidance Updates

The surrounding docs should state clearly:

- bounded change threads are now explicit file surfaces
- workstream docs should link to their thread folder
- specs/plans should link back to thread files
- progress can now be read at three levels:
  - roadmap completeness
  - workstream progress
  - thread progress

## Acceptance Criteria

- The repo documents an explicit `threads/` subtree beneath registered
  workstreams.
- Thread files have a lightweight recommended schema.
- The prompt pack is updated so bounded change thread construction and use are
  explicit.
- The new structure preserves the distinction between workstreams, threads,
  specs, and plans.

## Risks

If thread files become too detailed, they will duplicate specs/plans.

If the structure is introduced without prompt updates, users may keep skipping
the thread layer.

If validation is added too early, the process may become heavier than needed.

## Recommendation

Adopt explicit bounded change thread files as the next structural improvement.
That gives the planning model a clear filesystem expression while still keeping
the thread layer light and execution-oriented.
