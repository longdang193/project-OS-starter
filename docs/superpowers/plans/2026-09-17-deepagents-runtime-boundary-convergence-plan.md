---
layer: change
artifact_type: plan
status: completed
template_id: implementation-plan
contract_version: "1"
name: deepagents-runtime-boundary-convergence
parent_spec: docs/superpowers/specs/2026-09-14-parallel-deepagents-dispatch-spec.md
targets:
  - scripts/herdr_attempt_contract.py
  - scripts/dcode_project.py
  - scripts/herdr_main_launcher.py
  - scripts/herdr_parallel_dispatch.py
  - scripts/validate_repo_contracts.py
  - tests/test_herdr_attempt_contract.py
  - tests/test_dcode_project.py
  - tests/test_herdr_main_launcher.py
  - tests/test_herdr_parallel_dispatch.py
  - tests/test_validate_repo_contracts.py
  - docs/operating_system/runtime/runtime-surfaces.md
  - docs/operating_system/procedures/personal-local-worktree-procedure.md
  - docs/operating_system/procedures/runtime-adapter-procedure.md
  - docs/operating_system/tooling/runtime-tool-resolution.md
  - docs/operating_system/planning/planning-dispatch.md
  - docs/operating_system/rules/git-tracked-coordination-rule.md
  - docs/operating_system/rules/command-execution-rule.md
  - docs/operating_system/governance/precedence.md
  - docs/operating_system/governance/repo-governance.md
  - docs/operating_system/templates/agents/root-AGENTS.template.md
  - .agents/skills/skill-chief-of-staff/SKILL.md
  - .agents/skills/skill-deepagents-executing-plans/SKILL.md
  - .agents/skills/skill-dispatching-parallel-agents/SKILL.md
  - .agents/skills/skill-executing-plans/SKILL.md
  - .agents/skills/skill-requesting-code-review/SKILL.md
  - docs/superpowers/plans/2026-09-17-deepagents-attempt-contract-consolidation-plan.md
---

# Converge DeepAgents Runtime Boundaries And Guidance

## Review Basis

The follow-up verdicts for commit `eaf67df` identify unresolved contract,
recovery, continuation, authorization, and documentation problems. Repository
checks confirm the material claims:

- `resolve_attempt_budget()` and `eligibility_action()` have test callers but no
  production callers.
- `scripts/herdr_parallel_dispatch.py` imports both public
  `normalize_runtime_grant` and launcher-private `_normalize_runtime_grant`.
- Dispatcher settlement classification remains local at
  `scripts/herdr_parallel_dispatch.py:768`.
- Coordinated DeepAgents guidance still exposes raw `dcode-project` at
  `.agents/skills/skill-deepagents-executing-plans/SKILL.md:80`.
- CoS guidance still assigns lifecycle ownership to MAIN AGENT at
  `.agents/skills/skill-chief-of-staff/SKILL.md:40`.
- Runtime documentation identifies Herdr observation as transient in some
  sections but still assigns Herdr top-level lifecycle ownership in others.
- `scripts/dcode_project.py:_claim_attempt` does not reconcile stored terminal
  evidence or a retained correlated receipt before returning a recovery block.
- Wrapper admission constants duplicate `ADMISSION_RESULTS` from the shared
  contract.
- DeepAgents guidance still treats `NEEDS_CONTEXT` as an immediate same-task
  retry path.
- Command authorization and instruction-precedence documents describe
  conflicting exception and specificity rules.

The completed plan
`docs/superpowers/plans/2026-09-17-deepagents-attempt-contract-consolidation-plan.md`
remains historical evidence. This plan permits only a minimal factual closure
of its stale `Next action` and completion wording; it does not rewrite its
historical task evidence or other completed plans.

The parent specification is completed. This plan inherits its assignment,
receipt, retirement, retry, concurrency, and acceptance requirements; it
clarifies terminology and wires existing requirements into production callers.
It does not silently change the parent specification.

## Goal

Make the attempt contract the executable semantic boundary for coordinated
DeepAgents admission, budget, settlement, lifecycle, and eligibility. Add one
bounded attempt-guard reconciliation operation under the existing ownership
lock. Keep native execution facts in `dcode-project`, delivery and diagnostics
in Herdr, workflow truth in Plan plus Git, and task acceptance in CoS.

