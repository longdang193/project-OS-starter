---
layer: change
artifact_type: plan
template_id: implementation-plan
contract_version: "1"
status: active
name: worker-contract-benchmark-fixture
---

# Worker Contract Benchmark Fixture

## Goal

Complete bounded fixture tasks while preserving required proof and write scope.

## Execution Approach

- Mode: `inline sequential`
- Coordination: `git-tracked`
- Required skills: `skill-backend-verification`, `skill-code-standards`
- Preauthorized local actions: edit fixture-owned files and run listed checks.
- User-approval actions: commit, push, merge.
- Parallel ownership: `none`; one task at a time.

## Coordination State

| Task | State | Workspace | Executor | Depends On | Required Proof | Evidence |
| --- | --- | --- | --- | --- | --- | --- |
| Task 1 | `completed` | current | `deepagents` | none | fixture prerequisite proof | recorded |
| Task 2 | `completed` | current | `deepagents` | none | second prerequisite proof | recorded |
| Task 3 | `active` | current | `deepagents` | none | one-command proof | pending |
| Task 4 | `active` | current | `deepagents` | Task 1 | one-prerequisite proof | pending |
| Task 5 | `active` | current | `deepagents` | Tasks 1-2 | two-prerequisite proof | pending |
| Task 6 | `active` | current | `deepagents` | none | multi-command proof | pending |
| Task 7 | `active` | current | `deepagents` | Task 1 | shared-constraint proof | pending |
| Task 8 | `active` | current | `deepagents` | Tasks 1-2 | multi-file proof | pending |

## Task Breakdown

### Task 1: Seed fixture state

**Template Profile:**
- Controller-selected: `normal`

**Verification:**
- `python -c "print('fixture prerequisite one')"`

### Task 2: Seed second fixture state

**Template Profile:**
- Controller-selected: `normal`

**Verification:**
- `python -c "print('fixture prerequisite two')"`

### Task 3: Local one-command task

**Purpose:** Update one local fixture file.

**Template Profile:**
- Controller-selected: `normal`

**Files And Symbols:**
- Modify: `tests/fixtures/worker_contract_benchmark/local.txt`

**Required Change:**
- Write exactly `worker-task-3-complete` to `tests/fixtures/worker_contract_benchmark/local.txt`.

**Verification:**
- `python -c "print('local proof')"`

**Exit Criteria:**
- Local fixture change is verified.

**Authority:**
- Preauthorized local actions: edit `tests/fixtures/worker_contract_benchmark/local.txt`.
- Stop for: failed proof.

### Task 4: One-prerequisite task

**Purpose:** Update one dependent fixture file.

**Template Profile:**
- Controller-selected: `normal`

**Files And Symbols:**
- Modify: `tests/fixtures/worker_contract_benchmark/dependent.txt`

**Required Change:**
- Write exactly `worker-task-4-complete` to `tests/fixtures/worker_contract_benchmark/dependent.txt`.

**Verification:**
- `python -c "print('dependent proof')"`

**Exit Criteria:**
- Dependent fixture change is verified.

**Authority:**
- Preauthorized local actions: edit `tests/fixtures/worker_contract_benchmark/dependent.txt`.
- Stop for: failed proof.

### Task 5: Two-prerequisite task

**Purpose:** Update a fixture after two accepted prerequisites.

**Template Profile:**
- Controller-selected: `normal`

**Files And Symbols:**
- Modify: `tests/fixtures/worker_contract_benchmark/two-prereq.txt`

**Required Change:**
- Write exactly `worker-task-5-complete` to `tests/fixtures/worker_contract_benchmark/two-prereq.txt`.

**Verification:**
- `python -c "print('two prerequisite proof')"`

**Exit Criteria:**
- Two-prerequisite fixture change is verified.

**Authority:**
- Preauthorized local actions: edit `tests/fixtures/worker_contract_benchmark/two-prereq.txt`.
- Stop for: failed proof.

### Task 6: Multi-command task

**Purpose:** Update one fixture and prove both checks.

**Template Profile:**
- Controller-selected: `normal`

**Files And Symbols:**
- Modify: `tests/fixtures/worker_contract_benchmark/multi-command.txt`

**Required Change:**
- Write exactly `worker-task-6-complete` to `tests/fixtures/worker_contract_benchmark/multi-command.txt`.

**Verification:**
- `python -c "print('multi proof one')"`
- `python -c "print('multi proof two')"`

**Exit Criteria:**
- Both verification commands pass.

**Authority:**
- Preauthorized local actions: edit `tests/fixtures/worker_contract_benchmark/multi-command.txt`.
- Stop for: failed proof.

### Task 7: Shared-constraint task

**Purpose:** Update one fixture under explicit shared constraints.

**Template Profile:**
- Controller-selected: `normal`

**Files And Symbols:**
- Modify: `tests/fixtures/worker_contract_benchmark/constrained.txt`

**Required Change:**
- Write exactly `worker-task-7-complete` to `tests/fixtures/worker_contract_benchmark/constrained.txt`.

**Verification:**
- `python -c "print('constraint proof')"`

**Exit Criteria:**
- Constraint fixture change is verified.

**Authority:**
- Preauthorized local actions: edit `tests/fixtures/worker_contract_benchmark/constrained.txt`.
- Stop for: failed proof.

### Task 8: Multi-file task

**Purpose:** Update two related fixture files.

**Template Profile:**
- Controller-selected: `normal`

**Files And Symbols:**
- Modify: `tests/fixtures/worker_contract_benchmark/multi-a.txt` and `tests/fixtures/worker_contract_benchmark/multi-b.txt`

**Required Change:**
- Write exactly `worker-task-8-a-complete` to `tests/fixtures/worker_contract_benchmark/multi-a.txt`.
- Write exactly `worker-task-8-b-complete` to `tests/fixtures/worker_contract_benchmark/multi-b.txt`.

**Verification:**
- `python -c "print('multi-file proof')"`

**Exit Criteria:**
- Both fixture files stay within allowed scope.

**Authority:**
- Preauthorized local actions: edit `tests/fixtures/worker_contract_benchmark/multi-a.txt` and `tests/fixtures/worker_contract_benchmark/multi-b.txt`.
- Stop for: failed proof.

## Verification

Fixture verification is task-local and recorded by benchmark harness.
