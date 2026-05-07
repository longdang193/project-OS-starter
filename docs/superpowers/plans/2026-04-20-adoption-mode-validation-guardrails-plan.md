---
layer: operating_system
artifact_type: plan
status: active
parent_workstream: none
targets:
  - repo_config/adoption-mode.yaml
  - scripts/validate_adoption_shape.py
  - docs/adoption_guide.md
  - docs/operating_system/project-adoption-migration-guide.md
  - docs/operating_system/feature-routing-guide.md
  - docs/operating_system/skill-doc-system-lifecycle.md
  - docs/features/README.md
related_features: []
related_stages: []
---

# Adoption Mode And Validation Guardrails Implementation Plan

## Triage

Layer: operating_system
Feature type: ADD
Summary: Add an explicit adoption-mode contract and a read-only validator to prevent invalid starter adoption states.
Reasoning: This work governs repo adoption, documentation shape, generated-surface boundaries, and metadata validation. It is not a product feature or product stage.
Invariants:
- Adoption mode is the source of truth for whether feature/stage architecture metadata is absent, legacy flat, or managed folder-based.
- Starter method only mode must validate in the starter repo by default.
- Managed architecture metadata mode must reject mixed flat feature YAML and managed feature folders.
- Legacy compatibility mode must be explicit when flat feature contracts remain.
- The validator is read-only and never edits generated or source files.
- Operating-system work uses `targets`, not product feature `depends_on`.
Affected stages: none
Affected features: none
Primary lens: cross-cutting
Affected docs:
- cross_cutting_docs:
  - `docs/adoption_guide.md`
  - `docs/operating_system/project-adoption-migration-guide.md`
  - `docs/operating_system/feature-routing-guide.md`
  - `docs/operating_system/skill-doc-system-lifecycle.md`
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

- `docs/superpowers/specs/2026-04-20-adoption-mode-validation-guardrails-spec.md`

## Tasks

### 1. Add adoption mode source file

Create `repo_config/adoption-mode.yaml` with starter default mode:

```yaml
adoption_mode: starter_method_only
managed_architecture_metadata: false
legacy_feature_contracts: false
architecture_generator: none
notes: >
  Repo operating-system, intent, adapter, and publication guidance are adopted.
  Product feature/stage metadata is intentionally not adopted yet.
```

This file is human-owned config, not generated output.

### 2. Implement read-only validator

Create `scripts/validate_adoption_shape.py`.

Validator requirements:

- load `repo_config/adoption-mode.yaml`
- support only `starter_method_only`, `managed_architecture_metadata`, and `legacy_compatibility`
- report errors and warnings with paths and suggested fixes
- exit `1` when errors exist
- exit `0` when only warnings or no findings exist
- never modify files

Initial checks:

- mode/boolean consistency
- method-layer pseudo-feature IDs such as `repo-operating-system`
- obvious method-layer feature prefixes such as `repo-`, `agent-`, `adapter-`, `publication-`, and `docs-governance`
- flat feature YAML vs managed folder shape consistency
- feature `depends_on` references existing product feature IDs
- structured capability IDs look ID-like when present
- generated files with generated headers are not treated as human source

Mode-specific checks:

- `starter_method_only`: error on `feature.source.yaml`, managed contracts, architecture generated indexes, or feature/capability metadata markers in code/config/tests; warn on non-README files under `docs/features/` or `docs/stages/`
- `managed_architecture_metadata`: error on flat authoritative `docs/features/*.yaml`, missing `feature.source.yaml`, method pseudo-features, generated discovery without source folders, or `architecture_generator: none`; warn on missing lineage files and absent metadata markers
- `legacy_compatibility`: error on `feature.source.yaml`, managed generated contracts beside flat contracts, or `legacy_feature_contracts: false`; warn when no `migration_follow_up` exists

### 3. Add minimal tests or smoke validation

If the starter has a test framework, add tests for the validator.

If not, use command-level smoke checks:

```powershell
python scripts/validate_adoption_shape.py
```

Optional smoke scenarios may use temporary directories only if low-risk and simple.

### 4. Update adoption guide

Patch `docs/adoption_guide.md` to say:

- record adoption mode in `repo_config/adoption-mode.yaml`
- run `python scripts/validate_adoption_shape.py` before committing adoption changes
- validator should pass in starter method only mode before feature/stage metadata is introduced

### 5. Update migration guide

Patch `docs/operating_system/project-adoption-migration-guide.md` to say:

- adoption mode is recorded in `repo_config/adoption-mode.yaml`
- managed, legacy, and starter-only mode rules are mechanically checked by the validator
- halfway projects must use `legacy_compatibility` until full managed migration is planned

### 6. Update routing guide

Patch `docs/operating_system/feature-routing-guide.md` with candidate classification metadata:

```yaml
candidate_type: product_feature | product_stage | operating_system | spec_only | plan_only | generated | obsolete
adoption_mode: starter_method_only | managed_architecture_metadata | legacy_compatibility
creates_feature_metadata: true | false
creates_stage_metadata: true | false
updates_code_metadata: true | false
updates_generated_discovery: true | false
```

Explain that `candidate_type: operating_system` should use `targets` and usually `related_features: []`.

### 7. Update lifecycle and feature README docs

Patch `docs/operating_system/skill-doc-system-lifecycle.md` to include `repo_config/adoption-mode.yaml` in the source-of-truth model.

Patch `docs/features/README.md` to say folder interpretation is controlled by adoption mode.

### 8. Verify

Run:

```powershell
python scripts/validate_adoption_shape.py
git -C "C:\Users\HOANG PHI LONG DANG\repos\project-OS-starter" diff --check
git -C "C:\Users\HOANG PHI LONG DANG\repos\project-OS-starter" status --short --branch
```

Also inspect final diff for accidental generated-file edits.

## Acceptance Criteria

- `repo_config/adoption-mode.yaml` exists with starter default mode.
- `scripts/validate_adoption_shape.py` exists and is read-only.
- The validator passes on current starter state in `starter_method_only` mode.
- The validator fails on mode/boolean mismatch.
- The validator fails on method-layer pseudo-feature IDs such as `repo-operating-system`.
- The validator fails on mixed flat feature YAML plus managed feature folders in managed mode.
- Docs reference the adoption mode file and validator.
- No generated files are edited.
- `git diff --check` passes.
