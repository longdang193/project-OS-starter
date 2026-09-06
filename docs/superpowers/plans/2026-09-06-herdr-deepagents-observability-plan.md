---
layer: change
artifact_type: plan
template_id: implementation-plan
contract_version: "1"
status: completed
name: herdr-deepagents-observability
targets:
  - scripts/herdr_main_launcher.py
  - tests/test_herdr_main_launcher.py
  - docs/operating_system/runtime/runtime-surfaces.md
  - docs/operating_system/procedures/runtime-adapter-procedure.md
  - docs/operating_system/procedures/personal-local-worktree-procedure.md
  - docs/operating_system/tooling/runtime-tool-resolution.md
  - README.md
---

# Herdr DeepAgents Observability

## Goal

Give Herdr controller reliable visibility into Codex and DeepAgents work while
preserving one SSOT, symmetric executor handling, default-deny MCP policy, and
minimal maintenance across Herdr and DeepAgents releases.

## Implementation Outcomes

### Pull-based controller observation

Herdr remains transient observation authority. Controller can inspect session,
pane, process, lifecycle, and recent terminal output through Herdr's existing
CLI/API commands without a new supervisor, database, event bus, heartbeat, or
runtime ledger.

### Symmetric evidence contract

Codex and DeepAgents use one semantic observation record with executor, session,
pane, agent identity, task hash, lifecycle state, last observation, and evidence
source. Codex evidence uses agent lifecycle commands; DeepAgents evidence uses
pane-process commands. Tura maps to the same vocabulary through its own
`dcode-project`/`project-delegate` wrapper, without expanding Herdr launcher
scope. Transport-specific details stay in adapter procedures; Git-tracked plan
plus Git remain workflow and recovery truth.

### Safe ambiguity handling

Missing output, unchanged output, command timeout, and unavailable pane produce
`unknown` or `stuck_suspected` evidence only. Controller never auto-kills,
retries, advances, or treats silence as completion. Output is metadata-only by
default; task text, MCP results, credentials, and raw output require an
explicit disposable probe.

### Release-resilient admission

A bounded probe checks installed Herdr command and output contracts plus the
pinned DeepAgents runtime path. Unsupported command shape, version drift,
non-zero launch, timeout, and cleanup remain fail-closed and visible.

## Execution Approach

- Mode: `parallel-capable`
- Coordination: `git-tracked`
- Default task executor: `codex`
- Required skills: `skill-code-standards`, `skill-backend-verification`, `skill-dispatching-parallel-agents`, `skill-verification-before-completion`
- Isolation: `current workspace`
- Commit policy: `no commits during execution`
- Preauthorized local actions: inspect source and installed Herdr help; add this plan; edit declared launcher/tests/canonical docs; regenerate adapters; run bounded local probes with existing permissions; run tests and validators
- User-approval actions: credentials, authentication, runtime installation, external MCP writes, commits, push, merge, publication, destructive cleanup, and changes outside declared targets
- Parallel ownership: review lanes read-only; one implementation writer owns launcher/tests/docs after review
- Sequential fallback: capability probe, plan review, justified patch, focused proof, generated sync, final verification

## Coordination State

- Coordination owner: `single lead controller`
- Coordination schema: `2`
- Branch: `main`
- Base commit: `f7d02858be32f4c85a6f2b01eaa13f5a15d457ad`
- Expected workspace: preserve existing modified Herdr/MCP guidance files and untracked `.playwright-mcp/`, `db/`, and `out/`; do not reset, clean, or overwrite them
- Next action: verified; hand off to branch-finishing only if Git disposition is authorized
- Blockers: none

| Task | State | Workspace | Executor | Depends On | Required Proof | Evidence |
| --- | --- | --- | --- | --- | --- | --- |
| Task 1 | `completed` | current | `codex` | none | Herdr help and disposable observation probe | `herdr 0.8.2`; server snapshot, pane list/get, process-info, and bounded pane read passed; server had no pre-existing session and was stopped before probe |
| Task 2 | `completed` | current | `codex` | Task 1 | independent plan review and accepted findings | review found six issues; plan patched for timeout, executor paths, dirty scope, Tura scope, generated SSOT, and raw-output boundary |
| Task 3 | `completed` | current | `codex` | Task 2 | focused launcher/test proof for only justified code changes | `pytest -q tests/test_herdr_main_launcher.py`: 28 passed; finite subprocess timeout and observation evidence covered |
| Task 4 | `completed` | current | `codex` | Task 3 | canonical/generated parity and contract validators | adapter check, starter validation, repository contracts, and planning validation passed |
| Task 5 | `completed` | current | `codex` | Task 4 | final verification with fresh evidence | `pytest -q`: 356 passed; validators, adapter parity, diff check, launcher dry-run, and Herdr 0.8.2 live probe passed |

## Task Breakdown

### Task 1: Establish Native Observation Contract

**Purpose:**
- Prove Herdr's stable pull-based inspection surface before writing code.

