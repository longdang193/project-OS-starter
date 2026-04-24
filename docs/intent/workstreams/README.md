# Workstream Registry

This folder is the canonical registry for named product workstreams.

Use [master-workstream-roadmap.md](C:/Users/HOANG%20PHI%20LONG%20DANG/repos/project-OS-starter/docs/intent/master-workstream-roadmap.md)
as the high-level overview.
Use this folder when you need the concrete valid workstream IDs that specs and
plans may reference through `parent_workstream`.

When you are still deciding which workstream to use, or whether the work should
stay in `operating_system`, use the roadmap-aware prompts under
`docs/operating_system/prompt_templates/` before drafting downstream specs or
plans.

Rules:

- one Markdown file per named workstream
- filename should match `workstream_id`
- keep the file small and source-like
- use `parent_workstream: none` for intent or operating-system artifacts rather
  than inventing a product workstream

Suggested file shape:

```yaml
---
workstream_id: <id>
status: active | proposed | paused | completed
parent_intent: master-workstream-roadmap
---
```
