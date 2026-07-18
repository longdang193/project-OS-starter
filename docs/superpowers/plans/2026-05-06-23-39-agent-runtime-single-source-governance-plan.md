---
layer: operating_system
artifact_type: plan
status: proposed
parent_workstream: none
parent_thread: none
parent_spec: none
targets:
  - adapters/codex/mapping.yaml
  - adapters/claude/mapping.yaml
  - adapters/gemini/mapping.yaml
  - scripts/sync_agent_adapters.py
  - scripts/deploy_agent_rules.py
  - scripts/validate_agent_runtime_drift.py
  - scripts/validate_agent_metadata_schema.py
  - scripts/validate_prompt_metadata_schema.py
  - scripts/validate_repo_contracts.py
  - docs/operating_system/provider_settings/
  - docs/operating_system/manifest.yaml
  - docs/operating_system/provider_capabilities.yaml
  - docs/operating_system/governance/precedence.md
  - generated_agents/
related_features: []
related_stages: []
---

# Agent Runtime Single Source Governance Plan

## Goal

Implement a single-source runtime governance pipeline so Codex, Claude, and Antigravity runtime homes (`~/.codex`, `~/.claude`, `~/.gemini`) are fully generated from one canonical source surface, with deterministic sync/deploy/validation and no hand-edited runtime drift.

## Key Deliverables

- Canonical source mapping contract finalized for rules/workflows/skills/root entrypoint files.
- Provider runtime targets include generated root instruction files (`AGENTS.md`, `CLAUDE.md`, `GEMINI.md`) plus provider-specific runtime folders.
- Provider settings layer enforces a canonical semantic hook contract with provider-specific rendering.
- Codex lifecycle hooks rendered to `hooks.json` (with feature flag support) and wired to the shared validator wrapper.
- Claude lifecycle hooks rendered to `settings.json` and wired to the shared validator wrapper.
- Antigravity uses rules/workflows fallback guidance for validator invocation unless native lifecycle hooks are confirmed.
- Manifest + lockfile generation introduced for source/generated hash traceability.
- Schema validation enforced for skills/rules/workflows/prompts (including prompt metadata validator already added).
- Runtime deploy script hardened with `--check`, `--dry-run`, `--backup`, safe overwrite behavior, and explicit changed-path reporting.
- CI checks block stale generated artifacts and schema/runtime drift.

## Task Breakdown

- Task 1: Canonical source and mapping baseline
  - Confirm canonical source of truth:
    - `docs/operating_system/rules/*.md`
    - `.agents/skills/*/SKILL.md`
    - canonical root instruction templates.
  - Treat `.agents/skills/*/SKILL.md` as the canonical shared skill authoring surface, not as a generated Codex-only mirror.
  - Ensure adapter mappings are mapping-only and contain no duplicated semantic source content.

- Task 2: Root entrypoint generation and deploy
  - Add provider entrypoint generation outputs:
    - `generated_agents/codex/AGENTS.md`
    - `generated_agents/claude/CLAUDE.md`
    - `generated_agents/antigravity/GEMINI.md`
  - Ensure deploy copies to:
    - `~/.codex/AGENTS.md`
    - `~/.claude/CLAUDE.md`
    - `~/.gemini/GEMINI.md`
  - Add/update generated-file markers while preserving metadata-first contract.

- Task 3: Provider settings contract
  - Add canonical settings source:
    - `docs/operating_system/provider_settings/codex.yaml`
    - `docs/operating_system/provider_settings/claude.yaml`
    - `docs/operating_system/provider_settings/antigravity.yaml`
  - Define canonical semantic hook events (provider-agnostic):
    - `task_start`
    - `task_end`
    - `error`
    - `pre_tool`
    - `post_tool`
  - Add hook control fields:
    - `enabled`
    - `blocking`
    - `timeout_seconds`
    - `commands`
    - provider event mapping/fallback fields
  - Enforce provider-capability rendering:
    - Claude/Codex: lifecycle hook config generation enabled
    - Antigravity: rules/workflows fallback generation unless native lifecycle hooks are confirmed
  - Semantic events are provider-neutral. Adapters may render them only when the provider supports an equivalent lifecycle event; otherwise they must render fallback rule/workflow guidance or drop the event with validation output.

- Task 3A: Shared validator wrapper for hooks
  - Add a single hook command wrapper:
    - `scripts/hooks/run_validator.py --fast`
  - Wrapper behavior:
    - resolve repo root safely
    - invoke `scripts/validate_repo_contracts.py --fast` using `sys.executable`
    - preserve non-zero exit behavior
  - Ensure provider hooks call wrapper only (no duplicated validation logic in hook payloads).

