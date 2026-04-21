---
layer: operating_system
artifact_type: spec
status: proposed
parent_workstream: none
targets:
  - README.md
  - docs/
  - docs/adoption_guide.md
  - docs/operating_system/doc-system-lifecycle.md
  - docs/operating_system/repo-governance.md
  - scripts/validate_adoption_shape.py
  - scripts/sync_architecture_docs.py
  - scripts/setup_hooks.ps1
  - scripts/setup_hooks.sh
  - .github/workflows/repo-hooks.yml
  - tests/test_validate_adoption_shape.py
  - tests/test_setup_hooks.py
related_features: []
related_stages: []
---

# Required Project Folder Surface Spec

## Triage

Layer: operating_system
Feature type: ADD
Summary: Define and enforce the minimum required project folder surface, including `docs/intent/`, and document the required files each required folder should contain.
Reasoning: This is repo-method governance for project structure, source-of-truth placement, and validation. It does not introduce a product feature or alter runtime behavior.
Invariants:

- `docs/intent/` remains the source for project purpose, promises, stakeholders, and non-goals.
- `docs/operating_system/` remains the source for repo method, governance, and internal workflow rules.
- `README.md` remains a synthesized orientation layer rather than the sole home for intent, setup, or architecture truth.
- Required folder enforcement should stay lean and stable; it should not force every optional surface into existence on day one.
- If a folder is required, the repo should also describe the minimum file(s) or content shape expected inside it so validation is not purely structural theater.
- Conditional folders such as `docs/features/`, `docs/stages/`, `docs/generated/`, and `configs/` should be enforced only when the adopted mode or project shape requires them.

Dependencies:

- `docs/operating_system/doc-system-lifecycle.md`
- `docs/operating_system/repo-governance.md`
- `docs/adoption_guide.md`
- `scripts/validate_adoption_shape.py`
- `scripts/sync_architecture_docs.py`
- `.github/workflows/repo-hooks.yml`

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
  - `docs/adoption_guide.md`
  - `docs/operating_system/doc-system-lifecycle.md`
  - `docs/operating_system/repo-governance.md`
  - `docs/setup.md`
  - `docs/configuration.md`
  - `docs/usage.md`
  - `docs/pipeline.md`
  - `docs/architecture.md`
- readme: `README.md`
- generated: none

Generated refresh required: no
Capability IDs: none
Invariant IDs: none
Spec needed: yes
Plan needed: yes

## Problem

The repo now enforces a minimum root project document set under `docs/`, but it
does not yet enforce the presence of `docs/intent/` even though the
source-of-truth model clearly treats intent as a first-class governing layer.

That creates an avoidable gap:

- governance docs say project purpose should live in `docs/intent/`
- validators do not fail when the folder is missing
- a project can pass baseline checks while lacking any stable source for
  purpose, audience, success outcomes, promises, or non-goals
- some required folders are named in governance docs, but the expected files
  inside them are not consistently described

Without a documented and validated folder contract, repo structure can drift
toward two bad outcomes:

- everything collapses upward into `README.md`
- teams create empty or ambiguous folders with no clear file-level purpose

## Goal

Define a lean required project folder surface and enforce it through the normal
validation path.

That required surface should include `docs/intent/`, and each required folder
should have at least a minimal description of the file(s) or content expected
inside it so the repo structure remains meaningful rather than ceremonial.

## Non-Goals

This spec does not require every optional project surface to exist in every
repo.

This spec does not force `docs/features/`, `docs/stages/`, or `docs/generated/`
for projects that have not adopted those layers.

This spec does not define a full prose template for every file inside every
required folder.

This spec does not validate semantic quality of intent docs beyond a minimal
presence rule unless a later spec explicitly adds content checks.

This spec does not change the current required root document set under `docs/`;
it extends the repo contract around folder presence and file expectations.

## Proposed Required Folder Surface

Projects should have the following required folder surface:

```text
docs/intent/
docs/operating_system/
docs/superpowers/specs/
docs/superpowers/plans/
repo_config/
scripts/
tests/
```

Projects should also retain the already-required root project docs under
`docs/`:

```text
docs/setup.md
docs/configuration.md
docs/usage.md
docs/pipeline.md
docs/architecture.md
```

## Conditional Folder Surface

These folders are valid and often important, but should remain conditional
rather than globally required:

```text
docs/features/
docs/stages/
docs/generated/
configs/
aml/components/
docs/architecture_templates/
.agents/skills/
.codex/
setup/
```

Conditional enforcement rules should follow current adoption or project shape:

- require `docs/features/`, `docs/stages/`, and `docs/generated/` only when the
  project has adopted managed or legacy architecture metadata shapes that use
  them
- require `configs/` only when runtime/workflow configuration is part of the
  project
- require `aml/components/` only when AML components are actually in scope
- do not require `.agents/skills/`, `.codex/`, or `setup/` for every repo by
  default

## Required Folder Semantics

### `docs/intent/`

Required.

Purpose:

- project purpose
- stakeholders and audiences
- success outcomes
- promises the project should preserve
- constraints and non-goals

Minimum expected file rule:

- the folder must exist
- it should contain at least one human-authored intent document

Recommended baseline:

```text
docs/intent/README.md
```

That file should explain the project's purpose and point to any deeper
intent-layer files if the repo later splits intent by audience, promise set, or
initiative.

### `docs/operating_system/`

Required.

Purpose:

- repo governance
- workflow rules
- publication policy
- planning and validation rules
- internal operational memory

Minimum expected file rule:

- the folder must exist
- it should contain the governing repo-method documents the repo already treats
  as canonical

Baseline files should be documented explicitly:

