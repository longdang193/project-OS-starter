---
layer: change
artifact_type: plan
status: proposed
template_id: implementation-plan
name: tura-bounded-worker-codex-adapter
targets:
  - scripts/dcode_project.py
  - scripts/setup_deepagents_runtime.ps1
  - tests/test_dcode_project.py
  - docs/operating_system/templates/agents/root-AGENTS.template.md
  - docs/operating_system/procedures/personal-local-worktree-procedure.md
  - docs/operating_system/procedures/runtime-adapter-procedure.md
  - README.md
---

# Tura Bounded Worker And Codex Adapter Implementation Plan

## Goal

Define Tura as one reusable bounded-worker capability and implement its first explicit Native Codex adapter through `project-delegate`. Native Codex retains coordination, approval, MCP, Git, and final-acceptance ownership. Tura owns only one bounded invocation and its local agent loop. Keep Tura as the default worker after the controller explicitly chooses `project-delegate`, preserve native Codex subagents, preserve `dcode-project` as a backward-compatible DeepAgents entry point, and avoid duplicate role, provider, handoff, credential, result, or lifecycle configuration.

```text
Native Codex controller
  ├─ native subagent selected explicitly → Codex → LightRSI → 9router
  └─ project-delegate default
       └─ bounded Tura worker             → Tura → LightRSI → 9router

Legacy explicit path:
  dcode-project                          → DeepAgents → LightRSI → 9router
```

Default Tura selection applies only after the controller explicitly chooses the bounded-worker launcher. This plan does not intercept or silently replace native `spawn_agent` behavior. V1 is nonrecursive and adds no direct Codex-subagent-to-Tura, DeepAgents-to-Tura, or Tura-to-Tura invocation path.

## Approved Ownership And Invariants

| Concern | Sole owner |
|---|---|
| Controller task, thread, approval, sandbox, MCP, and final acceptance | Native Codex |
| Profile names, rank, model, description, and developer instructions | tracked `agents/{low,normal,high,xhigh}.toml` |
| MCP catalog and capability digest | active Codex `config.toml` |
| Validated external facts | `codex.mcp.handoff.v1` |
| Bounded-worker task rendering and process boundary | tracked `scripts/dcode_project.py` |
| External worker default | user-local `dcode-project/config.toml:[delegation].default_executor` |
| Tura binary and provider-config locations | user-local `dcode-project/config.toml:[paths]` |
| Tura provider routing | file selected by `TURA_PROVIDER_CONFIG` |
| Tura local agent loop, `command_run`, sessions, compaction, and stdout JSONL | Tura runtime |
| LightRSI forwarding and provider-token observation | LightRSI |
| Git workspace identity, change evidence, and integration | Git plus Native Codex controller |

Required invariants:

1. Tura is a bounded worker, not a workflow controller. Native Codex retains task decomposition, approval, MCP, Git review, verification, and final acceptance.
2. `default_executor = "tura"` affects only `project-delegate`; `dcode-project` remains explicitly DeepAgents-compatible.
3. `--executor tura|deepagents` is an explicit launcher override; there is no implicit fallback between runtimes.
4. Native Codex subagents remain available through native controller delegation and are never launched indirectly through Tura.
5. V1 adds no direct DeepAgents-to-Tura, Codex-subagent-to-Tura, or Tura-to-Tura path. Future callers must reuse this worker boundary rather than create new Tura prompt or provider stacks.
6. Both external runtimes select model and profile text from tracked `agents/*.toml` and consume the same validated `codex.mcp.handoff.v1` payload. DeepAgents receives profile developer instructions through its native role surface; current Tura CLI receives that text inside the bounded user task. V1 does not claim developer-role priority equivalence.
7. Tura receives no Codex MCP configuration, approval state, sandbox settings, thread state, durable plan state, or raw credentials in task text.
8. Tura receives provider credentials only through child-process environment assembled from existing user-local secret configuration and uses the configured provider file without a copied provider catalog.
9. The adapter treats Tura stdout JSONL as opaque runtime output and propagates child status. It does not define `DONE`, evidence, changed-file, test, or acceptance schemas.
10. Git diff, changed files, tests, concerns, evidence, and acceptance remain controller-derived facts rather than worker claims.
11. No runtime silently falls back on missing binary, invalid config, timeout, nonzero exit, malformed handoff, or provider failure. Return exit code `2` for launcher/config validation failure and the child exit code for runtime failure.
12. Every Tura worker receives a unique session id for fresh-context isolation. The adapter never reuses a session id or synthesizes an explicit cache key to chase cross-worker cache hits.
13. Cross-worker cache reuse is not assumed. Current Tura cache-key derivation includes provider route, provider identity, session directory, and session id, so fresh workers may occupy distinct provider cache cohorts even when their prompt prefixes match.
14. User-local runtime state, `.deepagents/`, Tura state, credentials, benchmark evidence, and generated wrappers remain untracked.
15. Adapter compatibility depends only on the public Tura CLI capabilities used by this plan: prompt input, `--quiet`, `--json`, `--sandbox`, `--session-id`, `--agent-id`, `-C`, `-m`, stdout/stderr, and exit status. No Tura internal Rust API, database, prompt file, or release-specific branch becomes an adapter dependency.
16. A compatible Tura release installed at the configured executable path requires no config, wrapper, profile, or adapter change. A moved executable requires only one setup rerun with the new path.
17. Correctness compatibility and efficiency admission are separate. A release may remain operational after capability checks while prior cache, latency, token, and billing claims become stale until rerun against that binary identity.
18. Default Tura worker execution is TL: `TURA_PROVIDER_CONFIG` routes Tura to LightRSI, and LightRSI forwards to 9router/provider. The adapter never rewrites that provider file, bypasses LightRSI, or introduces a direct-provider fallback.
19. Tura release compatibility for this installation requires both public CLI capability checks and one provider-backed TL smoke. Failure in Tura, LightRSI, 9router, routing, or provider accounting fails closed without switching to direct Tura or DeepAgents.

