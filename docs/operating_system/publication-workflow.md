# Publication Workflow

This document defines how private work is promoted to the public curated repo.

## Rule

The private repo is the development source of truth.

The public repo is a curated publication surface.

Do not develop normally in the public repo.

## Publication Steps

1. develop and commit in the private repo
2. review whether the public-facing docs and code are ready
3. run the curated export:

```powershell
.\scripts\publish_public_repo.ps1
```

4. inspect the export
5. publish intentionally:

```powershell
.\scripts\publish_public_repo.ps1 -Push
```

## Private-Only Paths

The publication workflow must exclude internal-only material such as:

- `docs/operating_system/`
- `docs/operating_system/agent_memory/`
- `agent-core/`
- `.codex/`
- `AGENTS.md`
- `.agents/`
- `.cursor/`
- `docs/superpowers/`
- `logs/`
- `sample/`

Lifecycle documentation now follows a stricter public-safe boundary:

- publish generated current-state feature contracts when they help explain the
  product-facing system
- publish generated stage contracts when they help explain the workflow stages
- do not publish `docs/features/*/feature.source.yaml`
- do not publish `docs/stages/*.source.yaml`
- do not publish feature-local `lineage.generated.yaml`
- do not publish feature `history.md` by default, because it may contain
  partially generated internal plan lineage
- do not publish aggregate `docs/generated/*` outputs unless they are
  explicitly allowlisted and reviewed as public-safe

In this repo, `.codex/` is the private Codex config/generated root.
It contains generated rules output and optional repo-local Codex subagent
config, but it is still not the canonical home for Codex skills or agent
memory.

## Review Standard

Before publication, confirm:

- the public README stands alone
- public docs do not depend on private repo workflow docs
- no internal agent/tooling assets leaked into the export
- no source-layer lifecycle authoring files leaked into the export
- no feature history files leaked into the export unless intentionally curated
- generated lifecycle or discovery docs are published only when they are
  explicitly public-safe

## Related Verification

If publication-boundary or adapter files changed first, run:

```powershell
.\scripts\sync_agent_adapters.ps1
.\scripts\verify_agent_adapters.ps1
```

before running the curated publish workflow.

Dry-run publication checks should work without a configured public remote. The remote is only required when `-Push` is requested.

If repo-level config ownership or publication config under `repo_config/` changes, run:

```powershell
.\.venv\Scripts\python.exe .\scripts\validate_repo_config.py
```

before publishing so publication boundaries and adapter mapping inputs are still
internally consistent.
