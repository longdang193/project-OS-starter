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

# Feature Contract Freshness Metadata Plan

**Feature Source:** `none`
**Feature Contract:** `none`
**Spec:** `docs/superpowers/specs/2026-04-22-feature-contract-freshness-metadata-spec.md`
**Type:** modify
**Plan Layer:** operating_system
**Plan Status:** active

**Goal:** Make generated feature-contract freshness metadata explicit in the starter docs as the canonical managed migration target.

## Doc Update Matrix

- Feature source: none
- Feature contract: all managed `docs/features/*/<feature_id>.yaml`
- Feature lineage: none
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

### Task 1: State The Canonical Freshness Contract

**Files:**
- Modify: `docs/operating_system/lifecycle/feature-lifecycle.md`
- Modify: `docs/operating_system/skill-doc-system-lifecycle.md`

- [ ] Step 1: Replace soft “may include” language with explicit target wording for generated freshness fields.
- [ ] Step 2: Say plainly that `revision`, `latest_change_id`, and `last_updated_at` belong in generated contracts, not `feature.source.yaml`.
- [ ] Step 3: Name the churn repo generated contract shape as the concrete migration target.

### Task 2: Update Migration Guidance

**Files:**
- Modify: `docs/operating_system/adoption/project-adoption-migration-guide.md`

- [ ] Step 1: State that older generated contracts without freshness metadata are migration debt when completed-plan metadata exists.
- [ ] Step 2: Keep the ownership split explicit between `feature.source.yaml` and generated contracts.

### Task 3: Verify

**Files:**
- Docs: `docs/operating_system/lifecycle/feature-lifecycle.md`
- Docs: `docs/operating_system/skill-doc-system-lifecycle.md`
- Docs: `docs/operating_system/adoption/project-adoption-migration-guide.md`

- [ ] Step 1: Review the touched sections for consistent wording.
- [ ] Step 2: Confirm the docs no longer imply freshness metadata is just optional decoration.
