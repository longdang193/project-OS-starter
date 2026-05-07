---
layer: operating_system
artifact_type: plan
status: completed
parent_workstream: none
targets:
  - docs/intent/README.md
  - docs/intent/master-workstream-roadmap.md
  - docs/intent/workstreams/
  - docs/operating_system/skill-planning-dispatch.md
  - docs/operating_system/repo-governance.md
  - docs/superpowers/specs/2026-04-27-workstream-coverage-and-bounded-change-governance-spec.md
related_features: []
related_stages: []
---

# Workstream Coverage And Bounded Change Governance Implementation Plan

**Feature Source:** `none`  
**Feature Contract:** `none`  
**Spec:** `docs/superpowers/specs/2026-04-27-workstream-coverage-and-bounded-change-governance-spec.md`  
**Type:** add  
**Plan Layer:** operating_system  
**Plan Status:** completed

> **For agentic workers:** Use `skill-executing-plans` or `skill-subagent-driven-development` to implement task-by-task.

**Goal:** Document the precise planning ladder, explain how roadmap coverage and workstream progress should be tracked, and define bounded change threads as the safe parallel execution unit.

**Architecture:** Add one intent-adjacent governance guide that explains the complete model: master roadmap coverage, registered workstream completeness, bounded change threads, workstream progress tracking, divergence review, and safe parallel execution. Then update the roadmap, workstream registry, one example workstream doc, and the operating-system planning/governance docs so the model is discoverable and concrete.

**Key Invariants:**
- the master roadmap remains a strategic coverage layer, not a progress board
- registered workstreams remain the concrete set that should cover the roadmap
- bounded change threads remain the execution unit beneath workstreams or the `operating_system` branch
- progress should be tracked in workstream docs and execution artifacts, not pushed back into the roadmap
- parallel work should be framed around bounded change threads rather than broad workstreams

**Rollout / Revert:**  
- rollback_trigger: the guide adds too much ceremony or duplicates the roadmap/planning docs too heavily  
- rollback_method: keep the new vocabulary in a lighter form, remove over-detailed sections, and retain only the cross-links and essential rules

---

## Triage

Layer: operating_system
Feature type: ADD
Summary: Add guidance for roadmap coverage, workstream progress, bounded change threads, and safe parallel execution.
Reasoning: This is repo-method governance work that clarifies how the existing planning layers should be used together.
Invariants:
  - roadmap stays strategic
  - workstreams collectively cover the roadmap
  - bounded change threads are the safe execution unit
  - `operating_system` remains a parallel branch
Dependencies:
  - `docs/intent/master-workstream-roadmap.md`
  - `docs/intent/workstreams/`
  - `docs/operating_system/skill-planning-dispatch.md`
  - `docs/operating_system/repo-governance.md`
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
    - `docs/operating_system/skill-planning-dispatch.md`
    - `docs/operating_system/repo-governance.md`
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
docs/intent/workstream-coverage-and-progress-guide.md
```

## Files To Modify

```text
docs/intent/README.md
docs/intent/master-workstream-roadmap.md
docs/intent/workstreams/README.md
docs/intent/workstreams/starter-adoption-experience.md
docs/operating_system/skill-planning-dispatch.md
docs/operating_system/repo-governance.md
docs/superpowers/specs/2026-04-27-workstream-coverage-and-bounded-change-governance-spec.md
docs/superpowers/plans/2026-04-27-09-40-workstream-coverage-and-bounded-change-governance-plan.md
```

## Task 1: Add The Governance Guide

**Files:**
- Create: `docs/intent/workstream-coverage-and-progress-guide.md`

- [x] Step 1: Define the precise ladder from roadmap to execution.
- [x] Step 2: Separate coverage tracking, workstream progress tracking, execution tracking, and divergence review.
- [x] Step 3: Define bounded change threads and the rules for safe parallel execution.

## Task 2: Rewire Intent And Workstream Surfaces

**Files:**
- Modify: `docs/intent/README.md`
- Modify: `docs/intent/master-workstream-roadmap.md`
- Modify: `docs/intent/workstreams/README.md`
- Modify: `docs/intent/workstreams/starter-adoption-experience.md`

- [x] Step 1: Link the new guide from the intent layer and roadmap.
- [x] Step 2: Update the workstream registry README so the recommended shape includes progress concepts.
- [x] Step 3: Update the example workstream doc so the new progress model is concrete.

## Task 3: Update Planning And Governance Docs

**Files:**
- Modify: `docs/operating_system/skill-planning-dispatch.md`
- Modify: `docs/operating_system/repo-governance.md`

- [x] Step 1: Update skill-planning-dispatch so bounded change threads are explicit beneath workstreams.
- [x] Step 2: Update repo-governance so coverage/progress/divergence tracking and bounded-change parallelism are stated plainly.

## Task 4: Close The Artifact Loop And Verify

**Files:**
- Modify: `docs/superpowers/specs/2026-04-27-workstream-coverage-and-bounded-change-governance-spec.md`
- Modify: `docs/superpowers/plans/2026-04-27-09-40-workstream-coverage-and-bounded-change-governance-plan.md`

- [x] Step 1: Mark the spec and plan completed after implementation.
- [x] Step 2: Run `scripts/validate_adoption_shape.py`.
- [x] Step 3: Run `git diff --check`.