## Non-Goals

- No universal plugin ABI, plugin registry, executor framework, or host-specific Tura configuration set.
- No recursive worker tree, child-worker budget system, or Tura-to-Tura execution in V1.
- No direct Tura tool injected into Native Codex subagents or DeepAgents in V1.
- No new OS-level sandbox claim. The adapter must use Tura's native `--sandbox` to restrict `command_run` workdirs and writes to the controller-authorized Git root, while process permissions remain inherited and controller verification remains authoritative.
- No semantic-version allowlist, per-release adapter, copied Tura binary, internal Tura module import, or release-specific configuration branch.
- No duplicated `tura-direct` and `tura-light-rsi` runtime configuration. One Tura provider-config SSOT owns TL routing; direct Tura exists only as an explicitly controlled benchmark arm when required.
- No LightRSI or Tura production-source change unless live proof identifies a separate reproducible contract defect requiring approval.

## Baseline Evidence

Current source facts:

- `scripts/dcode_project.py` already owns role loading, Codex provider binding, MCP capability digestion, handoff validation, bounded task context, user-local secret loading, and DeepAgents execution.
- `scripts/setup_deepagents_runtime.ps1` already owns user-local `dcode-project/config.toml` and command wrappers.
- `agents/*.toml` already defines `low`, `normal`, `high`, and `xhigh` profiles.
- Tura `tura_exec` already accepts `--quiet`, `--json`, `--session-id`, `--agent-id`, `-C`, and `-m` and honors `TURA_PROVIDER_CONFIG` plus `OPENAI_API_KEY`.
- Persistent local Tura provider config already routes `openai/combo-high` through LightRSI at `http://127.0.0.1:17667/v1`.
- Evidence snapshot only: Tura `main` at `71299d6544f7dbe5d91f5b5221df31db2088fc34` passes CLI prompt text into `RunAgentRequest.prompt`, then constructs provider messages as runtime identity, Tura system prompts, workspace/environment developer context, and finally the user task (`crates/gateway/src/tura_exec/embedded.rs`, `crates/runtime/src/manas/runtime_turn.rs`, `crates/runtime/src/session_bootstrap/initial_messages.rs`). This commit informs current cache analysis but is not a production compatibility pin.
- Current Tura keeps `command_run` tool shape stable across ordinary and final turns, but its explicit prompt-cache key includes session directory and session id (`crates/runtime/src/manas/tool_catalog.rs`, `crates/runtime/src/provider_flow/request_options.rs`). Stable-prefix eligibility and actual cross-worker cache hits therefore require separate provider-wire proof.

A prior local benchmark artifact exists at `C:/tmp/tl-l-tl-default-20260825/summary.json`, but its filesystem timestamp is August 25, 2026, which is future-dated relative to this plan's August 24, 2026 execution baseline. Treat it as advisory only. Task 6 must produce fresh dated evidence before admitting performance or cost claims. Provider cost fields in the advisory artifact were `0.0`; dollar-cost claims remain inadmissible until a provider exposes non-placeholder billing values.

## Implementation Outcomes

### One Bounded Worker Contract

Keep worker task rendering, role application, validated facts, workspace root, timeout, child environment, process cleanup, and failure propagation in one tracked launcher source. Treat existing Tura CLI arguments, stdout JSONL, and exit status as the runtime protocol instead of inventing a second structured response.

### First Native Codex Adapter

Install one new `project-delegate` command. It reads one user-local worker setting, defaults to Tura, accepts one explicit runtime override, and reuses the existing launcher source rather than creating a second role, handoff, credential, config, or output stack.

### Backward-Compatible DeepAgents Path

Keep `dcode-project` behavior stable by making its wrapper inject `--executor deepagents`. Existing commands, role views, `--no-mcp`, capability restrictions, handoff validation, and cleanup behavior remain unchanged.

### Tura Worker With Controller Boundary

Add a Tura worker branch to the existing launcher. It uses the selected tracked role, validated handoff facts, fixed Git root, configured Tura binary, configured provider config, deterministic child environment, bounded timeout, and opaque Tura JSONL output. Native Codex remains responsible for MCP calls, approval, Git review, verification, and acceptance.

### Release-Tolerant CLI Boundary

Depend only on required public Tura CLI capabilities, one configured executable path, and one provider-config path. Do not parse Tura versions or mirror release metadata. Compatible in-place upgrades require no adapter action; evidence receipts bind performance claims to the tested binary version/hash without blocking ordinary compatible use.

### Mandatory TL Production Route

Keep `TURA_PROVIDER_CONFIG` as the sole Tura routing source and require the configured production path `Tura → LightRSI → 9router → provider`. Setup stores its path without copying or interpreting provider catalogs. Release admission uses one bounded TL smoke and provider-wire evidence; failure never falls back to direct provider routing.

### Default And Override Symmetry

Use one executor resolver:

```text
explicit --executor
  else [delegation].default_executor
  else configuration error
```

Accepted external values are exactly `tura` and `deepagents`. Native Codex is selected by not calling the external launcher; no fake `codex` child runtime is introduced. Additional callers and recursion remain deferred until the nonrecursive worker boundary passes admission proof.

### Verification And Admission Evidence

