---
layer: change
artifact_type: spec
status: completed
template_id: detailed-specification
name: cos-canonical-work-coordination
targets:
  - .agents/skills/skill-chief-of-staff/SKILL.md
  - tests/test_skill_chief_of_staff.py
  - generated_agents/codex/skills/skill-chief-of-staff/SKILL.md
  - generated_agents/claude/skills/skill-chief-of-staff/SKILL.md
  - generated_agents/antigravity/skills/skill-chief-of-staff/SKILL.md
---

# CoS Canonical Work Coordination

## Goal and Problem

### Problem

- current behavior or opportunity: CoS activation is bound to approved Git-tracked plan execution, although its reusable behavior is coordination, synthesis, evidence reconciliation, blocker routing, and retirement.
- affected users, systems, or maintainers: native Codex lead controllers and maintainers of canonical CoS skill surfaces.
- evidence: `.agents/skills/skill-chief-of-staff/SKILL.md` requires an approved plan and makes Plan Binding precede Attention; `docs/operating_system/rules/git-tracked-coordination-rule.md` assigns workflow truth to plans and repository truth to Git.
- consequence of no change: repository audits and similar read-only coordination either overload one context or incorrectly enter plan execution semantics.

### Goal

- desired outcome: CoS coordinates canonical work without becoming owner of that work or creating a second coordination system.
- observable success: the skill supports existing plan-bound execution plus exact-commit repository advisory audits, while preserving current plan, Git, PR, verification, and runtime ownership boundaries.

## Required Outcomes

### Outcome: Canonical work binding

- affected actor or system: native Codex lead controller using CoS.
- required result: CoS binds to a deterministically identifiable canonical work item and records work identity, evidence authority, reference anchors, freshness boundary, acceptance authority, and coordination mode.
- success condition: plan-bound execution and repository-snapshot advisory audit have explicit binding rules; unsupported work types block or remain out of scope.

### Outcome: Separate coordination modes

- affected actor or system: CoS activation and delegated lane selection.
- required result: `advisory` permits inspect, synthesize, challenge, and recommend with no CoS mutation authority; `plan-bound-execution` preserves existing approved-plan execution ownership and bounded lane authority.
- success condition: no generic CoS `execute` authority exists and `skill-executing-plans` remains sole plan-execution owner.

### Outcome: Preserved distribution and contracts

- affected actor or system: canonical tests, generated adapters, and Starter build.
- required result: canonical skill tests cover new and preserved invariants; generated CoS mirrors derive from canonical source.
- success condition: focused tests, adapter sync, Starter validation, repository contracts, and diff checks pass.

## Design Analysis

### Change Summary

- baseline reference: current canonical CoS skill and existing plan-bound attention audit.
- added, changed, or removed behavior summary: add common Work Binding and repository-snapshot advisory binding; split common attention from plan-bound lane execution; retain deterministic Plan Binding unchanged.
- intentionally unchanged behavior: Herdr runtime gates, profile binding, lane ownership, review/integration lifecycle, retirement, Git/PR authority, and durable truth for plan-bound execution.
- affected maintained contracts: canonical CoS skill, focused CoS contract tests, generated CoS adapter surfaces.

### Current State and Evidence

| Question | Evidence | Source | Confidence | Specification implication |
|---|---|---|---|---|
| Who owns approved-plan execution? | `skill-executing-plans` owns execution; CoS is optional coordination specialization. | `.agents/skills/skill-executing-plans/SKILL.md`, `docs/operating_system/planning/planning-dispatch.md` | high | Keep plan-bound execution branch unchanged. |
| Who owns durable coordination truth? | Plan owns workflow state; Git owns repository state; runtime state is not recovery truth. | `docs/operating_system/rules/git-tracked-coordination-rule.md` | high | Advisory mode must not create durable CoS state. |
| Which CoS surfaces are canonical? | `.agents/skills` is canonical; generated agent surfaces derive through sync. | `scripts/sync_agent_adapters.py`, `tests/test_sync_agent_adapters.py` | high | Edit canonical skill and regenerate mirrors. |
| Which advisory target is bounded enough for V2? | Repository identity plus exact commit SHA gives stable read evidence. | reviewed verdict and current Git state | high | Implement repository-snapshot advisory audit only. |

