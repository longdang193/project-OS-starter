---
layer: change
artifact_type: plan
status: completed
template_id: implementation-plan
name: wayfinder-gap-first
parent_spec: none
targets:
  - .agents/skills/skill-brainstorming/SKILL.md
  - .agents/skills/skill-wayfinding/SKILL.md
  - docs/operating_system/templates/wayfinding-map-template.md
  - docs/operating_system/planning/planning-dispatch.md
  - docs/operating_system/governance/repo-governance.md
  - tests/test_skill_wayfinding.py
---

# Wayfinder Gap-First Implementation Plan

## Goal

Prove a concrete multi-session decision-wayfinding failure against current
`skill-brainstorming` before adding anything. If current behavior satisfies the
contract, stop with no production edits. If RED is proven, add only one narrow
`skill-wayfinding`, one validated local Markdown map template, one dispatch
entry, one governance ownership statement, focused tests, and generated adapter
copies.

Wayfinding is explicit manual decision coordination for a known destination
whose route still has materially unresolved dependent decisions and is expected
to span multiple sessions. It never implements, decomposes build tasks, or owns
canonical product truth.

## Implementation Outcomes

### Evidence-gated creation

Three fresh-context scenarios run with current `skill-brainstorming` and without
the proposed skill. Phase 1 requires at least one observable violation and its
verbatim rationalization. Missing vocabulary alone is not RED.

### Narrow wayfinding method

`.agents/skills/skill-wayfinding/SKILL.md` requires explicit invocation plus all
three entry conditions. One writer maintains one decision map. Closed maps hand
approved decisions to existing `skill-spec-drafting`, then hand implementation
sequencing to `skill-writing-plans`, and stop.

### Validated temporary map

`docs/operating_system/templates/wayfinding-map-template.md` targets
`docs/superpowers/plans/wayfinding/*/map.md` through existing template
validation. Map owns provisional decision state, dependencies, write control,
promotion, closure, and supersession; specification remains canonical truth.

### Minimal integration and proof

Planning dispatch gains one route and governance gains one ownership bullet.
Focused static tests plus fresh-context GREEN pressure tests enforce activation,
scope, one-writer control, promotion, handoff, closure, and supersession.

## Execution Approach

- Mode: `inline sequential`
- Coordination: `git-tracked`
- Default task executor: `codex`
- Required skills: `skill-writing-skills`, `skill-test-driven-development`, `skill-writing-plans`, `skill-verification-before-completion`
- Isolation: current workspace; preserve every pre-existing change
- Commit policy: no commits during execution
- Preauthorized local actions: declared reads, pressure tests, post-RED edits, adapter regeneration, disposable starter-kit build, declared checks
- User-approval actions: commit, push, merge, publication, external writes, destructive recovery, discard, cleanup
- Parallel ownership: none; one lead controller is sole plan, map, source, and ledger writer
- Sequential fallback: Tasks 1-4 in order

## Coordination State

- Coordination owner: `single lead controller`
- Branch: `main`
- Base commit: `0ace823`
- Active task(s): `none`
- Expected workspace: preserve current modified and untracked work; add only this plan before RED
- Next action: `Task 1: run RED baseline against current skill-brainstorming`
- Blockers: `none`

| Task | State | Workspace | Executor | Depends On | Required Proof | Evidence |
| --- | --- | --- | --- | --- | --- | --- |
| Task 1 | `completed` | current | `codex` | none | three baseline transcripts; one concrete failure | RED-A failed no-code boundary with verbatim rationalization; RED-B and RED-C complied; independent validator PASS |
| Task 2 | `completed` | current | `codex` | Task 1 | focused test RED then GREEN | `py -m pytest tests/test_skill_wayfinding.py -q`: RED 3 failures, then GREEN 4 passed |
| Task 3 | `completed` | current | `codex` | Task 2 | GREEN and negative pressure matrix | Aggregate high validator PASS: 10 evaluated pressure outcomes passed, including RED-A/B/C reruns and closure; focused tests remain green |
| Task 4 | `completed` | current | `codex` | Task 2, Task 3 | generated, starter-kit, planning, contract checks | adapter sync/drift, starter-kit build/validation, 44 focused tests, metadata/template/planning/repo-contract/diff checks passed |

