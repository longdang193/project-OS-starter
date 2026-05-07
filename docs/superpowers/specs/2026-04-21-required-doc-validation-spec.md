---
layer: operating_system
artifact_type: spec
status: proposed
parent_workstream: none
targets:
  - docs/setup.md
  - docs/configuration.md
  - docs/usage.md
  - docs/pipeline.md
  - docs/architecture.md
  - docs/adoption_guide.md
  - docs/operating_system/skill-doc-system-lifecycle.md
  - docs/operating_system/repo-governance.md
  - scripts/validate_adoption_shape.py
  - scripts/sync_architecture_docs.py
  - tests/test_validate_adoption_shape.py
related_features: []
related_stages: []
---

# Required Doc Validation Spec

## Triage

Layer: operating_system
Feature type: ADD
Summary: Add light validation for the required root project docs so the repo checks more than file presence.
Reasoning: This is repo-method validation and documentation governance. It does not alter product runtime behavior or feature contracts.
Invariants:

- The required root docs should remain human-authored guidance, not generated schema cargo.
- Validation should distinguish "required to exist" from "required to participate in architecture linkage."
- The repo should not require frontmatter on every required doc by default.
- Validation should reject empty or placeholder-only required docs that technically exist but do not help a real project.
- Required docs should remain cross-cutting project surfaces, not replacements for feature-local, stage-local, intent, or operating-system truth.

Dependencies:

- `docs/superpowers/specs/2026-04-21-project-doc-surface-spec.md`
- `docs/superpowers/specs/2026-04-21-required-project-folder-surface-spec.md`
- `docs/operating_system/skill-doc-system-lifecycle.md`
- `docs/operating_system/repo-governance.md`
- `scripts/validate_adoption_shape.py`
- `tools/docs/generate_architecture_metadata.py`

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
  - `docs/adoption_guide.md`
  - `docs/operating_system/skill-doc-system-lifecycle.md`
  - `docs/operating_system/repo-governance.md`
- readme: none
- generated: none

Generated refresh required: no
Capability IDs: none
Invariant IDs: none
Spec needed: yes
Plan needed: yes

## Problem

The repo now enforces that the required root project docs exist:

- `docs/setup.md`
- `docs/configuration.md`
- `docs/usage.md`
- `docs/pipeline.md`
- `docs/architecture.md`

However, current validation stops at presence.

That leaves several gaps:

- a one-line placeholder can pass forever
- required docs are not checked for even minimal semantic structure
- the repo does not define whether these docs need frontmatter or not
- contributors can confuse "this doc is required" with "this doc must be wired
  into architecture linkage metadata"

As a result, the required-doc rule protects structure but not usefulness.

## Goal

Add light validation for the required root docs so they are not merely present,
but minimally usable.

The validation should:

- keep the required docs human-friendly
- avoid forcing frontmatter on every required doc
- enforce a small amount of semantic coverage
- catch obvious placeholders or empty stubs

## Non-Goals

This spec does not require all required docs to carry `doc_id`, `doc_type`, or
`explains.*` frontmatter.

This spec does not make required docs participate in architecture linkage by
default.

This spec does not impose a full template or identical heading structure across
all projects.

This spec does not validate prose quality, completeness, or style beyond a
minimal semantic floor.

This spec does not change the current rules for Markdown frontmatter when a doc
already chooses to use architecture metadata.

## Current State

Today the system behaves like this:

- `scripts/validate_adoption_shape.py`
  - checks required-doc presence only
- `tools/docs/generate_architecture_metadata.py`
  - validates frontmatter only when a markdown doc actually contains it
  - checks `doc_id`, `explains.*`, and duplicate `doc_id` when present

So the repo currently has:

- presence validation: yes
- optional frontmatter validation when present: yes
- required metadata contract for required docs: no
- required semantic-content validation for required docs: no

## Proposed Validation Model

Use a two-tier model.

### Tier 1: Presence And Basic Structure

Required root docs must:

- exist at the required paths
- contain a first-level heading
- contain enough non-heading prose or bullets to be more than a stub

This should be enforced in `scripts/validate_adoption_shape.py`.

### Tier 2: Lightweight Semantic Coverage

Each required doc should also mention the core subject it exists to cover.