Prove config resolution, backward compatibility, failure behavior, handoff safety, low/normal profile mapping, Tura-through-LightRSI routing, provider request-shape stability, intra-worker and cross-worker cache behavior, workspace safety, and adapter overhead. Do not generalize cache or dollar savings beyond observed provider counters.

## Execution Approach

- Mode: `inline sequential`
- Coordination: `git-tracked`
- Executor: `codex`
- Required skills: `skill-code-standards`, `skill-backend-verification`, `skill-test-driven-development`, `skill-performance-optimization`, `skill-verification-before-completion`
- Isolation: `current clean workspace`; use a native worktree only if unrelated changes appear before execution
- Commit policy: `no commits during execution`
- Preauthorized local actions: edit named Starter files, run focused Python tests, run adapter setup against disposable config roots, launch bounded Tura/DeepAgents/Codex compatibility probes, run matched 10-repetition provider-backed proof, write redacted evidence under `C:/tmp`
- User-approval actions: push, merge, publication, external writes beyond provider test calls, destructive recovery, discard, cleanup, persistent credential replacement
- Parallel ownership: `none`; launcher, setup, tests, and canonical docs share one contract
- Sequential fallback: `Task 1 → Task 2 → Task 3 → Task 4 → Task 5 → Task 6`

## Coordination State

- Coordination owner: `single lead controller`
- Branch: `main`
- Base commit: `0e4e6b9b050b2046420c4ab2011ef47d7cafcd0b`
- Active task(s): `Task 6: live TL admission proof`
- Expected workspace: `in-scope Starter changes uncommitted; unrelated changes preserved`
- Next action: `resolve or explicitly approve separate Tura runtime routing fix, then rerun TL smoke`
- Blockers: `current Tura tura_exec drops CLI model override before runtime worker; TL returns unknown provider route: codex/gpt-5.6-sol`

| Task | State | Workspace | Executor | Depends On | Required Proof | Evidence |
|---|---|---|---|---|---|---|
| Task 1 | `completed` | current | `codex` | none | focused contract tests fail for missing behavior | `75` focused tests pass after implementation |
| Task 2 | `completed` | current | `codex` | Task 1 | focused launcher tests pass | resolver, Tura argv/env/task, timeout/status tests pass |
| Task 3 | `completed` | current | `codex` | Task 2 | setup and wrapper tests pass | PowerShell parse, wrapper/config static contract pass |
| Task 4 | `completed` | current | `codex` | Task 3 | full launcher regression suite passes | `75` focused tests pass |
| Task 5 | `completed` | current | `codex` | Task 4 | generated adapters and docs validation pass | sync check and repo-config validation pass |
| Task 6 | `blocked` | current | `codex` | Task 5 | live correctness, routing, safety, and performance gates pass | Tura reached LightRSI; provider route failed before usage |

## Task Breakdown

### Task 1: Lock Bounded Worker Contract With Failing Tests

**Purpose:**
- Define the smallest observable contract before changing launcher behavior.

**Task Function:**
- Contract-focused test design.

**Template Profile:**
- Controller-selected: `normal`
- Selection basis: bounded test additions around one mature Python launcher.

**Validator Profile:**
- Controller-selected: `high`
- Selection basis: independent review of security, compatibility, and default-selection cases.

**Specification Coverage:**
- Tura-default worker selection, explicit runtime override, controller-owned acceptance, opaque Tura output, nonrecursive V1, shared profiles and handoff, preserved DeepAgents path.

**Required Skills:**
- `skill-test-driven-development`
- `skill-backend-verification`

**Files And Symbols:**
- Inspect: `scripts/dcode_project.py:_config_path`
- Inspect: `scripts/dcode_project.py:_load_roles`
- Inspect: `scripts/dcode_project.py:_controller_options`
- Inspect: `scripts/dcode_project.py:_validate_handoff`
- Inspect: `scripts/dcode_project.py:_handoff_stdin`
- Inspect: `scripts/dcode_project.py:main`
- Modify: `tests/test_dcode_project.py`
- Verify: `tests/test_dcode_project.py`

**Dependencies:**
- Current clean Starter `main` at recorded base.
- Existing tests remain authoritative for DeepAgents behavior.

**Authority:**
- Preauthorized local actions: add focused unit tests and test helpers in existing test file.
- Stop for: any requirement to change `codex.mcp.handoff.v1`, profile file schema, or native Codex API.

**Steps:**
- [ ] Add config fixtures with `[delegation].default_executor = "tura"`, `paths.tura_executable`, and `paths.tura_provider_config`.
- [ ] Add failing tests for resolver order: explicit override, configured default, missing default, and invalid executor.
- [ ] Add failing tests proving `dcode-project` wrapper semantics select DeepAgents independently of configured Tura default, reject caller executor overrides, and preserve legacy setup when no Tura paths are supplied.
- [ ] Add failing Tura command-construction tests covering role model, repository root, `balanced` agent, mandatory native `--sandbox`, unique session id, quiet JSONL mode, and timeout.
- [ ] Add failing compatibility tests proving launcher behavior does not branch on Tura semantic version or commit and setup accepts arbitrary release/version text when all required CLI capabilities are present.
- [ ] Add failing environment tests proving only configured secret value, `TURA_PROVIDER_CONFIG`, project root, and encoding variables enter required child keys; task text and printed config never contain credential values.
- [ ] Add failing handoff test proving the existing validated canonical payload is reused unchanged in meaning for both executor paths.
- [ ] Add failing tests proving one deterministic worker task contains role instructions, bounded context, caller task, and validated facts exactly once without durable plan state or caller history.
- [ ] Add failing tests proving profile developer instructions are labeled as bounded task guidance rather than represented as Tura system/developer messages, because current Tura CLI exposes only prompt input.
- [ ] Add failing tests proving separate worker launches receive different session ids and the adapter does not pass or synthesize `prompt_cache_key`.
- [ ] Add failing tests proving launcher propagates opaque stdout/stderr and child status without interpreting worker claims about files, tests, evidence, concerns, or acceptance.
- [ ] Add failure tests for missing binary, missing provider config, timeout, nonzero child exit, and invalid role. Keep Tura JSONL opaque to launcher; benchmark and controller verifiers own result parsing.