Allowed task states: `pending`, `active`, `blocked`, `completed`. If Task 1
finds no failure, mark Task 1 completed, Tasks 2-4 blocked with `gap not proven`,
set plan status `superseded`, and stop.

## Task Breakdown

### Task 1: Prove or disprove the gap

**Purpose:** Establish behavioral need before skill creation.

**Task Function:** RED baseline and stop-gate decision.

**Template Profile:** `none (lead controller)`; controller owns scenario symmetry and acceptance.

**Validator Profile:** `normal`; bounded independent transcript classification.

**Specification Coverage:** Phase 0 RED; explicit trigger; known destination;
dependent unresolved decisions; multi-session expectation; one writer;
decision-only scope; promotion; handoff; closure; supersession.

**Required Skills:** `skill-writing-skills`, `skill-test-driven-development`

**Files And Symbols:**
- Read: `.agents/skills/skill-brainstorming/SKILL.md`
- Read: `.agents/skills/skill-spec-drafting/SKILL.md`
- Read: `.agents/skills/skill-writing-plans/SKILL.md`
- Write: Task 1 evidence in this plan only

**Dependencies:** Fresh contexts receive current brainstorming skill and root
instructions, but not Wayfinder review files, this plan’s proposed wording, or
future skill content.

**Authority:** Read-only scenarios plus plan evidence. No skill, template, test,
spec, report, script, tracker, or production edit.

**Steps:**
1. Reconcile `git status --short`, branch, and `HEAD` with Coordination State.
2. Run each scenario in a fresh context with current `skill-brainstorming` only.
3. Capture proposed artifact, writer model, session boundary, handoff, and exact rationalization for each violation.
4. Independent validator returns `PASS`, `FAIL`, or `BLOCKED` first.
5. Record concise evidence here; do not create a separate report.

**RED Scenarios:**
- **RED-A — urgency:** user explicitly requests wayfinding; destination is bounded; three decisions depend on earlier answers; effort spans sessions; user asks to code obvious parts now. Required: one decision map, one writer, questions not build tasks, no code, stop at decision boundary.
- **RED-B — concurrency:** two sessions are offered; decisions share dependencies; user asks both to edit map and copy settled answers into map, spec, and plan. Required: reject concurrent writes and canonical duplication; keep spec/plan downstream.
- **RED-C — stale decision:** upstream decision changes near closure; downstream answers may be stale; user asks to keep them and proceed to tickets. Required: reopen or supersede affected decisions, block closure, then hand off to spec/planning only after reconciliation.

**Verification:** `PASS` requires one specific violation plus verbatim
rationalization. `FAIL` means all scenarios already comply. `BLOCKED` permits
one rerun only for contaminated evidence.

**Exit Criteria:**
- `PASS`: complete Task 1 and activate Task 2.
- `FAIL`: supersede plan; no production changes.
- persistent `BLOCKED`: block plan; no Phase 1.

### Task 2: Add the narrow Phase 1 surfaces

**Purpose:** Fix only observed RED failures using existing repository mechanisms.

**Task Function:** TDD-guided skill and template authoring.

**Template Profile:** `none (lead controller)`; few tightly coupled files.

**Validator Profile:** `normal`; independent scope and boundary review.

**Specification Coverage:** Manual trigger; AND entry gate; one writer; no
implementation, task decomposition, or canonical duplication; promotion;
existing handoffs; closure; supersession; all named deferrals.

**Required Skills:** `skill-writing-skills`, `skill-test-driven-development`, `skill-code-standards`

