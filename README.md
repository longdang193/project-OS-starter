# Project OS Starter

## A starter kit for governed multi-agent development with AI coding agents.

Define how coding agents are assigned, bounded, equipped, observed, and accepted across multiple runtimes.

**One controller. Bounded lanes. Evidence before acceptance.**

- Shared capability profiles
- Controlled tool access
- Explicit Git and workspace boundaries
- Observable lifecycle and acceptance evidence

[GitHub](https://github.com/longdang193/project-OS-starter) · [Issues](https://github.com/longdang193/project-OS-starter/issues)

## Why Project OS Starter?

Individual coding agents can write useful code. Multi-agent development adds harder problems:

- Who owns each task?
- Which tools and runtimes may each worker use?
- How do concurrent changes avoid colliding?
- What counts as running, finished, or accepted?
- Which evidence survives retries, replacement attempts, and review?

Project OS Starter supplies repository structure and contracts for answering those questions consistently.

## How It Works

```text
Task Request → Lead Controller → Git-Tracked Plan → Bounded Admission
                                                        │
                                              Implementation Lanes
                                                        │
                                               Selected Runtime
                                                        │
                                              Accepted Evidence
                                                        │
                                             Acceptance Decision
```

The system separates task delivery, bounded execution, evidence, recovery, and final acceptance. Runtime completion alone does not establish task acceptance.

If admission or evidence fails, work enters `BLOCKED`. Reconciliation settles plan and Git state before any fresh attempt; retry is never automatic.

See [`docs/architecture.md`](docs/architecture.md), [`docs/pipeline.md`](docs/pipeline.md), and the [Archify workflow source](docs/architecture/project-os-starter-guided-story.workflow.json).

## Example Workflow

```text
Request: implement an API change, update its frontend usage, and review it.

Controller
 ├─ Lane A: backend change, selected profile, bounded workspace
 ├─ Lane B: frontend change, selected profile, bounded workspace
 ├─ Validate dependencies and collect runtime evidence
 └─ Review combined result and decide PASS / FAIL / BLOCKED
```

Workers own engineering inside assigned scope. The controller owns orchestration boundaries, evidence requirements, and acceptance.

## What It Governs

| Concern | Contract |
| --- | --- |
| Assignment | Roles, profiles, ownership, and task boundaries stay explicit. |
| Execution | Workers run through selected runtimes with bounded scope. |
| Capabilities | Tool and MCP access is selected deliberately, not inherited implicitly. |
| Workspace | Git and workspace boundaries make concurrent changes inspectable. |
| Lifecycle | Preparation, delivery, execution, observation, cleanup, and result state stay distinct. |
| Acceptance | Required evidence drives `PASS`, `FAIL`, or `BLOCKED`; worker claims do not. |

## Included Structure

- **Agent profiles** — reusable role and capability definitions.
- **Canonical sources** — one owning layer for rules, procedures, templates, and configuration.
- **Generated projections** — downstream instruction and starter-kit outputs derived from canonical sources; edit canonical sources, then regenerate outputs.
- **Validation tooling** — repository, metadata, configuration, lifecycle, and package-boundary checks.
- **Runtime adapters** — conventions for Native Codex, DeepAgents, Tura, and related local execution paths.
- **Regression coverage** — tests for delivery, isolation, capability selection, lifecycle, and evidence contracts.

## Design Principles

- **Evidence before acceptance** — completion is a claim until required proof exists.
- **Explicit authority** — controllers, workers, reviewers, and cleanup actions have separate responsibilities.
- **Repository as source of truth** — Git state, tests, contracts, and recorded evidence outrank chat output.
- **Canonical over copied** — generated surfaces are rebuilt from their owners.
- **Unknown stays unknown** — missing or ambiguous runtime evidence does not become success.

## Where It Fits

```text
Coding runtime
Codex / DeepAgents / Tura
          │
          ▼
Project OS Starter
assignment · boundaries · tools · lifecycle · evidence · acceptance
          │
          ▼
Project repository
code · tests · Git history · review
```

Project OS Starter is not a foundation model, IDE, memory database, or application framework. It is the operating layer around coding-agent execution.

## Scope And Status

This repository is an active starter/reference implementation. Runtime integrations, contracts, and generated surfaces may change as the system is hardened.

It does not promise autonomous engineering, zero-configuration deployment, universal runtime support, or performance gains without matching measurements.

Public distribution is curated separately from deeper implementation and runtime internals. The current public surface is an overview, not a complete drop-in product distribution.

## Evaluation Path

For maintainers with source access, evaluate the project through its contracts and tests:

```powershell
python scripts/validate_repo_contracts.py
python scripts/validate_repo_config.py
python -m pytest -q
```

Adopt only the layers your project can own, expose, and validate. Keep project-specific setup and product code in the consuming repository.

## Local Adoption

- Native personal work follows `native-personal-local` and `docs/operating_system/planning/planning-dispatch.md`.
- Native execution uses Codex, DeepAgents, or Tura, selected per bounded task.
- Shared operating-system docs, reusable scripts, and skills stay under the shared Project OS installation: `~/.agents/project-os` and `~/.agents/skills`.
- Keep project-specific project-local folders such as `docs/intent/`, `docs/superpowers/`, `repo_config/`, code, tests, and scripts in this repository when adopting this starter.
- When adopting this starter, create `docs/intent/` when durable project purpose needs more than `README.md`.
- DeepAgents runtime setup owns its version; version pinned by `scripts/setup_deepagents_runtime.ps1`.
- Select runtime profiles explicitly, for example `--role <profile>`.
- DeepAgents MCP is opt-in through explicit Herdr selection. Herdr accepts `--mcp-select` and forwards selected servers to `dcode-project`.
- MCP `headers` values must be `${VAR}` references. MCP `env` values may be `${VAR}` references or non-sensitive literals.

## Contributing

Keep changes focused. Update tests and documentation when behavior or contracts change. Edit canonical sources instead of generated projections. Open an issue before proposing broad changes.

## License

No license file is included yet. Review licensing before reuse or redistribution.
