---
layer: operating_system
artifact_type: plan
status: completed
parent_workstream: none
targets:
  - docs/intent/README.md
  - docs/intent/master-workstream-roadmap.md
  - docs/operating_system/skill-planning-dispatch.md
  - docs/operating_system/governance/repo-governance.md
  - .agents/skills/skill-brainstorming/SKILL.md
  - .agents/skills/skill-planning-dispatch/SKILL.md
  - .agents/skills/skill-writing-plans/SKILL.md
related_features: []
related_stages: []
---

# Intent Roadmap And Operating-System Classification Implementation Plan

**Feature Source:** `none`  
**Feature Contract:** `none`  
**Spec:** `docs/superpowers/specs/2026-04-24-intent-roadmap-and-operating-system-classification-spec.md`  
**Type:** modify  
**Plan Layer:** operating_system  
**Plan Status:** completed

> **For agentic workers:** Use `skill-executing-plans` or `skill-subagent-driven-development` to implement task-by-task.

**Goal:** Add an intent-owned master workstream roadmap and update planning guidance so `operating_system` remains a parallel first-class branch rather than being collapsed into product workstreams.

**Architecture:** Create a new `docs/intent/master-workstream-roadmap.md` as the top-down bridge from project intent into durable workstreams. Update intent and operating-system guidance so the planning lifecycle becomes explicit: start from intent, route into either a product workstream or the operating-system branch, then create bounded change specs and plans downstream.

**Key Invariants:**
- `docs/intent/` remains the canonical source for project purpose and outcomes.
- `operating_system` remains a planning classification, not a fake product workstream.
- Specs and plans remain bounded downstream artifacts under `docs/superpowers/`.
- The new roadmap explains direction; it does not replace execution artifacts.

**Rollout / Revert:**  
- rollback_trigger: The new structure makes planning more confusing, duplicates upstream intent truth, or blurs the distinction between product workstreams and operating-system work.  
- rollback_method: Remove the roadmap doc, revert the routing-language changes, and keep the current four-layer model without the new top-down bridge.

---

## Doc Update Matrix

- Feature source: none
- Feature contract: none
- Feature lineage: none
- Stage source: none
- Stage contracts: none
- Feature history: none
- Feature-specific docs: none
- Cross-cutting docs: none
- Operating-system docs:
  - `docs/operating_system/skill-planning-dispatch.md`
  - `docs/operating_system/governance/repo-governance.md`
  - `docs/superpowers/specs/2026-04-24-intent-roadmap-and-operating-system-classification-spec.md`
- README: none
- Generated discovery: none

## Files To Modify

```text
docs/intent/README.md
docs/intent/master-workstream-roadmap.md
docs/operating_system/skill-planning-dispatch.md
docs/operating_system/governance/repo-governance.md
.agents/skills/skill-brainstorming/SKILL.md
.agents/skills/skill-planning-dispatch/SKILL.md
.agents/skills/skill-writing-plans/SKILL.md
docs/superpowers/specs/2026-04-24-intent-roadmap-and-operating-system-classification-spec.md
```

## Scope Boundary

Implement only the smallest strong move:

1. add the intent-owned roadmap doc
2. update intent and operating-system docs to explain the new tree
3. lightly align skill wording where the planning story would otherwise drift
4. avoid redesigning metadata or execution mechanics in this pass

Do not:

- create a large workstream registry
- create per-workstream docs unless the roadmap truly needs examples
- change validator behavior
- invent a second source of truth for intent

## Task 1: Add The Intent-Owned Master Roadmap

**Files:**
- Create: `docs/intent/master-workstream-roadmap.md`
- Modify: `docs/intent/README.md`

- [x] Step 1: Create `docs/intent/master-workstream-roadmap.md` as the canonical bridge from project intent into durable workstreams.
- [x] Step 2: Make the roadmap explicitly preserve `operating_system` as a parallel branch for repo-method work.
- [x] Step 3: Keep the roadmap strategic and stable rather than turning it into a running execution log.
- [x] Step 4: Update `docs/intent/README.md` so it points to the roadmap and explains its role.

## Task 2: Update Operating-System Planning Guidance

**Files:**
- Modify: `docs/operating_system/skill-planning-dispatch.md`
- Modify: `docs/operating_system/governance/repo-governance.md`

- [x] Step 1: Update `skill-planning-dispatch.md` so the routing story becomes `intent -> workstream or operating_system -> change -> spec/plan`.
- [x] Step 2: Make the next routing question explicit: “product workstream or operating_system?”
- [x] Step 3: Update `repo-governance.md` to point to the intent-owned roadmap and explain the operating-system branch clearly.
- [x] Step 4: Keep the docs concise and workflow-oriented rather than turning them into a process manual.

## Task 3: Light Skill Alignment

**Files:**
- Modify: `.agents/skills/skill-brainstorming/SKILL.md`
- Modify: `.agents/skills/skill-planning-dispatch/SKILL.md`
- Modify: `.agents/skills/skill-writing-plans/SKILL.md`

- [x] Step 1: Add or adjust brief wording so the skills do not contradict the new roadmap model.
- [x] Step 2: Keep the skills detailed and executable; do not duplicate the full operating-system prose there.
- [x] Step 3: Only touch the minimal lines needed to keep the planning story aligned.

## Task 4: Mark Artifacts Complete

**Files:**
- Modify: `docs/superpowers/specs/2026-04-24-intent-roadmap-and-operating-system-classification-spec.md`
- Modify: `docs/superpowers/plans/2026-04-24-10-30-intent-roadmap-and-operating-system-classification-plan.md`

- [x] Step 1: Mark the spec completed once the doc changes land.
- [x] Step 2: Mark this plan completed after verification.

## Task 5: Verification

**Files:**
- Verify: `docs/intent/*.md`
- Verify: `docs/operating_system/*.md`
- Verify: `.agents/skills/*/SKILL.md`

- [ ] Step 1: Review the edited docs and skills together to confirm they now tell one consistent planning story.
- [ ] Step 2: Run the repo contract fast path to ensure doc changes did not break repo checks:

```powershell
$env:UV_CACHE_DIR=(Resolve-Path '.tmp-tests').Path; uv run python scripts\validate_repo_contracts.py --fast
```

- [ ] Step 3: Run whitespace validation:

```powershell
git diff --check
```

- [ ] Step 4: Review the final diff and confirm this stayed a documentation and workflow-guidance pass, not a hidden process redesign.
