---
layer: change
artifact_type: plan
template_id: implementation-plan
contract_version: "1"
status: active
name: context-cleaner-project-os-operational-integration
targets:
  - AGENTS.md
  - docs/operating_system/templates/agents/root-AGENTS.template.md
  - docs/operating_system/tooling/runtime-tool-resolution.md
  - docs/operating_system/procedures/personal-local-worktree-procedure.md
  - .agents/skills/skill-chief-of-staff/SKILL.md
  - generated_agents
---

# Context Cleaner Project OS Operational Integration Plan

## Goal

Add small operational guidance for optional, session-bound Context Cleaner use.

Preserve Project OS authority, Git ownership, plan ownership, acceptance flow,
and generated-surface rules.

Keep attribution, eligibility, scheduling, mutation, recovery, receipts, and
token accounting inside LightRSI.

Do not add new orchestration, Cleaner skill, MCP server, cleanup ledger, or
controller process.

## Implementation Outcomes

### Operational Project OS policy

Extend the existing standing permission with milestone-based optional use,
reliable current-session binding, protected evidence rules, scheduled-versus-
applied handling, refusal fallback, and no project record created solely for
cleaning.

### Capability and procedure guidance

Document one optional context-maintenance capability with supported host,
existing executable, session-binding requirement, observable receipt, and
conservative fallback. Keep Cleaner internals in LightRSI.

### CoS alignment

State that long-running agents maintain their own sessions, workers do not
require Cleaner, CoS does not routinely select or execute cleanup for worker
sessions, and short-lived workers normally finish and retire.

### Generated surfaces

Regenerate managed agent instructions from canonical sources. Do not hand-edit
generated outputs.

### Acceptance readiness

Require external LightRSI evidence for strict session binding, retry identity,
self-initiated analysis, successful application, and continued work.

## Execution Approach

- Mode: `inline sequential`
- Coordination: `git-tracked`
- Required skills: `skill-plan-document-reviewer`, `skill-code-standards`, `skill-backend-verification`, `skill-executing-plans`, `skill-verification-before-completion`
- Isolation: `current workspace`; reconcile pre-existing overlapping canonical and generated changes before regeneration
- Commit policy: `no commits during execution`
- Preauthorized local actions: edit declared canonical Project OS files; regenerate managed outputs; run declared tests, validators, Git checks, and read-only LightRSI evidence inspection
- User-approval actions: commit, push, merge, authentication, external repository mutation, destructive cleanup, discard, or edits outside declared targets
- Parallel ownership: none
- Sequential fallback: baseline → canonical policy → procedure and CoS guidance → generated refresh → external acceptance gate → final verification

## Coordination State

- Coordination owner: `single lead controller`
- Coordination schema: `2`
- Branch: `main`
- Base commit: `b6a6afbc0d63b7dfeeac21c5d70d99bee354818b`
- Review reference: `2de42b1d3bf92d9606d856e347abd7a657b86b01`
- Expected workspace: preserve existing tracked and untracked changes
- Next action: obtain LightRSI implementation-lane evidence, then rerun Task 5 acceptance
- Blockers: LightRSI source checkout and accepted Task 6 evidence are unavailable in this workspace; Project OS work is complete but plan cannot close

Existing workspace changes to preserve:

- `AGENTS.md`
- `README.md`
- `docs/operating_system/templates/agents/root-AGENTS.template.md`
- generated agent files
- `.playwright-mcp/`
- `db/`
- existing untracked plans

| Task | State | Workspace | Executor | Depends On | Required Proof | Evidence |
| --- | --- | --- | --- | --- | --- | --- |
| Task 1 | `completed` | current | `codex` | none | baseline Git and focused tests | `b6a6afbc`, focused suite `59 passed`; existing changes preserved; launcher scope recorded |
| Task 2 | `completed` | current | `codex` | Task 1 | canonical policy diff and focused doc tests | canonical policy added; focused suite `34 passed` |
| Task 3 | `completed` | current | `codex` | Task 2 | runtime, procedure, and CoS consistency checks | runtime/procedure/CoS guidance added; focused suite `40 passed` |
| Task 4 | `completed` | current | `codex` | Task 3 | generated sync and drift checks | sync, headers, drift, template validators passed; focused suite `39 passed`; pre-sync drift reconciled |
| Task 5 | `blocked` | current | `codex` | Task 4 | LightRSI acceptance evidence and final Project OS verification | Project OS validators passed; full suite `789 passed, 1 skipped`; installed CLI help available; no LightRSI source checkout or accepted self-cleaning evidence; no mutation run authorized |

