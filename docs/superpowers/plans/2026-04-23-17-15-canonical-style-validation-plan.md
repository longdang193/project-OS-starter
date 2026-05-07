---
layer: operating_system
artifact_type: plan
status: completed
parent_workstream: none
targets:
  - scripts/validate_adoption_shape.py
  - tests/test_validate_adoption_shape.py
  - docs/operating_system/skill-doc-system-lifecycle.md
  - docs/operating_system/repo-governance.md
  - docs/operating_system/project-adoption-migration-guide.md
  - docs/architecture_templates/feature.source.yaml
  - docs/architecture_templates/stage.source.yaml
  - docs/architecture_templates/markdown-frontmatter.md
related_features: []
related_stages: []
---

# Canonical Style Validation Implementation Plan

**Feature Source:** `none`  
**Feature Contract:** `none`  
**Spec:** `docs/superpowers/specs/2026-04-23-canonical-style-validation-spec.md`  
**Type:** modify  
**Plan Layer:** operating_system  
**Plan Status:** completed

> **For agentic workers:** Use `skill-executing-plans` or `skill-subagent-driven-development` to implement task-by-task.

**Goal:** Add a reusable canonical-style validation layer so the repo rejects valid-but-non-canonical required docs and managed metadata.

**Architecture:** This work extends `scripts/validate_adoption_shape.py` with reusable field-style helpers rather than more one-off checks. Phase 1 should land only the most objective rules first: concise string trimming and blank-line padding checks, unordered-list duplicate and empty-item checks, and repo-relative path normalization checks. Once those helpers and tests are stable, the docs and starter templates should be updated to state canonical style plainly.

**Key Invariants:**
- Canonical truth still flows from owning source layers into derived and generated surfaces.
- The validator rejects non-canonical inputs but does not rewrite files automatically.
- Phase 1 stays objective and low-ambiguity; broader ordering rules wait for later work.
- Managed templates should model canonical formatting rather than merely tolerated formatting.

**Rollout / Revert:**  
- rollback_trigger: Phase 1 rules produce noisy false positives in current starter fixtures or clearly valid managed examples.  
- rollback_method: Remove the new helper calls, revert the affected template/doc wording, and keep the spec for a narrower retry.

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
  - `docs/operating_system/repo-governance.md`
  - `docs/operating_system/project-adoption-migration-guide.md`
  - `docs/superpowers/specs/2026-04-23-canonical-style-validation-spec.md`
- README: none
- Generated discovery: none

## Files To Modify

```text
scripts/validate_adoption_shape.py
tests/test_validate_adoption_shape.py
docs/operating_system/skill-doc-system-lifecycle.md
docs/operating_system/repo-governance.md
docs/operating_system/project-adoption-migration-guide.md
docs/architecture_templates/feature.source.yaml
docs/architecture_templates/stage.source.yaml
docs/architecture_templates/markdown-frontmatter.md
docs/superpowers/specs/2026-04-23-canonical-style-validation-spec.md
```

## Phase 1 Scope

Implement only these canonical-style checks in this pass:

1. concise strings:
   - no leading/trailing whitespace
   - no blank-line padding
   - no double-newline content for concise fields
2. unordered string lists:
   - no empty-string items
   - no duplicate items
3. repo-relative path/reference strings:
   - no backslashes
   - no surrounding whitespace
   - no empty strings

Do not implement lexical ordering requirements in this pass unless a field is
already represented by stable canonical fixtures in the starter repo and the
rule is proven low-risk.

## Task 1: Add Reusable Canonical-Style Helpers

**Files:**
- Modify: `scripts/validate_adoption_shape.py`
- Test: `tests/test_validate_adoption_shape.py`
- Docs: none

- [x] Step 1: Add failing unit-style validator tests for concise-string, unordered-list, and repo-path canonical errors on temporary managed fixtures.
- [x] Step 2: Run the focused failing tests and confirm they fail for the expected new assertions.
- [x] Step 3: Add reusable helper functions in `scripts/validate_adoption_shape.py` for:
  - concise string validation
  - unordered string-list validation
  - repo-relative path validation
