---
artifact_type: spec
template_id: detailed-specification
status: active
layer: change
name: native-personal-local-worktree-flow
targets:
  - docs/operating_system/procedures/personal-local-worktree-procedure.md
  - docs/operating_system/procedures/harness-core-consumer-setup.md
  - docs/operating_system/rules/multi-agent-orchestration-rule.md
  - docs/operating_system/templates/agents/root-AGENTS.template.md
  - README.md
---

# Native Personal-Local Worktree Flow

## Goal and Problem

### Problem

- current behavior or opportunity: ordinary one-user work is often sent through
  managed packets, provider sessions, leases, runtime profiles, signed
  envelopes, lane scheduling, and optional-tool contracts. Live probes found
  repeated failures in those control-plane layers before product work started.
- affected users, systems, or maintainers: one local operator, Git repositories,
  Codex native subagents, and harness documentation.
- evidence: advanced lifecycle code spans state transitions, attempt preparation,
  lease issuance, lane scheduling, host capability gates, claims, checks, and
  terminalization in `packages/harness-core/src/harness_core/managed.py`.
  Native Git worktree isolation already exists in
  `.agents/skills/skill-using-git-worktrees/SKILL.md` and launcher profile
  staging already calls native `git worktree`.
- consequence of no change: personal tasks pay production-like operational cost,
  create failed runtime records, and encourage repeated harness patches instead
  of ordinary Git-based repair.

### Goal

- desired outcome: `native-personal-local` work is a native Git and Codex
  workflow, not a second harness runtime. It reuses a clean current checkout
  for small work and creates a native Git worktree only when isolation
  materially reduces risk.
- observable success: a local operator can scope work, run one Codex-native
  writer from actual selected workspace context, run declared checks, inspect
  Git diff, and choose review plus Git disposition without packets, provider
  hosts, leases, retries, controller envelopes, or custom workspace lifecycle.

## Required Outcomes

### Outcome: One native workspace selection rule

- affected actor or system: local operator and Git repository.
- required result: personal-local flow inspects current Git workspace first.
  It reuses that checkout when clean and task is small, local, and reversible.
  It creates a named native `git worktree` when checkout is dirty, task is
  high-impact, independent parallel work needs disjoint ownership, or operator
  explicitly requests isolation.
- success condition: worktree choice follows one existing
  `skill-using-git-worktrees` rule. No new route field, lane, workspace model,
  branch manager, copied checkout, or worktree cleanup implementation exists.

### Outcome: Honest native-agent boundary

- affected actor or system: Codex native subagent and local controller.
- required result: personal-local flow does not launch, host, proxy, bind, or
  audit provider sessions. A writer subagent is used only when Codex starts it
  from actual selected-workspace context. The controller supplies absolute
  workspace identity and the agent uses that workspace for every tool call.
  If current Codex surface cannot establish this context, controller performs
  work directly from selected workspace; it does not replace native subagents
  with harness provider infrastructure.
- success condition: independent Git checks execute against selected workspace,
  never infer correct working directory from agent text, and remain valid
  whether work is performed by controller or native subagent.

### Outcome: Git-owned scope and proof

- affected actor or system: local controller and Git.
- required result: controller records native Git output from selected workspace
  and compares every reported repository-relative path with declared task paths.
  Evidence contains tracked changes relative to exact selected base commit,
  non-ignored untracked files, and both source and destination for renamed or
  copied entries. A submodule or nested repository change blocks personal-local
  acceptance unless task explicitly uses its own repository root.
- success condition: staged, unstaged, deleted, renamed, copied, type-changed,
  unmerged, and untracked paths use native Git evidence. Absolute, parent,
  malformed, ignored, and outside-declared paths cannot become accepted proof.

### Outcome: Separate review from Git disposition

- affected actor or system: local operator and existing branch-finishing flow.
- required result: `accept` or `block` records review result in current task
  handoff only; it does not commit, merge, push, tag, release, reset, clean,
  stash, or remove workspace. Existing `skill-finishing-a-development-branch`
  owns explicit keep, commit, merge, push, or destructive discard choice.
- success condition: accepted dirty worktree is never force-removed. Blocked or
  failed work stays unchanged until operator explicitly retains or discards it
  with native Git action.

### Outcome: Advanced managed mode remains isolated

