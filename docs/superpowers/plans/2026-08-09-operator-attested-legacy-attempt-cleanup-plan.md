---
artifact_type: plan
status: completed
layer: change
template_id: implementation-plan
name: operator-attested-legacy-attempt-cleanup
parent_spec: docs/superpowers/specs/2026-08-09-unified-attempt-terminalization-ssot.md
targets:
  - packages/harness-core
  - repo_config/harness.yaml
  - docs/operating_system
  - ../codex-harness-host
---

# Operator-Attested Legacy Attempt Cleanup Plan

## Goal

Replace direct legacy abandonment with signed operator cleanup evidence. Core
keeps `terminalize_attempt(evidence)` as sole terminal-evidence transaction.
Legacy attempts remain isolated from dispatch and resume until core verifies
fresh complete cleanup scope, records block-only outcome, and controller applies
existing `block` decision without another human approval.

## Execution Status

Tasks 1 through 4 implemented and verified on August 9, 2026. Core release
`9862e140dddd24f259c967e73ae752997c21f84c` is tagged
`harness-core-v0.1.21` and pushed to `origin/main`. Host release
`ba7cd2ff1ac21843a4a8fd49ea5900d65eef6027` pins that tag, is version `0.1.6`,
and is pushed to `origin/master`.

Fresh final proof passed: core config validation, `233` core tests, generated
agent-surface sync, `29` generated-doc tests, core and host lock checks, host
runtime dependency tests, host capabilities, and host preflight. Host proof
used isolated environment `C:\tmp\codex-harness-host-0.1.6-verify-019fe663`;
the live Successor9 host environment and provider process tree were untouched.

## Implementation Outcomes

### Public-key legacy cleanup contract

`harness-core` validates one bounded `legacy_cleanup_attestation/v1` evidence
variant. `~/.codex/harness-attesters.toml` contains only Ed25519 public keys,
opaque attester IDs, roles, and active or revoked status. Private signing
material remains outside harness execution.

### Symmetric core terminalization

`terminalize_attempt` accepts exactly one evidence source per call. Valid
historical unleased cleanup evidence creates normal core terminal record and
block-only outcome, then enters `awaiting_decision`. Existing
`apply_controller_decision({"kind": "block"})` records final automatic block.

### Isolated migration and compatible runtime

Active legacy attempts cannot dispatch or resume, but do not globally block new
leased-packet admission. `abandon_legacy_attempt` becomes mutation-free
migration error. Host behavior stays process lifecycle and evidence only; host
runtime pin advances after verified core release.

## Execution Approach

- Mode: `sequential_work_lanes`.
- Required skills: `skill-test-driven-development`, `skill-code-standards`, `skill-backend-verification`, `skill-verification-before-completion`.
- Ownership: core tasks first in `.`; host release task second in `../codex-harness-host`.
- Isolation: use clean worktrees. Do not touch existing `JOB-PROJECT` work or host runtime edits.
- Commit policy: no commit, tag, publish, or push without separate authorization.
- Dependency rule: add `cryptography>=44,<45` because correct Ed25519 verification has no Python standard-library implementation. No host lifecycle feature or process-control fallback is added.

## Task Breakdown

### Task 1: Add policy and public-key attestation normalizer

**Purpose:**
Define one bounded, deterministic legacy cleanup evidence contract before state mutation.

**Specification Coverage:**
Ownership and trusted boundary; operator-attested legacy cleanup; exact schema;
fresh absence evidence; complete provider-tree scope; rejection behavior.

**Required Skills:**
`skill-test-driven-development`, `skill-code-standards`, `skill-backend-verification`.

**Files And Symbols:**
- Modify: `packages/harness-core/pyproject.toml`.
- Modify: `uv.lock`.
- Modify: `repo_config/harness.yaml`.
- Modify: `packages/harness-core/src/harness_core/config_validation.py:POLICY_FIELDS`.
- Create: `packages/harness-core/src/harness_core/legacy_cleanup.py`.
- Modify: `packages/harness-core/src/harness_core/managed.py:main`.
- Modify: `packages/harness-core/src/harness_core/api.py`.
- Create: `packages/harness-core/tests/test_legacy_cleanup.py`.
- Create: `packages/harness-core/tests/test_cli.py`.
- Modify: `packages/harness-core/tests/test_config_validation.py`.

**Dependencies:**
Active unified terminalization SSOT and clean core worktree.