## Task Breakdown

### Task 1: Establish baseline and scope

**Inspect:**

- `AGENTS.md`
- `docs/operating_system/templates/agents/root-AGENTS.template.md`
- `docs/operating_system/tooling/runtime-tool-resolution.md`
- `docs/operating_system/procedures/personal-local-worktree-procedure.md`
- `.agents/skills/skill-chief-of-staff/SKILL.md`
- `scripts/herdr_main_launcher.py:_codex_arguments`

**Actions:**

1. Record branch, `HEAD`, tracked changes, and untracked paths.
2. Confirm existing Cleaner permission is already present.
3. Confirm no duplicate operational guidance exists.
4. Record whether current launcher source contains
   `--dangerously-bypass-hook-trust` or `check_for_update_on_startup`.
5. Classify update-check configuration separately from hook-trust behavior.
6. Keep launcher trust review outside this plan; its presence must not block
   documentation work or a normal-agent pilot that does not require Herdr.

**Verification:**

```powershell
git status --short
git branch --show-current
git rev-parse HEAD
rg -n "Context Cleaner|dangerously-bypass-hook-trust|check_for_update_on_startup" AGENTS.md docs scripts generated_agents
py -3 -m pytest tests/test_native_personal_local_workflow.py tests/test_skill_chief_of_staff.py tests/test_sync_agent_adapters.py -q
```

**Task Function:** Baseline and scope mapping.

**Template Profile:**
- Controller-selected: `normal`
- Selection basis: bounded repository inspection and deterministic baseline checks.

**Validator Profile:**
- Controller-selected: `review`
- Selection basis: independent scope, source, and baseline-evidence check.

**Authority:**

- Preauthorized local actions: inspect repository state, run baseline commands, and record existing changes without modifying unrelated paths.
- Stop for: unknown workspace identity, failed baseline commands requiring interpretation, or any need to discard existing changes.

**Exit Criteria:** Existing permission, target files, generated boundaries, and launcher scope are confirmed.

### Task 2: Extend canonical Cleaner permission

**File:** `docs/operating_system/templates/agents/root-AGENTS.template.md`

Extend existing Cleaner permission. Do not add a second permission block.

Add this policy:

> Context cleaning is optional session-local maintenance, not a project-task transition. Consider it after verified milestones when obsolete context is substantial and expected continuation justifies overhead. Use only the reliably bound current Host session and Cleaner-reported selectable tasks. Treat `scheduled` as pending until a later eligible request permits status inspection. Preserve current instructions, decisions, dependencies, unresolved issues, and evidence awaiting acceptance. For missing capability, attribution, eligible work, or analysis refusal, preserve context and continue ordinary work. For stale or cancelled plans, follow the reported outcome and reanalyze only when worthwhile. For unresolved dispatch or recovery, follow LightRSI's reported recovery behavior; do not assume unchanged context or retry the operation. Do not create project records solely for cleaning.

Preserve current permission limits:

- no authority expansion
- no budget expansion
- no delegation expansion
- no external-action expansion
- no cleanup when attribution or retention is uncertain

**Verification:**

```powershell
rg -n -C 8 "Context Cleaner|session-local|scheduled|applied|incomplete history" docs/operating_system/templates/agents/root-AGENTS.template.md
py -3 -m pytest tests/test_native_personal_local_workflow.py tests/test_starter_kit_generation.py -q
```

**Task Function:** Canonical policy update.

**Template Profile:**
- Controller-selected: `normal`
- Selection basis: bounded documentation change with focused tests.

**Validator Profile:**
- Controller-selected: `review`
- Selection basis: policy duplication, ownership, and generated-boundary review.

**Authority:**

- Preauthorized local actions: extend the existing canonical permission and run focused documentation tests.
- Stop for: duplicate policy wording, conflict with Git-tracked coordination rules, or required behavior not covered by the canonical paragraph.

**Exit Criteria:** One canonical paragraph defines permission and operational use.

### Task 3: Add capability, procedure, and CoS guidance

#### Runtime capability policy

