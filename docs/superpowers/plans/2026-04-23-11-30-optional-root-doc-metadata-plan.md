---
layer: operating_system
artifact_type: plan
status: active
parent_workstream: none
targets:
  - scripts/validate_adoption_shape.py
  - tools/docs/generate_architecture_metadata.py
  - tests/test_validate_adoption_shape.py
  - tests/test_architecture_metadata_generation.py
  - docs/operating_system/repo-governance.md
  - docs/operating_system/doc-system-lifecycle.md
  - docs/operating_system/project-adoption-migration-guide.md
  - docs/architecture_templates/markdown-frontmatter.md
related_features: []
related_stages: []
---

# Optional Root Doc Metadata Implementation Plan

**Feature Source:** `none`  
**Feature Contract:** `none`  
**Spec:** `docs/superpowers/specs/2026-04-23-optional-root-doc-metadata-spec.md`  
**Type:** modify  
**Plan Layer:** operating_system  
**Plan Status:** active

**Goal:** Keep optional root docs optional when absent, but validator-enforce their managed metadata shape when present.

**Architecture:** Extend the existing managed root-doc metadata validator with a second optional-doc rule table. Reuse the same frontmatter parser and metadata checks as required root docs. Tighten the architecture metadata generator so misplaced frontmatter is rejected instead of silently skipped.

**Key Invariants:**
- Optional docs are not required.
- Present optional docs in managed mode are metadata-linked cross-cutting docs.
- Frontmatter must be visible to tooling or fail clearly.

---

## Tasks

### Task 1: Add failing tests

1. Add adoption-shape tests for malformed `docs/dataset.md` metadata.
2. Add adoption-shape tests for `docs/api.md` without required explain links.
3. Add adoption-shape tests for misplaced optional-doc frontmatter.
4. Add generator tests for misplaced Markdown frontmatter.

### Task 2: Implement adoption-shape validation

1. Add optional root-doc metadata rules.
2. Reuse the managed root-doc metadata helper for required and optional docs.
3. Reject metadata-looking frontmatter that does not start at the first byte.

### Task 3: Tighten generator parsing

1. Allow a UTF-8 BOM before frontmatter.
2. Reject leading-whitespace frontmatter with a clear error.
3. Reject malformed top-of-file frontmatter rather than treating it as absent metadata.

### Task 4: Update docs

1. Update repo governance and doc-system lifecycle guidance.
2. Update the migration guide and Markdown frontmatter template.
3. Keep the language clear that optional docs stay optional when absent.

### Task 5: Verify

1. Run Python compile checks.
2. Run focused adoption-shape and generator tests.
3. Run the full relevant test files.
4. Run the repo adoption validator.
