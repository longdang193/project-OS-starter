# Prompt Ladder Spec (Non-Standalone Prompt System)

## 1) Goal

Define a linked prompt ladder so prompts are executed in correct order, with explicit prerequisites and handoff rules, instead of being used as isolated standalone prompts.

## 2) Key Deliverables

- Canonical ladder model for planning -> execution -> closeout.
- Standard prompt metadata contract (`Use When`, `Prerequisites`, `Next Prompts`, `Not For`).
- Ordered related-prompt blocks added to all lifecycle-critical prompts.
- Validation rule to detect missing/invalid ladder links.

## 3) Scope

In scope:

- Prompt files under `docs/operating_system/prompt_templates/`.
- Prompt-level routing/ordering metadata.
- Ladder documentation in prompt README.

Out of scope:

- Changing business/project content in specs/plans.
- Replacing lifecycle validators with prompt logic.

## 4) Problem Statement

Current prompts are partially correct but can be invoked out of order. This causes:

- drift in execution sequencing,
- missing prerequisite checks,
- incorrect closeout decisions,
- duplicated prompt intent across files.

## 5) Design Principles

- Prompts are nodes in a ladder, not standalone tools.
- Every node must declare entry conditions and handoff path.
- Minimal management overhead: concise metadata, reusable structure.
- Deterministic routing over free-form prompt choice.

## 6) Canonical Ladder

Base ladder:

1. [intent-prompt.md](../../operating_system/prompt_templates/intent-prompt.md)
2. [master-workstream-roadmap-build-prompt.md](../../operating_system/prompt_templates/master-workstream-roadmap-build-prompt.md)
3. [registered-workstream-set-build-prompt.md](../../operating_system/prompt_templates/registered-workstream-set-build-prompt.md)
4. [bounded-change-thread-build-prompt.md](../../operating_system/prompt_templates/bounded-change-thread-build-prompt.md)
5. [thread-set-to-spec-set-prompt.md](../../operating_system/prompt_templates/thread-set-to-spec-set-prompt.md) (if multi-thread/spec set)
6. [spec-set-to-spec-authoring-map-prompt.md](../../operating_system/prompt_templates/spec-set-to-spec-authoring-map-prompt.md) (if needed)
7. [spec-prompt.md](../../operating_system/prompt_templates/spec-prompt.md)
8. [spec-set-execution-map-prompt.md](../../operating_system/prompt_templates/spec-set-execution-map-prompt.md) (if multi-spec execution ordering needed)
9. [plan-prompt.md](../../operating_system/prompt_templates/plan-prompt.md)
10. [execute-prompt.md](../../operating_system/prompt_templates/execute-prompt.md)
11. [implementation-next-action-gate-prompt.md](../../operating_system/prompt_templates/implementation-next-action-gate-prompt.md) (iterative loop)
12. [thread-closeout-readiness-prompt.md](../../operating_system/prompt_templates/thread-closeout-readiness-prompt.md)
13. [workstream-closeout-readiness-prompt.md](../../operating_system/prompt_templates/workstream-closeout-readiness-prompt.md)
14. [roadmap-closeout-readiness-prompt.md](../../operating_system/prompt_templates/roadmap-closeout-readiness-prompt.md)

Conditional insertion:

- [downstream-reconciliation-after-roadmap-format-change.md](../../operating_system/prompt_templates/downstream-reconciliation-after-roadmap-format-change.md) when roadmap format changes.

## 7) Prompt Metadata Contract (Required Sections)

Each ladder prompt must include:

- `Use When`
- `Prerequisites`
- `Required`
- `Optional`
- `Next Prompts`
- `Not For`

Optional:

- `Related Prompts`
- `Validation Hooks`

## 8) Next-Action Gate Position

[implementation-next-action-gate-prompt.md](../../operating_system/prompt_templates/implementation-next-action-gate-prompt.md) is not an entry prompt.
It is an execution-loop gate used after partial execution to select one bounded next action from existing artifacts only.

## 9) Prerequisite Semantics

- Required prerequisites must be satisfied before running prompt.
- If missing, prompt must return "minimal prerequisite action" instead of proceeding.
- If closure-ready, prompt may return `close now` as selected next action.

## 10) Validation Requirements

Add/extend validator to check:

- required sections exist in each ladder prompt,
- `Next Prompts` targets exist,
- no dead-end prompt unless marked terminal,
- no cycle except allowed iterative loop at next-action gate,
- closeout prompts include deliverable-satisfaction checks.

## 11) Reporting Format

Prompt-ladder validation report:

- missing sections
- broken next-prompt links
- invalid ordering references
- prompts missing prerequisite definitions
- terminal/loop compliance

## 12) Rollout Plan

1. Define ladder map in [prompt_templates/README.md](../../operating_system/prompt_templates/README.md).
2. Patch critical prompts with required sections.
3. Add validator checks for ladder contract.
4. Run validator in CI/local hooks.
5. Fix drift findings and lock baseline.

## 13) Completion Criteria

Spec is complete when:

1. All ladder prompts implement required section contract.
2. README contains canonical ordered ladder.
3. Validator enforces ladder integrity.
4. Closeout and next-action prompts reflect current lifecycle rules.
5. Validation passes with no blocking ladder drift.
