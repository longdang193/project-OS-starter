# Runtime Surfaces

This document records provider-native deployment model for operating-system rules,
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
| Codex | `generated_agents/codex/AGENTS.md` | `generated_agents/codex/rules/*.rules` | canonical docs only under `docs/operating_system/workflows/*.md` | `generated_agents/codex/skills/<skill>/SKILL.md` | `generated_agents/codex/hooks.json` |
| Claude | `generated_agents/claude/CLAUDE.md` | `generated_agents/claude/rules/*.md` | canonical docs only under `docs/operating_system/workflows/*.md` | `generated_agents/claude/skills/<skill>/SKILL.md` | `generated_agents/claude/settings.json` |
| Antigravity/Gemini | `generated_agents/antigravity/GEMINI.md` | `generated_agents/antigravity/rules/*.md` | canonical docs only under `docs/operating_system/workflows/*.md` | `generated_agents/antigravity/skills/<skill>/SKILL.md` | `generated_agents/antigravity/settings.json` |

## Deployment Targets

| Provider | Deploy root | Notes |
| --- | --- | --- |
| Shared native skills | `~/.agents/skills` | Deploy mirrors repo-owned `.agents/skills/<skill>/` into the user skill home and preserves unrelated installed skills. |
| Codex | `~/.codex` | Local deploy intentionally skips repo-owned `skills/` so repo checkout remains single source of skill discovery during local development. |
| Claude | `~/.claude` | Deploy includes generated native skills. |
| Antigravity/Gemini | `~/.gemini/antigravity` | Deploy includes generated native skills. |

## Policy

- Canonical repo sources remain source of truth.
- Shared user skill installs under `~/.agents/skills` are a synced copy of repo-owned skills, not a second authoring surface.
- Generated runtime outputs remain deployable packaging surfaces.
- Workflow procedures remain documented in `docs/operating_system/workflows/`; they are not deployed as runtime skills.
- Codex local deploy keeps `.codex/skills` free of repo-owned duplicates when repo skills are already available from workspace source.