Converge maintained guidance on that boundary without adding a scheduler,
runtime ledger, retry service, or new launcher.

## Implementation Outcomes

### Contract callers use one semantic owner

Production launcher and dispatcher paths consume the public functions in
`scripts/herdr_attempt_contract.py` for grant normalization, budget resolution,
settlement proof, lifecycle derivation, and eligibility. Private launcher
normalization and duplicated dispatcher policy are removed after all callers
and tests move to the public contract.

### Interrupted attempts reconcile without another runtime system

`dcode-project` persists validated settlement evidence before receipt removal
and reconciles active claims from the guard, correlated receipt, cleanup, and
descendant evidence under the existing lock. Settled same-binding attempts
remain idempotent; uncertainty remains `RECOVERY_REQUIRED`.

Admission outcomes stay explicit:

| Evidence | Outcome |
| --- | --- |
| No claim and no known prior attempt | `ADMITTED` / eligible |
| Valid active ownership | `BLOCKED` / replacement blocked |
| Same attempt binding | `IDEMPOTENT` / return existing status |
| Correlated terminal evidence with proven cleanup and descendants retired | settle claim |
| Known prior attempt with missing, stale, inconsistent, or mismatched evidence | `RECONCILE` / `RECOVERY_REQUIRED` |

### Coordinated and ordinary execution paths are distinct

Maintained skills and procedures state that ordinary personal-local DeepAgents
probes may call `dcode-project` directly, while Git-tracked coordinated
DeepAgents use the controller-owned launcher or existing parallel dispatcher
entry path that supplies assignment identity and grant bindings. No internal
assignment flags are copied into multiple skills.

### Ownership and recovery language is consistent

`runtime-surfaces.md` becomes the compact ownership index. It points to the
attempt contract as executable lifecycle semantics, `dcode-project` as native
DeepAgents execution and cleanup fact owner, Herdr as delivery and diagnostic
observer, CoS as authority and acceptance owner, and Plan plus Git as workflow
recovery truth. Observation evidence cannot be described as settlement,
continuation, retry, or acceptance authority.

### Drift has cheap repository proof

Repository validation blocks mechanical regressions:

1. production dispatcher imports of launcher-private policy helpers;
2. wrapper-local admission definitions that duplicate the shared contract;
3. broken canonical references in maintained guidance.

Generated-source drift remains covered by the existing adapter check. Semantic
wording remains a targeted review obligation; a phrase scanner is not treated
as proof of ownership correctness. Historical completed plans and generated
adapter outputs are excluded from the mechanical guidance scan.

## Non-Goals

- No new scheduler, retry engine, recovery daemon, heartbeat, or multi-attempt
  ledger.
- No change to `MAX_CONCURRENCY = 2`, the existing 10-second retry cap, or
  approved MCP security boundaries.
- No Codex or Tura lifecycle parity.
- No change to approved receipt ordering or bounded observation behavior from
  `docs/superpowers/specs/2026-09-14-parallel-deepagents-dispatch-spec.md`.
- No asynchronous return-after-claim redesign in this plan. Measure current
  dispatch and settlement latency first; change transport only under a separate
  approved spec amendment.
- No routine observation removal in this plan. The current approved spec still
  requires bounded process and pane probes; pane-to-diagnostic-only migration
  needs a structured executor result channel first.
- No broad rewrite of completed plans. One factual closure of the stale
  consolidation-plan next action is allowed.
- No generated files by hand or shared user-local runtime state.
- No new dependency, provider fallback, tracked `.deepagents/` state, project
  MCP mutation, authentication, push, merge, or destructive cleanup.
- No requirement for CoS activation in ordinary single-task Git-tracked
  execution; the lead controller owns continuation when CoS is absent.

## Execution Approach

- Mode: `inline sequential`
- Coordination: `git-tracked`
- Required skills: `skill-systematic-debugging`, `skill-test-driven-development`, `skill-backend-verification`, `skill-code-standards`, `skill-verification-before-completion`, `skill-plan-document-reviewer`
- Isolation: `current workspace`; preserve `.playwright-mcp/`, `db/`, and prior OCR plans
- Commit policy: `no commits during execution`
- Preauthorized local actions: edit listed source, test, validator, canonical documentation, and skill files; run focused tests, repository validators, adapter synchronization, and live local probes
- User-approval actions: push, merge, branch/worktree disposition, authentication, shared user-local runtime writes, destructive cleanup, and changes outside listed paths
- Parallel ownership: `none`; contract callers, validator rules, and canonical guidance share semantic names and require serialization
- Sequential fallback: contract and recovery integration → focused regression proof → canonical guidance and authority rules → validator proof → adapter sync and full verification

