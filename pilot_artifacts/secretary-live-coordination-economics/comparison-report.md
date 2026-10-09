# Live Coordination Economics

Status: `INCONCLUSIVE`

Configured Codex route: `9router`. Native `CODEX_HOME` contains `config.toml` and
`auth.json`; credential values were not read into artifacts or published.

Owned `scripts/secretary_live_runtime.py` launches bounded Codex work through
Herdr, binds `task_id`, `plan_revision`, `attempt_id`, and `run_id`, and emits
sanitized runtime receipts with observed timestamps and completion.

Three fixed baseline/candidate pairs completed with correctness-valid receipts.
Baseline recorded three controller turns; candidate recorded three controller
and three Secretary turns. Human interventions were zero in both arms.

Provider token usage and cost were unavailable, so paired cost deltas,
failure-inclusive cost, and cost-per-accepted-outcome remain `unknown`. No
efficiency benefit claim is made.