**Task Function:**
- Run capability discovery and a disposable local probe; record only verified
  command names, JSON/text shape, exit behavior, and cleanup outcome.

**Template Profile:**
- Controller-selected: `normal`
- Selection basis: bounded runtime contract discovery.

**Validator Profile:**
- Controller-selected: `review`
- Selection basis: independent command and evidence-shape check.

**Files And Symbols:**
- Inspect: `scripts/herdr_main_launcher.py`, `scripts/dcode_project.py`
- Inspect: Herdr commands `api snapshot`, `pane list`, `pane get`,
  `pane process-info`, `pane read`, `pane report-agent`, and `agent get`.
- Do not add persistent files or runtime state.

**Dependencies:**
- None.

**Authority:**
- Preauthorized: read-only local commands and disposable probe in existing
  session/pane only.
- Stop for: authentication, external writes, missing safe disposable target,
  or command contract that cannot be verified.

**Steps:**
- [x] Confirm Herdr version and help for required inspection commands.
- [x] Probe one harmless bounded DeepAgents or pane command using existing
  runtime configuration; retain only redacted metadata and discard raw output.
- [x] Compare Codex agent fields, DeepAgents pane-process fields, and Tura
  wrapper fields without requiring one transport to expose another's fields.
- [x] Record substitutions or unsupported fields in plan coordination state.

**Verification:**
- [x] `herdr --version`
- [x] `herdr api snapshot`
- [x] `herdr pane --help`
- [x] `herdr agent --help`
- Expected: commands exit normally and expose enough state to distinguish
  working, blocked, idle, failed, unavailable, and unknown without raw task
  data. Any `pane read` or `agent read` output is disposable, explicitly
  redacted probe input and never becomes stored evidence.

**Exit Criteria:**
- Native pull contract proven, or plan explicitly narrows to commands proven
  available. No custom observer is justified by assumption.

### Task 2: Independent Plan Review

**Purpose:**
- Find unsafe, contradictory, unprovable, or overbuilt plan requirements before
  activation.

**Task Function:**
- Review this plan against repository source, tests, generated boundaries, and
  Task 1 evidence. Return findings first using `P1`, `P2`, and `P3` severity.

**Template Profile:**
- Controller-selected: `review`
- Selection basis: independent readiness review.

**Validator Profile:**
- Controller-selected: `xhigh`
- Selection basis: cross-runtime SSOT, symmetry, and release-resilience risk.

**Files And Symbols:**
- Review: this plan, launcher entry points, current runtime procedures,
  `docs/operating_system/runtime/runtime-surfaces.md`, and related tests.
- Review generated surfaces only as parity consumers, never as canonical edit
  targets.

**Dependencies:**
- Task 1 complete.

**Authority:**
- Read-only review. Do not edit source, tests, generated files, or plan state.

**Steps:**
- [x] Check each named file, command, field, dependency, and exit criterion.
- [x] Check default-deny MCP, credential boundaries, no-persistent-supervisor
  policy, and ambiguity handling.
- [x] Check Codex/DeepAgents/Tura symmetry without pretending transports match.
- [x] Return smallest safe corrections only.

**Verification:**
- [x] Reviewer returns `implementation-ready`, or lists required `P1`/`P2`
  corrections with repository evidence.

**Exit Criteria:**
- Review findings accepted by lead; plan remains `proposed` until justified
  corrections are patched.

### Task 3: Apply Justified Minimal Patch

**Purpose:**
- Implement only review-approved changes needed for controller visibility.

**Task Function:**
- Patch one canonical implementation surface and its focused tests, reusing
  Herdr native pull commands. Prefer documentation/tests-only change when the
  probe proves current launcher already exposes required identity.

**Template Profile:**
- Controller-selected: `normal`
- Selection basis: bounded launcher and contract edits after review.

**Validator Profile:**
- Controller-selected: `review`
- Selection basis: focused regression and scope review.

**Files And Symbols:**
- Modify only if justified: `_run`/`_run_checked` in
  `scripts/herdr_main_launcher.py` and focused tests in
  `tests/test_herdr_main_launcher.py`. Every Herdr IPC call gets a finite
  timeout; catch `subprocess.TimeoutExpired` and fail closed with
  `LaunchBlocked` (or return `unknown` for an observation-only read). No
  controller path may hang on unbounded `subprocess.run`.
- Modify canonical guidance: runtime surfaces and procedures, `README.md`, and
  related canonical docs named in Task 4. Do not modify pre-existing dirty
  `tests/test_starter_kit_generation.py` in this plan; reconcile it separately
  only if a focused failure proves it is required.
- Derived output: `generated_agents/` is sync output, never a direct edit target.

**Dependencies:**
- Task 2 accepted findings.

**Authority:**
- Preauthorized: declared files and focused checks.
- Stop for: need for daemon/state store, raw-output persistence, MCP policy
  widening, or changes to DeepAgents release internals.

