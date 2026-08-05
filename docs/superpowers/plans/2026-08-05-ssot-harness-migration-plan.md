---
layer: change
artifact_type: plan
status: completed
template_id: implementation-plan
name: ssot-harness-migration
parent_spec: none
targets:
  - agents
  - repo_config
  - scripts
  - tests
  - docs/operating_system
  - .agents/skills
  - .gitignore
---

# SSOT Harness Migration Plan

## Goal

Add one repository-owned, symmetry-driven harness policy that resolves task
routing, agent roles, rules, skills, tool allowances, workspace policy, state
transitions, approval gates, and verification checks. Keep existing
`low`/`normal`/`high` TOML templates as model-capability sources. Keep rules
and skills in their current canonical owners. Deliver a small CLI interpreter
and deterministic verification without adding a mandatory daemon, scheduler,
or job manager. Ordinary tasks report reusable friction without changing the
harness; explicit improvement tasks investigate recurring evidence and retain
only independently proven interventions.

## Implementation Outcomes

### One Canonical Harness Policy

`repo_config/harness.yaml` becomes sole source for route selection,
state-transition policy, check definitions, approval gates, and references to
agent templates, roles, rules, and skills. Code reads this file; human routing
documentation is generated from it. No parallel `routes.yaml`, `gates.yaml`,
`tool-policy.yaml`, or duplicated prose matrix remains authoritative.

### Agent Templates And Roles Have Separate Ownership

`agents/low.toml`, `agents/normal.toml`, and `agents/high.toml` retain model,
provider, and capability-tier ownership. `agents/roles.yaml` defines recurring
roles through one uniform schema: write permission, compatible capability
tiers, required result fields, and supported result kinds. A route selects one
template plus one role; neither file repeats rules or skill procedures.
`harness_task.py` consumes and validates the registry, and controller dispatch
uses the normalized template name as the supported agent type. Runtime adapter
deployment does not copy these project-scoped templates to user-home targets.

### Controller-Compatible Resolution And Verification

`scripts/harness_task.py` resolves explicit controller task metadata into one
normalized task packet. Same resolver drives preflight and verification.
Verification checks task scope, approval-gated changes, declared state
transitions, and named commands defined in canonical policy. It writes
`verified` only from fresh harness evidence; agents return only claimed result.

### Durable Evidence Without Mandatory Control-Plane Records

Bounded work runs from current repository truth and does not require committed
task files. CLI can write a local, ignored run directory for parallel,
long-running, interruptible, or explicitly recoverable work. Durable specs and
plans remain Git-tracked only when project work needs coordination or recovery.

### Friction Reporting And Harness Improvement Stay Separate

Ordinary task outcomes can report reusable capability, environment, authority,
context, or proof friction. They use a valid fallback or return `blocked` when
required proof cannot be produced. They do not install tools, alter policy,
add telemetry, create a database, or repeatedly retry unchanged failures.
Harness changes require an explicit improvement task with representative-job
baseline, earliest-gap analysis, correct-owner decision, smallest intervention,
native validation, fresh-agent rerun, and keep/revise/remove outcome.

### Search And Transformation Tools Have One Route Each

Semble is an optional user-level, read-only MCP for broad local semantic search
when concept location is unknown. `rg` remains exact-text confirmation, Serena
remains exact-symbol authority, and GitNexus remains broad flow and impact
authority. `ast-grep` is an optional local CLI for structural match and preview;
it never writes source in this repository because `apply_patch` remains the only
edit path. ast-grep MCP remains deferred until complex AST-rule authoring shows
repeated, measured friction.

### Generated And Starter Surfaces Stay Aligned

Generated human routing output, root agent instructions, runtime adapters,
starter-kit manifest, validators, and tests agree with canonical templates,
roles, policy, rules, and skills. Starter kit contains necessary first-layer
harness inputs but not local run state or runtime scheduler.

## Execution Approach

