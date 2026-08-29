---
layer: change
artifact_type: plan
template_id: implementation-plan
contract_version: "1"
status: proposed
name: ssot-herdr-main-agent-launcher
targets:
  - scripts/herdr_main_launcher.py
  - scripts/agent_profile_registry.py
  - tests/test_herdr_main_launcher.py
  - docs/operating_system/runtime/runtime-surfaces.md
  - docs/operating_system/planning/planning-dispatch.md
---

# SSOT Herdr Main-Agent Launcher

## Goal

Provide one registry-driven launch path for independent top-level Codex main
agents inside Herdr. Keep `agents/*.toml` as the only profile/model source,
keep Herdr responsible only for main-agent topology and terminal observability,
and keep executor selection separate from profile selection.

The launcher must resolve `profile -> model`, reject missing or mismatched
bindings, start Codex through Herdr, and print enough returned identity for a
human or validator to verify the live pane. No per-profile launcher, duplicate
Codex profile file, automatic fallback, native Codex subagent, DeepAgents
worker, Tura worker, or `multi_agent_v1` call belongs in this change.

## Implementation Outcomes

### Registry-driven Herdr launch

Add one cross-platform Python launcher that accepts a discovered profile,
Herdr session, pane, and optional display name; loads the selected profile
through `scripts/agent_profile_registry.py`; resolves its canonical model; and
starts one `codex` agent through Herdr using that resolved model. The launcher
fails closed when the profile, registry, Herdr executable, or required binding
is unavailable.

### Symmetric verification and documentation

Use identical launch logic for ranked profiles (`low`, `normal`, `high`,
`xhigh`) and explicit-only profiles (`review`, `ui`). Record profile, executor,
provider, model, session, pane, and agent name in machine-readable preflight
output, then verify Herdr detection and terminal output with a bounded live
probe. Document ownership boundaries and the single launch path without
copying profile data.

## Execution Approach

- Mode: `inline sequential`
- Coordination: `git-tracked`
- Default task executor: `codex`
- Required skills: `skill-code-standards`, `skill-backend-verification`, `skill-executing-plans`, `skill-verification-before-completion`
- Isolation: `current workspace`; preserve existing uncommitted changes
- Commit policy: `no commits during execution`; Git disposition requires separate explicit authorization
- Preauthorized local actions: inspect named source and tests; add the declared launcher and focused test; update the declared operating-system docs; run declared local checks; run bounded read-only Herdr probes in the existing `codex-probe` session
- User-approval actions: install or update tools; authenticate; change provider configuration; create or delete Herdr sessions; stop or discard existing panes; delete untracked user data; commit; push; merge; publish
- Parallel ownership: none; registry contract, launcher, tests, docs, and runtime proof have one dependency chain
- Sequential fallback: complete Tasks 1–3 in order, then run Task 4 only after focused and repository checks pass

## Coordination State

- Coordination owner: `single lead controller`
- Coordination schema: `2`
- Branch: `main`
- Base commit: `0430dc6164a692a38fce60c353d2de97f29c5572`
- Expected workspace: existing tracked changes preserved; existing user untracked `.playwright-mcp/` and `db/` preserved; task-owned `out/` handled only under explicit cleanup authorization
- Next action: inspect current Herdr command contract and implement launcher contract using the existing registry loader
- Blockers: Herdr runtime state may differ between planning and execution; re-resolve session, pane, and executable at execution time

| Task | State | Workspace | Executor | Depends On | Required Proof | Evidence |
| --- | --- | --- | --- | --- | --- | --- |
| Task 1 | `pending` | current | `codex` | none | launcher help plus registry-backed dry-run contract | pending |
| Task 2 | `pending` | current | `codex` | Task 1 | focused launcher tests | pending |
| Task 3 | `pending` | current | `codex` | Task 1 | docs and contract validators | pending |
| Task 4 | `pending` | current | `codex` | Tasks 1–3 | Herdr agent detection, live marker acknowledgement, terminal readback | pending |

## Task Breakdown

### Task 1: Add registry-driven Herdr launcher

**Purpose:**
- Start one independent top-level Codex main-agent pane from a canonical repository profile without duplicating profile/model configuration.