- [x] Step 4: Keep helper signatures field-path aware so findings can name the exact offending field.
- [x] Step 5: Run the focused tests again and confirm the helpers make them pass.

Suggested focused command:

```powershell
$env:UV_CACHE_DIR=$env:TEMP; uv run python -m pytest tests/test_validate_adoption_shape.py -k "canonical_style or summary or duplicate or path" -q
```

## Task 2: Apply Phase 1 Rules To Managed Feature Sources And Contracts

**Files:**
- Modify: `scripts/validate_adoption_shape.py`
- Test: `tests/test_validate_adoption_shape.py`
- Docs: none

- [x] Step 1: Add failing tests for `docs/features/*/feature.source.yaml` fields:
  - `summary` with trailing whitespace
  - `summary` with trailing blank lines
  - duplicated `depends_on`
  - duplicated `domains`
  - duplicated or empty `stage_participation[*].capability_ids`
- [x] Step 2: Add failing tests for generated feature contract concise fields and any path/reference fields already validated by the current schema.
- [x] Step 3: Wire the new helpers into managed feature-source validation paths.
- [x] Step 4: Wire the new helpers into generated feature-contract validation paths where field classes are already explicit.
- [x] Step 5: Run the focused tests and confirm they pass.

## Task 3: Apply Phase 1 Rules To Stage Docs, Managed Root Docs, And Lineage Paths

**Files:**
- Modify: `scripts/validate_adoption_shape.py`
- Test: `tests/test_validate_adoption_shape.py`
- Docs: none

- [x] Step 1: Add failing tests for stage source and generated stage contract concise fields such as `summary`, `name`, `primary_features`, and `supporting_features`.
- [x] Step 2: Add failing tests for managed root-doc frontmatter:
  - whitespace-padded `doc_id`
  - whitespace-padded `doc_type`
  - duplicate items in `explains.*`
  - empty-string items in `explains.*`
- [x] Step 3: Add failing tests for repo-relative path fields in lineage or generated metadata that currently allow backslash-style or padded paths.
- [x] Step 4: Apply the helpers to stage validation, managed root-doc validation, and existing lineage path checks.
- [x] Step 5: Run the focused tests and confirm they pass.

## Task 4: Align Starter Templates And Guidance With Canonical Style

**Files:**
- Modify: `docs/architecture_templates/feature.source.yaml`
- Modify: `docs/architecture_templates/stage.source.yaml`
- Modify: `docs/architecture_templates/markdown-frontmatter.md`
- Modify: `docs/operating_system/skill-doc-system-lifecycle.md`
- Modify: `docs/operating_system/repo-governance.md`
- Modify: `docs/operating_system/project-adoption-migration-guide.md`
- Modify: `docs/superpowers/specs/2026-04-23-canonical-style-validation-spec.md`

- [x] Step 1: Update managed templates so concise metadata fields use canonical single-line style and unordered lists do not model duplicates or empty items.
- [x] Step 2: Add explicit guidance that canonical style is part of the contract, not optional polish.
- [x] Step 3: Clarify that the validator enforces schema plus canonical style for required managed surfaces.
- [x] Step 4: Keep guidance scoped to Phase 1 rules; do not promise stronger ordering enforcement before it exists.

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

- [x] Step 5: Review `git diff` and confirm Phase 1 stayed within canonical-style scope and did not silently expand into list-order normalization.

## Task 6: Downstream Sanity Check With JOB-PROJECT

**Files:**
- Verify only: downstream repo `C:\Users\HOANG PHI LONG DANG\repos\JOB-PROJECT`

- [x] Step 1: Run the updated starter validator against `JOB-PROJECT`.
- [x] Step 2: Confirm that the `cv_system/feature.source.yaml` `summary` shape now fails with a clear canonical-style finding.
- [x] Step 3: Record any additional Phase 1-style failures surfaced by the stricter rules.
- [x] Step 4: Keep downstream fixes out of this starter change unless explicitly requested.