- Mode: `inline sequential`
- Required skills: `skill-code-standards`, `skill-test-driven-development`, `skill-writing-skills`, `skill-verification-before-completion`
- Isolation: current workspace; preserve existing untracked `agents/` templates
- Commit policy: no commits during execution
- Parallel ownership: none; policy, interpreter, validators, generated docs, adapters, and starter manifest share references
- Sequential fallback: execute Task 0, then Tasks 1-9 in order; run focused Python tests after each code task, then final repository-contract validation after generated-surface work

## Task Breakdown

### Task 0: Add Improvement Skill Foundation

**Purpose:**
- Make `harness_improvement` route reference an existing canonical skill before
  policy validation begins.

**Files And Symbols:**
- Add: `.agents/skills/skill-improve-harness/SKILL.md`

**Steps:**
- [ ] Define friction evidence, earliest-gap, correct-owner, smallest-change,
  native-proof, fresh-rerun, and keep/revise/remove procedure.
- [ ] Keep improvement artifacts and planning-dispatch documentation in Task 5.

**Verification:**
- [ ] `python scripts/validate_agent_metadata_schema.py`

**Exit Criteria:**
- Harness policy can reference `skill-improve-harness` without a forward
  reference.

### Task 1: Define Canonical Agent Roles And Harness Policy

**Purpose:**
- Establish one uniform role registry and one routing policy without duplicating
  existing rule or skill content.

**Specification Coverage:**
- Template capability tier, role behavior, route selection, tool allowance,
  workspace policy, state transitions, approval gates, and check identifiers
  have one canonical source per fact.
- Rules remain in `docs/operating_system/rules/`; skills remain in
  `.agents/skills/`.

**Required Skills:**
- `skill-code-standards`

**Files And Symbols:**
- Inspect: `agents/low.toml`, `agents/normal.toml`, `agents/high.toml`
- Add: `agents/roles.yaml`
- Add: `repo_config/harness.yaml`
- Modify: `repo_config/starter-kit-manifest.json`
- Verify: `scripts/build_starter_kit.py:load_manifest`

**Dependencies:**
- Existing untracked `agents/` templates are deliberate user work and must be
  preserved.
- `PyYAML` is already pinned in `requirements.txt`.

**Steps:**
- [ ] Define each role with same required fields: `writes`, `accepts`,
  `result_kind`, and `required_fields`.
- [ ] Define `harness.yaml` with one versioned schema containing defaults,
  check definitions, approval gates, state graph, and route definitions.
- [ ] Reference templates by names matching `agents/<name>.toml`; reference
  rule and skill IDs without copying their bodies.
- [ ] Include only runtime-neutral initial routes: local implementation,
  debugging, research, plan review, and harness improvement. Adopted projects
  add backend, frontend, or product routes with real project checks to this
  same policy file.
- [ ] Define controller dispatch contract: normalized template must equal one
  supported agent type, and no route may select an unregistered template.
- [ ] Add `agents/` and harness policy to starter-kit copy and required paths;
  leave local `.harness/` state out of starter kit.

**Verification:**
- [ ] Inspect each role and route for all required schema fields.
- Expected: every route resolves exactly one template, one role, named rules,
  named skills, workspace policy, and checks.

**Exit Criteria:**
- One canonical role file and one canonical policy file express all initial
  selection differences as data.

### Task 2: Add Harness Configuration Validation

**Purpose:**
- Reject stale or contradictory harness references before controller or agent
  execution.

**Specification Coverage:**
- Canonical policy is executable only when every referenced template, role,
  rule, skill, state, check, and route is valid.
- Validation logic must not create a second embedded policy registry.

**Required Skills:**
- `skill-test-driven-development`
- `skill-code-standards`

**Files And Symbols:**
- Add: `scripts/validate_harness_config.py`
- Add: `tests/test_validate_harness_config.py`
- Modify: `scripts/validate_repo_contracts.py:IN_PROCESS_SCRIPT_NAMES`
- Modify: `scripts/validate_repo_contracts.py:build_subprocess_steps`
- Modify: `tests/test_validate_repo_contracts.py`