**Verification:**
- [ ] `py -3 -m pytest tests/test_dcode_project.py -q`
- Expected: only new contract tests fail because executor/Tura behavior is not implemented; all pre-existing tests remain green.

**Exit Criteria:**
- Required behavior and failures are represented by focused tests without changing production code.

### Task 2: Add Runtime Resolver And Tura Worker Branch

**Purpose:**
- Extend one launcher source with one explicit runtime seam and one nonrecursive bounded Tura worker path.

**Task Function:**
- Backend launcher implementation.

**Template Profile:**
- Controller-selected: `high`
- Selection basis: security-sensitive process launch, credential flow, timeout, backward compatibility, and cross-runtime semantics.

**Validator Profile:**
- Controller-selected: `xhigh`
- Selection basis: highest-risk independent validation of launcher boundary and failure handling.

**Specification Coverage:**
- One worker-boundary source, Tura default, explicit DeepAgents override, controller-owned acceptance, opaque runtime output, no recursion, no native interception, no fallback, shared roles/handoff/config.

**Required Skills:**
- `skill-code-standards`
- `skill-backend-verification`
- `skill-test-driven-development`

**Files And Symbols:**
- Modify: `scripts/dcode_project.py:_ALLOWED_RUNTIME_VALUE_OPTIONS`
- Modify: `scripts/dcode_project.py:_controller_options`
- Modify: `scripts/dcode_project.py:_runtime_binding`
- Modify: `scripts/dcode_project.py:_handoff_stdin`
- Modify: `scripts/dcode_project.py:main`
- Add only if needed inside same file: `_default_executor`, `_tura_worker_paths`, `_tura_worker_environment`, `_tura_worker_argv`, `_run_tura_worker`
- Verify: `tests/test_dcode_project.py`

**Dependencies:**
- Task 1 contract tests exist and fail for intended reasons.

**Authority:**
- Preauthorized local actions: modify one launcher file and satisfy Task 1 tests.
- Stop for: adding a plugin ABI, executor registry, semantic-version allowlist, per-release branch, internal Tura import, second config file, role registry, handoff schema, response schema, provider catalog, credential store, background daemon, retry/fallback framework, recursive worker support, or native Codex interception.

**Steps:**
- [ ] Parse `--executor tura|deepagents` once and reject duplicates or unknown values.
- [ ] Resolve executor through explicit override then `[delegation].default_executor`; require configured value and default setup to `tura`.
- [ ] Preserve the existing `--print-config` payload and add `default_executor`, `selected_executor`, Tura executable path, provider-config path, and path digests without secret values.
- [ ] Keep role loading and provider-name validation shared for both paths; use selected role model as `openai/<model>` for Tura.
- [ ] Keep MCP capability and handoff validation in the controller before either child starts.
- [ ] Construct one deterministic bounded-worker task from explicitly labeled profile guidance, bounded task context, caller task, and canonical validated handoff payload. Do not claim Tura system/developer-message priority; do not include caller history, durable plan state, acceptance claims, or paths to secret or handoff files.
- [ ] Launch configured Tura executable with `--quiet --json --sandbox --session-id <unique> --agent-id balanced -C <git-root> -m openai/<role-model> <task>`.
- [ ] Generate a fresh session id per worker invocation. Do not reuse sessions or pass an adapter-owned cache key; Tura and provider retain cache-key ownership.
- [ ] Do not run version parsing, release lookup, source inspection, or capability discovery on each task launch. Setup owns capability validation; task launch owns only executable/config existence checks and bounded execution.
- [ ] Set child-only `OPENAI_API_KEY`, `TURA_PROVIDER_CONFIG`, `TURA_PROJECT_ROOT`, and UTF-8 variables. Do not mutate user or process-global environment.
- [ ] Stream Tura stdout/stderr unchanged without adding or interpreting a second result schema, enforce configured/caller timeout, terminate the child tree on timeout, and return deterministic exit status.
- [ ] Keep V1 nonrecursive: do not expose a child-worker option, plugin registry, or Tura self-invocation contract.
- [ ] Keep current DeepAgents command, fixed capabilities, `--no-mcp`, role-view lifecycle, and cleanup code unchanged behind the `deepagents` branch.
- [ ] Make no automatic fallback. Error must name selected executor and actionable missing/invalid dependency without exposing secrets.

**Verification:**
- [ ] `py -3 -m pytest tests/test_dcode_project.py -q`
- Expected: all launcher contract and legacy DeepAgents tests pass.
- [ ] Direct boundary test with fake child executables records argv, cwd, environment-key names, stdin presence, exit code, and timeout behavior.
- Expected: Tura and DeepAgents branches receive only their declared inputs; Tura receives mandatory native sandboxing and unique session identity; both preserve Git root.

**Exit Criteria:**
- One launcher implements the first bounded Tura worker adapter with Tura selected by default and preserves the explicit DeepAgents compatibility branch.

### Task 3: Install Default Dispatcher And Preserve Legacy Wrapper

