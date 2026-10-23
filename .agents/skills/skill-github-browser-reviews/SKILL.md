---
name: skill-github-browser-reviews
description: Use only when the user explicitly requests this skill for a GitHub review through a normal ChatGPT browser tab with `@GitHub`.
required_reads: []
distribution_tier: starter_kit
---

# GitHub Browser Reviews

## Role

Use this skill only after the user explicitly invokes it by name or explicitly
requests the GitHub Browser Reviews workflow. It defines the preparation, request, and evidence
rules for a read-only review; it does not modify files, merge changes, or
replace repository ownership and branch controls.

## When to Use

Use only when the user explicitly requests this skill or workflow, for example:

- `$skill-github-browser-reviews`;
- "Use the GitHub Browser Reviews skill";
- an equivalent explicit request naming this skill and asking for a GitHub browser-tab review.

Do not activate this skill merely because:

- a plan, code change, or pull request needs review;
- the task mentions GitHub or asks to open, review, or merge a pull request;
- the review can read a committed revision from GitHub.

Use the applicable review or pull-request skill instead when this skill was not
explicitly requested.

Do not use a local Windows path as the only review source. If the requested revision is
not available on GitHub, report `incomplete` or `blocked` instead of claiming
that the review inspected local state.

## Non-Negotiable Invariants

1. **Explicit-invocation invariant:** Do not use this skill unless the user
   explicitly requested it by name or explicitly requested its workflow.
2. **Publication invariant:** Commit and push the selected plan or code changes
   to the intended branch before opening the review.
3. **Revision invariant:** Give the reviewer an exact branch or commit and an
   exact file URL. The review request must include the file path or GitHub file URL.
   Pin URLs to a commit when reproducibility matters.
4. **Browser invariant:** Use a normal ChatGPT browser tab and invoke `@GitHub`.
5. **Model invariant:** Let the user select either `GPT-5.6-Sol` or `GPT-6`.
6. **Reasoning invariant:** Let the user select `instant`, `medium`, or `high`
   and preserve that choice in the review request.
7. **Scope invariant:** Keep the request read-only and identify the stable
   context, repository, revision, file path, and review question.
8. **Evidence invariant:** Require the reviewer to cite a known heading, hash,
   or other file marker from the requested revision.
9. **Privacy invariant:** Do not include credentials, environment values,
   private instructions, or unrelated repository contents in the request.

## Review Procedure

### 1. Prepare the revision

Inspect the selected changes locally, then commit and push them to the intended
branch. Record the repository, branch, commit, and file paths used for review.
The review request must identify the repository and exact branch or commit. Do
not start the review until the pushed revision is reachable from GitHub.

### 2. Select the model and reasoning level

Before opening the review, let the user choose one model and one reasoning
level. The supported choices are:

- `GPT-5.6-Sol` or `GPT-6`;
- `instant`, `medium`, or `high` reasoning.

Record the selected values and carry them into the review request unchanged.

### 3. Open the review

Open a normal ChatGPT browser tab and invoke `@GitHub`. Keep the browser-tab request compact
and provide only the exact revision, read-only scope, stable context identifier,
and one review question.

Use this shape:

```text
@GitHub Review this exact file revision:
https://github.com/<owner>/<repo>/blob/<commit-or-branch>/<path>

Scope: read-only review of the selected revision.
Context: <stable review or work-item identifier>
Model: <GPT-5.6-Sol|GPT-6>
Reasoning: <instant|medium|high>
Question: <one precise review question>

Return findings ordered by severity and do not modify files.
```

### 4. Keep the request bounded

Do not paste the current chat transcript, system or developer instructions,
tool schemas, environment blocks, attachments, or transport wrappers. Do not
include credentials. Do not include unrelated repository contents. Those are
outer execution context, not review input. If the request is too large, rebuild it
with the exact GitHub URL and the smallest sufficient scope; do not blindly
retry a bloated request.

### 5. Verify review evidence

The reviewer must confirm that it read the requested revision by citing a known
heading, hash, file marker, or equivalent evidence before the review is accepted.
A URL being present, or a response that discusses the topic without revision
evidence, is not proof that the requested file was reviewed.

### 6. Handle unavailable revisions

Report `incomplete` or `blocked` when:

- the selected changes cannot be committed and pushed;
- the repository or revision is inaccessible to the reviewer;
- the review requires uncommitted local state;
- the reviewer cannot confirm the requested revision.

State the exact missing condition and do not substitute a local-only claim.

## Evidence Checklist

Before reporting success, record:

- repository, intended branch, and exact commit;
- successful push evidence and the reviewed file URL;
- read-only scope, stable context identifier, and review question;
- the heading, hash, or file marker cited by the reviewer;
- findings ordered by severity;
- any skipped checks or unavailable review evidence.

## Completion Result

Return one of:

- **verified:** the intended GitHub revision was pushed, read, and evidenced;
- **incomplete:** the review or evidence remains unfinished within scope;
- **blocked:** access, publication, or revision evidence requires an external
  action or user decision.

State the exact failed claim and evidence for `incomplete` or `blocked`.
