---
layer: operating_system
artifact_type: spec
status: completed
template_id: detailed-specification
name: serena-code-intelligence-and-operating-system-cleanup
parent_workstream: none
targets:
  - AGENTS.md
  - docs/operating_system/templates/agents/root-AGENTS.template.md
  - docs/operating_system/tooling/
  - docs/operating_system/rules/
  - docs/operating_system/prompt_templates/
  - docs/operating_system/governance/
  - docs/operating_system/lifecycle/
  - docs/operating_system/planning/
  - .agents/skills/
  - docs/architecture_templates/
  - docs/generated/
  - scripts/
  - tools/docs/
  - tests/
  - repo_config/
  - .gitignore
related_features: []
related_stages: []
---

# Serena Code Intelligence And Operating-System Cleanup Specification

## Goal

Replace inactive persistent architecture-lineage generation with a thin
code-intelligence model combining GitNexus, Serena, native code tools, tests,
CI, `docs/architecture.md`, and ADRs without a new orchestration layer.

Also simplify repository operating system by removing or merging redundant
rules, skills, workflows, prompt routing, metadata, mandatory reads, activation
hooks, planning layers, validation paths, and closeout gates identified by July
2026 audit review.

Source code, configuration, tests, and validators remain executable truth.
Architecture tools remain derived and disposable. Durable architecture intent
remains human-owned.

## Current-State Evidence

- `repo_config/adoption-mode.yaml` sets `adoption_mode: starter_method_only`,
  `managed_architecture_metadata: false`, and `architecture_generator: none`.
- CI already skips architecture sync for `starter_method_only`.
- `docs/generated/architecture_dag.yaml` has no nodes or edges.
- `docs/generated/capability_lineage.yaml` has no features.
- Architecture generation retains approximately 3,789 lines across generator,
  sync, audit, and dedicated tests, excluding broader validator branches.
- GitNexus is configured as Codex MCP but its local index is unavailable.
- Serena is not installed or configured.
- Repository has 23 skills; eight run identical validation before and after
  activation.
- Repository has 55 prompts with 85 prompt-level `required_reads` entries.
- Repository has 13 workflows, including seven live-run documents describing
  one execution loop.
- Written prompt/workflow metadata spec conflicts with executable validator.

## Key Deliverables

### Serena Installation And Inclusion

Install Serena for Codex using `uv`, `codex` context,
project-from-current-directory activation, and memory-disabled operation.

### Thin Code-Intelligence Policy

Define one short routing policy separating native tools, Serena, GitNexus,
tests/CI, and durable architecture documentation.

### Architecture-Lineage Removal

Remove persistent architecture contracts, metadata, maps, generation scripts,
architecture-only validation, tests, templates, and completion requirements.

### Governance Simplification

Reduce rules to invariants, skills to methods, workflows to transitions,
prompts to wording, and validators to executable contracts with consumers.

### Routing And Closeout Consolidation

Replace duplicated planning, live-run, reconciliation, and closeout routing
with a small workflow and prompt set.

### Metadata And Mandatory-Read Reduction

Remove metadata without consumers, broad activation hooks, and unconditional
reads not required for method correctness.

### Compatibility And Migration

Preserve publication safety, generated adapter ownership, verification before
completion, destructive-operation controls, non-architecture planning lineage,
and source-first fallback.

## Scope

### In Scope

- install and configure Serena for current Codex environment
- update user-local `%USERPROFILE%/.codex/config.toml` through Serena's supported
  Codex setup command
- update user-local `%USERPROFILE%/.serena/serena_config.yml` for
  `base_modes: [no-memories]`
- record tested Serena version and verification commands in tooling guidance
- include Serena in canonical root agent policy through owning template
- replace GitNexus-only pilot with combined code-intelligence policy
- add `.serena/` to `.gitignore`
- remove inactive architecture-lineage system and direct consumers
- remove architecture-specific Python metadata and capability linkage
- keep architecture documentation to `docs/architecture.md` plus ADRs
- reduce rule, skill, workflow, prompt, and metadata duplication
- remove broad validator hooks and excessive mandatory reads
- consolidate live-run and closeout logic
- narrow full audit-bundle triggers
- align prose metadata contracts with executable validators
- update generated adapters, tests, manifests, and CI

### Non-Goals