## Coordination State

- Coordination owner: `single lead controller`
- Coordination schema: `2`
- Branch: `main`
- Base commit: `eaf67df`
- Expected workspace: tracked tree clean; preserve untracked `.playwright-mcp/`, `db/`, `docs/superpowers/plans/2026-09-16-16-23-ocr-delegation-integration-plan.md`, and `docs/superpowers/plans/2026-09-16-ocr-delegation-hardening-plan.md`
- Next action: run Task 3 canonical guidance reconciliation after accepting Task 1 and Task 2 proof
- Blockers: `none`

| Task | State | Workspace | Executor | Depends On | Required Proof | Evidence |
| --- | --- | --- | --- | --- | --- | --- |
| Task 1 | `completed` | current | `codex` | none | contract caller scan and focused tests | `384 passed`; shared budget, identity, and reconciliation paths wired |
| Task 2 | `completed` | current | `codex` | Task 1 | launcher/dispatcher settlement and budget regressions | focused lifecycle suite passed; resource settlement uses shared proof |
| Task 3 | `completed` | current | `codex` | Task 2 | canonical guidance review and adapter sync | canonical ownership, continuation, command authority, and adapter outputs synchronized |
| Task 4 | `completed` | current | `codex` | Task 3 | validator unit tests and negative fixtures | `73 passed`; runtime boundary validator catches private policy regressions |
| Task 5 | `completed` | current | `codex` | Task 4 | full suite, validators, live probes, clean tracked state | `729 passed, 1 skipped`; focused `408 passed`; validators and adapter drift passed; live local lifecycle probe passed; latency measures unmeasured without real launcher/provider |

## Task Breakdown

### Task 1: Wire production callers and bounded recovery to attempt-contract semantics

**Purpose:** Remove semantic duplication from launcher and dispatcher and close
the interrupted-claim recovery gap without changing approved lifecycle
outcomes.

**Task Function:** Integrate shared public contract functions into existing
production paths.

**Template Profile:**
- Controller-selected: `none (lead controller)`
- Selection basis: shared backend contract with direct repository authority

**Specification Coverage:** Assignment identity, grant containment, budget
resolution, settlement proof, lifecycle interpretation, eligibility, and
bounded attempt-guard reconciliation.

**Required Skills:** `skill-systematic-debugging`, `skill-test-driven-development`, `skill-backend-verification`, `skill-code-standards`

**Files And Symbols:**
- Inspect: `scripts/herdr_attempt_contract.py:normalize_runtime_grant`,
  `resolve_attempt_budget`, `terminal_settlement_proven`,
  `derive_lifecycle_state`, and `eligibility_action`
- Inspect callers: `scripts/herdr_main_launcher.py:_normalize_runtime_grant`,
  `_classify_deepagents_outcome`, and budget/settlement branches;
  `scripts/herdr_parallel_dispatch.py:_grant_digest`, `_launcher_command`, and
  `classify`
- Inspect recovery: `scripts/dcode_project.py:_claim_attempt`,
  `_settle_attempt`, `_publish_result_receipt`, and the finalization path
- Inspect descriptor transport: `scripts/herdr_parallel_dispatch.py:_REQUIRED_FIELDS`,
  `_bind_requested_grant`, `_launcher_command`, and boolean field validation;
  `scripts/herdr_main_launcher.py:build_parser` and launch argument assembly
- Modify: `scripts/herdr_attempt_contract.py`,
  `scripts/dcode_project.py`,
  `scripts/herdr_main_launcher.py`, and
  `scripts/herdr_parallel_dispatch.py`
- Verify: `tests/test_herdr_attempt_contract.py`,
  `tests/test_dcode_project.py`,
  `tests/test_herdr_main_launcher.py`, and
  `tests/test_herdr_parallel_dispatch.py`

**Dependencies:** Preserve result-contract field names, existing receipt
correlation, native worker limits, settlement reserve, explicit grant
containment, and the existing ownership lock.

