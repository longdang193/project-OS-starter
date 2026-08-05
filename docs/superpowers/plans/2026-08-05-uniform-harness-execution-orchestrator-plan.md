---
artifact_type: plan
template_id: implementation-plan
status: completed
layer: change
parent_spec: docs/superpowers/specs/2026-08-05-uniform-harness-execution-orchestrator.md
---

# Uniform Harness Execution Orchestrator Plan

## Goal

Extend existing `scripts/harness_task.py` into one managed, packet-driven
execution lifecycle. Preserve controller decision authority, existing
standalone `preflight` and `verify` compatibility, and current SSOT boundaries.

## Implementation Outcomes

### Managed run lifecycle

`scripts/harness_task.py` owns one managed-run lifecycle:
`classify → preflight → authorize → workspace → dispatch → claim → verify → outcome → controller decision`.
Each run persists one atomic `.harness/runs/<run-id>/run.json` record with
immutable attempt packets, lanes, claims, evidence, friction, decisions, and
state history. Controller alone writes this record.

### Honest authorization and verification

Managed write attempts use declared `planned_write_paths`, controller-issued
approval records, a complete Git change-set snapshot, and criterion-level
evidence. Approval, automated proof, and semantic review remain distinct.

### Capability-gated mode expansion

Static route policy remains in `repo_config/harness.yaml`; role contracts remain
in `agents/roles.yaml`; host adapter capability remains runtime state. Initial
execution supports only `single_agent` when a supplied host adapter reports it
`enforced`; permitted but unavailable modes block without fallback. Generic CLI
use has no platform adapter and records this block honestly; host code calls the
injectable managed-run boundary when it can dispatch an agent.

### Migration-safe controller protocol

Existing `preflight` and `verify` CLI inputs remain usable. Managed runs gain
validated requests, common outcomes, controller decisions, bounded retries,
approval resume, and interrupted-run recovery. Controller skills and generated
instructions describe this protocol without duplicating policy.

## Execution Approach

- Mode: `harness sequential_agents`
- Required skills: `skill-executing-plans`, `skill-code-standards`, `skill-test-driven-development`, `skill-backend-verification`, `skill-subagent-driven-development`, `skill-verification-before-completion`
- Isolation: current workspace; shared executor, policy, and tests change serially.
- Commit policy: no commits during execution.
- Parallel ownership: none. Later host-adapter integration may use isolated parallel workspaces only through validated lane plans.
- Sequential fallback: implement and prove `single_agent` adapter boundary first; leave sequential and parallel modes capability-unavailable until concrete adapters exist.

## Task Breakdown

### Task 1: Extend static harness policy

**Purpose:**
- Add lifecycle state, retry, and managed-route policy. Keep runtime capability
  and mutable run state outside configuration.

**Specification Coverage:**
- Controller classification and preflight.
- One lifecycle for every execution mode.
- Bounded retries and approval resume.
- Static policy, role contract, and run state have separate SSOTs.

**Required Skills:**
- `skill-central-config-layer`
- `skill-code-standards`
- `skill-test-driven-development`

**Files And Symbols:**
- Inspect: `repo_config/harness.yaml`
- Inspect: `agents/roles.yaml`
- Modify: `repo_config/harness.yaml:states`
- Modify: `repo_config/harness.yaml:routes`
- Modify: `scripts/validate_harness_config.py:validate`
- Modify: `tests/test_validate_harness_config.py`
- Modify: `scripts/render_harness_routing.py:render` only if newly canonical route fields require generated routing visibility.
- Verify: `tests/test_render_harness_routing.py`

**Dependencies:**
- Approved parent specification.
- Existing roles remain canonical in `agents/roles.yaml`; do not copy role behavior into route policy.

