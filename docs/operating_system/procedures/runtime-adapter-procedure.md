# Runtime Adapter Procedure (Cross-Tool)

## Contract

1. `AGENTS.md` is the generated shared global baseline contract.
2. `~/.codex`, `~/.claude`, `~/.gemini` are runtime targets.
3. Runtime targets are generated and deployed only.
4. Canonical edits happen in repo sources only:
   - scoped `AGENTS.md` files, when present
   - `docs/operating_system/`
   - `.agents/skills/`
   - `agents/*.toml`
   - `docs/operating_system/templates/agents/root-AGENTS.template.md`

Scoped `AGENTS.md` files are canonical instructions for their directories.
`docs/operating_system/rules/` is canonical rule source. Adapter sync mirrors it
to `.agents/rules/` for supported local runtimes.

`agents/xhigh.toml`, `agents/high.toml`, `agents/normal.toml`, and
`agents/low.toml` are canonical delegated-role templates. They own delegated
provider alias, model, rank, and prompt. Profile order is `xhigh > high > normal > low`.
In validator-executor setups, validator profile must rank above executor profile.
Sync renders Codex TOML into
`generated_agents/codex/agents/`. User-local `dcode-project` generates ignored
DeepAgents project views at launch. Keep provider endpoints, credentials, MCP
configuration, and provider definitions out of role templates and tracked
outputs.

## Generate

```bash
python scripts/sync_agent_adapters.py --all-platforms
```

Outputs:

- `generated_agents/codex/`
- `generated_agents/claude/`
- `generated_agents/antigravity/`

## Deploy

```bash
python scripts/deploy_agent_runtime.py --target all
```

Targets:

- `~/.codex`
- `~/.claude`
- `~/.gemini`

DeepAgents is not an adapter-sync target. User-local `dcode-project` derives
ignored project subagents from `agents/*.toml` at launch. Every task launch
requires `--role <low|normal|high|xhigh>`; launcher consumes this selector and
uses selected source role's model for its primary `dcode -M` binding. Its
provider endpoint, credentials, provider definition, and mutable state remain
local. Each source role's `model_provider` must match active local Codex provider
binding.

Current `dcode-project` forces DeepAgents `--no-mcp`, fixes child CWD to selected
Git root, and rejects direct runtime-authority flags. It does not translate Codex
`mcp_servers`, approval policy, sandbox mode, profiles, or threads. It supplies
fixed launcher-owned built-ins: filesystem tools plus `git` and `py` shell
commands; task input cannot widen them. Launcher injects exact native file-tool
root into every bounded task. On Windows it looks like
`/Users/<user>/repos/<repo>`; append repository-relative paths. Never guess
`/workspace/...` or use Windows drive syntax. Call MCP through Codex, then let
`dcode-project` validate `codex.mcp.handoff.v1` and inject only sanitized
sources, facts, and constraints into task text. Setup rejects a
user-local `~/.deepagents/.mcp.json` to prevent an accidental direct MCP path.

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
