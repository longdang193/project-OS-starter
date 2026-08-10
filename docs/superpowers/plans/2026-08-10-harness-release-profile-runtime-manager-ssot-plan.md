---
artifact_type: plan
template_id: implementation-plan
status: active
layer: change
name: harness-release-profile-runtime-manager-ssot-plan
parent_spec: docs/superpowers/specs/2026-08-10-harness-release-profile-runtime-manager-ssot.md
targets:
  - packages/harness-core
  - packages/harness-core-launcher
  - repo_config/harness.yaml
  - scripts/deploy_harness_core_to_host.ps1
  - docs/operating_system
  - C:/Users/HOANG PHI LONG DANG/repos/codex-harness-host
  - C:/Users/HOANG PHI LONG DANG/repos/project-OS-starter-kit
---

# Harness Release Profile and Runtime Manager SSOT Plan

## Goal

Implement one core-owned runtime protocol profile, one staged host release
profile, and one launcher-owned local pointer. Preserve host lifecycle and
consumer request API boundaries. Remove routine consumer release maintenance.

## Implementation Outcomes

### Core profile and policy boundary

`harness-core` exports canonical runtime protocol/release-profile codecs,
validates same profile at initial and continuation admission, derives current
provider contract from profile, and keeps consumer `request_api` versioned and
policy-owned. Legacy contract field becomes diagnostic-only for legacy schema.

### Verified local runtime manager

Existing `harness-core-launcher` stages clean detached host worktrees, asks
staged core/host to create release profile, verifies host preflight, atomically
activates `$HOME/.codex/harness/current.json`, retains previous profile, and
invokes host only from pointer-selected root.

### Host, kit, and release conformance

Host emits factual profile and tool-use evidence in capability/preflight/run
paths. Core alone decides whether evidence satisfies packet requirements.
Generated consumer guidance calls launcher, not release-specific `uv` host
commands. Release checks classify implementation, profile, and consumer-schema
changes and prove source, host, launcher, kit, and live probe agreement.

## Execution Approach

- Mode: `sequential_work_lanes`
- Required skills: `skill-test-driven-development`, `skill-code-standards`, `skill-backend-verification`, `skill-using-git-worktrees`, `skill-verification-before-completion`
- Isolation: clean worktree for `project-OS-starter`; clean separate worktrees
  for `C:/Users/HOANG PHI LONG DANG/repos/codex-harness-host` and
  `C:/Users/HOANG PHI LONG DANG/repos/project-OS-starter-kit`.
- Commit policy: no commits, tags, publishes, consumer sync, or local profile
  activation without separate explicit authorization.
- Parallel ownership: none. Core profile codec precedes host and launcher;
  pointer dispatch precedes generated guidance; all release checks consume same
  immutable staging contract.
- Sequential fallback: before a tagged core release, run `uv sync --locked` in
  host source, build a local core wheel, temporarily install it into host `.venv`
  with `uv pip install --reinstall --no-deps`, run host tests through
  `.venv/Scripts/python.exe`, then restore with `uv sync --locked`. Never commit
  a local path dependency, alter a lockfile, or repoint a lockfile at an
  unreleased branch.

## Task Breakdown

### Task 1: Add core runtime-profile codec and shared admission

**Purpose:**
- Create one pure core profile contract. Remove current policy contract as an
  active compatibility authority without changing request API ownership.

**Specification Coverage:**
- Core-owned protocol profile; staged release profile codec; shared admission;
  legacy contract migration; profile evidence binding.

**Required Skills:**
- `skill-test-driven-development`
- `skill-code-standards`
- `skill-backend-verification`

**Files And Symbols:**
- Inspect: `packages/harness-core/src/harness_core/compatibility.py:COMPATIBILITY_PROFILES`
- Inspect: `packages/harness-core/src/harness_core/authority.py:canonical_json_bytes`
- Modify: `packages/harness-core/src/harness_core/compatibility.py:runtime_identity`
- Create: `packages/harness-core/src/harness_core/runtime_profile.py`
- Modify: `packages/harness-core/src/harness_core/api.py`
- Modify: `packages/harness-core/src/harness_core/managed.py:_core_identity`
- Modify: `packages/harness-core/src/harness_core/managed.py:_default_runtime_provider`
- Modify: `packages/harness-core/src/harness_core/managed.py:_validate_provider_runtime_binding`
- Modify: `packages/harness-core/src/harness_core/config_validation.py:RUNTIME_PROVIDER_FIELDS`
- Modify: `packages/harness-core/tests/test_compatibility.py`
- Create: `packages/harness-core/tests/test_runtime_profile.py`
- Modify: `packages/harness-core/tests/test_managed.py`
- Modify: `packages/harness-core/tests/test_config_validation.py`

