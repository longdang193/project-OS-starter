---
layer: change
artifact_type: plan
status: completed
template_id: implementation-plan
contract_version: "1"
name: switchyard-auto-routing-sidecar-experiment
targets:
  - "$CODEX_HOME/auto.config.toml"
  - "$HOME/.switchyard/routes.toml"
  - "$HOME/.switchyard/run-probes.ps1"
  - "$HOME/.switchyard/evidence/"
---

# Switchyard Auto-Routing Sidecar Experiment Plan

## Goal

Add one reversible local Codex `auto` profile through pinned Switchyard v0.2.0,
then the existing LightRSI endpoint. Keep current fixed Codex path, tracked roles,
LightRSI, 9router, and provider configuration unchanged.

This plan proves transport conservation and routing-signal visibility. It
collects exploratory correctness, latency, usage, and prompt-cache evidence. It
does not make `auto` default or claim production readiness.

## Implementation Outcomes

### Fixed route remains control

`$CODEX_HOME/config.toml` remains provider `9router`, model `combo-high`,
Responses wire format, endpoint `http://127.0.0.1:17667/v1`. Tracked
`agents/{low,normal,high,xhigh}.toml` remain unchanged. Fixed Codex sessions do
not depend on Switchyard.

### Opt-in sidecar route

`$CODEX_HOME/auto.config.toml` points model `auto` to provider `switchyard` at
`http://127.0.0.1:4000/v1`. `$HOME/.switchyard/routes.toml` exposes:

- `switchyard/high-control`: passthrough to `combo-high`
- `auto`: Stage Router between `combo-low` and `combo-high`
- `capable_first`, threshold `0.5`, recent window `3`
- no classifier, escalation, handoff prompt, or direct 9router/provider target

Both targets call existing LightRSI Responses endpoint
`http://127.0.0.1:17667/v1`.

### Protocol and routing evidence

Direct `combo-high` and `switchyard/high-control` produce equivalent Codex
JSONL, `apply_patch`, file state, and continuation behavior. A multi-turn `auto`
probe proves Switchyard receives post-tool history and records selected target
plus decision source.

### Reproducible exploratory comparison

One user-local PowerShell runner executes six deterministic probe classes three
times through fixed-high and three times through `auto`. It writes redacted
JSONL and aggregate CSV beneath `$HOME/.switchyard/evidence/`. Cache or cost
claims remain unverified without provider usage evidence.

## Execution Approach

- Mode: `inline sequential`
- Coordination: `git-tracked`
- Executor: `codex`
- Required skills: `skill-code-standards`, `skill-backend-verification`, `skill-performance-optimization`, `skill-verification-before-completion`
- Isolation: current workspace for plan state; OS temporary Git repositories for write probes
- Commit policy: no commits during execution
- Preauthorized local actions: inspect nonsecret config, create declared local files and temporary repositories, validate config, start and stop exact Switchyard process, run declared probes, inspect redacted Switchyard, Codex, and `lightrsi codex session` reports
- User-approval actions: network installation, provider-billed calls, commit, push, merge, publication, destructive cleanup, discard
- Parallel ownership: none
- Sequential fallback: Task 1, Task 2, Task 3, Task 4

## Coordination State

- Coordination owner: `single lead controller`
- Coordination schema: `1`
- Branch: `main`
- Base commit: `f9520e4`
- Active task(s): none
- Expected workspace: this plan plus preserved unrelated untracked `db/`
- Next action: none
- Blockers: none
- Residual notes: historical full-config byte hash has no retained source copy; semantic reconciliation is authoritative; local 9router cost is an estimate, not provider invoice cost.

| Task | State | Workspace | Executor | Depends On | Required Proof | Evidence |
| --- | --- | --- | --- | --- | --- | --- |
| Task 1 | `completed` | current + user-local | `codex` | none | baseline and binary identity | `$HOME/.switchyard/evidence/baseline.json`; Switchyard 0.2.0; listeners 17667/20128 |
| Task 2 | `completed` | user-local | `codex` | Task 1 | config validation and health | dry-run passed; health OK; routes auto/high-control |
| Task 3 | `completed` | temporary repos | `codex` | Task 2 | protocol and signal gates | protocol evidence; auto signal and stage-router metrics pass |
| Task 4 | `completed` | temporary repos + evidence | `codex` | Task 3 | paired probe matrix | `$HOME/.switchyard/evidence/probes/matrix-20260825-rerun6/`; 36/36 correctness; exact stopwatch aggregation; isolated Codex home; zero primary probe trust entries |