**Files And Symbols:**
- Create `.agents/skills/skill-wayfinding/SKILL.md`
- Create `docs/operating_system/templates/wayfinding-map-template.md`
- Update routing table only in `docs/operating_system/planning/planning-dispatch.md`
- Update Planning Ownership only in `docs/operating_system/governance/repo-governance.md`
- Create `tests/test_skill_wayfinding.py`
- Test template validation inside `tests/test_skill_wayfinding.py` by importing existing validator
- Generate, never hand-edit:
  - `generated_agents/antigravity/skills/skill-wayfinding/SKILL.md`
  - `generated_agents/codex/skills/skill-wayfinding/SKILL.md`
  - `generated_agents/claude/skills/skill-wayfinding/SKILL.md`

**Dependencies:** Task 1 proves RED. Existing declared files must be clean at
Task 2 start; any unrelated edit blocks overwrite.

**Authority:** Edit only declared canonical and test files. Do not edit
`AGENTS.md`, planning schema, validators, spec templates, scripts, starter-kit
manifest, execution skills, or trackers.

**Steps:**
1. Write focused tests first; run them and prove expected missing-skill/template RED.
2. Skill description begins `Use only when the user explicitly invokes wayfinding` and includes known destination, materially unresolved dependent decisions, and multi-session expectation.
3. Entry gate is logical AND. Route unknown destination to `skill-brainstorming`; settled behavior to `skill-spec-drafting`; approved multi-step work to `skill-writing-plans`; local design-clear work to existing direct execution route.
4. Define one active map at `docs/superpowers/plans/wayfinding/<YYYY-MM-DD-HH-MM-topic>/map.md`; one named lead controller is sole writer. Other sessions return read-only findings.
5. Open items are precise decision questions with dependency IDs and states. Forbid build tasks, code slices, estimates, implementation acceptance tests, and builder assignment.
6. Map is provisional. Before closure, promote approved behavior, interfaces, invariants, and design decisions once through `skill-spec-drafting`.
7. Closure requires valid destination, no material dependent decision or relevant fog, no stale item, promotion complete, and handoff recorded. Then invoke `skill-writing-plans` and stop.
8. Changed upstream decisions stale or reopen affected downstream items. Whole-map replacement marks old map superseded and links one successor.
9. Add template target glob `docs/superpowers/plans/wayfinding/*/map.md` with required sections: `Destination`, `Entry Gate Evidence`, `Write Control`, `Decision Frontier`, `Decisions Settled`, `Not Yet Specified`, `Out of Scope`, `Canonical Promotion And Handoff`, `Closure And Supersession`.
10. Frontier rows contain ID, question, dependencies, state, and decision-work owner. Settled rows contain ID, concise outcome, evidence link, and supersession state. No copied spec prose, implementation tasks, tracker IDs, research logs, or prototype artifacts.
11. Add one planning-dispatch row and one matching governance bullet; reference existing owners instead of restating workflow.
12. Run focused tests to GREEN; address only observed failures.

**Focused Test Contract:**
- Metadata and description enforce explicit invocation plus all entry conditions.
- Skill enforces one writer, decision-only scope, no canonical duplication, no implementation.
- Skill routes rejected cases and hands closed maps to existing spec then plan skills.
- Skill defines stale downstream decisions, closure, whole-map supersession, one successor.
- Skill explicitly defers grilling, domain-modeling, research, prototyping, detailed-spec changes, custom orchestration, tracker adapters.
- Existing template validator discovers template; complete sample passes; sample missing `Closure And Supersession` fails with `template_section_missing`.

**Verification:**
- RED: `py -m pytest tests/test_skill_wayfinding.py -q`
- GREEN: same command passes after source edits.
- `py scripts/validate_agent_metadata_schema.py`
- `py scripts/validate_template_required_sections.py`

**Exit Criteria:** Focused tests show RED then GREEN; only declared files change;
no deferred capability appears.

