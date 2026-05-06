---
layer: operating_system
artifact_type: plan
status: proposed
parent_workstream: none
parent_thread: none
parent_spec: none
targets:
  - AGENTS.md
  - adapters/
  - docs/operating_system/
  - .agents/skills/
  - generated_agents/
  - scripts/sync_agent_adapters.py
  - scripts/deploy_agent_runtime.py
related_features: []
related_stages: []
---

# Cross-Tool Global Baseline And Generated Runtime Rules Plan

## Goal

Implement a governed cross-tool rule system where:

1. `AGENTS.md` is the global baseline contract across tools.
2. `~/.codex`, `~/.claude`, and `~/.gemini` are generated runtime targets only.
3. Canonical edits happen only in repo sources.
4. Generation, deployment, and drift validation are automated and enforceable.

## Scope

In scope:

1. Baseline/runtime architecture:
   - `AGENTS.md` as global contract source
   - generated runtime outputs for Codex/Claude/Gemini
2. Canonical metadata schema updates for:
   - skills
   - rules
   - workflows
3. Generator + deploy scripts
4. Validator and CI drift checks

Out of scope:

- rewriting every historical prompt/workflow body for style consistency
- changing tool-native behavior beyond mapping/format adaptation

## Target Operating Model

1. Canonical sources in repo:
   - `AGENTS.md`
   - `docs/operating_system/`
   - `.agents/skills/`
2. Generated outputs in repo:
   - `generated_agents/codex/`
   - `generated_agents/claude/`
   - `generated_agents/antigravity/`
3. Deployed runtime targets:
   - `~/.codex`
   - `~/.claude`
   - `~/.gemini`
4. No hand edits allowed in generated runtime targets.

## Metadata Schema Contract

### Skill

Required frontmatter fields:

- `name`
- `description`
- `allowed-tools`
- `hooks` (`pre`, `post`)
- `required_reads`
- `tags`

### Rule

Required frontmatter fields:

- `name`
- `description`
- `alwaysApply`
- `required_reads`
- `tags`

### Workflow

Required frontmatter fields:

- `name`
- `description`
- `required_reads`
- `related_skills`
- `tags`

Conventions:

1. `name` unique and kebab-case.
2. Empty list fields represented as explicit `[]`.
3. `required_reads` entries are repo-relative canonical paths.
4. `description` is one-sentence trigger/purpose focused.

## Implementation Phases

## Phase 1: Folder and Adapter Surface

1. Add adapter config surface:
   - `adapters/codex/`
   - `adapters/claude/`
   - `adapters/gemini/`
2. Add generated output surface:
   - `generated_agents/codex/`
   - `generated_agents/claude/`
   - `generated_agents/antigravity/`
3. Add docs:
   - architecture/readme describing canonical vs generated vs deployed layers.

## Phase 2: Canonical Schema Rollout

1. Add/update schema docs under `docs/operating_system/`:
   - required fields per type
   - examples
2. Migrate target high-impact files first:
   - critical skills
   - critical workflows
   - core rule files
3. Track migration coverage.

## Phase 3: Generation and Deployment Tooling

1. Add generator script:
   - `scripts/sync_agent_adapters.py`
   - reads canonical sources
   - emits `generated_agents/*`
2. Add deploy script:
   - `scripts/deploy_agent_rules.py`
   - deploys generated artifacts to `~/.codex`, `~/.claude`, `~/.gemini`
3. Add `--check` mode:
   - compares current generated/deployed state against expected
   - non-zero exit on drift

## Phase 4: Validator Enforcement

1. Schema validator:
   - required metadata fields by artifact type
   - list type validation for `required_reads`, `tags`, etc.
2. Drift validator:
   - generated outputs stale vs canonical
   - deployed runtime stale vs generated
3. Integrate into `validate_repo_contracts.py --fast` path where appropriate.

## Phase 5: CI and Local Workflow

1. Local commands:
   - `python scripts/sync_agent_adapters.py`
   - `python scripts/deploy_agent_rules.py --target all`
   - `python scripts/sync_agent_adapters.py --check`
2. CI commands:
   - schema validators
   - sync `--check`
   - deploy drift check (optional for CI environment constraints)

## Key Scripts and Artifacts

New:

1. `scripts/sync_agent_adapters.py`
2. `scripts/deploy_agent_rules.py`
3. `scripts/validate_agent_metadata_schema.py`
4. `scripts/validate_agent_runtime_drift.py`
5. `tests/test_sync_agent_adapters.py`
6. `tests/test_validate_agent_metadata_schema.py`

Updated:

1. `scripts/validate_repo_contracts.py`
2. relevant docs in `docs/operating_system/`

## Validation Plan

1. Metadata schema checks pass on migrated artifacts.
2. Generation is deterministic (repeat run yields no diff).
3. Deploy writes expected files to each home directory target.
4. `--check` detects and fails on:
   - stale generated artifacts
   - stale runtime deployment targets

## Risk and Mitigation

1. Risk: platform-specific format mismatch.
   Mitigation: adapter-specific mapping tests for codex/claude/gemini.
2. Risk: accidental hand-edits in generated/deployed targets.
   Mitigation: header warnings + drift check + CI fail.
3. Risk: migration burden across many existing files.
   Mitigation: phased rollout with high-impact-first and coverage tracking.

## Done Criteria

1. Canonical schema documented and enforced.
2. Generator and deploy scripts operational.
3. Runtime targets generated/deployed from repo only.
4. Drift checks integrated and failing correctly when stale.
5. CI/local workflow documented and reproducible.