- affected actor or system: existing `harness-core`, launcher, host, and
  historical managed runs.
- required result: `managed-advanced` remains opt-in for users needing current
  host-backed packet evidence. Existing `harness-core-launcher controller-init`
  and `close` remain managed-outcome operations for personal OS-user authority;
  they are not native-personal-local development commands. Native-personal-local
  flow neither reads nor modifies `.harness` managed run records, packets,
  attempts, receipts, authority files, active runtime profile, or host
  configuration.
- success condition: advanced commands and historical evidence retain current
  contracts; personal-local documentation never claims managed acceptance.

## Design Analysis

### Current State and Evidence

| Question | Evidence | Source | Confidence | Specification implication |
|---|---|---|---|---|
| What native workspace owner exists? | Existing skill selects current checkout or native Git worktree, defines identity, and forbids raw deletion. | `.agents/skills/skill-using-git-worktrees/SKILL.md` | high | Reuse it; add no workspace abstraction. |
| Can harness force a native subagent working directory? | Current Codex tool guidance exposes `spawn_agent` but no workspace or `cwd` parameter. | `generated_agents/codex/skills/skill-using-superpowers/references/codex-tools.md` | high | Do not make automatic subagent dispatch a personal-local contract. |
| How does Git report every relevant change form? | Native `git diff --name-status -z -M -C --find-copies-harder <base> --` and non-ignored untracked-file output report tracked changes, renames, copies, and untracked files. | `git diff -h`; `git ls-files -h` | high | Retain native Git output as review evidence; add no parser, matcher, packet, or run state. |
| Can dirty worktree be safely removed? | Native `git worktree remove` requires force for dirty worktree. | `git worktree remove -h` | high | Separate review from integration and cleanup. |
| Which flow already owns commit/merge/discard? | Existing branch-finishing skill requires explicit user choice and separates keep, merge, push, and destructive discard. | `.agents/skills/skill-finishing-a-development-branch/SKILL.md` | high | Reuse it; add no personal cleanup command. |

### Prototype and Validation Evidence

- prototype reference: no prototype exists yet. Before implementation completion,
  use a disposable Git repository to prove clean-checkout reuse, isolated native
  worktree creation, scope rejection, dirty-worktree retention, and deferred
  explicit cleanup.
- validated scenarios and states: repeated managed API-dispatch probes exposed
  provider tool, terminal evidence, cache, proxy, dependency, claim, retry, and
  controller admission failures. These findings establish control-plane cost,
  not a substitute for native-flow proof.
- findings incorporated into approved behavior: no automatic subagent binding,
  no mandatory worktree, no custom local record/state machine, no automatic
  cleanup, and no copied Git parser or matcher.
- rejected alternatives: custom personal-local launcher commands, a new JSON
  run record, copied `run.json` states, packet/lane compatibility, provider host
  fallback, automatic retry, and Docker orchestration. Docker remains available
  only when existing repository task setup or checks already require it.

### Scope

- included behavior: native workspace selection, native subagent usage rules,
  Git scope proof, review result, explicit Git disposition, and canonical
  personal-local guidance.
- affected boundaries: existing worktree and branch-finishing skills, new
  personal-local procedure, personal harness procedure, orchestration rule,
  root agent template, README, and generated agent guidance.
- admissible cases: one trusted local OS user, one Git repository root, normal
  Git worktree state, controller or one native writer, and declared local shell
  checks.
- compatibility expectation: no package, API, policy-schema, runtime-profile,
  host, managed-run, authority, or generated-schema behavior changes.

### Non-Goals

- adding code or commands to `harness-core`, `harness-core-launcher`, or host;
- replacing current advanced managed execution;
- persistent personal-local run records or recovery state;
- guaranteed process containment, security sandboxing, or trusted execution of
  hostile code;
- automatic commit, merge, push, release, cleanup, parallel scheduling, or
  provider-tool enforcement;
- Docker setup or management. Existing project-owned Docker commands remain
  valid task setup or check commands when applicable.

### Requirements and Behavioral Contract

#### Requirement: Workspace selection

- trigger or actor: controller receives ordinary personal-local task.
- preconditions: selected repository is Git worktree; task has objective,
  repository-relative allowed paths, base commit, and declared checks when
  needed.