### Prototype and Validation Evidence

- prototype reference or `Not applicable: no UI or behavior prototype is required for text-based skill contract changes`.
- UX approval or `Not applicable: no UX surface exists`.
- frozen prototype revision or reference or `Not applicable: no prototype exists`.
- design export evidence or `Not required: no visual design output exists`:
  - selected export method: `Not applicable`.
  - export task reference: `Not applicable`.
  - requested deliverable: `Not applicable`.
  - durable output identity: `Not applicable`.
  - independent review: `Not applicable: no design export exists`.
- validated scenarios and states: plan-bound execution, exact-commit repository audit, ambiguous binding, unresolved acceptance authority, mutation-risk advisory execution, generated-source drift.
- findings incorporated into approved behavior: remove universal immutable snapshot, replace generic authority enum with coordination modes, make acceptance authority resolution implicit, split common and plan-bound semantics, add pre-write adapter drift check.
- rejected alternatives: universal immutable target for evolving work; generic CoS execute authority; per-work-type adapter files; general CoS routing in planning dispatch; timers, hooks, and persistent coordination state.

### Scope

- included behavior: common Work Binding; existing deterministic Plan Binding; repository-snapshot advisory binding; advisory versus plan-bound-execution modes; acceptance-authority resolution; source-relative evidence freshness; risk-based advisory isolation; common versus mode-specific attention and output boundaries.
- affected boundaries: canonical CoS skill, focused CoS contract tests, generated CoS mirrors, Starter validation path.
- admissible cases: plan-bound execution under approved Git-tracked plan; repository read-only audit at exact commit SHA when two or more independent lanes materially benefit from synthesis.
- compatibility expectation: existing plan-bound invocation remains valid and retains current lane, runtime, review, integration, retirement, and durable-truth contracts.

### Non-Goals

- PR, release, incident, specification, research, or cross-repository adapters.
- generic CoS Git, PR, merge, release, publication, or execution authority.
- new workflow databases, registries, profiles, timers, schedulers, hooks, helper agents, or persistent CoS state.
- changes to `planning-dispatch.md`, `skill-executing-plans`, or Git coordination rules.

### Requirements and Behavioral Contract

#### Requirement: Work Binding

- trigger or actor: native Codex lead invokes CoS for canonical work.
- preconditions: target work identity and evidence authority can be resolved; coordination benefit exceeds ordinary execution overhead.
- required behavior: bind work identity, evidence authority, reference anchors, source-relative freshness boundary, acceptance authority, and coordination mode before lane selection.
- output or state change: return binding facts in current turn; do not create durable CoS state.
- failure behavior: return `BLOCKED` when identity, authority, or required evidence cannot be resolved.
- observable acceptance: skill text defines common binding and blocks ambiguous or unsupported work.

#### Requirement: Plan-bound execution

- trigger or actor: approved Git-tracked plan explicitly lists `skill-chief-of-staff` and requires sustained Codex main-agent coordination.
- preconditions: existing Plan Binding algorithm succeeds; runtime, profile, lane, and authority gates pass.
- required behavior: retain existing plan-specific Attention, Runtime Gates, Lane Contract, Review And Integration, Returns And Retirement, and Durable Truth semantics.
- output or state change: existing plan-bound outputs remain available; `skill-executing-plans` remains execution owner.
- failure behavior: preserve existing `BLOCKED`, execution status, review verdict, and retirement semantics.
- observable acceptance: existing focused tests remain green and plan-bound sections remain clearly mode-scoped.

#### Requirement: Repository-snapshot advisory audit

