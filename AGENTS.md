# GENERATED FILE - do not edit directly.
# Source: `C:\Users\HOANG PHI LONG DANG\repos\project-OS-starter\agent-core\adapters\codex\root-AGENTS.template.md`
# Project Agent Instructions

This file is the repo-wide instruction layer for Codex.

## Scope

Use this file for repo-wide behavior only. More specific directory instructions may override it.

## Repo Rules

- The private repo is the development source of truth.
- The public repo is updated only through the curated publish workflow.
- Repo governance lives in `docs/operating_system/`.
- Skills live in `.agents/skills/`, which remains the canonical Codex skill surface.
- Skills should follow the Codex Skills model: one focused workflow per skill, with `SKILL.md` as the primary entrypoint.

## Working Expectations

- Keep changes aligned with the owning code and doc layer.
- Update tests and docs when behavior or contracts change.
- Do not expose private operating-system or agent-core material through the public mirror.
- If you change `agent-core/adapters/*`, generated `AGENTS.md`, or `codex/rules/*.rules`, run the sync and verify scripts before considering the change complete.

