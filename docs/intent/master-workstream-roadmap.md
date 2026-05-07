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

#### Key Deliverables

- activate and maintain `starter-adoption-experience` as the registered
  workstream anchor
- keep bounded change threads under
  `docs/intent/workstreams/threads/starter-adoption-experience/`
- ensure downstream artifacts use canonical planning lineage and lifecycle
  validation flow

### Phase 2

#### Goal

Define the next durable product workstream expansion only after Phase 1 closure
evidence confirms stable lifecycle behavior.

#### Key Deliverables

- identify additional roadmap outcomes that are not already covered by
  `starter-adoption-experience`
- map each new durable outcome to either:
  - a new registered product workstream, or
  - explicit `operating_system` ownership when it is method work
- document unresolved scope decisions as explicit gaps before downstream plan
  expansion

### Phase 3

#### Goal

Consolidate multi-workstream governance and closure readiness once Phase 2
scope is concretely registered and bounded.

#### Key Deliverables

- verify roadmap-to-workstream coverage is complete for intended outcomes
- validate cross-workstream dependency and closure logic at roadmap level
- maintain explicit unresolved-gap tracking where scope remains intentionally
  undecided

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