**Dependencies:**
- Task 1 canonical files exist.
- Existing validation pattern in `scripts/validate_repo_config.py` and its
  tests remains source for parser and diagnostic style.

**Steps:**
- [ ] Write failing focused tests for valid policy, missing template, missing
  role, unknown rule, unknown skill, unknown check, invalid state transition,
  and invalid role/template pairing.
- [ ] Implement validator from YAML and filesystem discovery only; do not
  duplicate allowed IDs in Python constants.
- [ ] Require check commands to be non-empty argument lists and route check
  references to exist.
- [ ] Register harness validation in canonical repository contract command.
- [ ] Preserve existing contract-validator subprocess and fast-mode behavior.
- [ ] Give new validator script repository metadata and add its starter-kit
  manifest/test entries in same change.

**Verification:**
- [ ] `python -m pytest tests/test_validate_harness_config.py -q`
- Expected: valid repository policy passes; each bad fixture reports exact
  broken canonical reference.
- [ ] `python -m pytest tests/test_validate_repo_contracts.py -q`
- Expected: harness validation participates in repository contract coverage.

**Exit Criteria:**
- Repository contracts fail before execution when harness configuration drifts.

### Task 3: Implement Shared Task Resolution

**Purpose:**
- Turn explicit controller task metadata into one small, deterministic task
  packet for agent dispatch and later verification.

**Specification Coverage:**
- Controller supplies task type, acceptance criteria, allowed paths, base ref,
  and requested persistence mode; harness does not infer risk from keywords.
- One resolver supplies both preflight and verification to prevent divergent
  route decisions.

**Required Skills:**
- `skill-test-driven-development`
- `skill-code-standards`

**Files And Symbols:**
- Add: `scripts/harness_task.py`
- Add: `tests/test_harness_task.py`
- Verify: `repo_config/harness.yaml`

**Dependencies:**
- Task 2 validator and canonical config pass.

**Steps:**
- [ ] Define versioned JSON task input with task type, acceptance criteria,
  allowed paths, base ref, optional run-directory request, and documented
  invalid-input exit behavior.
- [ ] Define normalized packet with template, role, rules, skills, tools,
  workspace policy, checks, approval gates, and allowed next states.
- [ ] Implement one pure `resolve_task(...)` path used by CLI subcommands.
- [ ] Add `preflight` command that validates policy and task input, prints only
  normalized JSON, and performs no source mutation.
- [ ] Reject unknown task types, empty acceptance criteria, unsafe relative
  paths, and unresolved policy references.
- [ ] Give new interpreter script repository metadata and add its starter-kit
  manifest/test entries in same change.

**Verification:**
- [ ] `python -m pytest tests/test_harness_task.py -q`
- Expected: representative routes resolve predictably; malformed inputs fail
  without writing artifacts.

**Exit Criteria:**
- Controller can dispatch `low`, `normal`, or `high` with a small packet rather
  than loading unrelated skills and procedures.

### Task 4: Add Evidence-First Verification And Optional Run State

**Purpose:**
- Independently verify task claims through current diff and fresh commands while
  preserving bounded-work simplicity.

**Specification Coverage:**
- Agent completion claims are not verification.
- Same route resolution drives verification.
- Local persistent state is optional and is never policy source or committed
  project memory.
- Ordinary task evidence reports reusable friction but does not trigger harness
  configuration or procedure mutation.

**Required Skills:**
- `skill-test-driven-development`
- `skill-code-standards`
- `skill-verification-before-completion`

**Files And Symbols:**
- Modify: `scripts/harness_task.py`
- Modify: `tests/test_harness_task.py`
- Modify: `.gitignore`
- Verify: `docs/operating_system/rules/command-execution-rule.md`

**Dependencies:**
- Task 3 task packet and resolver exist.

**Steps:**
- [ ] Add common claimed-result input schema; reserve `verified` result kind
  for harness output only.
- [ ] Add `verify` command that resolves task again, compares changed paths
  against allowed paths, detects configured approval-trigger files, validates
  proposed state transition, and executes named configured checks.
