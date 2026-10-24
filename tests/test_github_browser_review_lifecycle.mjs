import assert from "node:assert/strict";
import { mkdtemp, readFile, rm } from "node:fs/promises";
import { tmpdir } from "node:os";
import { join } from "node:path";
import test from "node:test";

import {
  ASSISTANT_TURN_SELECTOR,
  INTERRUPTION_PATTERN,
  INTERRUPTION_UI_SELECTOR,
  evaluateReviewCompletion,
  isPromptVisibleInComposer,
  openReviewTab,
  readVisibleInterruption,
  runReviewPromptInNewTab,
} from "../.agents/skills/skill-github-browser-reviews/scripts/run-review-prompt.mjs";
import {
  atomicWrite,
  acquireProfileLease,
  closeContext,
  createResult,
  createRunOutputDirectory,
  persistCleanupFailure,
  parseArguments,
  releaseProfileLease,
  runReviewTransaction,
  runReviewBatch,
  writeResult,
} from "../.agents/skills/skill-github-browser-reviews/scripts/run-review-prompt-cli.mjs";
import {
  findModelOption,
  openModelList,
  selectReviewModel,
} from "../.agents/skills/skill-github-browser-reviews/scripts/select-review-model.mjs";

test("normal CLI arguments keep the runner contract small", () => {
  const parsed = parseArguments([
    "--user-data-dir", "profile",
    "--model", "GPT-6",
    "--effort", "High",
    "--prompt-file", "prompt.md",
  ]);

  assert.equal(parsed.model, "GPT-6");
  assert.equal(parsed.effort, "High");
  assert.equal(parsed.promptFile, "prompt.md");
  assert.equal(parsed.outputDir, "review-output");
  assert.equal(parsed.expectedSha, undefined);
  assert.equal(parsed.expectedMarker, undefined);
});

test("output directory remains optional for controller-allocated review artifacts", () => {
  const parsed = parseArguments([
    "--cdp-endpoint", "http://127.0.0.1:1",
    "--model", "GPT-6",
    "--effort", "High",
    "--prompt-file", "review.md",
    "--output-dir", "review-output",
  ]);

  assert.equal(parsed.promptFile, "review.md");
  assert.equal(parsed.outputDir, "review-output");
});

test("batch arguments select one shared browser session", () => {
  const parsed = parseArguments([
    "--user-data-dir", "profile",
    "--batch-file", "reviews.json",
  ]);

  assert.equal(parsed.batchFile, "reviews.json");
  assert.equal(parsed.model, undefined);
  assert.equal(parsed.effort, undefined);
  assert.equal(parsed.promptFile, undefined);
});

test("runner contract uses completed as its successful terminal state", async () => {
  const runner = await readFile(
    new URL("../.agents/skills/skill-github-browser-reviews/scripts/run-review-prompt-cli.mjs", import.meta.url),
    "utf8",
  );

  assert.match(runner, /result\.status = "completed"/);
  assert.match(runner, /return result\.status === "completed" \? 0 : 1/);
  assert.doesNotMatch(runner, /result\.status = "verified"/);
});

