# Runtime Surfaces

This document records provider-native deployment for rules, skills, root instructions, and hooks.

## Canonical Sources

| Source | Role |
| --- | --- |
| `docs/operating_system/rules/*.md` | Canonical rule authoring |
| `.agents/skills/*/SKILL.md` | Canonical reusable method authoring |
| `docs/operating_system/templates/agents/root-AGENTS.template.md` | Canonical root instruction source |
| `agents/{xhigh,high,normal,low}.toml` | Canonical delegated-role definitions |

## Generated Runtime Outputs

| Provider | Root instructions | Rules | Native skills | Hooks/settings |
| --- | --- | --- | --- | --- |
| Codex | `generated_agents/codex/AGENTS.md` | none | `generated_agents/codex/skills/<skill>/SKILL.md` | none |
| Codex delegated roles | `generated_agents/codex/agents/<role>.toml` | none | none | Deployed to `~/.codex/agents/` |
| DeepAgents delegated roles | Root `AGENTS.md` auto-loaded; user-local `dcode-project` materializes ignored `.deepagents/agents/<role>/AGENTS.md` only for launch, then cleans marker-owned views | Canonical `docs/operating_system/rules/*.md` read when task scope requires; `.agents/rules` is not auto-loaded | `.agents/skills/<skill>/SKILL.md` auto-discovered | Local runtime only; no MCP projection |
| Claude | `generated_agents/claude/CLAUDE.md` | `generated_agents/claude/rules/*.md` | `generated_agents/claude/skills/<skill>/SKILL.md` | `generated_agents/claude/settings.json` |
| Antigravity/Gemini | `generated_agents/antigravity/GEMINI.md` | `generated_agents/antigravity/rules/*.md` | `generated_agents/antigravity/skills/<skill>/SKILL.md` | `generated_agents/antigravity/settings.json` |

## Deployment Targets

| Provider | Deploy root | Notes |
| --- | --- | --- |
| Shared native skills | `~/.agents/skills` | Synced copy of repo-owned skills; repo remains authoring source. |
| Codex | `~/.codex` | Local deploy skips duplicate repo-owned skills. |
| DeepAgents | User-local `dcode-project` | Launcher reads active Codex provider binding and local secret source; `--role` selects canonical source role model for primary launch; validates controller-owned handoff; forces `--no-mcp`. |
| Claude | `~/.claude` | Deploy includes generated native skills. |
| Antigravity/Gemini | `~/.gemini/antigravity` | Deploy includes generated native skills. |

## Policy

- Canonical repo sources remain source of truth.
- Profile order is `xhigh > high > normal > low`. In validator-executor setups,
  validator profile must rank above executor profile. `xhigh` is ceiling, so it
  cannot be executor in a separate profile-based validator pair.
- Generated runtime outputs remain deployable packaging surfaces.
- DeepAgents role views are local generated runtime state, not primary profiles or tracked adapter output.
- DeepAgents auto-loads root `AGENTS.md` and discovers `.agents/skills` as
  project skills. It does not load `.agents/rules` as direct instructions;
  those files are generated platform-adapter views. Detailed rules remain
  canonical under `docs/operating_system/rules/` and are read when task scope
  requires them.
- DeepAgents built-ins are executor-local. Current launcher does not project
  Codex MCP servers, tool allowlists, approval, sandbox, shell, profile, or
  thread settings.
- Codex controller owns MCP calls and writes `codex.mcp.handoff.v1` under
  `%USERPROFILE%\.local\share\dcode-project\handoffs`; `dcode-project` validates
  handoff path, age, schema, source IDs, capability digest, and sensitive-field
  exclusions, then injects only sanitized sources, facts, and constraints into
  task text before launching DeepAgents. `--mcp-select` narrows provenance
  only; it does not make MCP tools available inside DeepAgents.
- DeepAgents web search is executor-local and needs user-local `TAVILY_API_KEY`. It\n  is absent by default and never falls back to Codex browser or web MCP tools.
- Reusable operating methods live in skills; prompts remain wording-only.
