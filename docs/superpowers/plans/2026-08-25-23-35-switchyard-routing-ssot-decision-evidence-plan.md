---
layer: change
artifact_type: plan
status: completed
template_id: implementation-plan
name: switchyard-routing-ssot-decision-evidence
targets:
  - repo_config/switchyard-routing.toml
  - scripts/manage_switchyard_runtime.py
  - tests/test_manage_switchyard_runtime.py
  - docs/operating_system/procedures/runtime-adapter-procedure.md
  - docs/superpowers/plans/2026-08-25-17-08-switchyard-auto-routing-sidecar-experiment-plan.md
  - external:NVIDIA-NeMo/Switchyard@1fc9ab887d1c663b0048ae24d5f473d15ed8daaa
---

# Switchyard Routing SSOT And Decision Evidence Implementation Plan

## Goal

Create one maintainable routing-policy source for Switchyard's dynamic `auto`
route and extend Switchyard's existing append-only routing JSONL with the minimum
facts needed to explain one decision.

Initial automatic routing uses `normal ↔ high`. `low` remains fixed/manual until
measurements justify a separate economy policy. Switchyard owns trajectory
interpretation, scoring, thresholds, overrides, and target selection.
`project-OS-starter` only owns policy composition, runtime rendering, drift
checks, and one contract smoke. No routing algorithm copy, analytics subsystem,
registry, database, or production 9router join.

## Implementation Outcomes

### Canonical routing policy without profile duplication

`agents/low.toml`, `agents/normal.toml`, and `agents/high.toml` remain canonical
owners of provider aliases and model IDs. `repo_config/switchyard-routing.toml`
references `normal` and `high` by profile name and owns only automatic routing
parameters plus `policy_version = 1`. It never repeats provider/model facts.

One stdlib-only manager resolves profiles, reads the user-local Codex provider
binding, validates the combined contract, and renders:

- `$HOME/.switchyard/routes.toml`
- `$CODEX_HOME/auto.config.toml`

Both files are generated outputs with safe drift detection and atomic deployment.

### One minimal Switchyard decision record

Extend existing `RoutingRecord` JSONL. Do not add a response header, second event
stream, registry, database, route digest, or request-ID propagation layer.

Keep existing fields authoritative:

- `model`: Switchyard-selected target/alias
- `tier`: existing semantic tier
- `task`, `trial_id`, `session_id`
- existing token/cache fields
- existing `fallback_reason`

Add only these optional fields:

- `route`: `auto` for automatic routing records
- `decision_source`: `dimensions`, `override`, `tests_passed`, `llm-classifier`, or `fall_open`
- `decision_score`: signed score; positive favors capable, negative favors efficient
- `decision_threshold`: active confidence threshold when scoring participated

Fixed `switchyard/high-control` passthrough records intentionally omit `route`
and decision evidence because no routing decision occurs; selected `model`
remains authoritative for that control path.

`confidence` is derived as `abs(decision_score)` during analysis. Override reason
remains the existing coarse `decision_source = "override"`; detailed reason is
out of v1 scope.

9router remains owner of physical served model, tokens, cache, and cost. Existing
verification remains owner of PASS/FAIL/BLOCKED. Neither is copied into the
Switchyard routing record.

### One smoke, no tracking subsystem

The manager reads one new Switchyard routing row for smoke verification. It does
not query 9router SQLite, join cost data, attach outcomes, or create durable
evidence storage. Optional 9router physical-model/cost observation can happen
manually during later calibration and is not a v1 blocker.

The full 36-case matrix and quality/cost calibration remain separately gated.

## Execution Approach

