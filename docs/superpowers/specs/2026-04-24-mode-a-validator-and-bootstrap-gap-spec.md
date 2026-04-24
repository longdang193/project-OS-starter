---
layer: operating_system
artifact_type: spec
status: completed
parent_workstream: none
targets:
  - scripts/validate_adoption_shape.py
  - scripts/validate_repo_contracts.py
  - scripts/sync_architecture_docs.py
  - scripts/validator_policy.py
  - tools/docs/generate_architecture_metadata.py
  - docs/operating_system/repo-governance.md
  - docs/operating_system/doc-system-lifecycle.md
  - docs/operating_system/project-adoption-migration-guide.md
  - docs/project_templates/mode-a/
  - tests/test_validate_adoption_shape.py
  - tests/test_validate_repo_contracts.py
related_features: []
related_stages: []
---

# Mode A Validator And Bootstrap Gap Spec

## Triage

Layer: operating_system
Feature type: CHANGE
Summary: Make Mode A (`starter_method_only`) validator behavior and bootstrap expectations explicit, self-consistent, and lighter than managed architecture metadata.
Reasoning: The current Mode A story says “starter method only,” but the canonical validation path still assumes parts of the managed architecture toolchain. That makes bootstrap incomplete, encourages local validator drift, and hides real setup obligations from downstream repos.
Invariants:

- `starter_method_only` remains a supported adoption mode.
- Managed architecture metadata remains the only mode that requires managed feature folders and generated feature/stage contracts.
- The canonical repo-contract workflow must match the actual promises of the chosen adoption mode.
- Mode A bootstrap guidance must be self-contained about what files and scripts are required.
- Downstream repos should not need to patch starter validators locally just to satisfy the starter contract.

Dependencies:

- `scripts/validate_adoption_shape.py`
- `scripts/validate_repo_contracts.py`
- `scripts/sync_architecture_docs.py`
- `tools/docs/generate_architecture_metadata.py`
- `docs/project_templates/mode-a/`
- `docs/operating_system/project-adoption-migration-guide.md`
- `docs/operating_system/repo-governance.md`
- `docs/operating_system/doc-system-lifecycle.md`

Affected stages:

- none directly

Affected features:

- none directly

Primary lens: cross-cutting

Affected docs:

- feature_source: none
- feature_yaml: none
- feature_lineage: none
- feature_history: none
- stage_source: none
- stage_contract: none
- feature_docs: none
- cross_cutting_docs: none
- operating_system_docs:
  - `docs/operating_system/repo-governance.md`
  - `docs/operating_system/doc-system-lifecycle.md`
  - `docs/operating_system/project-adoption-migration-guide.md`
- readme: none
- generated: none

Generated refresh required: no
Capability IDs: none
Invariant IDs: none
Spec needed: yes
Plan needed: yes

## Problem

Mode A currently has a policy gap between what the docs imply and what the
validators actually require.

In practice:

1. the Mode A template pack is not self-contained enough for the canonical
   validator path
2. the canonical validator path still assumes architecture-sync machinery
3. starter-only repos can end up pulled into managed-style metadata discipline
   indirectly through shared sync/generator checks
4. `starter_method_only` both discourages generated architecture outputs and
   still routes through tooling that expects them

That creates downstream failure modes:

- missing starter-owned validation/sync scripts after bootstrap
- hidden dependencies on generator/audit/format helper scripts and tests
- local validator patching to “make it pass”
- confusion about whether Mode A is truly lighter than managed mode

## Current Gaps

### 1. `docs/features/` is not required in Mode A today

The current validator only requires the lean folder surface:

- `docs/intent/`
- `docs/operating_system/`
- `docs/superpowers/specs/`
- `docs/superpowers/plans/`
- `repo_config/`
- `scripts/`
- `tests/`

`docs/features/`, `docs/stages/`, and `docs/generated/` are still conditional.

That is acceptable for a genuinely lightweight Mode A, but it means the system
must not quietly assume managed feature folders or generated discovery are
present.

### 2. The Mode A template pack is too small for the current canonical validator path

The current `MODE_A_TEMPLATE_REQUIRED_FILES` list focuses on docs, config, and
placeholders, but it does not require the actual sync/validation toolchain used
by `scripts/validate_repo_contracts.py`.

### 3. The canonical repo-contract validator still assumes architecture-sync flow

`scripts/validate_repo_contracts.py` invokes:

