---
layer: operating_system
artifact_type: plan
status: completed
parent_workstream: none
targets:
  - docs/project_templates/mode-a/
  - docs/operating_system/project-adoption-migration-guide.md
  - docs/operating_system/skill-doc-system-lifecycle.md
  - docs/operating_system/repo-governance.md
  - docs/architecture_templates/README.md
  - scripts/validate_adoption_shape.py
  - tests/test_validate_adoption_shape.py
related_features: []
related_stages: []
---

# Mode A Project Template Pack Implementation Plan

**Feature Source:** `none`  
**Feature Contract:** `none`  
**Spec:** `docs/superpowers/specs/2026-04-23-mode-a-project-template-pack-spec.md`  
**Type:** add  
**Plan Layer:** operating_system  
**Plan Status:** completed

> **For agentic workers:** Use `skill-executing-plans` or `skill-subagent-driven-development` to implement task-by-task.

**Goal:** Add a copyable Mode A starter-method template pack that includes required docs, intent docs, repo metadata/config, runtime config, and required folder anchors.

**Architecture:** The template pack should live under `docs/project_templates/mode-a/` and mirror destination repo paths so agents can copy files without renaming. Mode A templates must remain prose/config starter-method templates and must not include Mode B managed architecture metadata. Guidance and tests should make the new pack discoverable and keep it complete over time.

**Key Invariants:**

- Mode A remains `starter_method_only`; do not introduce feature, stage, capability, generated discovery, or lineage metadata.
- Repo metadata/config templates are required starter surfaces.
- Templates should be public-safe by default while preserving reproducibility detail.
- The template path mirrors the destination path.
- Mode B templates remain under `docs/architecture_templates/`.

**Rollout / Revert:**  
- rollback_trigger: Template-pack validation creates false positives for existing starter use or Mode B templates.  
- rollback_method: Remove the new template-pack files and corresponding validation/doc references.

---

## Doc Update Matrix

- Feature source: none
- Feature contract: none
- Feature lineage: none
- Stage source: none
- Stage contracts: none
- Feature history: none
- Feature-specific docs: none
- Cross-cutting docs: none
- Operating-system docs:
  - `docs/operating_system/project-adoption-migration-guide.md`
  - `docs/operating_system/skill-doc-system-lifecycle.md`
  - `docs/operating_system/repo-governance.md`
  - `docs/architecture_templates/README.md`
  - `docs/superpowers/specs/2026-04-23-mode-a-project-template-pack-spec.md`
- README: none
- Generated discovery: none

## Files To Create

```text
docs/project_templates/mode-a/README.md
docs/project_templates/mode-a/docs/setup.md
docs/project_templates/mode-a/docs/configuration.md
docs/project_templates/mode-a/docs/usage.md
docs/project_templates/mode-a/docs/pipeline.md
docs/project_templates/mode-a/docs/architecture.md
docs/project_templates/mode-a/docs/intent/README.md
docs/project_templates/mode-a/docs/intent/project-charter.md
docs/project_templates/mode-a/docs/intent/constraints-and-non-goals.md
docs/project_templates/mode-a/docs/intent/stakeholders.md
docs/project_templates/mode-a/docs/intent/success-outcomes.md
docs/project_templates/mode-a/repo_config/adoption-mode.yaml
docs/project_templates/mode-a/repo_config/publication-config.json
docs/project_templates/mode-a/repo_config/agent-adapter-mappings.json
docs/project_templates/mode-a/configs/starter-runtime.yaml
docs/project_templates/mode-a/scripts/README.md
docs/project_templates/mode-a/tests/README.md
```

## Task 1: Add Template-Pack Completeness Tests

**Files:**

- Modify: `tests/test_validate_adoption_shape.py`
- Modify: `scripts/validate_adoption_shape.py`

