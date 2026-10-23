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

Profile availability is defined only by the files present in `agents/`. Remove
profile files from that directory when retiring a profile; generated adapter
surfaces are then updated by the synchronization script.

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
