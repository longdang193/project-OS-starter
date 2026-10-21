# Configuration

Use this document for cross-cutting project configuration guidance.

Keep it focused on:

- configuration surfaces and ownership
- environment variables, profiles, and config files
- defaults versus overrides
- how `repo_config/` and runtime environment settings interact

This document should prevent "works on my machine" drift by making config
behavior explicit.

## Agent profiles

The canonical profile registry is `agents/*.toml`. Ranked profiles describe
the general capability ordering used for default selection. Specialized
profiles omit `rank` and are explicit-only choices.

`web-medium` and `web-high` use the 9router models `combo-web-medium` and
`combo-web-high` for web-capable, long-context work. They are Herdr-only
profiles: the repository-owned Herdr launcher may resolve them, but the native
Codex adapter does not expose them. They do not replace the general `normal` or
`high` profiles and are not part of the ranked ordering.

When a provider exposes different protocols by model, its local Codex provider
binding may define `wire_api_by_model`. The selected model override takes
precedence over provider `wire_api`; the 9router web models use `chat`, while
the general models keep the provider default.

## Herdr pane affinity

Herdr reuses a live Codex pane only when all of these facts match:

- the pane is idle and has no conflicting live process;
- the incoming task has the same existing task, plan, or assignment identity;
- the executor, provider, and model profile are compatible.

Different or missing context always selects a new pane. The launcher records a
short context marker in its generated agent name so reuse does not mix
unrelated conversations. Idle panes with no live process are released through
the existing Herdr lifecycle mechanism; no separate reconciliation store is
created.
