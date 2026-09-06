---
layer: change
artifact_type: plan
template_id: implementation-plan
contract_version: "1"
status: completed
name: cos-adaptive-lane-grants
parent_spec: none
targets:
  - docs/operating_system/rules/git-tracked-coordination-rule.md
  - docs/operating_system/planning/planning-dispatch.md
  - docs/operating_system/templates/implementation-plan-template.md
  - docs/operating_system/procedures/personal-local-worktree-procedure.md
  - .agents/skills/skill-chief-of-staff/SKILL.md
  - scripts/validate_planning_lifecycle.py
  - scripts/herdr_main_launcher.py
  - tests/test_validate_planning_lifecycle.py
  - tests/test_herdr_main_launcher.py
  - tests/test_skill_chief_of_staff.py
  - generated_agents/
---

# CoS Adaptive Runtime Grants

## Goal

Add bounded, transient CoS-selected runtime grants without creating a second
authority or runtime-state system. Preserve native DeepAgents budgets by
default, expose only enforceable runtime controls, and make task `Authority`
the validated ceiling for adaptive execution.

The reviewed verdict is directionally correct but incomplete: the repository
has the authority and tactical-autonomy foundations, while Runtime Grant remains
design-only. Implementation must define grant fields, enforcement evidence,
safe redispatch, validator behavior, runtime projection, and generated-surface
reconciliation before enabling adaptive execution.

## Implementation Outcomes

### Validated authority ceiling

Proposed and active Git-tracked plans require a non-empty task `Authority`
contract with explicit preauthorized actions and stop conditions. Completed
plans, including historical `contract_version: "1"` plans, are not
retroactively checked against this wording.

### Transient Runtime Grant contract

CoS may assign a transient subset of task authority containing only defined
resource and capability fields. No persistent grant registry, YAML state file,
profile budget, or runtime recovery ledger is added.

The contract records, at minimum:

- `turns`: `native` or positive integer;
- `wall_clock_seconds`: `native` or positive integer;
- capability exposure intent resolved by the existing Runtime Tool Resolution
  path;
- concrete executor selectors recorded only in launch evidence.

Every launch reports requested value, effective value, and enforcement mode:
`native`, `runtime`, `outer-watchdog`, or `unsupported`.

### Safe runtime projection

DeepAgents keeps native inner execution budgets when no explicit grant exists.
Explicit `--max-turns` and `--timeout` values are projected only when granted.
Strict Codex turn limits remain `native` or fail closed; prompt text is never
treated as runtime enforcement. Existing MCP default-deny behavior remains.

### Safe grant adjustment

Grant changes use retire-and-redispatch, not hot mutation. Redispatch preserves
plan task identity, records a transient `grant_digest` in launcher evidence,
proves old process retirement,
reconciles plan plus Git state, and rejects duplicate active execution.

### Reconciled canonical and generated surfaces

Canonical rules, planning guidance, CoS skill text, runtime procedures,
launcher behavior, tests, and generated agent mirrors agree. Generated files
are refreshed from canonical sources only.

## Execution Approach

- Mode: `inline sequential`
- Coordination: `git-tracked`
- Default task executor: `codex`
- Required skills: `skill-executing-plans`, `skill-code-standards`, `skill-backend-verification`, `skill-verification-before-completion`
- Isolation: `current workspace`
- Commit policy: `no commits during execution`
- Preauthorized local actions: inspect named sources and tests; edit declared canonical files; add focused regression tests; run local validators, adapter synchronization, dry-run launcher checks, and bounded runtime probes; preserve existing modified and untracked workspace state
- User-approval actions: authentication, runtime installation, external MCP writes, commits, push, merge, publication, destructive cleanup, discard of existing changes, and changes outside declared targets
- Parallel ownership: none; shared canonical docs, launcher contracts, and generated outputs require one sequential writer
- Sequential fallback: baseline workspace, define contract, validate plans, project runtime, reconcile CoS guidance, synchronize generated outputs, run final proof

## Coordination State

- Coordination owner: `single lead controller`
- Coordination schema: `2`
- Branch: `main`
- Base commit: `48c26be`
- Reconciled at commit: `48c26be`
- Expected workspace: preserve untracked `.playwright-mcp/` and `db/`; do not reset, clean, or overwrite them
- Next action: run fresh completion verification for this reconciled historical plan
- Blockers: none