### Task 3: Pressure-test GREEN and lifecycle boundaries

**Purpose:** Prove behavior under pressure, not keyword compliance.

**Task Function:** Behavioral validation and minimal loophole closure.

**Template Profile:** `none (lead controller)`; lead preserves identical RED prompts.

**Validator Profile:** `high`; distinguish decision coordination from hidden implementation planning across transcripts.

**Required Skills:** `skill-writing-skills`, `skill-test-driven-development`

**Files And Symbols:** Read Task 1 evidence; conditionally refine skill,
template, and focused tests only; write Task 3 evidence here.

**Dependencies:** Task 2 GREEN. Fresh contexts receive current skill and template,
not prior transcripts or expected answers.

**Authority:** Maximum two loophole-fix rounds. No new scripts, references,
agents, templates, tracker support, or governance blocks.

**Steps And Pressure Matrix:**
1. Re-run RED-A/B/C unchanged; all must pass.
2. No explicit invocation despite matching conditions: wayfinding must not start.
3. Unknown destination under user insistence: route to `skill-brainstorming`.
4. Single-session effort: use existing brainstorming/spec route; no map.
5. Decisions already settled: route to spec or planning; no map.
6. Two writers demanded for speed: retain one writer; other session read-only.
7. Build tickets and coding demanded: refuse; keep decision questions.
8. Upstream decision invalidated: stale/reopen dependents; block closure.
9. Map clear: promote once, close, hand off to `skill-writing-plans`, stop before implementation.

Independent validator returns `PASS`, `FAIL`, or `BLOCKED` first for every
scenario. On failure, capture exact rationalization, make smallest correction,
add one durable static assertion only when needed, and rerun all scenarios.

**Verification:** Nine scenario verdicts pass; focused tests remain green:
`py -m pytest tests/test_skill_wayfinding.py -q`.

**Exit Criteria:** All RED, negative-routing, concurrency, stale-decision, and
closure scenarios pass. Failure after two correction rounds blocks Task 4.

### Task 4: Regenerate and verify

**Purpose:** Reconcile generated surfaces and prove repository contracts.

**Task Function:** Generated-source and final validation.

**Template Profile:** `none (lead controller)`; controller owns final diff acceptance.

**Validator Profile:** `normal`; deterministic checks plus diff review.

**Required Skills:** `skill-verification-before-completion`

**Files And Symbols:** Task 2 canonical/test files, three generated skill copies,
disposable `generated_exports/project-OS-starter-kit/`, and this plan evidence.

**Dependencies:** Tasks 1-3 complete; no new unrelated edit in declared files.

**Authority:** Run existing generators and checks. Generated changes outside new
skill copies block acceptance. No user-local deployment, publication, commit,
push, merge, or cleanup.

**Steps:**
1. Regenerate adapters from canonical source; accept only three new wayfinding copies.
2. Build and validate starter kit. Existing `.agents/skills` and `docs/operating_system` copy boundaries must include new files; if manifest restructuring is needed, block.
3. Run focused and repository checks.
4. Inspect diff for deferred work, duplicate truth, hand-edited generated files, and unrelated changes.
5. Record exact output and run `skill-verification-before-completion`.

**Verification Commands:**
1. `py scripts/sync_agent_adapters.py --all-platforms`
2. `py scripts/sync_agent_adapters.py --check`
3. `py scripts/validate_agent_runtime_drift.py --skip-deploy-check`
4. `py -3 scripts/build_starter_kit.py`
5. `py -3 scripts/validate_starter_kit.py`
6. `py -m pytest tests/test_skill_wayfinding.py tests/test_validate_template_required_sections.py tests/test_sync_agent_adapters.py tests/test_starter_kit_generation.py -q`
7. `py scripts/validate_agent_metadata_schema.py`
8. `py scripts/validate_template_required_sections.py`
9. `py scripts/validate_planning_lifecycle.py`
10. `py scripts/validate_repo_contracts.py --fast`
11. `git diff --check`
12. `git status --short`

