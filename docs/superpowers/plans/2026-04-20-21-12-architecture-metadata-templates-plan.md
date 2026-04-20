---
layer: operating_system
artifact_type: plan
status: active
parent_workstream: none
targets:
  - docs/architecture_templates/
  - docs/operating_system/project-adoption-migration-guide.md
  - docs/operating_system/doc-system-lifecycle.md
  - docs/features/README.md
  - docs/stages/README.md
related_features: []
related_stages: []
---

# Architecture Metadata Templates Implementation Plan

**Feature Source:** `none`
**Feature Contract:** `none`
**Spec:** `docs/superpowers/specs/2026-04-20-architecture-metadata-templates-spec.md`
**Type:** add
**Plan Layer:** operating_system
**Plan Status:** active

> **For agentic workers:** Use `executing-plans` or `subagent-driven-development` to implement task-by-task.

**Goal:** Add copy-safe Mode B architecture metadata templates and guide links that prevent double-entry drift.

**Architecture:** The template package lives under `docs/architecture_templates/` as operating-system guidance. It contains human-authored input examples only; generated contracts, lineage, stage contracts, and discovery outputs remain generator-owned and are referenced but not templated.

**Key Invariants:**

- Canonical truth flows downward from upstream owning layers; downstream layers derive views instead of re-entering the same fact.
- Templates are for `managed_architecture_metadata` mode or explicit Mode B migration work only.
- Generated files must not be copied from templates.
- Product/domain metadata must not represent starter adoption, repo governance, adapter work, publication setup, or agent/rule work.

**Rollout / Revert:**

- rollback_trigger: Validators start treating template examples as real architecture metadata, or template guidance contradicts the generator schema.
- rollback_method: Revert `docs/architecture_templates/` and the four guide links, then rerun adoption and architecture checks.

---

## Triage

Layer: operating_system
Feature type: ADD
Summary: Add a cross-cutting architecture metadata template package for Mode B adoption.
Reasoning: This work creates repo-method guidance and copy-safe examples, not a product feature, stage, or generated architecture output.
Invariants:

- Templates reinforce source ownership and no-double-entry guidance.
- Templates use supported schema fields only.
- Markdown metadata examples must be fenced examples, not active frontmatter scanned as real docs.
- Generated outputs remain excluded from human-copy templates.

Dependencies:

- `docs/operating_system/doc-system-lifecycle.md`
- `docs/operating_system/project-adoption-migration-guide.md`
- `docs/operating_system/feature-routing-guide.md`
- `tools/docs/generate_architecture_metadata.py`
- `scripts/validate_adoption_shape.py`
- `scripts/sync_architecture_docs.py`

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
  - `docs/architecture_templates/README.md`
  - `docs/architecture_templates/feature.source.yaml`
  - `docs/architecture_templates/stage.source.yaml`
  - `docs/architecture_templates/history.md`
  - `docs/architecture_templates/python-meta.py.template`
  - `docs/architecture_templates/python-capability.py.template`
  - `docs/architecture_templates/python-proves-test.py.template`
  - `docs/architecture_templates/yaml-architecture.yaml`
  - `docs/architecture_templates/markdown-frontmatter.md`
  - `docs/architecture_templates/mode-b-feature-migration-checklist.md`
  - `docs/operating_system/project-adoption-migration-guide.md`
  - `docs/operating_system/doc-system-lifecycle.md`
  - `docs/features/README.md`
  - `docs/stages/README.md`
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
- Cross-cutting docs: `docs/architecture_templates/*`
- Operating-system docs: `docs/operating_system/project-adoption-migration-guide.md`, `docs/operating_system/doc-system-lifecycle.md`
- README: none
- Generated discovery: none

## File Structure

- Create: `docs/architecture_templates/README.md`
- Create: `docs/architecture_templates/feature.source.yaml`
- Create: `docs/architecture_templates/stage.source.yaml`
- Create: `docs/architecture_templates/history.md`
- Create: `docs/architecture_templates/python-meta.py.template`
- Create: `docs/architecture_templates/python-capability.py.template`
- Create: `docs/architecture_templates/python-proves-test.py.template`
- Create: `docs/architecture_templates/yaml-architecture.yaml`
- Create: `docs/architecture_templates/markdown-frontmatter.md`
- Create: `docs/architecture_templates/mode-b-feature-migration-checklist.md`
- Modify: `docs/operating_system/project-adoption-migration-guide.md`
- Modify: `docs/operating_system/doc-system-lifecycle.md`
- Modify: `docs/features/README.md`
- Modify: `docs/stages/README.md`
- Test: no new test files planned
- Generated outputs: none

## Source Spec

This plan implements:

- `docs/superpowers/specs/2026-04-20-architecture-metadata-templates-spec.md`

## Tasks