- Mode: `inline sequential`
- Coordination: `git-tracked`
- Executor: `codex`
- Required skills: `skill-central-config-layer`, `skill-code-standards`, `skill-test-driven-development`, `skill-backend-verification`, `skill-verification-before-completion`
- Isolation: current project workspace plus isolated Switchyard checkout; user-local runtime writes only during Task 3
- Commit policy: no commits in this project; isolated upstream commit or publication is optional and separate from local proof
- Preauthorized local actions: inspect named sources and nonsecret runtime configuration; prepare/test isolated upstream patch; edit declared project files; create temporary fixtures; run focused tests, dry-run checks, and one provider-billed smoke
- User-approval actions: publish upstream patch, replace existing non-generated runtime files, run calibration matrix, commit/push/merge/publication, destructive recovery, discard, or unrelated cleanup
- Parallel ownership: none; tasks execute sequentially
- Sequential order: Task 1, Task 2, Task 3

## Coordination State

- Coordination owner: `single lead controller`
- Branch: `main`
- Base commit: `6e9b65ab0fb9167f0c8d79280e8467f5ff74720c`
- Active task(s): none
- Expected workspace: preserve existing edits to `scripts/validate_template_required_sections.py` and `tests/test_validate_template_required_sections.py`, untracked `db/`, existing Switchyard experiment plan, and this proposed plan
- Next action: none
- Blockers: none

| Task | State | Workspace | Executor | Depends On | Required Proof | Evidence |
| --- | --- | --- | --- | --- | --- | --- |
| Task 1 | `completed` | isolated Switchyard checkout | `codex` | none | minimal routing-log tests | Rust format and focused tests passed |
| Task 2 | `completed` | current project | `codex` | Task 1 local patch | manifest/parser/render tests | manager tests passed; generated runtime drift check passed; Codex `env_key` covered |
| Task 3 | `completed` | current + user-local runtime | `codex` | Task 1, Task 2 | one contract smoke | authenticated smoke `switchyard-contract-auth-v4` PASS; route evidence and exact cleanup verified |

## Task Breakdown

### Task 1: Add Minimal Switchyard Routing Evidence

**Purpose:**
- Persist only missing decision facts in existing `RoutingRecord` JSONL.

**Task Function:**
- Transport the final Stage Router source, signed score, and threshold to the existing terminal append path without changing routing behavior.

**Template Profile:**
- Controller-selected: `high`
- Selection basis: upstream routing-observability change with compatibility risk

**Validator Profile (optional):**
- Controller-selected: `xhigh`
- Selection basis: verify branch coverage, signed-score semantics, old JSONL compatibility, and no behavior change

**Specification Coverage:**
- Switchyard remains sole owner of routing logic.
- Existing `RoutingRecord` remains the only durable decision record.
- Existing `model`, `tier`, usage, task, trial, session, and fallback fields remain unchanged.
- No raw prompts, tool results, credentials, or provider secrets enter records.

**Required Skills:**
- `skill-code-standards`
- `skill-test-driven-development`
- `skill-backend-verification`

**Files And Symbols:**
- Upstream base: `NVIDIA-NeMo/Switchyard` tag `v0.2.0`, commit `1fc9ab887d1c663b0048ae24d5f473d15ed8daaa`
- Inspect first: `crates/libsy/src/algorithms/util/stage.rs:PickOutcome,DecisionSource,StageClassifier::score`
- Inspect first: `crates/libsy/src/algorithms/stage.rs:SourceStamp,build_route`
- Inspect first: `crates/libsy/src/algorithms/fall_through.rs:FallThroughDecision,FallThrough::route`
- Modify minimum required: `crates/switchyard-server/src/routing_log.rs:RoutingLogContext,RoutingLog::append,RoutingRecord`
- Modify minimum required: `crates/switchyard-server/src/usage_metrics.rs:observe`
- Modify minimum required: `crates/switchyard-server/src/lib.rs:SharedRoutingLog::append,stats_observer`
- Verify: existing routing-log tests and Stage Router/FallThrough tests

**Dependencies:**
- Pinned upstream source is fetched into an isolated checkout.
- Existing record reader defaults missing fields, preserving old JSONL.
- Existing `model` and `tier` fields are retained as the selected Switchyard target and semantic tier.