- Serena or GitNexus becoming architecture authority
- Serena memory, onboarding memory, generated wiki, or committed index
- new central registry, router, daemon, broker, or orchestration service
- GitNexus embeddings without measured value
- new enforcement dependency merely replacing deleted metadata
- deleting planning lineage solely because architecture lineage is removed
- rewriting historical specs and plans
- changing controlled public publication
- implementation planning inside this specification
- committing user-specific absolute paths, credentials, or MCP configuration
- exposing Serena dashboard or MCP transport beyond local machine

## Task/Wave Breakdown

### Wave 1: Install And Verify Serena

**Purpose:** establish Serena before policy depends on it.

**Steps:**
- [ ] confirm `uv` and `uvx`
- [ ] install Serena globally with Python 3.13
- [ ] initialize Serena global configuration
- [ ] run Serena Codex setup
- [ ] verify Codex MCP configuration
- [ ] enable `no-memories`
- [ ] activate repository from working directory
- [ ] verify symbol overview, lookup, references, and diagnostics

**Canonical commands:**

```powershell
uv tool install -p 3.13 serena-agent
serena init
serena setup codex
serena start-mcp-server --context codex --project-from-cwd
```

Use `uvx --from git+https://github.com/oraios/serena` only as disposable
fallback when global installation fails or version testing is required.

**Verification:**
- [ ] `serena --help` succeeds
- [ ] installed Serena version is recorded
- [ ] Codex lists Serena MCP
- [ ] project-from-CWD starts successfully
- [ ] memory/onboarding-memory tools are disabled
- [ ] MCP transport and optional dashboard remain local-only
- [ ] no Serena file is tracked

**Exit Criteria:** Serena provides exact symbol operations without committed
persistent architecture state.

### Wave 2: Establish Tool Ownership And Handoff

**Purpose:** make tool selection predictable without duplicate queries.

**Steps:**
- [ ] replace `docs/operating_system/tooling/gitnexus-pilot.md` with
      `code-intelligence-tools.md`
- [ ] update canonical root agent template
- [ ] regenerate `AGENTS.md`, provider adapters, and `.codex/rules`
- [ ] retain source-first fallback

| Need | Default owner |
|---|---|
| Small local text/file change | native code tools |
| Exact symbol, declaration, implementation, reference, diagnostic | Serena |
| Flow, route, process, module cluster, cross-repo relation, broad impact | GitNexus |
| Correctness and architecture enforcement | tests, static checks, CI |
| Durable boundaries and rationale | `docs/architecture.md`, ADRs |

**Handoff rules:**

1. Do not query both tools by default.
2. Use Serena directly when exact symbol scope is known.
3. Use GitNexus first when system flow or broad impact is unknown.
4. Move GitNexus to Serena only for exact identified symbols.
5. Move Serena to GitNexus only when local evidence reveals broader uncertainty.
6. Current source and tests win conflicts.
7. Tool unavailability never blocks safe source-first work.

**Verification:**
- [ ] one canonical policy owns routing
- [ ] root instructions contain only a thin summary
- [ ] no prompt or workflow exists solely for tool routing

**Exit Criteria:** tool responsibilities are distinct and conditional.

### Wave 3: Remove Persistent Architecture Generation

**Purpose:** delete inactive machinery instead of maintaining an unused system.

**Delete targets:**

- `tools/docs/generate_architecture_metadata.py`
- `scripts/sync_architecture_docs.py`
- `scripts/audit_architecture_linkage.py`
- `tests/test_sync_architecture_docs.py`
- `tests/test_architecture_metadata_generation.py`
- `tests/test_architecture_linkage_audit.py`
- `docs/generated/architecture_dag.yaml`
- `docs/generated/capability_lineage.yaml`
- architecture-generation-only files under `docs/architecture_templates/`
- managed-metadata prompts whose only purpose disappears
- architecture entries in starter-kit manifests and closure records

**Simplify targets:**

- remove architecture sync from `scripts/validate_repo_contracts.py`
- remove managed architecture branches from `scripts/validate_adoption_shape.py`
- remove architecture metadata coverage and capability-linkage modes from
  `scripts/validate_python_meta_headers.py`
- remove architecture sync CI step
- remove `managed_architecture_metadata`, `legacy_feature_contracts`, and
  `architecture_generator` when no consumer remains
