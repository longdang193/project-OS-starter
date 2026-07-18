---
layer: operating_system
artifact_type: spec
status: completed
parent_workstream: none
targets:
  - docs/operating_system/prompt_templates/
  - docs/operating_system/governance/repo-governance.md
  - docs/operating_system/planning/planning-dispatch.md
  - docs/operating_system/adoption/project-adoption-migration-guide.md
  - docs/project_templates/mode-a/README.md
related_features: []
related_stages: []
---

# Prompt Template Pack Spec

## Triage

Layer: operating_system
Feature type: ADD
Summary: Add a small prompt-template pack that users can copy to guide agents through the repo’s intended lifecycle from intent to spec, plan, execution, validation, and migration.
Reasoning: The repo now has stronger lifecycle rules, validators, and migration guidance, but users still need to know how to ask for the next step in the right shape. Prompt templates would reduce ambiguity, improve consistency across agents, and make the operating-system process easier to follow without requiring users to reverse-engineer it from skills and docs.
Invariants:

- Prompt templates should reinforce the repo lifecycle rather than invent a parallel workflow.
- Templates should be short, copyable, and task-oriented.
- Templates should point users toward the right source-of-truth layer and expected artifact.
- Templates should support both Mode A and managed-mode migration workflows where relevant.
- Prompt templates should remain guidance, not validator-enforced source files.

Dependencies:

- `docs/operating_system/governance/repo-governance.md`
- `docs/operating_system/planning/planning-dispatch.md`
- `docs/operating_system/adoption/project-adoption-migration-guide.md`
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
  - `docs/operating_system/governance/repo-governance.md`
  - `docs/operating_system/planning/planning-dispatch.md`
  - `docs/operating_system/adoption/project-adoption-migration-guide.md`
- readme: none
- generated: none

Generated refresh required: no
Capability IDs: none
Invariant IDs: none
Spec needed: yes
Plan needed: yes

## Problem

The repo has a stronger operating-system process now:

- `intent -> workstream or operating_system -> change -> spec -> plan -> execution`
- Mode A vs managed-mode guidance
- lifecycle warnings and migration signals
- stronger validator-backed governance

But users still have to know how to ask agents for each step.

That leaves a usability gap:

1. users may skip intent and jump straight to execution
2. users may ask for a plan when they really need a spec
3. migration and drift checks may be phrased vaguely
4. different agents may get the same work framed in inconsistent ways
5. the starter remains powerful but harder to adopt than it needs to be

## Goal

Add a small, copyable prompt-template pack that helps users guide agents through
the intended process with less ambiguity.

## Non-Goals

This spec does not add a new workflow beyond the existing lifecycle.

This spec does not replace skills or operating-system docs.

This spec does not make prompt files required for repo validity.

This spec does not turn prompt templates into executable automation.

## Recommended Design

Create a dedicated folder:

`docs/operating_system/prompt_templates/`

Populate it with a small set of short Markdown prompt files that each answer:

- when to use this prompt
- what the user should fill in
- what output they should expect from the agent

## Proposed Prompt Set

### 1. `intent-prompt.md`

Use when the user needs to describe:

- project purpose
- users/audiences
- success outcomes
- constraints and non-goals

Expected output:

- intent docs or clarified intent direction

### 2. `spec-prompt.md`

Use when the user has a problem/gap/change idea and wants a spec.

Expected output:

- a spec in `docs/superpowers/specs/`

### 3. `plan-prompt.md`

Use when a spec is already approved and the user wants an implementation plan.

Expected output:

- a plan in `docs/superpowers/plans/`

### 4. `execute-prompt.md`

Use when the user wants an existing plan executed.

Expected output:

- code/docs/tests changes plus verification

### 5. `validate-or-drift-prompt.md`

Use when the user wants to know:

- what is missing
- what is drifting
- what has outgrown the current mode

Expected output:

- validator/drift findings and recommended next moves

### 6. `mode-migration-prompt.md`

Use when the user wants to assess or plan:

- `starter_method_only -> managed_architecture_metadata`

Expected output:

- migration assessment, spec, or implementation plan

## Template Style

Each prompt file should be:

- short
- directly copyable
- plain-language
- explicit about expected outputs
- explicit about whether it is for design, plan, execution, or review

Each should avoid:

- giant instructional essays
- hidden repo jargon without explanation
- mixing multiple lifecycle steps in one prompt

## Documentation Updates

Update the operating-system docs so they point to the prompt pack as the
practical user-facing entrypoint for invoking the process.

Especially:

- `repo-governance.md`
- Mode A template guidance

## Acceptance Criteria

1. A prompt-template folder exists under `docs/operating_system/`.
2. The core lifecycle steps each have a prompt template.
3. The templates are short enough to copy into an agent chat directly.
4. The templates point to expected outputs such as intent docs, specs, plans, or validation findings.
5. Operating-system docs link to the prompt pack as a practical entrypoint.

## Recommendation

Implement this as a small documentation pack first.

That would make `project-OS-starter` easier to use without changing validator
behavior, and it would reinforce the process we have already been building
rather than introducing yet another system to learn.
