---
layer: operating_system
artifact_type: spec
status: completed
parent_workstream: none
targets:
  - docs/operating_system/prompt_templates/
  - docs/operating_system/skill-planning-dispatch.md
  - docs/operating_system/repo-governance.md
  - docs/intent/master-workstream-roadmap.md
  - docs/intent/workstreams/
related_features: []
related_stages: []
---

# Roadmap Vs Execution Divergence Prompt Spec

## Triage

Layer: operating_system
Feature type: ADD
Summary: Add a dedicated prompt template for checking divergence between the master roadmap or a workstream and the specs, plans, and execution completed so far.
Reasoning: The current prompt pack has prompts for roadmap gaps, workstream-fit review, and generic repo drift, but it does not yet have a prompt for comparing upstream planning intent against downstream execution artifacts and calling out where the repo has drifted, stalled, or over-expanded.
Invariants:

- The prompt should review alignment between upstream planning sources and downstream execution artifacts.
- It should stay distinct from generic metadata drift checks.
- It should support both roadmap-level and single-workstream reviews.
- It should preserve the distinction between product workstreams and `operating_system`.
- It should remain short and copyable.

Dependencies:

- `docs/operating_system/prompt_templates/`
- `docs/operating_system/skill-planning-dispatch.md`
- `docs/operating_system/repo-governance.md`
- `docs/intent/master-workstream-roadmap.md`
- `docs/intent/workstreams/`

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
  - `docs/operating_system/prompt_templates/`
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

The repo can now:

- define intent
- define a master roadmap
- register real workstreams
- draft specs and plans with `parent_workstream`
- validate some structural alignment

But it still lacks a prompt for the review question:

`Does the work we have actually done still match the roadmap or workstream we said we were following?`

Nearby prompts do adjacent jobs:

- `roadmap-gap-prompt.md` asks whether the roadmap is missing a durable thread
- `workstream-alignment-review-prompt.md` checks whether a proposed change fits
  a workstream
- `validate-or-drift-prompt.md` checks repo drift and validation gaps

What is missing is the retrospective alignment review:

- roadmap intent vs current specs/plans
- workstream intent vs executed changes so far
- missing execution under an intended thread
- off-roadmap execution
- stale or orphaned specs/plans
- operating-system work mixed into product workstreams, or vice versa

## Goal

Add a dedicated prompt for:

`master roadmap or workstream -> compare against downstream specs/plans/execution so far -> report divergence and next moves`

## Non-Goals

This spec does not add new validator enforcement.

This spec does not replace roadmap-gap or workstream-fit prompts.

This spec does not turn the roadmap into a progress tracker.

This spec does not require every execution review to become a formal audit.

## Recommended Design

Add a new prompt template:

`docs/operating_system/prompt_templates/roadmap-vs-execution-divergence-prompt.md`

### Suggested Prompt Shape

The prompt should collect:

- whether the review is roadmap-wide or a single workstream
- roadmap/workstream sources in scope
- known specs, plans, or executed changes to compare
- whether the concern is:
  - missing progress
  - drift from intent
  - off-roadmap work
  - stale artifacts
  - mixed workstream vs operating-system boundaries

### Suggested Prompt Responsibilities

The prompt should ask the agent to:

1. read the relevant roadmap or workstream sources first
2. compare them against downstream specs, plans, and executed work so far
3. separate true divergence from healthy evolution
4. identify missing execution, off-roadmap execution, stale artifacts, and
   misclassified work
5. recommend the next correction step

## Suggested Expected Output

The prompt should aim for:

- divergence findings
- explicit alignment vs misalignment calls
- recommendations such as:
  - refine roadmap/workstream docs
  - retire stale plans/specs
  - reclassify work into `operating_system`
  - draft the next spec/plan under the correct thread

## Proposed README / Guidance Updates

The prompt-pack README should describe this as the right prompt when a user
wants to compare planning intent against execution completed so far.

Planning/governance docs should lightly note that this is a planning-alignment
review, not just metadata drift detection.

## Acceptance Criteria

- A dedicated roadmap-vs-execution divergence prompt exists.
- The prompt clearly distinguishes planning-alignment review from generic drift
  checks.
- The prompt works for both roadmap-wide review and single-workstream review.
- The prompt-pack README and related docs point users to it appropriately.

## Risks

If this overlaps too much with roadmap-gap review, users may be unsure which
one to use.

If it overlaps too much with validate-or-drift, it may collapse planning drift
into metadata drift again.

If the prompt implies the roadmap must predict every executed detail, it will
become too rigid.

## Recommendation

Add the dedicated divergence prompt. The repo is now mature enough to benefit
from checking not only whether planning artifacts exist, but whether execution
still follows the master roadmap and registered workstreams in a healthy way.
