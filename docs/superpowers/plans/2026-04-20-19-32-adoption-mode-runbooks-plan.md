---
layer: operating_system
artifact_type: plan
status: proposed
parent_workstream: none
targets:
  - docs/adoption_guide.md
  - docs/operating_system/project-adoption-migration-guide.md
related_features: []
related_stages: []
---

# Adoption Mode Runbooks Implementation Plan

**Feature Source:** `none`
**Feature Contract:** `none`
**Spec:** `docs/superpowers/specs/2026-04-20-adoption-mode-runbooks-spec.md`
**Type:** modify
**Plan Layer:** operating_system
**Plan Status:** proposed

> **For agentic workers:** Use `skill-executing-plans` or `skill-subagent-driven-development` to implement task-by-task.

**Goal:** Add executable mode-specific adoption runbooks so future agents can choose, migrate, validate, and commit adoption states without creating partial architecture metadata.

**Architecture:** This is an operating-system documentation update. The detailed runbooks belong in `docs/operating_system/project-adoption-migration-guide.md`, while `docs/adoption_guide.md` should route adopters to those runbooks before feature or stage metadata work begins.

**Key Invariants:**

- Adoption mode must be declared in `repo_config/adoption-mode.yaml` before feature, stage, generated, or source metadata surfaces are changed.
- Operating-system adoption work must stay in the operating-system layer and must not be represented as a product feature, stage, capability, or product dependency.
- Mode B managed architecture metadata is a whole-project contract across feature folders, source contracts, generated outputs, source metadata, validation, and tests.
- Mode A remains valid for projects that only want the starter method and no product architecture metadata.
- Mode C is temporary legacy compatibility and must make the migration follow-up discoverable.
- Every adoption path ends with `python scripts/validate_adoption_shape.py`.

**Rollout / Revert:**

- rollback_trigger: The new guidance conflicts with the adoption-mode validator or makes Mode A, Mode B, or Mode C materially ambiguous.
- rollback_method: Revert the two documentation edits and re-run `git diff --check` plus `python scripts/validate_adoption_shape.py`.

---

## Triage

Layer: operating_system
Feature type: MODIFY
Summary: Add explicit mode-specific runbooks to the starter adoption documentation.
Reasoning: The work changes repo adoption process guidance and documentation routing, not product/domain feature behavior. No managed product feature or stage contract owns this change.
Invariants:

- Adoption mode selection remains the first step before architecture metadata migration.
- Managed metadata migration must not be represented as a method-layer pseudo-feature.
- Generated discovery and generated contracts remain derived outputs, not hand-authored source.
- The implementation must not change validator code, config, generated files, or downstream project metadata.

Dependencies:

- `repo_config/adoption-mode.yaml`
- `scripts/validate_adoption_shape.py`
- `docs/operating_system/feature-routing-guide.md`

Affected stages:

- none

Affected features:

- none

Primary lens: cross-cutting

Affected docs:

- feature_source: none
- feature_yaml: none
- feature_lineage: none
- feature_history: none
- stage_source: none
- stage_contract: none
- feature_docs: none
- cross_cutting_docs:
  - `docs/adoption_guide.md`
  - `docs/operating_system/project-adoption-migration-guide.md`
- readme: none
- generated: none

Generated refresh required: no
Capability IDs: none
Invariant IDs: none
Spec needed: yes
Plan needed: yes
Migration needed: no
Risk level: low

## Doc Update Matrix

- Feature source: none
- Feature contract: none
- Feature lineage: none
- Stage source: none
- Stage contracts: none
- Feature history: none
- Feature-specific docs: none
- Cross-cutting docs: `docs/adoption_guide.md`
- Operating-system docs: `docs/operating_system/project-adoption-migration-guide.md`
- README: none
- Generated discovery: none

## File Structure

- Create: none
- Modify: `docs/operating_system/project-adoption-migration-guide.md`
- Modify: `docs/adoption_guide.md`
- Test: no new test files
- Generated outputs: none

## Source Spec