### Task 1: Create Template Package README

**Files:**

- Create: `docs/architecture_templates/README.md`
- Docs: `docs/architecture_templates/README.md`

- [ ] Step 1: Create `docs/architecture_templates/README.md`.
- [ ] Step 2: State templates are for Mode B only.
- [ ] Step 3: Add the no-double-entry rule.
- [ ] Step 4: List copyable human-owned inputs.
- [ ] Step 5: List generated outputs that must not be copied.
- [ ] Step 6: Link adoption and lifecycle guides.
- [ ] Step 7: Include validation commands.

### Task 2: Create Feature, Stage, And History Templates

**Files:**

- Create: `docs/architecture_templates/feature.source.yaml`
- Create: `docs/architecture_templates/stage.source.yaml`
- Create: `docs/architecture_templates/history.md`
- Docs: `docs/architecture_templates/*`

- [ ] Step 1: Create `feature.source.yaml` with supported fields only.
- [ ] Step 2: Omit generated freshness fields and `manual_refs`.
- [ ] Step 3: Create `stage.source.yaml` with stage-owned role semantics.
- [ ] Step 4: Create `history.md` with generated-history markers and human notes.
- [ ] Step 5: Ensure no generated output template is created.

### Task 3: Create Source Metadata Templates

**Files:**

- Create: `docs/architecture_templates/python-meta.py.template`
- Create: `docs/architecture_templates/python-capability.py.template`
- Create: `docs/architecture_templates/python-proves-test.py.template`
- Create: `docs/architecture_templates/yaml-architecture.yaml`
- Create: `docs/architecture_templates/markdown-frontmatter.md`
- Docs: `docs/architecture_templates/*`

- [ ] Step 1: Create Python `@meta` example.
- [ ] Step 2: Create canonical Python `@capability` example.
- [ ] Step 3: Create Python test `@proves` example.
- [ ] Step 4: Create YAML `# @architecture` example.
- [ ] Step 5: Create Markdown frontmatter example as fenced code, not active frontmatter.
- [ ] Step 6: Include comments that identify ownership boundaries and avoid double entry.

### Task 4: Create Mode B Migration Checklist

**Files:**

- Create: `docs/architecture_templates/mode-b-feature-migration-checklist.md`
- Docs: `docs/architecture_templates/mode-b-feature-migration-checklist.md`

- [ ] Step 1: Create a short operational checklist.
- [ ] Step 2: Include adoption mode confirmation.
- [ ] Step 3: Include feature/stage/source metadata creation sequence.
- [ ] Step 4: Include generator, validator, test, and commit checks.

### Task 5: Link Guides To Templates

**Files:**

- Modify: `docs/operating_system/project-adoption-migration-guide.md`
- Modify: `docs/operating_system/doc-system-lifecycle.md`
- Modify: `docs/features/README.md`
- Modify: `docs/stages/README.md`
- Docs: exact files above

- [ ] Step 1: Link the Mode B runbook to `docs/architecture_templates/`.
- [ ] Step 2: Add `docs/architecture_templates/` to doc-system lifecycle as operating-system guidance.
- [ ] Step 3: Link feature README to feature templates.
- [ ] Step 4: Link stage README to stage templates.
- [ ] Step 5: Keep guide updates short; do not duplicate the full template guidance.

### Task 6: Verify

**Files:**

- Test: no new test files
- Docs: all created/modified docs

- [ ] Step 1: Run:

```powershell
python scripts/validate_adoption_shape.py
```

- [ ] Step 2: Run:

```powershell
python scripts/sync_architecture_docs.py --check
```

- [ ] Step 3: Run:

```powershell
pytest -q
```

- [ ] Step 4: Run:

```powershell
git diff --check
```

- [ ] Step 5: Review:

```powershell
git status --short --branch
git diff -- docs/architecture_templates docs/operating_system/project-adoption-migration-guide.md docs/operating_system/doc-system-lifecycle.md docs/features/README.md docs/stages/README.md
```

## Acceptance Criteria

- `docs/architecture_templates/README.md` exists and explains Mode B-only usage.
- The README includes the no-double-entry rule.
- Templates exist for feature source, stage source, history, Python `@meta`, Python `@capability`, Python `@proves`, YAML `# @architecture`, Markdown frontmatter, and a Mode B feature migration checklist.
- Templates avoid unsupported fields.
- Templates do not include copyable generated contract or generated lineage files.
- The adoption migration guide links to the template package from Mode B guidance.
- The doc-system lifecycle doc identifies the template package as operating-system guidance.
- Feature and stage READMEs link to the relevant templates without duplicating the full template guidance.
- `python scripts/validate_adoption_shape.py` passes.
- `python scripts/sync_architecture_docs.py --check` passes.
- `pytest -q` passes.
- `git diff --check` passes.
