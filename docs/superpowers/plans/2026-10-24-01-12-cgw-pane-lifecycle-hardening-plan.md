---
artifact_type: plan
template_id: implementation-plan
contract_version: "1"
status: proposed
layer: change
name: cgw-pane-lifecycle-hardening
targets:
  - scripts/agent_profile_registry.py
  - scripts/herdr_main_launcher.py
  - repo_config/retired-model-policy.json
  - scripts/retired-model-policy.json
  - tests/test_agent_profile_registry.py
  - tests/test_herdr_main_launcher.py
  - tests/test_starter_kit_generation.py
  - tests/test_deploy_agent_runtime.py
  - docs/configuration.md
  - docs/superpowers/plans/2026-10-24-01-12-cgw-pane-lifecycle-hardening-plan.md
---

# CGW Retirement And Auto-Pane Lifecycle Hardening

## Goal

Complete the Project OS CGW retirement boundary and make `--session auto
--pane auto` resilient when existing panes cannot be reused. The launcher must
continue to fail closed for untrustworthy global runtime identity, but an
isolated candidate defect, incompatible context, or slow candidate inspection
must not prevent safe allocation of a new pane when a valid source pane exists.

## Review Basis

- Repository: `longdang193/project-OS-starter`
- Current base: `009b3417e1a5e7fc2df4d75bf403c349e50f875a`
- Primary reviewed revision: `47457e0972c37eeb30d27ca9734cf478bb3d0bbf`
- Primary source: `scripts/herdr_main_launcher.py`, `_resolve_target_selector`
  and `_herdr_pane`
- Confirmed review findings: candidate rejection is handled separately from
  discovery/global validation; only `TargetCandidateRejected` is isolated in
  the candidate loop; the retirement policy declares `retiredProviderIds` and
  `providerAliases` but profile admission validates only model strings.
- Source-confirmed operational risk: the five-second discovery deadline can be
  consumed by per-pane inspection before the replacement-pane branch runs.
- Policy ownership is an upstream dependency, not a local ownership decision:
  `9router/open-sse/config/retiredModels.js` is canonical and the two local JSON
  files are generated projections. The related closure plan is therefore an
  execution dependency for policy provenance when policy contents or export
  assumptions change:
  `docs/superpowers/plans/2026-10-23-22-10-cgw-retirement-consolidated-closure-plan.md`.

## Implementation Outcomes

### Canonical CGW retirement enforcement

Profile admission normalizes provider aliases and rejects retired provider
identities (`chatgpt-web` and `cg`) as well as retired model names and
prefixes, before executable lookup, Herdr discovery, or dispatch. The local
policy projections remain synchronized with the upstream canonical policy
export.

### Safe automatic pane allocation

Auto-discovery distinguishes global snapshot corruption from candidate-local
ineligibility. Incompatible contexts, malformed candidate metadata, candidate
transport failures, and candidate inspection timeouts are recorded as
rejections and do not prevent allocation from a valid source pane. Global
identity failures still return a structured blocked/incomplete result.

### Bounded lifecycle overhead

The selector preserves the existing five-second discovery contract, reserves
time for authorized replacement allocation, and records deterministic
rejection/allocation evidence. It does not add a scheduler, registry,
background supervisor, or second lifecycle state store.

### Durable regression proof and documentation

Tests cover provider aliases, candidate fault isolation, deadline exhaustion,
replacement allocation, and fail-closed global corruption. Configuration
documentation describes the resulting reuse/allocation contract and the
upstream-versus-local/shared-runtime policy ownership.

## Execution Approach

- Mode: `inline sequential`
- Coordination: `git-tracked`
- Required skills: `skill-backend-verification`, `skill-code-standards`, `skill-verification-before-completion`
- Isolation: `current workspace`
- Commit policy: `no commits during execution`
- Preauthorized local actions: inspect and edit the listed source, tests, policy projection, documentation, and run the declared local verification commands
- User-approval actions: push, merge, publication, destructive cleanup, or changes outside the listed targets
- Parallel ownership: none; registry, launcher, policy projection, and tests share the same retirement/lifecycle contract
- Sequential fallback: provider-policy contract first, launcher behavior second, generated/package proof third, final verification last

## Coordination State