## Execution Notes

- Task 3 passes: direct and sidecar-high protocol artifacts match; continuation and `apply_patch` pass; Stage Router metrics show non-fallback decisions and zero routing fallbacks.
- Task 4 captured 36 runs: six probe classes × three repetitions × fixed-high/auto; all markers and final-state assertions pass; auto target is `combo-high` through `stage_router`.
- Task 4 is `experiment-valid`: 36/36 runs pass correctness and markers; `auto` selects `combo-high` through `stage_router`; fixed-high remains control; zero routing fallbacks; exact stopwatch timings recorded.
- Runner now uses per-run temporary `CODEX_HOME` with copied auth, explicit provider definitions under ignored config, newline-tolerant text assertions, route-keyed aggregate grouping, 9router request-detail deltas, and config reconciliation evidence. Fixed semantic fields and tracked role hashes remain the acceptance surface; historical full-config byte drift is recorded rather than treated as a runtime mutation.
- An earlier unauthenticated Switchyard SSOT smoke on 2026-08-25 received provider HTTP 401 and appended no terminal routing row; exact process cleanup passed. It is superseded by authenticated smoke evidence below and remains only as failure-path evidence.
- Authenticated Switchyard SSOT contract smoke `switchyard-contract-auth-v3` passed after installing the release binary built from pinned source SHA `1fc9ab887d1c663b0048ae24d5f473d15ed8daaa`; one row contained `route=auto`, `decision_source=fall_open`, signed score `0.0`, threshold `0.5`, selected model `combo-high`, usage, and exact process cleanup.
- Bounded paired calibration `paired-calibration-20260825` passed: direct fixed-high and authenticated `auto` requests both returned HTTP `200`; 9router `usageHistory` reported physical model `gpt-5.6-luna(high)`, input/output tokens, cache fields, and cost for both paths. Auto routing evidence remained `route=auto`, `decision_source=fall_open`, selected target `combo-high`.
- Telemetry runner hardening changed user-local `run-probes.ps1` correlation from non-unique `timestamp` to primary-key `usageHistory.id`. The earlier `telemetry-low5` matrix remains non-acceptance evidence because its auto requests received invalid Switchyard API-key responses; rerun only after starting Switchyard with the current transient auth binding.
- Root-cause verification found two verifier defects: durable 9router rows were read before asynchronous persistence completed, and ordered PowerShell hashtables were grouped by nonexistent properties. The runner now performs bounded condition-based usage polling and groups status with a scriptblock; newline-tolerant assertions cover both affected sibling probes.
- Fresh telemetry-backed matrix `verification-20260826-telemetry2` passed: `36/36` runs, `36/36` correct, zero exits or markers failures, `18/18` auto rows through `stage_router`, zero routing fallbacks, and `reported:18` 9router usage rows for each route. Cost remains a local estimate; provider invoice savings remain unclaimed.
## Task Breakdown

### Task 1: Capture baseline and install Switchyard

**Purpose:**
- Establish immutable fixed-route control and install one pinned sidecar binary.

**Task Function:**
- Baseline local runtime and install experimental dependency.

**Template Profile:**
- Controller-selected: `none (lead controller)`
- Selection basis: exact local inspection and one pinned installation.

**Validator Profile (optional):**
- Controller-selected: `none`
- Selection basis: direct command receipts suffice.

**Specification Coverage:**
- Fixed profiles bypass Switchyard.
- Switchyard version is pinned.
- No existing runtime config changes.

**Required Skills:**
- `skill-backend-verification`

**Files And Symbols:**
- Inspect: `$CODEX_HOME/config.toml:model_provider,model,model_reasoning_effort,model_providers.9router`
- Inspect: `agents/{low,normal,high,xhigh}.toml:model`
- Inspect: installed `codex`, `cargo`, `rustc`, `lightrsi`, `9router`
- Modify: Cargo user binary directory through pinned install
- Verify: `$HOME/.cargo/bin/switchyard-server.exe`

**Dependencies:**
- Planning baseline: `codex-cli 0.148.0`, LightRSI endpoint port `17667`, 9router port `20128`.

**Authority:**
- Preauthorized local actions: read nonsecret fields, hash configs, inspect versions/listeners.
- Stop for: changed Codex provider contract, missing model aliases, unavailable listeners, credentials in output, or required existing-runtime edit.