- remove active feature/stage generated-contract policy from governance,
  lifecycle, adoption guides, rules, skills, prompts, and agent memory
- keep `docs/generated/planning_lineage.yaml` only if independent planning
  consumer and validator remain after planning cleanup

**Historical treatment:**

- completed architecture-generation specs and plans remain unchanged
- current navigation may mark them historical or superseded
- historical artifacts never remain active policy through links alone

**Verification:**
- [ ] no executable reference remains to removed scripts, maps, or markers
- [ ] baseline validation no longer branches on managed architecture mode
- [ ] CI contains no architecture sync job
- [ ] starter kit contains no architecture-generation dependency
- [ ] `docs/architecture.md` remains

**Exit Criteria:** architecture understanding is live and derived; durable
intent is human maintained; no persistent lineage generator remains.

### Wave 4: Simplify Rules And Python Contracts

**Purpose:** keep hard invariants only in rules.

| Current rule | Action | Preserved behavior |
|---|---|---|
| `global-baseline-contract-rule.md` | delete | adapter sync and verification stay executable |
| `env-gitignore-contract-rule.md` | merge into repository/publication hygiene | secrets remain ignored |
| `audit-evidence-mandate-rule.md` | simplify | full evidence remains mandatory for high-impact incidents |
| `doc-contracts-rule.md` | simplify | real generated files remain source-owned |
| `python-contracts-rule.md` | simplify | typing, errors, tests, normal docs remain |
| `command-execution-rule.md` | keep | destructive and publication safety |
| `publication-boundary-rule.md` | keep | private/public boundary |

**Audit trigger after cleanup:**

Full report, manifest, and evidence bundle is required only for:

- security or privacy failure
- data loss or serious data-quality incident
- repeated production/runtime failure with user impact
- unclear invariant failure spanning multiple boundaries
- explicitly requested formal audit

Ordinary test failures use failing output, root-cause evidence, and fresh
verification without a full audit bundle.

**Python contract after cleanup:**

- no mandatory file-level `@meta` block
- no `ownership`, `capabilities`, `features`, `invariants`, `@capability`, or
  `@proves` architecture-linkage requirement
- module docstrings remain optional normal documentation
- precise types, narrow exceptions, non-lossy error handling, focused tests,
  and configured checks remain
- existing `@meta` blocks are grandfathered until materially touched and may be
  removed when no consumer remains

**Verification:**
- [ ] no rule merely declares another document authoritative
- [ ] every remaining rule contains an enforceable invariant
- [ ] Python validation no longer requires architecture metadata
- [ ] security, publication, and data-loss protections remain unchanged

**Exit Criteria:** rules are few, enforceable, and non-procedural.

### Wave 5: Consolidate Skills And Remove Activation Hooks

**Purpose:** keep one reusable method per skill and remove activation-time work.

**Target skill set:**

1. `skill-using-superpowers` — thin selection entry, no governance read
2. `skill-brainstorming`
3. `skill-change-planning` — merge planning dispatch, spec drafting, plan
   writing, and plan review
4. `skill-execute-and-close` — merge plan execution and verification
5. Superseded: retain separate `skill-requesting-code-review` and `skill-receiving-code-review` skills
6. `skill-systematic-debugging`
7. `skill-test-driven-development` — strong default, not retroactive deletion
8. `skill-using-git-worktrees`
9. Superseded: keep `skill-dispatching-parallel-agents` for fan-out/fan-in and `skill-parallel-execution` for concurrent write-lane coordination
10. `skill-code-standards` — preserve reusable language-agnostic code standards; refactoring remains separate
12. `skill-private-public-repo-governance`
13. `skill-central-config-layer`
14. `skill-creating-learning-materials`
15. `skill-writing-skills` — maintainer-only distribution

**Metadata target:**

- retain `name` and `description`
- retain `allowed-tools` only when consumed or non-empty
- retain `required_reads` only when method cannot function without the file
- remove empty `required_outputs`, empty hooks, generic tags, and
  `distribution_tier` when no active consumer remains
- change metadata validator and adapter tests with schema changes

**Hook target:**

- remove all `python scripts/hooks/run_validator.py --fast` skill pre-hooks
- remove read-only skill post-hooks
- do not replace them with Serena hooks
- run targeted checks after writes and relevant final validation before claims
- delete hook runner/setup assets if no consumer remains