- required behavior: inspect repository and current checkout. Reuse clean
  checkout for small reversible task; otherwise create native worktree under an
  ignored approved parent using named branch from exact base commit.
- output or state change: native Git checkout/worktree state only. Controller
  records workspace identity in task handoff, not custom runtime state.
- failure behavior: invalid repository, base ref, ignored-parent, target path,
  branch conflict, nested worktree, inconsistent metadata, or failed baseline
  stops before writer starts. No force, reset, prune, deletion, or overwrite.
- observable acceptance: same task inputs select same workspace mode under same
  checkout state; no helper copies Git workspace data.

#### Requirement: Writer context

- trigger or actor: controller begins task work after workspace selection.
- preconditions: selected workspace identity is known.
- required behavior: use Codex native writer only from actual selected workspace
  context. Every controller shell command specifies selected workspace. Prompt
  includes absolute workspace path, scope, checks, and Git restrictions.
- output or state change: native agent result is advisory; Git status and checks
  are final factual proof.
- failure behavior: missing native selected-workspace context disables writer
  dispatch; controller works directly or stops. No provider host fallback.
- observable acceptance: deliberate mismatched workspace test cannot be
  accepted because checks and change collection run from selected workspace.

#### Requirement: Change-set proof

- trigger or actor: writer completes or controller requests review.
- preconditions: exact base commit remains resolvable in selected workspace.
- required behavior: record `git diff --name-status -z -M -C
  --find-copies-harder <base> --` plus
  `git ls-files --others --exclude-standard -z` from selected workspace. Review
  every emitted path against declared task paths; treat `R` and `C` entries as
  two paths. Reject submodule or nested-repository changes.
- output or state change: native change output, reviewed path summary, and
  check outcomes in handoff only.
- failure behavior: failed Git commands, malformed zero-delimited entries,
  unsafe path, outside scope, unresolved conflict, or failed declared check
  blocks review acceptance and preserves workspace.
- observable acceptance: tracked and untracked mutations outside declared task
  paths fail; both rename/copy endpoints must be within declared task paths.

#### Requirement: Review and disposition

- trigger or actor: scope and declared checks pass.
- preconditions: controller presents native diff against selected base.
- required behavior: operator explicitly says `accept` or `block`. An accepted
  review hands off to existing branch-finishing flow for keep, commit, merge,
  push, or discard. A blocked review preserves its workspace and evidence; it
  does not hand off until operator explicitly requests a separate recovery or
  destructive-discard action.
- output or state change: conversational/task handoff review decision only.
- failure behavior: no decision, failed checks, or failed scope proof prevents
  `accept`. A blocked workspace remains unchanged. Dirty workspace removal is
  unavailable without a later explicit destructive branch-finishing disposition.
- observable acceptance: accepting changes leaves Git workspace unchanged;
  `git worktree remove` without force rejects dirty accepted worktree.

### Constraints and Alternatives

- constraint: native capability replaces custom code only where it provides
  exact required semantics. Git provides checkout/worktree/diff/status/cleanup;
  Codex provides native agents; repository skills provide lifecycle guidance.
- alternative: personal-local CLI with start/check/close JSON records.
  - benefit: one command surface and durable local history.
  - trade-off: recreates lifecycle state, recovery, locking, and compatibility
    work that Git and current skills already own.
  - reason rejected: no verified personal-use gap justifies that maintenance.
- alternative: always create worktree.
  - benefit: uniform isolation.
  - trade-off: branch and cleanup overhead for tiny clean-checkout tasks.
  - reason rejected: conflicts with existing native worktree rule.
- alternative: harness dispatches native subagent through provider adapter.
  - benefit: centralized telemetry and policy.
  - trade-off: restores exact managed control-plane failures this flow removes.
  - reason rejected: selected-workspace native dispatch is not exposed as stable
    harness interface.

## Design Decisions

### Decision: Workflow, not personal runtime

- context: personal-local needs low operational overhead and stable native
  behavior.
- selected approach: use existing Git and Codex workflows; update canonical
  procedure and skills only. Do not add personal-local executable code.
- rationale: eliminates copied workspace, state, agent, provider, and cleanup
  semantics.
- alternatives considered: custom core command, launcher command, and record.
- accepted trade-offs: no durable personal run history and no automatic native
  subagent dispatch.