**Dependencies:**
- Approved parent specification.
- Clean core worktree.

**Steps:**
- [ ] Add failing pure-contract tests for exact `harness_runtime_protocol_profile/v1`
  and `harness_runtime_release/v1` fields, canonical digest, unknown-field
  rejection, bool/integer rejection, provider/capability ordering, and
  conflicting core/host provenance.
- [ ] Implement core-only normalizers/builders using
  `authority.canonical_json_bytes`; export public profile APIs without copying
  canonical JSON logic into launcher or host.
- [ ] Declare one new compatibility generation before adding release-profile
  fields: policy schema `10`, packet API `9`, host API `8`, provider contract
  `8`, and `host_terminal_observation/v3`. Preserve packet API `8`, host API
  `7`, provider contract `7`, and terminal-observation v2 readers.
- [ ] Export pure core profile builder/validator APIs. Host CLI is the sole
  profile-writing boundary and supplies host provenance; generic core CLI keeps
  no managed `run` or duplicate release-profile writer.
- [ ] Replace current policy `contract_version` resolution with core protocol
  profile lookup. Preserve `harness_core.request_api` policy validation and
  explicit request version checks.
- [ ] Keep legacy policy schema readable with one diagnostic-only contract
  field. Define next schema without that field. Ensure current packet and
  continuation admission use same profile helper and reject mismatches before
  provider/workspace/packet work.
- [ ] Extend packet and host-binding validation with immutable runtime release
  profile snapshot. Preserve readers for packets without snapshot; never
  synthesize historical evidence.

**Verification:**
- [ ] `uv run --locked pytest -q packages/harness-core/tests/test_runtime_profile.py packages/harness-core/tests/test_compatibility.py packages/harness-core/tests/test_managed.py packages/harness-core/tests/test_config_validation.py -rA`
- [ ] `uv run --locked python scripts/validate_harness_config.py --repo-root .`
- Expected: one core digest binds initial/continuation admission; legacy policy
  cannot override contract; every invalid profile rejects without run mutation.

**Exit Criteria:**
- Core profile/release codecs are sole protocol/digest implementation. Policy
  request API remains unchanged. Direct boundary tests prove success, mismatch,
  legacy migration, historical-reader preservation, and no pre-admission state
  write.

### Task 2: Make host produce and bind staged release-profile evidence

**Purpose:**
- Let host assemble provenance through staged locked runtime while importing
  core profile codec. Bind one release profile to every host evidence path.

**Specification Coverage:**
- Staged release profile; host lifecycle boundary; active-profile invocation;
  host evidence/profile agreement.

**Required Skills:**
- `skill-test-driven-development`
- `skill-code-standards`
- `skill-backend-verification`

**Files And Symbols:**
- Inspect: `C:/Users/HOANG PHI LONG DANG/repos/codex-harness-host/src/codex_harness_host/cli.py:main`
- Inspect: `C:/Users/HOANG PHI LONG DANG/repos/codex-harness-host/src/codex_harness_host/adapter.py:CodexAdapter.preflight_evidence`
- Inspect: `C:/Users/HOANG PHI LONG DANG/repos/codex-harness-host/src/codex_harness_host/adapter.py:static_provider_runtime_binding`
- Create: `C:/Users/HOANG PHI LONG DANG/repos/codex-harness-host/src/codex_harness_host/release_profile.py`
- Modify: `C:/Users/HOANG PHI LONG DANG/repos/codex-harness-host/src/codex_harness_host/cli.py`
- Modify: `C:/Users/HOANG PHI LONG DANG/repos/codex-harness-host/src/codex_harness_host/adapter.py`
- Modify: `C:/Users/HOANG PHI LONG DANG/repos/codex-harness-host/pyproject.toml`
- Modify: `C:/Users/HOANG PHI LONG DANG/repos/codex-harness-host/uv.lock`
- Create: `C:/Users/HOANG PHI LONG DANG/repos/codex-harness-host/tests/test_release_profile.py`
- Modify: `C:/Users/HOANG PHI LONG DANG/repos/codex-harness-host/tests/test_cli.py`
- Modify: `C:/Users/HOANG PHI LONG DANG/repos/codex-harness-host/tests/test_adapter.py`
- Modify: `C:/Users/HOANG PHI LONG DANG/repos/codex-harness-host/tests/test_runtime_dependencies.py`

