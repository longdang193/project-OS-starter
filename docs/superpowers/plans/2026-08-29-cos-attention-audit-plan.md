---
layer: change
artifact_type: plan
template_id: implementation-plan
contract_version: "1"
status: completed
name: cos-attention-audit
targets:
  - .agents/skills/skill-chief-of-staff/SKILL.md
  - tests/test_skill_chief_of_staff.py
  - generated_agents/codex/skills/skill-chief-of-staff/SKILL.md
  - generated_agents/claude/skills/skill-chief-of-staff/SKILL.md
  - generated_agents/antigravity/skills/skill-chief-of-staff/SKILL.md
---

# CoS Attention Audit

## Goal

Add a minimal read-only Attention Audit to the canonical Chief of Staff skill.
Run it at the start of each explicit CoS turn when approved coordinated work
is outstanding. Keep plan, Git, GitHub, and Herdr ownership unchanged.

V1 provides opportunistic audit-on-CoS-turn, not wall-clock periodic
monitoring. Detecting problems while no CoS turn occurs requires a future
separately verified wake capability.

Do not add a timer, scheduler, daemon, hook integration, profile, helper LLM,
heartbeat database, persistent state, or runtime script. V1 has no autonomous
wake mechanism. A future verified runtime wake may invoke another ordinary CoS
turn, but it does not own coordination.

## Review Findings And Decisions

### [P1] Runtime trigger must be explicit-turn only

The revised verdict correctly removes the unowned timer. Current CoS attention
is pull-based and the repository defines no CoS wake loop. The implementation
must therefore attach the audit to an existing explicit CoS turn only. Future
polling or subscription support remains conditional runtime capability, not v1
scope.

Evidence: `.agents/skills/skill-chief-of-staff/SKILL.md:102-113`.

### [P1] Audit must preserve blocking semantics

The earlier verdict over-classified every failed proof as `BLOCKED`. The
verification contract returns introduced or unknown implementation failures to
execution/debugging. The audit consumes canonical owner semantics instead of
recreating a failure taxonomy: hard stops use `BLOCKED`; evidence needing CoS
judgment or an approved in-scope correction uses `INSPECT`.

Evidence: `.agents/skills/skill-verification-before-completion/SKILL.md:159-167`,
`.agents/skills/skill-reviewing-pull-requests/SKILL.md:25-30`.

### [P2] Audit outcomes are not workflow state

`NO_ACTION | INSPECT | BLOCKED` is an attention-result vocabulary. It must not
write task state or replace execution, review, or plan statuses. `BLOCKED`
reports an already-supported blocking condition; the audit remains read-only.

Evidence: `docs/operating_system/rules/git-tracked-coordination-rule.md:14-26`,
`docs/operating_system/rules/git-tracked-coordination-rule.md:48-54`.

### [P2] Do not require evidence-age state

The audit reports current evidence and naturally available identity/freshness
facts. It does not require `last_seen_at`, `last_check_at`, or prior snapshots.
This preserves plan-plus-Git recovery and avoids a second coordination state.

Evidence: `docs/operating_system/rules/git-tracked-coordination-rule.md:21-24`,
`.agents/skills/skill-chief-of-staff/SKILL.md:183-189`.

### [P2] Missing Herdr presence is phase-aware

An active task without a Herdr agent is not automatically an error. The task
may be pending launch or intentionally retired. Absence is actionable only when
current plan or current-turn evidence establishes that a live bound main agent
is expected. An unreconciled lane identity is a canonical hard stop.

Evidence: `.agents/skills/skill-chief-of-staff/SKILL.md:72-105`,
`.agents/skills/skill-chief-of-staff/SKILL.md:115-120`.

### [P3] External hook remains out of scope

`C:\tmp\LightRSI-review-569eff0dbafb4e928733842163dc78f4\components\adapters\codex\dist\tokenpilot-codex-hook.cmd`
is outside this repository and is not a CoS authority surface. No hook or
LightRSI session state is required for V1.

## Implementation Outcomes

### Canonical CoS audit contract

Extend `.agents/skills/skill-chief-of-staff/SKILL.md` with one Attention Audit
section placed after plan binding/attention rules and before next-action
selection. The section defines explicit-turn triggering, bounded inputs,
read-only behavior, canonical-owner status consumption, and output fields.

### Focused contract and generated-surface proof

Extend the existing CoS skill contract tests. Regenerate all provider adapters
from canonical source and verify Starter-compatible generated surfaces without
editing generated files directly.

## Execution Approach

- Mode: `inline sequential`
- Coordination: `git-tracked`
- Default task executor: `codex`
- Required skills: `skill-code-standards`, `skill-writing-skills`, `skill-executing-plans`, `skill-verification-before-completion`
- Isolation: `current workspace`; preserve existing untracked changes
- Commit policy: `no commits during execution`
- Preauthorized local actions: edit declared canonical source and focused tests; regenerate declared adapters; run declared local validators and tests; rebuild disposable Starter output
- User-approval actions: commit, push, merge, publication, destructive cleanup, discard, external hook/runtime changes
- Parallel ownership: none; canonical source, tests, generation, and validation are sequential
- Sequential fallback: complete canonical source, then tests, then adapter sync and final validation