- Coordination owner: `single lead controller`
- Coordination schema: `2`
- Branch: `codex/cgw-pane-lifecycle-hardening-plan-review`
- Base commit: `d863bcb133f715dc12678a1490ada227924cd069`
- Expected workspace: `preserve existing untracked .playwright-mcp/, .runtime/, and node_modules/ artifacts`
- Next action: implement Task 1 provider normalization and policy synchronization
- Blockers: upstream policy ownership/export provenance must be confirmed
  before changing policy contents; registry-only consumer hardening may proceed
  against the existing projection.

| Task | State | Workspace | Executor | Depends On | Required Proof | Evidence |
| --- | --- | --- | --- | --- | --- | --- |
| Task 1 | `pending` | current | `unresolved` | none | registry tests and policy projection equality | pending |
| Task 2 | `pending` | current | `unresolved` | Task 1 | focused auto-pane lifecycle tests | pending |
| Task 3 | `pending` | current | `unresolved` | Task 2 | documentation, starter-kit, and final verification | pending |

## Task Breakdown

### Task 1: Enforce retired provider identity and policy ownership

**Purpose:**
- Make CGW retirement apply to normalized provider identity, not only model spelling.

**Task Function:**
- Implement the canonical retirement validation contract and its packaged projection proof.

**Template Profile:**
- Controller-selected: `normal`
- Selection basis: registry behavior is bounded and source/test driven; resolve through planning dispatch before activation.

**Validator Profile:**
- Controller-selected: `review`
- Selection basis: independently verify provider alias rejection and no-side-effect ordering.

**Specification Coverage:**
- Retired `chatgpt-web` and `cg` provider identities fail closed before launch side effects.
- `9router/open-sse/config/retiredModels.js` remains the canonical policy
  source; `repo_config/retired-model-policy.json` is the local generated
  projection consumed by source checkout code, and
  `scripts/retired-model-policy.json` is its synchronized shared-runtime
  projection. This plan does not redefine upstream ownership.

**Required Skills:**
- `skill-code-standards`
- `skill-backend-verification`

**Files And Symbols:**
- Inspect: `scripts/agent_profile_registry.py:_load_retirement_policy`, `validate_model_reference`, `load_agent_profiles`
- Modify: `scripts/agent_profile_registry.py:validate_model_reference` and the policy-loading contract
- Modify: `tests/test_agent_profile_registry.py`
- Verify: `repo_config/retired-model-policy.json`, `scripts/retired-model-policy.json`, `repo_config/starter-kit-manifest.json`

**Dependencies:**
- Current policy fields and shared-runtime projection ownership are
  source-confirmed. Before changing policy contents or export assumptions,
  pin the upstream 9router policy revision/export contract; otherwise keep
  both local JSON files read-only and limit the change to consumer validation.

**Authority:**
- Preauthorized local actions: edit registry, synchronized projections only
  after the upstream export contract is pinned, and focused tests; run focused
  Python tests
- Stop for: an unavailable or unpinned cross-repository canonical policy
  source/export contract, a runtime-provider compatibility change, or a
  generated-surface change not represented in the manifest.

**Steps:**
- [ ] Step 1: Define one normalization path that maps `cg` to `chatgpt-web` and compares normalized provider identity against `retiredProviderIds`.
- [ ] Step 2: Keep model-name and model-prefix checks in the same retirement gate, with stable error wording that identifies the retired provider/model reference without exposing credentials.
- [ ] Step 3: Add tests for direct `chatgpt-web`, alias `cg`, and maintained provider `9router`; assert rejection occurs before executable lookup or Herdr calls.
- [ ] Step 4: Add a policy projection test that fails when the shared-runtime
  policy diverges from `repo_config/retired-model-policy.json`, and record the
  upstream policy revision/export contract used for the projection; do not
  make either local JSON file canonical.

**Verification:**
- [ ] `python -m pytest -q tests/test_agent_profile_registry.py tests/test_herdr_main_launcher.py -k "retired or provider or policy"`
- Expected: malformed or missing `retiredProviderIds` and `providerAliases`
  fail policy loading; a missing primary policy file exercises the packaged
  fallback; direct and aliased retired providers fail before side effects;
  maintained profiles remain loadable.

**Exit Criteria:**
- Provider aliases and retired provider IDs are enforced by one tested gate,
  and the local projections cannot silently drift from the pinned upstream
  policy export or each other.

### Task 2: Isolate candidate failures and preserve safe auto-pane allocation

**Purpose:**
- Ensure an incompatible or damaged existing pane does not fail closed when a safe replacement can be allocated.

**Task Function:**
- Refine target discovery error classification and deadline behavior without adding another lifecycle subsystem.