This plan implements:

- `docs/superpowers/specs/2026-04-20-adoption-mode-runbooks-spec.md`

## Tasks

### Task 1: Add Mode A Step-By-Step Runbook

**Files:**

- Modify: `docs/operating_system/project-adoption-migration-guide.md`
- Test: no new test files
- Docs: `docs/operating_system/project-adoption-migration-guide.md`

- [ ] Step 1: Add a `## Mode A Step-By-Step: Starter Method Only` section after the adoption modes overview.
- [ ] Step 2: Start the runbook by setting `repo_config/adoption-mode.yaml` to `starter_method_only`.
- [ ] Step 3: Include intent-layer setup for project purpose, constraints, stakeholders, and success outcomes.
- [ ] Step 4: Include operating-system adoption surfaces: docs, agent instructions, generated rules, adapter sync, publication guidance, and memory guidance.
- [ ] Step 5: Explicitly prohibit product feature folders, stage contracts, generated architecture indexes, and code/config/test feature metadata in Mode A.
- [ ] Step 6: State that method-layer changes use operating-system specs/plans with explicit `targets`.
- [ ] Step 7: Include adapter sync and verify commands when adapter, instruction, or generated rule surfaces changed:

```powershell
.\scripts\sync_agent_adapters.ps1
.\scripts\verify_agent_adapters.ps1
```

- [ ] Step 8: End the runbook with:

```powershell
python scripts/validate_adoption_shape.py
```

- [ ] Step 9: Add the Mode A stop condition: if product feature lineage, stage ownership, or generated feature contracts are needed, write a Mode B migration plan instead of adding one-off feature files.

### Task 2: Add Mode B Step-By-Step Runbook

**Files:**

- Modify: `docs/operating_system/project-adoption-migration-guide.md`
- Test: no new test files
- Docs: `docs/operating_system/project-adoption-migration-guide.md`

- [ ] Step 1: Add a `## Mode B Step-By-Step: Managed Architecture Metadata` section after the Mode A runbook.
- [ ] Step 2: Start the runbook by setting `repo_config/adoption-mode.yaml` to `managed_architecture_metadata`.
- [ ] Step 3: Add an inventory step that names existing product docs, flat feature YAML files, stage docs, generated files, code metadata, config metadata, test metadata, and pipeline/component metadata.
- [ ] Step 4: Add classification guidance for product features, product stages, product capabilities, cross-cutting product docs, and operating-system method material.
- [ ] Step 5: Require removing or re-homing method-layer pseudo-features into `docs/operating_system/` or operating-system specs/plans.
- [ ] Step 6: Require one folder per real product feature under `docs/features/<feature_id>/`.
- [ ] Step 7: Require human-owned feature meaning in `docs/features/<feature_id>/feature.source.yaml`.
- [ ] Step 8: Require generated feature outputs at `docs/features/<feature_id>/<feature_id>.yaml` and `docs/features/<feature_id>/lineage.generated.yaml`.
- [ ] Step 9: Require stable capability IDs, such as lowercase kebab-case identifiers instead of prose sentences.
- [ ] Step 10: Require stage source updates so `primary_features` and `supporting_features` describe stage ownership.
- [ ] Step 11: Require code, config, tests, AML components, scripts, and docs that feed lineage to reference canonical feature and capability IDs.
- [ ] Step 12: Require generated architecture refresh from the project generator when one exists.
- [ ] Step 13: Require verification that no authoritative flat `docs/features/*.yaml` files remain outside feature folders.
- [ ] Step 14: End the runbook with:

```powershell
python scripts/validate_adoption_shape.py
git diff --check
```

- [ ] Step 15: Add the Mode B warning that creating one feature folder is not enough to claim managed architecture metadata adoption.

### Task 3: Add Mode C Step-By-Step Runbook

**Files:**

- Modify: `docs/operating_system/project-adoption-migration-guide.md`
- Test: no new test files
- Docs: `docs/operating_system/project-adoption-migration-guide.md`

