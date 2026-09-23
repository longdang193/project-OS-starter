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

## Deployed Runtime Projections

| Projection | Role |
| --- | --- |
| `~/.agents/project-os/docs/operating_system/` | User-global deployed operating-system docs |
| `~/.agents/project-os/scripts/` | User-global deployed reusable Project OS scripts |

## Generated Runtime Outputs

| Provider | Root instructions | Rules | Native skills | Hooks/settings |
| --- | --- | --- | --- | --- |
| Codex | `generated_agents/codex/AGENTS.md` | none | `generated_agents/codex/skills/<skill>/SKILL.md` | none |
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
| DeepAgents | User-local `dcode-project` | setup-script-pinned `deepagents-code` version owns runtime version; launcher loads one Codex snapshot per invocation; DeepAgents alone derives `wire_api` to native `use_responses_api=false/true`; secrets load only for execution; selected worker model and effective parameters form worker evidence; same-worktree role views use exclusive attempt ownership; Tura configuration remains independent. |
| Claude | `~/.claude` | Deploy includes generated native skills. |
| Antigravity/Gemini | `~/.gemini/antigravity` | Deploy includes generated native skills. |

## DeepAgents Boundary Contract

- Plan plus Git owns workflow truth, authority, dependencies, checkpoints, and acceptance history.
- CoS owns assignment, continuation, escalation, and acceptance decisions.
- `scripts/project_os_runtime/` owns lane preparation, admission, capability/evidence semantics, budget containment, settlement proof, lifecycle, and eligibility semantics. `scripts/herdr_attempt_contract.py` remains a compatibility forwarding surface.
- `scripts/herdr_parallel_dispatch.py` owns bounded scheduling, invocation, and event delivery; `scripts/herdr_main_launcher.py` owns Herdr transport and observation.
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
- `agents/*.toml` owns profile/provider/model/instruction facts. For Codex, `scripts/herdr_main_launcher.py` resolves and projects them into Herdr; for DeepAgents, `dcode-project` resolves and projects the selected profile into DeepAgents. Herdr owns target selection, transport, and diagnostic observation; the shared runtime core owns lifecycle classification and eligibility; `dcode-project` owns DeepAgents projection, worker lifecycle, same-worktree role-view ownership, and assignment-scoped attempt claims. Tura keeps its existing provider and credential path. `scripts/opendesign_profile_adapter.py` reads the same profiles and projects the selected model and instructions into OpenDesign MCP `start_run`; OpenDesign runtime selection remains an explicit MCP `agent` field, and provider configuration remains runtime-owned because MCP exposes no provider field.
- `scripts/herdr_parallel_dispatch.py` admits at most two independent lanes after worktree, pane, write-set, contract, and mutable-resource checks. It retains uncertain capacity, preserves per-lane evidence, and defers active cancellation claims to existing Herdr/process retirement evidence.
- Native Herdr Codex workers disable every effective MCP server by default; a
  validated server-level selection enables only selected servers. Tool-level
  selection fails closed until Codex can enforce it. Browser MCPs stay
  available to the top-level controller without multiplying browser processes
  across workers.
- Codex Herdr probes use one resolved `CODEX_HOME`; the launcher passes it to Herdr and Codex child processes and blocks when project and home `hooks.json` both define `Stop` hooks.
- Launcher evidence separates registry/runtime projection, Git identity, Herdr observation, and launch-request binding facts; developer instructions are represented by digest, not raw text. Each dispatch has one `dispatch_id`; each launch attempt carries one `attempt_id` across delivery, observation, reconciliation, and retirement; coordinated DeepAgents also carries one stable `assignment_id` across retries. Terminal results keep delivery, execution, observation, task result, cleanup, and performance sections independent. Runtime completion is not task acceptance: the launcher emits no new `task_result.accepted: true` path, and CoS retains `PASS | FAIL | BLOCKED` acceptance authority. The launcher and its tests own task-delivery mechanics; CoS accepts only final delivery evidence, never readiness or intent alone. The launcher does not use `--until working` because that can match unrelated active work.
- Codex prompt submission is non-blocking; successful `agent start` also requires a live, newly observed Codex process before prompt delivery. `agent prompt` acknowledgement owns delivery evidence, while `agent get`/`agent read` own bounded execution observation. Observation timeout or stale output never rewrites confirmed delivery as rejection. A timed-out execution may retain `cleanup: unverified` and `reconciliation_required: true`; cleanup uncertainty does not erase timeout evidence.
- DeepAgents lifecycle receipts own worker execution and settlement facts. Structured `TaskResult` records own reported task outcomes; a confirmed receipt without confirmed structured result remains `unverified` and reconciliation-required. Pane observation supplies pre-receipt diagnostics and legacy fallback only; pane text never promotes managed completion to task success. CoS retains `PASS | FAIL | BLOCKED` acceptance authority.
- Bound `TaskResult` records carry assignment/attempt identity, progress, checkpoint, remaining work, and verification references through atomic publication; valid task results report evidence only and never grant acceptance or continuation.
- Runtime deployment stages marker-owned output, validates it, then swaps one complete target tree; failed activation restores prior target content.
- Launcher evidence records monotonic `preflight`, `target_discovery`, `worker_initialization`, `delivery`, `observation`, and `retirement` durations plus launcher subprocess counts. Values use explicit measured/not-attempted/unavailable status, include total duration and retry attribution, and stay workload-specific; no optimization claim is valid without matching baseline evidence.
- Native Codex CoS may pass `--session auto --pane auto`; the repository launcher discovers all eligible existing matching-`--cwd` panes from the default Herdr server, validates them through their workspace-qualified pane IDs, sorts candidates deterministically, and selects the first. Workspace IDs are not Herdr session names. Candidate evidence records the full eligible set. Mixed exact/`auto` selectors fail closed; no eligible target returns `target_resolution:not_found`. `HERDR_ENV` is not a controller dispatch gate; launcher child environments remove it.
- Herdr observation is bounded and transient: DeepAgents reads the correlated lifecycle receipt first; confirmed receipts skip pane `wait-output`, `process-info`, and `read` commands. Unresolved receipts use pane waits and pull probes for diagnostics or legacy fallback only; Codex uses `agent get`/`agent read` using the assignment attempt identity. `agent wait` remains a documented Herdr capability, not current launcher integration. Tura uses `project-delegate` outside the Herdr main-lane path. Initial or stale state is `unknown`, and silence may become `stuck_suspected` only as controller evidence. Observation never auto-kills, retries, advances, releases an assignment claim, or stores raw output. Replacement requires canonical `BLOCKED | RECONCILE | ELIGIBLE` settlement evidence.
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