**Purpose:**
- Expose Tura-default delegation with no new runtime config store and no break to existing commands.

**Task Function:**
- User-local setup and wrapper integration.

**Template Profile:**
- Controller-selected: `normal`
- Selection basis: bounded PowerShell setup changes with compatibility risk.

**Validator Profile:**
- Controller-selected: `high`
- Selection basis: validate upgrade, reset, quoting, and wrapper behavior on Windows.

**Specification Coverage:**
- One user-local config, one default setting, explicit legacy path, minimal management after restart.

**Required Skills:**
- `skill-code-standards`
- `skill-backend-verification`

**Files And Symbols:**
- Modify: `scripts/setup_deepagents_runtime.ps1:param`
- Modify: `scripts/setup_deepagents_runtime.ps1:user-local config writer`
- Modify: `scripts/setup_deepagents_runtime.ps1:dcode-project wrapper`
- Add in same setup output: `%USERPROFILE%/.local/bin/project-delegate.{ps1,cmd}`
- Verify: `tests/test_dcode_project.py`

**Dependencies:**
- Task 2 launcher supports both executor paths.
- Existing local Tura executable and provider config are discoverable by explicit setup parameters; no guessed path.

**Authority:**
- Preauthorized local actions: update setup script and test disposable user-local roots.
- Stop for: writing credential values into config, setting global `OPENAI_BASE_URL`, changing Windows startup tasks, or auto-starting Tura.

**Steps:**
- [ ] Add optional paired `-TuraExecutable` and `-TuraProviderConfig` parameters. Reject one without the other; validate both as existing regular files when supplied.
- [ ] During Tura-enabled setup, run one bounded `--help` capability probe and require prompt input plus `--quiet`, `--json`, `--sandbox`, `--session-id`, `--agent-id`, `-C`, and `-m`. Do not require an exact Tura version or commit.
- [ ] Validate only that the configured Tura provider-config path is an existing regular file. Do not copy, rewrite, parse, or maintain its provider catalog in Starter setup.
- [ ] Keep legacy DeepAgents-only setup valid when neither Tura parameter is supplied. Do not install `project-delegate` or write delegation keys in that mode.
- [ ] When both Tura parameters are supplied, add or replace only setup-owned `[delegation]` and Tura path values in the existing user-local `config.toml`, preserve Codex and secret bindings, set `default_executor = "tura"`, and install `project-delegate`.
- [ ] Store the resolved executable path only; do not copy the Tura binary or persist release metadata. Compatible replacement at the same path requires no setup rerun.
- [ ] Keep `-ResetConfig` as explicit full regeneration. When an existing config lacks Tura keys and no Tura pair is supplied, preserve it and print the exact migration command shape.
- [ ] Install `project-delegate` wrapper that invokes tracked `scripts/dcode_project.py` without forcing an executor.
- [ ] Change `dcode-project` wrapper to inject `--executor deepagents` and reject a caller-supplied `--executor`, preserving legacy command identity without permitting silent rerouting.
- [ ] Keep `dcode-doctor` and isolated DeepAgents installation behavior unchanged.
- [ ] Print resolved command paths and default executor after successful setup; never print secret value or provider-config contents.

**Verification:**
- [ ] Run setup tests against disposable `$HOME` covering legacy install without Tura, new Tura-enabled install, normal migration, reset, one-sided Tura parameters, missing Tura binary, missing provider config, paths containing spaces, arbitrary compatible version text, missing required CLI capability, compatible in-place binary replacement, and legacy wrapper execution.
- Expected: one config file exists; Tura-enabled setup makes `project-delegate --print-config` select Tura; `dcode-project --print-config` selects DeepAgents in both modes; no credential appears in files or stdout.

**Exit Criteria:**
- User installs once, then uses `project-delegate --role <profile> ...`; restart requires no config ritual, and legacy `dcode-project` remains stable.

### Task 4: Complete Regression And Security Coverage

**Purpose:**
- Prove symmetry and failure behavior without a live provider.

**Task Function:**
- Backend regression and contract verification.

**Template Profile:**
- Controller-selected: `normal`
- Selection basis: focused deterministic test completion after implementation.

**Validator Profile:**
- Controller-selected: `high`
- Selection basis: independent review of negative paths and secret boundaries.

**Specification Coverage:**
- Shared SSOTs, bounded-worker ownership, opaque runtime output, nonrecursive V1, no fallback, role symmetry, handoff safety, process cleanup, native-controller boundary.

**Required Skills:**
- `skill-backend-verification`

**Files And Symbols:**
- Modify: `tests/test_dcode_project.py`
- Verify: `scripts/dcode_project.py`
- Verify: `scripts/setup_deepagents_runtime.ps1`

**Dependencies:**
- Tasks 2 and 3 complete.

**Authority:**
- Preauthorized local actions: add only tests needed for stated contract.
- Stop for: plugin ABI or registry, direct subagent/DeepAgents integration, recursive Tura, persistent service management, generalized executor framework, or automatic routing heuristics.