**Verification:**
- [ ] canonical skill count is at most 15
- [ ] no skill validates repository merely because it was activated
- [ ] no normal skill has more than one unconditional required read
- [ ] merged skills preserve methods, safety, and handoffs
- [ ] generated adapters pass sync and drift verification

**Exit Criteria:** skill selection costs less than execution and skills do not
duplicate workflow transitions.

### Wave 6: Consolidate Workflows, Prompts, And Planning

**Purpose:** make workflows own transitions and prompts own wording.

**Target workflows:**



```text
optional scenario
preflight
execute
verify
failure: diagnose -> fix -> rerun
success: closeout
```

**Target prompt set:**

1. `task-intake-prompt.md`
2. `design-spec-prompt.md`
3. `implementation-plan-prompt.md`
4. `execute-next-action-prompt.md`
5. `debug-incident-prompt.md`
6. `live-run-prompt.md`
7. `parallel-change-prompt.md`
8. `verification-closeout-prompt.md`
9. `documentation-update-prompt.md`
10. `publication-prompt.md`
11. `drift-reconciliation-prompt.md`
12. `code-review-prompt.md`

Provider sync, runtime deployment, GitNexus refresh, Serena setup, starter sync,
and migration commands remain tooling procedures or scripts, not prompts.

**Closeout contract:**

```yaml
scope_type: task | thread | workstream | roadmap | live_run
scope_id: <identifier>
required_children: []
verification_commands: []
```

One closeout prompt checks scope, current verification, blockers, terminal child
items, required docs, real generated outputs, and publication boundary.

**Planning tiers:**

| Complexity | Required artifact |
|---|---|
| Small local or obvious fix | none |
| Medium multi-step or multi-file change | one implementation plan |
| Large or design-ambiguous change | one specification and one plan |
| Multi-workstream program | one roadmap and child plans |

Spec sets, bounded thread sets, spec-authoring maps, and execution maps become
conditional tools for real multi-spec sequencing.

**Verification:**
- [ ] workflow count is at most five
- [ ] prompt count is at most twelve
- [ ] prompt README is index, not transition graph
- [ ] prompt bodies do not restate metadata routing
- [ ] workflows own transition order
- [ ] closeout logic exists once
- [ ] live-run transition logic exists once
- [ ] small local work requires no planning artifact

**Exit Criteria:** one fact or transition has one owner.

### Wave 7: Align Metadata And Validators

**Purpose:** make executable schema sole active contract.

**Steps:**
      delete it when validator help is sufficient
- [ ] remove unused prompt fields before removing validator checks
- [ ] retain prompt identity, description, type, and optional stage unless a
      remaining consumer proves another field necessary
- [ ] remove normal prompt `required_reads`; place conditional reads in body
- [ ] remove prompt `next_steps` when workflows own transitions
- [ ] remove prompt `related_skills` when methods are owned elsewhere
- [ ] update ladder tests to test actual workflow links
- [ ] remove deleted assets from manifests
- [ ] keep adapter metadata only where deployment consumes it

**Verification:**
- [ ] prose and validator schema cannot disagree
- [ ] every retained metadata field has named consumer
- [ ] validation passes with deleted fields absent
- [ ] no required read exists only to satisfy schema shape

**Exit Criteria:** metadata describes active behavior, not historical structure.

### Wave 8: Final Reconciliation

**Purpose:** prove smaller operating system remains complete and publish-safe.

**Steps:**
- [ ] regenerate agent adapters from canonical templates
- [ ] update manifests and closure inventory
- [ ] run focused tests for changed validators and generators
- [ ] run full repository validation and tests
- [ ] run starter-kit build and verification
- [ ] verify public publication excludes Serena, GitNexus, private tooling, and
      internal operating-system material
- [ ] verify `.serena/` and `.gitnexus/` remain untracked
- [ ] record final deleted-file and line-count summary

**Verification:**
- [ ] canonical sync/check commands pass
- [ ] full tests pass
- [ ] generated adapters match canonical sources
- [ ] no stale active references remain
- [ ] Git working tree contains only intended changes

**Exit Criteria:** reduced system is operational, validated, and smaller without
losing required safety or publication behavior.

## Design Decisions

### Decision: Install Serena Globally, Keep Repository State Disposable

