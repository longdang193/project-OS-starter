# Rules And Workflows Procedure (Cross-Tool)

## Contract

1. `AGENTS.md` is the shared global baseline contract.
2. `~/.codex`, `~/.claude`, `~/.gemini` are runtime targets.
3. Runtime targets are generated and deployed only.
4. Canonical edits happen in repo sources only:
   - `docs/operating_system/`
   - `.agents/skills/`
   - `AGENTS.md`

## Generate

```bash
python scripts/sync_agent_adapters.py
```

Outputs:

- `generated_agents/codex/`
- `generated_agents/claude/`
- `generated_agents/antigravity/`

## Deploy

```bash
python scripts/deploy_agent_rules.py --target all
```

Targets:

- `~/.codex`
- `~/.claude`
- `~/.gemini`

## Drift Checks

Generated drift:

```bash
python scripts/sync_agent_adapters.py --check
```

Runtime drift:

```bash
python scripts/validate_agent_runtime_drift.py
```

CI-safe (skip home-directory check):

```bash
python scripts/validate_agent_runtime_drift.py --skip-deploy-check
```

## Metadata Schema Validation

```bash
python scripts/validate_agent_metadata_schema.py
```

Schema source:

- `docs/operating_system/agent-runtime-metadata-schema.md`