**Steps:**
- [ ] Add `awaiting_decision` and valid shared transitions to `states`; retain `accepted` and `blocked` as terminal states.
- [ ] Add named retry policies with maximum attempts, retryable reasons, exhaustion behavior, and approval-resume rules; make each managed route name exactly one policy.
- [ ] Validate route retry-policy references, state graph references, retry bounds and reasons, orchestration constraints, and role/template pairings.
- [ ] Keep executor capability out of YAML. Policy may permit a mode; runtime adapter reports whether it can enforce that mode.
- [ ] Regenerate `docs/operating_system/tooling/harness-routing.generated.md` only when renderer output changes from canonical route policy.

**Verification:**
- [ ] `python -m pytest tests/test_validate_harness_config.py tests/test_render_harness_routing.py -q`
- Expected: valid policy passes; missing retry policy, invalid retry bounds, invalid state transition, and invalid route references fail deterministically.
- [ ] `python scripts/validate_harness_config.py --repo-root .`
- Expected: canonical policy validates.
- [ ] `python scripts/render_harness_routing.py --repo-root . --check`
- Expected: generated routing artifact is fresh.

**Exit Criteria:**
- Static policy names lifecycle facts it owns and rejects malformed references without claiming runtime adapter support.

### Task 2: Add managed run records and immutable attempts

**Purpose:**
- Build managed-run request, packet, lane, outcome, and run-record handling inside existing harness owner.

**Specification Coverage:**
- Reproducible run authority.
- Immutable packet per attempt.
- Explicit lane plan.
- Controller is sole run-record writer.
- Policy permission and executor capability are distinct.

**Required Skills:**
- `skill-code-standards`
- `skill-test-driven-development`
- `skill-backend-verification`

**Files And Symbols:**
- Inspect: `scripts/harness_task.py:resolve_task`
- Modify: `scripts/harness_task.py:HarnessError`
- Modify: `scripts/harness_task.py:resolve_task`
- Modify: `scripts/harness_task.py:main`
- Add symbols in `scripts/harness_task.py`: managed request validation, immutable base-commit resolution, lane-plan normalization, run-record load/store, and managed-run preflight.
- Modify: `tests/test_harness_task.py`
- Verify: `.gitignore`

**Dependencies:**
- Task 1 complete.
- `.harness/` remains ignored runtime state; no versioned run artifact exists.

**Steps:**
- [ ] Define versioned managed-run input with task type, requested mode, base reference, allowed paths, planned write paths for write-capable roles, typed criteria, and optional controller metadata.
- [ ] Resolve `base_ref` to immutable commit before dispatch; record commit ID in packet instead of mutable branch name.
- [ ] Normalize every managed attempt to one lane plan. `single_agent` yields one writable `primary` lane; reject duplicate IDs, invalid dependencies, cycles, and overlapping writable paths before workspace setup.
- [ ] Store one `run.json` per run under `.harness/runs/<run-id>/`; write temp then replace for atomic controller-only persistence. Include request, ordered attempts, active state, and ordered state history.
- [ ] Store immutable packet snapshots within attempts. Retry, escalation, and approval resume create successor attempts; no in-place packet mutation.
- [ ] Keep version-1 `preflight` behavior working. Reject v1 plain criteria as sufficient managed-run acceptance until explicit review evidence exists.

**Verification:**
- [ ] `python -m pytest tests/test_harness_task.py -q`
- Expected: managed preflight records resolved base commit, creates one primary lane, rejects malformed lane plans, and preserves v1 standalone behavior.
- [ ] Add direct tests for atomic run persistence, immutable successor packet, invalid transition, and interrupted record reload.
- Expected: malformed or partial run input cannot become accepted attempt.

**Exit Criteria:**
- Managed lifecycle has one local run SSOT. Static policy and role catalog stay outside `run.json` except immutable packet snapshots.

### Task 3: Centralize authorization and change-set evidence

**Purpose:**
- Replace claim-trusted approval and incomplete diff discovery with shared controller-owned evidence.

**Specification Coverage:**
- Complete change-set snapshot.
- Common gate engine.
- Approval records are controller-owned evidence.
- Symmetric gates.

**Required Skills:**
- `skill-code-standards`
- `skill-test-driven-development`
- `skill-backend-verification`

