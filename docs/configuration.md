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
`combo-web-high` for web-capable, long-context work. They do not replace the
general `normal` or `high` profiles and are not part of the ranked ordering.