- [ ] Capture command, exit code, stdout/stderr paths or inline summary, diff
  result, failed gates, and acceptance-criterion mapping in evidence output.
- [ ] Emit normalized blocker entries for reusable friction; permit a valid
  fallback only when it proves the same acceptance claim.
- [ ] Write run artifacts only when caller passes explicit local run path;
  otherwise emit JSON to stdout and leave no control-plane record.
- [ ] Ignore `.harness/` without adding it to starter-kit copy or public export.
- [ ] Cap automatic retry ownership at returning `observed`; controller decides
  reroute, retry, escalation, or approval.
- [ ] Do not add friction aggregation, a database, telemetry, or automatic
  harness edits in this migration.

**Verification:**
- [ ] `python -m pytest tests/test_harness_task.py -q`
- Expected: scope escape, approval trigger, failed command, and invalid
  transition fail verification; passing fixture alone can produce `verified`.
- [ ] `git check-ignore .harness/example/run.json`
- Expected: local run state is ignored.

**Exit Criteria:**
- Harness has direct evidence for its `verified` claim and does not trust agent
  result text as proof.

### Task 5: Add Explicit Harness Improvement Method

**Purpose:**
- Make recurring friction investigation an explicit, bounded experiment rather
  than an ad hoc reaction during ordinary project work.

**Specification Coverage:**
- Reusable friction is reported during normal work; harness mutation requires
  explicit improvement scope.
- Each improvement identifies earliest gap and correct owner, then keeps a
  change only after native proof and fresh-agent rerun show useful outcome.

**Required Skills:**
- `skill-writing-skills`
- `skill-code-standards`

**Files And Symbols:**
- Add: `.agents/skills/skill-improve-harness/SKILL.md`
- Add: `docs/operating_system/templates/harness-improvement-template.md`
- Modify: `docs/operating_system/planning/planning-dispatch.md`
- Modify: `docs/operating_system/README.md`
- Modify: `tests/test_validate_template_required_sections.py`
- Modify: `tests/test_validate_agent_metadata_schema.py`

**Dependencies:**
- Task 4 defines ordinary task evidence and blocked outcomes.
- Existing rules, skills, tests, and runtime evidence remain authoritative over
  improvement narratives.

**Steps:**
- [ ] Define explicit trigger: user or authorized controller requests harness
  improvement after reusable friction warrants investigation.
- [ ] Define template sections: representative job, baseline, earliest gap,
  correct owner, smallest authorized intervention, native validation,
  fresh-agent rerun, decision, and bounded result.
- [ ] Require owner selection from harness, consumer repository, agent runtime,
  CI/environment, external service, or human decision before proposing edits.
- [ ] Require fresh-agent rerun from equivalent starting state and compare
  retries, human intervention, proof quality, and residual maintenance cost.
- [ ] Permit only `keep`, `revise`, `remove`, or `pending fresh rerun`; merged
  implementation alone must not count as confirmed improvement.
- [ ] State non-goals: no automatic policy modification, no automatic tool
  installation, no default database, and no mandatory telemetry collection.

**Verification:**
- [ ] `python -m pytest tests/test_validate_template_required_sections.py tests/test_validate_agent_metadata_schema.py -q`
- Expected: improvement skill metadata and template structure validate.
- [ ] Inspect planning dispatch and operating-system index.
- Expected: ordinary work stays bounded; explicit improvement task has one
  discoverable owner and method.

**Exit Criteria:**
- Repeated friction can improve harness deliberately without making every
  ordinary task a telemetry or control-plane operation.

### Task 6: Align Skill Selection And Generated Human Guidance

**Purpose:**
- Make harness-resolved routing authoritative when present while retaining
  source-first skill discovery when no task packet exists.

**Specification Coverage:**
- Rules define invariants, skills define methods, harness decides selection.
- Generated human routing output derives from policy; no competing generic
  matrix remains canonical.

**Required Skills:**
- `skill-writing-skills`
- `skill-code-standards`