- [x] Step 1: Add constants for the Mode A template pack root and required file list.
- [x] Step 2: Add a validator function that checks `docs/project_templates/mode-a/` contains every required template file.
- [x] Step 3: Validate `docs/project_templates/mode-a/repo_config/adoption-mode.yaml` declares `adoption_mode: starter_method_only`, `managed_architecture_metadata: false`, `legacy_feature_contracts: false`, and `architecture_generator: none`.
- [x] Step 4: Validate Mode A templates do not contain managed metadata markers such as `@capability`, `@proves`, `feature.source.yaml`, `stage.source.yaml`, `explains.features`, `capability_id:`, or `capability_ids:`.
- [x] Step 5: Add tests proving missing template files, wrong adoption mode, and managed metadata markers fail.
- [x] Step 6: Run the focused tests and confirm they fail before templates/implementation exist:

```powershell
$env:UV_CACHE_DIR=$env:TEMP; uv run python -m pytest tests/test_validate_adoption_shape.py -k "mode_a_template" -q
```

## Task 2: Create The Mode A Template Pack

**Files:**

- Create: all files listed in "Files To Create"

- [x] Step 1: Create `docs/project_templates/mode-a/README.md` describing copy direction, Mode A scope, and the no-managed-metadata rule.
- [x] Step 2: Create public-safe required doc templates:
  - `README.md`
  - `docs/setup.md`
  - `docs/configuration.md`
  - `docs/usage.md`
  - `docs/pipeline.md`
  - `docs/architecture.md`
- [x] Step 3: Create intent templates:
  - `docs/intent/README.md`
  - `docs/intent/project-charter.md`
  - `docs/intent/constraints-and-non-goals.md`
  - `docs/intent/stakeholders.md`
  - `docs/intent/success-outcomes.md`
- [x] Step 4: Create metadata/config templates:
  - `repo_config/adoption-mode.yaml`
  - `repo_config/publication-config.json`
  - `repo_config/agent-adapter-mappings.json`
  - `configs/starter-runtime.yaml`
- [x] Step 5: Create required-folder anchors:
  - `scripts/README.md`
  - `tests/README.md`
- [x] Step 6: Keep placeholders explicit and project-neutral. Use examples such as `<project-name>`, `<setup-command>`, `<runtime-profile>`, and `<public-path>`.

## Task 3: Update Mode A Guidance

**Files:**

- Modify: `docs/operating_system/project-adoption-migration-guide.md`
- Modify: `docs/operating_system/skill-doc-system-lifecycle.md`
- Modify: `docs/operating_system/repo-governance.md`
- Modify: `docs/architecture_templates/README.md`

- [x] Step 1: Update the Mode A runbook to say "start from `docs/project_templates/mode-a/`."
- [x] Step 2: Clarify that Mode A templates include repo metadata/config templates, not only prose docs.
- [x] Step 3: Add or update doc-system lifecycle wording so Mode A starter-method templates are separate from Mode B managed architecture templates.
- [x] Step 4: Update repo governance/publication guidance to say Mode A templates are public-safe starting points, while private operating-system surfaces still require curated publishing decisions.
- [x] Step 5: Update `docs/architecture_templates/README.md` to point Mode A users away from architecture templates and toward `docs/project_templates/mode-a/`.

## Task 4: Verify Template Pack Behavior

**Files:**

- Test: `tests/test_validate_adoption_shape.py`
- Verify: `scripts/validate_adoption_shape.py`

- [x] Step 1: Run focused tests:

```powershell
$env:UV_CACHE_DIR=$env:TEMP; uv run python -m pytest tests/test_validate_adoption_shape.py -k "mode_a_template" -q
```

- [x] Step 2: Run the full adoption-shape test file:

```powershell
$env:UV_CACHE_DIR=$env:TEMP; uv run python -m pytest tests/test_validate_adoption_shape.py -q
```

- [x] Step 3: Run the starter adoption validator:

```powershell
$env:UV_CACHE_DIR=$env:TEMP; uv run python scripts/validate_adoption_shape.py
```

- [x] Step 4: Run generated metadata check:

```powershell
$env:UV_CACHE_DIR=$env:TEMP; uv run python tools/docs/generate_architecture_metadata.py --check
```

- [x] Step 5: Run whitespace validation:

```powershell
git diff --check
```

- [x] Step 6: Review `git diff` to confirm no generated files were hand-edited and Mode B templates were not changed beyond README guidance.