**Dependencies:**
- Task 1 core profile APIs available in test environment.
- Temporary cross-repository test install may use a local core wheel only outside
  committed host files and lockfile.

**Steps:**
- [ ] Add failing host tests for building release profile from staged host root,
  full Git HEAD, locked installed core provenance, host package version, and
  core protocol profile. Reject dirty/missing Git, editable core, bad lock,
  malformed profile, and profile conflict.
- [ ] Implement host release-profile assembly as a thin provenance collector
  calling core public builder/validator. Write generated document at
  `staging/<id>/release.json`, sibling to clean `staging/<id>/host/`; never
  write it into host source or commit it.
- [ ] Add host CLI maintenance operation used by launcher to write/verify staged
  release profile. It must be non-managed, bounded, JSON-only, and reject
  arbitrary output paths outside staged runtime root.
- [ ] Extend capabilities, preflight, adapter identity, provider binding, lane
  evidence, and terminal evidence to carry exact release profile ID/digest.
  Reject missing/conflicting profile before provider lifecycle work.
- [ ] Update host package dependency and lock only after core release artifact
  is available through approved source. Before that, use exact temporary wheel
  install/restore procedure from execution approach and retain committed host
  lock unchanged.

**Verification:**
- [ ] From host worktree: `uv run --locked pytest -q tests/test_release_profile.py tests/test_cli.py tests/test_adapter.py tests/test_runtime_dependencies.py -rA`
- [ ] From host worktree: `uv run --locked codex-harness-host capabilities`
- [ ] From host worktree: `uv run --locked codex-harness-host preflight`
- Expected: staged profile is exact, evidence is profile-bound, malformed or
  provenance-conflicting stage has no provider process or core run mutation.

**Exit Criteria:**
- Host remains provider-lifecycle owner and emits one profile binding everywhere
  core consumes host identity/evidence. No host compatibility table or committed
  self-referential release file exists.

### Task 3: Extend existing launcher with atomic profile activation

**Purpose:**
- Reuse `harness-core-launcher` as stable bootstrap. Add profile staging,
  pointer transaction, rollback, doctor, and pointer-root host invocation.

**Specification Coverage:**
- V1 locked-source trust channel; atomic pointer; idempotency; rollback;
  PATH isolation; no new package or daemon.

**Required Skills:**
- `skill-test-driven-development`
- `skill-code-standards`
- `skill-backend-verification`

**Files And Symbols:**
- Inspect: `packages/harness-core-launcher/src/harness_core_launcher/loader.py:load_core`
- Inspect: `packages/harness-core-launcher/src/harness_core_launcher/cli.py:main`
- Create: `packages/harness-core-launcher/src/harness_core_launcher/runtime_manager.py`
- Modify: `packages/harness-core-launcher/src/harness_core_launcher/cli.py:main`
- Modify: `packages/harness-core-launcher/src/harness_core_launcher/__init__.py`
- Modify: `packages/harness-core-launcher/tests/test_loader.py`
- Create: `packages/harness-core-launcher/tests/test_runtime_manager.py`
- Modify: `packages/harness-core-launcher/pyproject.toml`

**Dependencies:**
- Tasks 1 and 2 define core verifier and host profile writer.
- Temporary Git fixtures support detached worktree staging.

**Steps:**
- [ ] Add failing launcher tests for no pointer, clean-source stage, source
  dirty/commit/lock rejection, staged-profile creation, same-digest replay,
  preflight failure cleanup, atomic activation fault before/after replacement,
  lock contention, rollback, two-profile retention, and stale PATH executable.
- [ ] Implement pointer codec at `$HOME/.codex/harness/current.json`, sibling
  staging/profile directories, same-directory temporary pointer write plus
  atomic replacement, and current-plus-previous cleanup. Use
  `git worktree move` to move linked `staging/<id>/host/` to
  `profiles/<digest>/host/`, move sibling `release.json`, and use
  `git worktree remove` for discarded linked worktrees. Never raw-rename a
  linked worktree or duplicate core schema/digest logic.
