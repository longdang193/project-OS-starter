# Execution Maps

This folder holds orchestration artifacts for a set of approved specs.

Use an execution map when one thread or workstream has already produced a spec
set and the next question is:

- what depends on what
- what can run in parallel
- what should run in sequence
- how the bounded plans should be split

Execution maps sit here in the ladder:

`thread set -> spec set -> execution map -> implementation plans -> execution`

Execution maps are:

- human-authored orchestration decisions
- cross-spec dependency and lane maps
- plan-breakdown guidance

Execution maps are not:

- design specs
- implementation plans
- generated lineage registries

Suggested frontmatter:

```yaml
---
layer: change
artifact_type: execution_map
status: proposed | active | completed | superseded
parent_workstream: <id> | none
threads:
  - <thread-id>
specs:
  - docs/superpowers/specs/<file>.md
---
```

Suggested sections:

- scope
- dependency graph
- execution waves
- parallel lanes
- shared-surface risks
- recommended plan breakdown
- orchestration notes

If you want the structural lineage view, use
`docs/generated/planning_lineage.yaml`.
If you want the human execution decision about ordering and parallelism, use an
execution map.
