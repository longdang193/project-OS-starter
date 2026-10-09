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

Fresh bounded smoke evidence reached a completed Codex pane, but the owned
runtime receipt still reported `BLOCKED_CAPABILITY` and emitted no
`response.usage` or billing fields. Pane status showed rounded session usage
(`52.7K` input, `1.85K` output, `54.6K` total) for `combo-normal`; this is
session-level, not run-bound raw provider evidence. Cache-read/cache-write
counts and cost remain `unknown`.

Follow-up smoke `run-economics-20261009-r3` ran with Herdr server available and
returned `launcher_exit_code=0`, but still reported
`runtime_completion_evidence_missing`. The bound payload contained no observed
model, provider, controller, session, timestamps, source bindings, or
`response.usage`; no trial started. The Codex pane was closed after the bounded
probe to prevent orphaned work.

Provider token usage and cost were therefore unavailable for paired comparison.
Failure-inclusive cost and cost-per-accepted-outcome remain `unknown`. No
efficiency benefit claim is made.

Read-only 9router observation was tested without changing LightRSI or 9Router.
The local database contains request-level token and cost rows, but the strict
observer rejected `run-economics-20261009-r3`: its recorded runtime start was
after the first matching provider request, and no request for the declared
session appeared in the bounded window. The sanitized result is retained in
`live-economics-9router-observation.json`. 9router data can support economics
only for an isolated session whose full timestamp boundary and one-to-one
request/cost join are proven.

Follow-up isolated probe `run-economics-20261009-r4` stopped before provider
launch because Herdr reported `target_resolution=not_found; eligible
candidates=0`. It produced no 9router request marker or usage row, so no
fallback direct launch or economics inference was attempted.

Probe `run-economics-20261009-r5` launched in a task-owned Herdr pane and
produced one exact 9router request/cost pair (`94,655` input tokens, `247`
output tokens, `$0.0377495`). The request used a long-lived Codex session with
135 other rows, so the strict observer rejected the run on
`timestamp_boundary_unproven`; the pair is diagnostic only, not economics
evidence. The task-owned Herdr workspace was closed after the probe.

Existing baseline/candidate trial windows were also measured from 9router
`usageHistory`. All six windows contained exactly one successful usage row.
Window-observed median cost changed from `$0.0084305` to `$0.0084880`
(`+0.68%`), while median total tokens fell by `3`. Total candidate cost was
`$0.073578` versus `$0.0260715` baseline (`+182.2%`), driven by
`candidate-2` at `$0.056752`. Formula audit matches 9router pricing exactly:
`candidate-2` cache-read tokens fell from `24,832` to `3,328`, while total
tokens stayed nearly flat. Median cache-read tokens did not change, so this
shows no typical cost shift but does show one large cache-reuse loss. Full
sanitized evidence is in
`router-window-economics.json`. Accepted outcomes remain unknown, so cost per
accepted outcome remains unknown.

## Confirmation pairs — October 9, 2026

- Three baseline/candidate direct Codex pairs completed through read-only `9router` `usageHistory` observation.
- Primary metric: median per-window `cache_read_input_tokens`.
- Baseline median: `448,512`; candidate median: `217,088`; observed delta: `-231,424` (`-51.6%`).
- Baseline total: `22` requests, `1,725,440` cache-read tokens, `$1.72483`; candidate total: `13` requests, `1,000,704` cache-read tokens, `$1.0223985`.
- Request counts were unequal (`4/3/15` vs `6/3/4`), so this is not a matched economics result. No causal Secretary claim, acceptance economics, or cost-per-accepted-outcome claim is valid.
- Evidence: `confirmation-pairs-20261009.json`; status remains `diagnostic-window-attributed-only` under `BLOCKED_CAPABILITY`.