**Steps:**
- [x] Patch smallest root-cause owner identified by review.
- [x] Keep one semantic evidence shape with executor-specific source labels.
- [x] Use `agent get`/`agent read` for Codex and `pane process-info`/`pane read`
  for DeepAgents; do not require agent lifecycle state for a pane process.
- [x] Keep default-deny MCP and `codex.mcp.handoff.v1` facts/provenance boundary.
- [x] Add one regression check for new branch or parser logic; no framework or
  speculative abstraction.

**Verification:**
- [x] `pytest -q tests/test_herdr_main_launcher.py`
- Expected: current and new observation/ambiguity/timeout cases pass; no
  launcher command can wait forever.

**Exit Criteria:**
- Controller can inspect active work without relying on buffered launcher
  output, and no unproven runtime contract is introduced.

### Task 4: Reconcile Canonical And Generated Surfaces

**Purpose:**
- Remove stale or misleading guidance while preserving generated-file ownership.

**Task Function:**
- Update canonical runtime docs, sync adapters, and run contract checks.

**Template Profile:**
- Controller-selected: `normal`
- Selection basis: bounded SSOT/generated parity work.

**Validator Profile:**
- Controller-selected: `review`
- Selection basis: stale-text and generated-output verification.

**Files And Symbols:**
- Modify canonical docs only: runtime surfaces, runtime-adapter procedure,
  personal-local procedure, runtime-tool-resolution, and README.
- Verify derived `generated_agents/` output through adapter sync; never hand-edit
  generated files. Read existing `tests/test_starter_kit_generation.py`, but do
  not claim ownership of its pre-existing dirty changes.

**Dependencies:**
- Task 3 complete.

**Authority:**
- Preauthorized: canonical docs, generated sync, and local validators.
- Stop for: conflict with unrelated pre-existing edits.

**Steps:**
- [x] State Herdr pull observation commands and semantic evidence ownership.
- [x] State Codex agent versus DeepAgents pane-process commands; document Tura
  only under its own wrapper path.
- [x] State `unknown`/`stuck_suspected` behavior and no auto-recovery.
- [x] State raw-output and secret redaction boundary: metadata by default;
  explicit disposable redacted probe only.
- [x] Run adapter sync; verify generated parity.

**Verification:**
- [x] `python scripts/sync_agent_adapters.py --check --all-platforms`
- [x] `python scripts/validate_starter_kit.py`
- [x] `python scripts/validate_repo_contracts.py --fast`
- Expected: canonical/generated surfaces agree; no stale black-box or
  no-MCP-only claim remains outside historical plans.

**Exit Criteria:**
- One canonical policy explains controller observation for all executors;
  adapter views match it.

### Task 5: Final Verification

**Purpose:**
- Prove behavior, safety, parity, and preservation before any Git disposition.

**Task Function:**
- Run fresh focused, repository, and bounded live evidence checks.

**Template Profile:**
- Controller-selected: `review`
- Selection basis: independent completion verification.

**Validator Profile:**
- Controller-selected: `none`
- Selection basis: final review lane owns validation.

**Files And Symbols:**
- Verify all changed files and current Git diff.
- Verify Herdr observation probe, launcher failure/timeout paths, and generated
  output parity.

**Dependencies:**
- Task 4 complete.

**Authority:**
- Read-only verification and bounded local probes.
- Stop for: authentication, external side effects, unrelated failures, or
  dirty-state ambiguity.

**Steps:**
- [x] Run focused launcher tests.
- [x] Run full test suite and repository validators.
- [x] Run one disposable live observation probe with metadata-only output.
- [x] Confirm launcher IPC timeout and failure paths do not hang the controller.
- [x] Confirm pre-existing modified files and untracked paths remain preserved.

**Verification:**
- [x] `pytest -q`
- [x] `git diff --check`
- [x] `python scripts/validate_starter_kit.py`
- [x] `python scripts/validate_repo_contracts.py --fast`
- Expected: all required checks pass; live probe returns inspectable state or a
  documented `unknown` result without false completion.

**Exit Criteria:**
- `skill-verification-before-completion` returns `verified`; plan status may
  then move to `completed` by lead controller.

## Verification

- `pytest -q`
- `python scripts/validate_starter_kit.py`
- `python scripts/validate_repo_contracts.py --fast`
- `python scripts/sync_agent_adapters.py --check --all-platforms`
- `git diff --check`
- bounded Herdr live observation probe using existing local session/pane only

## Completion Criteria

The plan is ready for completion verification when:

1. Herdr native pull observation is proven for available runtime surfaces.
2. Controller evidence distinguishes lifecycle states without treating silence
   as completion or introducing a persistent supervisor.
3. Codex, DeepAgents, and Tura share semantic evidence ownership while keeping
   transport differences explicit.
4. Default-deny MCP, credential exclusion, handoff provenance, and cleanup
   contracts remain intact.
5. Canonical docs and generated adapters agree with implementation.
6. Fresh tests, validators, diff checks, and bounded live probe pass.
7. Existing dirty files and disposable paths remain intact.