- affected owners and boundaries: Git owns workspace; Codex owns agent; skills
  and procedure own guidance; branch-finishing owns Git disposition.

### Decision: Separate native work from managed personal closure

- context: existing launcher guidance describes `controller-init` and `close`
  as personal-local authority operations, while ordinary development needs no
  authority or managed record.
- selected approach: reserve `native-personal-local` for native Git/Codex
  development. Describe launcher controller setup and closure as advanced
  managed-outcome operations for a personal OS user.
- rationale: one term cannot honestly mean both a no-harness workflow and a
  signed managed terminalization path.
- alternatives considered: retain overloaded personal-local wording and add
  exceptions to every procedure.
- accepted trade-offs: existing launcher command names stay unchanged; guidance
  adds one clear boundary.
- affected owners and boundaries: README, harness consumer setup, orchestration
  rule, and generated root-agent guidance own terminology.

### Decision: Conditional worktree selection

- context: isolation helps only when checkout or task risk needs it.
- selected approach: use current checkout when safe; use native worktree under
  existing skill conditions.
- rationale: preserves isolation where needed without making every small task
  create branch and cleanup burden.
- alternatives considered: always current checkout and always worktree.
- accepted trade-offs: workflow has two native workspace modes but one shared
  proof and disposition contract.
- affected owners and boundaries: `skill-using-git-worktrees` owns selection
  and identity.

### Decision: Git output is proof, not protocol

- context: scope checks must cover all Git change forms without copying Git
  implementation.
- selected approach: retain native zero-delimited Git name-status and untracked
  output as review evidence. Controller compares emitted repository-relative
  paths with declared task paths; no parser, matcher, run record, or personal
  local package API is added.
- rationale: Git owns change detection and encoding. Personal-local guidance
  owns explicit review, avoiding copied harness validation behavior.
- alternatives considered: `git status --porcelain` parser, agent-declared
  changed files, and a new local scope-check command.
- accepted trade-offs: review is intentionally interactive and unsuitable for
  unattended or hostile-code automation.
- affected owners and boundaries: Git owns data production; canonical personal
  local procedure owns evidence review.

### Compatibility, Migration, and Risk

- old behavior: personal work may choose complex managed execution and its
  provider, runtime, authority, and packet prerequisites.
- new behavior: guidance defaults ordinary personal work to native workflow;
  managed mode remains explicit advanced option.
- compatibility boundary: existing managed APIs, packages, profiles, hosts,
  authority files, historical evidence, policy, and generated schema stay
  unchanged.
- migration or backfill: none. Existing managed runs retain current closure
  procedure; no `.harness` state is read or converted.
- rollout and rollback: documentation and skills only. Roll back by reverting
  canonical guidance and regenerating agent surfaces.
- deprecation or consumer impact: no command removal. Guidance de-emphasizes
  managed execution for ordinary personal tasks.
- risk:
  - mitigation: real Git disposable-repository proof, explicit workspace
    identity, independent checks/diff from selected workspace, and no forced
    cleanup.

## Invariants and Edge Cases

### Invariants

- Git remains source of truth for repository identity, workspace, base, branch,
  status, diff, untracked files, and worktree cleanup.
- Codex native subagent output never substitutes for selected-workspace Git
  evidence or declared check output.
- Current checkout and isolated worktree use identical scope, check, review,
  and disposition rules.
- Personal-local creates no packets, attempts, leases, provider sessions,
  authority files, controller envelope, `.harness` record, scheduler state, or
  runtime profile mutation.
- No automatic commit, merge, push, release, retry, cleanup, force removal,
  reset, clean, stash, or branch deletion occurs.
- Managed-advanced operates independently and historical managed evidence is
  never modified by personal-local workflow.

### Edge Cases

- empty or minimal input: missing objective, base, allowed path, or malformed
  check blocks before writer work. Read-only work may declare no checks and no
  write paths.
- normal and large input: one writer/controller owns one selected workspace.
  Parallel work uses separately approved disjoint native worktrees; no custom
  scheduler starts them.
- duplicate, missing, malformed, or unsupported data: branch/path collisions,
  missing base, dirty baseline, invalid Git output, unsafe paths, and nested
  worktree stop without destructive recovery.
