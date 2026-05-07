---
layer: operating_system
artifact_type: spec
status: completed
parent_workstream: none
targets:
  - docs/intent/master-workstream-roadmap.md
  - docs/intent/workstream-coverage-and-progress-guide.md
  - docs/operating_system/skill-planning-dispatch.md
  - docs/operating_system/repo-governance.md
related_features: []
related_stages: []
---

# Roadmap-Level Completion Checklist Spec

## Triage

Layer: operating_system
Feature type: ADD
Summary: Add a lightweight roadmap-level completion checklist to the master workstream roadmap so coverage/completeness can be reviewed without turning the roadmap into an execution tracker.
Reasoning: The repo now has a more precise governance model for roadmap coverage, registered workstreams, bounded change threads, and progress tracking. The remaining small gap is a concise checklist in the master roadmap itself that helps reviewers ask whether the roadmap and registered workstream set are complete enough to reach the end goal.
Invariants:

- The checklist should track strategic completeness, not execution progress.
- The master roadmap must remain a coverage layer, not a task board.
- Detailed progress should stay in registered workstream docs and downstream specs/plans.
- The checklist should stay short and review-oriented.

Dependencies:

- `docs/intent/master-workstream-roadmap.md`
- `docs/intent/workstream-coverage-and-progress-guide.md`
- `docs/operating_system/skill-planning-dispatch.md`
- `docs/operating_system/repo-governance.md`

Affected stages:

- none directly

Affected features:

- none directly

Primary lens: cross-cutting

Affected docs:

- feature_source: none
- feature_yaml: none
- feature_lineage: none
- feature_history: none
- stage_source: none
- stage_contract: none
- feature_docs: none
- cross_cutting_docs: none
- operating_system_docs:
  - `docs/operating_system/skill-planning-dispatch.md`
  - `docs/operating_system/repo-governance.md`
- readme: none
- generated: none

Generated refresh required: no
Capability IDs: none
Invariant IDs: none
Spec needed: yes
Plan needed: yes

## Problem

The current system now distinguishes:

- roadmap coverage
- workstream progress
- execution tracking
- divergence review

But the master roadmap itself still lacks a compact built-in review aid for the
question:

`Is the current roadmap + registered workstream set complete enough to reach the intended end goal?`

Without that, reviewers have to reconstruct the review questions from the
larger governance guide every time.

## Goal

Add a short roadmap-level completion checklist to
`docs/intent/master-workstream-roadmap.md` that helps reviewers test strategic
coverage and completeness.

## Non-Goals

This spec does not add a task checklist for specs or plans.

This spec does not turn the roadmap into a progress tracker.

This spec does not add validator enforcement for the checklist yet.

This spec does not move workstream progress tracking out of registered
workstream docs.

## Recommended Design

Add a small section such as:

`## Roadmap-Level Completion Checklist`

The checklist should cover only strategic questions, for example:

- are the major delivery threads identified?
- does each major thread map to a registered workstream or to
  `operating_system` intentionally?
- are any major J2BDs still unowned?
- are there obvious duplicate or vague workstreams?
- are cross-workstream dependencies understood well enough?
- is the set complete enough to reach the intended end state?

## Guidance Updates

The surrounding guide/docs should make the split explicit:

- roadmap checklist = completeness review
- workstream docs = progress review
- specs/plans = execution progress

## Acceptance Criteria

- The master roadmap includes a short completion checklist.
- The checklist stays strategic and does not become a task tracker.
- The supporting docs reinforce that detailed progress belongs elsewhere.

## Risks

If the checklist is too detailed, it will drag execution tracking into the
roadmap.

If it is too vague, it will not help real reviews.

## Recommendation

Add the checklist now as a lightweight review aid. It fits the current setup
well and makes roadmap completeness easier to assess without changing the
ownership model of progress tracking.
