---
prompt_id: post-patch-regression-scope-prompt
type: prompt
stage: execution
owner_layer: change
entry_points:
  - a patch was applied and regression validation scope must be decided
  - uncertainty exists between targeted tests and broader/full regression
prerequisites:
  - patch diff and affected components are known
  - at least one targeted verification command is available
next_steps:
  - implementation-next-action-gate-prompt.md
  - thread-closeout-readiness-prompt.md
skills:
  - verification-before-completion
  - systematic-debugging
status: active
---
# Post-Patch Regression Scope Prompt

## Use When

you need to choose the correct regression verification scope after a patch

## Prerequisites

### Required

- patch impact surface is identified

### Optional

- historical flaky or high-risk areas

## Next Prompts

- implementation-next-action-gate-prompt.md
- thread-closeout-readiness-prompt.md

## Not For

initial patch design before any code change

```text
Decide the minimum sufficient regression scope after this patch.

Context:
- patch summary:
- affected files/modules/contracts:
- related workflows/specs:
- risk indicators:

Please:
1. classify impact scope: local | adjacent | cross-cutting
2. choose verification scope:
   - targeted only
   - targeted + expanded subset
   - full suite
3. justify choice with risk and dependency impact
4. list exact commands to run now
5. return one selected next action and why alternatives are not yet eligible
   - if closure criteria are already satisfied, select `close now`
```

Expected output:
- regression-scope decision, exact verification commands, and one selected next action

