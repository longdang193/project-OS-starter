---
layer: operating_system
artifact_type: plan
status: proposed
template_id: implementation-plan
name: session-handoff-layer
parent_workstream: none
targets:
  - .agents/skills/skill-executing-plans/SKILL.md
  - docs/operating_system/prompt_templates/implementation-next-action-gate-prompt.md
  - docs/operating_system/prompt_templates/
  - docs/operating_system/templates/
  - docs/operating_system/governance/repo-governance.md
  - docs/operating_system/agent_memory/failure-ledger.md
  - docs/superpowers/plans/
related_features: []
related_stages: []
---

## Goal

Add repo-governed session handoff layer so long-running execution can safely move to a new session without losing relevant context, while keeping source-of-truth discipline and avoiding raw-log-first resume behavior.

## Key Deliverables

### Session handoff contract for execution workflows

Define a standard execution context pack that captures bounded scope, canonical inputs, current task truth, verification state, exact next action, blockers, and optional deep-context references. The contract must make the context pack primary handoff artifact and keep source files as authoritative truth.

### Execution skill and prompt alignment against narration-only stalls

Update execution guidance so agents must maintain the context pack during long work, refresh both plan state and handoff state as progress lands, and prefer concrete action over status-only narration. Related prompts must use precise wording that tells agents to keep plan and handoff artifacts current during execution, not only at end-of-session handoff. The next-action prompt must align with this by selecting and executing smallest concrete next step or surfacing explicit blocker.

### Optional raw session log integration with guardrails

Define how Gemini conversation logs such as `.gemini/antigravity/brain/<conversation-id>/.system_generated/logs/overview.txt` may be referenced as optional deep context, without making them mandatory, primary, or stronger than current repo source.

## Task/Wave Breakdown

### Task 1: Define session handoff architecture and artifact shape

**Purpose:**
- Establish operating-system level contract for resumable session handoff.
- Bound what must live in context pack versus reusable agent memory versus raw session logs.

**Files:**
- Inspect: `docs/operating_system/planning/planning-dispatch.md`
- Inspect: `docs/operating_system/lifecycle/doc-system-lifecycle.md`
- Inspect: `docs/operating_system/governance/repo-governance.md`
- Modify: `docs/operating_system/governance/repo-governance.md`
- Modify: `docs/operating_system/templates/`
- Verify: `repo_config/planning_artifact_schema.yaml`

**Preconditions:**
- Operating-system routing confirmed.
- Scope remains bounded to handoff protocol, not generic memory system redesign.

**Steps:**
- [ ] Step 1: Draft compact triage summary for session handoff work and preserve `layer: operating_system`, `Feature type: ADD`, `Affected features: none`, `Plan needed: yes` assumptions in implementation notes or linked execution artifacts.
- [ ] Step 2: Define canonical execution context pack shape, including required fields for objective, bounded scope, canonical inputs, task status, files changed, verification state, open problems, next exact action, and resume prompt.
- [ ] Step 3: Decide canonical storage guidance for context pack and distinguish temporary handoff artifact usage from durable `docs/operating_system/agent_memory/*` usage.
- [ ] Step 4: Define optional deep-context block for conversation id and `overview.txt` path, including consult-only conditions and conflict-resolution rule favoring current source.

**Verification:**
- [ ] Handoff contract names exact owning surfaces and does not invent product feature contracts.
- [ ] Context-pack design preserves source-first resume order and avoids raw-log-primary behavior.

**Exit Criteria:**
- Session handoff architecture is documented clearly enough that downstream skill edits can implement it without re-deciding ownership or data shape.

### Task 2: Update execution skill and next-action prompt for resumable handoff

**Purpose:**
- Encode handoff maintenance and anti-stall behavior directly into execution workflow surfaces.

**Files:**
- Inspect: `.agents/skills/skill-executing-plans/SKILL.md`
- Inspect: `docs/operating_system/prompt_templates/implementation-next-action-gate-prompt.md`
- Inspect: `docs/operating_system/prompt_templates/`
- Modify: `.agents/skills/skill-executing-plans/SKILL.md`
- Modify: `docs/operating_system/prompt_templates/implementation-next-action-gate-prompt.md`
- Modify: `docs/operating_system/prompt_templates/`
- Verify: `.agents/skills/skill-executing-plans/SKILL.md`

**Preconditions:**
- Task 1 complete.
- Existing execution skill anti-stall gap confirmed.

