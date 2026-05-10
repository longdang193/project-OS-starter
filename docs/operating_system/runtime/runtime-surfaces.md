# Runtime Surfaces

This document records the provider-native deployment model for operating-system rules,
workflows, skills, root instructions, and hooks.

## Canonical Sources

| Source | Role |
| --- | --- |
| `docs/operating_system/rules/*.md` | Canonical rule authoring |
| `docs/operating_system/workflows/*.md` | Canonical workflow authoring |
| `.agents/skills/*/SKILL.md` | Canonical native skill authoring |
| `docs/operating_system/provider_settings/*.yaml` | Canonical hook/settings authoring |
| `AGENTS.md` | Canonical root instruction source |

## Generated Runtime Outputs

| Provider | Root instructions | Rules | Workflows | Native skills | Hooks/settings |
| --- | --- | --- | --- | --- | --- |
| Codex | `generated_agents/codex/AGENTS.md` | `generated_agents/codex/rules/*.rules` | `generated_agents/codex/skills/<workflow>/SKILL.md` | `generated_agents/codex/skills/<skill>/SKILL.md` | `generated_agents/codex/hooks.json` |
| Claude | `generated_agents/claude/CLAUDE.md` | `generated_agents/claude/rules/*.md` | `generated_agents/claude/skills/<workflow>/SKILL.md` | `generated_agents/claude/skills/<skill>/SKILL.md` | `generated_agents/claude/settings.json` |
| Antigravity/Gemini | `generated_agents/antigravity/GEMINI.md` | `generated_agents/antigravity/rules/*.md` | `generated_agents/antigravity/skills/<workflow>/SKILL.md` | `generated_agents/antigravity/skills/<skill>/SKILL.md` | `generated_agents/antigravity/settings.json` |

## Deployment Targets

| Provider | Deploy root | Notes |
| --- | --- | --- |
| Codex | `~/.codex/**` | `AGENTS.md` is authoritative; generated `rules/` are mirrors unless runtime support is verified. |
| Claude | `~/.claude/**` | `CLAUDE.md`, `rules/`, `skills/`, and `settings.json` are native runtime surfaces. |
| Antigravity/Gemini | `~/.gemini/**` | `GEMINI.md` is root instructions; `skills/**` is routed to `~/.gemini/antigravity/skills/**`. |

## Starter-Kit Local Targets

| Surface | Path | Contract |
| --- | --- | --- |
| Generated export | `generated_exports/project-OS-starter-kit` | Rebuilt artifact owned by source repo build flow. |
| Sibling starter-kit repo | `C:\Users\HOANG PHI LONG DANG\repos\project-OS-starter-kit` | Local git checkout that must be updated by full-tree sync from generated export before commit/push. |

When work says "update starter kit", default meaning is:

1. rebuild generated export
2. validate generated export
3. mirror full tree into sibling starter-kit repo
4. verify parity between both trees
5. commit/push sibling repo when publication is intended

Partial directory-only syncs are not canonical closeout.

## Local Mirrors

`.agents/rules` and `.agents/workflows` may remain local mirrors for repo discovery, but they
must not be treated as authoritative runtime auto-load paths unless a provider runtime confirms
that behavior.