**Files And Symbols:**
- Modify: `.agents/skills/skill-using-superpowers/SKILL.md`
- Add: `scripts/render_harness_routing.py`
- Add: `docs/operating_system/tooling/harness-routing.generated.md`
- Modify: `docs/operating_system/tooling/frontend-backend-integration-tools.md`
- Modify: `docs/operating_system/templates/agents/root-AGENTS.template.md`
- Modify: `tests/test_sync_agent_adapters.py`
- Add: `tests/test_render_harness_routing.py`

**Dependencies:**
- Tasks 1-2 policy and validation are complete.

**Steps:**
- [ ] Update `skill-using-superpowers` so validated task packet selects exact
  skills; extra skills require user request or controller escalation/rerouting.
- [ ] Preserve current skill-discovery behavior when no harness packet exists.
- [ ] Render one generated human route table from `harness.yaml`; mark it
  generated and do not hand-edit it.
- [ ] Add renderer `--check` mode that compares committed output with canonical
  policy, register it in `validate_repo_contracts.py`, and test stale output
  fails repository-contract validation.
- [ ] Replace broad lifecycle rows in frontend/backend guide with link to
  generated general routing; retain only unique cross-boundary method details.
- [ ] Add concise root instruction: controller packet is authoritative, rules
  remain mandatory, and agents return claimed results.
- [ ] Regenerate agent adapters after canonical skill and template edits.
- [ ] Give new renderer script repository metadata and add its starter-kit
  manifest/test entries in same change.

**Verification:**
- [ ] `python -m pytest tests/test_render_harness_routing.py tests/test_sync_agent_adapters.py -q`
- Expected: table is reproducible from policy and runtime adapters include
  current skill/root-instruction content.
- [ ] `python scripts/sync_agent_adapters.py --check`
- Expected: no generated adapter drift.

**Exit Criteria:**
- One policy controls task routing; skills remain focused procedures and runtime
  prompts do not force every possible skill into context.

### Task 7: Add Semble And ast-grep Tool Routing

**Purpose:**
- Add one optional local semantic-search MCP and one optional structural-preview
  CLI without duplicating current code-intelligence or source-editing owners.

**Specification Coverage:**
- Semble handles broad local concept search only when exact location is unknown.
- ast-grep previews repeated syntactic matches; `apply_patch` remains sole write
  mechanism.
- Neither tool becomes a required project dependency, CI prerequisite,
  repository MCP configuration, or default agent context.

**Required Skills:**
- `skill-code-standards`

**Files And Symbols:**
- Modify: `repo_config/harness.yaml`
- Modify: `docs/operating_system/tooling/code-intelligence-tools.md`
- Add: `docs/operating_system/procedures/code-intelligence-tools-setup.md`
- Modify: `docs/operating_system/rules/command-execution-rule.md`
- Modify: `docs/operating_system/README.md`
- Modify: `tests/test_validate_harness_config.py`
- Modify: `tests/test_sync_agent_adapters.py`

**Dependencies:**
- Tasks 1-2 establish canonical policy and reference validation.
- Task 6 establishes packet-based selection and generated adapter refresh.

**Steps:**
- [ ] Add optional, read-only `semble_codebase_search` capability with fallback
  to native search, Serena, or GitNexus when unavailable; no route may require
  Semble to claim completion.
- [ ] Add optional `ast_grep_preview` capability for structural discovery and
  JSON/preview output only; prohibit direct ast-grep rewrite in policy and docs.
- [ ] Define one routing table: Semble for broad unknown local concepts,
  `rg` for exact text, Serena for symbols, GitNexus for flows/impact, and
  ast-grep for repeated syntax patterns.
- [ ] Add user-level setup/removal procedure with no committed API key, no
  repository `.codex` configuration, no `semble init`, and capability smoke
  checks after client restart. Verify Semble does not create repository-local
  state; otherwise document ignored/private cache ownership and removal.
- [ ] Add `sg` read-only preview commands to command-execution guidance; retain
  `apply_patch` as only source mutation command.