## Coordination State

- Coordination owner: `single lead controller`
- Coordination schema: `2`
- Branch: `main`
- Base commit: `eb385e2fc9b1ed14cf2cf86ee2bf05010c492e9d`
- Expected workspace: preserve untracked `.playwright-mcp/`, `db/`, and `out/`; do not include them in task scope
- Next action: await authorized branch disposition
- Blockers: none

| Task | State | Workspace | Executor | Depends On | Required Proof | Evidence |
| --- | --- | --- | --- | --- | --- | --- |
| Task 1 | `completed` | current | `codex` | none | red focused CoS contract tests | 1 failed, 7 passed (expected RED) |
| Task 2 | `completed` | current | `codex` | Task 1 | focused CoS contract tests pass | 8 passed |
| Task 3 | `completed` | current | `codex` | Task 2 | adapter sync, Starter rebuild, validators, diff check | sync clean; repo contracts, Starter validation, focused tests, and diff check passed |

## Task Breakdown

### Task 1: Add RED Attention Audit contract tests

**Purpose:**
- Define failing contract checks before changing the CoS skill.

**Task Function:**
- Extend existing CoS source-contract assertions with the approved audit invariants.

**Template Profile:**
- Controller-selected: `none (lead controller)`
- Selection basis: existing test file owns CoS wording and TDD requires failing tests before skill edits.

**Validator Profile:**
- Controller-selected: `none`
- Selection basis: focused contract tests plus generated-surface and repository validators.

**Specification Coverage:**
- Test explicit-turn trigger after plan binding and before next-action selection.
- Test `NO_ACTION | INSPECT | BLOCKED` as audit outcomes separate from ledger state.
- Test canonical-owner status consumption rather than an exhaustive CoS failure table.
- Test relevant-scope inputs and phase-qualified Herdr absence.
- Test read-only boundaries and scoped V1 exclusions for timer, helper LLM, profile, and persistent state.

**Required Skills:**
- `skill-writing-skills`
- `skill-code-standards`

**Files And Symbols:**
- Inspect: `.agents/skills/skill-chief-of-staff/SKILL.md:Plan Binding`, `Attention`, `Returns And Retirement`, `Durable Truth And Escalation`
- Modify: `tests/test_skill_chief_of_staff.py`
- Verify: `tests/test_skill_chief_of_staff.py`

**Dependencies:**
- Revised verdict accepted as direct approved scope.
- No runtime caller or wake mechanism exists in current repository.

**Authority:**
- Preauthorized local actions: edit focused CoS tests only; inspect named governance and verification sources.
- Stop for: request to add runtime scheduling, external hook ownership, helper-agent dispatch, persistent state, or new profile.

**Steps:**
- [x] Step 1: Add failing assertions for explicit-turn trigger and ordering.
- [x] Step 2: Add failing assertions for statuses, read-only boundary, scoped lane evidence, and V1 exclusions.
- [x] Step 3: Run focused test and record expected failure before skill edit.

**Verification:**
- [x] `py -3 -m pytest tests/test_skill_chief_of_staff.py -q`
- Expected: new audit assertions fail against current skill; existing assertions remain informative.

**Exit Criteria:**
- RED tests fail for missing Attention Audit contract and no production file changed; 1 failed, 7 passed.

### Task 2: Add explicit-turn Attention Audit contract

**Purpose:**
- Implement the smallest CoS behavior that satisfies RED tests without creating a runtime coordinator.

**Task Function:**
- Update reusable CoS coordination instructions while preserving existing authority and return contracts.

**Template Profile:**
- Controller-selected: `none (lead controller)`
- Selection basis: narrow canonical skill wording change with known ownership; tests already define the required contract.

**Validator Profile:**
- Controller-selected: `none`
- Selection basis: no independent profile needed for direct string-contract tests.

**Specification Coverage:**
- Satisfy RED tests for explicit-turn audit ordering.
- Satisfy RED tests for `NO_ACTION | INSPECT | BLOCKED` and separation from ledger state.
- Consume canonical-owner semantics without duplicating condition tables.
- Satisfy phase-qualified Herdr absence wording.
- Satisfy scoped exclusions for timer, helper LLM, profile, persistent state, and mutation authority.

**Required Skills:**
- `skill-code-standards`

**Files And Symbols:**
- Inspect: `.agents/skills/skill-chief-of-staff/SKILL.md:Plan Binding`, `Attention`
- Modify: `.agents/skills/skill-chief-of-staff/SKILL.md:Attention`
- Verify: `tests/test_skill_chief_of_staff.py`