**Steps:**
- [ ] Run `uv add --package harness-core "cryptography>=44,<45"`, then retain matching direct dependency and update `uv.lock`.
- [ ] Add validated `legacy_cleanup` policy with exact values: historical packet maximum API `7`; scopes `operator_discovered_provider_tree` and `operator_attested_no_provider_process`; discovery methods `windows_parent_chain/v1` and `windows_no_process_observation/v1`; attestation age `900` seconds; lifetime `900` seconds; clock skew `60` seconds; payload limit `8192` bytes; identifier limit `128` bytes; creation-ID limit `256` bytes; reason length `4096`; identity limit `32`; role `managed_cleanup_operator`.
- [ ] Implement `legacy_cleanup_trusted_config_path()`, `load_legacy_cleanup_attesters()`, `normalize_legacy_cleanup_attestation()`, and `verify_legacy_cleanup_signature()` in `legacy_cleanup.py`. Load only `~/.codex/harness-attesters.toml`; accept only one `[attesters.<issuer_key_id>]` record containing `attester_id`, `role`, `algorithm = "ed25519"`, `public_key`, and `status`.
- [ ] Reject private-key fields, unknown fields, duplicate issuer IDs, invalid base64url public keys or signatures, revoked issuers, unsupported algorithms, non-ASCII opaque IDs, non-lowercase SHA-256, nonpositive PIDs, duplicate `{pid, creation_id}`, non-absent identity state, `scope_complete != true`, unknown scope or discovery method, missing `absence_observed_at`, timestamp ordering failure, stale or future timestamp, oversized payload, and scope-shape mismatch. Require nonempty root-included list for `operator_discovered_provider_tree`; require null root and empty list for `operator_attested_no_provider_process`.
- [ ] Canonicalize unsigned evidence with UTF-8 sorted compact JSON bytes. Require exact unsigned fields and one transport-only `attestation_signature`; return normalized attester ID, issuer key ID, signed-payload digest, bounded audit values, and one tagged scope shape.
- [ ] Add operator-only `harness-core sign-legacy-cleanup --attestation <path> --private-key-file <path> --output <path>`. Reject key file under repository root. Command writes signed JSON only and never creates or edits `run.json`; use it only from external operator identity with ACL-protected key material.
- [ ] Add controller-only `harness-core terminalize-attempt --repo-root <path> --run-id <id> --evidence <path> --auto-block`. Command invokes `terminalize_attempt` once, applies only legacy `block`, returns success on same-evidence replay after block, and exposes no host lifecycle action.
- [ ] Add direct unit and CLI tests using ephemeral Ed25519 private keys only inside test process. Write public-only TOML under temporary home path; prove active signature passes, revoked issuer blocks new evidence, existing replay survives later revocation, and every rejected case leaves no mutable test run state.

**Verification:**
- [ ] `uv run --locked --package harness-core pytest packages/harness-core/tests/test_legacy_cleanup.py packages/harness-core/tests/test_config_validation.py -q`
- [ ] `uv run --locked python scripts/validate_harness_config.py --repo-root .`
- Expected: valid public-key signature normalizes; invalid input rejects deterministically; policy accepts only exact bounded fields.

**Exit Criteria:**
Core has one public-key-only normalizer plus controller and operator entrypoints with direct rejection proof.

### Task 2: Route cleanup through core terminalization and automatic block

**Purpose:**
Retire independent legacy mutation without creating a second terminal path.

**Specification Coverage:**
Single `terminalize_attempt(evidence)` boundary; atomicity; idempotency; block-only
outcome; controller decision symmetry; migration isolation.

**Required Skills:**
`skill-test-driven-development`, `skill-code-standards`, `skill-backend-verification`.

**Files And Symbols:**
- Modify: `packages/harness-core/src/harness_core/managed.py:_terminalization_input`.
- Modify: `packages/harness-core/src/harness_core/managed.py:terminalize_attempt`.
- Modify: `packages/harness-core/src/harness_core/managed.py:run_managed`.
- Modify: `packages/harness-core/src/harness_core/managed.py:migration_preflight`.
- Modify: `packages/harness-core/src/harness_core/managed.py:abandon_legacy_attempt`.
- Modify: `packages/harness-core/src/harness_core/managed.py:apply_controller_decision`.
- Modify: `packages/harness-core/src/harness_core/api.py`.
- Modify: `packages/harness-core/tests/test_terminalization.py`.
- Modify: `packages/harness-core/tests/test_managed.py`.

**Dependencies:**
Task 1 complete.

