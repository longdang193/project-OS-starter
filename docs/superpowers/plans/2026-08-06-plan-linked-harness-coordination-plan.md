---
artifact_type: plan
template_id: implementation-plan
status: completed
layer: change
name: plan-linked-harness-coordination
parent_spec: docs/superpowers/specs/2026-08-06-plan-linked-harness-coordination.md
targets:
  - repo_config/planning_artifact_schema.yaml
  - scripts/plan_coordination.py
  - scripts/validate_planning_lifecycle.py
  - scripts/harness_task.py
  - docs/operating_system/templates/implementation-plan-template.md
  - docs/operating_system/templates/agents/root-AGENTS.template.md
  - .agents/skills/skill-writing-plans/SKILL.md
  - .agents/skills/skill-executing-plans/SKILL.md
  - .agents/skills/skill-subagent-driven-development/SKILL.md
  - repo_config/starter-kit-manifest.json
related_features:
  - managed-harness
  - plan-coordination
---

# Plan-Linked Harness Coordination Plan

## Goal

Deliver one Git-tracked plan manifest contract that binds coordinated managed
work to immutable packet evidence, derives multi-session task state from runs,
and keeps controller activation serialized without creating a scheduler, lock,
or second state store.

## Implementation Outcomes

### Shared Coordination Contract

One reusable parser/normalizer validates plan frontmatter, Git tracking,
canonical task IDs, dependencies, topology, safe write paths, and normalized
manifest digest. Planning validator and harness core consume same result.

### Plan-Bound Managed Execution

Manifest-enabled managed requests derive topology, base reference, and planned
write paths from one plan task. Immutable packet stores `plan_ref`,
`plan_task_id`, and normalized `plan_digest`; existing `base_commit` remains
sole resolved code-base identity.

### Derived Handoff And Admission

Run records retain controller handoff and expose one derived task status per
plan task. One controller admits only one active task per active plan/target
branch; packet-internal parallelism remains existing isolated-lane behavior.

### Guided Starter Surface

Planning template, routing instructions, procedure, and relevant skills guide
manifest-enabled work without imposing fields on ordinary plans. Generated
adapter and starter-kit outputs derive from canonical sources.

## Execution Approach

- Mode: `inline sequential`
- Required skills: `skill-writing-plans`, `skill-code-standards`,
  `skill-test-driven-development`, `skill-backend-verification`,
  `skill-verification-before-completion`
- Isolation: current workspace; all implementation tasks share harness core and
  plan validator ownership, so parallel writers are unsafe.
- Commit policy: no commits during execution without separate authorization.
- Parallel ownership: none.
- Sequential fallback: Task 1 defines shared parser; Tasks 2 and 3 consume it;
  Task 4 updates derived guidance and starter output after canonical behavior
  passes.

## Task Breakdown

### Task 1: Add Shared Plan Coordination Parser

**Purpose:**
- Create one canonical read-only coordination-manifest parser and validator for
  both planning lifecycle validation and harness packet resolution.

**Specification Coverage:**
- Plan-owned coordination manifest.
- Git-tracked plan requirement.
- Normalized coordination digest.
- Canonical topology, task identity, dependency, and write-path contract.

**Required Skills:**
- `skill-code-standards`
- `skill-test-driven-development`
- `skill-backend-verification`

**Files And Symbols:**
- Modify: `repo_config/planning_artifact_schema.yaml` plan optional-field
  metadata for `coordination`.
- Create: `scripts/plan_coordination.py` with `PlanCoordination`,
  `load_plan_coordination`, `normalize_coordination`, `coordination_digest`,
  and task/dependency validation helpers.
- Modify: `scripts/validate_planning_lifecycle.py:validate_artifact` to call
  shared coordination validation for manifest-enabled plans.
- Create: `tests/test_plan_coordination.py` shared parser, tracked-plan,
  normalization, digest, task-ID, dependency, mode, and path tests.
- Modify: `tests/test_validate_planning_lifecycle.py` manifest validation
  integration tests.

