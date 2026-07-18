---
layer: operating_system
artifact_type: plan
status: completed
parent_workstream: none
targets:
  - docs/operating_system/prompt_templates/
  - docs/intent/workstream-coverage-and-progress-guide.md
  - docs/operating_system/planning/planning-dispatch.md
  - docs/operating_system/governance/repo-governance.md
  - docs/superpowers/specs/2026-04-27-parallel-bounded-change-planning-prompt-spec.md
related_features: []
related_stages: []
---

# Parallel Bounded Change Planning Prompt Implementation Plan

**Feature Source:** `none`
**Feature Contract:** `none`
**Spec:** `docs/superpowers/specs/2026-04-27-parallel-bounded-change-planning-prompt-spec.md`
**Type:** add
**Plan Layer:** operating_system
**Plan Status:** completed

> **For agentic workers:** Use `skill-executing-plans` or `skill-subagent-driven-development` to implement task-by-task.

**Goal:** Add a prompt template that helps users decide which bounded change threads can run in parallel safely, what should stay sequential, and how ownership should be split.

**Architecture:** Create a dedicated `parallel-bounded-change-planning` prompt under the prompt pack, then update the prompt-pack README and the nearby workstream/planning/governance docs so the repo’s “bounded change threads are the safe parallel unit” rule becomes directly usable.

**Key Invariants:**
- the prompt reasons about bounded change threads, not vague workstreams
- it distinguishes independent slices from dependency-coupled slices
- it makes shared surface risk explicit
- it keeps `operating_system` visible when the work is repo-method work

**Rollout / Revert:**
- rollback_trigger: the prompt overlaps too heavily with generic planning prompts or encourages unsafe optimism about parallelism
- rollback_method: remove the prompt and retain only wording improvements that still clarify the bounded-change execution rule

---

## Triage

Layer: operating_system
Feature type: ADD
Summary: Add a dedicated prompt for safe parallel planning across bounded change threads.
Reasoning: This is repo-method guidance that turns the bounded-change parallelism rule into a practical invocation surface.
Invariants:
  - bounded change threads remain the safe execution unit
  - shared surfaces and dependencies must be made explicit
  - the prompt pack should stay concise and actionable
Dependencies:
  - `docs/operating_system/prompt_templates/`
  - `docs/intent/workstream-coverage-and-progress-guide.md`
  - `docs/operating_system/planning/planning-dispatch.md`
  - `docs/operating_system/governance/repo-governance.md`
Affected stages:
  - none
Affected features:
  - none
Primary lens: cross-cutting
Affected docs:
  feature_source: none
  feature_yaml: none
  feature_lineage: none
  feature_history: none
  stage_source: none
  stage_contract: none
  feature_docs:
    - none
  cross_cutting_docs:
    - none
  operating_system_docs:
    - `docs/operating_system/prompt_templates/`
    - `docs/operating_system/planning/planning-dispatch.md`
    - `docs/operating_system/governance/repo-governance.md`
  readme: none
  generated:
    - none
Generated refresh required: no
Capability IDs:
  - none
Invariant IDs:
  - none
Spec needed: yes
Plan needed: yes

## Files To Create

```text
docs/operating_system/prompt_templates/parallel-bounded-change-planning-prompt.md
```

## Files To Modify

```text
docs/operating_system/prompt_templates/README.md
docs/intent/workstream-coverage-and-progress-guide.md
docs/operating_system/planning/planning-dispatch.md
docs/operating_system/governance/repo-governance.md
docs/superpowers/specs/2026-04-27-parallel-bounded-change-planning-prompt-spec.md
docs/superpowers/plans/2026-04-27-12-10-parallel-bounded-change-planning-prompt-plan.md
```

## Task 1: Add The Parallel Planning Prompt

**Files:**
- Create: `docs/operating_system/prompt_templates/parallel-bounded-change-planning-prompt.md`

- [x] Step 1: Add a short prompt for workstream or bounded-change sets in scope.
- [x] Step 2: Make shared surfaces and dependency checks explicit.
- [x] Step 3: Make the expected output include parallel lanes, sequencing warnings, ownership boundaries, and next artifacts.

## Task 2: Rewire Guidance

**Files:**
- Modify: `docs/operating_system/prompt_templates/README.md`
- Modify: `docs/intent/workstream-coverage-and-progress-guide.md`
- Modify: `docs/operating_system/planning/planning-dispatch.md`
- Modify: `docs/operating_system/governance/repo-governance.md`

- [x] Step 1: Add the prompt to the README with a clear safe-parallelism use case.
- [x] Step 2: Update the workstream coverage/progress guide so it points to the new prompt for the bounded-change parallelism rule.
- [x] Step 3: Update planning/governance docs so the new prompt is discoverable from the execution model.

## Task 3: Close The Artifact Loop And Verify

**Files:**
- Modify: `docs/superpowers/specs/2026-04-27-parallel-bounded-change-planning-prompt-spec.md`
- Modify: `docs/superpowers/plans/2026-04-27-12-10-parallel-bounded-change-planning-prompt-plan.md`

- [x] Step 1: Mark the spec and plan completed after implementation.
- [x] Step 2: Run `scripts/validate_adoption_shape.py`.
- [x] Step 3: Run `git diff --check`.