**Steps:**
- [ ] Extend `_terminalization_input` so evidence has exactly one source: `host_terminal_observations`, `recovery_observation`, `stranded_recovery`, or `legacy_cleanup_attestation`. Reject source mixing before any run write.
- [ ] In `terminalize_attempt`, branch legacy normalization before `_attempt_lease_binding`. Permit only historical unleased active attempt with no claim, node observation, evidence, outcome, decision, terminal record, or current terminal-observation contract. Keep normal leased and recovery paths unchanged.
- [ ] Build legacy terminal ID and evidence digest from run ID, attempt ID, null lease identity, and normalized signed attestation digest. Persist `attempt_terminal_evidence/v2` with `source_kind: legacy_cleanup`, null lease fields, normalized legacy audit, no host observation digests, classification `legacy_cleanup_attested`, and block-only allowed decision. Preserve pre-existing leased v2 record shape; reader tests must require nonnull lease fields unless `source_kind` is `legacy_cleanup`.
- [ ] Normalize candidate legacy evidence and compare its digest with existing terminal record before terminal-state rejection. Same evidence returns `replayed` from `awaiting_decision` or `blocked`; different evidence returns `attempt_already_terminal`. Do not re-evaluate issuer status when exact stored digest already matches.
- [ ] Preserve existing atomic lock, state history, revision, temporary-file, and conflicting-evidence behavior. Transition valid legacy terminalization to `awaiting_decision`, never directly to `blocked`.
- [ ] Make `apply_controller_decision` reject every decision except `block` for `legacy_cleanup_attested`. `terminalize-attempt --auto-block` must retry-safe apply block only from matching `awaiting_decision`, treat matching terminal `blocked` result as success, and reject all other states.
- [ ] Change `migration_preflight` and `run_managed` admission so active legacy attempts report isolated status and reject their dispatch or resume, while new leased packets remain admissible. Preserve exact historical packet bytes.
- [ ] Replace `abandon_legacy_attempt` mutation with `HarnessError("legacy_abandonment_retired")`; retain temporary API export only for callers to receive migration error. Do not add host cleanup, termination, or attestation command.
- [ ] Add focused regression tests for both cleanup scopes, valid terminalization then automatic block, exact replay before and after block, replay after issuer revocation, conflicting signed evidence, all legacy eligibility rejections, tagged null legacy lease fields, byte-identical failure paths, concurrent calls, retired abandonment, new-packet admission despite isolated legacy run, and legacy resume rejection.

**Verification:**
- [ ] `uv run --locked --package harness-core pytest packages/harness-core/tests/test_terminalization.py packages/harness-core/tests/test_managed.py packages/harness-core/tests/test_legacy_cleanup.py -q`
- [ ] `uv run --locked --package harness-core pytest packages/harness-core/tests -q`
- Expected: one core terminal transaction writes every legacy terminal record; controller entrypoint recovers interrupted automatic block; no legacy mutation bypass remains.

**Exit Criteria:**
Legacy cleanup shares terminalization and decision machinery without synthetic lease or direct block writer.

### Task 3: Update controller guidance and generated policy surfaces

**Purpose:**
Make controller flow, public-key configuration boundary, and migration behavior consumable without leaking signing material or adding host responsibility.

**Specification Coverage:**
Trusted configuration ownership; bounded agent autonomy; host boundary; migration;
runtime compatibility; generated guidance.

**Required Skills:**
`skill-code-standards`, `skill-backend-verification`.

**Files And Symbols:**
- Modify: `docs/operating_system/procedures/managed-execution-adapter-contract.md`.
- Modify: `docs/operating_system/procedures/harness-core-consumer-setup.md`.
- Modify: `docs/operating_system/templates/agents/root-AGENTS.template.md`.
- Modify: `README.md`.
- Generate: `AGENTS.md`.
- Generate: `generated_agents/codex/AGENTS.md`.
- Generate: `generated_agents/claude/CLAUDE.md`.
- Generate: `generated_agents/antigravity/GEMINI.md`.
- Generate: `docs/operating_system/tooling/harness-routing.generated.md`.
- Verify: `scripts/sync_agent_adapters.py`.
- Verify: `scripts/render_harness_routing.py`.

**Dependencies:**
Task 2 complete.

**Steps:**
- [ ] Document public-only `~/.codex/harness-attesters.toml` schema, external private signer boundary, exact attestation fields, Ed25519 signing bytes, and redaction rule. Do not include real keys, actor names, process output, commands, paths, or private signing guidance.
- [ ] Document operator sequence: build unsigned evidence, run `harness-core sign-legacy-cleanup` from external operator identity with key outside repository and agent workspace, then transfer signed JSON without private key. Document controller sequence: run `harness-core terminalize-attempt --auto-block`; command resumes safely after interruption. State that agent may transport attestation but cannot mint or broaden it.
- [ ] Replace active-legacy release-drain wording with isolation from dispatch and resume. Keep host lifecycle-only ownership and explicit prohibition on `taskkill`, PID-tree reaper, named Job Object reaper, and generic CLI cleanup command.
- [ ] Update canonical root-agent template only; regenerate derived agent instructions and routing from canonical sources.