**Task Function:**
- Resolve and bind one profile to one Herdr Codex pane.

**Template Profile:**
- Controller-selected: `none (lead controller)`
- Selection basis: small, deterministic launcher change with direct repository and runtime contracts; no delegated benefit.

**Validator Profile:**
- Controller-selected: `none`
- Selection basis: focused tests and final verification cover the bounded launcher contract.

**Specification Coverage:**
- `agents/*.toml` is the SSOT for profile identity, provider, model, rank, and instructions.
- Executor selection remains independent from profile selection.
- Herdr owns only independent top-level Codex main-agent topology and observability.
- Missing or mismatched profile/model binding returns `BLOCKED` or nonzero failure; no fallback.
- All profiles use one symmetric launch path.

**Required Skills:**
- `skill-code-standards`, `skill-backend-verification`

**Files And Symbols:**
- Inspect: `scripts/agent_profile_registry.py:load_agent_profiles`
- Inspect: `agents/*.toml:profile records`
- Inspect: installed `herdr agent start --help` and `codex --help`
- Modify: `scripts/herdr_main_launcher.py:main`, `resolve_launch`, `run_launch` (new symbols)
- Verify: `scripts/herdr_main_launcher.py`

**Dependencies:**
- Existing `AgentProfile` loader and Herdr `agent start` command remain available.
- Herdr executable is resolved from current PATH; no stale absolute path is stored.

**Authority:**
- Preauthorized local actions: add launcher file; read registry and executable help; run dry-run and missing-input checks.
- Stop for: registry schema changes; provider/auth changes; new fallback behavior; direct edits to generated agent surfaces; Herdr session or pane deletion.

**Steps:**
- [ ] Step 1: Define CLI inputs `--profile`, `--session`, `--pane`, optional `--name`, optional repository root, and `--dry-run`.
- [ ] Step 2: Load selected profile with `load_agent_profiles`, resolve `herdr` with `shutil.which`, and reject unknown or unavailable bindings before launch.
- [ ] Step 3: Build one symmetric Herdr command using `agent start`, `--kind codex`, and the registry-resolved model; never accept caller-supplied model or provider overrides.
- [ ] Step 4: Print sorted JSON preflight fields `profile`, `executor`, `model_provider`, `model`, `session`, `pane`, and `agent` before invoking Herdr; propagate Herdr exit status and stderr.

**Verification:**
- [ ] `py -B scripts/herdr_main_launcher.py --help`
- Expected: help lists required profile/session/pane inputs and dry-run mode.
- [ ] `py -B scripts/herdr_main_launcher.py --profile xhigh --session codex-probe --pane w1:p5 --dry-run`
- Expected: JSON reports `profile=xhigh`, `executor=codex`, `model=combo-xhigh`, and no process launch.
- [ ] Unknown profile and missing Herdr executable checks
- Expected: nonzero exit with actionable failure; no fallback model or alternate executor.

**Exit Criteria:**
- One launcher resolves every profile through the existing registry and emits exact launch facts without duplicate configuration.

### Task 2: Add focused launcher contract tests

**Purpose:**
- Prevent profile/model drift, fallback behavior, and asymmetric profile handling.

**Task Function:**
- Exercise launcher resolution and failure boundaries with deterministic subprocess seams.

**Template Profile:**
- Controller-selected: `normal`
- Selection basis: bounded test authoring; low ambiguity and low runtime risk.

**Validator Profile:**
- Controller-selected: `review`
- Selection basis: independent contract inspection is sufficient; no rank relationship required.

**Specification Coverage:**
- Registry is sole profile/model source.
- `xhigh` resolves to `combo-xhigh`; `review` remains explicit-only but follows same command shape.
- Caller cannot inject a different model or executor.
- Launcher propagates runtime failure and does not mutate repository state.

**Required Skills:**
- `skill-test-driven-development`, `skill-code-standards`

**Files And Symbols:**
- Inspect: `scripts/agent_profile_registry.py:AgentProfile`
- Modify: `tests/test_herdr_main_launcher.py:test_dry_run_uses_registry_model`, `test_profiles_share_launch_shape`, `test_unknown_profile_fails`, `test_herdr_missing_fails` (new symbols)
- Verify: `scripts/herdr_main_launcher.py`, `tests/test_herdr_main_launcher.py`