The budget contract is explicit: the lead controller supplies
`remaining_authorized_task_allowance` from the active task's durable
`Authority.cumulative_wall_clock_seconds` minus prior attempt allocations; when
usage is unknown, the full allocated wall-clock grant is charged. The launcher
measures elapsed attempt time and applies `settlement_reserve_seconds`;
`resolve_attempt_budget()` produces the effective worker budget;
`dcode-project` enforces that value at its worker boundary. Requested grant
values remain separate from effective execution values. No caller may derive
cumulative authority from pane output or provider timing.

**Authority:**
- Preauthorized local actions: edit Task 1 files and run named focused tests
- Stop for: required result-contract schema change, changed approved lifecycle
  meaning, or external runtime write

**Steps:**
1. Add test-first cases for no-claim admission, active blocking, same-binding
   idempotency, terminal-evidence reconciliation, insufficient authority, and
   insufficient settlement reserve before changing production callers.
2. Import `ADMISSION_RESULTS` from `herdr_attempt_contract.py` and remove the
   wrapper-local duplicate without changing serialized admission values.
3. Add one descriptor field named
   `remaining_authorized_task_allowance` for coordinated single-lane and
   parallel launches. Require a real nonnegative numeric value; reject strings
   such as `"false"` for `prior_attempt_known` and reject malformed budget
   inputs before worker launch.
4. Replace production uses of launcher-private grant normalization with
   `normalize_runtime_grant`; remove the private dispatcher import and delete
   the private helper only after repository references are updated.
5. At launcher admission, derive elapsed attempt time from the invocation clock,
   retain the configured settlement reserve, and call
   `resolve_attempt_budget(requested_grant, remaining_authorized_task_allowance,
   remaining_attempt_time, settlement_reserve_seconds)`. Forward only resolved
   worker timeout to `dcode-project`; preserve requested/effective grant
   evidence separately.
6. Replace duplicated dispatcher wall-clock and settlement policy with
   `resolve_attempt_budget` and `terminal_settlement_proven` using existing
   evidence fields.
7. Make launcher classification publish distinct execution, cleanup, task
   result, settlement, and lifecycle facts; use `derive_lifecycle_state` and
   `eligibility_action` for semantic mapping rather than inline mappings.
8. Add one `dcode-project` reconciliation operation under the existing
   ownership lock. It reads the current guard first, then uses only a
   correlated stored settlement record or retained receipt with verified
   cleanup and descendant retirement to settle an active claim. Unknown or
   mismatched evidence remains `RECOVERY_REQUIRED`.
9. Persist validated terminal settlement evidence in the guard before receipt
   removal using the existing atomic temp-file, `fsync`, and `os.replace`
   writer. Repeated same-binding invocation returns existing status; it never
   launches a second worker. Retained evidence remains usable after raw receipt
   expiry.
10. Keep `dcode-project` native worker and cleanup evidence authoritative for
   execution facts; do not move task acceptance into the dispatcher.
11. Search all production and test references to confirm no stale private helper,
   wrapper-local admission enum, or duplicate semantic predicate remains.

**Verification:**
- `python -m pytest -q tests/test_herdr_attempt_contract.py tests/test_herdr_main_launcher.py tests/test_herdr_parallel_dispatch.py`
- `python -m pytest -q tests/test_dcode_project.py`
- `rg -n "_normalize_runtime_grant|WHOLE_ATTEMPT_WALL_CLOCK_SECONDS|resource_settled" scripts tests`
- `rg -n "ADMISSION_RESULTS" scripts tests`
- Assert explicit `600` seconds succeeds when remaining authority and reserve
  contain it; insufficient authority and insufficient reserve reject before
  worker launch; native worker limits remain enforced by their owning boundary.
- Assert active claims with correlated terminal evidence reconcile under the
  existing lock, while unknown or mismatched evidence stays blocked.

**Exit Criteria:** Production callers use public contract functions; descriptor
identity and recovery fields validate before launch; one bounded recovery
operation handles interrupted claims; focused tests prove
unchanged receipt, lifecycle, budget, capacity, idempotency, and blocking
semantics; no launcher-private policy import remains.

### Task 2: Prove recovery, settlement separation, and continuation safety

