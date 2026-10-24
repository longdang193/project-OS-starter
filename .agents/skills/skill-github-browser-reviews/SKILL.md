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
4. **Browser invariant:** Prefer the Node/Playwright automation runner as the
   primary execution path. It must own the authenticated browser context and
   invoke `@GitHub` through the visible UI. Use CDP attachment only when a
   TCP CDP endpoint is explicitly available. A pipe-backed Playwright MCP
   browser has no TCP CDP endpoint; do not attempt to attach the standalone
   CLI to it. Use ChromeDev only for session attachment or low-level
   diagnostics when the primary runner cannot operate.
5. **Model invariant:** Let the user select either `GPT-5.6-Sol` or `GPT-6`.
6. **Reasoning invariant:** Let the user select `Instant`, `Medium`, or `High`
   and preserve that choice in the review request.
7. **Scope invariant:** Keep the request read-only and identify the stable
   context, repository, revision, file path, and review question.
8. **Evidence invariant:** Require the reviewer to cite a known heading, hash,
   or other file marker from the requested revision.
9. **Privacy invariant:** Do not include credentials, environment values,
   private instructions, or unrelated repository contents in the request.
10. **Rerun-authorization invariant:** Do not rerun, retry, resubmit, or open a
    replacement for a requested GitHub review unless the user explicitly orders
    that review to be rerun. An incomplete, stale, interrupted, or inconclusive
    review is not permission to start another one.

### ChatGPT Web selector semantics

ChatGPT Web exposes a `Select ChatGPT model` button. Open it to reveal model
radio items and a `Power` thinking-effort control. The effort is displayed as
`Instant`, `Medium`, or `High`; use the control's left/right keys rather than
dragging the overlapping visual thumb. Record the selected model and effort
exactly as displayed.

Use the visible selected state as the authority. Treat model selection and
thinking effort as separate controls and verify them separately. A generic
`Locked`, `Usage limit reached`, or similar banner is unscoped evidence unless
the visible UI attaches it to a specific model item or the specific effort
control. Never attribute that banner to a model merely because it appears
near the model list, and never treat it as account-wide model unavailability.

For the requested model, verify the visible radio item's checked/selected
state and inspect only the same item's visible disabled, locked, or error
state. A click timeout, pointer interception, unchanged page, or failure to
click an overlapping control does not prove that the model is locked. If the
requested model remains visibly selectable but an unscoped banner is present,
record the banner as an unscoped selector warning and continue only when the
requested model and effort are both visibly verified. If either value is not
verified, report it as unverified or incomplete rather than guessing the
cause.

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
- `Instant`, `Medium`, or `High` response mode.

Use this bounded interaction sequence:

1. Click the visible `Select ChatGPT model` button.
2. Select the requested visible model radio item.
3. Focus the visible `Power` control and press left or right until the
   requested effort is displayed.
4. Verify that the selected model radio item and effort label visibly match
   the request.

If the model remains unchanged after one normal click and one bounded
visible-item fallback, stop as `incomplete` unless the requested model item is
visibly marked disabled or locked; a failed click alone is not a lock signal.
Likewise, do not treat a generic usage-limit banner as a model failure unless
the UI visibly associates it with that model item. Do not use force-click
loops, repeated resubmissions, or hidden DOM state to claim selection. Record
any unscoped banner separately from model availability. Only after both the
model radio item and the effort control are visibly verified may the review
request be submitted.

For repeatable browser automation, use the page-bound helper at
`scripts/select-review-model.mjs`:

```js
import { selectReviewModel } from "./scripts/select-review-model.mjs";

await selectReviewModel(page, {
  model: "GPT-6",
  effort: "High"
});
```

The helper accepts an existing authenticated Playwright `page`; it does not
launch a browser, authenticate, submit a review, inspect hidden state, or retry
indefinitely. If it cannot visibly confirm the requested model and effort, stop
the review as `incomplete` or `blocked`.

The model selector may open on the thinking-effort subview, leaving stale model
rows in the DOM while the visible `Medium`/`High` power control covers them.
Navigate through the visible `Select model` control before locating a model;
then click a safe point in the upper part of the requested row, use real
Playwright hit-testing, and verify `aria-checked` afterward. Do not replace
that click with `element.click()`, `force`, or hidden-state inspection: pointer
interception is a selector failure, not evidence that the model is locked.
Match the model label separately from nearby status or usage-banner text.

For an explicitly authorized end-to-end prompt submission, use
`scripts/run-review-prompt.mjs`. It navigates an existing authenticated page
to ChatGPT, selects and verifies the model and effort, fills the prompt, and
submits it once. `openReviewTab(context)` and
`runReviewPromptInNewTab(context, options)` can create a tab from an existing
authenticated Playwright context; they do not launch a browser or
authenticate. The submission helper never retries or reruns a review request;
the completion helper only observes visible completion signals and returns the
  final visible assistant turn for the caller to record.

### Helper execution boundary

These `.mjs` helpers run in the Node/Playwright runner, not in the ChatGPT page
context. Do not import them from `page.evaluate` or another inline browser
snippet; page evaluation cannot resolve workspace modules. Load them through
the runner's file-backed entry point instead:

