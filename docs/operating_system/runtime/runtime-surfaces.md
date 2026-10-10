# Runtime Surfaces

This document records provider-native deployment for the user-global Project OS
runtime, rules, skills, root instructions, and hooks.

## Authoring SSOT

Production runtime dependency boundaries are enforced by `scripts/validate_repo_contracts.py` using stdlib `ast` import parsing. CI owns runtime behavior tests; this validator owns structural and prose contract checks, avoiding duplicate validator tests in the runtime matrix.

| Source | Role |
| --- | --- |
| `docs/operating_system/rules/*.md` | Canonical rule authoring |
| `.agents/skills/*/SKILL.md` | Canonical reusable method authoring in this repository |
| `docs/operating_system/templates/agents/root-AGENTS.template.md` | Canonical root instruction source |
| `agents/*.toml` | Canonical agent-profile registry, including optional rank |
| `scripts/herdr_main_launcher.py` | Canonical existing-target resolution and Herdr transport/observation projection |
| `scripts/herdr_parallel_dispatch.py` | Canonical bounded foreground coordinator for isolated DeepAgents lanes; no durable ledger or supervisor |
| `scripts/dcode_project.py` | Canonical DeepAgents projection, worker lifecycle, and generated role-view ownership |
| `scripts/opendesign_profile_adapter.py` | Canonical projection from a selected profile to an OpenDesign MCP `start_run` request |
| `scripts/ocr_delegate_adapter.py` | Canonical optional range-only OCR preparation adapter; native review remains authoritative |

## Plan Dispatch

Use existing dispatcher admission and execution paths with canonical plan input:

```powershell
py scripts/herdr_parallel_dispatch.py `
  --plan-file <plan.md> `
  --task "Task 3" `
  --runtime-bindings <runtime.json>