- context: Serena must work across Codex tasks without becoming a committed
  project architecture database.
- choice:
  - install `serena-agent` with `uv tool install -p 3.13`
  - configure Codex through `serena setup codex`
  - use `--context codex --project-from-cwd`
  - configure `base_modes: [no-memories]`
  - ignore `.serena/`
- alternatives considered:
  - commit `.serena/project.yml`
  - install through Docker
  - run only through temporary `uvx`
- impact: installation is user-local and no committed memory/index layer exists.

### Decision: GitNexus And Serena Replace Discovery, Not Enforcement

- context: deletion removes lookup surfaces but must not move authority to MCP.
- choice:
  - GitNexus owns broad graph discovery
  - Serena owns exact live symbol discovery and semantic edits
  - tests and CI own enforcement
  - `docs/architecture.md` and ADRs own durable intent
- alternatives considered:
  - retain generated lineage
  - use Serena memory as documentation
  - use GitNexus wiki as documentation
- impact: architecture evidence refreshes on demand; graph refresh is not a
  universal completion requirement.

### Decision: No New Tool-Orchestration Layer

- context: cleanup must not replace document orchestration with tool
  orchestration.
- choice: one short conditional policy in canonical agent instructions and one
  tooling document.
- alternatives considered: central registry, routing workflow, prompt ladder.
- impact: tool choice remains local to task.

### Decision: Delete Inactive Architecture Generation Completely

- context: current mode disables generation and outputs are empty.
- choice: remove generator, wrappers, outputs, validators, tests, templates, and
  active policy references together.
- alternatives considered: indefinite grandfathering, optional starter module,
  archive directory.
- impact: managed consumers must pin older starter version or extract retired
  machinery before adopting this breaking cleanup.

### Decision: Grandfather Historical Artifacts, Not Active Complexity

- context: completed specs/plans reference retired architecture generation.
- choice: leave history unchanged while removing active links and validators.
- alternatives considered: rewrite history or keep runtime because history cites
  it.
- impact: history remains accurate without controlling current behavior.

### Decision: Use Conditional Reads And Explicit Verification

- context: mandatory reads and hooks impose cost before relevance is known.
- choice: unconditional reads only for method correctness, targeted checks after
  writes, and final verification before completion claims.
- alternatives considered: full validation on activation and global reads.
- impact: less latency and unrelated failure noise without weaker proof.

## Invariants

- Source code, runtime configuration, tests, and validators remain executable
  truth.
- GitNexus and Serena remain derived, disposable analysis tools.
- Serena installation and MCP configuration remain user-local.
- No user-specific absolute path is committed to starter artifacts.
- Serena MCP and dashboard access remain local-only.
- Tool output never overrides current source or test evidence.
- Tool unavailability does not block safe source-first work.
- No persistent architecture graph, wiki, lineage registry, or Serena memory is
  committed.
- `docs/architecture.md` remains human-owned.
- Significant durable decisions use ADRs when rationale must be preserved.
- Generated agent adapters remain source-owned and are never hand-edited.
- Private/public publication boundaries remain enforced.
- Security, privacy, destructive-operation, and data-loss controls remain.
- Validation evidence remains required before completion claims.
- Planning lineage and architecture lineage remain separate concerns.
- Historical specs and plans do not become active policy through links.
- No new dependency is added when existing platform capability suffices.
- No new orchestration layer is introduced.

## Acceptance Criteria

### Serena

- Serena installs through official `uv` path.
- Codex starts Serena in `codex` context for current repository.
- `no-memories` is active.
- exact symbol and reference lookup work.
- `.serena/` is ignored and no Serena artifact is tracked.

### Code Intelligence

- one canonical policy distinguishes native tools, Serena, GitNexus, tests/CI,
  and architecture docs.
- no task requires both MCPs unless escalation criteria apply.
- GitNexus remains optional and private-only.
- source-first fallback is explicit.

### Architecture Cleanup

- no persistent architecture generator, sync wrapper, audit wrapper, generated
  graph, capability map, or architecture-only test remains.
- no CI or completion gate requires architecture regeneration.
- no Python metadata is required for architecture linkage.
- `docs/architecture.md` remains.

### Operating-System Cleanup