| Task | State | Workspace | Executor | Depends On | Required Proof | Evidence |
| --- | --- | --- | --- | --- | --- | --- |
| Task 1 | `completed` | current | `codex` | none | baseline and contract decision | reviewed verdict patched plan; Git status, source review, contract fields and redispatch rules recorded |
| Task 2 | `completed` | current | `codex` | Task 1 | validator regression proof | `26 passed`; proposed/active Authority enforced; completed legacy wording preserved |
| Task 3 | `completed` | current | `codex` | Task 1 | runtime projection proof | `31 passed`; Herdr projection and fail-closed bounds covered; wrapper verify-only |
| Task 4 | `completed` | current | `codex` | Tasks 2-3 | canonical guidance proof | canonical docs and mirrors synchronized; consumer/runtime boundary reconciled |

## Task Breakdown

### Task 1: Freeze baseline and define grant contract

**Purpose:**
- Establish source-of-truth boundaries and settle exact transient grant and redispatch semantics before runtime changes.

**Task Function:**
- Reconcile reviewed architecture with current repository contracts and dirty-workspace constraints.

**Template Profile:**
- Controller-selected: `none (lead controller)`
- Selection basis: authority-bearing contract definition requires direct controller ownership; no delegation benefit before the contract is fixed.

**Validator Profile (optional):**
- Controller-selected: `review`
- Selection basis: independent adversarial review of authority, runtime enforcement, redispatch, and scope boundaries.

**Specification Coverage:**
- Plan Authority is the maximum ceiling.
- `Worker Runtime Grant ⊆ Main Runtime Grant`; `Plan Lane Authority ⊆ task Authority`.
- Profile files remain capability identity, not runtime policy.
- Grant changes use retire-and-redispatch, not hot mutation.
- Runtime session state never becomes recovery truth.

**Required Skills:**
- `skill-chief-of-staff`, `skill-code-standards`

**Files And Symbols:**
- Inspect: `docs/operating_system/rules/git-tracked-coordination-rule.md`
- Inspect: `docs/operating_system/planning/planning-dispatch.md`
- Inspect: `docs/operating_system/templates/implementation-plan-template.md`
- Inspect: `scripts/herdr_main_launcher.py:resolve_launch`
- Inspect: `scripts/dcode_project.py:_worker_timeout` and worker launch path
- Verify: repository status, branch, `HEAD`, expected base, and named preserved changes

**Dependencies:**
- None.

**Authority:**
- Preauthorized local actions: read-only inspection; update this proposed plan if contract findings require exact wording changes; run Git status and source checks
- Stop for: request to discard or overwrite existing changes; need for new persistent state; unsupported runtime enforcement; authority, scope, or acceptance changes outside this plan

**Steps:**
- [x] Step 1: Record current Git/workspace baseline without cleanup.
- [x] Step 2: Define normalized grant fields, defaults, enforcement labels, and MCP selector boundary.
- [x] Step 3: Define redispatch preconditions, task identity, transient `grant_digest`, retirement proof, and duplicate-run rejection.
- [x] Step 4: Confirm no grant field requires `agents/*.toml`, persistent runtime state, or prompt-only enforcement.

**Verification:**
- [x] Inspect current rule, template, launcher, wrapper, and runtime procedure sources.
- Expected: every proposed field has one canonical owner, one enforceable projection or explicit unsupported result, and one recovery-safe adjustment path.

**Exit Criteria:**
- Contract is explicit enough for validator and runtime implementation without inventing behavior.

### Task 2: Enforce task Authority in planning lifecycle

**Purpose:**
- Make proposed and active Git-tracked plan Authority structurally required while preserving completed-plan compatibility.

**Task Function:**
- Extend planning lifecycle validation with the smallest stable Authority check.

**Template Profile:**
- Controller-selected: `normal`
- Selection basis: bounded validator and test change with clear source/test ownership and low implementation ambiguity.

**Validator Profile (optional):**
- Controller-selected: `review`
- Selection basis: independent validation of fail-closed parsing and historical compatibility.

**Specification Coverage:**
- Proposed and active Git-tracked plans require exactly one non-empty `Preauthorized local actions` and `Stop for` entry per task.
- Completed plans are not retroactively checked against the new wording.
- Free-form Authority text is structural evidence, not a replacement for runtime grant subset checks.