**Files And Symbols:**
- Inspect: `scripts/harness_task.py:_path_matches`
- Inspect: `scripts/harness_task.py:_changed_paths`
- Inspect: `scripts/harness_task.py:_validate_claim`
- Inspect: `scripts/harness_task.py:verify_task`
- Modify: `scripts/harness_task.py:_path_matches`
- Modify: `scripts/harness_task.py:_changed_paths`
- Modify: `scripts/harness_task.py:_validate_claim`
- Modify: `scripts/harness_task.py:verify_task`
- Add symbols in `scripts/harness_task.py`: change-set collector, approval record validator, and common gate evaluator.
- Modify: `tests/test_harness_task.py`

**Dependencies:**
- Task 2 complete.
- Gate patterns remain policy-owned in `repo_config/harness.yaml`.

**Steps:**
- [ ] Reuse one normalized path matcher for planned-write authorization and actual post-execution gate evaluation. Keep `allowed_paths` as maximum scope, never planned-write intent.
- [ ] Collect tracked staged and unstaged added, modified, deleted, and renamed paths against resolved base commit plus untracked nonignored paths. Persist path and change kind in attempt evidence.
- [ ] Validate controller-issued approval fields: gate, approver identity, approved path scope, attempt ID, and issuance time. Match approved scope and gate before dispatch or acceptance.
- [ ] Ignore `claim.approved_gates` for managed runs; preserve standalone compatibility only where version-1 contract requires it.
- [ ] Block before dispatch for unapproved protected planned writes. Block after execution for protected actual changes outside approved scope.

**Verification:**
- [ ] Add parameterized direct tests using identical patterns for planned and actual path inputs.
- Expected: same protected path yields matching gate result at both stages.
- [ ] Add tests for untracked scope escape, renamed/deleted protected path, forged claim approval, stale/mismatched controller approval, and no-dispatch pre-gate block.
- Expected: none bypasses scope or gate enforcement.
- [ ] `python -m pytest tests/test_harness_task.py -q`
- Expected: current scope and approval tests still pass with managed-run proof.

**Exit Criteria:**
- Only fresh repository evidence and controller approval records authorize managed protected changes.

### Task 4: Make criteria evidence-based

**Purpose:**
- Replace implicit acceptance with criterion-level automated, review, or manual evidence states.

**Specification Coverage:**
- Honest verification.
- Evidence-based verification.
- Review and approval are different evidence paths.

**Required Skills:**
- `skill-code-standards`
- `skill-test-driven-development`
- `skill-backend-verification`

**Files And Symbols:**
- Inspect: `scripts/harness_task.py:verify_task`
- Modify: `scripts/harness_task.py:verify_task`
- Add symbols in `scripts/harness_task.py`: typed criterion validator and criterion evidence evaluator.
- Modify: `tests/test_harness_task.py`

**Dependencies:**
- Tasks 2 and 3 complete.

**Steps:**
- [ ] Define managed criteria with stable ID, evidence kind, and expected source. Support configured command evidence, change-set evidence, and reviewer/manual evidence without treating them as interchangeable.
- [ ] Record every criterion as `proven`, `failed`, or `review_required` with evidence reference in attempt evidence.
- [ ] Run configured checks once per attempt and attach output records only to criteria that declare those checks as evidence.
- [ ] Require semantic review evidence before acceptance when criteria or route policy need it; approval record never satisfies semantic review.
- [ ] Preserve standalone v1 output shape where possible, but prevent managed run from auto-proving plain text criteria solely because no blocker exists.

**Verification:**
- [ ] Add tests for passing command and diff criteria, failed command criterion, missing evidence declaration, review-required criterion, and approval/review non-substitution.
- Expected: managed run accepts only when every required criterion is proven.
- [ ] `python -m pytest tests/test_harness_task.py -q`
- Expected: verifier returns evidence records and no implicit criterion success.

**Exit Criteria:**
- Acceptance evidence identifies why each criterion passed, failed, or awaits review.

### Task 5: Execute one controller-owned lifecycle

**Purpose:**
- Add common state transitions, outcomes, decisions, retries, approval resume, and friction capture around managed attempts.

