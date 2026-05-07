---
layer: operating_system
artifact_type: plan
status: proposed
parent_workstream: none
parent_thread: none
parent_spec: none
targets:
  - docs/operating_system/prompt_templates/execute-prompt.md
  - docs/operating_system/prompt_templates/implementation-next-action-gate-prompt.md
  - docs/operating_system/prompt_templates/thread-closeout-readiness-prompt.md
  - docs/operating_system/prompt_templates/workstream-closeout-readiness-prompt.md
  - docs/operating_system/prompt_templates/roadmap-closeout-readiness-prompt.md
related_features: []
related_stages: []
---

# Related Skills High-Impact Prompts Plan

## Goal

Add a concise `Related Skills` section to high-impact prompts so skill routing
is explicit where it matters most.

## Key Deliverables

- `Related Skills` added to the 5 high-impact prompts only.
- Wording standardized to `skill -> use when`.
- Prompt README updated with selective-use convention.

## Task Breakdown

- task 1:
  - add `## Related Skills` to:
    - `execute-prompt.md`
    - `implementation-next-action-gate-prompt.md`
    - `thread-closeout-readiness-prompt.md`
    - `workstream-closeout-readiness-prompt.md`
    - `roadmap-closeout-readiness-prompt.md`
- task 2:
  - map relevant skills per prompt:
    - `skill-executing-plans`
    - `skill-verification-before-completion`
    - `skill-planning-dispatch` (where rerouting applies)
- task 3:
  - update `prompt_templates/README.md` to document selective use of
    `Related Skills` in high-impact prompts
- task 4:
  - verify coverage and ensure no unrelated prompt edits

## Verification

- `rg -n "## Related Skills" docs/operating_system/prompt_templates`
- manual review of 5 target prompt files

## Completion Criteria

Plan is complete when:

1. all Key Deliverables are satisfied
2. all downstream/child items are terminal
3. every child item is `completed` or `dropped`
