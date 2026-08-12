# Runtime Adapter Procedure (Cross-Tool)

## Contract

1. `AGENTS.md` is the generated shared global baseline contract.
2. `~/.codex`, `~/.claude`, `~/.gemini` are runtime targets.
3. Runtime targets are generated and deployed only.
4. Canonical edits happen in repo sources only:
   - `AGENTS.md` and scoped `AGENTS.md` files
   - `docs/operating_system/`
   - `.agents/skills/`
   - `agents/*.toml`
   - `docs/operating_system/templates/agents/root-AGENTS.template.md`

Scoped `AGENTS.md` files are canonical instructions for their directories.
`docs/operating_system/rules/` is canonical rule source. Adapter sync mirrors it
to `.agents/rules/` for supported local runtimes.

`agents/high.toml`, `agents/normal.toml`, and `agents/low.toml` are canonical
delegated-role templates. Sync renders Codex TOML into
`generated_agents/codex/agents/` and DeepAgents project subagents into
`.deepagents/agents/`. Both inherit provider and model selection from active
user-local primary runtime. Keep endpoints, credentials, MCP configuration, and
private model bindings out of role templates and generated project agents.

## Generate

```bash
python scripts/sync_agent_adapters.py --all-platforms
```

Outputs:

- `generated_agents/codex/`
- `generated_agents/claude/`
- `generated_agents/antigravity/`
- `.deepagents/agents/`

## Deploy

```bash
python scripts/deploy_agent_runtime.py --target all
```

Targets:

- `~/.codex`
- `~/.claude`
- `~/.gemini`

DeepAgents project subagents are discovered from repository
`.deepagents/agents/`; do not deploy them to `~/.deepagents`. User-local
`dcode --agent` primary profiles, provider setup, credentials, and mutable state
remain under `~/.deepagents`.

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

- `docs/operating_system/runtime/agent-runtime-metadata-schema.md`