- `docs/operating_system/doc-system-lifecycle.md`
- `docs/operating_system/repo-governance.md`

The validator does not need to require every operating-system file immediately,
but the governance docs should clearly state that these two files are the
minimum governing surfaces.

### `docs/superpowers/specs/`

Required.

Purpose:

- design artifacts for bounded workstreams or changes

Minimum expected file rule:

- the folder must exist even if it is temporarily sparse in a fresh project
- spec creation remains task-driven rather than requiring a fake bootstrap spec

The folder description should explain that files here are created when a change
needs design capture, not to satisfy arbitrary folder occupancy.

### `docs/superpowers/plans/`

Required.

Purpose:

- execution artifacts for bounded workstreams or changes

Minimum expected file rule:

- the folder must exist even if it is temporarily sparse in a fresh project
- plan creation remains task-driven rather than requiring a fake bootstrap plan

The folder description should explain that plans appear when work is being
implemented, not as empty placeholders.

### `repo_config/`

Required.

Purpose:

- repo/system configuration
- publication boundaries
- adapter generation mappings
- adoption mode state

Minimum expected file rule:

- the folder must exist
- it should contain `repo_config/adoption-mode.yaml`

That file is already enforced and should stay the anchor file for the repo's
adoption-state contract.

### `scripts/`

Required.

Purpose:

- repo automation
- validation
- sync/check workflows
- setup helpers

Minimum expected file rule:

- the folder must exist
- it should contain the repo's executable maintenance and validation entrypoints

The governance docs should clarify that `scripts/` is not just a dump bucket;
it owns repo workflow executables such as validation, sync, and setup helpers.

### `tests/`

Required.

Purpose:

- verification surface
- regression tests for repo behavior, validation, and code

Minimum expected file rule:

- the folder must exist
- it should contain the project's executable verification surfaces

The validator should check folder presence only at first, while documentation
should explain that repos are expected to place baseline verification under
`tests/`.

## File Description Gap

If the repo requires a folder, it should also describe the files that belong
inside it.

This spec therefore requires documentation updates wherever that description is
missing or too vague.

At minimum, the docs should explicitly describe:

- what `docs/intent/README.md` or equivalent intent entry file should cover
- which operating-system files are baseline governing files
- that `docs/superpowers/specs/` and `docs/superpowers/plans/` are required
  folders but may be empty until real artifacts exist
- that `repo_config/adoption-mode.yaml` is the required anchor file under
  `repo_config/`
- what kinds of executables belong in `scripts/`
- that `tests/` is the baseline verification surface

## Validator Design

Extend the existing repo-shape validator:

```text
scripts/validate_adoption_shape.py
```

New required-folder behavior should include:

- fail when `docs/intent/` is missing
- fail when `docs/operating_system/` is missing
- fail when `docs/superpowers/specs/` is missing
- fail when `docs/superpowers/plans/` is missing
- fail when `repo_config/` is missing
- fail when `scripts/` is missing
- fail when `tests/` is missing

New required-anchor behavior should include:

- keep failing when `repo_config/adoption-mode.yaml` is missing
- optionally fail when `docs/intent/` exists but contains no markdown files
  after bootstrap, if that rule can be added without creating noisy false
  failures

Validator messages should name the missing folder or anchor file and explain
why the layer exists.

## Hook And CI Design

These folder checks should run through the normal baseline validation path:

- `scripts/sync_architecture_docs.py`
- `scripts/setup_hooks.ps1`
- `scripts/setup_hooks.sh`
- `.github/workflows/repo-hooks.yml`

The goal is one canonical doc-shape validation path, not a second forgotten
command.

## Documentation Updates

### `README.md`

Update bootstrap guidance so the repo structure expectations mention:

- `docs/intent/`
- `docs/operating_system/`
- `docs/superpowers/specs/`
- `docs/superpowers/plans/`
- `repo_config/`
- `scripts/`
- `tests/`

Keep the explanation brief and link deeper governance docs rather than turning
README into a full structural spec.

### `docs/adoption_guide.md`

Add the required folder surface to bootstrap or first-commit guidance.

Clarify which folders are always required and which are conditional on adopted
architecture-doc shape.

### `docs/operating_system/doc-system-lifecycle.md`

Document the required folder surface and add explicit descriptions for the
minimum files or expected file types inside required folders.

This is the main place to close the current "folder exists but file
expectations are unclear" gap.

### `docs/operating_system/repo-governance.md`

Add the required folder surface to repo governance expectations and state that
the normal validation path checks it.

### Folder README Surfaces

Where missing or too vague, add or update folder-local README guidance for:

- `docs/intent/`
- `docs/features/`
- `docs/stages/`

The intent folder especially should gain a clear description of what belongs
there if that description is not already present.

## Acceptance Criteria

The implementation is complete when:

- the repo explicitly defines a required project folder surface
- `docs/intent/` is part of that required surface
- the repo docs describe the minimum expected files or file types for each
  required folder
- the validator fails when a required folder is missing
- the validator continues to fail when `repo_config/adoption-mode.yaml` is
  missing
- the normal hook and CI path runs the required-folder validation
- conditional folders remain documented as conditional rather than globally
  required
- the new structure rules stay aligned with the current source-of-truth model

## Open Questions

- Should `docs/intent/` require a specific anchor file such as
  `docs/intent/README.md`, or is "at least one markdown file" enough?
- Should `docs/superpowers/specs/` and `docs/superpowers/plans/` be required to
  exist even in extremely minimal repos, or should bootstrap scripts create
  them by default so validation never fails on a fresh starter?
- Should `tests/` remain globally required for all projects, or should there be
  a narrow exception for documentation-only repos?
