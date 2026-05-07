---
layer: operating_system
artifact_type: spec
status: completed
parent_workstream: none
targets:
  - docs/operating_system/prompt_templates/README.md
  - docs/operating_system/repo-governance.md
  - docs/operating_system/skill-doc-system-lifecycle.md
  - docs/operating_system/prompt_templates/
related_features: []
related_stages: []
---

# Required Root Doc Update Prompt Spec

## Triage

Layer: operating_system  
Feature type: ADD  
Summary: Add a dedicated prompt for updating the validator-enforced required root docs under `docs/`.  
Reasoning: The repo has a validator-enforced required root-doc surface, but the prompt pack does not yet provide a direct maintenance prompt for keeping those docs in sync with current repo reality.  
Invariants:

- required root docs remain cross-cutting summaries rather than new source-of-truth layers
- the prompt should help update required root docs without duplicating lower-level intent, operating-system, feature, or stage sources
- the prompt should reflect validator expectations for the required root-doc contract
- optional root docs should be handled as optional follow-ons, not silently promoted to required

Dependencies:

- `docs/operating_system/prompt_templates/README.md`
- `docs/operating_system/repo-governance.md`
- `docs/operating_system/skill-doc-system-lifecycle.md`
- required root-doc contract wording in current repo governance

Affected stages:

- none

Affected features:

- none

Primary lens: cross-cutting

Affected docs:
  feature_source: none
  feature_yaml: none
  feature_lineage: none
  feature_history: none
  stage_source: none
  stage_contract: none
  feature_docs:
    - none
  cross_cutting_docs:
    - `docs/operating_system/prompt_templates/README.md`
    - `docs/operating_system/repo-governance.md`
    - `docs/operating_system/skill-doc-system-lifecycle.md`
    - `docs/operating_system/prompt_templates/required-root-doc-update-prompt.md`
  readme: none
  generated:
    - none
Generated refresh required: no
Capability IDs:
  - none
Invariant IDs:
  - none
Spec needed: yes
Plan needed: yes

## Problem

The repo currently enforces a required root-doc surface:

- `docs/setup.md`
- `docs/configuration.md`
- `docs/usage.md`
- `docs/pipeline.md`
- `docs/architecture.md`

Those files are validator-owned contract surfaces, not optional polish.

But the prompt pack still lacks a dedicated prompt for:

- updating those required docs
- checking their scope against current repo reality
- keeping them informative without duplicating lower-level source layers

Without a focused prompt, users and agents will improvise, which increases the
risk of:

- stale root docs
- duplicated content
- weak validator-facing coverage
- root docs drifting away from current repo structure

## Goal

Add a dedicated prompt that helps humans and agents update the required
cross-cutting root docs in a consistent, validator-aware way.

## Non-Goals

This spec does not change which root docs are required.

This spec does not redesign the validator rules for required root docs.

This spec does not turn root docs into replacements for intent, operating
system, feature, stage, or generated discovery surfaces.

## Prompt Scope

The new prompt should support updating:

- required:
  - `docs/setup.md`
  - `docs/configuration.md`
  - `docs/usage.md`
  - `docs/pipeline.md`
  - `docs/architecture.md`
- optional when applicable:
  - `docs/api.md`
  - `docs/testing.md`
  - `docs/observability.md`
  - `docs/dataset.md`

## Required Prompt Behavior

The prompt should tell the agent to:

1. inspect current repo structure and current docs
2. determine which required root docs are stale, thin, or missing expected
   subject coverage
3. update the root docs as cross-cutting summaries
4. avoid copying lower-level source-of-truth content verbatim into them
5. call out optional root docs that are now worth adding, without pretending
   they are required
6. run the validator-facing checks after the doc update

## Root-Doc Positioning Rules

The prompt should reinforce:

- root docs are cross-cutting docs
- root docs summarize and point to source layers
- root docs are not replacements for:
  - `docs/intent/`
  - `docs/operating_system/`
  - feature-local docs
  - stage sources/contracts
  - generated discovery

## Recommended Prompt Inputs

The prompt should ask for:

- repo context or project type
- known areas that changed recently
- which required root docs are suspected stale
- whether optional root docs are expected

## Recommended Prompt Outputs

The prompt should aim to produce:

- updated required root docs
- a short report of which required docs were refreshed
- notes on optional root docs worth adding later
- validator follow-up recommendation

## Related Prompt-Pack Changes

The prompt pack README should include this new prompt as a review/upkeep prompt
for the validator-enforced root-doc surface.

## Related Repo-Control Doc Changes

At minimum, the supporting docs should mention that:

- required root docs have a dedicated update prompt
- the prompt is for cross-cutting summary maintenance
- it should be used when the required root docs have drifted from current repo
  shape

Likely touchpoints:

- `docs/operating_system/prompt_templates/README.md`
- `docs/operating_system/repo-governance.md`
- `docs/operating_system/skill-doc-system-lifecycle.md`

## Acceptance Criteria

- the prompt pack includes a dedicated required-root-doc update prompt
- the prompt clearly distinguishes required vs optional root docs
- the prompt reinforces that root docs are summaries, not new source layers
- the prompt guidance reflects current validator expectations for the required
  root-doc contract
- the prompt README and relevant governance docs point to the new prompt

## Recommendation

Add:

- `docs/operating_system/prompt_templates/required-root-doc-update-prompt.md`

and wire it into the prompt-pack README plus the relevant governance/docs
surfaces so required root-doc maintenance becomes an explicit supported
workflow.