- [ ] Explain ast-grep MCP is deferred and may be evaluated only through an
  explicit harness-improvement task for complex AST-rule authoring.
- [ ] Regenerate adapters after canonical command-rule change.

**Verification:**
- [ ] `python -m pytest tests/test_validate_harness_config.py tests/test_sync_agent_adapters.py -q`
- Expected: optional tool capabilities resolve with fallbacks and generated
  rule/runtime surfaces remain aligned.
- [ ] `sg --version` and one read-only structural-preview command against a
  disposable fixture.
- Expected: ast-grep reports matches without modifying source.
- [ ] Configure Semble only in user-level client settings; restart client and
  execute one broad local semantic-search query.
- Expected: Semble returns local search results or remains unavailable without
  blocking native/Serena/GitNexus fallback.

**Exit Criteria:**
- Semble and ast-grep improve discovery when installed, remain optional when
  absent, and do not create a second source-editing or code-intelligence owner.

### Task 8: Package And Test Starter-Harness Distribution

**Purpose:**
- Ensure adopted projects receive first-layer harness inputs, validators, and
  tests without factory-only runtime deployment or local execution state.

**Specification Coverage:**
- Starter kit has canonical templates, role registry, policy, interpreter,
  validation, and generated guidance.
- Optional second-layer job manager is explicitly excluded.

**Required Skills:**
- `skill-test-driven-development`
- `skill-code-standards`

**Files And Symbols:**
- Modify: `repo_config/starter-kit-manifest.json`
- Modify: `scripts/build_starter_kit.py` only if manifest behavior exposes a
  concrete package gap
- Modify: `scripts/validate_starter_kit.py` only if manifest behavior exposes
  a concrete validation gap
- Modify: `tests/test_starter_kit_generation.py`
- Modify: `README.md`
- Verify: `scripts/validate_repo_contracts.py`

**Dependencies:**
- Tasks 1-7 are complete and generated surfaces are fresh.

**Steps:**
- [ ] Include `agents/`, `agents/roles.yaml`, `repo_config/harness.yaml`,
  harness scripts, focused tests, and generated routing guidance in manifest.
- [ ] Keep `.harness/`, runtime deployment scripts, user-home configuration,
  and future scheduler outside starter distribution.
- [ ] Add test coverage that starter kit includes canonical harness sources and
  excludes local run state.
- [ ] Update README ownership list and bootstrap guidance with first-layer
  harness entry points and optional-orchestrator boundary.

**Verification:**
- [ ] `python -m pytest tests/test_starter_kit_generation.py -q`
- Expected: starter build includes harness sources and excludes runtime state.
- [ ] `python scripts/build_starter_kit.py`
- Expected: starter kit builds from manifest without missing harness files.
- [ ] `python scripts/validate_starter_kit.py`
- Expected: generated kit validates required and forbidden paths.

**Exit Criteria:**
- New project bootstrap receives one usable first-layer harness with no hidden
  factory dependencies.

### Task 9: Run Final Contract And Regression Verification

**Purpose:**
- Prove canonical policy, generated surfaces, starter packaging, and existing
  safeguards agree before closure.

**Specification Coverage:**
- No completed migration claim without fresh focused and broad evidence.

**Required Skills:**
- `skill-verification-before-completion`

**Files And Symbols:**
- Verify: `scripts/validate_repo_contracts.py`
- Verify: `scripts/validate_agent_runtime_drift.py`
- Verify: `scripts/build_starter_kit.py`
- Verify: `scripts/validate_starter_kit.py`
- Verify: `git diff --check`

**Dependencies:**
- Tasks 1-8 complete.

**Steps:**
- [ ] Inspect final diff for changes outside templates, policy, interpreter,
  validators, tests, generated docs/adapters, packaging, and documentation.
- [ ] Run focused harness tests before broad repository checks.
- [ ] Run canonical repository contract validation and agent runtime drift check.
- [ ] Run optional Semble and ast-grep smoke checks only when configured in the
  current user environment; record unavailable tools as optional, not failed
  repository proof.