- [ ] Implement one activation-lock abstraction: `msvcrt.locking` on Windows
  and `fcntl.flock` on POSIX. Return typed busy result. Test direct contention
  for each supported platform branch.
- [ ] Implement one `verify_active_profile()` gate before every launcher host
  invocation: doctor, capabilities, preflight, managed run, and pass-through.
  Verify pointer containment, release digest, Git HEAD and clean state, lock
  provenance, installed core direct URL, host/core releases, and schema support.
  Invoke host only through explicit `uv --project <active_root>` or equivalent
  absolute active-root command. Pass profile path as bounded non-secret runtime
  context. Never resolve host from PATH.
- [ ] Add launcher commands for upgrade, rollback, doctor, preflight, and host
  pass-through. Require supported release schema; return typed JSON for missing,
  invalid, untrusted, busy, preflight-failed, mismatch, and rollback-unavailable
  states.
- [ ] Ensure cleanup never deletes current/previous profiles, arbitrary paths,
  source checkout, user provider configuration, `.harness`, or running provider
  processes.

**Verification:**
- [ ] `uv run --locked pytest -q packages/harness-core-launcher/tests/test_loader.py packages/harness-core-launcher/tests/test_runtime_manager.py -rA`
- [ ] Temporary fixture verifies `Get-Command codex-harness-host` resolves a
  stale stub while launcher invokes only pointer-selected host root.
- Expected: every activation is idempotent, atomic, rollback-safe, and does not
  start provider work on rejection.

**Exit Criteria:**
- Existing launcher is sole bootstrap. Current pointer and active-root invocation
  replace release-specific consumer `uv` commands without new package, daemon,
  mutable profile table, or PATH host fallback.

### Task 4: Bind profile through core managed lifecycle

**Purpose:**
- Complete core/host/launcher contract. Require matching profile evidence before
  packet or provider work and retain immutable snapshot in new packets.

**Specification Coverage:**
- Uniform managed invocation; packet/run evidence; initial/continuation
  symmetry; historical packet preservation.

**Required Skills:**
- `skill-test-driven-development`
- `skill-backend-verification`

**Files And Symbols:**
- Modify: `packages/harness-core/src/harness_core/managed.py:static_provider_runtime_binding`
- Modify: `packages/harness-core/src/harness_core/managed.py:_validate_provider_runtime_binding`
- Modify: `packages/harness-core/src/harness_core/managed.py:resolve_managed_packet`
- Modify: `packages/harness-core/src/harness_core/managed.py:run_managed`
- Modify: `packages/harness-core/src/harness_core/terminal_observation.py`
- Modify: `packages/harness-core/tests/test_managed.py`
- Modify: `packages/harness-core/tests/test_terminal_observation.py`
- Modify: `C:/Users/HOANG PHI LONG DANG/repos/codex-harness-host/src/codex_harness_host/adapter.py`
- Modify: `C:/Users/HOANG PHI LONG DANG/repos/codex-harness-host/tests/test_adapter.py`
- Modify: `C:/Users/HOANG PHI LONG DANG/repos/codex-harness-host/tests/test_live_single_work_lane.py`
- Modify: `C:/Users/HOANG PHI LONG DANG/repos/codex-harness-host/tests/test_live_parallel_work_lanes.py`

**Dependencies:**
- Tasks 1 through 3 complete in temporary cross-repository test environment.

**Steps:**
- [ ] Add failure-first tests for missing, malformed, stale, mismatched, and
  capability-conflicting release profile evidence at initial admission,
  continuation, preflight, lane execution, and terminal observation boundaries.
- [ ] Add failure-first core/host tests for completed validator with no recorded
  packet-selected tool use. Host must return factual terminal observation with
  empty `selected_tools_used`; core must reject packet tool requirement, persist
  validator terminal observation, and release lease. Keep host rejection of
  ambient or disallowed tool access.
- [ ] Extend static binding and packet schema with exact release-profile snapshot
  and validate against core profile once. Reuse same validator in initial and
  continuation paths; reject before workspace or `run.json` creation.
- [ ] Project profile evidence into host preflight/terminal data and assert core
  preserves it only as validated immutable packet evidence.
- [ ] Remove host decision on minimum packet-selected tool use. Host records
  factual selected-tool use and terminal observation only; core is sole owner of
  packet minimum-tool satisfaction for primary and validator lanes.