- no more than 15 canonical skills
- no more than five workflow documents
- no more than twelve prompt templates
- no full-repo skill activation hooks
- no normal skill has more than one unconditional required read
- prompt/workflow metadata matches executable validation
- closeout logic exists once
- live-run transition logic exists once
- planning artifacts are complexity-tiered
- full audit bundles are limited to high-impact incidents

### Verification

- focused tests pass for changed scripts and validators
- full repository test suite passes
- full repository contract validation passes
- adapter sync and verification pass
- starter-kit build and verification pass
- publication-boundary checks pass
- no stale active reference remains to deleted surfaces

## Risks And Mitigations

### Risk: Serena Installation Breaks Across Codex Environments

- mitigation: use official `uv` installation and Codex setup; retain
  source-first fallback and disposable `uvx` fallback.

### Risk: Serena Adds Context Or Tool Bloat

- mitigation: use `codex` context, `no-memories`, no committed onboarding, and
  conditional invocation.

### Risk: Architecture Removal Breaks Managed Consumers

- mitigation: identify active downstream managed repositories before deletion;
  publish breaking-change note; allow pinning or extraction instead of retaining
  machinery in starter.

### Risk: Broad Cleanup Deletes Safety Controls

- mitigation: preserve publication, destructive command, secret, verification,
  security, privacy, and data-loss invariants with focused tests.

### Risk: Metadata Removal Breaks Adapter Deployment

- mitigation: trace fields through `deploy_agent_runtime.py`,
  `sync_agent_adapters.py`, build scripts, and tests; change consumer and schema
  atomically.

### Risk: Historical References Fail Link Validators

- mitigation: exempt completed history from active-link checks or mark retired
  references without rewriting historical content.

### Risk: Cleanup Becomes One Unsafe Mega-Patch

- mitigation: implementation plan splits work into independently verifiable
  waves; every wave leaves validation runnable.

## Validation Plan

- proof target: Serena is installed and usable by Codex
  - method: run official install/setup, reload MCP, perform symbol overview and
    reference lookup
  - evidence: command output, MCP listing, successful Serena responses

- proof target: Serena creates no committed persistent context
  - method: inspect `.gitignore`, `git status`, and repository search
  - evidence: `.serena/` ignored and no tracked Serena file

- proof target: architecture generation is fully removed
  - method: search retired scripts, paths, markers, config keys, and wording
  - evidence: only completed historical artifacts contain references

- proof target: executable behavior remains valid
  - method: run focused/full tests and repository validators
  - evidence: passing output

- proof target: adapter surfaces remain synchronized
  - method: run canonical adapter sync and verification
  - evidence: no drift after regeneration

- proof target: publication boundary remains intact
  - method: run starter/publication validation without push
  - evidence: private tooling and operating-system files remain excluded

- proof target: process duplication is reduced
  - method: count skills, workflows, prompts, hooks, reads, and duplicate
    closeout/live-run phrases before and after
  - evidence: thresholds met and one-owner routing confirmed

- proof target: retained metadata has active consumers
  - method: map every retained field to code or adapter consumer
  - evidence: metadata-consumer table in implementation closeout

## Completion Criteria

This specification is ready for implementation planning when:

1. Serena installation and Codex integration are accepted.
2. GitNexus/Serena handoff ownership is accepted.
3. complete architecture-generation deletion is accepted as breaking cleanup.
4. target skill, workflow, prompt, and rule counts are accepted.
5. invariants and non-goals are accepted.
6. implementation is split into reversible, independently verified waves.
7. no unresolved decision requires a new orchestration layer.

## Open Approval Questions

1. Should completed architecture-generation specs/plans remain in place as
   history, or move to archive in a separate later change?
2. Should `docs/generated/planning_lineage.yaml` remain after planning cleanup,
   or should its value be audited in the same implementation plan?
3. Should `skill-writing-skills` remain in starter kit or move to a private
   maintainer-only package immediately?

## External References

- [Serena README and installation](https://github.com/oraios/serena/blob/main/README.md)
- [Serena client configuration](https://oraios.github.io/serena/02-usage/030_clients.html)
- [Serena project configuration](https://oraios.github.io/serena/02-usage/050_configuration.html)
- [Serena security guidance](https://oraios.github.io/serena/02-usage/070_security.html)
- [GitNexus repository](https://github.com/abhigyanpatwari/GitNexus)