**Purpose:** Prove interrupted claims reconcile safely, resource retirement does
not depend on semantic task-result acceptance, and uncertain ownership still
blocks redispatch.

**Task Function:** Extend existing tests around launcher classification and
dispatcher capacity.

**Template Profile:**
- Controller-selected: `none (lead controller)`
- Selection basis: focused failure-path regression proof

**Specification Coverage:** Runtime completion versus acceptance, cleanup and
descendant retirement, bounded capacity, retry safety, idempotent admission,
and explicit continuation after `NEEDS_CONTEXT`.

**Required Skills:** `skill-test-driven-development`, `skill-backend-verification`

**Files And Symbols:**
- Modify: `tests/test_herdr_main_launcher.py`,
  `tests/test_dcode_project.py`,
  `tests/test_herdr_parallel_dispatch.py`, and
  `tests/test_herdr_attempt_contract.py`
- Exercise: `herdr_main_launcher._classify_deepagents_outcome`, dispatcher
  `classify`, `dcode_project._claim_attempt`,
  `dcode_project._settle_attempt`, `terminal_settlement_proven`,
  `derive_lifecycle_state`, and `eligibility_action`

**Dependencies:** Task 1 production contract wiring is complete.

**Authority:**
- Preauthorized local actions: edit named tests and run focused test commands
- Stop for: behavior requiring new retry, acceptance, or observation authority

**Steps:**
1. Use the Task 1 red cases as the admission matrix: no claim with no known
   prior attempt is eligible; valid active ownership blocks replacement; same
   binding returns existing status; correlated terminal evidence with proven
   cleanup settles; known prior work with missing or inconsistent evidence
   returns `RECONCILE`.
2. Add a regression where an active guard has correlated terminal settlement
   evidence; reconciliation settles it under the existing lock without worker
   launch.
3. Add a regression where a retained correlated receipt proves retirement;
   reconciliation settles the guard and preserves the evidence before receipt
   removal. A receipt for another attempt never settles the current claim, and
   an expired raw receipt cannot erase durable guard evidence.
4. Add interruption tests between receipt publication, guard evidence
   persistence, guard settlement, and receipt deletion. Every restart path must
   either recover from correlated durable evidence or remain
   `RECOVERY_REQUIRED`; no partial state may authorize replay.
5. Add a regression where guard, receipt, or binding evidence is missing,
   stale, or mismatched; reconciliation returns `RECOVERY_REQUIRED` and keeps
   ownership occupied.
6. Add a regression where worker and descendants are retired and cleanup is
   confirmed while report or acceptance evidence is missing; capacity retires
   but task acceptance remains unresolved.
7. Add a regression where worker or descendants remain unknown; capacity stays
   occupied and eligibility returns `RECONCILE`.
8. Add a regression for same-binding idempotency and competing binding
   blocking, confirming no replacement launch is implied.
9. Add a regression for explicit budget containment and settlement reserve,
   including the `600`-second explicit grant case described by the verdict.
10. Add a regression that `NEEDS_CONTEXT` requests information but does not
   authorize replay without explicit continuation, settled prior ownership,
   remaining authority, and updated task context.
11. Keep pane and wait output as diagnostic input only; assert no test treats
   observation as acceptance or automatic retry authority.

**Verification:**
- `python -m pytest -q tests/test_herdr_attempt_contract.py tests/test_herdr_main_launcher.py tests/test_herdr_parallel_dispatch.py`
- `python -m pytest -q tests/test_dcode_project.py`
- `git diff --check`
- Test interruption cases with deterministic injected failures at each
  publication step; do not use sleep-based race tests.

**Exit Criteria:** Task 1 records red admission, recovery, and budget cases
before its production changes; this task adds and executes remaining
regressions without converting missing evidence into success; interrupted
claims reconcile only from correlated evidence; capacity, task-result, and
continuation states remain independently observable.

### Task 3: Converge canonical runtime and skill guidance

**Purpose:** Remove contradictory ownership and launch instructions from
maintained canonical documents.

**Task Function:** Update canonical guidance, not generated mirrors.

**Template Profile:**
- Controller-selected: `none (lead controller)`
- Selection basis: cross-document ownership and generation boundary

**Specification Coverage:** Plan plus Git recovery SSOT, CoS authority,
coordinated execution identity, MCP authorization/validation/forwarding, and
diagnostic observation limits.