**File:** `docs/operating_system/tooling/runtime-tool-resolution.md`

Under `Capability Policy SSOT`, add:

| Requirement | Owner | Contract |
| --- | --- | --- |
| Optional context maintenance | LightRSI Cleaner plus active host adapter | Use supported host executable with reliable current-session binding and observable Cleaner receipt. Missing capability, attribution, eligible work, or analysis refusal preserves context and permits ordinary work. `scheduled` continues through the next eligible ordinary request before status inspection. Stale or cancelled plans follow their reported outcome. Unresolved dispatch or recovery follows LightRSI recovery behavior without assuming unchanged context or retrying. |

Clarify that:

- Project OS names capability requirements only.
- LightRSI resolves session identity.
- Project OS must not use global latest-session state as authority.
- Missing capability does not block ordinary work.

#### Personal-local procedure

**File:** `docs/operating_system/procedures/personal-local-worktree-procedure.md`

Add section `## Optional Context Maintenance` with this flow:

```text
lightrsi codex clean --session <current-host-session-id>
lightrsi codex clean --plan <returned-plan-id> --select <eligible-task-ids>
continue original work through one eligible ordinary request
lightrsi codex clean --status <returned-plan-id>
```

Require the agent to:

1. Run only after a meaningful verified milestone.
2. Use runtime-provided current Host session identity.
3. Select only Cleaner-reported tasks belonging to that session.
4. Preserve instructions, decisions, dependencies, unresolved issues, and review evidence.
5. For missing capability, attribution, eligible work, or analysis refusal, preserve context and continue ordinary work.
6. Treat `scheduled` as pending; continue through the next eligible ordinary request, inspect resulting status, and claim savings only when `applied`.
7. For stale or cancelled plans, follow the reported outcome and reanalyze only when worthwhile.
8. For unresolved dispatch or recovery, follow LightRSI's reported recovery behavior; do not assume unchanged context or retry the operation.
9. Avoid repeated retries when conditions did not change.
10. Create no task, commit, audit document, or ledger solely for cleaning.

Do not duplicate LightRSI recovery internals.

#### CoS procedure reference

**File:** `.agents/skills/skill-chief-of-staff/SKILL.md`

Add one concise reference under `Conditional References` or
`Context Continuity And Dispatch Gate`:

- long-running CoS may maintain its own session
- each supported worker owns its own session
- CoS does not routinely select or execute cleanup for worker sessions; ordinary observation, troubleshooting, and acceptance remain unchanged
- short-lived workers normally finish and retire
- operational steps use the personal-local procedure

**Verification:**

```powershell
rg -n -C 5 "Optional Context Maintenance|context maintenance|current-host-session-id|scheduled|applied" docs/operating_system/tooling/runtime-tool-resolution.md docs/operating_system/procedures/personal-local-worktree-procedure.md
rg -n -C 5 "own session|worker sessions|finish and retire|personal-local-worktree-procedure" .agents/skills/skill-chief-of-staff/SKILL.md
py -3 -m pytest tests/test_native_personal_local_workflow.py tests/test_skill_chief_of_staff.py -q
```

**Task Function:** Capability and procedure alignment.

**Template Profile:**
- Controller-selected: `normal`
- Selection basis: cross-document contract alignment without new runtime code.

**Validator Profile:**
- Controller-selected: `review`
- Selection basis: session-binding, fallback, and ownership consistency review.

**Authority:**

- Preauthorized local actions: edit declared canonical documentation and skill files; run focused tests and static consistency checks.
- Stop for: conflicting session-binding ownership, duplicated LightRSI runbook content, or any instruction that makes Cleaner mandatory.

**Exit Criteria:** Runtime policy, personal procedure, and CoS behavior describe one consistent session-local workflow.

### Task 4: Regenerate and validate managed surfaces

Canonical source order:

1. `docs/operating_system/templates/agents/root-AGENTS.template.md`
2. `.agents/skills/skill-chief-of-staff/SKILL.md`
3. runtime and procedure documents
4. generated agent surfaces

Before generation, inspect existing diffs in `AGENTS.md`, the canonical
template, and generated files. Run the sync check first. If it reports drift,
reconcile each overlapping hunk against the canonical source and preserve
unrelated changes before generation. Do not overwrite an unreviewed generated
change.

