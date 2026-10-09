# Live Coordination Economics

Status: `INCONCLUSIVE`

Evidence disposition: `UNVERIFIED_PROBE`

Configured Codex route: `9router`. Native `CODEX_HOME` contains `config.toml` and
`auth.json`; credential values were not read into artifacts or published.

Owned `scripts/secretary_live_runtime.py` launches bounded Codex work through
Herdr, binds `task_id`, `plan_revision`, `attempt_id`, and `run_id`, and emits
sanitized runtime receipts with observed timestamps and completion.

Committed smoke and trial JSON predates current hardened receipt validation.
It lacks required assignment and producer-owned source bindings, so it is
retained as probe history only. It does not prove runtime completion,
correctness, controller/Secretary turns, or matched-pair independence.

Provider token usage and cost were unavailable, so paired cost deltas,
failure-inclusive cost, and cost-per-accepted-outcome remain `unknown`. No
efficiency benefit claim is made.