- [ ] Preserve profile-less historical packets/readers. Reject their new
  dispatch/resume only under existing historical compatibility rules; never
  synthesize profile or mutate stored packet.
- [ ] Add bounded read-only host probe through launcher, then compare pointer,
  host capabilities/preflight, packet, and terminal evidence digests.

**Verification:**
- [ ] `uv run --locked pytest -q packages/harness-core/tests/test_managed.py packages/harness-core/tests/test_terminal_observation.py -rA`
- [ ] From host worktree: `uv run --locked pytest -q tests/test_adapter.py tests/test_live_single_work_lane.py tests/test_live_parallel_work_lanes.py -rA`
- Expected: one digest survives full lifecycle; any forced mismatch creates no
  packet/run state or provider work.

**Exit Criteria:**
- Initial, continuation, live single-lane, and live parallel-lane paths share
  one core profile admission and profile-bound host evidence.

### Task 5: Migrate consumer policy, canonical guidance, and kit outputs

**Purpose:**
- Remove copied runtime compatibility values and manual host invocation from
  maintained consumer surfaces. Preserve policy request API and routing SSOT.

**Specification Coverage:**
- Thin consumer policy; legacy migration; kit ownership; generated surfaces;
  no consumer-specific release update for compatible implementation release.

**Required Skills:**
- `skill-code-standards`
- `skill-backend-verification`

**Files And Symbols:**
- Modify: `repo_config/harness.yaml:runtime_providers`
- Modify: `scripts/validate_harness_config.py`
- Modify: `scripts/deploy_harness_core_to_host.ps1`
- Modify: `tests/test_deploy_harness_core_to_host.py`
- Modify: `docs/operating_system/procedures/harness-core-consumer-setup.md`
- Modify: `docs/operating_system/procedures/managed-execution-adapter-contract.md`
- Modify: `docs/operating_system/templates/agents/root-AGENTS.template.md`
- Modify: `docs/operating_system/rules/multi-agent-orchestration-rule.md`
- Modify: `C:/Users/HOANG PHI LONG DANG/repos/project-OS-starter-kit/repo_config/harness.yaml`
- Modify: `C:/Users/HOANG PHI LONG DANG/repos/project-OS-starter-kit/docs/operating_system/templates/agents/root-AGENTS.template.md`
- Modify: `C:/Users/HOANG PHI LONG DANG/repos/project-OS-starter-kit/docs/operating_system/rules/multi-agent-orchestration-rule.md`
- Modify: `C:/Users/HOANG PHI LONG DANG/repos/project-OS-starter-kit/scripts/validate_repo_contracts.py`

**Dependencies:**
- Tasks 1 through 4 pass direct tests.
- Canonical core/host/launcher command interface settled.

**Steps:**
- [ ] Add policy fixtures for legacy provider contract diagnostic-only behavior
  and new schema rejection. Keep `harness_core.request_api` owner/value.
- [ ] Update canonical consumer policy to remove active `contract_version` and
  move equivalent capability requirements to core profile validation. Do not
  add host/packet/profile numbers elsewhere.
- [ ] Replace deployment bridge body with launcher doctor/preflight evidence;
  retain script name only as migration bridge. Assert it never calls bare host.
- [ ] Update consumer setup, managed adapter contract, root agent template, and
  orchestration rule with launcher-first command and typed remediation. Keep
  provider user config external and secret-free.
- [ ] Apply identical canonical changes to starter kit, run its own generators,
  then sync current repository kit outputs only after separate approval.
- [ ] Render adapter outputs from templates. Delete obsolete release pins and
  manual locked-host command prose rather than maintaining parallel guidance.

**Verification:**
- [ ] `uv run --locked python scripts/validate_harness_config.py --repo-root .`
- [ ] `uv run --locked pytest -q tests/test_deploy_harness_core_to_host.py -rA`
- [ ] `uv run --locked python scripts/sync_agent_adapters.py --check`
- [ ] From starter-kit worktree: run its documented contract, template, and
  generated-output validators.
- Expected: request API remains policy-owned; runtime contract does not appear
  in active consumer policy or generated guidance; bridge invokes launcher only.

**Exit Criteria:**
- Core, docs, and kit have one consumer migration story. Kit owns generated
  epoch/sync; no release profile stores kit generation metadata.

### Task 6: Add release conformance classification and full proof

**Purpose:**
- Make release effort proportional to changed contract and prove v1 runtime
  works through actual active-pointer path.

