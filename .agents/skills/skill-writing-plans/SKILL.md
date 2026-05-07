---
name: skill-writing-plans
description: Use when a confirmed design needs a multi-step implementation plan before
  code changes begin.
allowed-tools: []
hooks:
  pre:
  - python scripts/hooks/run_validator.py --fast
  post:
  - python scripts/hooks/run_validator.py --fast
required_reads:
- docs/operating_system/templates/implementation-plan-template.md
- docs/operating_system/templates/task-start-routing-guide.md
- docs/operating_system/repo-governance.md
tags:
- skill
- planning
- implementation-plan
- skill-writing-plans
required_outputs:
- docs/superpowers/plans/YYYY-MM-DD-HH-MM-<topic>-plan.md
---

# Writing Plans

## Role

Create executable implementation plans from approved design context.

## Canonical References

- `docs/operating_system/templates/implementation-plan-template.md`
- `docs/operating_system/templates/task-start-routing-guide.md`
- `docs/operating_system/prompt_templates/implementation-next-action-gate-prompt.md`
- `docs/operating_system/repo-governance.md`

If this file conflicts with canonical templates/governance, follow canonical docs.

## Mandatory Read

Before drafting a plan, read:

- canonical references above, especially:
  - `docs/operating_system/templates/task-start-routing-guide.md`
  - `docs/operating_system/templates/implementation-plan-template.md`

## GitNexus Usage

Use GitNexus when plan quality depends on cross-file dependency awareness.

- Prefer GitNexus for broad impact mapping and shared-module dependency checks.
- For narrowly scoped plans, GitNexus is optional.
- Before high-trust use, check freshness:
  - `.\scripts\get_gitnexus_freshness.ps1`
- If stale, use GitNexus only as advisory and keep the plan source-first.
- If GitNexus conflicts with source/docs/tests, trust source/docs/tests.
- If GitNexus has tooling or query issues, consult the `gitnexus-guide` skill first; if unresolved, continue source-first.

## Preconditions

- triage exists (`skill-planning-dispatch`)
- design context exists (approved detailed spec or approved execution-map context)
- scope is bounded enough for implementation

## Plan Output

Default path:
- `docs/superpowers/plans/YYYY-MM-DD-HH-MM-<topic>-plan.md`

Use the canonical implementation plan template and fill exact paths, tests, and commands.

## Minimal Workflow

1. confirm preconditions
2. map files/tests/docs affected
3. write small testable tasks
4. include validation commands and rollback notes where needed
5. hand off to `skill-executing-plans` (or `skill-subagent-driven-development`)

## Guardrails

- No implementation code in this skill.
- Do not duplicate lifecycle/routing policy text here.
- Keep guidance concise; canonical template carries required structure.
- Plan tasks so later execution can pick next actions via the next-action gate prompt.
- Do not author plan steps that require inventing unrelated execution actions.