**Required Skills:** `skill-code-standards`, `skill-plan-document-reviewer`

**Files And Symbols:**
- Modify canonical guidance:
  - `.agents/skills/skill-chief-of-staff/SKILL.md`
  - `.agents/skills/skill-deepagents-executing-plans/SKILL.md`
  - `.agents/skills/skill-dispatching-parallel-agents/SKILL.md`
  - `.agents/skills/skill-executing-plans/SKILL.md`
  - `docs/operating_system/runtime/runtime-surfaces.md`
  - `docs/operating_system/procedures/personal-local-worktree-procedure.md`
  - `docs/operating_system/procedures/runtime-adapter-procedure.md`
  - `docs/operating_system/tooling/runtime-tool-resolution.md`
  - `docs/operating_system/planning/planning-dispatch.md`
  - `docs/operating_system/rules/git-tracked-coordination-rule.md`
  - `docs/operating_system/rules/command-execution-rule.md`
  - `docs/operating_system/governance/precedence.md`
  - `docs/operating_system/governance/repo-governance.md`
  - `docs/operating_system/templates/agents/root-AGENTS.template.md`
  - `.agents/skills/skill-requesting-code-review/SKILL.md`
- Correct only stale current-state metadata in
  `docs/superpowers/plans/2026-09-17-deepagents-attempt-contract-consolidation-plan.md`:
  replace its obsolete next action and add a concise post-completion note;
  preserve historical task evidence.
- Generated outputs: `generated_agents/{codex,claude,antigravity}/...` only via
  `scripts/sync_agent_adapters.py`

**Dependencies:** Tasks 1 and 2 establish executable names and preserved
behavior. Canonical sources change before generated outputs.

**Authority:**
- Preauthorized local actions: edit named canonical docs and skills, run sync
  and documentation validators
- Stop for: new lifecycle policy, changed MCP trust boundary, or generated
  output that cannot be derived from canonical source

**Steps:**
1. State two launch modes: direct `dcode-project` for ordinary personal-local
   probes, and controller-owned launcher/dispatcher for Git-tracked coordinated
   DeepAgents assignments.
2. State that coordinated entry supplies assignment identity, repository and
   plan identity, lane identity, grant digest, and prior-attempt evidence
   internally; skills do not duplicate private flags.
3. Replace MAIN AGENT lifecycle ownership with bounded execution, lane-local
   changes, tactical decisions, and returned evidence.
4. Record the ownership map: Plan plus Git for workflow truth; CoS for
   authority, continuation, and acceptance; attempt contract for semantics;
   `dcode-project` for native execution facts; `owned_process.py` for owned
   process-tree lifetime; Herdr for delivery and diagnostics; dispatcher for
   wave admission and capacity aggregation.
5. Clarify recovery: runtime sessions are not workflow recovery truth; an
   unresolved attempt claim can fail closed for execution safety until
   ownership is reconciled.
6. Clarify MCP wording as controller authorization, `dcode-project` validation
   and enforcement, and Herdr forwarding when present.
7. Replace `NEEDS_CONTEXT` retry wording with one continuation contract:
   additional context is a request, not replay authority; retry requires
   settled prior resources, an explicit continuation decision by CoS when CoS
   is active or by the lead controller otherwise, remaining cumulative
   authority, and updated task context.
8. State that coordinated entry derives and transports assignment identity,
   grant digest, and `prior_attempt_known`; CoS does not manually reconstruct
   launcher-private fields.
9. Preserve approved receipt-aware observation wording and explicitly state
   that pane reads, waits, and markers cannot settle resources, retry work,
   continue plans, or accept task results.
10. State that one DeepAgents lane uses the launcher and an independent
    dependency-ready DeepAgents wave uses existing `herdr_parallel_dispatch.py`
    with `MAX_CONCURRENCY = 2`; Codex or mixed waves retain sequential target
    acquisition/delivery where required while independent workers may execute
    concurrently.
11. Reconcile command authorization: exact current authority must match
    repository, branch/ref, operation, lane/task, and conditions; absent or
    exceptional authority still requires confirmation.
12. Reconcile precedence: hard canonical rules constrain all projections;
    within that envelope, scoped instructions specialize or narrow root
    guidance and cannot weaken hard invariants.