```js
import { runReviewPromptInNewTab } from "./.agents/skills/skill-github-browser-reviews/scripts/run-review-prompt.mjs";

const { page } = await runReviewPromptInNewTab(context, {
  model: "GPT-6",
  effort: "High",
  prompt: reviewPrompt
});
```

The runner must either own or receive an already authenticated Playwright
`context`. The CLI's `--user-data-dir` mode creates the owned context; the
library helpers and `--cdp-endpoint` mode require the caller to provide one.
Use a browser tool's `filename` or `sourcePath` option only when it supports
file-backed Node execution. If the helper cannot be loaded or the authenticated
context cannot be created or attached, report `incomplete` or `blocked`; do not
replace the helper with hidden DOM or network-state inspection. Prompt submission remains gated by the explicit user authorization required by this
skill.

For a standalone, repeatable Node invocation, use the ESM CLI entrypoint rather
than evaluating the `.mjs` module as a browser VM script. The primary mode
launches a visible Playwright browser with a dedicated authenticated profile:

```bash
node .agents/skills/skill-github-browser-reviews/scripts/run-review-prompt-cli.mjs \
  --user-data-dir <authenticated-playwright-profile> \
  --model GPT-6 \
  --effort High \
  --prompt-file <review-prompt.txt> \
  --output-dir <review-output-directory>
```

One normal invocation is one bounded review transaction. It selects and visibly
verifies the requested model and effort, submits at most once, waits for a new
stable visible assistant turn, writes `response.md` and a small `result.json`,
and only then closes the owned browser context. Terminal runner results are
`completed`, `incomplete`, or `blocked`; a nonzero exit code accompanies the
last two. The controller, not the runner, validates revision-specific review
evidence and may classify the overall workflow as `verified`. The runner never
retries or silently recovers a failed submission.

For multiple reviews, keep the same transaction boundary but call the
CLI module's `openReviewContext(options)` once, then call
`runReviewBatch({ attached, reviews, outputDir })` from the Node controller. It
reuses one authenticated context for sequential reviews—including repeated
reviews with the same model—allocates a separate
`run-*` output directory per review, closes each review page after its artifacts
are persisted, and closes the shared context once at the end. Do not add a
keep-open flag or a second browser lifecycle owner. The optional `--batch-file`
manifest is the standalone entry point for this mode. Persistent-profile mode
holds an exclusive profile lease for the lifetime of the owned context, so
overlapping launches fail before opening a second browser. If a review reports
that the shared context is unusable, the controller stops the batch and closes
the context rather than attempting later reviews against a broken session.

When a TCP CDP endpoint is explicitly available, `--cdp-endpoint` remains an
optional attach mode and `--context-index` selects its browser context. The
CLI imports `run-review-prompt.mjs` through Node's ESM loader and submits
exactly once. It never authenticates
a profile for the user. A pipe-backed Playwright MCP browser cannot be used
with `--cdp-endpoint`; use the owned-profile mode or MCP directly.
`browser_run_code_unsafe` is not an ESM module runner; do not pass this CLI or
either `.mjs` helper to that VM as a raw file.

### 3. Open the review

Run the Node/Playwright automation path first to open or control an authenticated
normal Chrome/Edge ChatGPT Web tab and invoke `@GitHub` through the visible UI.
If the owned-profile runner cannot create or use the required session, report
`incomplete` or `blocked`; use ChromeDev only for low-level diagnostics. Keep
the browser request compact and provide only the exact revision, read-only
scope, stable context identifier, and one review question.
Use visible page state as the authority for model, response mode, completion,
and interruption status; do not infer these from hidden DOM or transport
metadata.

Use this shape, with every GitHub URL pinned to the expected full commit SHA:

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

Keep the browser-tab request compact and provide only the exact revision,
read-only scope, stable context identifier, and one review question.

Do not paste the current chat transcript, system or developer instructions,
tool schemas, environment blocks, attachments, or transport wrappers. Do not
include credentials. Do not include unrelated repository contents. Those are
outer execution context, not review input. If the request is too large, rebuild it
with the exact GitHub URL and the smallest sufficient scope; do not blindly
retry a bloated request.

### 5. Verify review evidence

The reviewer should confirm that it read the requested revision by citing a
known heading, hash, file marker, or equivalent evidence before the review is
accepted. The runner records the completed response and conversation identity;
the caller remains responsible for judging file-specific review evidence.

### 6. Handle unavailable revisions

Report `incomplete` or `blocked` when:

- the selected changes cannot be committed and pushed;
- the repository or revision is inaccessible to the reviewer;
- the review requires uncommitted local state;
- the reviewer cannot confirm the requested revision.

State the exact missing condition and do not substitute a local-only claim.

### 7. Rerun only on explicit order

If the review is incomplete, interrupted, stale, inconclusive, or otherwise
missing required evidence, stop and report the exact condition. Do not
automatically rerun it, retry the same request, submit a replacement request,
or open another browser review. Continue only after the user explicitly orders
the requested GitHub review to be rerun; a general request to continue, fix,
review, or implement is not sufficient unless it explicitly authorizes the
rerun.

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