- trigger or actor: native Codex lead explicitly invokes advisory CoS for repository audit.
- preconditions: repository identity, exact commit SHA, scoped target, and evidence authority resolve; no plan task is required.
- required behavior: inspect independent bounded lanes at the bound commit, synthesize and challenge returns, and recommend next action.
- output or state change: return advisory recommendation and evidence freshness; external canonical owner accepts recommendation.
- failure behavior: return `BLOCKED` for unresolved binding or acceptance authority; return `INSPECT` for evidence requiring judgment; never mutate repository or workflow state from CoS.
- observable acceptance: skill distinguishes advisory audit from plan-bound task selection and defines exact-commit binding.

#### Requirement: Acceptance authority and isolation

- trigger or actor: CoS prepares an acceptance-sensitive recommendation or advisory lane.
- preconditions: canonical owner or existing repository/workflow authority is discoverable.
- required behavior: resolve authority in order `explicit current-work owner`, `canonical work owner`, `existing repository/workflow authority`; use `BLOCKED` if unresolved. Use no worktree for remote/immutable inspection; use clean isolation or pre/post Git proof when local tools can mutate.
- output or state change: report authority and isolation decision; CoS itself gains no mutation authority.
- failure behavior: stop before mutation-risk dispatch when isolation or authority cannot be established.
- observable acceptance: skill includes both resolution order and risk-based isolation rule.

## Constraints and Alternatives

- constraint: plan workflow state and Git repository state already have authoritative owners.
- alternative: add a generic CoS execution authority.
  - benefit: simpler wording.
  - trade-off: blurs coordination and execution ownership.
  - reason accepted or rejected: rejected; use two coordination modes.
- alternative: create one adapter file per work type.
  - benefit: explicit per-type machinery.
  - trade-off: duplicates protocol and creates maintenance surface.
  - reason accepted or rejected: rejected; use one common contract and only two V2 modes.
- alternative: activate CoS for this self-modification plan.
  - benefit: dogfoods CoS.
  - trade-off: violates CoS activation gate and adds unnecessary orchestration.
  - reason accepted or rejected: rejected; ordinary plan execution modifies CoS.

## Design Decisions

### Decision: Common binding with preserved Plan Binding

- context: plan-bound execution already has tested deterministic binding semantics.
- selected approach: add `## Work Binding`, then retain `## Plan Binding` as a mode-specific section and add repository-snapshot advisory binding beside it.
- rationale: broadens use without replacing proven behavior.
- alternatives considered: rename Plan Binding to Work Binding; rejected because tests and plan-specific assumptions would drift.
- accepted trade-offs: repository audit is exact-commit bounded; evolving work types wait for later design.
- affected owners and boundaries: CoS owns coordination protocol; plans, Git, GitHub, verification, and runtime owners remain unchanged.

### Decision: Advisory and plan-bound-execution modes

- context: generic execute authority would grant the wrong ownership signal.
- selected approach: `advisory` and `plan-bound-execution` only.
- rationale: makes mutation boundary explicit and preserves existing plan authority.
- alternatives considered: `inspect | recommend | execute`; rejected because `execute` is not CoS authority.
- accepted trade-offs: future modes require a later specification.
- affected owners and boundaries: advisory recommendations remain external-owner decisions; plan execution remains `skill-executing-plans`.

### Compatibility, Migration, and Risk

- old behavior: every CoS invocation binds to approved Git-tracked plan execution.
- new behavior: CoS may also bind to exact-commit repository advisory audit; plan-bound behavior remains unchanged.
- compatibility boundary: only native Codex lead can activate CoS; delegated lane agents cannot reactivate it.
- migration or backfill: no migration; existing plan artifacts and generated surfaces remain valid after regeneration.
- rollout and rollback: update canonical skill and tests, regenerate mirrors; revert canonical change and regenerate to roll back.
- deprecation or consumer impact: no existing executor or plan field changes.
- risk:
  - mitigation: exact-commit advisory binding, external acceptance authority, no mutation authority, focused contract tests, generated drift preflight.