13. Replace the active 60-second retry rationale with temporary bounded
    provider-backoff/latency policy pending native retry-contract proof.
14. Replace the review example's commit-message base discovery with the
    recorded approved base/checkpoint and `HEAD_SHA=$(git rev-parse HEAD)`.
15. Close the completed consolidation plan's stale next action with a factual
    note pointing to this corrective plan; do not rewrite historical claims.
16. State that stable discovery may be reused within one invocation, while
    mutable Git, worktree, claim, and process facts refresh before writes.
17. Clarify transport lifecycle versus worker lifecycle: Herdr transport
    termination is diagnostic and must not terminate or abandon a worker-owned
    claim; `dcode-project` owns worker supervision and cleanup evidence.
18. Run adapter synchronization after canonical skill edits.

**Verification:**
- `python scripts/sync_agent_adapters.py --all-platforms`
- `python scripts/sync_agent_adapters.py --all-platforms --check`
- `python scripts/validate_generated_header_format.py`
- `python scripts/validate_planning_lifecycle.py --repo-root .`

**Exit Criteria:** Maintained canonical guidance has one consistent boundary
model; authorization, precedence, continuation, retry rationale, and dispatch
entry paths agree; generated adapters match canonical skills; historical plan
evidence remains unchanged except for the named factual closure.

### Task 4: Enforce runtime-guidance boundary invariants

**Purpose:** Prevent the same documentation drift from returning after future
runtime changes.

**Task Function:** Add narrow static validation to the existing repository
contract validator.

**Template Profile:**
- Controller-selected: `none (lead controller)`
- Selection basis: small deterministic validator and unit-test surface

**Specification Coverage:** SSOT, canonical/generated boundaries, and
maintained guidance consistency.

**Required Skills:** `skill-test-driven-development`, `skill-code-standards`

**Files And Symbols:**
- Modify: `scripts/validate_repo_contracts.py` and
  `tests/test_validate_repo_contracts.py`
- Add no new validator script; reuse `ValidationIssue`, existing repository
  root resolution, and current validator command

**Dependencies:** Task 3 canonical wording is complete.

**Authority:**
- Preauthorized local actions: edit named validator and tests, run validator
  commands
- Stop for: validator rules requiring historical-plan rewrites, broad natural
  language parsing, or false-positive suppression by weakening the invariant

**Steps:**
1. Define a fixed list of maintained canonical files and mechanical assertions
   for private imports, duplicate admission definitions, and broken canonical
   references.
2. Add `validate_runtime_boundary_guidance(root)` returning existing
   `ValidationIssue` records with file, line-independent rule, and remediation
   message.
3. Invoke it from `validate_repo_contracts.py` before starter-kit
   classification, preserving existing exit behavior.
4. Add positive fixtures for shared admission constants, public contract imports,
   valid canonical references, and existing adapter-derived paths.
5. Add negative fixtures for private launcher imports, wrapper-local admission
   constants, and missing canonical references.
6. Record semantic wording review in Task 3 evidence; do not claim static text
   checks prove equivalent prose is absent.
7. Keep completed plans, generated adapters, and user-local runtime paths out
   of this validator's scan.

**Verification:**
- `python -m pytest -q tests/test_validate_repo_contracts.py`
- `python scripts/validate_repo_contracts.py --repo-root . --fast`
- `python scripts/validate_repo_contracts.py --repo-root .`

**Exit Criteria:** Validator catches each named regression with a focused
negative fixture and passes current canonical guidance without scanning
historical plans or generated outputs.

### Task 5: Fresh integration verification and live probes

**Purpose:** Prove source, tests, generated surfaces, and local runtime
boundaries agree before plan completion.

**Task Function:** Run final repository and live boundary verification.

**Template Profile:**
- Controller-selected: `none (lead controller)`
- Selection basis: final acceptance and local runtime evidence

**Specification Coverage:** All implementation outcomes and preserved
non-goals.

**Required Skills:** `skill-backend-verification`, `skill-verification-before-completion`, `skill-disposable-artifact-cleanup`

**Files And Symbols:**
- Verify all Task 1–4 targets and generated adapter outputs.
- Live probe existing local contract paths through the smallest temporary
  directory under the repository: admitted, same-binding idempotent,
  competing binding blocked, harmless worker completion, cleanup confirmed.

