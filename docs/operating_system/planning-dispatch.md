# Planning Dispatch

This document defines the minimum planning gate for non-trivial changes.

## Purpose

Before writing a spec or plan, identify:

- what kind of change this is
- which feature or operating-system area owns it
- whether stages are affected
- which docs must move with it

When a task touches a feature folder, read the minimum truthful set instead of
loading every file by default:

- `feature.source.yaml` first
- the generated `<feature_id>.yaml` only when the assembled contract view is needed
- `lineage.generated.yaml` only for ownership, evidence, drift, or traceability work
- `history.md` only for narrative context

Use the smallest truthful reading set for any affected feature folder:

- `feature.source.yaml` first
- generated `<feature_id>.yaml` only if the assembled current contract is needed
- `lineage.generated.yaml` only for ownership/evidence/drift work
- `history.md` only for narrative context
- do not load an entire feature folder by default

## Triage Block

Use this block before specs or implementation plans:

```text
Feature type: ADD | MODIFY | REPLACE
Summary: <1 sentence>
Reasoning: <why this classification>
Invariants:
  - <must hold true>
Dependencies:
  - <if known>
Affected stages:
  - <stage_id> | none
Affected features:
  - <feature_id> | none
Primary lens: stage | feature | mixed | cross-cutting
Affected docs:
  feature_source: `docs/features/<feature_id>/feature.source.yaml` | none
  feature_yaml: `docs/features/<feature_id>/<feature_id>.yaml` | none
  feature_lineage: `docs/features/<feature_id>/lineage.generated.yaml` | none
  feature_history: `docs/features/<feature_id>/history.md` | none
  stage_source: `docs/stages/<stage_id>.source.yaml` | none
  stage_contract: `docs/stages/<stage_id>.yaml` | none
  feature_docs:
    - `docs/features/<feature_id>/<doc>.md`
  cross_cutting_docs:
    - `docs/<doc>.md`
    - `docs/operating_system/<doc>.md`
  readme: `README.md` | none
  generated:
    - `docs/generated/<file>` | none
Generated refresh required: yes | no
Capability IDs:
  - <capability_id> | none
Invariant IDs:
  - <invariant_id> | none
Spec needed: yes | no
Plan needed: yes | no
```

`<feature_id>` is placeholder notation in planning docs. The real generated
contract path uses the concrete feature id as the filename, for example
`docs/features/model-training-pipeline/model-training-pipeline.yaml`.

## Dispatch Rules

- unclear design -> write a spec first
- clear design, non-trivial execution -> write a plan
- approved plan -> implement
- cross-cutting repo workflow changes may use `Affected features: none`

## Operating-System Changes

When the change is about repo structure, publication workflow, agent instructions, or tooling policy:

- primary lens is usually `cross-cutting`
- affected features may be `none`
- the owning docs live under `docs/operating_system/`
- if the change is also stage-aware, still name both `stage_source` and
  `stage_contract` targets rather than only the generated stage path

Generated discovery note:

- use `docs/generated/architecture_dag.yaml` and
  `docs/generated/capability_lineage.yaml` when a change affects generated
  architecture metadata indexes
- use `docs/features/<feature_id>/lineage.generated.yaml` as the detailed
  generated evidence surface for opted-in feature changes
- record `generated: none` and `Generated refresh required: no` for unrelated
  work instead of inventing placeholder files

## Metadata-Aware Planning

When a change affects an opted-in feature, record the stable IDs that will move
with the change:

- feature ID in `affected.features`
- capability IDs in specs/plans and code `@capability` markers
- invariant IDs in specs/plans when an invariant is changed or tested
- test proof IDs with `@proves <capability_id>`
- generated refresh requirements for feature YAML, feature-local lineage, and
  DAG outputs
- human history updates only when narrative context changes; do not add
  generated timeline blocks to `history.md`

Use `tools\docs\generate_architecture_metadata.py --validate-only` before
implementation if metadata shape is uncertain, and `--check` before completion
when metadata source files changed.

Prefer the canonical repo workflow when doing the full architecture sync/check pass:

```powershell
.\.venv\Scripts\python.exe scripts/sync_architecture_docs.py
.\.venv\Scripts\python.exe scripts/sync_architecture_docs.py --check
```

If a narrower metadata command is used for a bounded purpose, document that it
is subordinate to the canonical sync/check workflow rather than a separate
default path.

If a narrower metadata command is used for a bounded reason, explain that it is
subordinate to the canonical architecture sync/check workflow rather than a
separate default path.
## Hygiene And Drift Changes

When the change is a bounded cleanup or drift-audit pass rather than a managed
product feature:

- `Affected features: none` is valid
- `Primary lens` may remain `cross-cutting`
- still name the exact docs and rules that own the cleanup
- do not force a fake feature contract just to satisfy the planning format