**Authority:**
- Preauthorized local actions: prepare local patch, run upstream tests, and build/test local binary
- Stop for: selected-target behavior change; raw sensitive data; new database/registry/header; generic FallThrough changes not proven necessary; upstream publication or commit

**Steps:**
- [x] First trace whether current final decision context can reach `RoutingLogContext` without changing generic FallThrough semantics.
- [x] Add `route`, `decision_source`, `decision_score`, and `decision_threshold` as optional JSONL fields with serde defaults.
- [x] Populate `decision_source` from existing Stage Router categories: `dimensions`, `override`, `tests_passed`, `llm-classifier`, and `fall_open`.
- [x] Preserve signed score only when available. Do not add confidence; analysis derives `abs(decision_score)`.
- [x] Preserve threshold only when scoring participated; use null for hard overrides and no-signal paths.
- [x] Keep existing `model` and `tier` as selected target and semantic tier. Do not add `selected_target`, `selected_tier`, `request_id`, or `route_config_digest`.
- [x] Attach fields to final routed usage rows in aggregate and streaming paths. Keep classifier/judge rows unchanged.
- [x] If a generic transport field is unavoidable, add one optional field with default `None`; do not alter classifier ordering, target selection, or fallback semantics.
- [x] Add tests for positive/negative dimension scores, override, tests-passed, LLM classifier, fall-open, aggregate response, stream response, old JSONL, and sensitive-field rejection.
- [x] Run formatter and focused upstream tests. Local binary is installed at Switchyard 0.2.0; upstream publication remains optional follow-up.

**Verification:**
- [x] `cargo fmt --all -- --check`
- [x] `cargo test -p switchyard-protocol -p switchyard-libsy -p switchyard-server`
- Expected: existing routing behavior is unchanged; old records parse; one new routed row contains the four optional fields.

**Exit Criteria:**
- Local isolated Switchyard patch emits minimal decision evidence through existing JSONL without requiring upstream publication.

### Task 2: Add Normal-High Routing SSOT And Runtime Generator

**Purpose:**
- Generate safe automatic routing configuration while keeping profile and provider ownership centralized.

**Task Function:**
- Define strict manifest/profile resolution and render/check/deploy behavior.

**Template Profile:**
- Controller-selected: `normal`
- Selection basis: bounded configuration and filesystem integration with overwrite safety

**Validator Profile (optional):**
- Controller-selected: `high`
- Selection basis: verify profile ownership, normal/high symmetry, deterministic rendering, idempotency, and secret absence

**Specification Coverage:**
- `agents/low.toml`, `agents/normal.toml`, and `agents/high.toml` remain model/provider owners.
- Initial auto route is `normal ↔ high`.
- `low` remains fixed/manual and is not an auto endpoint in v1.
- Runtime files are generated, not manual sources.

**Required Skills:**
- `skill-central-config-layer`
- `skill-code-standards`
- `skill-test-driven-development`

**Files And Symbols:**
- Create: `repo_config/switchyard-routing.toml`
- Create/modify: `scripts/manage_switchyard_runtime.py:RoutingPolicy,AgentProfile,load_routing_policy,load_agent_profiles,resolve_routing_contract`
- Create/modify: `tests/test_manage_switchyard_runtime.py`
- Modify: `docs/operating_system/procedures/runtime-adapter-procedure.md`
- Inspect: `agents/low.toml`, `agents/normal.toml`, `agents/high.toml`, `scripts/sync_agent_adapters.py:_load_agent_roles`

**Dependencies:**
- Task 1 local Switchyard patch passes tests and supplies the supported JSONL fields.
- `agents/normal.toml` resolves `combo-normal`; `agents/high.toml` resolves `combo-high` through the same provider alias.
- Python standard library `tomllib`, `dataclasses`, `hashlib`, and `pathlib` are available.

**Authority:**
- Preauthorized local actions: add manifest, parser, renderer, and focused tests
- Stop for: low profile becoming an auto endpoint; duplicated model IDs; credentials in generated text; provider ownership moving into manifest

