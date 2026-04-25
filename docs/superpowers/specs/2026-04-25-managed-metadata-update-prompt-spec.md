---
layer: operating_system
artifact_type: spec
status: completed
parent_workstream: none
targets:
  - docs/operating_system/prompt_templates/
  - docs/operating_system/planning-dispatch.md
  - docs/operating_system/repo-governance.md
  - docs/operating_system/doc-system-lifecycle.md
related_features: []
related_stages: []
---

# Managed Metadata Update Prompt Spec

## Triage

Layer: operating_system
Feature type: ADD
Summary: Add a dedicated prompt template for updating already-managed architecture metadata surfaces and their linked files.
Reasoning: The current prompt pack has a migration prompt for moving into `managed_architecture_metadata` and a validation/drift prompt for discovering problems, but it does not have a purpose-built prompt for the common case where a repo is already managed and needs its feature, stage, root-doc, and generated metadata surfaces updated or repaired in place.
Invariants:

- The new prompt should be distinct from migration; "already managed, now update/fix" is a different job.
- The new prompt should reinforce canonical source-of-truth flow from human-owned sources to generated outputs.
- The prompt should name validator/sync expectations without pretending generated files are hand-edited sources.
- The prompt should support both targeted updates and drift-remediation updates.
- The prompt should remain short and copyable.

Dependencies:

- `docs/operating_system/prompt_templates/`
- `docs/operating_system/planning-dispatch.md`
- `docs/operating_system/repo-governance.md`
- `docs/operating_system/doc-system-lifecycle.md`

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
  - `docs/operating_system/prompt_templates/`
  - `docs/operating_system/planning-dispatch.md`
  - `docs/operating_system/repo-governance.md`
  - `docs/operating_system/doc-system-lifecycle.md`
- readme: none
- generated: none

Generated refresh required: no
Capability IDs: none
Invariant IDs: none
Spec needed: yes
Plan needed: yes

## Problem

The current prompt pack covers nearby jobs, but not the actual managed-update
workflow:

- `validate-or-drift-prompt.md` helps find gaps and drift
- `mode-migration-prompt.md` helps move from `starter_method_only` into
  `managed_architecture_metadata`
- `spec-prompt.md`, `plan-prompt.md`, and `execute-prompt.md` help once the
  bounded work is already framed

What is missing is the practical middle prompt for repos that are already in
managed mode and need to:

- update `feature.source.yaml`
- update stage source files
- fix root-doc metadata/frontmatter
- refresh generated feature/stage contracts
- refresh lineage/generated discovery
- rerun the canonical validator/sync path

Without that dedicated prompt, users have to improvise across migration,
validation, and generic execution prompts.

## Goal

Add a dedicated prompt template for:

`managed repo -> update/fix human-owned sources -> refresh generated outputs -> rerun canonical checks`

The prompt should help users ask for managed metadata updates directly, without
confusing that work with adoption-mode migration.

## Non-Goals

This spec does not add new validator rules by itself.

This spec does not change managed metadata schemas.

This spec does not replace migration prompts for Mode A repos.

This spec does not make prompt templates validator-enforced.

## Recommended Design

Add a new prompt template:

`docs/operating_system/prompt_templates/managed-metadata-update-prompt.md`

### Suggested Prompt Shape

The prompt should collect:

- repo context
- whether the repo is already `managed_architecture_metadata`
- which managed surfaces are in scope
- whether the request is:
  - feature/stage/source update
  - drift remediation
  - metadata normalization
  - generated refresh
- roadmap/workstream context when applicable

### Suggested Prompt Responsibilities

The prompt should ask the agent to:

1. confirm the repo is already in managed mode, or say if a migration prompt is
   the better entrypoint
2. identify the human-owned source surfaces that should change first
3. identify the generated outputs that should be refreshed later, not hand-edited
4. run the canonical validator/sync flow or explain the needed checks
5. report what changed, what was regenerated, and what drift remains

## Suggested Expected Output

The prompt should aim for outputs like:

- updated managed source files
- refreshed generated metadata outputs
- validator/sync results
- a spec or implementation plan when the work is too large to execute safely in
  one pass

## Proposed README / Guidance Updates

The prompt-pack README should mention this new prompt as the right choice when:

- the repo is already managed
- the user wants to update or fix managed metadata surfaces
- the task is not a migration from Mode A

Planning/governance docs should lightly distinguish:

- migration into managed mode
- validation/drift discovery
- managed-mode update/fix execution

## Acceptance Criteria

- A dedicated managed-metadata update prompt exists in the prompt pack.
- The prompt clearly distinguishes update/fix work from migration work.
- The prompt reinforces source-first updates and generated refresh later.
- The prompt-pack README and related operating-system docs point users to the
  new prompt appropriately.

## Risks

If this prompt overlaps too heavily with `validate-or-drift`, users may still
be unsure which one to choose.

If it overlaps too heavily with `mode-migration`, the pack becomes redundant.

If it tells users to edit generated files directly, it would contradict the
repo’s source-of-truth model.

## Recommendation

Add the dedicated prompt. The repo now has enough managed-mode structure that
"update/fix managed metadata in place" deserves its own first-class entrypoint
instead of being improvised through migration or drift prompts.
