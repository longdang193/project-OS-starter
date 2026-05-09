---
template_id: master-workstream-roadmap
status: active
---

# Master Workstream Roadmap

## Goal

Define the durable workstream roadmap that preserves intent-to-execution
traceability and keeps product workstream scope separate from
`operating_system` method work.

## Key Deliverables

- phase-structured roadmap with per-phase ownership boundaries
- explicit mapping from roadmap phases to registered workstreams
- clear downstream planning lineage expectations for specs/plans

## Phase Structure

### Phase 1

#### Goal

Establish the starter adoption planning lifecycle foundation with one explicit,
traceable product workstream and bounded thread execution.

#### Enables

- activation of bounded thread execution under `starter-adoption-experience`
- truthful downstream spec and plan lineage using canonical lifecycle validation flow

#### Exit Criteria

- `starter-adoption-experience` remains the active registered workstream anchor
- bounded change threads remain scoped under `docs/intent/workstreams/threads/starter-adoption-experience/`
- downstream artifacts are using canonical planning lineage and lifecycle validation flow

### Phase 2

#### Goal

Define the next durable product workstream expansion only after Phase 1 closure
evidence confirms stable lifecycle behavior.

#### Depends On

- Phase 1

#### Enables

- new registered product workstreams for durable roadmap outcomes
- explicit `operating_system` ownership classification for method work

#### Exit Criteria

- additional roadmap outcomes not already covered by `starter-adoption-experience` are identified
- each new durable outcome is mapped to either a registered product workstream or explicit `operating_system` ownership
- unresolved scope decisions are documented as explicit gaps before downstream plan expansion

### Phase 3

#### Goal

Consolidate multi-workstream governance and closure readiness once Phase 2
scope is concretely registered and bounded.

#### Depends On

- Phase 2

#### Exit Criteria

- roadmap-to-workstream coverage is complete for intended outcomes
- cross-workstream dependency and closure logic is validated at roadmap level
- unresolved gaps remain explicitly tracked where scope is intentionally undecided

## Workstream Index

- `starter-adoption-experience` - starter planning lifecycle and downstream
  reconciliation governance foundation

## Completion Criteria

A roadmap item is considered complete when:

1. all Key Deliverables are satisfied
2. all downstream/child items are terminal
3. every child item is `completed` or `dropped`

Canonical source-of-truth:

- `docs/operating_system/governance/repo-governance.md`
- `scripts/validate_planning_lifecycle.py`