- [ ] Rebuild and validate starter kit.
- [ ] Record failed, skipped, environmental, or deferred checks; do not mark
  plan complete from checkboxes alone.

**Verification:**
- [ ] `python -m pytest tests/test_validate_harness_config.py tests/test_harness_task.py tests/test_render_harness_routing.py tests/test_sync_agent_adapters.py -q`
- Expected: harness-specific behavior passes.
- [ ] `python scripts/validate_repo_contracts.py`
- Expected: repository contract validation passes.
- [ ] `python scripts/validate_agent_runtime_drift.py --skip-deploy-check`
- Expected: canonical and generated runtime artifacts have no drift.
- [ ] `git diff --check`
- Expected: no whitespace errors.

**Exit Criteria:**
- `skill-verification-before-completion` can return `verified` with fresh
  evidence, or reports exact incomplete/blocked condition.

## Verification

- `python -m pytest tests/test_validate_harness_config.py tests/test_harness_task.py tests/test_render_harness_routing.py tests/test_sync_agent_adapters.py tests/test_validate_template_required_sections.py tests/test_starter_kit_generation.py -q`
- `python scripts/validate_repo_contracts.py`
- `python scripts/validate_agent_runtime_drift.py --skip-deploy-check`
- `python scripts/build_starter_kit.py`
- `python scripts/validate_starter_kit.py`
- `git diff --check`

## Completion Criteria

The plan is ready for completion verification when:

1. `agents/*.toml` owns template capability, `agents/roles.yaml` owns role
   behavior, and `repo_config/harness.yaml` owns routing and gates without
   duplicate policy files
2. every policy reference is validated against canonical templates, roles,
   rules, skills, checks, and state transitions
3. preflight and verification use same resolver; only harness evidence can
   return `verified`
4. bounded work needs no task-record files; explicit local run artifacts are
   ignored, noncanonical, and excluded from starter output
5. ordinary work reports reusable friction, uses valid fallback or blocks, and
   cannot mutate harness policy, tools, telemetry, or runtime configuration
6. explicit improvement work has baseline, earliest-gap/owner analysis, native
   proof, fresh-agent rerun, and keep/revise/remove decision
7. Semble remains optional and read-only with source-first fallback; ast-grep
   remains structural preview only and cannot bypass `apply_patch`
8. generated routing guidance and runtime adapters are refreshed from canonical
   inputs
9. starter output contains first-layer harness surfaces and excludes job
   manager, user-home deployment, and local run state
10. focused tests and final commands pass, or blockers are recorded and plan
   status remains non-completed

The plan may be marked `completed` only when
`skill-verification-before-completion`:

1. runs fresh final verification
2. confirms completion criteria against repository evidence
3. finds no unresolved required task, failed required check, stale status, or
   unrecorded scope deviation
4. returns `verified` and updates plan status

## Execution Record

Verified August 5, 2026:

- `python -m pytest tests/test_validate_harness_config.py tests/test_harness_task.py tests/test_render_harness_routing.py tests/test_sync_agent_adapters.py tests/test_validate_template_required_sections.py tests/test_starter_kit_generation.py -q` — 48 passed
- `python scripts/validate_repo_contracts.py` — passed
- `python scripts/validate_agent_runtime_drift.py --skip-deploy-check` — passed
- `python scripts/build_starter_kit.py` and `python scripts/validate_starter_kit.py` — passed
- `git diff --check` — passed
- `sg --json --lang python -p 'raise $EXCEPTION' scripts/harness_task.py` — 17 read-only matches; no source mutation

Semble MCP was not configured in current client. This is expected optional
state; native search, Serena, and GitNexus remain defined fallbacks.

Multi-agent amendment verified August 5, 2026:

- `orchestration` policy validates `single_agent`, `sequential_agents`, and
  isolated `parallel_lanes` before task resolution.
- Active subagent, parallel, review, planning, and routing guidance now use
  packets and claimed results; commit-range review-package coupling is removed.
- Focused regression suite, full repository contracts, runtime drift, starter
  build/validation, and `git diff --check` passed.