**Steps:**
- [ ] Record Git state, Codex/Cargo versions, fixed endpoint, model aliases, and SHA-256 hashes of existing Codex and tracked role configs.
- [ ] Require existing LightRSI and 9router owners to provide active unchanged listeners; record process IDs for ports `17667` and `20128` without starting or modifying either runtime under this plan.
- [ ] Obtain approval, then run `cargo install --locked switchyard-server --version 0.2.0`.
- [ ] Record Switchyard version, executable path, and SHA-256.

**Verification:**
- [ ] `codex --version` — expected `codex-cli 0.148.0`; version drift blocks until profile and Responses semantics are revalidated.
- [ ] `Get-NetTCPConnection -State Listen | Where-Object LocalPort -In 17667,20128` — expected both listeners.
- [ ] `switchyard-server --version` — expected `0.2.0`.
- [ ] `git status --short` — expected plan plus preserved `db/` only.

**Exit Criteria:**
- Fixed baseline, listener ownership, pinned binary identity, and unchanged tracked roles are recorded without secrets.

### Task 2: Configure opt-in auto profile

**Purpose:**
- Create exact local Switchyard and Codex config without touching fixed paths.

**Task Function:**
- Configure one Responses-compatible Stage Router sidecar.

**Template Profile:**
- Controller-selected: `none (lead controller)`
- Selection basis: two small reversible TOML files.

**Validator Profile (optional):**
- Controller-selected: `none`
- Selection basis: strict parsing, dry-run, health, and hash comparison prove task.

**Specification Coverage:**
- `auto` remains explicit opt-in.
- Sidecar upstream is LightRSI, not 9router.
- Fixed config and tracked roles remain unchanged.

**Required Skills:**
- `skill-code-standards`
- `skill-backend-verification`

**Files And Symbols:**
- Create: `$HOME/.switchyard/routes.toml:llm_clients.lightrsi,targets,routes`
- Create: `$CODEX_HOME/auto.config.toml:model,model_provider,model_providers.switchyard`
- Create: `$HOME/.switchyard/evidence/`
- Verify: `$CODEX_HOME/config.toml`
- Verify: `agents/*.toml`

**Dependencies:**
- Task 1 complete; Switchyard installed; LightRSI listening on `17667`.

**Authority:**
- Preauthorized local actions: create declared local files, validate, launch one hidden process on `127.0.0.1:4000`.
- Stop for: pre-existing target files, occupied port `4000`, new auth requirement, or required base Codex/LightRSI/9router edit.

**Steps:**
- [ ] Create `routes.toml` with schema `1`, one `openai_responses` LightRSI client, targets `combo-low` and `combo-high`, passthrough ID `switchyard/high-control`, and Stage Router ID `auto` using `capable_first`, `0.5`, and window `3`.
- [ ] Create `auto.config.toml` with provider `switchyard`, model `auto`, Responses wire API, and base URL `http://127.0.0.1:4000/v1`; inherit base reasoning, sandbox, approvals, MCP, and features.
- [ ] Validate Switchyard config and Codex strict profile parsing.
- [ ] Start Switchyard with `Start-Process -WindowStyle Hidden`, routing JSONL, redirected stdout/stderr, host `127.0.0.1`, port `4000`; record PID.
- [ ] Verify health and model list; recheck fixed config and role hashes.

**Verification:**
- [ ] `switchyard-server --config "$HOME/.switchyard/routes.toml" --dry-run` — expected exit `0`.
- [ ] `codex -p auto --strict-config --help` — expected exit `0`.
- [ ] `Invoke-RestMethod http://127.0.0.1:4000/health` — expected healthy response.
- [ ] `Invoke-RestMethod http://127.0.0.1:4000/v1/models` — expected `auto` and `switchyard/high-control`.
- [ ] `git status --short` — expected no new repository runtime change.

**Exit Criteria:**
- Sidecar and profile validate, declared routes appear, fixed hashes remain unchanged.

### Task 3: Prove protocol conservation and signal visibility

**Purpose:**
- Stop before benchmarking when sidecar changes Codex semantics or lacks usable trajectory input.

**Task Function:**
- Execute transport, tool, continuation, and routing-observability probes.

**Template Profile:**
- Controller-selected: `high`
- Selection basis: Responses streaming, custom tools, continuation, and attribution carry material risk.

**Validator Profile (optional):**
- Controller-selected: `high`
- Selection basis: independently compare direct and sidecar artifacts and routing logs.

**Specification Coverage:**
- Gate 0: usable post-tool history reaches Stage Router.
- Gate A: passthrough-high preserves Codex behavior.

