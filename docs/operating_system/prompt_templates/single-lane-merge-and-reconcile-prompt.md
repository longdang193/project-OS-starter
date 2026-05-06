---
prompt_id: single-lane-merge-and-reconcile-prompt
type: prompt
stage: closeout
owner_layer: change
entry_points:
  - one lane is implementation-complete and needs PR/merge orchestration
  - a single lane merge needs lifecycle/evidence reconciliation before closure
prerequisites:
  - lane verification evidence is available
  - lane branch/worktree context is identified
next_steps:
  - implementation-next-action-gate-prompt.md
  - thread-closeout-readiness-prompt.md
  - workstream-closeout-readiness-prompt.md
skills:
  - verification-before-completion
  - finishing-a-development-branch
  - planning-dispatch
status: active
---
# Single-Lane Merge And Reconcile Prompt

## Use When

you need to merge one lane safely and reconcile lifecycle evidence afterward

## Prerequisites

### Required

- single lane record (id, owner, branch/worktree path, status)
- lane verification evidence

### Optional

- open PR link and review outcomes

## Next Prompts

- implementation-next-action-gate-prompt.md
- thread-closeout-readiness-prompt.md
- workstream-closeout-readiness-prompt.md

## Not For

multi-lane merge sequencing (use multi-worktree merge/reconcile prompt)

```text
Orchestrate PR/merge for one lane and reconcile closure evidence.

Context:
- roadmap/workstream/thread in scope:
- lane record (id, owner, branch/worktree path, status):
- verification evidence:
- open blockers/conflicts:

Please:
1. verify lane is merge-eligible:
   - bounded scope respected
   - verification evidence present
   - no unresolved critical blockers
2. decide merge path:
   - open/update PR
   - merge now
   - hold/defer with reason
3. after merge, run required post-merge verification and report impact
4. reconcile lifecycle/status/evidence:
   - thread/workstream status updates
   - checkpoint/result-pack evidence linkage
   - unresolved risk log
5. if blockers remain, return the minimal prerequisite action needed to unblock
6. return one selected next action and why alternatives are not yet eligible
   - if closure criteria are already satisfied, select `close now` and explain why further actions are not eligible
```

Expected output:
- single-lane merge/reconcile report with one selected next action (or `close now`)

