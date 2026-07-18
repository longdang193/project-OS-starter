# Code Intelligence Tools

Use live code intelligence for discovery. Keep source, tests, and CI as truth.

## Ownership

| Need | Default tool |
|---|---|
| Small local text or file change | native code tools |
| Exact symbol, declaration, implementation, reference, or diagnostic | Serena |
| End-to-end flow, route, process, module cluster, cross-repo relation, or broad impact | GitNexus |
| Correctness and architecture enforcement | tests, static checks, CI |
| Durable architecture boundaries and rationale | `docs/architecture.md`, ADRs |

## Handoff

1. Do not query Serena and GitNexus for the same fact by default.
2. Start with Serena when exact symbol scope is known.
3. Start with GitNexus when broad flow or impact is unknown.
4. Move from GitNexus to Serena only for exact identified symbols.
5. Move from Serena to GitNexus only when local evidence exposes broader uncertainty.
6. Current source and tests win every conflict.
7. Tool absence or stale indexes never block safe source-first work.

## Serena

- Tested with Serena `1.6.0` installed by `uv tool install -p 3.13 serena-agent`.
- Run with `--context codex --project-from-cwd`.
- Keep `no-memories` and `no-onboarding` active.
- Keep dashboard disabled unless troubleshooting locally.
- Never commit `.serena/`, memories, indexes, onboarding output, or generated wikis.

## GitNexus

- Keep GitNexus private-only and optional.
- Check freshness with `scripts/get_gitnexus_freshness.ps1` before high-trust impact or refactor use.
- Refresh only when graph evidence materially helps.
- Never make GitNexus refresh a universal completion gate.
- Never publish `.gitnexus/` or GitNexus-specific internal notes.

## Boundary

Neither tool owns architecture or runtime behavior. Use `docs/architecture.md`
for durable system shape, ADRs for significant decisions, and native tests/CI
for enforceable boundaries.