**Steps:**
- [ ] Verify every profile resolves from tracked `agents/*.toml` for both runtime branches without copied model maps.
- [ ] Verify role developer instructions enter the bounded Tura task exactly once.
- [ ] Verify validated handoff facts enter Tura task exactly once and raw handoff path never enters child text.
- [ ] Verify MCP selections affect handoff provenance validation only and no MCP server/tool config enters Tura environment or task.
- [ ] Verify every Tura launch includes native `--sandbox`, fixed Git root, and a fresh session id; verify no adapter-owned `prompt_cache_key` or shared session id exists.
- [ ] Verify profile developer instructions are rendered as clearly labeled task guidance and repository documentation does not claim Tura developer-role priority equivalence.
- [ ] Verify Tura timeout kills child tree and leaves no owned runtime process.
- [ ] Verify nonzero child status is propagated and does not invoke another executor.
- [ ] Verify Tura stdout JSONL remains opaque and no worker-emitted file, test, evidence, concern, or completion claim changes launcher exit or acceptance behavior.
- [ ] Verify no child-worker, recursive invocation, plugin registration, direct Codex-subagent, or direct DeepAgents-to-Tura surface is added.
- [ ] Verify `--executor deepagents` keeps role-view creation/removal and fixed capability flags.
- [ ] Verify `project-delegate` does not mutate tracked files for read-only tasks and the launcher does not perform Git integration.

**Verification:**
- [ ] `py -3 -m pytest tests/test_dcode_project.py -q`
- [ ] `py -3 -m pytest tests/test_native_personal_local_workflow.py -q`
- [ ] `py -3 scripts/validate_repo_config.py`
- Expected: all checks pass with zero tracked runtime artifacts.

**Exit Criteria:**
- Deterministic tests cover success, validation failure, runtime failure, timeout, cleanup, handoff, profile-priority honesty, native workspace sandboxing, fresh-session isolation, cache-key ownership, secrets, bounded-worker ownership, opaque output, nonrecursion, and DeepAgents compatibility.

### Task 5: Update Canonical Governance And Generated Surfaces

**Purpose:**
- Make default behavior recoverable from tracked SSOT without duplicating operational instructions.

**Task Function:**
- Canonical documentation and generated-adapter alignment.

**Template Profile:**
- Controller-selected: `normal`
- Selection basis: bounded documentation changes across canonical and generated surfaces.

**Validator Profile:**
- Controller-selected: `high`
- Selection basis: check ownership wording, generated boundaries, and no silent native replacement.

**Specification Coverage:**
- Tura bounded-worker definition, first Native Codex adapter, Tura default, Native Codex preservation, DeepAgents compatibility, deferred additional callers, restart behavior.

**Required Skills:**
- `skill-code-standards`

**Files And Symbols:**
- Modify canonical: `docs/operating_system/templates/agents/root-AGENTS.template.md:Native Personal-Local Work`
- Modify canonical: `docs/operating_system/procedures/personal-local-worktree-procedure.md:executor selection and evidence`
- Modify canonical: `docs/operating_system/procedures/runtime-adapter-procedure.md:local executor boundary`
- Modify: `README.md:local executor summary`
- Regenerate: root `AGENTS.md` and declared generated adapters through existing sync command
- Verify: generated surfaces named by sync validator

**Dependencies:**
- Task 4 proves actual behavior.

**Authority:**
- Preauthorized local actions: edit canonical docs, run repository sync and generated-tree validators.
- Stop for: public documentation that exposes private paths, credentials, internal MCP data, or local benchmark evidence.

**Steps:**
- [ ] State Tura is a bounded worker and `project-delegate` is its first explicit Native Codex adapter, defaulting to configured Tura.
- [ ] State native Codex subagents remain controller-selected and are not intercepted.
- [ ] State `dcode-project` is explicit DeepAgents compatibility command.
- [ ] Document profile/runtime independence, tracked `agents/*.toml` ownership, Tura task-guidance priority limitation, opaque Tura output, and controller-owned Git/tests/evidence/acceptance.
- [ ] Document V1 non-goals: no plugin registry, direct DeepAgents-to-Tura, direct Codex-subagent-to-Tura, Tura recursion, or new OS-level sandbox claim; document mandatory Tura-native `--sandbox` separately.
- [ ] Document no fallback, no MCP projection, no Tura login daemon, and no manual post-restart action beyond launching delegated work normally.
- [ ] Document setup/migration command using placeholders only.
- [ ] Document upgrade behavior: compatible replacement at configured path needs no configuration action; moved binary needs one setup rerun; one bounded `project-delegate` TL smoke re-admits the release path; prior performance evidence becomes stale when binary identity changes.
- [ ] Run canonical adapter sync instead of hand-editing generated files.

**Verification:**
- [ ] `py -3 scripts/sync_agent_adapters.py --check`
- [ ] `py -3 scripts/validate_repo_config.py`
- [ ] `py -3 -m pytest tests/test_native_personal_local_workflow.py -q`
- Expected: canonical and generated instructions agree; private values and machine-specific paths remain absent.

**Exit Criteria:**
- Repository truth explains one bounded Tura worker boundary, its first Native Codex adapter, one legacy DeepAgents launcher, deferred additional callers, and unchanged native Codex behavior.

### Task 6: Run Live Compatibility And Efficiency Admission

**Purpose:**
- Establish that the first bounded-worker adapter preserves direct Tura behavior without transferring controller ownership or damaging Native Codex and DeepAgents paths.

**Task Function:**
- Real-dependency compatibility, performance, and failure proof.

**Template Profile:**
- Controller-selected: `high`
- Selection basis: provider-backed multi-runtime evidence and admission judgment.

**Validator Profile:**
- Controller-selected: `xhigh`
- Selection basis: independent comparison of correctness, provider accounting, process cleanup, and claims.

**Specification Coverage:**
- Default bounded Tura operation, low/normal profiles, opaque runtime output, controller-derived acceptance, nonrecursive V1, preserved Native Codex capabilities, preserved DeepAgents override, evidence before additional caller integration.

**Required Skills:**
- `skill-backend-verification`
- `skill-performance-optimization`
- `skill-verification-before-completion`

