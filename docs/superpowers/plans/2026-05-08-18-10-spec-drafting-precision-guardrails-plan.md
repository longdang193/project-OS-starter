---
layer: operating_system
artifact_type: plan
status: proposed
template_id: implementation-plan
name: spec-drafting-precision-guardrails
parent_workstream: none
parent_spec: docs/superpowers/specs/spec-drafting-precision-guardrails-spec.md
targets:
  - docs/operating_system/templates/detailed-specification-template.md
  - .agents/skills/skill-brainstorming/SKILL.md
  - .agents/skills/skill-plan-document-reviewer/SKILL.md
  - docs/operating_system/planning/planning-dispatch.md
related_features: []
related_stages: []
---

## Goal

Patch operating-system planning guidance so future detailed specs do not stop at file/wave naming and instead must state executable contract edges: doc-update timing, fallback behavior for missing ambient context, span/ownership hierarchy, and mode-specific invariants.

## Key Deliverables

### Deliverable 1: Spec-authoring guardrails tightened at source

Update canonical spec-authoring surfaces so detailed-spec drafting guidance explicitly requires authors to classify named doc targets as required-now vs deferred vs conditional, define fallback behavior when runtime context may be absent, and state hierarchy invariants when orchestration or observability lineage matters.

### Deliverable 2: Review and routing surfaces catch underspecified contracts

Update reviewer/routing guidance so plan or spec review can flag missing contract edges before implementation planning starts, especially for cross-cutting observability or orchestration work where mode-specific behavior and degraded-safe fallback rules affect execution safety.

## Task/Wave Breakdown

### task 1: Confirm owning surfaces and bounded patch scope

Re-read current operating-system sources that control spec drafting and review behavior, then lock exact patch scope to canonical sources instead of generated outputs. Verify whether `docs/operating_system/templates/detailed-specification-template.md` is sufficient alone or whether `planning-dispatch.md`, `skill-brainstorming`, and `skill-plan-document-reviewer` also need aligned wording so the same contract expectations appear at draft time and review time.

Verification intent:
- confirm target list stays source-first
- confirm no generated adapter outputs are edited directly
- confirm operating-system lineage with `parent_workstream: none` remains intentional

### task 2: Add missing contract-edge prompts to spec-authoring guidance

Patch spec-authoring guidance to require explicit answers for:
- doc target timing: update now, defer, or conditional-on-surface-change
- ambient-context fallback semantics: success path, missing-context path, invalid-context path, and lineage claims allowed in fallback mode
- hierarchy invariants: exact parent/child/sibling expectations for named spans, jobs, or orchestration units
- mode matrix: behavior/topology differences across supported execution modes when mode changes execution shape
- defer-now gate: decisions that materially shape implementation or verification must be resolved in the spec, not left implicit

Touched surfaces should prefer minimal canonical updates, likely centered on `detailed-specification-template.md` plus any nearby drafting guidance text needed to make these prompts discoverable to spec authors.

Verification intent:
- source review shows new prompts are explicit, not implied
- wording remains generic enough for non-observability specs while still covering observability/orchestration edge cases

### task 3: Align reviewer and routing guidance with new precision rules

Patch review/routing surfaces so missing contract edges are caught before plan authoring or execution. At minimum, review whether `skill-plan-document-reviewer/SKILL.md` should add checks for deferred-but-blocking decisions, missing fallback semantics, and missing mode-specific hierarchy rules. If routing guidance also needs reinforcement, update `planning-dispatch.md` so cross-cutting specs must name behavior contracts, not only files and waves.

Verification intent:
- reviewer checklist can explicitly flag ambiguities like doc-scope drift, fallback ambiguity, or mode-topology drift
- routing guidance remains concise and does not duplicate full template text unnecessarily

### task 4: Validate repo consistency and handoff readiness

Run bounded validation appropriate for operating-system doc/skill changes. Confirm edited sources remain structurally valid and that plan consumers can use updated guidance without guessing. If any generated/runtime instruction surfaces depend on changed skill sources, identify whether sync is required now or deferred until implementation phase based on actual touched files.

Verification intent:
- repo validation passes for changed docs/skills
- changed guidance is internally consistent across template, drafting skill, and review skill
- follow-up execution can start from updated plan/spec process without re-deciding these guardrails

## Verification

- review edited files for explicit contract-edge prompts and consistent terminology
- .\.venv\Scripts\python.exe scripts/validate_repo_contracts.py --fast

## Completion Criteria

A plan item is considered complete when:

1. all Key Deliverables are satisfied
2. all downstream/child items are terminal
3. every child item is `completed` or `dropped`

Canonical source-of-truth:

<LINK>
- `docs/operating_system/governance/repo-governance.md`
- `scripts/validate_planning_lifecycle.py`
</LINK>
