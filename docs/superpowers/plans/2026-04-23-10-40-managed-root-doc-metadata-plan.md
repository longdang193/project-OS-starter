---
layer: operating_system
artifact_type: plan
status: active
parent_workstream: none
targets:
  - scripts/validate_adoption_shape.py
  - tests/test_validate_adoption_shape.py
  - docs/operating_system/governance/repo-governance.md
  - docs/operating_system/skill-doc-system-lifecycle.md
  - docs/operating_system/adoption/project-adoption-migration-guide.md
  - docs/architecture_templates/markdown-frontmatter.md
related_features: []
related_stages: []
---

# Managed Root Doc Metadata Implementation Plan

**Feature Source:** `none`
**Feature Contract:** `none`
**Spec:** `docs/superpowers/specs/2026-04-23-managed-root-doc-metadata-spec.md`
**Type:** modify
**Plan Layer:** operating_system
**Plan Status:** active

> **For agentic workers:** Use `skill-executing-plans` when carrying out the implementation in-session.

**Goal:** Make managed repos treat the required root docs as metadata-linked docs with validator-enforced frontmatter instead of optional unlinked prose.

**Architecture:** Keep the implementation centered in `scripts/validate_adoption_shape.py`. Reuse the existing required-root-doc pass for presence and substance checks, add a narrow managed-mode metadata validator for the same files, and document the new managed migration target in the operating-system docs and frontmatter template guidance.

**Key Invariants:**
- Root docs remain cross-cutting explanations, not the deepest source of truth.
- Managed mode keeps one explicit migration target for root-doc metadata.
- Starter-only repos are not forced into managed root-doc frontmatter.
- Metadata should help discovery and validation without turning every Markdown file into a metadata-heavy artifact.

**Rollout / Revert:**
- rollback_trigger: The new validator rejects the current starter repo fixtures or obviously valid managed root-doc examples.
- rollback_method: Revert the managed root-doc metadata validator and keep only the existing presence/substance checks until the contract is refined.

---

## Doc Update Matrix

- Feature source: none
- Feature contract: none
- Feature lineage: none
- Stage source: none
- Stage contract: none
- Feature-specific docs: none
- Cross-cutting docs:
  - `docs/setup.md`
  - `docs/configuration.md`
  - `docs/usage.md`
  - `docs/pipeline.md`
  - `docs/architecture.md`
- Operating-system docs:
  - `docs/operating_system/governance/repo-governance.md`
  - `docs/operating_system/skill-doc-system-lifecycle.md`
  - `docs/operating_system/adoption/project-adoption-migration-guide.md`
  - `docs/architecture_templates/markdown-frontmatter.md`
- README: none
- Generated discovery: none

---

## Files To Modify

- `scripts/validate_adoption_shape.py`
- `tests/test_validate_adoption_shape.py`
- `docs/operating_system/governance/repo-governance.md`
- `docs/operating_system/skill-doc-system-lifecycle.md`
- `docs/operating_system/adoption/project-adoption-migration-guide.md`
- `docs/architecture_templates/markdown-frontmatter.md`

## Tests To Add Or Update

- Add failing tests for:
  - missing frontmatter on managed `docs/pipeline.md`
  - missing `explains.stages` on managed `docs/pipeline.md`
- Update managed-mode seed fixtures so required root docs use the canonical metadata shape.
- Keep starter-only fixtures unchanged so the scope stays limited to managed mode.

## Verification Commands

- `python -m py_compile scripts/validate_adoption_shape.py tests/test_validate_adoption_shape.py`
- `$env:PYTHONPATH=(Resolve-Path '.tmp-tests\pytest-deps').Path; python -m pytest tests/test_validate_adoption_shape.py -q`
- `$env:PYTHONPATH=(Resolve-Path '.tmp-tests\pytest-deps').Path; python scripts/validate_adoption_shape.py`
- `$env:PYTHONPATH=(Resolve-Path '.tmp-tests\pytest-deps').Path; python scripts/validate_adoption_shape.py --repo-root 'C:\Users\HOANG PHI LONG DANG\repos\JOB-PROJECT'`

---

## Tasks

### Task 1: Add failing tests for the missing managed root-doc metadata contract

1. Update the managed fixture helper to write root docs with canonical frontmatter.
2. Add one test that proves managed `docs/pipeline.md` fails when frontmatter is missing.
3. Add one test that proves managed `docs/pipeline.md` fails when `explains.stages` is absent.
4. Run the targeted pytest slice and confirm the new tests fail before implementation.

### Task 2: Implement managed root-doc metadata validation

1. Add a small parsing helper for Markdown frontmatter.
2. Keep the existing required-root-doc content checks, but evaluate body/heading coverage after removing frontmatter.
3. Add a managed-mode validator that enforces:
   - frontmatter presence
   - canonical `doc_id`
   - non-empty `doc_type`
   - `explains` mapping with list-shaped values
   - file-appropriate required explain families
4. Re-run the focused tests and make them green.

### Task 3: Align docs and migration guidance

1. Update `repo-governance.md` and `skill-doc-system-lifecycle.md` to say required root docs are metadata-linked in managed mode.
2. Update `project-adoption-migration-guide.md` to call this out as part of managed migration.
3. Update the Markdown frontmatter template doc so agents understand that required managed root docs use this pattern.

### Task 4: Verify against starter and downstream drift

1. Run `py_compile`.
2. Run the full focused validator test file.
3. Run the validator on this repo.
4. Run the validator against `JOB-PROJECT` and confirm it now flags the missing `docs/pipeline.md` metadata.