**Required Skills:**
- `skill-code-standards`, `skill-backend-verification`

**Files And Symbols:**
- Inspect: `scripts/validate_planning_lifecycle.py:validate_execution_contract`
- Inspect: `scripts/validate_planning_lifecycle.py:validate_git_coordination`
- Modify: `scripts/validate_planning_lifecycle.py:validate_execution_contract`
- Modify: `tests/test_validate_planning_lifecycle.py`
- Verify: `docs/operating_system/templates/implementation-plan-template.md`

**Dependencies:**
- Task 1 complete.

**Authority:**
- Preauthorized local actions: edit named validator and focused tests; run focused pytest and planning validation
- Stop for: schema redesign beyond task Authority presence and structure; changes to historical artifact policy; unrelated plan failures requiring source changes

**Steps:**
- [x] Step 1: Add proposed/active Git-tracked Authority section detection and exact non-empty field checks.
- [x] Step 2: Add missing, duplicate, malformed, and historical compatibility tests.
- [x] Step 3: Run focused validator tests and inspect findings against current plans.

**Verification:**
- [x] `py -3 -m pytest tests/test_validate_planning_lifecycle.py -q`
- Expected: new Authority failures are detected; existing valid proposed, active, and completed plans retain expected status.

**Exit Criteria:**
- Lifecycle validator proves the plan has a usable Authority boundary before adaptive execution can start.

### Task 3: Project enforceable grants through Herdr

**Purpose:**
- Add optional Herdr runtime grant projection while preserving native defaults, DeepAgents direct-MCP default-deny, and executor-specific enforcement truth.

**Task Function:**
- Implement bounded launcher and wrapper projection with direct boundary tests.

**Template Profile:**
- Controller-selected: `high`
- Selection basis: cross-module runtime contract, security-sensitive MCP boundary, subprocess lifecycle, and failure-path risk.

**Validator Profile (optional):**
- Controller-selected: `review`
- Selection basis: independent review of command construction, evidence accuracy, unsupported bounds, and cleanup.

**Specification Coverage:**
- No explicit budget grant preserves DeepAgents native inner behavior.
- Explicit DeepAgents bounds project through existing supported wrapper flags `--max-turns` and `--timeout`.
- Herdr outer watchdog remains separately reported.
- Strict Codex turn limits are unsupported unless runtime-enforceable.
- DeepAgents direct MCP projection remains default-deny; only approved selectors project into isolated runtime configuration.
- Capability exposure intent is resolved by the adapter; concrete selectors and task identity are bound to launch evidence.

**Required Skills:**
- `skill-code-standards`, `skill-backend-verification`

**Files And Symbols:**
- Inspect: `scripts/herdr_main_launcher.py:build_parser`, `resolve_launch`, `main`
- Inspect: `scripts/dcode_project.py:_reject_unmanaged_runtime_options`, `_worker_timeout`, `main`
- Modify: `scripts/herdr_main_launcher.py`
- Modify: `tests/test_herdr_main_launcher.py`
- Verify: `scripts/dcode_project.py` and existing `tests/test_dcode_project.py` changes without reverting them
- Verify: `docs/operating_system/procedures/personal-local-worktree-procedure.md`

**Dependencies:**
- Task 1 complete.
- Existing uncommitted `scripts/dcode_project.py` and `tests/test_dcode_project.py` changes remain preserved and are verify-only scope.

**Authority:**
- Preauthorized local actions: edit named launcher/wrapper/tests; run focused tests, dry-run command construction, and bounded local subprocess probes
- Stop for: authentication or runtime installation; unsupported strict Codex enforcement; MCP policy expansion; cleanup or overwrite of existing workspace artifacts

**Steps:**
- [x] Step 1: Add validated optional grant inputs and normalized evidence without adding persistent grant state.
- [x] Step 2: Project DeepAgents explicit bounds only when present; preserve native defaults otherwise.
- [x] Step 3: Preserve approved `--mcp-select` projection and DeepAgents direct-MCP default-deny behavior.
- [x] Step 4: Add transient `grant_digest`, outer-watchdog ceiling checks, and fail-closed unsupported strict bounds.
- [x] Step 5: Add success, failure, timeout, MCP, redaction, cleanup, and unchanged-Git-state tests.

