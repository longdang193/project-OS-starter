---
layer: operating_system
artifact_type: spec
status: proposed
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

# Mode A Project Template Pack Spec

## Triage

Layer: operating_system
Feature type: CHANGE
Summary: Add copyable Mode A starter-method templates for required docs, intent docs, repo metadata/config, runtime config, and required folder anchors.
Reasoning: Mode A adoption currently tells projects which files and folders to create, but it does not provide a complete copyable template pack. This leaves agents to invent `repo_config/`, `configs/`, required docs, and folder anchors from memory, which creates drift and weakens reproducibility.
Invariants:

- Mode A remains starter-method-only and must not create product feature, stage, capability, generated discovery, or lineage metadata.
- Repo metadata/config templates are first-class starter surfaces, not afterthought examples.
- Template truth should flow from the starter template pack into adopted projects; downstream projects should fill placeholders rather than re-create the same structure manually.
- Mode A templates must not duplicate Mode B managed architecture templates.
- Required project docs should start public-safe by default and preserve reproducibility details without exposing private operating-system material.

Dependencies:

- `docs/operating_system/project-adoption-migration-guide.md`
- `docs/operating_system/skill-doc-system-lifecycle.md`
- `docs/operating_system/repo-governance.md`
- `docs/architecture_templates/README.md`
- `scripts/validate_adoption_shape.py`

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
- cross_cutting_docs:
  - `README.md`
  - `docs/setup.md`
  - `docs/configuration.md`
  - `docs/usage.md`
  - `docs/pipeline.md`
  - `docs/architecture.md`
  - `docs/intent/project-charter.md`
  - `docs/intent/constraints-and-non-goals.md`
  - `docs/intent/stakeholders.md`
  - `docs/intent/success-outcomes.md`
  - `docs/operating_system/project-adoption-migration-guide.md`
  - `docs/operating_system/skill-doc-system-lifecycle.md`
  - `docs/operating_system/repo-governance.md`
  - `docs/architecture_templates/README.md`
- readme: `README.md`
- generated: none

Generated refresh required: no
Capability IDs: none
Invariant IDs: none
Spec needed: yes
Plan needed: yes

## Problem

The starter now distinguishes three adoption modes:

- Mode A: starter method only
- Mode B: managed architecture metadata
- Mode C: legacy compatibility

Mode B has copyable architecture metadata templates under
`docs/architecture_templates/`. Mode A does not have an equivalent project
template pack.

The current Mode A guide names required docs and required folders, but agents
must still invent the initial files. This creates several drift risks:

- missing `repo_config/` metadata/config files
- missing `configs/` runtime config scaffold
- inconsistent required root docs
- missing `docs/intent/` starter files
- empty required folders without useful anchors
- accidental Mode B metadata in starter-method-only projects
- public-safety rewrites that trim too much reproducibility detail

The most important missing category is metadata/config templates. A project can
copy doc templates and still fail to declare the adoption mode, publication
boundary, adapter mapping, or runtime configuration in a reproducible way.

## Goal

Add a copyable Mode A project template pack that mirrors the expected starter
surface for a new project.

The pack should include:

- required project docs
- required intent docs
- required repo metadata/config files
- required runtime config scaffold
- anchor files for required folders that may otherwise be empty at project start

The adoption guide should point Mode A projects to this pack instead of asking
agents to invent the files.

## Non-Goals

This spec does not introduce managed feature/stage metadata into Mode A.

This spec does not replace `docs/architecture_templates/`; that directory
remains the Mode B managed metadata template surface.

This spec does not require optional docs such as `docs/dataset.md`,
`docs/api.md`, `docs/observability.md`, or `docs/testing.md` for every project.

This spec does not require projects to publish private operating-system docs.

## Template Location

Create a path-mirrored template pack:

```text
docs/project_templates/mode-a/
  README.md
  docs/
    setup.md
    configuration.md
    usage.md
    pipeline.md
    architecture.md
    intent/
      README.md
      project-charter.md
      constraints-and-non-goals.md
      stakeholders.md
      success-outcomes.md
  repo_config/
    adoption-mode.yaml
    publication-config.json
    agent-adapter-mappings.json
  configs/
    starter-runtime.yaml
  scripts/
    README.md
  tests/
    README.md
```