**Dependencies:** Tasks 1–4 complete and accepted by the lead controller.

**Authority:**
- Preauthorized local actions: run declared tests, validators, sync checks,
  temporary local probes, and safe cleanup of probe-owned files
- Stop for: external authentication, shared runtime deployment, unresolved
  descendant ownership, or any untracked path not created by this task

**Steps:**
1. Run focused backend tests for contract, launcher, dispatcher, process, and
   deployment behavior.
2. Run the full test suite and record fresh output.
3. Run repository validators, generated-header validation, adapter drift check,
   and `git diff --check`.
4. Run live local admission and cleanup probes without external provider calls.
5. Record four baseline measures only when their real launcher or dispatcher
   path is exercised: dispatch-to-claim latency, completion-to-capacity-release
   latency, controller tool calls per attempt, and attempts requiring manual
   reconciliation. Define timestamps and denominators in the probe report;
   record `unmeasured` when a path is not exercised. Do not substitute fixture
   timings or claim an optimization result.
6. Verify temporary probe artifacts are removed and unrelated untracked paths
   remain untouched.
7. Reconcile plan evidence, task states, and Git diff before any completion
   claim. Do not commit or push under this plan.

**Verification:**
- `python -m pytest -q tests/test_herdr_attempt_contract.py tests/test_herdr_main_launcher.py tests/test_herdr_parallel_dispatch.py tests/test_owned_process.py tests/test_deploy_agent_runtime.py tests/test_validate_repo_contracts.py`
- `python -m pytest -q`
- `python scripts/validate_repo_contracts.py --repo-root .`
- `python scripts/sync_agent_adapters.py --all-platforms --check`
- `python scripts/validate_generated_header_format.py`
- `git diff --check`
- Deterministic report records `ADMITTED`, `IDEMPOTENT`, `BLOCKED`,
  `RECONCILE`, successful harmless worker completion, confirmed cleanup, and
  recovery outcomes.
- Operational report records launcher/dispatcher measures only when those
  paths run: timestamps use monotonic start/end pairs, denominators count
  completed attempts or attempts in the exercised wave, and unavailable values
  are `unmeasured`.

**Exit Criteria:** Fresh automated and live evidence proves contract ownership,
capacity separation, guidance parity, validator coverage, and unchanged
unrelated workspace state.

## Verification

The lead controller accepts each task only after its declared proof passes.
Final verification must show:

- production source has no duplicate semantic owner for grant, budget,
  settlement, lifecycle, or eligibility;
- coordinated and ordinary DeepAgents launch guidance is distinguishable;
- Plan plus Git remains workflow recovery SSOT;
- observation remains transient diagnostic evidence;
- generated adapters pass all-platform drift checks;
- full test suite and repository validators pass;
- live local probes show admission, idempotency, blocking, worker completion,
  cleanup, and bounded reconciliation;
- baseline latency and tool-call measures are recorded without claiming an
  optimization result;
- unrelated untracked paths remain unmodified and untracked.

## Completion Criteria

- Tasks 1–5 are `completed` in this plan's ledger with command output recorded.
- No unresolved P1 or required P2 review finding remains in maintained source,
  tests, or canonical guidance.
- No historical completed plan is broadly rewritten; only its named stale
  next-action and completion note receive factual closure.
- No shared user-local runtime deployment occurs.
- No commit, push, merge, or branch disposition occurs under this plan;
  those actions require separate explicit authorization.

## Rollback And Stop Conditions

- Revert only the current task's uncommitted changes when focused proof shows
  a contract or lifecycle regression; preserve prior committed fixes.
- Stop before changing result schema, receipt schema, MCP trust behavior,
  retry cap, concurrency, or approved spec semantics.
- Stop before making `dcode-project` return asynchronously after claim; that
  requires a separate approved transport specification and ownership proof.
- Stop when validator wording cannot distinguish maintained canonical guidance
  from historical evidence without broad text heuristics.
- Stop before modifying untracked paths not created by Task 5 probes.

## Deferred Follow-Up

Receipt-confirmed fast-path observation reduction and asynchronous
return-after-claim remain deferred. The current approved spec requires bounded
process and pane probes, and transport detachment needs separate ownership
proof. Create a spec amendment before changing either behavior. Do not add a
scheduler, lifecycle ledger, or automatic retry mechanism to solve them.