**Steps:**
- [x] Create `repo_config/switchyard-routing.toml` with `policy_version = 1`, Switchyard minimum version, routing-log field contract, `efficient_profile = "normal"`, `capable_profile = "high"`, route IDs, picker, threshold, and recent window.
- [x] Resolve profiles strictly and reject missing profiles, identical tiers, provider mismatch, unsupported picker, invalid threshold/window, empty route names, and model duplication in manifest.
- [x] Render `$HOME/.switchyard/routes.toml` and `$CODEX_HOME/auto.config.toml` with generated headers, including only the upstream credential environment-variable name; do not render credentials, evidence, 9router SQL, or analytics configuration.
- [x] Implement deterministic render, read-only check, atomic deploy, idempotent second deploy, and explicit `--replace-existing` migration for existing files.
- [x] Add tests for normal/high resolution, low exclusion, deterministic bytes, secret absence, drift, replacement refusal, and unrelated-file preservation.

**Verification:**
- [x] `py -m pytest tests/test_manage_switchyard_runtime.py -q` — 8 passed.
- Expected: generated files select normal/high endpoints and contain no credential values or duplicated model facts.

**Exit Criteria:**
- One manifest drives safe normal/high runtime generation and leaves low fixed/manual.

### Task 3: Migrate Runtime And Run One Routing Contract Smoke

**Purpose:**
- Prove one real automatic request produces one valid Switchyard routing row without making cost attribution a production requirement.

**Task Function:**
- Execute local migration, read one routing row, and verify exact process cleanup.

**Template Profile:**
- Controller-selected: `high`
- Selection basis: provider-billed request, process ownership, runtime migration, and cleanup safety

**Validator Profile (optional):**
- Controller-selected: `xhigh`
- Selection basis: fresh review of routing evidence, failure paths, process cleanup, and workspace preservation

**Specification Coverage:**
- Runtime files derive from canonical normal/high policy.
- One request proves Switchyard route, source, score/threshold when applicable, selected model/tier, usage, and cleanup.
- 9router physical-model/cost observation is optional and non-blocking.
- Quality/cost calibration and 36-case matrix remain deferred.

**Required Skills:**
- `skill-backend-verification`
- `skill-verification-before-completion`

**Files And Symbols:**
- Modify: `scripts/manage_switchyard_runtime.py:run_smoke,read_switchyard_row`
- Modify: `tests/test_manage_switchyard_runtime.py`
- Modify: `docs/superpowers/plans/2026-08-25-17-08-switchyard-auto-routing-sidecar-experiment-plan.md:Coordination State`
- Verify: `$HOME/.switchyard/routes.toml`
- Verify: `$CODEX_HOME/auto.config.toml`
- Verify: one temporary redacted routing-row summary

**Dependencies:**
- Tasks 1-2 complete.
- Explicit approval for any replacement of existing non-generated runtime files via `--replace-existing`.
- Task 1 local binary is installed and writes the supported routing row.

**Authority:**
- Preauthorized local actions: manager check, dry-run, one provider-billed smoke, read-only routing-log read, temporary summary, and exact process cleanup
- Stop for: replacement mismatch, listener ownership conflict, missing routing row, invalid score semantics, provider failure, secret leakage, extra process descendants, or request count above one

**Steps:**
- [x] Run manager `check`; inspect drift before migration.
- [x] Run manager `deploy --replace-existing`; rerun `check` and confirm zero drift.
- [x] Run Switchyard version and generated-config dry-run; normal/high route IDs and supported routing-log fields pass.
- [x] Snapshot routing-log byte offset, start one Switchyard process, send exactly one direct Responses request to route `auto`, write one redacted temporary summary, and stop the exact process in `finally`.
- [x] Require `route = auto`, populated `decision_source`, valid signed `decision_score` and `decision_threshold` when applicable, existing `model`/`tier`, token usage, no secrets, and zero retained smoke process. Authenticated smoke `switchyard-contract-auth-v4` passed with `request_count=1`, HTTP 200, `route=auto`, `decision_source=fall_open`, model `combo-high`, token usage, and exact process cleanup. Fixed passthrough source inspection confirms its route and decision fields remain absent by design.
- [x] Treat 9router physical-model/cost inspection as optional observation only; it did not gate this smoke.
- [x] Update earlier experiment plan with smoke evidence; keep calibration and 36-case matrix separately gated.