**Template Profile:**
- Controller-selected: `high`
- Selection basis: launcher behavior is high-impact but localized to target discovery and existing pane-lock helpers.

**Validator Profile:**
- Controller-selected: `review`
- Selection basis: validate both allocation and preserved fail-closed cases independently.

**Specification Coverage:**
- Only pane-scoped candidate inspection failures become rejection evidence:
  `LaunchBlocked`/`CommandTransportTimeout` from process-info or candidate
  metadata inspection may be isolated when the snapshot proves the candidate
  identity. Session-wide agent discovery, snapshot retrieval, and other global
  identity failures remain `TargetResolutionBlocked`.
- Malformed unrelated snapshot rows do not abort discovery; rows whose `cwd`
  cannot be read, or whose missing identity could belong to the current
  workspace, fail closed as structured global corruption.
- Discovery stops with an allocation reserve before the five-second deadline is consumed, then allocates from a validated source pane.

**Required Skills:**
- `skill-code-standards`
- `skill-backend-verification`

**Files And Symbols:**
- Inspect: `scripts/herdr_main_launcher.py:_herdr_pane`, `_resolve_target_selector`, `_pane_ownership_lock`
- Modify: `scripts/herdr_main_launcher.py:_resolve_target_selector` and a new
  `_inspect_auto_candidate` (or equivalent) boundary with explicit operation
  provenance
- Modify: `tests/test_herdr_main_launcher.py`
- Verify: target-resolution evidence fields and existing pane-lock behavior

**Dependencies:**
- Task 1 must preserve profile/provider inputs used by `_herdr_pane`.
- Existing regression `test_target_selector_allocates_pane_when_all_matching_panes_are_ineligible` remains the baseline success case.

**Authority:**
- Preauthorized local actions: edit launcher target discovery and focused tests; run deterministic unit tests with mocked Herdr responses
- Stop for: changes to pane ownership semantics, new persistent lifecycle state, or a need to relax global identity validation

**Steps:**
- [ ] Step 1: Add a candidate-local inspection boundary that preserves
  operation provenance and converts only recoverable pane-scoped
  `LaunchBlocked` and `CommandTransportTimeout` results into
  `TargetCandidateRejected` with structured reasons. Do not catch all
  `LaunchBlocked` values: session-wide `_agent_for_pane` discovery, snapshot
  retrieval, and malformed global responses must remain globally blocked.
- [ ] Step 2: Reclassify snapshot validation so rows with a provably unrelated
  `cwd` can be recorded/skipped, while missing `cwd`, a non-list snapshot, or
  missing `workspace_id`/`pane_id` on a row that may belong to the current
  workspace returns `TargetResolutionBlocked` with deterministic evidence:
  `status=incomplete`, `mode=auto`, `failure_kind=global_snapshot`, a stable
  reason code, and the retained validation detail. Candidate-local failures
  use `failure_kind=candidate_rejected` and never masquerade as global
  corruption.
- [ ] Step 3: Add an explicit allocation reserve within
  `_TARGET_DISCOVERY_TIMEOUT`. Before each candidate inspection, cap its
  timeout to the remaining deadline minus the reserve; once that candidate
  budget is exhausted, stop scanning and use a separate bounded split/poll
  budget for replacement allocation. The reserve must be protected before
  starting a slow subprocess, not only checked after it returns.
- [ ] Step 4: Preserve the existing split-and-poll behavior, structured `allocation` evidence, and exact-pane ownership verification.
- [ ] Step 5: Add tests for incompatible context plus malformed peer, candidate
  invalid JSON, candidate transport timeout, a candidate timeout that asserts
  the capped timeout passed to the subprocess, deadline-before-allocation,
  successful allocation, and each structured global snapshot-corruption case.

**Verification:**
- [ ] `python -m pytest -q tests/test_herdr_main_launcher.py -k "target_selector or target_resolution or pane_ownership"`
- Expected: incompatible/malformed/slow peers do not suppress safe allocation; global identity corruption still returns `TargetResolutionBlocked` with explicit evidence.

**Exit Criteria:**
- Every recoverable candidate-local failure reaches either another candidate or replacement allocation, and only unisolatable global corruption remains fail-closed.

### Task 3: Reconcile docs, packaged output, and final acceptance evidence

**Purpose:**
- Keep the implementation contract and distributed starter-kit output aligned with the source changes.

**Task Function:**
- Reconcile documentation and generated/package validation after the behavioral changes are proven.

**Template Profile:**
- Controller-selected: `normal`
- Selection basis: final cross-surface reconciliation and verification.

