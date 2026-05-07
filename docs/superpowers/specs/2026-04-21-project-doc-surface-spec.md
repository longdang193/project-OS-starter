---
layer: operating_system
artifact_type: spec
status: proposed
parent_workstream: none
targets:
  - README.md
  - docs/
  - docs/adoption_guide.md
  - docs/operating_system/skill-doc-system-lifecycle.md
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

# Project Documentation Surface Spec

## Triage

Layer: operating_system
Feature type: ADD
Summary: Define and enforce the minimum root documentation set a project should carry beside the top-level `README.md`.
Reasoning: This is repo-method governance for project documentation structure, validation, and CI enforcement. It does not create or modify a product feature contract.
Invariants:

- `README.md` remains a synthesized overview, not the deepest source of truth.
- Cross-cutting project docs under `docs/` should explain setup, operation, and architecture without duplicating generated or feature-local truth.
- Required project docs should be machine-checkable so missing foundational docs do not survive into normal repo use.
- Optional docs should be encouraged and named consistently, but absence of optional docs should not fail validation.
- Feature-local and stage-local docs remain deeper sources when the subject is feature-specific or stage-specific.

Dependencies:

- `docs/operating_system/skill-doc-system-lifecycle.md`
- `docs/adoption_guide.md`
- `docs/operating_system/repo-governance.md`
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
  - `docs/setup.md`
  - `docs/configuration.md`
  - `docs/usage.md`
  - `docs/pipeline.md`
  - `docs/architecture.md`
  - `docs/dataset.md`
  - `docs/api.md`
  - `docs/observability.md`
  - `docs/testing.md`
  - `docs/adoption_guide.md`
  - `docs/operating_system/skill-doc-system-lifecycle.md`
  - `docs/operating_system/repo-governance.md`
- readme: `README.md`
- generated: none

Generated refresh required: no
Capability IDs: none
Invariant IDs: none
Spec needed: yes
Plan needed: yes

## Problem

The starter already distinguishes `README.md`, intent docs, operating-system
docs, feature/stage lifecycle docs, and generated discovery. However, it does
not yet define a standard root-level project documentation surface under
`docs/` for the documents most teams need after bootstrap.

That gap creates drift:

- one project may keep everything in `README.md`
- another may create ad hoc names such as `runbook.md`, `how-to-run.md`, or
  `system-design.md`
- another may omit key documents such as setup or configuration guidance until
  reproducibility breaks
- CI and local hooks do not currently fail when the required project docs are
  missing

The repo needs a small, explicit contract for which cross-cutting project docs
should exist beside `README.md`, which of them are required, and where that
contract is checked.

## Goal

Define a standard root-level project documentation set under `docs/` so a
bootstrapped project has a predictable place for setup, configuration, usage,
workflow, and architecture guidance.

The goal is not to force every possible document into existence on day one. The
goal is to make the required project-operability docs explicit and
machine-checkable while leaving richer docs optional.

## Non-Goals

This spec does not define feature-local documentation requirements.

This spec does not replace `docs/intent/` or `docs/operating_system/`.

This spec does not require an API, dataset, observability, or testing document
for projects that do not have those concerns yet.

This spec does not force one canonical prose structure inside each document.
It defines the required document surface and minimum subject coverage.

This spec does not move generated discovery into the human-authored root doc
set.

## Proposed Root Documentation Set

Beside the top-level `README.md`, projects should use these cross-cutting docs
directly under `docs/`.

### Required

```text
docs/setup.md
docs/configuration.md
docs/usage.md
docs/pipeline.md
docs/architecture.md
```

### Optional

```text
docs/dataset.md
docs/api.md
docs/observability.md
docs/testing.md
```

These filenames should be treated as the default names for cross-cutting
project docs. Avoid inventing near-duplicates such as `run-guide.md`,
`system-design.md`, or `how-to-configure.md` unless the project has a strong
reason and explicitly documents the exception.

## Required Document Semantics

### `docs/setup.md`

Required.

Purpose:

- reproducibility steps
- local environment bootstrap
- dependencies and version expectations
- install or provisioning sequence
- any non-obvious preconditions needed before the project can run

This doc answers: "How do I get a working local environment without relying on
tribal knowledge?"

### `docs/configuration.md`

Required.

Purpose:

- configuration surfaces and where they live
- required environment variables, files, secrets references, or profiles
- defaults versus environment-specific overrides
- how config ownership is split between `repo_config/`, `configs/`, runtime
  env vars, and any other config layers

This doc answers: "What knobs exist, where do they live, and why does the
project behave differently across environments?"

### `docs/usage.md`

Required.

Purpose:

- how to use the project after setup succeeds
- common run commands, entrypoints, or operator flows
- typical local development loop
- user/operator-facing invocation patterns

This is not the same as setup. It answers: "Now that the environment exists,
how do I actually run and use the project?"