**Files And Symbols:**
- Execute: `%USERPROFILE%/.local/bin/project-delegate.cmd`
- Execute: `%USERPROFILE%/.local/bin/dcode-project.cmd`
- Execute: configured Tura executable
- Inspect: configured Tura provider config path
- Inspect evidence: `C:/tmp/codex-tura-adapter-proof-20260824/`
- No production source modification authorized in this task.

**Dependencies:**
- Tasks 1–5 complete with fresh deterministic tests.
- 9router at `127.0.0.1:20128` and LightRSI at `127.0.0.1:17667` are healthy.
- Provider credentials are read from configured local secret source without printing.
- Installed Tura executable passes required public CLI capability checks. Record version/hash/commit when available; a difference from evidence snapshot `71299d6544f7dbe5d91f5b5221df31db2088fc34` invalidates prior efficiency claims and requires the bounded TL smoke before renewed compatibility claims, but requires no adapter/config change when the public CLI remains compatible.

**Authority:**
- Preauthorized local actions: run read-only bounded tasks, use disposable sessions/state, record redacted metrics, inspect process and Git state.
- Stop for: provider/model/route mismatch, tracked workspace mutation, missing usage counters, repeated runtime leak, changed prompt/tool workload, or any request to publish evidence.

**Steps:**
- [ ] Run `project-delegate --print-config` and prove selected/default executor `tura`, role models from tracked files, Tura path/config digests, provider name, MCP digest, and no secret values.
- [ ] Run `dcode-project --print-config` and prove selected executor `deepagents` with unchanged model/profile/MCP digests.
- [ ] Run one bounded release-admission smoke through `project-delegate` and prove provider-wire route `Tura → LightRSI:17667 → 9router:20128 → provider`, successful final marker, usage counters, native sandbox, and no direct-provider or DeepAgents fallback.
- [ ] Run one native Codex `low` and one native Codex `normal` read-only probe; confirm native tools, MCP authority, approvals, and controller behavior remain unchanged.
- [ ] Run three `project-delegate` read-only capability probes for `low` and three for `normal`; require exact requested operations, final marker, zero tracked mutation, and clean child cleanup.
- [ ] Run one explicit DeepAgents `low` and one `normal` probe through `dcode-project`; require existing fixed capabilities, `--no-mcp`, role mapping, and cleanup.
- [ ] Confirm neither native Codex probes nor DeepAgents probes receive a direct Tura tool, and confirm no Tura invocation creates a child-worker invocation.
- [ ] Capture the adapter-rendered task once through the deterministic fake-child boundary and reuse that exact task for the direct-Tura arm; do not maintain a second benchmark prompt template.
- [ ] Run ten randomized matched raw-Tura-CLI versus `project-delegate` trials with both arms using the same configured TL provider file and identical rendered task, profile, model, LightRSI/9router/provider route, workspace, command count, timeout, and restored fixture. This measures adapter overhead, not T-versus-TL routing.
- [ ] Through existing provider-wire instrumentation, record redacted ordered message-role/content digests, tool-schema digest, relevant option digests, and first differing message index for two fresh workers with different bounded tasks in the same restored workspace/profile/model/route/date/timezone/language/shell cohort. If exact request shape is unavailable, mark stable-prefix conclusion `INCONCLUSIVE` rather than inferring it from CLI arguments.
- [ ] Prove same-workspace fresh workers keep Tura identity/system and tool-schema digests stable; record workspace/environment developer-message digests separately; require controller task and handoff differences to begin at the user-task message or later.
- [ ] Record unique session ids and prompt-cache-key digests per worker. Treat different keys as expected under current Tura derivation; never reuse sessions to manufacture a hit.
- [ ] Report cache behavior in separate cohorts: intra-worker later turns sharing one session/key, and cross-worker fresh sessions using different session/key identities.
- [ ] Record per trial: correctness, exit/timeout, verified TL route, provider request count/status, input/cached/uncached/output tokens, cache-key presence/digest, model, route, latency, adapter process overhead, command count, final marker, Git status, sandbox state, fallback absence, and process cleanup.
- [ ] Record provider cost/billing fields when present. If all remain zero or absent, mark dollar-cost conclusion `INCONCLUSIVE`.
- [ ] Require `10/10` adapter strict pass, mandatory Tura-native sandbox evidence, zero runtime leaks, zero tracked mutation, same provider request count, no material input/uncached-token regression against direct Tura under the same fresh-session policy, and adapter p50 overhead no greater than `5%` or `1,000 ms`, whichever is larger.
- [ ] Compare against prior L/T/TL evidence only after confirming same provider/model/workload conditions. Do not claim general superiority outside bounded tool-heavy delegated tasks.

**Verification:**
- [ ] Redacted evidence directory contains config receipts, required-capability receipt, Tura version/hash/commit identity when available, request-shape digests, session/cache-key cohort receipts, per-trial JSONL, aggregate summary, environment identity, Git before/after, sandbox evidence, and process-cleanup receipts.
- [ ] `py -3 -m pytest tests/test_dcode_project.py tests/test_native_personal_local_workflow.py -q`
- [ ] `py -3 scripts/validate_repo_config.py`
- Expected: deterministic suite passes; live paths pass; bounded-worker adapter preserves direct-Tura request/token behavior within stated gate; controller-derived Git and verification evidence remains authoritative; native Codex and DeepAgents remain available and unchanged.

**Exit Criteria:**
- Tura-default worker delegation is admitted only for bounded nonrecursive work through `project-delegate` with complete controller-derived correctness, native workspace-sandbox evidence, and provider-token evidence. Cross-worker cache benefit remains unclaimed unless fresh-session request-shape and cached-token evidence prove it; additional callers, recursion, and billing savings remain unadmitted.