**Dependencies:**
- Approved parent specification.
- Preserve `scripts/planning_artifact_schema.py` as owner of generic artifact
  metadata; do not move coordination semantics into template-only checks.

**Steps:**
- [ ] Add `coordination` as optional plan frontmatter metadata without making it
  mandatory for legacy plans.
- [ ] Implement one parser that reads YAML frontmatter from repository-relative
  plan path, verifies `git ls-files` tracking, rejects unknown fields, and
  returns immutable normalized data. Structural validation must allow both
  `proposed` and `active` plans; managed task resolution alone requires
  `active` status before dispatch.
- [ ] Validate required manifest shape: `target_branch`, `base_ref`, non-empty
  task list, unique ASCII-slug IDs, existing acyclic dependencies, canonical
  topology names from harness policy, and safe non-empty planned write paths.
- [ ] Verify every manifest task ID appears exactly once as a prose task
  `Coordination ID`; reject missing, duplicate, or unknown prose references.
- [ ] Compute SHA-256 only from deterministic normalized `coordination` data;
  never hash mutable prose, run evidence, or packet state.
- [ ] Reuse parser from planning lifecycle validator; add direct fixture tests
  for valid proposed and active manifests plus every rejected structural case.

**Verification:**
- [ ] `python -m pytest tests/test_plan_coordination.py tests/test_validate_planning_lifecycle.py -q`
- [ ] `python scripts/validate_planning_lifecycle.py`
- Expected: valid Git-tracked proposed or active manifest passes; untracked,
  malformed, cyclic, unsafe, unknown, unmapped, duplicate-mapped, and legacy
  topology manifests fail with stable errors; manifest-free plans still pass.

**Exit Criteria:**
- One shared component owns manifest parsing, validation, normalization, and
  digest for every later consumer.

### Task 2: Bind Manifest Tasks To Managed Packets

**Purpose:**
- Make manifest-enabled managed execution resolve one plan task into one
  immutable packet without duplicating route, base, or path facts.

**Specification Coverage:**
- Immutable plan-to-packet binding.
- Existing packet `base_commit` as code-base SSOT.
- Backward compatibility for uncoordinated requests.
- Successor-only recovery after manifest or base change.

**Required Skills:**
- `skill-code-standards`
- `skill-test-driven-development`
- `skill-backend-verification`

**Files And Symbols:**
- Modify: `scripts/harness_task.py:_normalize_managed_request`,
  `resolve_managed_packet`, `_successor_request`, `run_managed`, and
  `apply_controller_decision`.
- Modify: `tests/test_harness_task.py` coordinated packet, legacy request,
  manifest/base mismatch, and successor immutability coverage.
- Verify: `scripts/plan_coordination.py` Task 1 public contract.

**Dependencies:**
- Task 1 complete.

**Steps:**
- [ ] Accept `plan_ref` and `plan_task_id` only as a pair. Resolve their shared
  manifest before route packet creation.
- [ ] For coordinated requests, derive `execution_mode` and
  `planned_write_paths` from manifest task, and `base_ref` from its containing
  plan manifest. Reject caller-supplied conflicting values; retain normal
  request behavior when plan fields are absent.
- [ ] Store repository-relative `plan_ref`, stable task ID, and normalized
  digest in immutable packet. Keep existing `base_commit` as sole resolved
  commit field; do not add `plan_base_commit`.
- [ ] Permit continuation only when packet plan fields, digest, and existing
  base commit still match current manifest. Require controller successor
  attempt after mismatch; never mutate prior packet.
- [ ] Extend successor request allowlist only for plan reference/task identity
  fields. Re-resolve current manifest for successor instead of copying mutable
  manifest data into request or run state.

**Verification:**
- [ ] `python -m pytest tests/test_harness_task.py tests/test_plan_coordination.py -q`
- [ ] Direct test: coordinated request packet derives canonical mode, base ref,
  paths, and digest from manifest.
- [ ] Direct test: one missing plan field, untracked plan, changed digest, base
  mismatch, and conflicting request field block before adapter dispatch.
