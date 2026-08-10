# project-OS-starter

A private starter repository for carrying forward the repo operating system without coupling new projects to a specific runtime structure.

## What This Repo Owns

- `docs/operating_system/`: human-readable repo governance and procedures
- `.agents/skills/`: canonical Codex skill discovery surface
- `docs/operating_system/templates/agents/`: source templates for generated instruction outputs
- `repo_config/`: starter-level configuration for shipped starter validation and planning contracts
- `scripts/`: validation, hooks, and curated repo procedures

## Canonical Vs Generated

Canonical source layers live in:

- `docs/operating_system/`
- `.agents/skills/`
- `docs/operating_system/templates/agents/`
- `repo_config/`
- `configs/`
- `scripts/`

Generated outputs are downstream artifacts:

- `AGENTS.md`
- `docs/AGENTS.md`
- `.codex/rules/*.rules`

Do not edit generated outputs directly. Regenerate them from the source layers.

## Bootstrap A New Project

Start with [docs/adoption_guide.md](docs/adoption_guide.md).

First-hour flow:

1. replace the starter identity in `README.md`
2. create the standard root project docs under `docs/`:
   - `setup.md`
   - `configuration.md`
   - `usage.md`
   - `pipeline.md`
   - `architecture.md`
3. keep the required project folders in place:
   - `docs/intent/`
   - `docs/operating_system/`
   - `docs/superpowers/specs/`
   - `docs/superpowers/plans/`
   - `repo_config/`
   - `scripts/`
   - `tests/`
4. fill `docs/intent/` before deep procedure docs
5. decide whether the private/public publication procedure applies
6. review starter governance and shipped root agent docs before adding any
   source-only factory procedures

## Agent Memory

Use official MCP Memory Server for verified reusable project knowledge. See `docs/operating_system/rules/agent-memory-rule.md` for fetch, update, privacy, precedence, and fallback policy; see `docs/operating_system/procedures/mcp-memory-server-setup.md` for client setup.

Memory data is private local state outside repository. Source code, tests, ADRs, current governance, and explicit instructions remain authoritative.

## Integration MCPs

Optional Context7 and Specmatic MCP servers support version-specific library research and OpenAPI contract work. See `docs/operating_system/procedures/frontend-backend-integration-mcp-setup.md` for private Codex setup, smoke tests, fallbacks, and removal.

Semble MCP and ast-grep CLI remain optional discovery tools. See `docs/operating_system/procedures/code-intelligence-tools-setup.md`; neither belongs in repository config or CI.

## Harness

First layer: `agents/*.toml`, `agents/roles.yaml`, and
`repo_config/harness.yaml`. `harness_core.request_api` selects supported core
request protocol. Install compatible `harness-core` and
`harness-core-launcher` releases, then run `harness-core validate --repo-root
<repo-root>` for consumer policy. Legacy `scripts/harness_task.py` and
`scripts/validate_harness_config.py` are package bridges only. Managed execution
needs host-supplied `run_managed` adapter. Generic package CLI exposes
`run-unavailable` only for explicit no-host-adapter proof; controller must block or record explicit
`waive`, which leaves run terminal `unvalidated`. `.harness/` stores optional
ignored local run artifacts. No scheduler, daemon, or job manager ships with
starter kit. For `runtime_provider_id: codex_app_server`, use provider-host
execution, never generic `run-unavailable`:

Current leased packets use a core-issued finite execution lease and one core
`terminalize_attempt(envelope)` boundary. Evidence produces `attempt_outcome/v2`;
one-decision terminal outcomes auto-finalize, while ambiguous terminal outcomes
need signed external `controller_authorization/v1`. Core writes one v3 receipt.
Host owns provider process lifecycle and bounded terminal observations only;
Windows providers run inside one kill-on-close Job Object per lease.

Historical unleased attempts stay isolated from dispatch and resume. External
operator signs bounded `legacy_cleanup_attestation/v1` evidence with an Ed25519
key outside repository and agent workspace. Current public records live in
`~/.codex/harness-authorities.toml`; migrate retired attester records with
`harness-core migrate-harness-authorities`. Controller submits canonical
`harness-core terminalize-attempt --input <envelope.json>`. Temporary
`--evidence` accepts only the policy-defined historical legacy packet API;
`--auto-block` is rejected. Core records one tagged null-lease terminal record,
then policy auto-finalizes `blocked`. Host never performs legacy cleanup or
terminal state writes.

```powershell
harness-core-launcher doctor
harness-core-launcher capabilities
harness-core-launcher preflight
harness-core-launcher run --harness-root <repo-root> --request <request.json>
```

`harness-core-launcher` selects the verified pointer-owned host release profile.
Host reads transport only from trusted user configuration. Do not put an endpoint,
launch command, or credentials in repository policy, requests, or packets. Never
dispatch bare `codex-harness-host`: PATH can resolve an unrelated user-level tool
instead of the active release profile.

Host contract:
`docs/operating_system/procedures/managed-execution-adapter-contract.md`.
Consumer install and compatibility preflight:
`docs/operating_system/procedures/harness-core-consumer-setup.md`.

## Customize First

When bootstrapping a new project, review these first:

- `docs/setup.md`
- `docs/configuration.md`
- `docs/usage.md`
- `docs/pipeline.md`
- `docs/architecture.md`
- `docs/intent/README.md`
- `docs/operating_system/governance/repo-governance.md`
- `docs/operating_system/governance/repo-governance.md`
- `docs/operating_system/templates/agents/*.template.md`
- `repo_config/planning_artifact_schema.yaml`
- `repo_config/planning_artifact_schema.yaml`

## Optional Nested AGENTS Templates

The starter ships with optional example templates:

- `docs/operating_system/templates/agents/example-runtime-AGENTS.template.md`
- `docs/operating_system/templates/agents/example-admin-AGENTS.template.md`

These are examples only. Keep them as optional starter guidance unless your
source repo also owns a separate generation procedure for additional agent entry
surfaces.

## Public Mirror Procedure

Use the curated publication script to prepare a public-safe export:

```powershell
.\scripts\publish_public_repo.ps1
```

Push to the configured public remote when ready:

```powershell
.\scripts\publish_public_repo.ps1 -Push
```

The default starter config keeps operating-system docs, skills, adapter sources, generated agent files, and other private-only materials out of the public mirror.

Repo/system configuration lives in `repo_config/`. Optional durable product feature documentation may live in `docs/features/`; code, configuration, schemas, and tests own executable behavior.

## Reusable Documentation Update Prompt

Use this reusable prompt when updating docs in any project:

- `docs/prompts/docs-update-prompt.md`

Keep it generic and repo-agnostic. Apply with a separate README-only prompt when needed.