**Validator Profile:**
- Controller-selected: `review`
- Selection basis: independently inspect generated policy ownership and final test output.

**Specification Coverage:**
- Documentation states context mismatch and candidate inspection failure allocate a new pane when safe, while global identity failure remains blocked.
- Starter-kit output excludes shared-runtime policy and launcher files, while
  shared-runtime deployment contains the synchronized policy projection and
  launcher behavior.

**Required Skills:**
- `skill-verification-before-completion`

**Files And Symbols:**
- Inspect: `docs/configuration.md:Herdr pane affinity`, `repo_config/starter-kit-manifest.json`
- Modify: `docs/configuration.md`
- Verify: `scripts/build_starter_kit.py`, `scripts/validate_starter_kit.py`,
  `scripts/validate_repo_config.py`, `scripts/deploy_agent_runtime.py`, and
  `tests/test_deploy_agent_runtime.py`

**Dependencies:**
- Tasks 1 and 2 complete with focused tests passing.

**Authority:**
- Preauthorized local actions: update the listed documentation and this plan's
  coordination/evidence sections, and run build/validation commands using
  disposable output
- Stop for: generated drift requiring edits outside canonical sources, failed policy ownership validation, or any untracked user artifact being deleted

**Steps:**
- [ ] Step 1: Update the pane-affinity documentation with the candidate-local versus global-failure contract and policy ownership.
- [ ] Step 2: Build a temporary starter kit from
  `repo_config/starter-kit-manifest.json` and verify that shared paths are
  absent from the generated kit. Separately verify the shared-runtime
  deployment/parity path contains `scripts/retired-model-policy.json` and
  `scripts/herdr_main_launcher.py`, with the policy projection equal to
  `repo_config/retired-model-policy.json`.
- [ ] Step 3: Run the focused tests plus repository configuration and starter-kit validators; record exact output in the plan evidence.

**Verification:**
- [ ] `python -m pytest -q tests/test_agent_profile_registry.py tests/test_herdr_main_launcher.py tests/test_starter_kit_generation.py tests/test_deploy_agent_runtime.py tests/test_validate_repo_config.py`
- [ ] `python scripts/validate_repo_config.py --repo-root . --starter-kit-manifest repo_config/starter-kit-manifest.json`
- [ ] `python scripts/build_starter_kit.py --repo-root . --manifest repo_config/starter-kit-manifest.json --output-root "$env:TEMP\\project-os-starter-kit-plan-check"` followed by `python scripts/validate_starter_kit.py --repo-root . --manifest repo_config/starter-kit-manifest.json --kit-root "$env:TEMP\\project-os-starter-kit-plan-check\\project-OS-starter-kit"`
- Expected: focused tests and validators pass; the generated starter kit
  contains no shared-runtime policy or launcher path, while shared-runtime
  deployment contains the synchronized policy and launcher and no retired
  maintained profile.

**Exit Criteria:**
- Source, tests, documentation, policy projections, shared-runtime deployment,
  and starter-kit boundaries agree, with no new tracked lifecycle state or
  unresolved required finding.

## Verification

- `python -m pytest -q tests/test_agent_profile_registry.py tests/test_herdr_main_launcher.py tests/test_starter_kit_generation.py tests/test_deploy_agent_runtime.py tests/test_validate_repo_config.py`
- `python scripts/validate_repo_config.py --repo-root . --starter-kit-manifest repo_config/starter-kit-manifest.json`
- Build and validate a disposable starter-kit output using `scripts/build_starter_kit.py` and `scripts/validate_starter_kit.py`.
- Inspect `git diff --check` and `git status --short`; preserve pre-existing untracked runtime/browser artifacts.

## Completion Criteria

The plan is ready for completion verification when:

1. retired provider IDs and aliases fail before any launcher side effect;
2. candidate-local pane defects no longer suppress safe replacement allocation;
3. global snapshot corruption still fails closed with deterministic structured
   evidence, while candidate-local failures retain candidate rejection scope;
4. deadline behavior is bounded and covered without adding a second lifecycle store;
5. upstream policy ownership, local projections, shared-runtime deployment,
   docs, tests, and starter-kit boundaries are reconciled;
6. all required focused tests and validators pass with fresh output;
7. no speculative cross-repository runtime, scheduler, or registry work is added.

The plan remains `proposed` until implementation is explicitly approved. It may
be marked `completed` only after `skill-verification-before-completion` returns
`verified` against fresh repository evidence.