**Dependencies:**
- Task 1 launcher CLI and pure resolution seam complete.
- Tests use temporary profile files and mocked subprocess/`shutil.which`; no Herdr process, credentials, network, or repository mutation.

**Authority:**
- Preauthorized local actions: add one focused test file and run it.
- Stop for: broad test refactor; new dependency; tests that create persistent runtime artifacts.

**Steps:**
- [ ] Step 1: Test `xhigh` dry-run output and exact `combo-xhigh` model binding.
- [ ] Step 2: Parameterize ranked and explicit-only profiles to prove identical launch shape and default agent naming.
- [ ] Step 3: Test unknown profile, missing Herdr, invalid profile registry, and Herdr nonzero exit paths.
- [ ] Step 4: Assert no caller model/provider/executor override can replace registry facts.

**Verification:**
- [ ] `py -m pytest tests/test_herdr_main_launcher.py -q`
- Expected: all focused tests pass without creating persistent files outside pytest temporary storage.

**Exit Criteria:**
- Focused tests fail on profile/model drift, fallback, asymmetric launch paths, and missing runtime boundaries.

### Task 3: Document ownership and runtime contract

**Purpose:**
- Make SSOT, executor selection, Herdr topology, and evidence boundaries discoverable without duplicating profile data.

**Task Function:**
- Reconcile operating-system documentation with implemented launcher behavior.

**Template Profile:**
- Controller-selected: `normal`
- Selection basis: bounded documentation reconciliation with low implementation ambiguity.

**Validator Profile:**
- Controller-selected: `review`
- Selection basis: independent source-to-doc contract check; no rank relationship required.

**Specification Coverage:**
- `agents/*.toml` remains canonical profile registry.
- `scripts/agent_profile_registry.py` remains canonical loader.
- Herdr manages only independent top-level Codex main-agent sessions.
- Codex, DeepAgents, and Tura executor paths remain distinct.
- Runtime output reports enough identity for transparent observation.

**Required Skills:**
- `skill-code-standards`

**Files And Symbols:**
- Inspect: `docs/operating_system/runtime/runtime-surfaces.md:Canonical Sources`, `Policy`
- Inspect: `docs/operating_system/planning/planning-dispatch.md:Executor Selection`, `CoS boundaries`
- Modify: `docs/operating_system/runtime/runtime-surfaces.md:canonical launcher ownership`
- Modify: `docs/operating_system/planning/planning-dispatch.md:Herdr top-level Codex launch rule`
- Verify: `scripts/validate_repo_contracts.py`, `scripts/validate_planning_lifecycle.py`

**Dependencies:**
- Task 1 command contract is fixed.
- No generated adapter requires update because this task changes operating-system docs only.

**Authority:**
- Preauthorized local actions: edit the two declared canonical docs; run documentation and repository validators.
- Stop for: changes to generated adapters, profile schema, executor behavior, Herdr server behavior, or public documentation.

**Steps:**
- [ ] Step 1: Add launcher ownership to runtime surfaces: registry owns profile/model; launcher resolves; Herdr owns pane/session topology.
- [ ] Step 2: Add dispatch rule that CoS may choose Herdr only for independent top-level Codex main agents and may not route DeepAgents, Tura, native subagents, or internal workers through Herdr.
- [ ] Step 3: Document required preflight and live evidence fields without copying profile records.

**Verification:**
- [ ] `py -B scripts/validate_repo_contracts.py`
- Expected: repository contracts pass.
- [ ] `py -B scripts/validate_planning_lifecycle.py`
- Expected: planning lifecycle passes with no stale status or unchecked required evidence introduced.

**Exit Criteria:**
- Documentation names one source for each fact and one symmetric path for every supported profile/executor combination.

### Task 4: Run bounded live Herdr proof

**Purpose:**
- Prove the launcher starts a visible top-level Codex agent and that Herdr exposes identity, lifecycle, and output.

**Task Function:**
- Capture direct runtime boundary and terminal evidence.

**Template Profile:**
- Controller-selected: `none (lead controller)`
- Selection basis: runtime control and acceptance remain with native Codex controller.

**Validator Profile:**
- Controller-selected: `review`
- Selection basis: independent read-only observation; no rank relationship required.

