---
layer: operating_system
artifact_type: plan
status: active
parent_workstream: none
targets:
  - docs/adoption_guide.md
  - docs/operating_system/project-adoption-migration-guide.md
  - docs/operating_system/skill-doc-system-lifecycle.md
  - docs/operating_system/feature-routing-guide.md
  - docs/features/README.md
related_features: []
related_stages: []
---

# Adoption Migration Guide Implementation Plan

## Triage

Layer: operating_system
Feature type: ADD
Summary: Add starter guidance that prevents existing projects from entering a half-migrated architecture metadata state.
Reasoning: This governs repo adoption process, documentation placement, generated surfaces, and metadata migration. It does not add or modify a product feature.
Invariants:
- Adoption mode must be explicit before changing feature/stage/generated/code metadata surfaces.
- Managed architecture metadata requires feature folders, source files, generated outputs, and source metadata to move together.
- Flat feature YAML outside feature folders is legacy compatibility only.
- Generated discovery must be refreshed from source and not hand-edited.
- Code/config/test/doc metadata must reference canonical feature and capability IDs in managed mode.
Affected stages: none
Affected features: none
Primary lens: cross-cutting
Affected docs:
- cross_cutting_docs:
  - `docs/adoption_guide.md`
  - `docs/operating_system/project-adoption-migration-guide.md`
  - `docs/operating_system/skill-doc-system-lifecycle.md`
  - `docs/operating_system/feature-routing-guide.md`
  - `docs/features/README.md`
- readme: none
- generated: none
Generated refresh required: no
Capability IDs: none
Invariant IDs: none
Spec needed: yes
Plan needed: yes

## Source Spec

This plan implements:

- `docs/superpowers/specs/2026-04-20-adoption-migration-guide-spec.md`

## Tasks

### 1. Add project adoption migration guide

Create `docs/operating_system/project-adoption-migration-guide.md` with:

- adoption mode decision
- starter method only mode
- managed architecture metadata mode
- legacy compatibility mode
- canonical managed feature folder shape
- flat feature YAML legacy warning
- migration sequence
- source metadata update expectations
- generated discovery refresh rules
- validation checklist
- DE-PROJECT-style half-migration anti-pattern

### 2. Update adoption guide

Patch `docs/adoption_guide.md` to require choosing an adoption mode before feature/stage creation.

Add cross-links to:

- `docs/operating_system/project-adoption-migration-guide.md`
- `docs/operating_system/feature-routing-guide.md`

### 3. Update feature README

Patch `docs/features/README.md` so it states:

- managed mode requires feature folders
- flat `docs/features/*.yaml` files are legacy-only
- do not mix flat authoritative contracts with generated folder contracts

### 4. Update doc-system lifecycle

Patch `docs/operating_system/skill-doc-system-lifecycle.md` to distinguish managed feature-folder mode from legacy flat YAML mode.

Add a reference to the migration guide near feature placement rules.

### 5. Update feature routing guide

Patch `docs/operating_system/feature-routing-guide.md` to explain that it classifies candidates, while `project-adoption-migration-guide.md` governs migrating existing project surfaces.

### 6. Verify

Run:

```powershell
git -C "C:\Users\HOANG PHI LONG DANG\repos\project-OS-starter" diff --check
git -C "C:\Users\HOANG PHI LONG DANG\repos\project-OS-starter" status --short --branch
```

Search touched docs for accidental literal newline escapes.

## Acceptance Criteria

- `docs/operating_system/project-adoption-migration-guide.md` exists.
- `docs/adoption_guide.md` requires adoption-mode selection before feature/stage metadata work.
- `docs/features/README.md` warns against mixed legacy/managed feature shapes.
- `docs/operating_system/skill-doc-system-lifecycle.md` names flat feature YAML as legacy-only in managed architecture contexts.
- `docs/operating_system/feature-routing-guide.md` links classification to migration guidance.
- No generated files are edited.
- `git diff --check` passes.
