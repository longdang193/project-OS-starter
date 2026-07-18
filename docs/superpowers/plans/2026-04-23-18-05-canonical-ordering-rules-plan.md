---
layer: operating_system
artifact_type: plan
status: completed
parent_workstream: none
targets:
  - scripts/validate_adoption_shape.py
  - tests/test_validate_adoption_shape.py
  - docs/operating_system/skill-doc-system-lifecycle.md
  - docs/operating_system/governance/repo-governance.md
  - docs/operating_system/adoption/project-adoption-migration-guide.md
  - docs/architecture_templates/feature.source.yaml
  - docs/architecture_templates/stage.source.yaml
  - docs/architecture_templates/markdown-frontmatter.md
related_features: []
related_stages: []
---

# Canonical Ordering Rules Implementation Plan

**Feature Source:** `none`
**Feature Contract:** `none`
**Spec:** `docs/superpowers/specs/2026-04-23-canonical-ordering-rules-spec.md`
**Type:** modify
**Plan Layer:** operating_system
**Plan Status:** completed

> **For agentic workers:** Use `skill-executing-plans` or `skill-subagent-driven-development` to implement task-by-task.

**Goal:** Add Phase 2 canonical ordering validation for non-semantic managed metadata lists, starting with human-authored sources and managed root-doc frontmatter.

**Architecture:** Extend the Phase 1 canonical-style helper layer with ordering-aware validators that run only after normalization succeeds. Land Phase 2A first on human-authored feature source, stage source, and managed root-doc frontmatter lists, then update docs/templates so the starter states the ordering contract plainly without overpromising generator-side enforcement.

**Key Invariants:**
- Only unordered field classes get ordering enforcement.
- Chronology and workflow sequences such as `timeline` remain exempt.
- The validator rejects non-canonical ordering but does not rewrite files.
- Phase 2A must stay limited to low-ambiguity human-authored lists and managed frontmatter.
- Generated ref-family ordering stays out of this pass unless tests prove the current starter fixtures are already stable.

**Rollout / Revert:**
- rollback_trigger: Phase 2A flags current starter fixtures or realistic managed examples whose order is actually semantic or generator-dependent.
- rollback_method: Remove the ordering helper calls for the noisy fields, keep the spec/plan, and retry with a narrower field set.

---

## Doc Update Matrix

- Feature source: none
- Feature contract: none
- Feature lineage: none
- Stage source: none
- Stage contracts: none
- Feature history: none
- Feature-specific docs: none
- Cross-cutting docs:
  - `docs/architecture_templates/feature.source.yaml`
  - `docs/architecture_templates/stage.source.yaml`
  - `docs/architecture_templates/markdown-frontmatter.md`
- Operating-system docs:
  - `docs/operating_system/skill-doc-system-lifecycle.md`
  - `docs/operating_system/governance/repo-governance.md`
  - `docs/operating_system/adoption/project-adoption-migration-guide.md`
  - `docs/superpowers/specs/2026-04-23-canonical-ordering-rules-spec.md`
- README: none
- Generated discovery: none

## Files To Modify

```text
scripts/validate_adoption_shape.py
tests/test_validate_adoption_shape.py
docs/operating_system/skill-doc-system-lifecycle.md
docs/operating_system/governance/repo-governance.md
docs/operating_system/adoption/project-adoption-migration-guide.md
docs/architecture_templates/feature.source.yaml
docs/architecture_templates/stage.source.yaml
docs/architecture_templates/markdown-frontmatter.md
docs/superpowers/specs/2026-04-23-canonical-ordering-rules-spec.md
```

## Scope Boundary

Implement only Phase 2A in this pass:

1. feature source unordered lists
2. stage source unordered lists
3. managed root-doc `explains.*` lists
4. template examples and operating-system docs that describe those rules

Do not implement generated feature/stage ref ordering in this pass unless the
tests show the starter fixtures are already stable and the implementation stays
small.

## Task 1: Add Focused Failing Ordering Tests

**Files:**
- Modify: `tests/test_validate_adoption_shape.py`
- Docs: none

- [x] Step 1: Add failing tests for unsorted `feature.source.yaml` fields:
  - `domains`
  - `depends_on`
  - `lineage_exceptions`
  - `stage_participation[*].capability_ids`
- [x] Step 2: Add failing tests for unsorted `docs/stages/*.source.yaml` fields:
  - `primary_features`
  - `supporting_features`
  - `inputs`
  - `outputs`
- [x] Step 3: Add failing tests for unsorted managed root-doc frontmatter:
  - `explains.features`
  - `explains.capabilities`
  - `explains.stages`
  - path-like `explains.configs` or `explains.components` when applicable