**Required Skills:**
- `skill-backend-verification`

**Files And Symbols:**
- Create: `$TEMP/switchyard-protocol-direct/value.txt`
- Create: `$TEMP/switchyard-protocol-sidecar/value.txt`
- Create: `$HOME/.switchyard/evidence/protocol-direct.jsonl`
- Create: `$HOME/.switchyard/evidence/protocol-sidecar.jsonl`
- Create: `$HOME/.switchyard/evidence/auto-signal.jsonl`
- Inspect: `$HOME/.switchyard/evidence/routing.jsonl`

**Dependencies:**
- Task 2 complete; both control paths resolve alias `combo-high` through same LightRSI endpoint.

**Authority:**
- Preauthorized local actions: create exact temporary repos, run bounded sessions, retain evidence, stop exact Switchyard PID.
- Stop for: malformed JSONL, missing `apply_patch`, wrong final state, continuation failure, missing target attribution, every Stage Router request falling open, cross-tier fallback, or tracked repository mutation.

**Steps:**
- [ ] Create two identical temporary Git repos with committed `value.txt` containing `BEFORE`.
- [ ] Run direct `combo-high` with prompt `Use apply_patch to replace exact content BEFORE with AFTER in value.txt, read the file, then return exactly PROTOCOL_PATCH_OK.` Capture JSONL.
- [ ] Run identical prompt through profile `auto` with model override `switchyard/high-control`.
- [ ] Require both exits `0`, parseable JSONL, `apply_patch` event, exact marker, byte-identical one-line diff, and identical final file hash.
- [ ] Extract each session UUID from its Codex JSONL, then run `codex exec resume $directThreadId "Return exactly PROTOCOL_CONTINUATION_OK" --json` and `codex exec resume $sidecarThreadId "Return exactly PROTOCOL_CONTINUATION_OK" --json -p auto -m switchyard/high-control`.
- [ ] Run multi-turn `auto` probe that reads `README.md`, then `agents/high.toml`, then reports the tracked high alias. Capture selected target and decision source for each request.
- [ ] Require capable first turn plus at least one later history-informed decision that is not `fall_open`.

**Verification:**
- [ ] Parse all Codex outputs with PowerShell `ConvertFrom-Json` — expected every nonblank line valid.
- [ ] Compare temporary repo diffs and file hashes — expected identical results.
- [ ] Inspect routing JSONL — expected passthrough always `combo-high`; auto includes request ID, target, and decision source.
- [ ] `git status --short` — expected plan plus preserved `db/` only.

**Exit Criteria:**
- Direct and sidecar-high behavior matches; continuation and `apply_patch` work; Stage Router sees usable history. Failure blocks Task 4 and removes `auto` from active use.

### Task 4: Run paired exploratory matrix

**Purpose:**
- Produce reproducible evidence for correctness, routing distribution, latency, usage, and cache reads.

**Task Function:**
- Build and execute one minimal local benchmark runner.

**Template Profile:**
- Controller-selected: `high`
- Selection basis: paired workload control, telemetry joining, and correctness comparison require material judgment.

**Validator Profile (optional):**
- Controller-selected: `high`
- Selection basis: independently verify parity, calculations, redaction, and claims.

**Specification Coverage:**
- Compare fixed-high and `auto` under identical conditions.
- Correctness remains primary invariant.
- Provider cache claims require provider evidence.
- `auto` remains opt-in.

**Required Skills:**
- `skill-backend-verification`
- `skill-performance-optimization`

**Files And Symbols:**
- Create: `$HOME/.switchyard/run-probes.ps1`
- Create: `$HOME/.switchyard/evidence/probes/$runId/summary.csv`
- Create: `$HOME/.switchyard/evidence/probes/$runId/decision.md`
- Inspect: Switchyard routing JSONL and Codex JSONL usage events
- Inspect: `lightrsi codex session $threadId report`
- Verify: temporary fixture Git state and exact assertions

**Dependencies:**
- Task 3 passes; user approves provider-billed calls.

**Authority:**
- Preauthorized local actions: create runner, execute declared matrix, retain redacted evidence, stop exact Switchyard PID.
- Stop for: workload mismatch, secret/raw-content leakage, missing route attribution, correctness divergence, cross-tier fallback, or tracked repository mutation.

