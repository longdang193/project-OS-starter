# Runtime Surfaces

This document records provider-native deployment for rules, skills, root instructions, and hooks.

## Canonical Sources

| Source | Role |
| --- | --- |
| `docs/operating_system/rules/*.md` | Canonical rule authoring |
| `.agents/skills/*/SKILL.md` | Canonical reusable method authoring |
| `docs/operating_system/templates/agents/root-AGENTS.template.md` | Canonical root instruction source |
| `agents/{high,normal,low}.toml` | Canonical delegated-role definitions |

## Generated Runtime Outputs

| Provider | Root instructions | Rules | Native skills | Hooks/settings |
| --- | --- | --- | --- | --- |
| Codex | `generated_agents/codex/AGENTS.md` | none | `generated_agents/codex/skills/<skill>/SKILL.md` | none |
| Codex delegated roles | `generated_agents/codex/agents/<role>.toml` | none | none | Deployed to `~/.codex/agents/` |
| DeepAgents delegated roles | `agents/<role>.toml` | User-local `dcode-project` materializes ignored `.deepagents/agents/<role>/AGENTS.md` only for launch, then cleans marker-owned views | none | Local runtime only; no MCP projection |
| Claude | `generated_agents/claude/CLAUDE.md` | `generated_agents/claude/rules/*.md` | `generated_agents/claude/skills/<skill>/SKILL.md` | `generated_agents/claude/settings.json` |
| Antigravity/Gemini | `generated_agents/antigravity/GEMINI.md` | `generated_agents/antigravity/rules/*.md` | `generated_agents/antigravity/skills/<skill>/SKILL.md` | `generated_agents/antigravity/settings.json` |

## Deployment Targets

| Provider | Deploy root | Notes |
| --- | --- | --- |
| Shared native skills | `~/.agents/skills` | Synced copy of repo-owned skills; repo remains authoring source. |
| Codex | `~/.codex` | Local deploy skips duplicate repo-owned skills. |
| DeepAgents | User-local `dcode-project` | Launcher reads active Codex provider binding, local secret source, and optional local role-model overrides; forces `--no-mcp`. |
| Claude | `~/.claude` | Deploy includes generated native skills. |
| Antigravity/Gemini | `~/.gemini/antigravity` | Deploy includes generated native skills. |

## Policy

- Canonical repo sources remain source of truth.
- Generated runtime outputs remain deployable packaging surfaces.
- DeepAgents role views are local generated runtime state, not primary profiles or tracked adapter output.
- DeepAgents built-ins are executor-local. Current launcher does not project
  Codex MCP servers, tool allowlists, approval, sandbox, shell, profile, or
  thread settings.
- DeepAgents web search requires its own user-local provider configuration. It
  is absent by default and never falls back to Codex browser or web MCP tools.
- Reusable operating methods live in skills; prompts remain wording-only.