- `scripts/sync_architecture_docs.py --check`
- `scripts/validate_adoption_shape.py`
- `scripts/validate_repo_config.py`

That means Mode A is still routed through architecture-sync tooling even when
the repo has not opted into managed architecture metadata.

### 4. Mode A can inherit stronger metadata requirements indirectly

Even when repo-contract validation does not directly scan arbitrary Python files
for `@meta`, the architecture generator path can do so during sync/check.

That makes starter-only repos feel “half managed”:

- stricter than the docs first suggest
- not strict in a clearly documented, intentionally adopted way

## Goal

Make Mode A explicit and coherent by choosing one simple contract:

- Mode A is genuinely lighter than managed mode
- Mode A bootstrap docs say exactly which files are required
- the canonical validator path honors that lighter contract

## Non-Goals

This spec does not remove managed architecture metadata mode.

This spec does not weaken managed-mode validator enforcement.

This spec does not make `docs/features/` globally required for every repo.

This spec does not redesign the full architecture generator.

This spec does not force downstream starter-only repos to publish generated
architecture discovery just to satisfy a method-only setup.

## Recommended Design

Choose the simpler path:

## Path B: Make Mode A truly lighter

Instead of copying the full architecture toolchain into every Mode A bootstrap,
make the canonical validator flow mode-aware.

### Validator ownership model

- `starter_method_only`
  - validates repo shape, required docs, adoption-mode consistency, and the
    absence of managed feature/stage metadata
  - does not require managed feature folders
  - does not require non-empty generated architecture discovery
  - does not require the managed architecture sync/generator path as a normal
    bootstrap invariant

- `managed_architecture_metadata`
  - keeps the current full architecture sync/generator/contract expectations

- `legacy_compatibility`
  - keeps its own compatibility rules, separate from Mode A

### Canonical repo-contract behavior

`scripts/validate_repo_contracts.py` should branch by adoption mode:

- in `starter_method_only`
  - run `validate_adoption_shape.py`
  - run `validate_repo_config.py`
  - run repo-contract checks that are still mode-appropriate
  - skip architecture-sync/generator checks that belong only to managed mode

- in managed mode
  - keep the current architecture sync/check path

This keeps the canonical command canonical while still respecting mode.

### Mode A bootstrap expectations

The Mode A template pack should explicitly require only the starter-owned files
needed for Mode A itself.

If a script remains required by the canonical Mode A validator path, it must be
present in the template pack.

If a script is managed-mode-only, it should not be silently required for a
starter-only repo.

### `docs/features/` and `docs/generated/`

For Mode A:

- `docs/features/` remains optional
- if present, it may contain prose-only scaffolding such as `README.md`
- feature metadata files remain forbidden until the repo adopts managed mode

- `docs/generated/` remains optional
- empty scaffolds may exist
- non-empty managed discovery should not be required to make Mode A valid

### Documentation updates

The migration guide and repo governance docs should say plainly:

- Mode A is lighter, but not “no validation”
- Mode A validates repo method, docs, and adoption boundaries
- Mode A does not imply the full managed architecture sync/generator toolchain
- if a repo wants the full feature/stage/generated contract system, it must
  adopt managed mode

## Alternative Rejected

### Path A: Make Mode A bootstrap copy the full architecture toolchain

This would reduce “missing file” failures, but it would also make Mode A much
heavier in practice and blur the distinction between:

- method-only starter adoption
- managed architecture metadata

That path makes the bootstrap more self-contained, but at the cost of making
Mode A feel like managed mode with fewer docs rather than a genuinely lighter
operating model.

## Acceptance Criteria

- `starter_method_only` repos can pass the canonical repo-contract validator
  without carrying the full managed architecture sync/generator dependency chain
- the validator no longer pushes Mode A repos into managed-style generated
  discovery expectations
- the Mode A template pack and migration guide state the required bootstrap
  surface explicitly
- `docs/features/` and required files inside it are enforced only when the
  adopted mode actually requires them
- downstream repos no longer need local starter-validator patches just to keep
  Mode A aligned with upstream

## Follow-Up Implementation Notes

The implementation plan should likely include:

1. centralize adoption-mode branching for repo-contract orchestration
2. make `sync_architecture_docs.py` managed-mode-only in the canonical path
3. tighten Mode A template docs around what is and is not expected
4. add regression tests for:
   - starter-only repo without `docs/features/`
   - starter-only repo without managed generated discovery
   - managed repo that still requires full architecture sync/check