**Specification Coverage:**
- Uniform lifecycle execution.
- Uniform decision protocol.
- Bounded retries and approval resume.
- Friction capture without autonomous mutation.

**Required Skills:**
- `skill-code-standards`
- `skill-test-driven-development`
- `skill-backend-verification`

**Files And Symbols:**
- Inspect: `scripts/harness_task.py:verify_task`
- Inspect: `scripts/harness_task.py:main`
- Modify: `scripts/harness_task.py:main`
- Add symbols in `scripts/harness_task.py`: lifecycle runner, outcome builder, controller-decision validator, retry-policy evaluator, approval-resume handler, and friction recorder.
- Modify: `tests/test_harness_task.py`

**Dependencies:**
- Tasks 1 through 4 complete.

**Steps:**
- [ ] Export one injectable `run_managed(root, request, adapter, ...)` callable as managed lifecycle owner. Keep controller classification outside executor.
- [ ] Add CLI `run` and controller-decision/resume entrypoints. CLI uses explicit unavailable adapter unless a platform host calls the injectable boundary; it must persist `execution_mode_unavailable`, never pretend it dispatched work.
- [ ] Apply one ordered state machine for every mode: `classified`, `planned`, `running`, `observed`, `verifying`, `awaiting_decision`, then terminal `accepted` or `blocked`.
- [ ] Emit machine-readable outcome with reason, evidence references, and permitted decisions. Accept only controller `accept`, `retry`, `escalate`, `request_approval`, or `block` decisions matching state and retry policy.
- [ ] Create successor attempts for retry, escalation, and valid approval resume. Enforce max attempts, retryable reasons, exhaustion behavior, and stale approval rejection from policy.
- [ ] Record normalized friction with category, attempt/lane source, observed evidence, and proposed improvement. Never auto-edit policy, skills, tools, or adapters from friction.
- [ ] Resume interrupted run only from persisted state; never repeat accepted attempt or duplicate recorded decision.

**Verification:**
- [ ] Add direct tests for accepted single attempt, failed check, invalid claim, retry successor, escalation successor, retry exhaustion, request approval, approval resume, invalid decision, and interrupted-run recovery.
- Expected: all non-normal paths emit common outcome records and preserve prior attempts unchanged.
- [ ] `python -m pytest tests/test_harness_task.py -q`
- Expected: lifecycle histories follow configured transitions only.

**Exit Criteria:**
- Executor applies transitions and records evidence. Controller still owns classification and final decisions.

### Task 6: Add host adapter boundary and single-agent proof

**Purpose:**
- Make dispatch and workspace capability explicit without claiming Python can call platform agent tools directly.

**Specification Coverage:**
- Controlled mode expansion.
- Workspace preparation and lane ownership.
- Agent dispatch and claim collection.
- Policy permission and executor capability are distinct.

**Required Skills:**
- `skill-code-standards`
- `skill-test-driven-development`
- `skill-backend-verification`

**Files And Symbols:**
- Inspect: `scripts/harness_task.py:main`
- Modify: `scripts/harness_task.py`
- Add symbols in `scripts/harness_task.py`: host adapter capability discovery, workspace preparation, lane dispatch, cancellation, and claim collection boundary.
- Modify: `tests/test_harness_task.py`

**Dependencies:**
- Tasks 2 through 5 complete.
- No Python code directly invokes Codex `spawn_agent`; host integration supplies adapter operations.

**Steps:**
- [ ] Define minimal adapter operations: `capabilities`, `prepare_workspace`, `dispatch_lane`, `cancel_lane`, and `collect_claim`. Use small callable or protocol boundary; add no daemon, scheduler, or adapter class hierarchy.
- [ ] Keep platform-specific Codex, Claude, or other client adapters outside this starter. A host supplies the adapter at its own integration boundary.
- [ ] Model support per mode as `enforced`, `advisory`, or `unavailable`. Dispatch only when policy allows mode and adapter reports `enforced`; otherwise persist `execution_mode_unavailable` and do not fall back.
- [ ] Implement only `single_agent` lifecycle behavior. Prepare current workspace, dispatch one `primary` lane, collect one normalized claim, and use shared verifier.
- [ ] Leave sequential and parallel capability-unavailable until real host adapters provide lane dispatch, dependency ordering, isolated workspaces, cancellation, and claim collection.
- [ ] Add fake adapter tests for success, capability block, workspace failure, dispatch failure, claim-shape failure, cancellation, and no-dispatch after preflight or approval block.