test("review transaction uses the caller-owned context instead of launching another browser", async () => {
  const runner = await readFile(
    new URL("../.agents/skills/skill-github-browser-reviews/scripts/run-review-prompt-cli.mjs", import.meta.url),
    "utf8",
  );
  const transaction = runner.slice(runner.indexOf("export async function runReviewTransaction"), runner.indexOf("export async function runReviewBatch"));

  assert.match(transaction, /runPrompt\(context/);
  assert.match(transaction, /prompt: options\.prompt/);
  assert.doesNotMatch(transaction, /loadPlaywright\(\)/);
  assert.doesNotMatch(transaction, /openContext\(/);
});

test("model selection keeps the simple picker view when model radios are visible", async () => {
  let modelControlClicked = false;
  const menu = {
    locator(selector) {
      assert.equal(selector, '[role="menuitemradio"]:visible');
      return {
        count: async () => 2,
        first() {
          return { click: async () => {} };
        },
      };
    },
    getByRole() {
      return {
        first() {
          return this;
        },
        async count() {
          return 1;
        },
        async isVisible() {
          return true;
        },
        async click() {
          modelControlClicked = true;
        },
      };
    },
  };

  await openModelList(menu);

  assert.equal(modelControlClicked, false);
});

test("model selection opens the model view when visible radios are covered", async () => {
  let reopened = false;
  const modelOptions = {
    count: async () => 2,
    first() {
      return {
        async click(options) {
          assert.equal(options.trial, true);
          throw new Error("effort view intercepts pointer events");
        },
      };
    },
  };
  const menu = {
    locator(selector) {
      assert.equal(selector, '[role="menuitemradio"]:visible');
      return modelOptions;
    },
  };
  const reopenedMenu = { reopened: true };

  const result = await openModelList(menu, {
    reopen: async () => {
      reopened = true;
      return reopenedMenu;
    },
  });

  assert.equal(reopened, true);
  assert.equal(result, reopenedMenu);
});

test("model selection reopens when the requested model row is covered", async () => {
  let reopened = false;
  const modelOptions = {
    count: async () => 2,
    nth(index) {
      return {
        async innerText() {
          return index === 0 ? "GPT-6" : "GPT-5.6 Sol";
        },
        async click(options) {
          assert.equal(options.trial, true);
          if (index === 1) throw new Error("effort view intercepts requested row");
        },
      };
    },
    first() {
      return this.nth(0);
    },
  };
  const menu = {
    locator(selector) {
      assert.equal(selector, '[role="menuitemradio"]:visible');
      return modelOptions;
    },
  };
  const reopenedMenu = { reopened: true };

  const result = await openModelList(menu, {
    model: "GPT-5.6-Sol",
    reopen: async () => {
      reopened = true;
      return reopenedMenu;
    },
  });

  assert.equal(reopened, true);
  assert.equal(result, reopenedMenu);
});

test("model selection reopens when the real requested-row click is intercepted", async () => {
  let menuVisible = false;
  let firstClick = true;
  let selected = false;
  const radioOptions = {
    count: async () => 2,
    nth(index) {
      return {
        async innerText() {
          return index === 0 ? "GPT-6" : "GPT-5.6 Sol";
        },
        async getAttribute(name) {
          assert.equal(name, "aria-checked");
          return index === 1 && selected ? "true" : "false";
        },
        async click(options = {}) {
          if (options.trial) return;
          if (firstClick) {
            firstClick = false;
            throw new Error("real click intercepted");
          }
          selected = true;
        },
      };
    },
    first() {
      return this.nth(0);
    },
  };
  const menu = {
    async isVisible() {
      return menuVisible;
    },
    async waitFor({ state }) {
      if (state === "hidden") menuVisible = false;
      if (state === "visible") menuVisible = true;
    },
    locator(selector) {
      if (selector === '[role="menuitemradio"]:visible') return radioOptions;
      if (selector === '[role="status"]') {
        return {
          first() {
            return {
              async isVisible() {
                return true;
              },
              async innerText() {
                return "High";
              },
            };
          },
        };
      }
      throw new Error(`Unexpected locator: ${selector}`);
    },
    getByRole(role, options = {}) {
      if (role === "menuitem" && options.name === "Select model") {
        return {
          first() {
            return {
              async isVisible() {
                return false;
              },
            };
          },
        };
      }
      if (role === "menuitem" && options.name === "Power") {
        return {
          first() {
            return {
              async isVisible() {
                return true;
              },
              async focus() {},
              async press() {},
            };
          },
        };
      }
      throw new Error(`Unexpected menu role lookup: ${role}`);
    },
  };
  const page = {
    getByRole(role, options = {}) {
      if (role === "menu") {
        return { first: () => menu };
      }
      if (role === "button" && options.name === "Select ChatGPT model") {
        return {
          first() {
            return {
              async waitFor() {},
              async click() {
                menuVisible = true;
              },
            };
          },
        };
      }
      throw new Error(`Unexpected page role lookup: ${role}`);
    },
    keyboard: {
      async press(key) {
        assert.equal(key, "Escape");
        menuVisible = false;
      },
    },
  };

  await selectReviewModel(page, { model: "GPT-5.6-Sol", effort: "High" });
  assert.equal(selected, true);
});

test("completion requires a new stable visible assistant turn and conversation", () => {
  assert.equal(evaluateReviewCompletion({
    assistantText: "Finding: src/example.js:12 uses the requested revision.",
    assistantTurnCount: 2,
    baselineAssistantTurnCount: 1,
    composerReady: true,
    conversationId: "conversation-1",
    generating: false,
    interrupted: false,
    responseActionsReady: true,
    stableSampleCount: 2,
  }), true);

  assert.equal(evaluateReviewCompletion({
    assistantText: "Finding",
    assistantTurnCount: 2,
    baselineAssistantTurnCount: 1,
    composerReady: true,
    conversationId: null,
    generating: false,
    interrupted: false,
    responseActionsReady: true,
    stableSampleCount: 2,
  }), false);

  assert.equal(evaluateReviewCompletion({
    assistantText: "Finding",
    assistantTurnCount: 1,
    baselineAssistantTurnCount: 1,
    composerReady: true,
    conversationId: "conversation-1",
    generating: false,
    interrupted: false,
    responseActionsReady: true,
    stableSampleCount: 2,
  }), false);

  assert.equal(evaluateReviewCompletion({
    assistantText: "I’ll verify the exact commit before reviewing it.",
    assistantTurnCount: 2,
    baselineAssistantTurnCount: 1,
    composerReady: true,
    conversationId: "conversation-1",
    generating: false,
    interrupted: false,
    responseActionsReady: false,
    stableSampleCount: 2,
  }), false);
});

test("assistant fallback excludes rich-text user turns", () => {
  assert.match(ASSISTANT_TURN_SELECTOR, /data-message-author-role="assistant"/);
  assert.match(ASSISTANT_TURN_SELECTOR, /:not\(/);
  assert.doesNotMatch(ASSISTANT_TURN_SELECTOR, /,\s*main/);
});

test("interruption detection ignores ordinary assistant text containing try again", () => {
  assert.equal(INTERRUPTION_PATTERN.test("You can try again with a narrower question."), false);
  assert.equal(INTERRUPTION_PATTERN.test("Something went wrong. Please try again."), true);
});

test("interruption detection reads only dedicated visible error UI", async () => {
  let requestedSelector;
  const page = {
    locator(selector) {
      requestedSelector = selector;
      return {
        first() {
          return this;
        },
        async count() {
          return 0;
        },
        async isVisible() {
          return false;
        },
      };
    },
  };

  assert.equal(await readVisibleInterruption(page), false);
  assert.equal(requestedSelector, INTERRUPTION_UI_SELECTOR);
});

test("model lookup requires an exact visible label", async () => {
  const options = [
    { text: "GPT-6 Preview", checked: "false" },
    { text: "GPT-6", checked: "true" },
  ];
  const menu = {
    locator(selector) {
      assert.equal(selector, '[role="menuitemradio"]:visible');
      return {
        async count() {
          return options.length;
        },
        nth(index) {
          return {
            async innerText() {
              return options[index].text;
            },
            async getAttribute(name) {
              return name === "aria-checked" ? options[index].checked : null;
            },
          };
        },
      };
    },
  };

  const option = await findModelOption(menu, "GPT-6");
  assert.equal(await option.innerText(), "GPT-6");
});

test("review tab closes when authenticated composer setup fails", async () => {
  let closed = false;
  const page = {
    url: () => "https://chatgpt.com/",
    getByRole() {
      return {
        first() {
          return this;
        },
        async isVisible() {
          return false;
        },
      };
    },
    async close() {
      closed = true;
    },
  };

  await assert.rejects(
    openReviewTab({ newPage: async () => page }),
    /Authenticated ChatGPT composer was not found/,
  );
  assert.equal(closed, true);
});

test("review tab closes when model preparation fails after newPage", async () => {
  let closed = false;
  const composer = { async isVisible() { return true; } };
  const page = {
    url: () => "https://chatgpt.com/",
    getByRole(role, options = {}) {
      if (role === "textbox") return { first() { return composer; } };
      if (role === "menu") {
        return {
          first() {
            return {
              async isVisible() { return false; },
              async waitFor() { throw new Error("model menu did not open"); },
            };
          },
        };
      }
      if (role === "button" && options.name === "Select ChatGPT model") {
        return {
          first() {
            return {
              async waitFor() {},
              async click() {},
            };
          },
        };
      }
      throw new Error(`Unexpected role lookup: ${role}`);
    },
    async close() {
      closed = true;
    },
  };

  await assert.rejects(
    runReviewPromptInNewTab(
      { newPage: async () => page },
      { model: "GPT-6", effort: "High", prompt: "review" },
    ),
    /model menu did not open/,
  );
  assert.equal(closed, true);
});

test("prompt entry validation reads the composer value", async () => {
  const prompt = "@GitHub Review https://github.com/longdang193/project-OS-starter";
  const composer = {
    async inputValue() {
      return prompt;
    },
    async innerText() {
      return "";
    },
  };

  assert.equal(await isPromptVisibleInComposer(composer, prompt), true);
});

test("prompt entry validation tolerates rich-link whitespace in contenteditable composers", async () => {
  const prompt = "@GitHub Review https://github.com/longdang193/project-OS-starter";
  const composer = {
    async inputValue() {
      throw new Error("not an input element");
    },
    async innerText() {
      return "@GitHub Review \nhttps://github.com/longdang193/project-OS-starter\n\n";
    },
  };

  assert.equal(await isPromptVisibleInComposer(composer, prompt), true);
});

test("result records the requested and observed lifecycle state", () => {
  const result = createResult({ model: "GPT-5.6-Sol", effort: "High" });

  assert.deepEqual(result, {
    status: "running",
    run_id: null,
    model_requested: "GPT-5.6-Sol",
    model_verified: null,
    effort_requested: "High",
    effort_verified: null,
    submission_attempted: false,
    submission: "not_started",
    completion: "not_started",
    conversation_url: null,
    conversation_id: null,
    assistant_message_id: null,
    assistant_turn_index: null,
    response_path: "response.md",
    cleanup_status: "not_started",
    cleanup_warning: null,
    failure_scope: null,
    failure_stage: null,
    failure_reason: null,
  });
});

test("page cleanup failure makes a completed transaction incomplete", async () => {
  const parent = await mkdtemp(join(tmpdir(), "github-review-page-cleanup-"));
  try {
    const result = await runReviewTransaction({}, {
      effort: "High",
      model: "GPT-6",
      outputDir: parent,
      prompt: "review",
      dependencies: {
        runReviewPromptInNewTab: async () => ({
          effort: "High",
          model: "GPT-6",
          page: {
            async close() {
              throw new Error("page close failed");
            },
          },
          promptSubmitted: true,
          submission: "acknowledged",
        }),
        waitForReviewCompletion: async () => ({
          assistantMessageId: "assistant-1",
          assistantTurnIndex: 1,
          conversationId: "review",
          currentUrl: "https://chatgpt.com/c/review",
          response: "response",
          status: "confirmed",
        }),
      },
    });

    assert.equal(result.status, "incomplete");
    assert.equal(result.cleanup_status, "failed");
    assert.equal(result.cleanup_warning, "page close failed");
  } finally {
    await rm(parent, { recursive: true, force: true });
  }
});

test("result and response writes are atomic and preserve final evidence", async () => {
  const outputDir = await mkdtemp(join(tmpdir(), "github-review-runner-"));
  try {
    const result = createResult({ model: "GPT-6", effort: "High" });
    result.status = "completed";
    result.submission = "acknowledged";
    result.completion = "confirmed";

    await writeResult(outputDir, result);
    await atomicWrite(join(outputDir, "response.md"), "Finding at line 12.\n");

    assert.equal(JSON.parse(await readFile(join(outputDir, "result.json"), "utf8")).status, "completed");
    assert.equal(await readFile(join(outputDir, "response.md"), "utf8"), "Finding at line 12.\n");
  } finally {
    await rm(outputDir, { recursive: true, force: true });
  }
});

test("cleanup failures are persisted after a completed transaction", async () => {
  const outputDir = await mkdtemp(join(tmpdir(), "github-review-cleanup-"));
  try {
    const result = createResult({ model: "GPT-6", effort: "High" });
    result.status = "completed";
    result.completion = "confirmed";
    await writeResult(outputDir, result);

    await persistCleanupFailure(result, outputDir, "context close failed");

    const persisted = JSON.parse(await readFile(join(outputDir, "result.json"), "utf8"));
    assert.equal(persisted.status, "incomplete");
    assert.equal(persisted.failure_stage, "cleanup");
    assert.equal(persisted.failure_reason, "context close failed");
  } finally {
    await rm(outputDir, { recursive: true, force: true });
  }
});

test("attached cleanup closes the page and disconnects without closing the context", async () => {
  const events = [];
  await closeContext({
    browser: { async close() { events.push("browser-close"); } },
    context: { async close() { events.push("context-close"); } },
    ownsContext: false,
    page: { async close() { events.push("page-close"); } },
  });

  assert.deepEqual(events, ["page-close", "browser-close"]);
});

test("owned persistent cleanup closes the context exactly once", async () => {
  const events = [];
  await closeContext({
    browser: { async close() { events.push("browser-close"); } },
    context: { async close() { events.push("context-close"); } },
    ownsContext: true,
    page: { async close() { events.push("page-close"); } },
  });

  assert.deepEqual(events, ["context-close"]);
});

test("each output allocation creates a distinct run directory", async () => {
  const parent = await mkdtemp(join(tmpdir(), "github-review-runs-"));
  try {
    const first = await createRunOutputDirectory(parent);
    const second = await createRunOutputDirectory(parent);

    assert.notEqual(first.outputDir, second.outputDir);
    assert.notEqual(first.runId, second.runId);
    assert.match(first.outputDir, /run-/);
    assert.match(second.outputDir, /run-/);
  } finally {
    await rm(parent, { recursive: true, force: true });
  }
});

test("review batch reuses one context, isolates runs, and closes the context once", async () => {
  const parent = await mkdtemp(join(tmpdir(), "github-review-batch-"));
  const context = {};
  const attached = {
    browser: null,
    context,
    ownsContext: true,
  };
  const seenContexts = [];
  const seenPages = [];
  const results = [];
  let contextCloseCount = 0;

  attached.context.close = async () => {
    contextCloseCount += 1;
  };

  try {
    const batch = await runReviewBatch({
      attached,
      outputDir: parent,
      reviews: [
        { model: "GPT-5.6-Sol", effort: "High", prompt: "first" },
        { model: "GPT-5.6-Sol", effort: "High", prompt: "second" },
      ],
      runTransaction: async (reviewContext, review) => {
        const allocation = await createRunOutputDirectory(review.outputDir);
        const page = {
          async close() {
            seenPages.push(page);
          },
        };
        seenContexts.push(reviewContext);
        results.push({ outputDir: allocation.outputDir, page });
        await page.close();
        return { outputDir: allocation.outputDir, status: "completed" };
      },
    });

    assert.equal(batch.length, 2);
    assert.deepEqual(seenContexts, [context, context]);
    assert.notEqual(results[0].outputDir, results[1].outputDir);
    assert.equal(seenPages.length, 2);
    assert.equal(contextCloseCount, 1);
  } finally {
    await rm(parent, { recursive: true, force: true });
  }
});

test("review batch persists cleanup failure for completed transactions", async () => {
  const parent = await mkdtemp(join(tmpdir(), "github-review-batch-cleanup-"));
  const attached = {
    browser: null,
    context: {
      async close() {
        throw new Error("context close failed");
      },
    },
    ownsContext: true,
  };
  let result;

  try {
    await assert.rejects(
      runReviewBatch({
        attached,
        outputDir: parent,
        reviews: [{ model: "GPT-6", effort: "High", prompt: "review" }],
        runTransaction: async (reviewContext, review) => {
          const allocation = await createRunOutputDirectory(review.outputDir);
          result = createResult(review);
          result.status = "completed";
          result.output_dir = allocation.outputDir;
          await writeResult(allocation.outputDir, result);
          return result;
        },
      }),
      /context close failed/,
    );

    const persisted = JSON.parse(await readFile(join(result.output_dir, "result.json"), "utf8"));
    assert.equal(persisted.status, "incomplete");
    assert.equal(persisted.failure_stage, "cleanup");
    assert.equal(persisted.failure_reason, "context close failed");
  } finally {
    await rm(parent, { recursive: true, force: true });
  }
});

test("review batch stops after a shared-context failure", async () => {
  const context = {};
  const attached = { browser: null, context, ownsContext: true };
  const attempted = [];
  let closeCount = 0;
  context.close = async () => {
    closeCount += 1;
  };

  const results = await runReviewBatch({
    attached,
    outputDir: "review-output",
    reviews: [
      { model: "GPT-6", effort: "High", prompt: "first" },
      { model: "GPT-6", effort: "High", prompt: "second" },
    ],
    runTransaction: async (_reviewContext, review) => {
      attempted.push(review.prompt);
      if (review.prompt === "first") {
        return { status: "blocked", failure_scope: "shared_context" };
      }
      return { status: "completed" };
    },
  });

  assert.deepEqual(attempted, ["first"]);
  assert.deepEqual(results, [{ status: "blocked", failure_scope: "shared_context" }]);
  assert.equal(closeCount, 1);
});

test("profile lease prevents overlapping persistent-profile launches", async () => {
  const parent = await mkdtemp(join(tmpdir(), "github-review-profile-"));
  const profile = join(parent, "profile");
  try {
    const first = await acquireProfileLease(profile);
    await assert.rejects(acquireProfileLease(profile), /profile is already in use/);
    await releaseProfileLease(first);
    const second = await acquireProfileLease(profile);
    await releaseProfileLease(second);
  } finally {
    await rm(parent, { recursive: true, force: true });
  }
});