**Dependencies:**
- Task 1 RED tests complete and failing for expected missing contract.

**Authority:**
- Preauthorized local actions: edit canonical skill; run focused pytest command.
- Stop for: need for a new runtime implementation or test fixture beyond source-contract coverage.

**Steps:**
- [x] Step 1: Add minimal Attention Audit wording after plan binding and before next-action selection.
- [x] Step 2: Define bounded relevant-source scope and canonical-owner status consumption.
- [x] Step 3: Define `attention_target`, read-only boundary, and V1 exclusions.

**Verification:**
- [x] `py -3 -m pytest tests/test_skill_chief_of_staff.py -q`
- Expected: focused CoS contract tests pass.

**Exit Criteria:**
- Focused tests pass and guard explicit-turn ordering, canonical-owner semantics, scoped lane evidence, and read-only V1 boundaries.

### Task 3: Regenerate adapters and verify distribution surfaces

**Purpose:**
- Propagate canonical CoS skill changes through maintained generated surfaces and prove no drift.

**Task Function:**
- Regenerate, inspect, and validate generated agent surfaces without direct generated-file edits.

**Template Profile:**
- Controller-selected: `none (lead controller)`
- Selection basis: deterministic repository generation and validation.

**Validator Profile:**
- Controller-selected: `none`
- Selection basis: repository sync, Starter validators, and final verification provide direct proof.

**Specification Coverage:**
- Canonical source remains `.agents/skills/skill-chief-of-staff/SKILL.md`.
- Generated Codex, Claude, and Antigravity surfaces match canonical source.
- Starter output remains aligned with source manifest and excludes factory-only content.
- Adapter and Starter generator implementations are unchanged; parity and built-output checks are sufficient proof.

**Required Skills:**
- `skill-executing-plans`
- `skill-verification-before-completion`

**Files And Symbols:**
- Inspect: `scripts/sync_agent_adapters.py`, `scripts/build_starter_kit.py`, `scripts/validate_starter_kit.py`
- Modify: `generated_agents/codex/skills/skill-chief-of-staff/SKILL.md`, `generated_agents/claude/skills/skill-chief-of-staff/SKILL.md`, `generated_agents/antigravity/skills/skill-chief-of-staff/SKILL.md` via sync only
- Verify: `generated_agents/`, `generated_exports/project-OS-starter-kit/`

**Dependencies:**
- Task 2 complete.

**Authority:**
- Preauthorized local actions: run adapter sync, Starter rebuild, validators, focused tests, and `git diff --check`; inspect generated diffs.
- Stop for: generated drift outside declared CoS surfaces, manifest changes, publication changes, or destructive cleanup requirement.

**Steps:**
- [x] Step 1: Run `py -3 scripts/sync_agent_adapters.py --all-platforms`.
- [x] Step 2: Inspect generated CoS skill diffs and run adapter drift check.
- [x] Step 3: Rebuild and validate Starter output.
- [x] Step 4: Run final focused and repository contract checks.

**Verification:**
- [x] `py -3 scripts/sync_agent_adapters.py --all-platforms --check`
- [x] `py -3 scripts/validate_repo_contracts.py --fast`
- [x] `py -3 scripts/build_starter_kit.py`
- [x] `py -3 scripts/validate_starter_kit.py`
- [x] `py -3 -m pytest tests/test_skill_chief_of_staff.py -q`
- [x] `git diff --check`
- Expected: all commands exit 0; only declared canonical, test, and generated CoS surfaces change.

**Exit Criteria:**
- Generated adapters and Starter output match canonical source; no runtime, hook, scheduler, or persistent-state files are added.

## Verification

- `py -3 scripts/sync_agent_adapters.py --all-platforms --check`
- `py -3 scripts/validate_repo_contracts.py --fast`
- `py -3 scripts/build_starter_kit.py`
- `py -3 scripts/validate_starter_kit.py`
- `py -3 -m pytest tests/test_skill_chief_of_staff.py -q`
- `git diff --check`
- Inspect `git diff --name-only` and confirm unrelated untracked `.playwright-mcp/`, `db/`, and `out/` remain preserved and out of scope.

## Completion Criteria

The plan is ready for completion verification when:

1. explicit-turn Attention Audit contract is present in canonical CoS skill
2. audit outcomes remain separate from workflow, execution, and review states
3. hard-stop and repairable-finding classifications are documented correctly
4. focused CoS contract tests pass
5. generated adapters are synchronized without direct generated edits
6. Starter rebuild and validation pass
7. no timer, scheduler, daemon, hook, helper LLM, profile, or persistent heartbeat state is added
8. final verification finds no unrelated scope change or unresolved blocker

Completion was verified from fresh command output, generated-surface parity,
Starter validation, focused tests, and reviewed Git diff scope. Branch commit,
push, merge, publication, and cleanup remain separately unauthorized.