**Specification Coverage:**
- Release tiers; cross-repository provenance; direct backend proof; bounded live
  probe; final source/kit/runtime drift reconciliation.

**Required Skills:**
- `skill-backend-verification`
- `skill-verification-before-completion`

**Files And Symbols:**
- Modify: `scripts/validate_repo_contracts.py`
- Create: `scripts/validate_harness_release_profile.py`
- Create: `tests/test_validate_harness_release_profile.py`
- Modify: `C:/Users/HOANG PHI LONG DANG/repos/codex-harness-host/tests/test_runtime_dependencies.py`
- Modify: `C:/Users/HOANG PHI LONG DANG/repos/project-OS-starter-kit/scripts/validate_repo_contracts.py`
- Modify: `docs/operating_system/procedures/harness-core-consumer-setup.md`

**Dependencies:**
- Tasks 1 through 5 complete.
- Approved temporary core artifact available for host test environment.
- No active historical run is used as test subject.

**Steps:**
- [ ] Add release-profile validator that compares core protocol output, staged
  release profile, pointer, host identities/evidence, policy schema, and kit
  generated surfaces. It classifies source change using externally observable
  profile, host-manager, and consumer-schema inputs; it does not infer from
  prose version strings.
- [ ] Add fixtures for implementation-only change, profile change, and
  consumer-schema change. Assert expected required check set and kit-sync
  disposition for each.
- [ ] Run direct core/launcher/host matrix for profile validation, activation,
  rollback, policy migration, claim repair capability, retry policy, execution
  budget/finalization reserve, toolsets/skill sets, and single/sequential/
  parallel scheduling profiles.
- [ ] Run one fresh active-pointer, read-only managed provider probe after local
  preflight. Capture profile ID/digest through pointer, capability, preflight,
  packet, lane evidence, and terminal receipt without dispatching product work.
- [ ] Reconcile source docs, generated adapters, kit, locks, runtime identity,
  and diff hygiene. Treat unavailable live provider as recorded blocker, never
  substitute stale host/PATH proof or mutate historical run.

**Verification:**
- [ ] `uv run --locked pytest -q packages/harness-core/tests packages/harness-core-launcher/tests tests/test_validate_harness_release_profile.py -rA`
- [ ] From host worktree: `uv run --locked pytest -q tests -rA`
- [ ] `uv run --locked python scripts/validate_harness_release_profile.py --fast`
- [ ] `uv run --locked python scripts/validate_repo_contracts.py --fast`
- [ ] `git diff --check` in core, host, and kit worktrees.
- Expected: release tier is mechanically reproducible; every required profile
  boundary matches; bounded fresh probe succeeds or records typed environment
  blocker with no product/run mutation.

**Exit Criteria:**
- Verification can prove source, installed runtime, profile, policy, kit, and
  live host agree. Compatible implementation release needs focused checks only;
  profile/consumer changes trigger required broader proof.

## Verification

- Run all task-local tests before consuming downstream work.
- Run final core, launcher, host, and kit suites only after temporary cross-repo
  installation has exact planned profile contract.
- Run source/kit validators and generated-output checks after canonical changes.
- Run one bounded fresh active-pointer read-only probe after local profile stage.
- Record unavailable external provider as blocker; never retry through bare PATH
  host, legacy packet, historical run, or consumer-local fallback.

## Completion Criteria

The plan is ready for completion verification when:

1. protocol/release/pointer schemas and typed failure paths have direct tests
2. profile trust reuses clean Git source, detached worktree, lock provenance,
   staged core verification, and no custom registry or self-referential commit
3. activation is atomic, contention-safe, idempotent, rollback-safe, and keeps
   exactly current plus previous verified profile
4. launcher selects host by active pointer only; host retains provider lifecycle
   ownership; core retains compatibility, packet, and run ownership
5. initial and continuation admission, packet, host evidence, and terminal
   evidence bind one release profile digest and tool-use requirements have one
   core owner
6. consumer request API remains policy-owned; active provider contract is
   core-owned; legacy policy and historical packet preservation are proven
7. canonical docs and starter-kit surfaces have no release-specific host paths,
   package pins, host/packet API, or provider contract copies
8. release classification and cross-repository matrix prove focused versus full
   verification disposition, with fresh bounded active-pointer probe evidence
9. final verification reports no unresolved required task, failed check, stale
   generated output, unrecorded deviation, or unapproved release action