**Verification:**
- [ ] `python -m pytest tests/test_harness_task.py -q`
- Expected: fake enforced single-agent adapter completes shared lifecycle; unavailable mode never dispatches.
- [ ] Inspect test spy calls.
- Expected: preflight, gate, and capability failures make zero workspace or dispatch calls.

**Exit Criteria:**
- First executable mode works behind tested host boundary. Unsupported modes block instead of degrading behavior.

### Task 7: Align controller documentation and generated instruction surfaces

**Purpose:**
- Publish controller workflow derived from policy and executor contracts; remove old manual orchestration guidance from generated adapters.

**Specification Coverage:**
- Migration-safe controller protocol.
- Static policy, role contract, and run state have separate SSOTs.
- Friction capture without autonomous mutation.

**Required Skills:**
- `skill-subagent-driven-development`
- `skill-writing-skills`

**Files And Symbols:**
- Inspect: `.agents/skills/skill-subagent-driven-development/SKILL.md`
- Inspect: `docs/operating_system/templates/agents/root-AGENTS.template.md`
- Inspect: `docs/operating_system/tooling/code-intelligence-tools.md`
- Modify: `.agents/skills/skill-subagent-driven-development/SKILL.md`
- Modify: `docs/operating_system/templates/agents/root-AGENTS.template.md` only where controller instructions must cite managed lifecycle commands.
- Modify: `docs/operating_system/tooling/code-intelligence-tools.md` only if tool capability/friction procedure needs exact new reference.
- Generate: `AGENTS.md`
- Generate: `generated_agents/**`
- Verify: `scripts/sync_agent_adapters.py`
- Verify: `tests/test_skill_subagent_driven_development_assets.py`
- Verify: `tests/test_sync_agent_adapters.py`

**Dependencies:**
- Tasks 1 through 6 complete.
- Generated files are outputs. Edit canonical sources only.

**Steps:**
- [ ] Replace manual controller orchestration sequence with managed-run packet, outcome, controller-decision, and verified-evidence protocol.
- [ ] State capability limits plainly: controller uses only enabled modes; no silent fallback; no direct platform dispatch claim where adapter is absent.
- [ ] Define friction handoff to `skill-improve-harness` as evidence-based backlog input, not automatic self-mutation.
- [ ] Run adapter sync after canonical instruction edits. Do not edit generated surfaces by hand.

**Verification:**
- [ ] `python scripts/sync_agent_adapters.py --check`
- Expected: generated instruction surfaces match canonical sources.
- [ ] `python -m pytest tests/test_skill_subagent_driven_development_assets.py tests/test_sync_agent_adapters.py -q`
- Expected: controller and generated asset contracts pass.
- [ ] `python scripts/validate_repo_contracts.py --fast`
- Expected: generated boundaries and harness configuration validate together.

**Exit Criteria:**
- Controller docs describe one lifecycle, one packet authority per attempt, one mutable run record, and one decision owner.

### Task 8: Run fresh end-to-end contract verification

**Purpose:**
- Prove managed lifecycle behavior, policy contract, generated-surface sync, and starter distribution without claiming unimplemented modes work.

**Specification Coverage:**
- All parent-spec validation claims and completion criteria.

**Required Skills:**
- `skill-verification-before-completion`
- `skill-backend-verification`

**Files And Symbols:**
- Verify: `scripts/harness_task.py`
- Verify: `repo_config/harness.yaml`
- Verify: `agents/roles.yaml`
- Verify: `tests/test_harness_task.py`
- Verify: `tests/test_validate_harness_config.py`
- Verify: `tests/test_render_harness_routing.py`
- Verify: `docs/operating_system/tooling/harness-routing.generated.md`
- Verify: `repo_config/starter-kit-manifest.json`