```

`runtime.json` is keyed by task ID and contains only runtime-owned fields:
`repository_identity`, `worktree`, `expected_base`, `session`, `pane`,
`runtime_grant`, `allowed_write_set`, `fixed_contracts`, `mutable_resources`,
`local_capabilities`, `remaining_authorized_task_allowance`, `attempt_deadline`,
and `accepted_prerequisites`. Optional launcher-owned fields may pass through
without plan-derived defaults. `prepare_plan_lanes()` is the single
execution-eligible preparation owner; `prepare_lane_inputs()` is a compatibility
adapter to that owner. Plan mode is mutually exclusive with `--lanes-file`;
both modes share admission, launch-bound freshness verification, and
`run_parallel()`.

`PreparedLane` remains the normalized static launch contract. The dispatcher may
produce an ephemeral `LaunchPreflight` projection immediately before delivery;
it reports root blockers as `PASS`, `BLOCKED`, or `NOT_EVALUATED` and must not
copy stable lane authority into a second contract. Runtime discovery stays out
of `plan_preparation.py`. Assignment identity remains stable across retries;
real launch attempts receive fresh attempt identity and attempt-scoped result
paths.

Canonical plan input projects plan goal, the complete selected task section,
accepted prerequisite identities, non-duplicative required proof, and the
allowlisted shared constraints `Required skills`, `Preauthorized local actions`,
`User-approval actions`, and `Parallel ownership`. Runtime authority and
resources remain caller-owned through `runtime.json`.

## Deployed Runtime Projections

| Projection | Role |
| --- | --- |
| `~/.agents/project-os/docs/operating_system/` | User-global deployed operating-system docs |
| `~/.agents/project-os/scripts/` | User-global deployed reusable Project OS scripts |

## Generated Runtime Outputs

| Provider | Root instructions | Rules | Native skills | Hooks/settings |
| --- | --- | --- | --- | --- |
| Codex | `generated_agents/codex/AGENTS.md` | `.agents/rules/*.md` | `generated_agents/codex/skills/<skill>/SKILL.md` | none |
| Codex delegated roles | `generated_agents/codex/agents/<role>.toml` | none | none | Deployed to `~/.codex/agents/` |
| DeepAgents delegated roles | Root `AGENTS.md` auto-loaded; user-local `dcode-project` materializes ignored `.deepagents/agents/<role>/AGENTS.md` only for launch, owns one same-worktree attempt at a time, then removes only its marker-owned views | Canonical `docs/operating_system/rules/*.md` read when task scope requires; `.agents/rules` is not auto-loaded | `~/.agents/skills/<skill>/SKILL.md` auto-discovered | Local runtime; Herdr-owned MCP selection through explicit `--mcp-select`; default `--no-mcp`; temporary launcher-owned config and isolated child `DEEPAGENTS_HOME`; project MCP configs remain untouched and untrusted |
| Claude | `generated_agents/claude/CLAUDE.md` | `.agents/rules/*.md` | `generated_agents/claude/skills/<skill>/SKILL.md` | none |
| Antigravity/Gemini | `generated_agents/antigravity/GEMINI.md` | `.agents/rules/*.md` | `generated_agents/antigravity/skills/<skill>/SKILL.md` | none |

## Deployment Targets

| Provider | Deploy root | Notes |
| --- | --- | --- |
| Shared native skills | `~/.agents/skills` | Synced copy of repo-owned skills; repo remains authoring source. |
| Shared Project OS runtime | `~/.agents/project-os` | Marker-owned sync of approved docs/scripts; one installation serves local projects. |
| Codex | `~/.codex` | Local deploy skips duplicate repo-owned skills. |
| DeepAgents | User-local `dcode-project` | setup-script-pinned `deepagents-code` version owns runtime version; launcher loads one Codex snapshot per invocation; DeepAgents derives `wire_api` to native `use_responses_api=false/true`; secrets load only for execution; selected worker model and effective parameters form worker evidence; same-worktree role views use exclusive attempt ownership. |
| Claude | `~/.claude` | Deploy includes generated native skills. |
| Antigravity/Gemini | `~/.gemini/antigravity` | Deploy includes generated native skills. |

## DeepAgents Boundary Contract

- Plan plus Git owns workflow truth, authority, dependencies, checkpoints, and acceptance history.
- CoS owns assignment, continuation, escalation, and acceptance decisions.
- `scripts/project_os_runtime/` owns lane preparation, admission, capability/evidence semantics, budget containment, settlement proof, lifecycle, and eligibility semantics. `scripts/herdr_attempt_contract.py` remains a compatibility forwarding surface.
- Remote integration accepts only normalized provider evidence: required checks plus `review_required`, `review_policy_satisfied`, `effective_review_state`, `reviewed_head_sha`, and a non-empty policy source. A GitHub-capable controller/provider computes the ephemeral effective review outcome; reconciliation validates it and does not own GitHub credentials or review-history reconstruction.
- `scripts/project_os_runtime/acceptance.py` exposes the native CoS acceptance boundary. `evaluate_acceptance()` derives `PASS`, `FAIL`, or `BLOCKED` from controller identity and authority, plan/task binding, active task eligibility, Worker evidence, the approved task condition set with exact observed coverage, Git checkpoint, verification, and settlement facts. `authorize_dependent_transition()` accepts only a complete internally consistent decision with fresh proof, matching task/plan identity, and completed dependencies; neither function writes plan state or creates a second authority.
- `prepare_plan_lanes()` admits selected tasks only when their recorded state is `pending` or `active`; `blocked` and `completed` fail before lane construction. `apply_accepted_plan_transitions()` is the canonical CoS mutation boundary: it requires the complete acceptance decision, Git proof, exact accepted transition, and revision-bound batch before delegating to the guarded writer. It persists an immutable pending release binding before the Plan write, then requires a controller-owned Git checkpoint verifier to prove that the checkpoint is reachable from the coordination ref and contains the exact accepted Plan revision before evidence disposal. `apply_plan_transitions()` remains Git-agnostic, serializes cooperating writers with a cross-process lock, and rejects stale revisions, wrong expected states, unsupported transitions, and incomplete prerequisites. Predecessor completion remains a separate structural-readiness fact.
- `scripts/herdr_parallel_dispatch.py` owns bounded scheduling, invocation, and event delivery; `scripts/herdr_main_launcher.py` owns Herdr transport and observation.
- Herdr CLI status is nonzero when any result has unresolved ownership or a non-null `failure_kind`; lifecycle facts such as `unresolved: false` and `capacity: retired` remain unchanged for safely settled failures.
- `scripts/dcode_project.py` owns worker execution, deadlines, PATH availability, descendants, cleanup, receipts, and same-worktree attempt claims; the shared runtime core owns lifecycle classification and eligibility.
- Herdr observation never proves retirement, authorizes retry, or accepts work.
- Ordinary personal-local probes may invoke `dcode-project` directly. Coordinated Git-tracked work enters through `herdr_main_launcher.py` or `herdr_parallel_dispatch.py`, which supplies correlated identity and grant evidence.
- `NEEDS_CONTEXT` requests information, not replay. Continuation requires settled ownership, explicit controller decision, remaining durable authority, and updated context.

## Policy

- Canonical repo sources remain source of truth.
- `~/.agents/project-os` is one user-global installation, not project state. Do not place plans, specs, project intent, project config, product code, or project tests there.
- `deploy_agent_runtime.py` syncs approved shared docs/scripts and records ownership metadata. `--check` reports missing, stale, drifted, or foreign-owned bundle files.
- Globalized scripts resolve project root from explicit `--repo-root`, then Git top-level, and block when neither exists.
- Project-local paths remain fallback when the shared installation is absent or marker ownership fails.
- `agents/*.toml` owns profile/provider/model/instruction facts. For Codex, `scripts/herdr_main_launcher.py` resolves and projects them into Herdr; for DeepAgents, `dcode-project` resolves and projects the selected profile into DeepAgents. Herdr owns target selection, transport, and diagnostic observation; the shared runtime core owns lifecycle classification and eligibility; `dcode-project` owns DeepAgents projection, worker lifecycle, same-worktree role-view ownership, and assignment-scoped attempt claims. `scripts/opendesign_profile_adapter.py` reads the same profiles and projects the selected model and instructions into OpenDesign MCP `start_run`; OpenDesign runtime selection remains an explicit MCP `agent` field, and provider configuration remains runtime-owned because MCP exposes no provider field.
- `scripts/herdr_parallel_dispatch.py` admits at most two independent lanes after worktree, pane, write-set, contract, and mutable-resource checks. It retains uncertain capacity, preserves per-lane evidence, and defers active cancellation claims to existing Herdr/process retirement evidence.
- Native Herdr Codex workers disable every effective MCP server by default; a
  validated server-level selection enables only selected servers. Tool-level
  selection fails closed until Codex can enforce it. Browser MCPs stay
  available to the top-level controller without multiplying browser processes
  across workers.
- Codex Herdr probes use one resolved `CODEX_HOME`; the launcher passes it to Herdr and Codex child processes and blocks when project and home `hooks.json` both define `Stop` hooks.
- Live Secretary probes consume native Codex `config.toml` and `auth.json` only
  through the resolved `CODEX_HOME`; pilot code never reads, copies, injects, or
  publishes credential values. The configured provider must be `9router`. A
  receipt-backed `READY` state uses the owned
  `scripts/secretary_live_runtime.py` Herdr pane runner, independently observed
  Codex completion, launcher-owned `attempt_id`, and sanitized
  timestamps/outcomes. Missing launcher, attribution, or completion is
  `BLOCKED_CAPABILITY`, not provider fallback or synthetic live evidence.
- Launcher evidence separates registry/runtime projection, Git identity, Herdr observation, and launch-request binding facts; developer instructions are represented by digest, not raw text. Each dispatch has one `dispatch_id`; each launch attempt carries one `attempt_id` across delivery, observation, reconciliation, and retirement; coordinated DeepAgents also carries one stable `assignment_id` across retries. Terminal results keep delivery, execution, observation, task result, cleanup, and performance sections independent. Runtime completion is not task acceptance: the launcher emits no new `task_result.accepted: true` path, and CoS retains `PASS | FAIL | BLOCKED` acceptance authority. The launcher and its tests own task-delivery mechanics; CoS accepts only final delivery evidence, never readiness or intent alone. The launcher does not use `--until working` because that can match unrelated active work.
- Codex prompt submission is non-blocking; successful `agent start` also requires a live, newly observed Codex process before prompt delivery. `agent prompt` acknowledgement owns delivery evidence, while `agent get`/`agent read` own bounded execution observation. Observation timeout or stale output never rewrites confirmed delivery as rejection. A timed-out execution may retain `cleanup: unverified` and `reconciliation_required: true`; cleanup uncertainty does not erase timeout evidence.
- DeepAgents lifecycle receipts own worker execution and settlement facts. Structured `TaskResult` records own reported task outcomes; a confirmed receipt without confirmed structured result remains `unverified` and reconciliation-required. Pane observation supplies pre-receipt diagnostics and legacy fallback only; pane text never promotes managed completion to task success. CoS retains `PASS | FAIL | BLOCKED` acceptance authority.
- Bound `TaskResult` records carry assignment/attempt identity, progress, checkpoint, remaining work, and verification references through atomic publication; valid task results report evidence only and never grant acceptance or continuation.
- Runtime deployment stages marker-owned output, validates it, then swaps one complete target tree; failed activation restores prior target content.
- Launcher evidence records monotonic `preflight`, `target_discovery`, `worker_initialization`, `delivery`, `observation`, and `retirement` durations plus launcher subprocess counts. Values use explicit measured/not-attempted/unavailable status, include total duration and retry attribution, and stay workload-specific; no optimization claim is valid without matching baseline evidence.
- Native Codex CoS may pass `--session auto --pane auto`; the repository launcher discovers all eligible existing matching-`--cwd` panes from the default Herdr server. With a named session and `--pane auto`, it queries only that session's pane list. The launcher validates workspace-qualified pane IDs, filters shell-only foreground processes, sorts candidates deterministically, and selects the first. Workspace IDs are not Herdr session names. Candidate evidence records the full eligible set. Mixed exact/`auto` selectors fail closed; no eligible target returns `target_resolution:not_found`. `HERDR_ENV` is not a controller dispatch gate; launcher child environments remove it.
- Herdr observation is bounded and transient: DeepAgents reads the correlated lifecycle receipt first; confirmed receipts skip pane `wait-output`, `process-info`, and `read` commands. Unresolved receipts use pane waits and pull probes for diagnostics or legacy fallback only; Codex uses `agent get`/`agent read` using the assignment attempt identity. `agent wait` remains a documented Herdr capability, not current launcher integration. Initial or stale state is `unknown`, and silence may become `stuck_suspected` only as controller evidence. Observation never auto-kills, retries, advances, releases an assignment claim, or stores raw output. Replacement requires canonical `BLOCKED | RECONCILE | ELIGIBLE` settlement evidence.
- Numeric Codex wall-clock grants fail closed until a named runtime owner can enforce interruption and cleanup. Native/default grants remain supported; no unsupported `outer-watchdog` claim is emitted.
- Positive `rank` values order only ranked profiles. Ranked profiles are ordered
  by registry rank; unranked profiles are explicit-only and non-orderable. Select
  executor and validator profiles independently from
  their bounded task contracts. A validator may be lower, equal, or higher than
  its executor when reliable for validation; specialized profiles may execute
  or validate based on task fitness.
- Generated runtime outputs remain deployable packaging surfaces.
- DeepAgents profile views are local generated runtime state, not primary profiles or tracked adapter output.
- DeepAgents auto-loads root `AGENTS.md` and discovers shared skills from
  `~/.agents/skills`. It does not load `.agents/rules` as direct instructions;
  those files are generated platform-adapter views. Detailed rules remain
  canonical under `docs/operating_system/rules/` and are read when task scope
  requires them.
- DeepAgents built-ins are executor-local. Herdr accepts explicit
  `--mcp-select <server[.tool][,server[.tool]...]>` and forwards it to
  `dcode-project`, which validates selection against approved Codex
   `[mcp_servers]`; no selection keeps child `--no-mcp`. Selecting a server
   exposes its tools; selecting a tool narrows access. Approval, sandbox, shell,
   profile, and thread settings remain separate.
- `dcode-project` owns DeepAgents capability validation and child projection;
  Herdr only forwards approved selectors or the default `--no-mcp`. Unsupported
  selectors fail before lane retirement.
- Coordinated DeepAgents resolves only the setup-owned wrapper at
  `~/.local/bin/dcode-project` on POSIX or `%USERPROFILE%\.local\bin\dcode-project.cmd`
  on Windows. Missing wrapper fails closed with setup guidance; arbitrary `PATH`
  executables are not accepted.
- Native Codex selection uses the same server identity contract but rejects
  tool selectors before launch. Requested and effective selection remain
  separate evidence fields.
- Headless `-n` auto-runs MCP tools only when read-only metadata is coherent;
  unannotated and mutating calls fail closed. Local compatibility permits only
  `playwright_browser_tabs` with `action=list`.
- Direct MCP uses temporary launcher-owned config under isolated child
  `DEEPAGENTS_HOME`; no per-task `.mcp.json` or `--trust-project-mcp`, and project
  MCP configs remain untouched and untrusted. MCP `headers` values must be
  `${VAR}` references. MCP `env` values may be `${VAR}` references or
  non-sensitive literals. Raw credentials and config secrets stay out of task
  text, logs, and tracked files.
- Codex controller owns handoff facts and writes `codex.mcp.handoff.v1` under
  `%USERPROFILE%\.local\share\dcode-project\handoffs`; `dcode-project` validates
  handoff path, age, schema, source IDs, capability digest, and sensitive-field
  exclusions, then injects only sanitized sources, facts, and constraints into
  task text. Handoff remains facts and provenance, not tool access.
- MCP escalation is controller-mediated: pre-dispatch facts use one handoff;
  mid-task requests return `NEEDS_CONTEXT`, then the outer Codex controller
  may refresh the handoff and retry the same plan task only after explicit
  continuation decision and settled prior-attempt evidence. When CoS is active,
  CoS coordinates that refresh and retry.
- DeepAgents web search is executor-local and needs user-local `TAVILY_API_KEY`.
  It is absent by default and never falls back to Codex browser or web MCP tools.
- Project `.env` files are untrusted runtime input. Launcher-owned provider
  environment values win, and project files must not carry credentials or
  runtime authority.
- Reusable operating methods live in skills; prompts remain wording-only.
- Optional OCR preparation belongs to `scripts/ocr_delegate_adapter.py`,
  `scripts/owned_process.py`, and `scripts/review_content_policy.py`; see
  `docs/operating_system/procedures/ocr-delegation-procedure.md`. Adapter owns
  Git-range identity, protected exclusions, bounded OCR execution, schema v1,
  provenance, and native fallback. It does not integrate with
  `tokenpilot-codex-hook.cmd`, hooks, installers, or generated runtime files.
- Project Secretary, when explicitly active, is an attention surface over these
  runtime paths; it does not replace direct execution selection or CoS. Runtime
  sessions, notifications, and operational receipts remain bounded evidence.
  Idle, timeout, missing notification, disconnect, and connection closure are
  hints requiring reconciliation, not proof of completion, cancellation,
  retirement, or failure.
- The in-process Secretary adapter is a contract fake. Active ownership is
  keyed by `(repository_identity, workstream)`; the complete
  `ControllerBinding`—repository identity, canonical work, workstream,
  expected branch, and expected base—detects binding drift. `AttentionDelta`
  and `CoordinationDelta` are communication payloads, not activation identity,
  and their set-like references are normalized at construction.
  `CommunicationEnvelope` carries a separate `message_id` and canonical
  evidence anchor. Activation reuse uses `activation_id`; delivery reuse uses
  `message_id`, controller identity, binding, and payload fingerprint.
  `ControllerSessionJournal` owns only in-memory receipts, active ownership,
  delivery receipts, release state, and deterministic controller identity for
  this contract fake. Released receipts never restore active ownership. Only a
  transport-owned durable journal may claim process-crash recovery.
- The bounded live Secretary wrapper is `scripts/secretary_live_runtime.py`.
  It launches through `scripts/herdr_main_launcher.py`, resolves one configured
  `CODEX_HOME` containing `config.toml` and `auth.json`, requires provider
  `9router`, and emits sanitized producer-bound receipts. Live launch requires
  an existing Herdr pane matching the requested worktree; missing target
  resolution is `BLOCKED_CAPABILITY`, not permission to use fallback transport.
  Receipt validity does not prove Worker publication, settlement, or CoS
  acceptance.
- Live receipts may carry measured token usage from `response.usage` and a
  separately marked published-rate-card cost estimate. Missing model/rate
  attribution keeps cost `unknown`; estimates never claim provider billing.
  For `9router`, published dashboard pricing is reference/savings pricing;
  it must be reported as an estimate, never as actual spend. Current direct
  mappings are `glm/glm-4.7` at `$0.60/M` input and `$2.20/M` output, and
  `minimax/MiniMax-M2.1` at `$0.20/M` input and `$1.00/M` output, sourced from
  the 9router GitHub docs effective `2026-10-09`. `combo-normal` and
  `combo-high` remain `unknown` until 9router exposes downstream attribution.
  9Router usage is normalized from `prompt_tokens`, `completion_tokens`,
  `cached_tokens` or `prompt_tokens_details.cached_tokens`, and
  `cache_creation_input_tokens` into `input_tokens`, `output_tokens`,
  `cache_read_input_tokens`, and `cache_write_input_tokens`. Cached tokens are
  never charged at normal input rates: cost stays `unknown` until matching
  cache-read/cache-write rates are published and attributed to the model.
  Local 9router config currently resolves them to `cx/gpt-*` Codex subscription
  members; combo membership is route state, not a stable repository rate card.
  Pilot comparison reports paired input/output/total token deltas even when
  estimated cost is unavailable.
- Secretary event hints use canonical identity `(source, workstream, event_type,
  observed_identity)`. `observed_anchor` identifies canonical evidence and
  optional `source_sequence` orders observations within one source. Coalescing
  unions evidence references; older observations remain actionable until
  current evidence explicitly resolves or supersedes that same canonical
  identity.
