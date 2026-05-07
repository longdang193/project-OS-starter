---
layer: operating_system
artifact_type: plan
status: proposed
parent_workstream: none
targets:
  - docs/superpowers/specs/2026-05-03-task-routing-and-central-template-system-spec.md
  - docs/operating_system/templates/
  - docs/operating_system/prompt_templates/
  - .agents/skills/
  - docs/operating_system/skill-planning-dispatch.md
related_features: []
related_stages: []
---

# Task Routing And Central Template System Implementation Plan

**Feature Source:** `none`  
**Feature Contract:** `none`  
**Spec:** `docs/superpowers/specs/2026-05-03-task-routing-and-central-template-system-spec.md`  
**Type:** add  
**Plan Layer:** operating_system  
**Plan Status:** proposed

> **For agentic workers:** Use `skill-executing-plans` or `skill-subagent-driven-development` to implement task-by-task.

## Goal

Implement a central-template + skill-discovery workflow where agents can choose
the correct task starting point and apply the correct canonical template
without ambiguity.

## Key Deliverables

- central template structure finalized and documented
- task start routing guide integrated into skill-level instructions
- relevant skills updated to reference canonical templates
- prompt/template docs aligned with canonical routing/template policy

## Task 1: Finalize Canonical Template Structure

- [ ] Move/organize templates under canonical subfolders:
  - `docs/operating_system/templates/routing/`
  - `docs/operating_system/templates/planning/`
- [ ] Add `docs/operating_system/templates/README.md` with:
  - ownership and precedence rules
  - required sections (`Goal`, `Key Deliverables`)
  - compatibility/update notes

## Task 2: Integrate Task Start Routing Guide

- [ ] Create canonical routing guide template under:
  - `docs/operating_system/templates/routing/task-start-routing-guide.md`
- [ ] Link routing guide from:
  - `docs/operating_system/skill-planning-dispatch.md`
  - relevant prompt templates where task-start choice is made

## Task 3: Update Skills To Use Canonical Templates

- [ ] Identify skill set that creates roadmap/workstream/thread/spec/plan docs.
- [ ] For each relevant `SKILL.md`, add template-reference block:
  - canonical template path
  - required sections
  - precedence rule (governance/template first, skill extensions second)
- [ ] Remove or de-authorize local duplicate template instructions when present.

## Task 4: Add Usage Examples And Discovery Hints

- [ ] Add concise “how to apply template” examples in:
  - routing-related skill docs
  - spec/plan creation skill docs
- [ ] Ensure examples reflect lineage and validator-aware metadata norms.

## Task 5: Validate And Close

- [ ] Run targeted checks:
  - `python scripts/validate_planning_lifecycle.py --strict`
- [ ] Run broader checks as possible:
  - `python scripts/validate_repo_contracts.py --fast`
- [ ] Verify prompt/template index links remain correct.
- [ ] Mark spec and plan `completed` when deliverables and downstream tasks are terminal.

## Risks / Notes

- Existing skill wording may conflict with new canonical template policy.
- Some repos/worktrees may surface unrelated validator failures; scope closeout
  should still verify local changes are internally consistent.
