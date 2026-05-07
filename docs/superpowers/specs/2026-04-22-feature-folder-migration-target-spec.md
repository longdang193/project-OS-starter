---
layer: operating_system
artifact_type: spec
status: proposed
parent_workstream: none
targets:
  - docs/operating_system/project-adoption-migration-guide.md
  - docs/operating_system/mode-b-example-migration.md
  - docs/operating_system/skill-doc-system-lifecycle.md
  - docs/architecture_templates/
  - scripts/validate_adoption_shape.py
related_features: []
related_stages: []
---

# Feature Folder Migration Target Spec

## Triage

Layer: operating_system
Feature type: CHANGE
Summary: Define a concrete migration target for feature folders so agents know how to move older managed metadata folders onto the current starter-style shape.
Reasoning: Comparing `customer-churn-prediction-azureml/docs/features/churn-data-preparation/` and `JOB-PROJECT/docs/features/inspection_debugging/` shows that agents currently do not have explicit enough migration guidance. The target format is not just about `lineage.generated.yaml`; the whole feature folder contract differs across source, generated contract, lineage, and history surfaces.
Invariants:

- The desired migration target is the newer feature-folder shape used by `customer-churn-prediction-azureml/docs/features/churn-data-preparation/`.
- `feature.source.yaml` stays minimal and human-owned.
- `<feature_id>.yaml` stays generated current-state contract output.
- `lineage.generated.yaml` stays generated evidence-oriented lineage output.
- `history.md` should use the partial-generated history pattern rather than hand-maintained version-changelog style when the starter history model is adopted.

Dependencies:

- `docs/operating_system/project-adoption-migration-guide.md`
- `docs/operating_system/skill-doc-system-lifecycle.md`
- current starter architecture generator and validators

Affected stages:

- none

Affected features:

- all downstream Mode B feature folders migrating from older managed metadata shapes

Primary lens: cross-cutting

Affected docs:

- feature_source: managed `docs/features/*/feature.source.yaml`
- feature_yaml: managed `docs/features/*/<feature_id>.yaml`
- feature_lineage: managed `docs/features/*/lineage.generated.yaml`
- feature_history: managed `docs/features/*/history.md`
- cross_cutting_docs:
  - `docs/operating_system/project-adoption-migration-guide.md`
  - `docs/operating_system/mode-b-example-migration.md`
  - `docs/operating_system/skill-doc-system-lifecycle.md`

Generated refresh required: yes
Capability IDs: none
Invariant IDs: none
Spec needed: yes
Plan needed: yes

## Comparison Summary

The comparison between the two feature folders shows meaningful contract drift.

Desired target:

- `customer-churn-prediction-azureml/docs/features/churn-data-preparation/`

Older shape:

- `JOB-PROJECT/docs/features/inspection_debugging/`

### Feature Source Differences

Desired target source shape is smaller and source-like:

- `feature_id`
- `name`
- `status`
- `type`
- `summary`
- `invariants`
- `domains`
- `depends_on`
- `capabilities`
- `stage_participation`

Older source shape currently includes contract-adjacent or legacy fields such as:

- `owner`
- `primary_stage`
- `stages`
- `refs`
- `keywords`
- capability `name` and `summary` fields instead of the newer evidence-oriented
  `statement` + `state` shape

This means the older repo is storing too much generated or summary-adjacent
material in the human-owned source file.

### Generated Contract Differences

Desired target generated contract:

- carries the generated header
- mirrors the source-owned semantic shape
- adds generated `refs`
- may add freshness metadata such as `revision`, `latest_change_id`,
  `last_updated_at`

Older generated contract still looks close to the source file and continues to
carry legacy fields such as:

- top-level mapping wrapper keyed by feature ID
- `owner`
- `primary_stage`
- `stages`
- `keywords`

That makes the generated contract look like a lightly copied source file rather
than the current starter-style assembled current-state contract.

### Lineage Differences

Desired target lineage shape:

- generated header
- `feature_id`
- `source`
- `invariants`
- `capabilities` as a mapping keyed by capability ID
- `timeline`

Older lineage shape currently uses a summary-style structure with fields such as:

- `generated_contract`
- `naming_policy`
- `capability_shape`
- `capability_ids`
- `capabilities` as a list
- `refs`
- `refs_by_type`

That is a different artifact contract, not just a formatting variation.

### History Differences

Desired target history shape uses the starter partial-generated model:

- `# History`
- generated block between `<!-- GENERATED HISTORY START -->` and
  `<!-- GENERATED HISTORY END -->`
- `## Human Notes` for human-authored additions

Older history shape is a manual changelog/version ledger:

- version-number sections like `2.28.0`
- manual release-log narrative as the primary structure

That older history format can preserve useful content, but it does not match
the starter-style partial-generated history contract.

## Goal

Provide a precise migration target so agents can move older feature folders to
the desired newer starter-style format without guessing.

The guidance should tell the agent:

- what belongs in `feature.source.yaml`
- what must move into generated contract output
- what must move into `lineage.generated.yaml`
- how to treat existing manual changelog history during migration

## Non-Goals

This spec does not require every downstream repo to use the exact same feature
IDs or domain taxonomy.

This spec does not force immediate deletion of meaningful historical content.

This spec does not require a fully automatic converter in the first step.

## Canonical Migration Target

When migrating an older managed feature folder to the desired target, the agent
should produce:

```text
docs/features/<feature_id>/
  feature.source.yaml
  <feature_id>.yaml
  lineage.generated.yaml
  history.md
```

### Target `feature.source.yaml`

The source file should keep only human-owned semantic meaning:

- `feature_id`
- `name`
- `status`
- `type`
- `summary`
- `invariants`
- `domains`
- `depends_on`
- `capabilities`
- `stage_participation`
- `lineage_exceptions` when needed

The migration guide should explicitly say to remove or relocate older
source-level fields such as:

- `owner`
- `primary_stage`
- `stages`
- `refs`
- `keywords`

If a repo still needs some of that information, it should either:

- derive it into generated outputs
- move it into prose docs
- or map it into the current canonical source fields rather than keeping the
  old field names

### Target Capabilities In Source

The desired target should prefer the newer source capability shape used by the
customer repo:

```yaml
capabilities:
  - capability_id: <feature_id>.<capability_slug>
    statement: <human-owned capability statement>
    state: active
```

The guide should stop leaving agents to infer whether `name`/`summary` or
`statement`/`state` is the target shape.

### Target Generated Contract

The generated feature contract should:

- carry the generated header
- preserve the canonical current-state semantic contract
- carry generated refs and freshness fields when applicable
- not serve as a second source file

### Target Lineage

The generated lineage file should use the newer evidence-oriented canonical
shape already formalized by the lineage schema contract:

- generated header
- `feature_id`
- `source`
- `invariants`
- `capabilities` mapping keyed by capability ID
- `timeline`

Agents should be told explicitly that older summary-style lineage outputs are
not acceptable migration endpoints.

### Target History

The migration target for `history.md` should be:

- starter-style partial-generated history
- preserve useful manual notes by moving them under `## Human Notes`
- do not keep version-number changelog sections as the primary contract once
  the starter history model is adopted

## Agent Migration Guidance

The new guidance should give agents a concrete migration checklist:

1. compare the existing feature folder against the canonical starter target
2. minimize `feature.source.yaml` to human-owned semantic fields only
3. normalize capabilities to the target source shape
4. regenerate `<feature_id>.yaml`
5. regenerate `lineage.generated.yaml`
6. convert `history.md` into partial-generated history while preserving useful
   human notes
7. run the canonical sync/check workflow

The docs should explicitly tell the agent not to:

- copy older source fields forward just because they already exist
- treat `lineage.generated.yaml` as a refs summary or contract dump
- keep a version-changelog history format as the final target when the starter
  history model is available

## Validation Follow-Up

The first implementation may keep this as guidance, but the spec should leave
room to later validate:

- allowed source-file fields
- target capability shape in `feature.source.yaml`
- partial-generated history markers

## Acceptance Criteria

The implementation is complete when:

- the migration guide explicitly points to the desired feature-folder target
- the source/generated/history boundaries are described clearly enough for an
  agent to follow without guessing
- the desired target matches the newer customer-style feature folder rather
  than the older JOB-PROJECT-style shape

## Open Questions

- Should `feature.source.yaml` validation later reject extra legacy fields such
  as `owner`, `stages`, `primary_stage`, `refs`, and `keywords`?
- Should we add a dedicated feature-folder migration example that shows a
  before/after transformation from the older JOB-PROJECT-style shape to the
  newer target?
- Should history migration be guidance-only at first, or should the validator
  later require partial-generated history markers for managed features?
