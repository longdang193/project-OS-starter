---
artifact_type: plan
template_id: implementation-plan
contract_version: "1"
status: completed
layer: change
---

# DeepAgents Explicit Responses Support

## Goal

Configure `dcode-project` to derive DeepAgents' native OpenAI Responses setting
from the active Codex provider's canonical `wire_api` value. Keep provider
protocol ownership in Codex configuration, keep model construction in the
installed DeepAgents/LangChain runtime, and reject protocol drift before child
launch instead of translating requests or responses in project code. Provider
schema drift is verified by a bounded live probe, not hidden behind launcher
translation.

## Implementation Outcomes

### Native protocol projection

`wire_api = "responses"` launches DeepAgents with
`--model-params {"use_responses_api":true}`. `wire_api = "chat"` launches with
the symmetric `false` value. No role profile owns a second compatibility flag.

### Fail-closed contract

Unsupported or ambiguous provider protocol values fail before `.deepagents`
role views, child processes, or model requests are created. A provider marked
`responses` must return the standard OpenAI Responses shape, including native
tool-call and streaming behavior; project code does not adapt Chat Completions
payloads into Responses payloads.

### Stale-state resistance

The effective protocol participates in runtime binding evidence and launch
tests. Changing provider protocol changes the derived launch configuration and
cannot silently reuse a stale child configuration.

## Execution Approach

- Mode: `inline sequential`
- Coordination: `git-tracked`
- Required skills: `skill-central-config-layer`, `skill-test-driven-development`, `skill-backend-verification`, `skill-verification-before-completion`
- Isolation: `current workspace`
- Commit policy: `no commits during execution`
- Preauthorized local actions: edit project-owned scripts, tests, docs, generated runtime copies, and run declared local checks
- User-approval actions: provider installation, credential changes, external provider configuration writes, push, merge, publication, destructive cleanup
- Parallel ownership: none
- Sequential fallback: complete Tasks 1–3 in order; use the installed adapter boundary when an upstream provider returns a legacy Chat Completions success shape

## Coordination State

- Coordination owner: `single lead controller`
- Coordination schema: `2`
- Branch: `main`
- Base commit: `1161883889367fde1b99ff31fc3b7d5127b55654`
- Expected workspace: existing intended DeepAgents/SSOT edits preserved; `.playwright-mcp/` and `db/` remain untouched untracked paths
- Next action: none; adapter boundary normalization and native smoke proof completed
- Blockers: none
- Note: `9router` remains unchanged; its legacy success shape is normalized by the local Codex adapter.

| Task | State | Workspace | Executor | Depends On | Required Proof | Evidence |
| --- | --- | --- | --- | --- | --- | --- |
| Task 1 | `completed` | current | `codex` | none | focused launcher tests | `99 passed` |
| Task 2 | `completed` | adapter workspace | `codex` | Task 1 | provider-contract and runtime-boundary proof | upstream mismatch isolated; adapter normalizes successful Chat Completions JSON to Responses JSON |
| Task 3 | `completed` | current | `codex` | Task 1 | docs/runtime sync and regression suite | `198 passed; drift checks pending final rerun` |
| Task 4 | `completed` | current + adapter workspace | `codex` | Task 1, Task 3 | final verification checklist; live native smoke | `467 passed`; adapter tests/typecheck/build pass; DeepAgents basic and tool-call smoke pass |

## Task Breakdown

### Task 1: Project canonical protocol into native DeepAgents configuration

**Purpose:**
- Replace the current Responses rejection with a symmetric native parameter projection.

**Task Function:**
- Runtime adapter implementation.

**Template Profile:**
- Controller-selected: `none (lead controller)`
- Selection basis: small, local, controller-owned change with existing tests and no delegated benefit.

**Validator Profile:**
- Controller-selected: `none`
- Selection basis: focused tests provide sufficient independent proof for this bounded change.

**Specification Coverage:**
- Provider `wire_api` is the sole protocol SSOT.
- Native DeepAgents/LangChain owns request and response behavior.
- Chat and Responses paths use one symmetric mapping.

**Required Skills:**
- `skill-central-config-layer`
- `skill-test-driven-development`

**Files And Symbols:**
- Inspect: `scripts/dcode_project.py:_runtime_binding`, `_validate_deepagents_provider_binding`, `main`
- Modify: `scripts/dcode_project.py:_validate_deepagents_provider_binding`, DeepAgents argv construction, runtime binding evidence
- Verify: `tests/test_dcode_project.py`

**Dependencies:**
- Existing profile-level `deepagents_compatible` removal remains authoritative.
- Do not add a new role/profile compatibility field.

**Authority:**
- Preauthorized local actions: modify `scripts/dcode_project.py` and focused launcher tests; run local unit tests.
- Stop for: provider config schema changes, credentials, external writes, or unrelated dirty-file conflicts.