- [ ] Direct test: legacy version-2/version-3 requests without plan fields keep
  current packet shape and behavior.
- Expected: packet is sole immutable binding; legacy routes remain compatible.

**Exit Criteria:**
- Every coordinated packet has one valid plan task binding and no duplicated
  code-base or write-ownership fact.

### Task 3: Derive Task Status, Record Handoff, And Serialize Admission

**Purpose:**
- Let fresh controller sessions recover coordination from plan-bound run records
  while admitting one active plan task at a time.

**Specification Coverage:**
- Session-safe handoff and recovery.
- Derived `ready`, `active`, `blocked`, and `done` task states.
- Serialized controller activation.
- Symmetric single, sequential, and parallel topology coordination.

**Required Skills:**
- `skill-code-standards`
- `skill-test-driven-development`
- `skill-backend-verification`

**Files And Symbols:**
- Modify: `scripts/harness_task.py` with `coordination_status`,
  `record_controller_handoff`, coordinated-run discovery, and pre-dispatch
  admission helpers.
- Modify: `scripts/harness_task.py:main` with read-only
  `coordination-status --plan <repo-relative-path>` and run-scoped
  `handoff --run-id <id> --handoff <json>` commands.
- Modify: `tests/test_harness_task.py` derived-state, handoff, duplicate-active,
  dependency, terminal-state, and canonical-topology parameterized tests.
- Verify: `docs/operating_system/procedures/managed-execution-adapter-contract.md`
  in Task 4 documents public lifecycle behavior.

**Dependencies:**
- Task 1 complete.
- Task 2 complete.

**Steps:**
- [ ] Scan run records by immutable packet `plan_ref` and `plan_task_id`; derive
  task state without writing task state, run IDs, or handoff into plan file.
- [ ] Add one run-owned handoff object with required non-empty
  `last_verified_fact`, `next_action`, `blocker_or_decision`, and timestamp.
  Allow controller only; reject uncoordinated or terminal-run handoff writes.
- [ ] Before creating coordinated run, require all manifest dependencies to be
  derived `done`, reject multiple current runs for task, and reject activation
  while another task from same plan/target branch is active.
- [ ] Reuse existing route/capability intersection, lane normalization,
  final-workspace checks, fresh validator lane, friction recording, and
  controller decision lifecycle for every topology. Do not add topology branch
  to task status or handoff logic.
- [ ] Expose read-only status output for controller selection. Keep simultaneous
  controller activation unsupported; do not add lock, lease, heartbeat, queue,
  or background recovery.

**Verification:**
- [ ] `python -m pytest tests/test_harness_task.py -q`
- [ ] Direct test: no run plus completed dependencies is `ready`; one planned
  or executing run is `active`; blocked/unvalidated is `blocked`; accepted is
  `done`.
- [ ] Direct test: new controller continues matching planned packet, records
  handoff in run, and creates successor after manifest/base change.
- [ ] Direct test: unmet dependency, duplicate current run, and another active
  task block before host workspace preparation or lane dispatch.
- [ ] Direct test: same packet/run-state contract applies to canonical single,
  sequential, and parallel modes.
- Expected: session handoff and admission derive from run truth; no second
  registry or false cross-controller guarantee exists.

**Exit Criteria:**
- Fresh controller can select one admissible plan task from plan plus runs and
  recover only through recorded packet/run evidence.

### Task 4: Update Planning Guidance And Distributed Starter Surface

**Purpose:**
- Make agents author and execute coordinated plans consistently, while keeping
  optional manifest use and generated outputs aligned.

**Specification Coverage:**
- Manifest-enabled planning process.
- Serialized controller scope and no simultaneous-controller claim.
- Canonical topology names and packet/run ownership.
- Starter-kit compatibility and generated-surface integrity.

**Required Skills:**
- `skill-code-standards`
- `skill-backend-verification`

**Files And Symbols:**
- Modify: `docs/operating_system/templates/implementation-plan-template.md`
  with optional coordination-manifest schema, task `Coordination ID` reference,
  and canonical mode names.
