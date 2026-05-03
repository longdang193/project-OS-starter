---
layer: operating_system
artifact_type: spec
status: proposed
parent_workstream: none
parent_thread: starter-adoption-experience.prompt-template-metadata-and-validation
---

# Per-Workstream Lifecycle Coverage And Bootstrap Linkages Spec

## Goal

Make planning drift less likely by defining explicit lifecycle coverage
requirements per active/completed workstream.

## Requirements

1. Each active/completed workstream must maintain all execution-map types:
   - `complete_spec_set`
   - `spec_authoring`
   - `implementation_execution`
2. Each active/completed workstream must have at least one thread-linked spec
   and at least one thread-linked plan.
3. If full artifacts are not ready yet, teams must create bounded bootstrap
   linkage artifacts instead of leaving lineage empty.

## Bootstrap Linkage Pattern

When needed, bootstrap with:

- one thread-linked bootstrap spec
- one thread-linked bootstrap plan referencing that spec

This keeps lifecycle validators and planning lineage coherent while preserving
incremental delivery.