**Steps:**
- [x] Create one native PowerShell runner with mandatory `-RunId` and optional `-DryRun`. It creates isolated fixtures, runs `codex exec --json`, captures elapsed time and exit code, parses JSONL, hashes final files, checks markers, joins routing records, and writes CSV. Add no dependency.
- [x] Implement six deterministic multi-turn probes: repository search, one-file patch, three-file rename, failing-test diagnosis, read-only review, repeated known edit. Each has exact final-state assertion or marker.
- [x] Run each probe three times through direct `combo-high`, then three times through profile `auto`, using identical fixture bytes, prompts, sandbox, approvals, and ordering: `36` runs total.
- [x] Record route, correctness, elapsed milliseconds, target sequence, switch count, decision sources, retries, failures, and Codex token usage. For every captured Codex thread ID, run `lightrsi codex session $threadId report` and record cached input tokens plus any reported served-model/provider fields; absent fields are recorded as `unverified`.
- [x] Write aggregate counts, median, and p95. Label cost/cache conclusions `unverified` when provider usage evidence is absent.
- [x] Write result `experiment-valid`, `experiment-failed`, or `experiment-inconclusive`. `experiment-valid` means protocol, correctness, attribution, and redaction pass; it does not mean cheaper or production-ready.
- [x] Keep `auto` opt-in, leave base config unchanged, and stop Switchyard after capture.

**Verification:**
- [x] Run `$HOME/.switchyard/run-probes.ps1 -RunId self-check -DryRun` — `36` planned records, zero Codex/provider calls, and no fixture mutation.
- [x] Run `$HOME/.switchyard/run-probes.ps1` with explicit run ID — `36` complete records in `matrix-20260825-rerun6`.
- [x] Validate six classes × three repetitions × two routes and identical pair fixture/prompt hashes.
- [x] Inspect decision, routing log, and one raw record per class — no secrets, attributable targets, proven correctness.
- [x] Run `lightrsi codex session $threadId report` for one fixed-high and one `auto` thread from every probe class.
- [x] Compare final semantic config and role hashes with Task 1 — semantic fields and roles unchanged; full config hash drift remains recorded.
- [x] Rerun matrix after telemetry patch and require `config-reconciliation.json` plus 9router request-detail status for every run — `verification-20260826-telemetry2`; aggregate status corrected to `reported:18` per route.
- [x] Fresh profile activation gate: clean `codex exec --profile auto` reached Switchyard, changed the fixture, returned the marker, and appended `route=auto` rows with `decision_source=dimensions`; verifier waits for durable JSONL flush before reading evidence.
- [x] `git status --short` — plan plus preserved `db/` only.

**Exit Criteria:**
- Paired evidence is reproducible and redacted, all correctness assertions pass, targets are attributable, fixed config remains unchanged, and claims stay within measured evidence.

## Verification

- `switchyard-server --version`
- `switchyard-server --config "$HOME/.switchyard/routes.toml" --dry-run`
- `codex -p auto --strict-config --help`
- `Invoke-RestMethod http://127.0.0.1:4000/health`
- Parse protocol and probe JSONL with PowerShell `ConvertFrom-Json`
- Validate pair counts, fixture hashes, prompt hashes, correctness, and route attribution
- Inspect `$HOME/.switchyard/evidence/probes/$runId/config-reconciliation.json`; compare semantic fixed fields and `agents/*.toml` hashes, while retaining full config hash as informational
- Query `http://127.0.0.1:20128/api/usage/request-details?page=1&pageSize=100` during controlled runs
- `git diff --check`
- `py scripts/validate_template_required_sections.py`
- Controller review of redacted protocol, routing, correctness, latency, usage, cache, and served-model evidence

## Completion Criteria

The plan is ready for completion verification when:

1. Switchyard v0.2.0 is pinned by version and SHA-256
2. fixed Codex semantic contract, tracked roles, LightRSI, and 9router configuration remain unchanged; full config byte identity is informational because historical baseline content is unavailable
3. `$CODEX_HOME/auto.config.toml` is the only Codex surface enabling Switchyard
4. Switchyard targets only existing LightRSI Responses endpoint
5. passthrough-high matches direct-high for JSONL, `apply_patch`, final state, and continuation
6. Stage Router records usable post-tool history rather than falling open every request
7. all `36` paired runs have deterministic correctness and attributable targets
8. 9router request-detail usage is captured per run; its calculated cost is labeled local estimate, and provider invoice savings remain unclaimed without provider billing evidence
9. `auto` remains opt-in and no default or tracked role changes
10. final checks pass and unrelated `db/` remains untouched

Only `skill-verification-before-completion` may mark this plan `completed` after
fresh proof and reconciliation of task ledger, Git state, and gate failures.