### `docs/pipeline.md`

Required.

Purpose:

- workflow or processing stages
- sequence of major steps
- handoffs between stages, services, or artifacts
- operational flow for the system

This is the high-level workflow explanation surface, even for projects that are
not literal data pipelines.

### `docs/architecture.md`

Required.

Purpose:

- major components and boundaries
- key dependencies and integration points
- information flow or control flow at system level
- why the system is shaped the way it is

This is the default cross-cutting architecture explanation surface. Feature- or
stage-specific architecture detail should still live deeper when appropriate.

## Optional Document Semantics

### `docs/dataset.md`

Optional.

Use when the project depends materially on datasets, source data, training
data, evaluation corpora, schema expectations, provenance, or data contracts.

### `docs/api.md`

Optional.

Use when the project exposes APIs, RPC tools, CLIs that behave like public
interfaces, service contracts, or important machine-facing endpoints.

### `docs/observability.md`

Optional.

Use when the project has meaningful logs, traces, metrics, alerts, health
signals, dashboards, or production diagnostics that operators need to
understand.

### `docs/testing.md`

Optional.

Use when the project needs a cross-cutting explanation of test strategy, test
layers, commands, fixtures, smoke checks, or release-gating verification beyond
what can live in `README.md` or local test docs.

## Placement Rules

These root docs are cross-cutting project docs under `docs/`, not replacements
for deeper ownership layers.

Rules:

- `README.md` summarizes and links; it should not absorb all of setup,
  configuration, usage, pipeline, and architecture detail.
- `docs/intent/` remains the source for project purpose, outcomes, and
  stakeholders.
- `docs/operating_system/` remains the source for repo method, workflow rules,
  validation policy, and governance.
- `docs/features/<feature_id>/` remains the home for feature-specific
  explanation and history.
- `docs/stages/` remains the home for stage-specific workflow boundaries when
  stage-aware docs are adopted.
- `docs/generated/*` remains generated only.

## Validator Design

Extend the existing validation path so required root docs are checked as part of
repo doc-shape validation.

Primary validator:

```text
scripts/validate_adoption_shape.py
```

New required-doc behavior:

- verify that `docs/setup.md` exists
- verify that `docs/configuration.md` exists
- verify that `docs/usage.md` exists
- verify that `docs/pipeline.md` exists
- verify that `docs/architecture.md` exists

Validator messages should name the missing path and explain the required topic.

Optional docs should not fail validation. At most, they may be documented as a
recommended set in guides.

## Hook And CI Design

The required-doc validator should run through the repo's normal local and CI
validation path instead of becoming a one-off command that people forget.

Update these paths accordingly:

- `scripts/setup_hooks.ps1`
- `scripts/setup_hooks.sh`
- `scripts/sync_architecture_docs.py`
- `.github/workflows/repo-hooks.yml`

The check should be part of the same baseline doc-validation path used before
commit and in CI.

## Documentation Updates

### `README.md`

Update the bootstrap section so it tells projects that `README.md` is not
enough on its own and points to the standard root docs under `docs/`.

### `docs/adoption_guide.md`

Add the expected root doc set to the first-hour or first-commit guidance so new
projects know to create:

- setup
- configuration
- usage
- pipeline
- architecture

Clarify that dataset, API, observability, and testing docs are optional but
recommended when those concerns exist.

### `docs/operating_system/skill-doc-system-lifecycle.md`

Add the standard root-level project doc set to the source-of-truth and
placement guidance for cross-cutting docs under `docs/*.md`.

Clarify that these files are the default human-authored cross-cutting project
docs beneath the top-level `README.md`.

### `docs/operating_system/repo-governance.md`

Add the root project documentation surface to the repo governance expectations
and note that the validation/hook path checks the required set.

## Acceptance Criteria

The implementation is complete when:

- the repo documents a standard root project doc set under `docs/`
- the required set is:
  - `docs/setup.md`
  - `docs/configuration.md`
  - `docs/usage.md`
  - `docs/pipeline.md`
  - `docs/architecture.md`
- the optional set is documented as:
  - `docs/dataset.md`
  - `docs/api.md`
  - `docs/observability.md`
  - `docs/testing.md`
- `README.md`, `docs/adoption_guide.md`,
  `docs/operating_system/skill-doc-system-lifecycle.md`, and
  `docs/operating_system/repo-governance.md` all describe the new contract
- the validator fails when a required root doc is missing
- local hook setup and CI run the required-doc check through the normal
  validation path
- optional docs do not fail validation when absent

## Open Questions

- Should the validator check only file presence, or should it also enforce a
  minimum heading or subject checklist inside each required doc?
- Should projects be allowed to alias one required doc to another filename if
  the alias is linked from `README.md`, or should the default names be strict?
- Should `docs/testing.md` remain optional for every project, or become
  required once the repo has a non-trivial test matrix?