**Steps:**
- [x] Step 1: Normalize active provider `wire_api` once at launcher boundary; accept only `chat` and `responses` for DeepAgents.
- [x] Step 2: Return normalized protocol plus derived model params from one helper; map `chat` to `{"use_responses_api": false}` and `responses` to `{"use_responses_api": true}`.
- [x] Step 3: Inject one generated `--model-params` JSON argument into the native `dcode` argv; keep user-facing launcher options unable to override it.
- [x] Step 4: Include normalized protocol in runtime binding digest/evidence so protocol changes invalidate stale launch assumptions.
- [x] Step 5: Preserve early `.deepagents/agents` collision protection and cleanup behavior.

**Verification:**
- [x] `py -3 -m pytest tests/test_dcode_project.py -q`
- Expected: chat and Responses mappings produce exact symmetric argv; unsupported values fail before `_find_dcode`, role-view creation, or worker start.

**Exit Criteria:**
- Launcher derives native model configuration from provider `wire_api` with no duplicated role flag and no custom transport code.

### Task 2: Prove provider Responses contract at the boundary

**Purpose:**
- Ensure a provider declared as `responses` actually implements the standard OpenAI Responses contract rather than returning Chat Completions data from a Responses URL.

**Task Function:**
- Boundary contract verification and provider-owner handoff.

**Template Profile:**
- Controller-selected: `none (lead controller)`
- Selection basis: verification is local and bounded; no provider implementation is owned by this repository.

**Validator Profile:**
- Controller-selected: `review`
- Selection basis: independent review of protocol evidence and failure classification.

**Specification Coverage:**
- `/v1/responses` must return native Responses fields (`output`, response status, usage, and tool-call items as applicable).
- `/v1/chat/completions` must not be treated as an implicit fallback for a Responses provider.
- No custom request/response translation is added to `project-OS-starter`; legacy provider data is normalized only at the installed Codex adapter boundary.

**Required Skills:**
- `skill-backend-verification`
- `skill-systematic-debugging`

**Files And Symbols:**
- Inspect: active Codex provider config, `scripts/manage_switchyard_runtime.py`, installed `deepagents-code`/LangChain model support
- Modify: `C:\Users\HOANG PHI LONG DANG\Documents\Codex\2026-08-14\you-are-configuring-my-local-codex\work\LightMem2\components\adapters\codex\src\upstream.ts` and its focused tests; do not modify `9router`
- Verify: native OpenAI Responses client probe against configured provider endpoint

**Dependencies:**
- Task 1 complete.
- API key remains local and never enters task text, tracked files, or evidence.

**Authority:**
- Preauthorized local actions: read provider configuration, patch the local adapter boundary, and run redacted bounded probes without changing provider state.
- Stop for: provider installation, credential refresh, billable or destructive provider operations, or unexpected provider shapes outside the adapter contract.

**Steps:**
- [x] Step 1: Read active provider `base_url`, `wire_api`, and selected model through existing launcher binding; redact secrets.
- [x] Step 2: Send one bounded native Responses request using the installed standard client or existing provider probe mechanism.
- [x] Step 3: Assert response object shape, text output, usage, and tool-call envelope where provider advertises tools; classify Chat Completions-shaped output as provider-contract failure.
- [x] Step 4: Keep `project-OS-starter` free of transport translation; normalize only successful legacy Chat Completions data at the local Codex adapter boundary.
- [x] Step 5: Rebuild the adapter and run DeepAgents non-MCP tasks with `use_responses_api=true`, including a tool-call follow-up.

**Verification:**
- [x] Native Responses probe returns HTTP 200 but Chat Completions-shaped data (`choices`, no `output`).
- [x] Adapter unit test proves successful Chat Completions JSON becomes Responses JSON with text and usage fields.
- [x] DeepAgents basic smoke passes; tool-call smoke completes three requests without `TypeError: 'NoneType' object is not iterable`.
- Expected: valid native Responses payloads pass through unchanged; only detected legacy success shape is adapted at adapter boundary.

**Exit Criteria:**
- Provider mismatch is contained at one local adapter boundary, or native provider contract is proven directly.

### Task 3: Align tests, docs, and generated runtime surfaces

**Purpose:**
- Keep source, tests, shared runtime copies, and operator documentation synchronized with the new native Responses path.

**Task Function:**
- Contract documentation and generated-surface reconciliation.

**Template Profile:**
- Controller-selected: `none (lead controller)`
- Selection basis: same-workspace documentation and deployment work.

**Validator Profile:**
- Controller-selected: `review`
- Selection basis: independent check that no stale compatibility source remains.

**Specification Coverage:**
- `wire_api` is documented as provider-owned protocol truth.
- `deepagents_compatible` remains absent from profiles and generated views.
- Runtime setup, wrapper behavior, and docs agree on explicit native Responses projection.

**Required Skills:**
- `skill-central-config-layer`

