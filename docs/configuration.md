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
- the effective local-capability and MCP-selection digest matches the incoming
  assignment.

Different or missing context selects a new pane when a validated source pane
can be split. Candidate-local inspection failures, including incompatible
context, malformed pane process metadata, or a candidate process-info timeout,
are recorded as candidate rejections and do not suppress that replacement
allocation. Global snapshot corruption or session-wide agent identity failures
remain blocked with structured incomplete evidence rather than being treated as
an individual pane defect. The selector reserves time inside its discovery
budget for the split-and-poll allocation path; it does not create a scheduler,
registry, or separate reconciliation store.

The retirement policy is canonical in the upstream 9router source. The local
`repo_config/retired-model-policy.json` and
`scripts/retired-model-policy.json` files are synchronized projections used by
repository validation and shared-runtime deployment. Starter-kit generation
does not copy the shared-runtime launcher or policy projection into consumer
repositories.

Idle panes with no live process are released through the existing Herdr
lifecycle mechanism.

Reuse is preferred over recreating a browser window or pane. A mismatch in
capability selection, identity, or lifecycle state allocates a replacement
instead of mutating an incompatible live process. Allocation discovery and
lock acquisition have separate bounded budgets; a pane created without a
verified post-split identity is reported as `created_unverified` and is not
silently reused.

MCP servers that use environment-backed fields such as
`bearer_token_env_var`, `env_http_headers`, structured `env_vars`, or
`*_env_var` OAuth references are treated as incompatible with existing Codex
agents because their effective runtime values cannot be fingerprinted safely.
Those launches receive a unique replacement agent name rather than incurring a
deterministic name collision. Direct, uncoordinated DeepAgents launches do not
create structured result artifacts because they lack the assignment bindings
required for safe settlement.

DeepAgents result directories are launcher-owned temporary artifacts. They are
removed only after durable task-result publication, identity correlation,
terminal lifecycle settlement, and no-continuation proof. Missing, foreign,
identity-mismatched, or ambiguous evidence is retained with a recovery marker;
the bounded recovery cleanup touches only marked `herdr-result-*` directories.