- Modify: `docs/operating_system/planning/planning-dispatch.md` coordinated
  multi-session trigger and source-first fallback.
- Modify: `docs/operating_system/procedures/managed-execution-adapter-contract.md`
  plan-packet binding, run-owned handoff, and serialized admission contract.
- Modify: `docs/operating_system/templates/agents/root-AGENTS.template.md`
  plan-linked managed-routing guidance.
- Modify: `.agents/skills/skill-writing-plans/SKILL.md`,
  `.agents/skills/skill-executing-plans/SKILL.md`, and
  `.agents/skills/skill-subagent-driven-development/SKILL.md` with exact
  manifest selection, handoff, and controller boundaries.
- Modify: `repo_config/starter-kit-manifest.json` to include
  `scripts/plan_coordination.py` and `tests/test_plan_coordination.py`.
- Generated: `AGENTS.md` and `generated_agents/**` through
  `scripts/sync_agent_adapters.py`.
- Modify: `tests/test_starter_kit_generation.py` required copied coordination
  parser/test coverage.
- Modify: `tests/test_sync_agent_adapters.py` only if canonical skill/template
  mapping behavior requires regression coverage.

**Dependencies:**
- Tasks 1 through 3 complete.

**Steps:**
- [ ] Add optional manifest example and `Coordination ID` task reference to plan
  template. Preserve ordinary plan template flow without manifest.
- [ ] Replace legacy execution guidance names with `single_work_lane`,
  `sequential_work_lanes`, and `parallel_work_lanes`; label source-first work
  separately from managed topologies.
- [ ] State one ownership rule everywhere: plan manifest owns static
  coordination, packet owns immutable binding, `run.json` owns state/handoff/
  evidence, and controller serializes activation.
- [ ] Document that simultaneous controllers are unavailable, manifest changes
  require successor attempt, and host thread resume is never inferred.
- [ ] Synchronize canonical agent surfaces, add starter manifest paths, then
  update only affected generated/starter regression tests.

**Verification:**
- [ ] `python scripts/sync_agent_adapters.py --all-platforms`
- [ ] `python scripts/sync_agent_adapters.py --all-platforms --check`
- [ ] `python -m pytest tests/test_sync_agent_adapters.py tests/test_starter_kit_generation.py -q`
- [ ] `python scripts/build_starter_kit.py`
- [ ] `python scripts/validate_starter_kit.py`
- Expected: canonical guidance is synchronized; kit ships shared parser and
  tests, while `.harness` state and private host runtime remain excluded.

**Exit Criteria:**
- Every agent surface receives one truthful coordination rule derived from
  canonical template, skills, contract, and starter manifest.

## Verification

- `python -m pytest tests/test_plan_coordination.py tests/test_validate_planning_lifecycle.py tests/test_harness_task.py tests/test_sync_agent_adapters.py tests/test_starter_kit_generation.py -q`
- `python scripts/validate_planning_lifecycle.py`
- `python scripts/validate_template_required_sections.py`
- `python scripts/validate_harness_config.py --repo-root .`
- `python scripts/validate_repo_contracts.py`
- `python scripts/validate_agent_runtime_drift.py --skip-deploy-check`
- `python scripts/sync_agent_adapters.py --all-platforms --check`
- `python scripts/build_starter_kit.py`
- `python scripts/validate_starter_kit.py`
- `git diff --check`

## Completion Criteria

The plan is ready for completion verification when:

1. one shared parser validates and normalizes every manifest-enabled plan
2. coordinated packets bind exactly one tracked plan task and normalized digest
   while existing `base_commit` remains sole code-base identity
3. plan task state and handoff derive from run records without mutable plan
   state or second registry
4. controller admits one active task per active plan/target branch; parallelism
   remains packet-internal and topology symmetric
5. legacy manifest-free plans and managed requests retain current behavior
6. canonical guidance, generated adapters, and starter kit are synchronized
7. every final verification command passes from fresh evidence

The plan may be marked `completed` only when
`skill-verification-before-completion` returns `verified` from fresh evidence.