## Verification

### Execution Evidence

- `py -3 -m pytest tests/test_dcode_project.py tests/test_native_personal_local_workflow.py -q` -> `75 passed`.
- `py -3 -m pytest -q` -> `168 passed`.
- `py -3 scripts/validate_repo_config.py` -> passed.
- `py -3 scripts/sync_agent_adapters.py --check` -> passed.
- `py -3 -m py_compile scripts/dcode_project.py` -> passed.
- PowerShell parse of `scripts/setup_deepagents_runtime.ps1` -> passed.
- Real Tura CLI capability probe -> passed for prompt input, `--quiet`, `--json`, `--sandbox`, `--session-id`, `--agent-id`, `-C`, and `-m`.
- Real `project-delegate`-equivalent Tura launch reached `Tura -> LightRSI` but failed before provider usage with `unknown provider route: codex/gpt-5.6-sol`.
- Direct Tura launch reproduced the same failure, proving current blocker is Tura runtime/provider binding, not Starter adapter process construction.
- No TL correctness, billing, cache, or performance claim is admitted until this blocker is fixed and the required fresh 10-trial proof passes.

Final artifact-level verification:

```powershell
py -3 -m pytest tests/test_dcode_project.py tests/test_native_personal_local_workflow.py -q
py -3 scripts/sync_agent_adapters.py --check
py -3 scripts/validate_repo_config.py
project-delegate --print-config
project-delegate --role normal --json --max-turns 4 --timeout 120 -n "Perform the approved read-only adapter smoke task and return exactly TURA_ADAPTER_OK"
dcode-project --role normal --no-mcp --json --max-turns 4 --timeout 120 -n "Return exactly DEEPAGENTS_COMPAT_OK"
```

Expected final state:

- `project-delegate` is the first Native Codex adapter to one bounded Tura worker boundary and selects Tura by default.
- `dcode-project` selects DeepAgents explicitly.
- native Codex subagents remain unchanged and controller-owned.
- both runtime branches use tracked profiles and validated handoff facts.
- Tura output remains its existing opaque JSONL plus child exit status; no second acceptance protocol exists.
- Git diff, tests, evidence, concerns, and acceptance remain Native Codex controller responsibilities.
- no direct DeepAgents-to-Tura, Codex-subagent-to-Tura, or Tura-to-Tura path exists in V1.
- no Codex MCP, approval, sandbox-state, thread, or raw credential projection reaches Tura; the adapter supplies only fixed Tura-native `--sandbox`.
- no silent fallback occurs.
- compatible Tura replacement at the configured executable path requires no config, wrapper, or adapter update.
- one provider-config SSOT keeps default execution on TL; neither adapter nor release migration creates a direct-provider production route.
- each new Tura binary identity receives one bounded TL smoke before renewed compatibility claims; failed smoke has no fallback.
- Tura release identity scopes efficiency evidence only; no semantic-version branch controls ordinary compatible execution.
- no runtime artifact or secret becomes tracked.
- live evidence supports only claims allowed by real provider counters.

## Completion Criteria

The plan is ready for completion verification when:

1. Tura is documented and tested as a bounded worker while Native Codex retains coordination, MCP, Git, verification, and acceptance ownership
2. `project-delegate` exists as the first Native Codex adapter and selects Tura from one user-local default setting
3. `dcode-project` preserves existing DeepAgents behavior through explicit runtime selection
4. all four tracked profiles resolve symmetrically without copied model maps
5. both runtime branches reuse existing handoff validation and controller-owned MCP provenance
6. Tura child environment, deterministic task construction, mandatory native workspace sandbox, fresh-session isolation, opaque output, timeout, failure, and cleanup contracts pass deterministic tests
7. no plugin registry, second response schema, direct additional caller, recursive worker path, adapter-owned cache key, shared session, or new OS-level sandbox claim is introduced
8. setup validates required public Tura CLI capabilities without an exact-version allowlist, then produces one config and two wrappers without storing or printing credentials
9. compatible in-place Tura replacement requires no setup, config, wrapper, profile, or adapter change; a moved executable requires one setup rerun only
10. one bounded provider-backed smoke proves each new Tura binary identity still follows `Tura → LightRSI → 9router → provider` with usage counters and no direct-provider or DeepAgents fallback
11. no per-task release lookup, version parsing, source inspection, or capability probe is added
12. canonical docs and generated adapters agree with implemented and upgrade behavior
13. native Codex low/normal and DeepAgents low/normal compatibility probes pass unchanged
14. Tura low/normal worker probes pass with clean Git/process state and controller-derived correctness evidence
15. provider-wire evidence proves or explicitly marks `INCONCLUSIVE` the stable request-shape boundary across different tasks, with workspace/environment and tool digests recorded separately
16. intra-worker and cross-worker fresh-session cache cohorts are reported separately without reusing session ids to manufacture hits
17. ten matched raw-Tura-CLI/adapter TL trials pass correctness and overhead gates with provider token counters bound to recorded Tura binary identity
18. prior efficiency evidence becomes stale after Tura binary identity changes, but compatible operation remains allowed after the TL smoke
19. billing claims remain `INCONCLUSIVE` unless real nonzero cost counters are present
20. plan deviations, substitutions, blockers, and deferrals are recorded

The plan may be marked `completed` only when `skill-verification-before-completion` runs fresh final verification, reconciles plan plus Git, finds no unresolved required task or failed gate, and records verified evidence. Checked boxes alone are not proof.