- Task 3B: Provider-specific hook outputs
  - Codex:
    - generate `generated_agents/codex/hooks.json`
    - set/verify hook feature support in generated codex runtime config
    - avoid mixed inline hooks + `hooks.json` in the same layer unless explicitly allowed
  - Claude:
    - generate `generated_agents/claude/settings.json` with lifecycle hooks mapped from canonical semantic events
  - Antigravity:
    - generate fallback rule/workflow guidance that instructs validator execution before completion claims
    - do not emit fake lifecycle-hook config when capability is unavailable

- Task 4: Manifest and lockfile
  - Add `docs/operating_system/manifest.yaml` to declare source-to-target mapping.
  - Add lock generation to capture source/generated hashes:
    - `generated_agents/manifest.lock.json`
  - Lockfile records hashes for canonical sources and generated artifacts; deployed runtime hashes are recorded or checked by runtime drift validation.
  - Extend drift checks to fail when lock is stale against canonical sources.

- Task 5: Schema and policy validation
  - Keep existing validators and add missing checks for:
    - duplicate IDs/names across rule/workflow/prompt surfaces
    - broken `required_reads` references
    - invalid stage/type fields per schema.
  - Add provider-settings schema checks for:
    - provider/file identity consistency
    - `hooks.enabled` boolean validity
    - enabled events have provider mapping or fallback
    - `commands` values are non-empty strings
    - `timeout_seconds` required for blocking hooks and bounded to safe limits
    - command safety policy (must call approved wrapper for validator authority)
    - no URL-encoded filesystem paths in command strings
    - capability-consistent output generation (no unsupported lifecycle hooks emitted)
  - Add or update `provider_capabilities.yaml` and `precedence.md` and validate policy references exist.

- Task 6: Deploy hardening
  - Rename deploy entrypoint to runtime-focused command:
    - `scripts/deploy_agent_runtime.py`
    - keep compatibility shim: `scripts/deploy_agent_rules.py`
  - Extend deploy command behavior:
    - `--check`
    - `--dry-run`
    - `--backup`
    - `--force`
  - Enforce manual-edit refusal on runtime targets unless `--force`.
  - Implement atomic write flow and changed-file summary output.

- Task 7: CI and ownership enforcement
  - Add/adjust CI job to run:
    - schema validators
    - `sync_agent_adapters.py --check`
    - generated artifact drift checks
    - runtime drift checks in repo-safe mode.
  - Mark generated surfaces as generated in `.gitattributes` and tighten `CODEOWNERS` for governance surfaces.

- Task 8: Documentation and migration notes
  - Update governance docs to reflect finalized target layout and deploy conventions.
  - Document provider hook capability model and fallback behavior:
    - Codex and Claude lifecycle hooks
    - Antigravity rules/workflows fallback
  - Document canonical semantic event names and provider event mapping.
  - Add migration notes for existing repos consuming old `global_*` naming or legacy target paths.
  - Document operator runbook for sync/deploy/validate cycle.

## Verification

- `python scripts/validate_agent_metadata_schema.py`
- `python scripts/validate_prompt_metadata_schema.py`
- `python scripts/validate_provider_settings_schema.py`
- `python scripts/sync_agent_adapters.py`
- `python scripts/sync_agent_adapters.py --check`
- `python scripts/validate_agent_runtime_drift.py --skip-deploy-check`
- `python scripts/deploy_agent_runtime.py --target all --dry-run`
- `python scripts/deploy_agent_runtime.py --target all --check`
- `python scripts/validate_repo_contracts.py --fast`

## Completion Criteria

A plan item is considered complete when:

1. all Key Deliverables are satisfied
2. all downstream/child items are terminal
3. every child item is `completed` or `dropped`

Additionally for this plan:

- Runtime homes for Codex, Claude, and Antigravity are reproducible from canonical sources with no manual edit requirement.
- Drift and schema checks fail reliably on stale or non-compliant generated/runtime artifacts.
- Updated governance docs and commands match actual implemented behavior.
- Provider hook behavior is capability-correct:
  - Codex and Claude run shared validator wrapper from lifecycle hooks
  - Antigravity uses documented fallback rules/workflows instead of unsupported lifecycle-hook configs
- Codex hook generation does not mix inline hooks and `hooks.json` in the same config layer unless explicitly configured and validated.