**Verification:**
- [x] `py -3 -m pytest tests/test_herdr_main_launcher.py tests/test_dcode_project.py -q`
- Expected: focused tests prove native defaults, explicit DeepAgents limits, DeepAgents direct-MCP default-deny, approved selection, unsupported Codex bounds, redaction, and cleanup behavior.

**Exit Criteria:**
- Launcher and wrapper expose only defined, enforceable grants and report actual enforcement without changing default execution behavior.

### Task 4: Reconcile canonical CoS and runtime guidance

**Purpose:**
- Align durable rules and operational guidance with implemented grant semantics and safe redispatch behavior.

**Task Function:**
- Update canonical coordination, planning, CoS, and runtime documentation without duplicating ownership.

**Template Profile:**
- Controller-selected: `normal`
- Selection basis: bounded canonical documentation reconciliation after implementation facts are available.

**Validator Profile (optional):**
- Controller-selected: `review`
- Selection basis: independent stale-claim and generated-source review.

**Specification Coverage:**
- CoS controls exposure and resource grant; MAIN AGENT chooses tactics within grant.
- Tool availability does not imply authority.
- Redispatch is the only grant adjustment mechanism.
- Native, runtime, outer-watchdog, and unsupported enforcement are not conflated.

**Required Skills:**
- `skill-code-standards`

**Files And Symbols:**
- Modify: `docs/operating_system/rules/git-tracked-coordination-rule.md`
- Modify: `docs/operating_system/planning/planning-dispatch.md`
- Modify: `docs/operating_system/templates/implementation-plan-template.md`
- Modify: `docs/operating_system/procedures/personal-local-worktree-procedure.md`
- Modify: `.agents/skills/skill-chief-of-staff/SKILL.md`
- Verify: `tests/test_skill_chief_of_staff.py`
- Verify: `docs/operating_system/tooling/runtime-tool-resolution.md`

**Dependencies:**
- Tasks 2 and 3 complete.

**Authority:**
- Preauthorized local actions: edit named canonical documentation and skill source; run focused text-contract tests and repository planning validation
- Stop for: new policy owner, new persistent artifact, contradiction with runtime behavior, or documentation claim lacking executable evidence

**Steps:**
- [x] Step 1: Add the grant subset invariant and transient-state boundary to coordination rules.
- [x] Step 2: Add grant and redispatch guidance to planning and CoS canonical sources.
- [x] Step 3: Document DeepAgents native defaults and Herdr outer-watchdog distinction.
- [x] Step 4: Remove unsupported or prompt-only enforcement claims.

**Verification:**
- [x] `py -3 -m pytest tests/test_skill_chief_of_staff.py -q`
- [x] Run planning contract tests plus `py -3 scripts/validate_planning_lifecycle.py` after reconciling current plan state.
- Expected: canonical guidance matches launcher behavior and no stale fixed-budget claim remains.

**Exit Criteria:**
- Maintained sources describe one coherent contract with no conflicting runtime or authority claims.

## Verification

- `py -3 -m pytest -q`
- `py -3 scripts/validate_planning_lifecycle.py`
- `git diff --check`
- `py -3 scripts/sync_agent_adapters.py --check --all-platforms`
- Generated-header, starter-kit, repository-contract, and adapter-parity validators
- Fresh bounded Herdr/DeepAgents probe with captured launch, enforcement, retirement, cleanup, and Git-state evidence

## Completion Criteria

The plan is ready for completion verification when:

1. the Authority contract and Runtime Grant fields have one canonical owner;
2. validator behavior covers proposed, active, malformed, and completed plans;
3. launcher and wrapper behavior preserves native defaults and reports real enforcement;
4. redispatch cannot duplicate active work or bypass plan/Git reconciliation;
5. DeepAgents direct MCP remains default-deny outside explicitly approved selectors;
6. canonical documentation, skills, tests, and generated outputs agree;
7. focused tests, full tests, validators, diff checks, and runtime probe produce fresh evidence;
8. existing modified and untracked workspace state remains preserved and no unrelated cleanup occurs.

The plan may be marked `completed` only after `skill-verification-before-completion`
returns `verified` against fresh repository evidence.