Run adapter generation only after that reconciliation. Do not hand-edit
generated files.

```powershell
py -B scripts/sync_agent_adapters.py --all-platforms --check
py -B scripts/sync_agent_adapters.py --all-platforms
```

Inspect generated changes. Confirm only deterministic outputs changed.

**Verification:**

```powershell
py -B scripts/sync_agent_adapters.py --all-platforms --check
py -B scripts/validate_generated_header_format.py
py -B scripts/validate_agent_runtime_drift.py --all-platforms --skip-deploy-check
py -B scripts/validate_template_required_sections.py
py -3 -m pytest tests/test_sync_agent_adapters.py tests/test_starter_kit_generation.py tests/test_validate_generated_header_format.py -q
git diff --check
```

**Task Function:** Generated-surface synchronization.

**Template Profile:**
- Controller-selected: `normal`
- Selection basis: deterministic adapter generation and validator execution.

**Validator Profile:**
- Controller-selected: `review`
- Selection basis: canonical-versus-generated drift and unrelated-change review.

**Authority:**

- Preauthorized local actions: regenerate managed outputs and run generated-surface validators.
- Stop for: nondeterministic generated output, drift, header failure, changes outside declared generated surfaces, or mutation of unrelated user work.

**Exit Criteria:** Canonical and generated surfaces match, and Project OS
guidance verification is recorded separately from live LightRSI Task 6
acceptance.

### Task 5: External LightRSI prerequisite and final acceptance

This task does not modify LightRSI from this workspace.

**External LightRSI source surfaces:**

- `components/products/cli/src/hosts/codex.ts`
- `components/products/cli/src/clean.ts`
- `components/adapters/codex/src/context-cleaner/bridge.ts`
- `components/adapters/codex/src/proxy-runtime.ts`
- `docs/superpowers/plans/2026-09-19-context-cleaner-safety-autonomy-follow-up-plan.md`

**Required LightRSI guarantees and outstanding gaps:**

Existing implementation evidence may satisfy guarantees below; this Project OS
plan must not reopen production work when the LightRSI plan already records
accepted proof.

**Guarantees to consume from LightRSI evidence:**

1. Unresolved current-session identity refuses write-capable cleaning.
2. Explicit validated session selection remains supported.
3. No duplicate generation occurs after successful provider response with local persistence failure.
4. Unresolved-tool protection remains intact.
5. Automatic lifecycle eviction remains disabled for the Codex proxy.

**Outstanding gaps before Task 6 acceptance:**

1. Repeated cancellation replays the stored canonical receipt.
2. Accepted task selection remains canonical through schedule finalization.
3. Self-cleaning succeeds through the normal agent tool interface.
4. Normal intervening tool results do not create perpetual stale-plan rejection.

**LightRSI handoff:**

Send this dependency mapping to the existing LightRSI plan
`docs/superpowers/plans/2026-09-19-context-cleaner-safety-autonomy-follow-up-plan.md`.
The LightRSI implementation lane owns execution and evidence; Project OS
consumes its accepted results.

| LightRSI owner | Required outcome |
| --- | --- |
| Task 7 | Resolve cancellation replay and reordered-selection finalization gaps |
| Task 8 | Reference existing attribution and approved-Cleaner execution evidence |
| Task 6, Gate A | Prove strict binding and completed internal milestones within a continuing objective |
| Task 6, Gate B | Same agent analyzes, selects, schedules, observes application, and continues |
| Task 6, Gate C | Record functional acceptance and bounded cost and latency findings |

**Required direct boundary proof:**

- fresh normal Codex session
- agent-owned continuing objective
- completed internal milestone
- same normal agent invokes Cleaner through its ordinary tool interface without human-selected IDs
- eligible tasks bound to current session
- same agent receives selectable tasks and schedules cleanup
- `scheduled` receipt
- same agent continues through an eligible ordinary request
- same agent observes committed `applied` status
- retained required evidence
- same agent resumes the original objective
- safe refusal for incomplete or uncertain history
- no cross-session selection
- idempotent cancellation and reordered-selection handling

**Required regression scenarios:**

- the Cleaner invocation's own tool exchange remains protected without making successful self-maintenance impossible
- normal intervening tool results and continuation do not cause perpetual stale-plan rejection