The template path should mirror the destination path so an agent can copy the
pack into a new project without translating names by hand.

## Required Metadata/Config Templates

### `repo_config/adoption-mode.yaml`

The Mode A template must declare starter-method-only adoption:

```yaml
adoption_mode: starter_method_only
managed_architecture_metadata: false
legacy_feature_contracts: false
architecture_generator: none
notes: >
  Repo operating-system, intent, adapter, and publication guidance are adopted.
  Product feature/stage metadata is intentionally not adopted yet.
```

This file is the source of truth for the selected adoption mode.

### `repo_config/publication-config.json`

The publication template should define the private-to-public boundary and make
public-safe defaults explicit. It should preserve reproducibility docs while
excluding private operating-system, agent-core, internal specs/plans, local
memory, and other private-only surfaces unless a curated publish workflow
rewrites them intentionally.

### `repo_config/agent-adapter-mappings.json`

The adapter mapping template should provide the starter-compatible mapping
surface for generated agent instructions and rules. Projects may customize
downstream outputs, but should not invent a new adapter source layout.

### `configs/starter-runtime.yaml`

The runtime config template should give projects a minimal, reproducible place
for environment/profile/debug defaults without mixing runtime settings into
repo governance metadata.

## Required Doc Templates

The Mode A pack should include public-safe, copyable versions of:

- `README.md`
- `docs/setup.md`
- `docs/configuration.md`
- `docs/usage.md`
- `docs/pipeline.md`
- `docs/architecture.md`

These docs should use placeholders for project-specific values, dependencies,
commands, data paths, and environment variables.

They should not include managed architecture frontmatter by default. Mode A
root docs are prose docs unless the project later migrates to Mode B.

Optional project docs such as `docs/dataset.md`, `docs/api.md`,
`docs/observability.md`, and `docs/testing.md` may be added later from the
same style, but they should not be required by the initial Mode A pack.

## Required Intent Templates

The Mode A pack should include:

- `docs/intent/README.md`
- `docs/intent/project-charter.md`
- `docs/intent/constraints-and-non-goals.md`
- `docs/intent/stakeholders.md`
- `docs/intent/success-outcomes.md`

Intent templates should be stable source-like docs. They should not become
execution logs, changelogs, or feature registries.

`docs/intent/README.md` should explain the purpose of the intent layer and
point to the deeper intent docs. It is an orientation anchor, not a replacement
for project-specific intent content.

## Required Folder Anchor Templates

The Mode A pack should include minimal anchors for required folders that may
otherwise be empty:

- `scripts/README.md`
- `tests/README.md`

These anchors should explain the expected contents and validation posture
without pretending that scripts or tests already exist.

## Relationship To Mode B Templates

`docs/architecture_templates/` remains the only starter-provided copyable
surface for managed architecture metadata.

Mode A docs should point to `docs/project_templates/mode-a/`.

Mode B docs should point to `docs/architecture_templates/`.

Agents should not copy `feature.source.yaml`, `stage.source.yaml`,
`markdown-frontmatter.md`, `python-capability.py.template`, or similar managed
metadata templates into a Mode A project unless the project is intentionally
migrating to Mode B.

## Validation And Guidance

Update guidance so Mode A adoption says:

- start from `docs/project_templates/mode-a/`
- fill placeholders instead of re-inventing file shapes
- keep `repo_config/adoption-mode.yaml` as the adoption-mode source of truth
- keep runtime config in `configs/`
- do not add feature/stage/capability metadata

Optionally update validation/docs tests to ensure the template pack exists and
contains the required files.

## Validation

Add or update tests for:

- Mode A template pack contains all required files
- Mode A template `repo_config/adoption-mode.yaml` declares
  `starter_method_only`
- Mode A project templates do not include managed architecture frontmatter or
  feature/stage/capability metadata
- adoption guide references the Mode A template pack
- architecture template README clearly remains Mode B-only
