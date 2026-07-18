---
layer: operating_system
artifact_type: plan
status: active
parent_workstream: none
targets:
  - docs/operating_system/adoption/project-adoption-migration-guide.md
  - docs/operating_system/skill-doc-system-lifecycle.md
  - docs/operating_system/adoption/mode-b-example-migration.md
related_features: []
related_stages: []
---

# Generated Discovery Migration Target Plan

**Feature Source:** `none`
**Feature Contract:** `none`
**Spec:** `docs/superpowers/specs/2026-04-22-generated-discovery-migration-target-spec.md`
**Type:** modify
**Plan Layer:** operating_system
**Plan Status:** active

**Goal:** Make the canonical `docs/generated/` migration target explicit in the starter operating-system docs.

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
  - `docs/operating_system/adoption/project-adoption-migration-guide.md`
  - `docs/operating_system/skill-doc-system-lifecycle.md`
  - `docs/operating_system/adoption/mode-b-example-migration.md`
- README: none
- Generated discovery: none

### Task 1: State The Canonical Target

**Files:**
- Modify: `docs/operating_system/adoption/project-adoption-migration-guide.md`
- Modify: `docs/operating_system/skill-doc-system-lifecycle.md`

- [ ] Step 1: Name `customer-churn-prediction-azureml/docs/generated/` as the concrete canonical target example.
- [ ] Step 2: List `architecture_dag.yaml` and `capability_lineage.yaml` as the current managed target files.
- [ ] Step 3: State that older summary-index families are superseded migration debt, not coequal steady-state outputs.

### Task 2: Update The Example Migration

**Files:**
- Modify: `docs/operating_system/adoption/mode-b-example-migration.md`

- [ ] Step 1: Add the generated-discovery target to the example migration shape.
- [ ] Step 2: Explain that older `docs/generated/*` summary files should be retired after generator-backed migration.

### Task 3: Verify

**Files:**
- Docs: `docs/operating_system/adoption/project-adoption-migration-guide.md`
- Docs: `docs/operating_system/skill-doc-system-lifecycle.md`
- Docs: `docs/operating_system/adoption/mode-b-example-migration.md`

- [ ] Step 1: Review the touched sections for consistent target wording.
- [ ] Step 2: Confirm the docs do not imply the old and new generated-discovery families should coexist.