**Verification:**
- [x] `py scripts/manage_switchyard_runtime.py check --codex-config "$HOME/.codex/config.toml" --codex-home "$HOME/.codex" --switchyard-home "$HOME/.switchyard"`
- [x] `switchyard-server --config "$HOME/.switchyard/routes.toml" --dry-run`
- [x] `py scripts/manage_switchyard_runtime.py smoke --run-id switchyard-contract-auth-v4 --codex-config "$HOME/.codex/config.toml" --codex-home "$HOME/.codex" --switchyard-home "$HOME/.switchyard"` — `PASS`, HTTP 200, request count 1, valid routing row, exact process cleanup true.
- Expected: one valid final routing row; passed. Earlier unauthenticated run remains recorded as provider HTTP 401.

**Exit Criteria:**
- One real automatic decision is explainable from existing Switchyard JSONL with no project tracking or 9router integration layer.

## Verification

- `cargo fmt --all -- --check` in pinned Switchyard checkout
- `cargo test -p switchyard-protocol -p switchyard-libsy -p switchyard-server` in pinned Switchyard checkout
- `py -m pytest tests/test_manage_switchyard_runtime.py -q`
- `py scripts/manage_switchyard_runtime.py check --codex-config "$HOME/.codex/config.toml" --codex-home "$HOME/.codex" --switchyard-home "$HOME/.switchyard"`
- `switchyard-server --version`
- `switchyard-server --config "$HOME/.switchyard/routes.toml" --dry-run`
- Inspect temporary summary for route, source, score/threshold when applicable, existing model/tier, token usage, and no secrets.
- `py scripts/validate_template_required_sections.py`
- `git diff --check`
- `git status --short`

## Completion Criteria

The plan is ready for completion verification when:

1. `repo_config/switchyard-routing.toml` is the only tracked owner of automatic routing policy and `policy_version`
2. `agents/low.toml`, `agents/normal.toml`, and `agents/high.toml` remain the only tracked owners of provider aliases and models
3. auto uses normal/high; low remains fixed/manual
4. runtime files are generated deterministically from canonical policy, profiles, and local provider binding
5. existing non-generated runtime files are replaced only after drift inspection and explicit `--replace-existing` approval
6. existing Switchyard `RoutingRecord` remains the only durable routing-decision record
7. Switchyard adds only route, decision source, signed score, and threshold fields, with optional backward-compatible serialization
8. existing model/tier/token/cache/task/trial/session/fallback fields remain authoritative
9. no Switchyard classifier, score calculation, threshold rule, or route inference is copied into project code
10. no project 9router SQL/cost/outcome integration layer exists
11. existing verification remains owner of PASS/FAIL/BLOCKED
12. raw prompts, raw tool results, credentials, API keys, cookies, and connection secrets are absent from records and temporary artifacts
13. one real routing contract smoke passes and exact process cleanup is proven
14. quality/cost calibration and the 36-case matrix remain unrun and separately gated
15. existing unrelated workspace changes and untracked `db/` remain preserved
16. final commands pass and earlier Switchyard experiment plan records current smoke evidence and deferred work

The plan may be marked `completed` only when `skill-verification-before-completion`:

1. runs fresh final verification
2. confirms completion criteria against repository and user-local evidence
3. finds no unresolved required task, failed required check, stale coordination state, secret exposure, or unrecorded scope deviation
4. returns `verified` and updates plan status

A checked box records progress; it is not proof by itself.

