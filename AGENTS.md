# GENERATED FILE - do not edit directly.
# Source: `docs/operating_system/templates/agents/root-AGENTS.template.md`
# Project Agent Instructions

This file is the repo-wide instruction layer for Codex.

## Scope

Use this file for repo-wide behavior only. More specific directory instructions may override it.

## Repo Rules

- The private repo is the development source of truth.
- The public repo is updated only through the curated publish procedure.
- Repo governance lives in `docs/operating_system/`.
- Agent memory lives in `docs/operating_system/agent_memory/`.
- Skills live in `.agents/skills/`, which remains the canonical Codex skill surface.
- `.codex/rules/` is a generated rules output surface, not the canonical home for skills or memory.
- Skills should follow the Codex Skills model: one focused method per skill, with `SKILL.md` as the primary entrypoint.

## Working Expectations

- Keep changes aligned with the owning code and doc layer.
- Consult relevant agent memory before planning when the task touches reusable repo methods or known invariants.
- Consult `docs/operating_system/agent_memory/failure-ledger.md` during debugging, retries, or after important mistakes.
- Update the agent-memory layer when a significant reusable lesson emerges.
- Update tests and docs when behavior or contracts change.
- Do not expose private operating-system or agent-core material through the public mirror.
- If you change `docs/operating_system/templates/agents/*`, generated `AGENTS.md`, or generated provider runtime rules, run the sync and verify scripts before considering the change complete.

## Code Intelligence

Use native code tools for small local work, Serena for exact symbols and
references, and GitNexus for broad flows or impact. Do not query both by
default. Source and tests win every conflict; unavailable tools never block
safe source-first work.

- Serena runs with `--context codex --project-from-cwd`, `no-memories`, and
  `no-onboarding`. Never commit `.serena/` state.
- GitNexus remains optional and private-only. Check freshness before high-trust
  impact or refactor use; never make refresh a universal completion gate.
- Tests and CI own enforcement. `docs/architecture.md` and ADRs own durable
  architecture intent.
- Detailed policy: `docs/operating_system/tooling/code-intelligence-tools.md`.