**Dependencies:**
- Tasks 1 through 7 complete.

**Steps:**
- [ ] Run focused harness tests before broad repository checks.
- [ ] Inspect one fake-adapter managed-run artifact for state history, immutable packet, lane claim, change-set evidence, criterion evidence, outcome, controller decision, and friction record.
- [ ] Run canonical config, generation, starter-kit, and whitespace checks.
- [ ] Record unavailable platform-adapter integration, skipped checks, or failed checks as incomplete or blocked; never report sequential/parallel execution as implemented without real adapter evidence.

**Verification:**
- [ ] `python -m pytest tests/test_validate_harness_config.py tests/test_harness_task.py tests/test_render_harness_routing.py tests/test_skill_subagent_driven_development_assets.py tests/test_sync_agent_adapters.py tests/test_starter_kit_generation.py -q`
- Expected: harness, policy, generated-surface, and starter packaging coverage passes.
- [ ] `python scripts/validate_repo_contracts.py`
- Expected: repository contracts pass.
- [ ] `python scripts/validate_agent_runtime_drift.py --skip-deploy-check`
- Expected: canonical and generated runtime artifacts have no drift.
- [ ] `python scripts/build_starter_kit.py; if ($LASTEXITCODE -eq 0) { python scripts/validate_starter_kit.py }`
- Expected: starter kit contains first-layer harness sources and excludes `.harness/` runtime state.
- [ ] `git diff --check`
- Expected: no whitespace errors.

**Exit Criteria:**
- `single_agent` has direct boundary proof. Other modes have concrete adapter evidence or remain explicitly unavailable.

## Verification

- `python -m pytest tests/test_validate_harness_config.py tests/test_harness_task.py tests/test_render_harness_routing.py tests/test_skill_subagent_driven_development_assets.py tests/test_sync_agent_adapters.py tests/test_starter_kit_generation.py -q`
- `python scripts/validate_harness_config.py --repo-root .`
- `python scripts/render_harness_routing.py --repo-root . --check`
- `python scripts/validate_repo_contracts.py`
- `python scripts/validate_agent_runtime_drift.py --skip-deploy-check`
- `python scripts/build_starter_kit.py`
- `python scripts/validate_starter_kit.py`
- `git diff --check`

## Completion Criteria

The implementation is ready for completion verification when:

1. managed execution uses one controller-owned `run.json` and immutable per-attempt packets
2. policy, role contracts, runtime capability, and mutable run state retain separate named owners
3. managed authorization uses planned and actual path gates with same matcher, complete change-set evidence, and controller-issued approvals
4. every managed criterion records direct automated, review, or manual evidence and never auto-proves from absence of blockers
5. `single_agent` runs only through enforced host adapter; unsupported modes block without fallback
6. retry, escalation, approval resume, blocked states, and interruption preserve immutable prior attempts and obey configured bounds
7. canonical controller docs and generated adapters are synchronized
8. final verification passes or records remaining platform-adapter work as blocked rather than complete

The plan may be marked `completed` only when `skill-verification-before-completion` returns `verified` from fresh repository evidence.

## Execution Record

- 2026-08-05 — verified: managed run records, immutable successor attempts,
  controller-issued approval gates, complete Git change snapshots,
  criterion-level evidence, bounded retry, approval resume, and host-adapter
  capability gating are covered by direct harness tests.
- 2026-08-05 — verified: controller instructions use managed lifecycle and
  generated adapters are synchronized.
- 2026-08-05 — passed: focused suite, repository contracts, runtime drift,
  starter-kit build and validation, and `git diff --check`.
- Deliberate boundary: generic CLI has no platform dispatch adapter. It records
  `execution_mode_unavailable`; platform host must inject adapter before agent
  dispatch. `sequential_agents` and `parallel_lanes` remain unavailable.
