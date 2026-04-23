# Markdown Frontmatter Template

Use frontmatter only for docs that materially explain a feature, capability, stage, config, component, or operator workflow. Do not add it to every markdown file by default.

In `managed_architecture_metadata` mode, the required root docs
`docs/setup.md`, `docs/configuration.md`, `docs/usage.md`, `docs/pipeline.md`,
and `docs/architecture.md` are part of that metadata-linked doc surface and
should follow this pattern with canonical `doc_id` values.

The optional root docs `docs/dataset.md`, `docs/api.md`,
`docs/observability.md`, and `docs/testing.md` stay optional. When present in
managed mode, they also follow this pattern with canonical `doc_id` values.
Place the opening `---` at the first byte of the file so tooling can parse it.

Copy the fenced example below to the top of a real explanatory markdown file:

```md
---
doc_id: billing-insights-operator-guide
doc_type: guide
explains:
  features:
    - billing-insights
  capabilities:
    - billing-insights.billing-revenue-summary
  stages:
    - analytics
---

# Billing Insights Operator Guide
```

Canonical style notes for real managed docs:

- keep `doc_id` and `doc_type` as single-line concise strings
- keep `explains.*` lists free of duplicates and empty items
- use forward-slash repo-relative paths when a path-based `explains.*` list is
  present

Keep this template as a fenced example so validators do not treat it as real architecture metadata.