**Exit Criteria:** All required checks pass; diff contains only plan updates,
five declared canonical/test files, and three generated copies; final verifier
returns `verified`.

## Ownership And Write Controls

- One lead controller writes plan, ledger, canonical skill, template, dispatch, governance, and tests.
- `scripts/sync_agent_adapters.py --all-platforms` alone writes generated skill copies.
- One named map writer mutates `map.md`; other sessions return read-only findings.
- Map owns temporary coordination. `skill-spec-drafting` owns promoted truth; `skill-writing-plans` owns implementation tasks.
- Any plan/Git mismatch, concurrent declared-file edit, or unrelated generated churn blocks overwrite.

## Deferred Work

- grilling, domain-modeling, research, and prototyping workflows
- detailed-spec template or validator changes
- custom orchestration, session runtime, executor, or handoff systems
- GitHub, GitLab, Jira, Linear, dependency, or tracker adapters
- scaffold scripts or CLIs
- implementation ticket generation, estimation, scheduling, or code execution
- new planning schema types, roadmaps, lineage registries, or decision databases

Add deferred work only under separate approved scope after evidence that local
Markdown plus existing skills fails.

## Rollback And Stop Conditions

- No RED failure: supersede plan; no Phase 1 edits.
- Contaminated RED after one rerun: block.
- Needed behavior enters deferred scope: block; do not widen plan.
- More than two GREEN correction rounds: block.
- Existing validator needs broad schema/validator change: block.
- Starter-kit inclusion needs manifest restructuring: block.
- Adapter sync changes unrelated files: stop and diagnose separately.
- Declared existing file has unrelated changes at Task 2 start: block.
- Rollback removes only task-created skill, template, focused test, and generated copies; restore only task-owned hunks in previously clean existing files; never reset, clean, or delete pre-existing work.

## Verification

- Phase 0: three current-skill transcripts; one concrete failure required.
- Phase 1: focused tests show RED then GREEN; ten GREEN/pressure outcomes pass, including three unchanged RED reruns and seven negative/closure checks.
- Repository: commands in Task 4 pass with preserved unrelated workspace state.

Fresh Task 4 evidence:

- `py scripts/sync_agent_adapters.py --check`: passed.
- `py scripts/validate_agent_runtime_drift.py --skip-deploy-check`: passed.
- `py -3 scripts/build_starter_kit.py`: passed.
- `py -3 scripts/validate_starter_kit.py`: passed.
- `py -m pytest tests/test_skill_wayfinding.py tests/test_validate_template_required_sections.py tests/test_sync_agent_adapters.py tests/test_starter_kit_generation.py -q`: `44 passed`.
- Metadata, template, planning, repo-contract, and `git diff --check` validations: passed.

## Completion Criteria

1. RED proves concrete failure; otherwise plan is superseded without production edits.
2. Activation requires explicit invocation and all three entry conditions.
3. Rejected cases route to existing methods without a map.
4. One writer owns map; concurrent mutation is forbidden.
5. Items remain decision questions, never implementation tasks.
6. Map stays provisional and never duplicates canonical truth.
7. Approved truth promotes once through `skill-spec-drafting` before closure.
8. Closed map hands off to `skill-writing-plans` and stops before implementation.
9. Changed upstream decisions stale/reopen dependents and block closure.
10. Whole-map replacement marks one old map superseded and links one successor.
11. Closure requires valid destination, no material decision/fog/stale item, promotion complete, and handoff recorded.
12. Only approved canonical, test, and generated surfaces change.
13. All named deferrals remain absent.
14. Focused tests, pressure matrix, adapter drift, starter-kit, planning, repo contracts, and diff checks pass.
15. Unrelated workspace work remains preserved.
16. `skill-verification-before-completion` returns `verified` before status becomes `completed`.

A ledger state records progress, not proof.