If either scenario fails, record a LightRSI capability gap. External cleaning
of an idle worker is diagnostic evidence only, not Task 6 completion.

**Acceptance evidence:**

- LightRSI commit or review artifact containing focused regression proof
- direct CLI invocation output
- canonical receipt identity
- applied mutation evidence
- continuation evidence
- cost and latency measurements
- human intervention count
- applied removal separate from estimated savings
- separate Project OS guidance verification from live Task 6 acceptance

**Task Function:** External acceptance evidence review.

**Template Profile:**
- Controller-selected: `normal`
- Selection basis: bounded evidence inspection against explicit LightRSI acceptance gates.

**Validator Profile:**
- Controller-selected: `review`
- Selection basis: independent backend-boundary, retry, identity, and continuation review.

**Authority:**

- Preauthorized local actions: inspect external LightRSI evidence and record acceptance status in this plan.
- Stop for: missing LightRSI handoff or evidence, unresolved retry identity conflict, unresolved active-tool snapshot behavior, cross-session fallback, or safe refusal reported as successful cleaning.

**Exit Criteria:** External LightRSI evidence satisfies the acceptance gate. Otherwise plan remains incomplete or blocked.

## Non-Goals

- No new Context Cleaner skill.
- No Cleaner MCP server.
- No Project OS cleanup ledger.
- No Project OS session resolver.
- No automatic lifecycle eviction.
- No periodic cleanup daemon.
- No controller process for normal-agent cleaning.
- No Herdr worker-wide cleanup obligation.
- No manual edits to generated agent files.
- No `scripts/herdr_main_launcher.py` edit in this plan. Review launcher hook trust separately; its result does not block Project OS guidance or a normal-agent pilot that does not require Herdr.
- No edits to the installed `tokenpilot-codex-hook.cmd` wrapper.
- No cleanup, discard, commit, push, merge, or alteration of unrelated workspace changes.

## Verification

Focused Project OS proof:

```powershell
py -3 -m pytest tests/test_native_personal_local_workflow.py tests/test_skill_chief_of_staff.py tests/test_sync_agent_adapters.py tests/test_starter_kit_generation.py tests/test_validate_generated_header_format.py -q
```

Repository contract proof:

```powershell
py -B scripts/validate_repo_contracts.py --repo-root . --fast
py -B scripts/validate_planning_lifecycle.py --repo-root .
py -B scripts/validate_agent_runtime_drift.py --all-platforms --skip-deploy-check
py -B scripts/sync_agent_adapters.py --all-platforms --check
py -B scripts/validate_generated_header_format.py
py -B scripts/validate_template_required_sections.py
git diff --check
```

Final test proof:

```powershell
py -3 -m pytest -q
```

External backend proof uses LightRSI's CLI boundary and covers success,
incomplete-history refusal, unresolved-session refusal, cross-session
isolation, cancellation replay, reordered selection, provider success plus
local persistence failure, scheduled-to-applied transition, and continuation.

## Completion Criteria

1. Existing Cleaner permission remains single-source.
2. Operational guidance is optional, milestone-based, and session-bound.
3. Project OS does not resolve Cleaner session identity.
4. Agents consume public Cleaner status and receipts; Project OS does not parse or mutate LightRSI internal stores.
5. Runtime policy and personal procedure agree.
6. CoS and worker ownership rules agree; CoS does not routinely select or execute worker cleanup, while ordinary observation and acceptance remain unchanged.
7. Generated surfaces match canonical sources.
8. Focused tests and repository validators pass.
9. Full test suite passes, or isolated pre-existing failures are recorded.
10. Launcher hook trust is reviewed separately and does not block this plan.
11. LightRSI proves strict identity, retry safety, active-tool behavior,
    application, and continuation.
12. Project OS guidance verification and live LightRSI Task 6 acceptance are recorded as separate evidence.
13. No unrelated tracked or untracked workspace path changes.
14. Plan status changes to `completed` only after fresh verification returns
    `verified`.

## Handoff

After approval:

1. Use `skill-plan-document-reviewer`.
2. Resolve review findings.
3. Change plan status to `active`.
4. Execute with `skill-executing-plans`.
5. Use `skill-verification-before-completion` for final claims.
6. Send the LightRSI dependency mapping to its implementation lane.
7. Keep external LightRSI work as a prerequisite, not hidden Project OS compensation.