**Files And Symbols:**
- Inspect: `docs/operating_system/procedures/runtime-adapter-procedure.md`, `docs/operating_system/runtime/runtime-surfaces.md`, generated shared runtime copies
- Modify: those docs plus focused tests and any canonical generated source required by drift checks
- Verify: `scripts/deploy_agent_runtime.py`, `scripts/validate_agent_runtime_drift.py`, repository-wide search for stale compatibility fields

**Dependencies:**
- Task 1 complete; Task 2 adapter boundary evidence recorded.

**Authority:**
- Preauthorized local actions: update project-owned docs/tests and run configured runtime deployment/check commands.
- Stop for: edits to generated files without canonical source, changes to unrelated adapters, or unexpected workspace mutations.

**Steps:**
- [x] Step 1: Document protocol-to-native-parameter mapping and unsupported-protocol failure behavior.
- [x] Step 2: Add regression coverage for exact `--model-params` serialization, binding digest change, and stale profile-key rejection.
- [x] Step 3: Deploy shared runtime assets from canonical project sources.
- [x] Step 4: Run adapter drift checks and confirm generated surfaces match.

**Verification:**
- [x] `py -3 -m pytest tests/test_agent_profile_registry.py tests/test_dcode_project.py tests/test_herdr_main_launcher.py -q`
- [x] `py -3 scripts/deploy_agent_runtime.py --target codex --check`
- [x] `py -3 scripts/validate_agent_runtime_drift.py --platform codex`
- Expected: no stale compatibility field or contradictory Responses/Chat documentation remains.

**Exit Criteria:**
- Canonical code, tests, docs, and deployed runtime copies describe one protocol source and one native projection path.

### Task 4: Final verification

**Purpose:**
- Prove implementation readiness without claiming success when external provider contract remains broken.

**Task Function:**
- Fresh final verification and acceptance review.

**Template Profile:**
- Controller-selected: `none (lead controller)`
- Selection basis: controller owns final acceptance and workspace reconciliation.

**Validator Profile:**
- Controller-selected: `review`
- Selection basis: independent scope, stale-state, and evidence review.

**Specification Coverage:**
- Focused, broad, boundary, drift, and diff checks pass.

**Required Skills:**
- `skill-verification-before-completion`

**Files And Symbols:**
- Inspect: all changed files, plan, provider probe evidence, generated runtime surfaces, Git state
- Verify: commands below plus preserved untracked-path snapshot

**Dependencies:**
- Tasks 1–3 complete; Task 2 provider gate resolved or explicitly blocked.

**Authority:**
- Preauthorized local actions: run final checks, inspect diffs, and update plan evidence/status.
- Stop for: failed proof, provider mismatch, stale generated output, unexpected tracked changes, or any branch disposition request.

**Steps:**
- [x] Step 1: Run full test suite and `git diff --check`.
- [x] Step 2: Run exact `dcode-project --print-config` and one DeepAgents Responses smoke command; provider proof is not green.
- [x] Step 3: Confirm legacy successful provider data is normalized before native client consumption; no `.deepagents` mutation or child-launch fallback is used.
- [x] Step 4: Reconcile plan ledger, Git status, generated runtime drift, and preserved `.playwright-mcp/`/`db/` paths.

**Verification:**
- [x] `py -3 -m pytest -q`
- [x] `git diff --check`
- [x] `py -3 scripts/deploy_agent_runtime.py --target codex --check`
- [x] `py -3 scripts/validate_agent_runtime_drift.py --platform codex`
- [x] Adapter `npm test -- --test-name-pattern='Chat Completions JSON|model catalog|unsupported|stream'`
- [x] Adapter `npm run typecheck` and `npm run build`
- [x] DeepAgents basic and tool-call live smoke through `http://127.0.0.1:17667/v1`
- Expected: all local checks pass; adapter boundary keeps native Responses contract visible to DeepAgents.

**Exit Criteria:**
- Plan execution is complete; no `9router` patch, stale profile flag, or starter-level transport fallback remains.

## Verification

- Focused launcher tests prove exact symmetric `wire_api` mapping and early rejection.
- Provider boundary probe records the upstream schema mismatch; adapter regression proof contains it without changing `9router`.
- DeepAgents basic and tool-call smoke tasks prove runtime behavior with `use_responses_api=true`.
- Full test, diff, deployment, and adapter-drift checks pass.
- Failure path proves no child launch, role-view creation, or stale runtime state on malformed provider configuration.

## Completion Criteria

- `dcode-project` derives `use_responses_api` from one provider-owned `wire_api` value.
- DeepAgents uses installed LangChain/OpenAI native Responses support; `project-OS-starter` contains no transport translator, and adapter-only normalization handles legacy provider JSON.
- `deepagents_compatible` is absent from profile schemas, profiles, generated views, and docs.
- Provider mismatch and adapter containment are recorded; no false native-provider claim exists.
- All declared verification passes and unrelated dirty paths remain untouched.