## Invariants and Edge Cases

### Invariants

- CoS coordinates work; it does not own work execution or canonical work truth.
- `skill-executing-plans` remains sole approved-plan execution owner.
- Plan Binding resolution order and blocking semantics remain unchanged.
- Advisory mode cannot mutate plan, Git, PR, review, release, or durable coordination state.
- CoS does not create adapter files, registries, timers, hooks, profiles, or persistent state.
- Generated surfaces derive from canonical `.agents/skills` sources.
- Acceptance authority is external to CoS.

### Edge Cases

- empty or minimal input: no canonical target or no independent coordination benefit uses ordinary execution or returns `BLOCKED` when binding is required.
- normal and large input: advisory audit stays scoped to declared repository target and exact commit; no unrelated repository scan is implied.
- duplicate, missing, malformed, or unsupported data: ambiguous identity, missing authority, or unsupported work type returns `BLOCKED`.
- retry, cancellation, timeout, partial failure, or concurrency: advisory mode reports current-turn evidence; it creates no retry state; plan-bound behavior keeps existing runtime and lane rules.
- migration or mixed-version state: generated mirrors are regenerated after canonical source change; stale adapter output fails sync check.
- generated-source consistency: canonical source edits precede adapter sync; unrelated pre-existing generated drift blocks mutating sync.
- security or accessibility boundary: no new external write authority or credential handling is introduced.

## Validation Plan

### Backend Verification Claims

- direct boundary: `Not applicable: skill and documentation contract change has no backend boundary`.
- important success and failure behavior: focused source-contract tests cover valid modes, preserved Plan Binding, and blocking boundaries.
- final state or side effects: generated mirrors match canonical source; no unrelated generated paths change.
- rollback, retry, duplicate, or idempotency behavior: `Not applicable: no runtime state or mutation is introduced`.
- canonical contract and conformance proof, or `Not applicable: no backend contract exists`: canonical skill tests and adapter sync.
- real dependencies requiring proof, or `Not applicable: no runtime dependency is changed`: no real dependency changes.
- representative-operation trace mechanism, or `Not applicable: no backend operation exists`: no backend operation exists.
- performance claim and threshold, or `Not applicable: no performance claim`: no performance claim.

### Acceptance Criterion: Canonical contract is mode-separated

- setup or precondition: canonical CoS skill is inspected.
- action: evaluate Work Binding, advisory, and plan-bound sections.
- expected result: common attention rules are separate from plan-bound task/lane rules; exact Plan Binding semantics remain.
- failure condition: advisory audit requires plan binding or generic CoS execution authority appears.
- proof method: focused `tests/test_skill_chief_of_staff.py` assertions and source inspection.
- expected evidence: focused test passes and canonical section order matches contract.

### Acceptance Criterion: Distribution remains aligned

- setup or precondition: canonical skill changed.
- action: run adapter sync check, Starter build/validation, repository contract validation, and diff check.
- expected result: generated CoS mirrors match canonical source and no unrelated generated surfaces change.
- failure condition: pre-existing unrelated drift, generated mismatch, validator failure, or out-of-scope path change.
- proof method: named repository commands in implementation plan.
- expected evidence: all commands exit 0 and changed-file scope is declared.

## Completion Criteria

Specification is complete when:

1. common Work Binding and two mode contracts are explicit
2. existing Plan Binding and plan-bound execution ownership are preserved
3. repository advisory audit has exact-commit binding and no mutation authority
4. acceptance authority and risk-based isolation are defined
5. unsupported future work types and new state surfaces are excluded
6. implementation plan can name exact files, tasks, commands, and proof

Implementation verification (2026-08-30): focused CoS tests, planning and
template validators, adapter sync and runtime-drift checks, Starter build and
validation, repository contract validation, and `git diff --check` passed.