**Verification:**
- [ ] `uv run --locked python scripts/sync_agent_adapters.py`
- [ ] `uv run --locked python scripts/render_harness_routing.py`
- [ ] `uv run --locked pytest tests/test_sync_agent_adapters.py tests/test_render_harness_routing.py tests/test_validate_template_required_sections.py -q`
- Expected: generated files match canonical docs; no raw secret, private path, old direct-abandonment rule, or host cleanup ownership remains.

**Exit Criteria:**
Controller and agents receive one safe cleanup flow from canonical documentation.

### Task 4: Release core and refresh host runtime pin

**Purpose:**
Ship compatible runtime without giving host terminal-state or attester responsibilities.

**Specification Coverage:**
Runtime compatibility; host ownership; released-package proof; migration safety.

**Required Skills:**
`skill-code-standards`, `skill-backend-verification`, `skill-verification-before-completion`.

**Files And Symbols:**
- Modify: `packages/harness-core/pyproject.toml`.
- Modify: `../codex-harness-host/pyproject.toml`.
- Modify: `../codex-harness-host/uv.lock`.
- Modify: `../codex-harness-host/tests/test_runtime_dependencies.py`.
- Verify: `../codex-harness-host/tests/test_cli.py`.

**Dependencies:**
Tasks 1 through 3 complete and core verification green.

**Steps:**
- [ ] Bump `harness-core` package version from `0.1.20` to `0.1.21` after authorized release preparation; create tag `harness-core-v0.1.21` only after separate commit and tag approval.
- [ ] In clean host worktree, bump `codex-harness-host` from `0.1.5` to `0.1.6`, pin `harness-core` source to `harness-core-v0.1.21`, refresh `uv.lock`, and update runtime dependency assertion.
- [ ] Keep host API `7`, host capabilities, process lifecycle, observation schema, and CLI command set unchanged. Do not add terminalization, attestation verification, legacy cleanup, or process termination command to host.
- [ ] Run `uv sync --locked` in host worktree and prove imported `harness_core` package version is `0.1.21` before host capability and preflight checks.

**Verification:**
- [ ] From `.`: `uv run --locked --package harness-core pytest packages/harness-core/tests -q`
- [ ] From `../codex-harness-host`: `uv sync --locked`
- [ ] From `../codex-harness-host`: `uv run --locked pytest tests/test_runtime_dependencies.py tests/test_cli.py tests/test_adapter.py -q`
- [ ] From `../codex-harness-host`: `uv run --locked codex-harness-host capabilities`
- [ ] From `../codex-harness-host`: `uv run --locked codex-harness-host preflight`
- Expected: released host imports core `0.1.21`, still advertises API `7`, and exposes no cleanup or termination command.

**Exit Criteria:**
Compatible released core and host preserve ownership boundary and runtime admission proof.

## Verification

- `uv run --locked python scripts/validate_harness_config.py --repo-root .`
- `uv run --locked --package harness-core pytest packages/harness-core/tests/test_legacy_cleanup.py packages/harness-core/tests/test_terminalization.py packages/harness-core/tests/test_managed.py packages/harness-core/tests/test_config_validation.py -q`
- `uv run --locked --package harness-core pytest packages/harness-core/tests -q`
- `uv run --locked python scripts/sync_agent_adapters.py`
- `uv run --locked python scripts/render_harness_routing.py`
- `uv run --locked pytest tests/test_sync_agent_adapters.py tests/test_render_harness_routing.py tests/test_validate_template_required_sections.py -q`
- `uv lock --check`
- From `../codex-harness-host`: `uv lock --check`
- From `../codex-harness-host`: `uv run --locked pytest tests/test_runtime_dependencies.py tests/test_cli.py tests/test_adapter.py -q`
- `git diff --check`

## Completion Criteria

1. Core accepts only bounded signed `legacy_cleanup_attestation/v1` from active public-key attester configuration.
2. Private signing material never enters repository, trusted verifier config, host, packet, request, agent workspace, or `run.json`.
3. Valid unleased historical cleanup uses `terminalize_attempt`, records core-owned terminal evidence, and exposes only `block` decision.
4. Invalid, stale, partial, duplicate, conflicting, leased, current, claimed, observed, or terminal attempts remain byte-identical.
5. `abandon_legacy_attempt` cannot mutate state; host owns no cleanup command or legacy process action.
6. Active legacy attempts block only their dispatch and resume; new leased packets remain admissible.
7. Core, documentation, generated-surface, lockfile, host runtime, capability, preflight, and whitespace checks pass from fresh commands.

Plan completes only after `skill-verification-before-completion` reports fresh
verified evidence. Commits, tags, releases, and pushes remain separate explicit
authorization.
