---
layer: operating_system
artifact_type: spec
status: completed
parent_workstream: none
targets:
  - scripts/validate_adoption_shape.py
  - scripts/validator_policy.py
  - docs/operating_system/repo-governance.md
  - docs/operating_system/doc-system-lifecycle.md
  - docs/operating_system/project-adoption-migration-guide.md
  - docs/project_templates/mode-a/README.md
  - tests/test_validate_adoption_shape.py
related_features: []
related_stages: []
---

# Mode A Missing-Surface Discovery Spec

## Triage

Layer: operating_system
Feature type: CHANGE
Summary: Add warning-level discovery rules for `starter_method_only` so the repo can detect likely missing doc surfaces after a project grows beyond the initial scratch phase.
Reasoning: Mode A is intentionally lighter than managed architecture metadata, but today it mostly blocks forbidden managed surfaces rather than helping a growing repo notice when lightweight product documentation anchors are missing.
Invariants:

- `starter_method_only` remains lighter than `managed_architecture_metadata`.
- Managed feature/stage metadata is still optional in Mode A.
- Canonical truth continues to flow downward from upstream owning layers.
- Mode A discovery should guide, not silently promote repos into managed mode.
- Objective missing-surface signals should be warnings first, not hard errors.

Dependencies:

- `scripts/validate_adoption_shape.py`
- `scripts/validator_policy.py`
- `docs/operating_system/repo-governance.md`
- `docs/operating_system/doc-system-lifecycle.md`
- `docs/operating_system/project-adoption-migration-guide.md`
- `docs/project_templates/mode-a/README.md`

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

Mode A currently answers the question:

- "Are you using managed metadata before opting in?"

But it does not answer the question:

- "Has this repo grown enough that lightweight product documentation anchors are now missing?"

That leaves a practical blind spot for scratch-built repos:

1. the repo can remain validator-green while lacking any product feature home
2. growth in code, workflows, or interfaces is not reflected back into docs
3. missing documentation is discovered manually rather than through the starter
4. the only strong enforcement arrives after a repo opts into managed metadata

That is too late for the "build from scratch, then gradually harden" path.

## Goal

Teach Mode A to discover likely missing documentation surfaces once a repo has
clear signals of real product/runtime structure, without forcing full managed
feature or stage metadata.

## Non-Goals

This spec does not make Mode A equivalent to managed mode.

This spec does not require `docs/features/<feature_id>/feature.source.yaml` in
`starter_method_only`.

This spec does not force generated contracts, lineage files, or stage contracts
into Mode A.

This spec does not attempt perfect semantic feature inference from code.

This spec does not turn heuristic discovery warnings into immediate hard
failures.

## Recommended Design

Add a new warning-only validation pass inside
`scripts/validate_adoption_shape.py` for `starter_method_only`.

The pass should look for objective signs that a repo has meaningful product
surface and then warn when corresponding lightweight doc anchors are missing.

## Discovery Model

### 1. Required lightweight anchors once the repo is clearly non-trivial

When a repo has evidence of real runtime/product structure, Mode A should warn
if these prose anchors are missing:

- `docs/features/README.md`
- `docs/api.md` when the repo exposes API/server surfaces

The warning should say that these are Mode A prose anchors, not managed
metadata obligations.

`docs/pipeline.md` is already enforced separately as a required root doc, so
the discovery layer does not need to duplicate that rule.

### 2. Use heuristic evidence, not wishful inference

Start with simple evidence classes already available from the file tree:

- `src/` exists with more than a trivial number of Python/TypeScript files
- multiple runtime scripts exist under `scripts/`
- server/API entrypoints exist
- workflow/pipeline orchestration files exist
- tests exist that imply multiple runtime flows

The validator should not attempt feature-name inference in Phase 1.

Instead it should answer:

- "This repo appears to have meaningful product/runtime surface."
- "You are missing the lightweight doc anchor that should help humans find it."

### 3. Warning-only severity in Mode A

These findings should be `WARN`, not `ERROR`, because:

- heuristics are not perfect
- the repo may be intentionally early-stage
- the goal is discovery and guidance, not premature migration pressure

### 4. Clear separation from managed mode

The messages must not tell the user to create managed artifacts unless they are
actually choosing Mode B.

Good messages:

- add `docs/features/README.md` as the prose home for product features
- add `docs/pipeline.md` to explain the workflow at a human level
- add `docs/api.md` to document the external interface

Bad messages:

- create `feature.source.yaml`
- create generated contracts
- switch modes automatically

## Proposed Phase 1 Rules

### Rule A: Missing feature index in a non-trivial repo

Warn when:

- adoption mode is `starter_method_only`
- runtime code or tests indicate a real product surface
- `docs/features/README.md` is missing

Purpose:

- every growing repo should have at least one discoverable home for product
  features, even before managed metadata exists

### Rule B: Missing pipeline doc in a workflow-heavy repo

Warn when:

- orchestration/workflow/pipeline evidence exists
- `docs/pipeline.md` is missing

Purpose:

- preserve reproducibility and newcomer discoverability for multi-step systems

### Rule C: Missing API doc in an interface-heavy repo

Warn when:

- API/server/endpoint evidence exists
- `docs/api.md` is missing

Purpose:

- prevent hidden external interface drift in repos that already expose an API

## Policy Placement

The heuristic thresholds and file-anchor mapping should live in
`scripts/validator_policy.py`, while `scripts/validate_adoption_shape.py`
remains the flow/orchestration layer.

That keeps the "what counts as likely missing surface" policy centralized.

## Docs To Update

Update the Mode A guidance so it says this plainly:

- Mode A does not require managed feature metadata
- Mode A does still try to discover missing lightweight doc anchors as the repo
  grows
- warnings from that discovery layer are migration and documentation debt, not
  schema violations

## Acceptance Criteria

1. A small starter-only repo with only the Mode A template pack stays clean.
2. A non-trivial Mode A repo without `docs/features/README.md` gets a warning.
3. An API-heavy Mode A repo without `docs/api.md` gets a warning.
4. Managed mode behavior remains unchanged.
5. No new managed-mode files become required in `starter_method_only`.

## Recommendation

Implement this as a small, warning-only Phase 1 in `validate_adoption_shape.py`.

That gives scratch-built repos a way to notice missing documentation surfaces
early, without collapsing Mode A into managed metadata before they are ready.