- [ ] Step 1: Add a `## Mode C Step-By-Step: Legacy Compatibility` section after the Mode B runbook.
- [ ] Step 2: Start the runbook by setting `repo_config/adoption-mode.yaml` to `legacy_compatibility`.
- [ ] Step 3: Require `migration_follow_up.required: true` and a reference to the plan or issue that will migrate to Mode A or Mode B.
- [ ] Step 4: Require inventorying existing flat feature contracts and classifying product features separately from method-layer material.
- [ ] Step 5: State that legacy flat feature contracts remain the temporary current truth.
- [ ] Step 6: Prohibit managed feature folders, generated feature contracts, and generated lineage files until a Mode B migration plan is executed.
- [ ] Step 7: Re-home obvious method-layer pseudo-features into operating-system docs/specs/plans when safe.
- [ ] Step 8: End the runbook with:

```powershell
python scripts/validate_adoption_shape.py
```

- [ ] Step 9: State that validator warnings are migration debt unless the guide documents why they are intentionally allowed in Mode C.
- [ ] Step 10: Add the Mode C stop condition: if generated lineage or capability-level code tracing is required, stop extending Mode C and move to a Mode B migration plan.

### Task 4: Route The Adoption Guide To Runbooks

**Files:**

- Modify: `docs/adoption_guide.md`
- Test: no new test files
- Docs: `docs/adoption_guide.md`

- [ ] Step 1: In `## 4. Choose Adoption Mode`, link to the three mode-specific runbook headings in `docs/operating_system/project-adoption-migration-guide.md`.
- [ ] Step 2: Move the runbook link before any instruction to create, define, or migrate product feature/stage metadata.
- [ ] Step 3: Keep the existing adoption mode summaries concise; do not duplicate the full runbooks in `docs/adoption_guide.md`.
- [ ] Step 4: Clarify that adopters should follow the selected runbook before adjusting feature or stage metadata.
- [ ] Step 5: Preserve the existing validator command:

```powershell
python scripts/validate_adoption_shape.py
```

### Task 5: Verify Documentation-Only Change

**Files:**

- Test: no new test files
- Docs: `docs/adoption_guide.md`
- Docs: `docs/operating_system/project-adoption-migration-guide.md`

- [ ] Step 1: Run the adoption validator:

```powershell
python scripts/validate_adoption_shape.py
```

- [ ] Step 2: Run whitespace validation:

```powershell
git diff --check
```

- [ ] Step 3: Check the final diff:

```powershell
git diff -- docs/adoption_guide.md docs/operating_system/project-adoption-migration-guide.md
```

- [ ] Step 4: Confirm no generated files changed:

```powershell
git status --short
```

- [ ] Step 5: Commit after the docs and validation agree.

## Acceptance Criteria

- `docs/operating_system/project-adoption-migration-guide.md` contains:
  - `## Mode A Step-By-Step: Starter Method Only`
  - `## Mode B Step-By-Step: Managed Architecture Metadata`
  - `## Mode C Step-By-Step: Legacy Compatibility`
- The Mode A section clearly says not to create product feature/stage/generated metadata.
- The Mode B section covers feature folder packing, required files, capability ID normalization, stage ownership, source metadata updates, generated refresh, validator checks, tests, and diff checks.
- The Mode B section warns that one feature folder does not mean the project has adopted the managed metadata contract.
- The Mode C section says legacy compatibility is temporary and requires a migration follow-up.
- `docs/adoption_guide.md` links adopters to the mode-specific runbooks before feature or stage metadata work.
- No code, validator, config, generated output, feature contract, or stage contract changes are made.
- `python scripts/validate_adoption_shape.py` passes.
- `git diff --check` passes.

## Open Questions For Implementation

- Should a short Mode B example migration for one feature be added to this guide now, or left for a separate example document?
- Should Mode C allow immediate deletion of method-layer pseudo-features, or require a separate operating-system cleanup plan for large downstream projects?
- Should the validator later require a migration follow-up link for every `legacy_compatibility` project?
