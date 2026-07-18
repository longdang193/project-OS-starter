---
layer: operating_system
artifact_type: spec
status: completed
parent_workstream: none
targets:
  - docs/intent/master-workstream-roadmap.md
  - docs/intent/workstreams/
  - scripts/validate_adoption_shape.py
  - docs/operating_system/planning/planning-dispatch.md
  - docs/operating_system/governance/repo-governance.md
  - docs/operating_system/prompt_templates/
  - tests/test_validate_adoption_shape.py
related_features: []
related_stages: []
---

# Workstream Registry Surface Spec

## Triage

Layer: operating_system
Feature type: ADD
Summary: Add a real workstream registry surface under `docs/intent/` so named `parent_workstream` values can be validated against an explicit source of truth.
Reasoning: The repo now validates that `parent_workstream` exists and is intentional, but it still cannot verify whether a named workstream actually exists. A lightweight registry surface would make roadmap alignment stronger without forcing the master roadmap itself to carry every workstream detail inline.
Invariants:

- `docs/intent/master-workstream-roadmap.md` remains the high-level top-down bridge.
- `docs/intent/workstreams/` becomes the canonical registry for named workstreams when they exist.
- `parent_workstream: none` remains valid for true intent and operating-system artifacts.
- Validator enforcement should only check against the registry once the registry surface exists.
- The registry should stay small and stable, not turn into a changelog.

Dependencies:

- `docs/intent/master-workstream-roadmap.md`
- `scripts/validate_adoption_shape.py`
- `docs/operating_system/planning/planning-dispatch.md`
- `docs/operating_system/governance/repo-governance.md`
- `docs/operating_system/prompt_templates/`
- `tests/test_validate_adoption_shape.py`

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
  - `docs/operating_system/planning/planning-dispatch.md`
  - `docs/operating_system/governance/repo-governance.md`
  - `docs/operating_system/prompt_templates/`
- readme: none
- generated: none

Generated refresh required: no
Capability IDs: none
Invariant IDs: none
Spec needed: yes
Plan needed: yes

## Problem

The current repo is in an in-between state:

- `parent_workstream` is now validator-checked
- but named workstreams are not validated against a real registry

That leaves one remaining weakness:

- a plan/spec can name a plausible-looking workstream ID
- the validator cannot tell whether that workstream is real, current, or typoed

So the current rule is useful, but not fully anchored.

## Goal

Add a real, lightweight workstream registry surface so named workstreams can be
looked up and validated.

## Non-Goals

This spec does not require every repo to create many workstream docs
immediately.

This spec does not turn the master roadmap into a detailed registry itself.

This spec does not require operating-system artifacts to map to a product
workstream.

This spec does not add workflow status tracking beyond what a stable registry
needs.

## Recommended Design

Create:

`docs/intent/workstreams/`

with one Markdown file per real named workstream, for example:

`docs/intent/workstreams/<workstream-id>.md`

The master roadmap remains the overview.
The new folder becomes the explicit registry.

## Registry Shape

Each workstream file should stay small and source-like.

Suggested frontmatter:

```yaml
---
workstream_id: <id>
status: active | proposed | paused | completed
parent_intent: master-workstream-roadmap
---
```

Suggested body:

- what this workstream exists to achieve
- what kinds of specs/plans belong under it
- what does not belong under it
- success signals

## Validator Upgrade

Once this registry exists, `validate_adoption_shape.py` should upgrade the
`parent_workstream` rule:

- `none` stays valid for `intent` and `operating_system`
- named workstreams for `change` / `workstream` artifacts must exist in
  `docs/intent/workstreams/`

This is the moment where validation can become source-backed instead of
heuristic.

## Documentation Updates

Update:

- `repo-governance.md`
- prompt templates

so they say:

- the master roadmap is the overview
- `docs/intent/workstreams/` is the registry for named workstreams
- `parent_workstream` should resolve to a real registry entry when not `none`

## Acceptance Criteria

1. A workstream registry surface exists under `docs/intent/workstreams/`.
2. Named workstream docs have a small stable structure.
3. The validator can verify that named `parent_workstream` values resolve to a real registry entry.
4. `parent_workstream: none` remains valid for `intent` and `operating_system`.
5. Guidance and prompts point users to the registry as the place to discover valid workstream IDs.

## Recommendation

Implement this as the next follow-up after the current `parent_workstream`
validator pass.

That would complete the loop:

- master roadmap as overview
- workstream docs as registry
- specs/plans as downstream bounded artifacts
- validator checks against a real source of truth