- [x] Step 4: Add passing control tests proving already sorted fixtures still validate.
- [x] Step 5: Run only the new ordering-focused tests and confirm they fail for the new assertions.

Suggested focused command:

```powershell
$env:UV_CACHE_DIR=$env:TEMP; uv run python -m pytest tests/test_validate_adoption_shape.py -k "ordering or sorted or explains" -q
```

## Task 2: Implement Reusable Ordering Helpers

**Files:**
- Modify: `scripts/validate_adoption_shape.py`
- Test: `tests/test_validate_adoption_shape.py`
- Docs: none

- [x] Step 1: Add helper functions for canonical ordering validation, such as:
  - `validate_sorted_string_list(...)`
  - `validate_sorted_path_list(...)`
  - any small shared sort-key helper needed for repo-relative paths
- [x] Step 2: Make the helpers field-path aware so findings name the exact offending field.
- [x] Step 3: Ensure ordering checks run only after Phase 1 normalization passes for the same field.
- [x] Step 4: Keep error messages concise and corrective, including the expected canonical order when practical.
- [x] Step 5: Rerun the focused tests and confirm the helper layer makes them pass.

## Task 3: Apply Ordering Rules To Phase 2A Surfaces

**Files:**
- Modify: `scripts/validate_adoption_shape.py`
- Test: `tests/test_validate_adoption_shape.py`
- Docs: none

- [x] Step 1: Apply ordering checks to managed `feature.source.yaml` unordered lists.
- [x] Step 2: Apply ordering checks to managed `docs/stages/*.source.yaml` unordered lists.
- [x] Step 3: Apply ordering checks to managed required and optional root-doc `explains.*` lists.
- [x] Step 4: Confirm ordered surfaces such as `timeline` remain untouched and unvalidated for lexical order.
- [x] Step 5: Rerun the focused ordering tests and confirm they pass.

## Task 4: Align Templates And Guidance

**Files:**
- Modify: `docs/architecture_templates/feature.source.yaml`
- Modify: `docs/architecture_templates/stage.source.yaml`
- Modify: `docs/architecture_templates/markdown-frontmatter.md`
- Modify: `docs/operating_system/skill-doc-system-lifecycle.md`
- Modify: `docs/operating_system/governance/repo-governance.md`
- Modify: `docs/operating_system/adoption/project-adoption-migration-guide.md`
- Modify: `docs/superpowers/specs/2026-04-23-canonical-ordering-rules-spec.md`

- [x] Step 1: Update template examples so unordered lists already appear in canonical order.
- [x] Step 2: Add explicit guidance that ordering is part of canonical style only for non-semantic fields.
- [x] Step 3: State plainly that chronology and workflow sequences stay exempt.
- [x] Step 4: Keep the wording scoped to Phase 2A and avoid implying generated ref-family ordering is already enforced.

## Task 5: Run Full Verification

**Files:**
- Test: `tests/test_validate_adoption_shape.py`
- Verify: `scripts/validate_adoption_shape.py`
- Docs: all modified docs above

- [x] Step 1: Run the full validator test file:

```powershell
$env:UV_CACHE_DIR=$env:TEMP; uv run python -m pytest tests/test_validate_adoption_shape.py -q
```

- [x] Step 2: Run the starter validator:

```powershell
$env:UV_CACHE_DIR=$env:TEMP; uv run python scripts/validate_adoption_shape.py
```

- [x] Step 3: Run generated metadata check:

```powershell
$env:UV_CACHE_DIR=$env:TEMP; uv run python tools/docs/generate_architecture_metadata.py --check
```

- [x] Step 4: Run whitespace validation:

```powershell
git diff --check
```

- [x] Step 5: Review `git diff` and confirm the change stayed within Phase 2A ordering scope.

## Task 6: Downstream Sanity Check

**Files:**
- Verify only: downstream repo `C:\Users\HOANG PHI LONG DANG\repos\JOB-PROJECT`

- [x] Step 1: Run the updated validator against `JOB-PROJECT`.
- [x] Step 2: Record whether any existing managed metadata now fails only because of unordered-list ordering.
- [x] Step 3: Confirm the findings are objective and useful, not generator-noise or chronology false positives.
- [x] Step 4: Keep downstream fixes out of this starter change unless explicitly requested.

Suggested downstream command:

```powershell
$env:UV_CACHE_DIR=$env:TEMP; uv run python scripts/validate_adoption_shape.py --repo-root 'C:\Users\HOANG PHI LONG DANG\repos\JOB-PROJECT'
```
