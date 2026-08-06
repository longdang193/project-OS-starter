# Managed Execution Adapter Contract

## Boundary

`scripts/harness_task.py` owns packet resolution, run records, authorization,
verification, outcomes, and controller decisions. Host owns actual agent and
workspace operations. Generic CLI has no host adapter.

Managed work starts only when host calls `run_managed(root, request, adapter)`.
No packet or `.harness/runs/<run-id>/run.json` means source-first local work,
not harness-managed work.

Packet owns role-derived claim schema for every executable lane. Host prompts
and core claim validation consume that same immutable schema.

## Required Adapter Methods

Host adapter provides these methods:

| Method | Input | Required result |
| --- | --- | --- |
| `capabilities()` | none | map of mode to `enforced`, `advisory`, or `unavailable` |
| `prepare_workspace(lane, packet)` | immutable lane and packet | workspace identity object |
| `dispatch_lane(lane, packet, workspace, cancellation_token)` | immutable lane, packet, workspace | opaque dispatch handle |
| `collect_claim(handle)` | dispatch handle | role-valid `claimed_result` |
| `collect_lane_evidence(handle, lane, packet, workspace)` | dispatch handle, immutable lane and packet, workspace | host execution evidence for exactly one dispatched lane |
| `cancel_lane(handle)` | dispatch handle | cancellation attempt |
| `materialize_final_state(lane, packet, workspaces)` | immutable integration lane, packet, workspaces | final workspace identity object |
| `verify_tool_bindings(lane, packet, workspace)` | immutable lane, packet, workspace | one verified root binding per selected packet tool |
| `run_checks(packet, workspace)` | immutable packet, final workspace | host check evidence from selected packet-scoped shell binding |

Only `enforced` capability permits dispatch. `advisory`, `unavailable`, absent,
or malformed capability produces `execution_mode_unavailable` before workspace
preparation or dispatch.

## Adapter-Owned Workspace Boundary

Every managed writable lane uses an adapter-owned isolated workspace. Host
dispatches the writer only with that workspace as its root and an enforced
write-capable sandbox that cannot write outside it. Host materializes one final
isolated state before validator dispatches; validator uses that state with an
enforced read-only sandbox.

Ambient desktop or CLI threads outside the adapter are source-first,
unvalidated work. They are not managed lanes and no host capability may claim
to intercept or accept their writes.

## Packet Tool Bindings

`repo_config/harness.yaml` owns logical tool metadata. Packet resolution copies
an immutable `tool_bindings` manifest with one declaration for every selected
route tool. Host must resolve every declaration to exactly one native binding
whose workspace root equals the dispatched lane workspace.

Each host binding evidence record must include tool, host kind, effective
access, root probe, workspace root, and `verified: true`. Writer lanes use
`writer_access`; validator lanes use `validator_access`, which must be
read-only. Missing, duplicate, ambient, mismatched, or unverified bindings
block dispatch. Ambient desktop MCP roots never satisfy a packet binding.

Host runs checks only through a verified selected `shell` binding in the final
packet workspace. Check evidence must identify that workspace and binding.

## Lane Execution Evidence

After each lane claim, host returns immutable execution evidence from its own
dispatch handle. Agent JSON claims cannot provide this evidence. Each record
must include exact lane ID, workspace root, host thread ID, host turn ID,
enforced sandbox, selected packet tools used, raw tool-call names, command
results, `ambient_mcp: false`, and workspace status before and after turn.

Writer evidence must show use of at least one packet-selected tool with
`workspace_write` access. Each command result must use exact packet workspace.
Validator evidence must show a separate `read-only` turn, use of at least one
packet-selected read-only tool, and identical workspace status before and
after. Core stores both lane records in `run.json` and fails verification if a
work or validator lane lacks valid host evidence.

## Completion States

| Result | Meaning |
| --- | --- |
| `accepted` | Controller accepted fresh harness evidence with proven criteria. |
| `blocked` | Managed lifecycle could not continue. |
| `unvalidated` | Controller explicitly waived unavailable managed execution with reason. Local proof may exist but is not managed acceptance. |

Host must never convert `unvalidated` to `accepted`. Start a new managed run
after capability exists.

## Validator Lanes

Independent validator evidence exists only when host capability supports a
separate read-only lane. Host must dispatch validator with a fresh immutable
packet after implementer claim, record its own claim, and keep validator paths
read-only. Implementer claim, local tests, and controller prose never count as
validator evidence.

`single_work_lane` is current core execution mode, but remains unavailable
until host adapter reports it `enforced`. `sequential_work_lanes` and
`parallel_work_lanes` remain unavailable until host adapter implements and
verifies their lane semantics. Do not silently downgrade a requested mode.

## Controller Rule

Controller records only allowed decisions in `run.json`: accept, retry,
escalate, request approval, waive, or block. `waive` requires non-empty
`reason` and is allowed only when outcome permits it. Controller cannot accept
an unavailable or waived run.