- retry, cancellation, timeout, partial failure, or concurrency: no workflow
  retry exists. Interrupted/failed workspace remains for inspection; new work
  begins only through normal fresh workspace selection. Concurrent writers may
  not share write paths or workspace.
- migration or mixed-version state: Not applicable: no schema or runtime
  version changes. Existing managed records are outside this flow.
- generated-source consistency: canonical procedure, skill, rule, template,
  and README change before `sync_agent_adapters.py` regenerates outputs.
- security or accessibility boundary: personal trusted OS-user workflow only;
  do not use for shared machine, production, hostile code, or secret-isolation
  requirements. Existing repository Docker commands may be declared setup or
  checks when task already needs them; flow does not manage containers.

## Validation Plan

### Backend Verification Claims

- direct boundary: disposable Git repository executes documented workspace
  selection, native worktree creation, Git change collection, check, review,
  and cleanup commands.
- important success and failure behavior: clean checkout reuse; dirty checkout
  creates isolated worktree; mutation outside declared task paths blocks; failed
  check blocks; dirty accepted worktree remains until explicit Git disposition.
- final state or side effects: Git worktree list, branch, base commit, status,
  and diff match documented flow. No package, profile, host, authority, or
  managed-run state changes.
- rollback, retry, duplicate, or idempotency behavior: starting fails without
  mutation for colliding worktree/branch; native repeated removal is not
  claimed; failed workspace is retained and later discard is explicit.
- canonical contract and conformance proof: canonical documentation passes
  planning, template, generated-agent, and repository contract validators.
- real dependencies requiring proof: Git CLI/worktree behavior in disposable
  local repository. Codex native subagent binding is deliberately not claimed
  as automated behavior.
- representative-operation trace mechanism: capture Git worktree list, base
  commit, status, changed paths, check exit result, and explicit disposition in
  execution handoff.
- performance claim and threshold: Not applicable: no performance claim.

### Acceptance Criterion: Safe native workspace choice

- setup or precondition: disposable repository has clean checkout, then dirty
  checkout or explicit isolation request.
- action: follow canonical personal-local workspace procedure.
- expected result: clean small task reuses checkout; dirty or requested-isolated
  task creates native worktree at exact base under ignored parent.
- failure condition: custom copied workspace, force/reset/cleanup, or worktree
  creation for clean small task without isolation reason.
- proof method: Git commands and procedure output.
- expected evidence: repository root, base SHA, worktree list, selected mode,
  and clean baseline result.

### Acceptance Criterion: Scope proof blocks incomplete or unsafe work

- setup or precondition: selected workspace has exact base and declared task
  paths.
- action: create staged, unstaged, untracked, and rename/copy mutations; run a
  declared passing and failing check.
- expected result: all native Git-reported paths are reviewed; outside path, failed check,
  malformed Git entry, conflict, or nested repository blocks acceptance.
- failure condition: agent text or partial `git status` allows unverified path.
- proof method: zero-delimited Git output, reviewed path summary, and check exit
  code from selected workspace.
- expected evidence: both rename endpoints, untracked path, failed/successful
  check result, and `block` disposition where required.

### Acceptance Criterion: Review cannot destroy accepted changes

- setup or precondition: scoped declared checks pass in dirty native worktree.
- action: operator accepts, then attempts normal worktree removal before Git
  disposition.
- expected result: acceptance changes no Git data; native removal refuses dirty
  workspace; existing branch-finishing workflow owns later keep/commit/merge or
  explicit destructive discard.
- failure condition: automatic commit, merge, push, cleanup, or forced removal.
- proof method: Git status, diff, worktree-remove result, and handoff record.
- expected evidence: unchanged dirty diff after acceptance and no force action.

## Completion Criteria

Specification is complete when:

1. native workspace selection reuses current checkout when safe and worktree
   isolation only when justified
2. native-agent use has no invented working-directory guarantee or provider
   fallback
3. native Git change evidence, scope review, check, and Git disposition
   contracts cover stated change forms and failure cases
4. no personal-local code, state record, command, package, runtime profile, or
   managed record is introduced
5. canonical guidance and generated agent surfaces distinguish personal-local
   workflow from advanced managed execution
6. disposable Git proof and documentation validators satisfy every acceptance
   criterion
7. implementation sequencing remains in linked implementation plan