**Specification Coverage:**
- Herdr owns main-agent topology.
- Executor selection resolves Codex.
- `agents/xhigh.toml` resolves to `combo-xhigh`.
- Live output is visible in the managed pane.
- No nested Herdr client, native subagent, DeepAgents worker, Tura worker, or executor-local helper is used.

**Required Skills:**
- `skill-backend-verification`, `skill-verification-before-completion`

**Files And Symbols:**
- Inspect: `agents/xhigh.toml:model`
- Inspect: `scripts/herdr_main_launcher.py:preflight output`
- Verify: `herdr --session codex-probe agent list`, `herdr --session codex-probe agent get xhigh-main`, `herdr --session codex-probe agent read xhigh-main --source recent-unwrapped --lines 30`
- Record: plan Coordination State Evidence column and final Verification section

**Dependencies:**
- Tasks 1–3 pass.
- Existing `codex-probe` session is running and contains a user-approved disposable pane; otherwise stop and request approval before creating one.

**Authority:**
- Preauthorized local actions: send one read-only marker prompt, wait, read output, and inspect Herdr state.
- Stop for: nested Herdr error; missing session/pane; unexpected model/provider; any write-capable prompt; need to create/delete/stop runtime resources.

**Steps:**
- [ ] Step 1: From external PowerShell, confirm `herdr --session codex-probe agent list` and select an available pane.
- [ ] Step 2: Run `py -B scripts/herdr_main_launcher.py --profile xhigh --session codex-probe --pane w1:p5 --name xhigh-main`; capture preflight JSON and Herdr start output.
- [ ] Step 3: Run `herdr --session codex-probe agent get xhigh-main` and confirm `agent=codex`, `agent_status=idle|working`, matching session, pane, and cwd.
- [ ] Step 4: Send marker `LIVE_SSO_HERDR_XHIGH_2026-08-29` with read-only instructions; wait for `LIVE_SSO_HERDR_XHIGH_ACK`; read recent unwrapped output.
- [ ] Step 5: Record exact commands, returned facts, exit codes, and output marker in plan evidence; do not mark completed from prose alone.

**Verification:**
- [ ] `herdr --session codex-probe agent list`
- Expected: named `xhigh-main` appears under `codex` with a live pane ID.
- [ ] `herdr --session codex-probe agent read xhigh-main --source recent-unwrapped --lines 30`
- Expected: output contains the exact acknowledgement marker.
- [ ] `git status --short`
- Expected: only declared tracked implementation/doc/test changes and pre-existing user files remain.

**Exit Criteria:**
- Direct Herdr evidence proves profile, model, executor, session, pane, lifecycle, and terminal output with no hidden fallback.

## Verification

- `py -m pytest tests/test_herdr_main_launcher.py -q`
- `py -B scripts/validate_repo_contracts.py`
- `py -B scripts/validate_planning_lifecycle.py`
- `py -B scripts/sync_agent_adapters.py --all-platforms --check`
- `git diff --check`
- `herdr --session codex-probe agent list`
- `herdr --session codex-probe agent read xhigh-main --source recent-unwrapped --lines 30`

Expected final state: focused tests pass; repository, planning, and adapter
checks pass; Herdr shows `xhigh-main` as a `codex` agent; terminal readback
contains `LIVE_SSO_HERDR_XHIGH_ACK`; no unapproved files, runtime resources,
provider settings, or Git disposition changes occur.

## Completion Criteria

The plan is ready for completion verification when:

1. `agents/*.toml` remains the only profile/model source.
2. One launcher handles ranked and explicit-only profiles with identical logic.
3. Herdr receives only resolved Codex launch facts and owns only top-level pane/session lifecycle.
4. Missing profile, missing Herdr, invalid registry, and runtime failure paths fail closed.
5. Focused tests prove registry binding, symmetry, no fallback, and error propagation.
6. Operating-system docs state the same ownership boundaries without copied profile data.
7. Fresh live Herdr evidence proves visible agent identity and output.
8. Plan ledger transitions and evidence contain exact commands and outputs; checked boxes alone do not establish completion.
9. No commit, push, merge, cleanup, or session deletion occurs without separate explicit authorization.