This validation should stay simple and heuristic-based rather than trying to
grade writing quality.

For example:

### `docs/setup.md`

Should include at least one of these concepts:

- dependencies
- tool versions
- install or provisioning steps
- prerequisites

### `docs/configuration.md`

Should include at least one of these concepts:

- environment variables
- config files
- profiles
- defaults versus overrides
- configuration ownership

### `docs/usage.md`

Should include at least one of these concepts:

- commands
- entrypoints
- run flow
- operator or developer workflow

### `docs/pipeline.md`

Should include at least one of these concepts:

- stages
- workflow
- steps
- handoffs
- processing flow

### `docs/architecture.md`

Should include at least one of these concepts:

- components
- boundaries
- integrations
- information flow
- control flow

The validator should not require exact wording. It should use a small approved
keyword set or similarly light heuristic for each file.

## Placeholder Rejection Rule

The validator should fail when a required doc is clearly still a placeholder.

Examples of content that should fail:

- a heading only with no supporting content
- one sentence that only says "use this doc for X" without project-specific or
  actionable detail
- obvious placeholder markers such as `TODO`, `TBD`, `placeholder`, or
  `fill this in later` when they make up the majority of the doc

The validator should be careful not to punish short but real docs. The target
is empty scaffolding, not concise writing.

## Frontmatter Policy

Required root docs should **not** require frontmatter by default.

Reasoning:

- these are baseline human guidance docs
- not every required doc needs to explain a feature, capability, stage, config,
  or component in the architecture-linkage sense
- forcing frontmatter everywhere would create ceremony without clear value

However, when a required doc does include frontmatter, existing frontmatter
rules should still apply:

- `doc_id` must be valid
- `explains.*` keys must be valid
- duplicate `doc_id` values must fail

## Where Validation Lives

Primary enforcement should stay in:

```text
scripts/validate_adoption_shape.py
```

The normal check path should continue to run through:

- `scripts/sync_architecture_docs.py`
- local hook setup scripts
- `.github/workflows/repo-hooks.yml`

Frontmatter-specific validation when frontmatter is present should continue to
live in `tools/docs/generate_architecture_metadata.py`.

## Validator Design

Add a dedicated required-doc validation block in
`scripts/validate_adoption_shape.py`.

For each required doc:

- verify the file exists
- verify it starts with or contains a Markdown H1
- verify it contains a minimum amount of substantive text
- verify it satisfies its lightweight semantic coverage rule
- fail on obvious placeholder-only content

Suggested implementation style:

- keep the heuristics transparent and local
- store per-doc keyword groups in one small mapping
- keep error messages specific to the file and missing subject

Examples of good failure messages:

- `docs/setup.md: required setup doc is still placeholder-only`
- `docs/configuration.md: required configuration doc does not mention config surfaces, env vars, profiles, or overrides`
- `docs/architecture.md: required architecture doc is missing component or flow coverage`

## Documentation Updates

Update the governance docs so the validation model is visible:

### `docs/operating_system/skill-doc-system-lifecycle.md`

Clarify that required root docs are validated for:

- presence
- minimal structure
- light semantic coverage

State explicitly that frontmatter is optional for required root docs unless the
doc participates in architecture linkage.

### `docs/operating_system/repo-governance.md`

Add the same rule summary to repo governance expectations so contributors know
what the validator is checking.

### `docs/adoption_guide.md`

Mention that required docs should be replaced with real project guidance before
the first project commit, not left as starter stubs.

## Acceptance Criteria

The implementation is complete when:

- required root docs are still enforced by path
- the validator fails when a required doc is heading-only or obvious placeholder text
- the validator fails when a required doc lacks its lightweight semantic subject coverage
- short but real docs can still pass
- required root docs do not need frontmatter by default
- docs with frontmatter still follow the existing frontmatter validation rules
- the normal sync/check path runs the new validation
- governance docs explain the new behavior

## Open Questions

- Should the semantic checks use plain keyword lists, heading expectations, or a
  small hybrid of both?
- Should optional docs like `docs/testing.md` later gain the same style of
  validation once they exist?
- Should there be a "starter grace mode" for untouched scaffolds, or should the
  validator immediately require real content once the required-doc rule exists?
