---
layer: operating_system
artifact_type: plan
status: active
parent_workstream: none
targets:
  - docs/operating_system/lifecycle/feature-lifecycle.md
  - docs/operating_system/skill-doc-system-lifecycle.md
  - docs/operating_system/adoption/project-adoption-migration-guide.md
related_features: []
related_stages: []
---

# Lineage Timeline Schema Migration Target Plan

**Feature Source:** `none`  
**Feature Contract:** `none`  
**Spec:** `docs/superpowers/specs/2026-04-22-lineage-timeline-schema-migration-target-spec.md`
**Type:** modify  
**Plan Layer:** operating_system
**Plan Status:** active

**Goal:** Make the richer `lineage.generated.yaml > timeline` schema explicit in the starter docs as the canonical migration target.

## Doc Update Matrix

- Feature source: none
- Feature contract: none
- Feature lineage: all managed `docs/features/*/lineage.generated.yaml`
- Stage source: none
- Stage contracts: none
- Feature history: none
- Feature-specific docs: none
- Cross-cutting docs: none
- Operating-system docs:
  - `docs/operating_system/lifecycle/feature-lifecycle.md`
  - `docs/operating_system/skill-doc-system-lifecycle.md`
  - `docs/operating_system/adoption/project-adoption-migration-guide.md`
- README: none
- Generated discovery: none

### Task 1: State The Canonical Timeline Target

**Files:**
- Modify: `docs/operating_system/lifecycle/feature-lifecycle.md`
- Modify: `docs/operating_system/skill-doc-system-lifecycle.md`

- [ ] Step 1: Say plainly that `timeline` is a list of richer completed-change records, not just spec/plan refs.
- [ ] Step 2: Name the churn repo timeline shape as the concrete target.
- [ ] Step 3: Call the older `{kind, path}` timeline shape superseded migration debt.

### Task 2: Update Migration Guidance

**Files:**
- Modify: `docs/operating_system/adoption/project-adoption-migration-guide.md`

- [ ] Step 1: Add migration wording that replaces the older timeline shape with the richer completed-change shape.
- [ ] Step 2: Make clear that managed repos should regenerate feature-local lineage rather than preserve legacy timeline entries.

### Task 3: Verify

**Files:**
- Docs: `docs/operating_system/lifecycle/feature-lifecycle.md`
- Docs: `docs/operating_system/skill-doc-system-lifecycle.md`
- Docs: `docs/operating_system/adoption/project-adoption-migration-guide.md`

- [ ] Step 1: Review the touched sections for consistent wording.
- [ ] Step 2: Confirm the docs no longer imply the old and new timeline entry shapes are coequal.
