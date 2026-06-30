# Invariants

- Generated adapter outputs are regenerated through `python scripts/sync_agent_adapters.py --all-platforms` and verified through `python scripts/sync_agent_adapters.py --check --all-platforms`; they are not hand-edited as source of truth.
- The private repo is the development source of truth; the public repo is updated only through the curated publish workflow.
- Cross-cutting operating-system work should stay under `docs/operating_system/` and may use `Feature: none` when no managed product feature contract is being changed.
- Important recurring failures should point to a current guardrail or a clearly named follow-up guardrail.
