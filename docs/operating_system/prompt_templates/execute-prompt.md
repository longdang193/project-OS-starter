# Execute Prompt

## Use When

an implementation plan exists and execution should run task-by-task

## Prerequisites

### Required

- plan path exists

### Optional

- latest readiness assessment

## Next Prompts

- implementation-next-action-gate-prompt.md
- thread-closeout-readiness-prompt.md

## Not For

planning from scratch
Use this when an implementation plan already exists and you want the agent to
carry it out.

If you are still deciding which roadmap thread the work belongs to, use
`roadmap-to-workstream-prompt.md` or `workstream-alignment-review-prompt.md`
before this prompt.

```text
Execute this implementation plan in this session.

Plan:
- path:
- roadmap thread this work follows (use a valid ID from `docs/intent/workstreams/`, or `none` if operating_system work):

Please:
1. review the plan critically before starting
2. confirm the execution still matches the roadmap thread or the operating-system justification
3. implement it task by task
4. keep source-of-truth docs in sync as changes land
5. determine each next action using `implementation-next-action-gate-prompt.md`; do not invent unrelated next steps
6. run the relevant verification commands
7. if this execution closes a plan/workstream, run the closeout gate checks:
   - `python scripts/validate_planning_lifecycle.py --strict`
   - `python scripts/validate_checkpoint_packs.py`
   - `python scripts/validate_repo_contracts.py --fast`
8. summarize what changed and what still needs follow-up
```

Expected output:
- implemented changes plus verification results
