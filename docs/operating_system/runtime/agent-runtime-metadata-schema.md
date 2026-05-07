# Agent Runtime Metadata Schema

## Goal

Define a practical canonical metadata contract for skills, rules, and workflows
that can be generated and deployed into Codex, Claude, and Antigravity runtimes
(`~/.codex`, `~/.claude`, `~/.gemini`).

## Skill Frontmatter

Required fields:

- `name`
- `description`
- `allowed-tools`
- `hooks` with `pre` and `post` lists
- `required_reads`
- `tags`

Example:

```yaml
---
name: example-skill
description: Use this skill when the user asks for X.
allowed-tools: []
hooks:
  pre: []
  post: []
required_reads: []
tags: []
---
```

## Rule Frontmatter

Required fields:

- `name`
- `description`
- `alwaysApply` (`true|false`)
- `required_reads`
- `tags`

Example:

```yaml
---
name: example-rule
description: Enforce Y across runtime usage.
alwaysApply: true
required_reads: []
tags: []
---
```

## Workflow Frontmatter

Required fields:

- `name`
- `description`
- `required_reads`
- `related_skills`
- `tags`

Example:

```yaml
---
name: example-workflow
description: Run workflow Z when condition C holds.
required_reads: []
related_skills: []
tags: []
---
```

## Conventions

1. `name` should be stable and kebab-case.
2. Arrays must be explicit lists (`[]` if empty).
3. `required_reads` should use repo-relative canonical paths.
4. This schema is canonical in repo; adapters map it to platform-specific
   runtime surfaces.