**Steps:**
- [ ] Step 1: Add session continuation protocol to `skill-executing-plans`, including when to create or refresh context pack and what minimum contents are required before handoff.
- [ ] Step 2: Add explicit resume-order rule: context pack first, referenced source second, optional raw session log only for ambiguity or audit trail.
- [ ] Step 3: Strengthen anti-stall guidance so execution turns must land concrete work, explicit blocker, or refreshed handoff artifact instead of only narrating intent.
- [ ] Step 4: Update `implementation-next-action-gate-prompt.md` so next-action selection requires smallest concrete execution step now, explicit blocker when safe execution cannot proceed, and prompt wording that requires the agent to refresh plan state and handoff state as progress lands.
- [ ] Step 5: Audit related execution prompts under `docs/operating_system/prompt_templates/` and tighten wording where needed so they say agents must keep plans and handoff artifacts updated throughout the process rather than only during closeout.

**Verification:**
- [ ] Skill text forbids vague “next I will ...” endings when no blocker exists.
- [ ] Prompt text no longer permits advice-only next-action output as terminal behavior.
- [ ] Related prompt wording clearly requires plan/handoff updates during execution progress, not only at end-of-session handoff.

**Exit Criteria:**
- Execution workflow surfaces encode resumable handoff and anti-stall behavior consistently.

### Task 3: Add template, examples, and optional memory/failure guidance

**Purpose:**
- Make handoff protocol easy to use repeatedly and easy to recover in new sessions.

**Files:**
- Inspect: `docs/operating_system/agent_memory/failure-ledger.md`
- Modify: `docs/operating_system/templates/`
- Modify: `docs/operating_system/agent_memory/failure-ledger.md`
- Verify: `docs/operating_system/templates/`

**Preconditions:**
- Task 2 complete.
- Final template home under `docs/operating_system/templates/` or equivalent operating-system-owned path chosen in Task 1.

**Steps:**
- [ ] Step 1: Add reusable execution context pack template with required headings and concise field guidance.
- [ ] Step 2: Include optional deep-context fields for `conversation_id`, `overview_log`, `consult_if`, and notable historical pivots rather than embedding raw session text.
- [ ] Step 3: If repeated stall pattern qualifies as reusable lesson, add failure-ledger entry describing narration-only execution drift in long sessions and prevention through context-pack + anti-stall rules.
- [ ] Step 4: Ensure template language keeps artifacts compact, source-linked, and suitable for direct paste into new-session resume prompt.

**Verification:**
- [ ] Template is sufficient for new-session resume without prior chat transcript.
- [ ] Raw session log remains optional reference, not required payload.

**Exit Criteria:**
- Repo has concrete template and memory guidance supporting repeated use of session handoff protocol.

### Task 4: Validate governance alignment and handoff workflow closure

**Purpose:**
- Confirm session handoff layer fits repo governance, private/public boundary rules, and downstream starter behavior.

**Files:**
- Inspect: `docs/operating_system/governance/repo-governance.md`
- Inspect: `docs/operating_system/lifecycle/doc-system-lifecycle.md`
- Modify: `docs/operating_system/governance/repo-governance.md`
- Verify: `docs/operating_system/`

**Preconditions:**
- Tasks 1 through 3 complete.
- Changed docs and skills identify any shipped starter dependency closures they introduce.

**Steps:**
- [ ] Step 1: Audit whether handoff protocol needs brief governance note on primary handoff artifact, optional private raw log references, and source-first conflict resolution.
- [ ] Step 2: Audit whether workflow docs that mention execution or closeout need small updates so session handoff becomes part of normal long-lane discipline.
- [ ] Step 3: Confirm no new public-safe promise accidentally depends on private-only operating-system paths beyond existing starter/private boundary expectations.
- [ ] Step 4: Prepare execution notes for follow-on implementation or direct handoff to `skill-executing-plans`.

**Verification:**
- [ ] Governance language remains operating-system scoped and does not blur into feature lifecycle surfaces.
- [ ] Any new template or workflow references resolve to shipped/private-valid paths already governed by repo rules.

**Exit Criteria:**
- Session handoff layer is ready for bounded implementation without unresolved governance ambiguity.

## Verification

- Review changed plan targets against `docs/operating_system/templates/implementation-plan-template.md` and `repo_config/planning_artifact_schema.yaml` for structure and metadata compliance.
- Run relevant repo validation/check commands after implementation lands, likely including:
  - `.\.venv\Scripts\python.exe scripts/validate_repo_contracts.py --fast`
  - any adapter sync/verify flow required if shipped skill surfaces or generated runtime instruction files change
- Re-read updated `skill-executing-plans`, prompt/template text, and governance notes to confirm resume order is: context pack -> source files -> optional raw session log.
- Re-read updated prompt wording to confirm it explicitly requires agents to update plan state and handoff state along the execution process, not only at closeout or session handoff.

## Completion Criteria

This plan is complete when:

1. all Key Deliverables are satisfied
2. downstream implementation updates define and ship session handoff contract, template, and anti-stall integration
3. every child item is `completed` or `dropped`
