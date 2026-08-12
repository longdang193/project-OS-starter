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
| DeepAgents project subagents | `.deepagents/agents/<role>/AGENTS.md` | none | none | Repository discovery only; no home deployment |
| Claude | `generated_agents/claude/CLAUDE.md` | `generated_agents/claude/rules/*.md` | `generated_agents/claude/skills/<skill>/SKILL.md` | `generated_agents/claude/settings.json` |
| Antigravity/Gemini | `generated_agents/antigravity/GEMINI.md` | `generated_agents/antigravity/rules/*.md` | `generated_agents/antigravity/skills/<skill>/SKILL.md` | `generated_agents/antigravity/settings.json` |

## Deployment Targets

| Provider | Deploy root | Notes |
| --- | --- | --- |
| Shared native skills | `~/.agents/skills` | Synced copy of repo-owned skills; repo remains authoring source. |
| Codex | `~/.codex` | Local deploy skips duplicate repo-owned skills. |
| DeepAgents | none | Project subagents load from `.deepagents/agents/`; `~/.deepagents` keeps user-local primary profile and mutable state. |
| Claude | `~/.claude` | Deploy includes generated native skills. |
| Antigravity/Gemini | `~/.gemini/antigravity` | Deploy includes generated native skills. |

## Policy

- Canonical repo sources remain source of truth.
- Generated runtime outputs remain deployable packaging surfaces.
- DeepAgents project subagents are generated prompt views, not primary profiles.
- Reusable operating methods live in skills; prompts remain wording-only.
