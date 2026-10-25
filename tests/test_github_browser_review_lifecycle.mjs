import assert from "node:assert/strict";
import { mkdtemp, readFile, rm, writeFile } from "node:fs/promises";
import { tmpdir } from "node:os";
import { join, resolve } from "node:path";
import test from "node:test";

import {
  ASSISTANT_TURN_SELECTOR,
  INTERRUPTION_PATTERN,
  INTERRUPTION_UI_SELECTOR,
  evaluateReviewCompletion,
  isPromptVisibleInComposer,
  openReviewTab,
  preflightAuthenticatedContext,
  readVisibleInterruption,
  runReviewPromptInNewTab,
  submitPrompt,
  SUBMISSION_ACK_TIMEOUT_MS,
  SUBMISSION_ACK_POLL_MS,
  waitForReviewCompletion,
} from "../.agents/skills/skill-github-browser-reviews/scripts/run-review-prompt.mjs";
import {
  atomicWrite,
  acquireProfileLease,
  closeContext,
  createResult,
  createRunOutputDirectory,
  installTerminationCleanup,
  main,
  parseArguments,
  readBatchReviews,
  releaseProfileLease,
  runReviewBatch,
  runReviewTransaction,
  summarizeBatchResults,
  writeResult,
} from "../.agents/skills/skill-github-browser-reviews/scripts/run-review-prompt-cli.mjs";
import {
  findModelOption,
  MENU_TRANSITION_TIMEOUT_MS,
  MODEL_MENU_INTERACTION_TIMEOUT_MS,
  UI_ACTION_TIMEOUT_MS,
  openModelList,
  openModelMenu,
  selectReviewModel,
  setEffort,
} from "../.agents/skills/skill-github-browser-reviews/scripts/select-review-model.mjs";

test("model-menu interactions use the bounded five-second timeout", async () => {
  const clickOptions = [];
  const modelControl = {
    async count() {
      return 1;
    },
    async isVisible() {
      return true;
    },
    async click(options) {
      clickOptions.push(options);
    },
  };
  const menu = {
    locator(selector) {
      assert.equal(selector, '[role="menuitemradio"]:visible');
      return { async count() { return 0; } };
    },
    getByRole(role, options) {
      assert.equal(role, "menuitem");
      assert.deepEqual(options, { name: "Select model", exact: true });
      return { first() { return modelControl; } };
    },
  };

  await openModelList(menu, { model: "GPT-6" });

  assert.equal(MODEL_MENU_INTERACTION_TIMEOUT_MS, 5000);
  assert.equal(UI_ACTION_TIMEOUT_MS, 5000);
  assert.equal(MENU_TRANSITION_TIMEOUT_MS, 5000);
  assert.deepEqual(clickOptions, [{ timeout: 5000 }]);
});

test("initial model-menu click uses the bounded UI action timeout", async () => {
  const clickOptions = [];
  const menu = {
    first() {
      return {
        async isVisible() { return false; },
        async waitFor() {},
      };
    },
  };
  const control = {
    first() { return this; },
    async waitFor() {},
    async click(options) { clickOptions.push(options); },
  };
  const page = {
    getByRole(role, options) {
      if (role === "menu") return menu;
      if (role === "button" && options.name === "Select ChatGPT model") return control;
      throw new Error(`Unexpected role lookup: ${role}`);
    },
  };

  await openModelMenu(page);

  assert.deepEqual(clickOptions, [{ timeout: UI_ACTION_TIMEOUT_MS }]);
});

test("prompt submission uses the bounded UI action timeout", async () => {
  const prompt = "review prompt";
  const fillOptions = [];
  const clickOptions = [];
  let submitted = false;
  const composer = {
    async fill(_value, options) { fillOptions.push(options); },
    async inputValue() { return submitted ? "" : prompt; },
    async innerText() { return ""; },
  };
  const sendButton = {
    first() { return this; },
    async isVisible() { return true; },
    async click(options) {
      clickOptions.push(options);
      submitted = true;
    },
  };
  const page = {
    getByRole(role) {
      if (role === "button") return sendButton;
      throw new Error(`Unexpected role lookup: ${role}`);
    },
    async waitForTimeout() {},
  };

  await submitPrompt(page, composer, prompt);

  assert.deepEqual(fillOptions, [{ timeout: 5000 }]);
  assert.deepEqual(clickOptions, [{ timeout: 5000 }]);
});

test("prompt acknowledgement polls once without resubmitting", async () => {
  const prompt = "review prompt";
  let submitted = false;
  let waitCalls = 0;
  const composer = {
    async fill() {},
    async inputValue() { return submitted && waitCalls > 0 ? "" : prompt; },
    async innerText() { return ""; },
  };
  const sendButton = {
    first() { return this; },
    async isVisible() { return true; },
    async click() { submitted = true; },
  };
  const page = {
    getByRole(role) {
      if (role === "button") return sendButton;
      throw new Error(`Unexpected role lookup: ${role}`);
    },
    async waitForTimeout(delay) {
      assert.ok(delay <= SUBMISSION_ACK_POLL_MS);
      assert.ok(delay <= SUBMISSION_ACK_TIMEOUT_MS);
      waitCalls += 1;
    },
  };

  const result = await submitPrompt(page, composer, prompt);
  assert.equal(result.submission, "acknowledged");
  assert.equal(submitted, true);
  assert.equal(waitCalls, 1);
});

test("normal CLI arguments keep the runner contract small", () => {
  const parsed = parseArguments([
    "--user-data-dir", "github-review/project",
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

test("profile arguments require a dedicated project profile path", () => {
  assert.throws(
    () => parseArguments([
      "--user-data-dir", "profile",
      "--model", "GPT-6",
      "--effort", "High",
      "--prompt-file", "review.md",
    ]),
    /dedicated github-review/,
  );
  assert.throws(
    () => parseArguments([
      "--user-data-dir", "C:/Chrome/User Data",
      "--model", "GPT-6",
      "--effort", "High",
      "--prompt-file", "review.md",
    ]),
    /normal Chrome profile/,
  );
});

test("unknown CLI arguments fail before browser setup", () => {
  assert.throws(
    () => parseArguments([
      "--user-data-dir", "github-review/project",
      "--model", "GPT-6",
      "--effort", "High",
      "--prompt-file", "review.md",
      "--outpt-dir", "review-output",
    ]),
    /Unknown argument: --outpt-dir/,
  );
});

test("batch CLI arguments replace single-review arguments", () => {
  const parsed = parseArguments([
    "--user-data-dir", "github-review/project",
    "--batch-file", "reviews.json",
    "--output-dir", "review-output",
  ]);

  assert.equal(parsed.batchFile, "reviews.json");
  assert.equal(parsed.model, undefined);
  assert.equal(parsed.promptFile, undefined);
});

test("batch CLI arguments reject mixed single-review options", () => {
  assert.throws(
    () => parseArguments([
      "--user-data-dir", "github-review/project",
      "--batch-file", "reviews.json",
      "--model", "GPT-6",
    ]),
    /cannot be combined with --batch-file/,
  );
});

test("batch manifest resolves prompt files and validates review entries", async () => {
  const parent = await mkdtemp(join(tmpdir(), "github-review-manifest-"));
  try {
    await writeFile(join(parent, "sol.md"), "first review\n", "utf8");
    await writeFile(join(parent, "gpt6.md"), "second review\n", "utf8");
    const manifestPath = join(parent, "reviews.json");
    await writeFile(manifestPath, JSON.stringify({
      reviews: [
        { model: "GPT-5.6-Sol", effort: "High", prompt_file: "sol.md" },
        { model: "GPT-6", effort: "High", prompt_file: "gpt6.md" },
      ],
    }), "utf8");

    const reviews = await readBatchReviews(manifestPath);

    assert.deepEqual(reviews, [
      {
        model: "GPT-5.6-Sol",
        effort: "High",
        promptFile: join(parent, "sol.md"),
        prompt: "first review\n",
        repository: null,
        commitSha: null,
        reviewUrls: [],
        reviewIndex: 0,
      },
      {
        model: "GPT-6",
        effort: "High",
        promptFile: join(parent, "gpt6.md"),
        prompt: "second review\n",
        repository: null,
        commitSha: null,
        reviewUrls: [],
        reviewIndex: 1,
      },
    ]);
  } finally {
    await rm(parent, { recursive: true, force: true });
  }
});

test("batch summary is completed only when every review completes", () => {
  const summary = summarizeBatchResults([
    { status: "completed", output_dir: "run-a" },
    { status: "incomplete", output_dir: "run-b" },
  ]);

  assert.equal(summary.status, "incomplete");
  assert.equal(summary.review_count, 2);
  assert.equal(summary.completed_count, 1);
  assert.equal(summary.failed_count, 1);
    assert.equal(summary.requested_count, 2);
    assert.equal(summary.attempted_count, 2);
    assert.equal(summary.skipped_count, 0);
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
  assert.match(transaction, /dependencies\.runReviewPromptInNewTab \|\| runReviewPromptInNewTab/);
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
  await assert.rejects(openModelList(menu), /require one bounded reopen/);
});

test("model selection keeps the effort view when a covered row is already selected", async () => {
  const modelOptions = {
    count: async () => 2,
    nth(index) {
      return {
        async innerText() {
          return index === 0 ? "GPT-6" : "GPT-5.6 Sol";
        },
        async click(options) {
          assert.equal(options.trial, true);
          throw new Error("effort view intercepts selected row");
        },
      };
    },
    first() {
      return this.nth(0);
    },
  };
  const menu = {
    locator(selector) {
      if (selector === '[role="menuitemradio"]:visible') return modelOptions;
      if (selector === '[role="menuitem"][aria-label="Power"]:visible') {
        return {
          first() {
            return {
              async isVisible() {
                return true;
              },
            };
          },
        };
      }
      throw new Error(`Unexpected locator: ${selector}`);
    },
  };

  const result = await openModelList(menu, { model: "GPT-6" });

  assert.equal(result, menu);
});
test("model selection reopens when the requested model row is covered", async () => {
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
  await assert.rejects(
    openModelList(menu, { model: "GPT-5.6-Sol" }),
    /require one bounded reopen/,
  );
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

test("model selection adjusts effort when the UI labels the control by its current level", async () => {
  let menuVisible = false;
  let currentEffort = "Medium";
  const pressedKeys = [];
  const radioOptions = {
    count: async () => 2,
    nth(index) {
      return {
        async innerText() {
          return index === 0 ? "GPT-6" : "GPT-5.6 Sol";
        },
        async getAttribute(name) {
          assert.equal(name, "aria-checked");
          return index === 0 ? "true" : "false";
        },
        async click() {},
      };
    },
  };
  const effortControl = {
    async isVisible() {
      return true;
    },
    async focus() {},
    async press(key) {
      pressedKeys.push(key);
      currentEffort = "High";
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
                return `${currentEffort}, 2 of 3.`;
              },
            };
          },
        };
      }
      throw new Error(`Unexpected locator: ${selector}`);
    },
    getByRole(role, options = {}) {
      if (role !== "menuitem") throw new Error(`Unexpected menu role lookup: ${role}`);
      if (options.name === "Select model") {
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
      if (options.name === "Power") {
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
      if (options.name === "Medium") {
        return {
          first() {
            return effortControl;
          },
        };
      }
      throw new Error(`Unexpected effort control lookup: ${options.name}`);
    },
  };
  const page = {
    getByRole(role, options = {}) {
      if (role === "menu") return { first: () => menu };
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

  await selectReviewModel(page, { model: "GPT-6", effort: "High" });
  assert.deepEqual(pressedKeys, ["ArrowRight"]);
});
test("effort selection uses the visible Power control when its accessible name is only an aria label", async () => {
  let currentEffort = "Medium";
  const pressedKeys = [];
  const powerControl = {
    async isVisible() {
      return true;
    },
    async focus() {},
    async press(key) {
      pressedKeys.push(key);
      currentEffort = "High";
    },
  };
  const menu = {
    locator(selector) {
      if (selector === '[role="status"]') {
        return {
          first() {
            return {
              async isVisible() {
                return true;
              },
              async innerText() {
                return `${currentEffort}, 2 of 3.`;
              },
            };
          },
        };
      }
      if (selector === '[role="menuitem"][aria-label="Power"]:visible') {
        return {
          first() {
            return powerControl;
          },
        };
      }
      throw new Error(`Unexpected locator: ${selector}`);
    },
    getByRole(role) {
      assert.equal(role, "menuitem");
      return {
        first() {
          return {
            async isVisible() {
              return false;
            },
          };
        },
      };
    },
  };

  await setEffort(menu, "High");
  assert.equal(currentEffort, "High");
  assert.deepEqual(pressedKeys, ["ArrowRight"]);
});

test("effort focus and keyboard actions use the bounded UI timeout", async () => {
  const focusOptions = [];
  const pressOptions = [];
  let currentEffort = "Medium";
  const control = {
    async isVisible() { return true; },
    async focus(options) { focusOptions.push(options); },
    async press(key, options) {
      assert.equal(key, "ArrowRight");
      pressOptions.push(options);
      currentEffort = "High";
    },
  };
  const menu = {
    locator(selector) {
      if (selector === '[role="status"]') return { first: () => ({ async isVisible() { return true; }, async innerText() { return `${currentEffort}, 2 of 3.`; } }) };
      if (selector === '[role="menuitem"][aria-label="Power"]:visible') return { first: () => control };
      throw new Error(`Unexpected locator: ${selector}`);
    },
    getByRole() { return { first: () => ({ async isVisible() { return false; } }) }; },
  };

  await setEffort(menu, "High");

  assert.deepEqual(focusOptions, [{ timeout: 5000 }]);
  assert.deepEqual(pressOptions, [{ timeout: 5000 }]);
});
test("effort selection falls back to the visible slider when named controls are not exposed", async () => {
  let currentEffort = "Medium";
  const pressedKeys = [];
  const slider = {
    async isVisible() {
      return true;
    },
    async focus() {},
    async press(key) {
      pressedKeys.push(key);
      currentEffort = "High";
    },
  };
  const menu = {
    locator(selector) {
      if (selector === '[role="status"]') {
        return {
          first() {
            return {
              async isVisible() {
                return true;
              },
              async innerText() {
                return `${currentEffort}, 2 of 3.`;
              },
            };
          },
        };
      }
      if (selector === '[role="slider"]:visible') {
        return {
          first() {
            return slider;
          },
        };
      }
      throw new Error(`Unexpected locator: ${selector}`);
    },
    getByRole(role, options = {}) {
      assert.equal(role, "menuitem");
      return {
        first() {
          return {
            async isVisible() {
              return false;
            },
          };
        },
      };
    },
  };

  await setEffort(menu, "High");
  assert.equal(currentEffort, "High");
  assert.deepEqual(pressedKeys, ["ArrowRight"]);
});

test("unchanged effort skips control discovery and focus", async () => {
  const menu = {
    locator(selector) {
      if (selector === '[role="status"]') {
        return {
          first() {
            return {
              async isVisible() {
                return true;
              },
              async innerText() {
                return "High, 3 of 3.";
              },
            };
          },
        };
      }
      throw new Error("control lookup should not run");
    },
    getByRole() {
      throw new Error("control lookup should not run");
    },
  };

  await setEffort(menu, "High");
});

test("completion requires a new stable visible assistant turn and conversation", () => {
  assert.equal(evaluateReviewCompletion({
    assistantMessageId: "assistant-1",
    assistantText: "Finding: src/example.js:12 uses the requested revision.",
    assistantTurnCount: 2,
    baselineAssistantTurnCount: 1,
    composerReady: true,
    conversationId: "conversation-1",
    generationObserved: true,
    generating: false,
    interrupted: false,
    responseActionsReady: true,
    stableSampleCount: 2,
  }), true);

  assert.equal(evaluateReviewCompletion({
    assistantMessageId: null,
    assistantText: "Finding",
    assistantTurnCount: 2,
    baselineAssistantTurnCount: 1,
    composerReady: true,
    conversationId: null,
    generationObserved: false,
    generating: false,
    interrupted: false,
    responseActionsReady: true,
    stableSampleCount: 2,
  }), false);

  assert.equal(evaluateReviewCompletion({
    assistantMessageId: "assistant-1",
    assistantText: "Finding",
    assistantTurnCount: 1,
    baselineAssistantTurnCount: 1,
    composerReady: true,
    conversationId: "conversation-1",
    generationObserved: true,
    generating: false,
    interrupted: false,
    responseActionsReady: true,
    stableSampleCount: 2,
  }), false);

  assert.equal(evaluateReviewCompletion({
    assistantMessageId: "assistant-1",
    assistantText: "I’ll verify the exact commit before reviewing it.",
    assistantTurnCount: 2,
    baselineAssistantTurnCount: 1,
    composerReady: true,
    conversationId: "conversation-1",
    generationObserved: false,
    generating: false,
    interrupted: false,
    responseActionsReady: false,
    stableSampleCount: 2,
  }), false);

  assert.equal(evaluateReviewCompletion({
    assistantMessageId: null,
    assistantText: "I’ll review only the pinned revision before reporting findings.",
    assistantTurnCount: 2,
    baselineAssistantTurnCount: 1,
    composerReady: true,
    conversationId: "conversation-1",
    generationObserved: true,
    generating: false,
    interrupted: false,
    responseActionsReady: false,
    stableSampleCount: 2,
  }), false);

  assert.equal(evaluateReviewCompletion({
    assistantMessageId: "assistant-1",
    assistantText: "I’ll verify the exact commit before reviewing it.",
    assistantTurnCount: 2,
    baselineAssistantTurnCount: 1,
    composerReady: true,
    conversationId: "conversation-1",
    generationObserved: false,
    generating: false,
    interrupted: false,
    responseActionsReady: false,
    stableSampleCount: 2,
  }), false);

  assert.equal(evaluateReviewCompletion({
    assistantMessageId: "assistant-1",
    assistantText: "Finding: the pinned revision is confirmed.",
    assistantTurnCount: 2,
    baselineAssistantTurnCount: 1,
    composerReady: true,
    conversationId: "conversation-1",
    generationObserved: false,
    generating: false,
    interrupted: false,
    responseActionsReady: true,
    stableSampleCount: 2,
  }), true);
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

test("interruption detection checks dedicated and scoped generic error UI", async () => {
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
  assert.equal(requestedSelector, '[role="alert"]:visible');
});

test("interruption detection ignores unrelated generic alerts", async () => {
  const page = {
    locator(selector) {
      return {
        first() { return this; },
        async count() { return selector === '[role="alert"]:visible' ? 1 : 0; },
        async isVisible() { return true; },
        async innerText() { return "Draft saved"; },
      };
    },
  };

  assert.equal(await readVisibleInterruption(page), false);
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

test("review tab scopes composer readiness failure as review and closes", async () => {
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
    (error) => {
      assert.match(error.message, /Authenticated ChatGPT composer was not found/);
      assert.equal(error.failureScope, "review");
      return true;
    },
  );
  assert.equal(closed, true);
});

test("review tab marks context setup failures as shared-context failures", async () => {
  await assert.rejects(
    openReviewTab({
      async newPage() {
        throw new Error("new page failed");
      },
    }),
    (error) => {
      assert.equal(error.failureScope, "shared_context");
      assert.match(error.message, /new page failed/);
      return true;
    },
  );
});

test("authentication preflight closes its probe page and accepts a visible composer", async () => {
  let closed = false;
  const composer = {
    first() { return this; },
    async waitFor() {},
    async isVisible() { return true; },
  };
  const loginControl = {
    first() { return this; },
    async isVisible() { return false; },
  };
  const page = {
    url: () => "https://chatgpt.com/",
    getByRole(role, options) {
      if (role === "button") return loginControl;
      assert.equal(options.name, "Ask ChatGPT");
      return composer;
    },
    async close() { closed = true; },
  };

  await preflightAuthenticatedContext({ newPage: async () => page });
  assert.equal(closed, true);
});

test("authentication preflight blocks a visible login wall", async () => {
  let closed = false;
  const loginControl = {
    first() { return this; },
    async isVisible() { return true; },
  };
  const page = {
    url: () => "https://chatgpt.com/",
    getByRole() { return loginControl; },
    async close() { closed = true; },
  };

  await assert.rejects(
    preflightAuthenticatedContext({ newPage: async () => page }),
    (error) => {
      assert.equal(error.failureScope, "shared_context");
      assert.match(error.message, /authentication is required/);
      return true;
    },
  );
  assert.equal(closed, true);
});

test("review tab closes when model preparation fails after newPage", async () => {
  let closed = false;
  const composer = {
    async waitFor() {},
    async isVisible() { return true; },
  };
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
    (error) => {
      assert.equal(error.failureScope, "review");
      assert.match(error.message, /model menu did not open/);
      return true;
    },
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

test("completion polling avoids full assistant text reads while generating", async () => {
  let stopChecks = 0;
  let innerTextReads = 0;
  const assistantTurn = {
    async getAttribute(attribute) {
      return attribute === "data-message-id" ? "assistant-1" : null;
    },
    async innerText() {
      innerTextReads += 1;
      return "Finding: exact revision confirmed.";
    },
  };
  const assistantTurns = {
    async count() {
      return 1;
    },
    nth() {
      return assistantTurn;
    },
  };
  const interruption = {
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
  const stopButton = {
    first() {
      return this;
    },
    async isVisible() {
      stopChecks += 1;
      return stopChecks <= 2;
    },
  };
  const responseAction = {
    last() {
      return this;
    },
    async isVisible() {
      return true;
    },
  };
  const composer = {
    first() {
      return this;
    },
    async isVisible() {
      return true;
    },
  };
  const page = {
    locator(selector) {
      if (selector.includes("data-message-author-role")) return assistantTurns;
      if (selector.includes("[role=\"alert\"]") || selector.includes("data-testid")) return interruption;
      throw new Error(`Unexpected locator: ${selector}`);
    },
    getByRole(role, options) {
      if (role === "button" && options.name.source.includes("Stop generating")) return stopButton;
      if (role === "button" && options.name.source.includes("Regenerate response")) return responseAction;
      if (role === "textbox") return composer;
      throw new Error(`Unexpected role lookup: ${role}`);
    },
    url() {
      return "https://chatgpt.com/c/probe";
    },
    async waitForTimeout() {},
  };

  const result = await waitForReviewCompletion(page, {
    baseline: { assistantTurnCount: 0 },
    timeoutMs: 100,
  });

  assert.equal(result.status, "confirmed");
  assert.equal(innerTextReads, 3);
});

test("completion accepts a stable markdown fallback response without message metadata", async () => {
  const assistantTurn = {
    async getAttribute() {
      return null;
    },
    async innerText() {
      return "Finding: exact revision confirmed.";
    },
  };
  const assistantTurns = {
    async count() {
      return 1;
    },
    nth() {
      return assistantTurn;
    },
  };
  const interruption = {
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
  const stopButton = {
    first() {
      return this;
    },
    async isVisible() {
      return false;
    },
  };
  const responseAction = {
    last() {
      return this;
    },
    async isVisible() {
      return true;
    },
  };
  const composer = {
    first() {
      return this;
    },
    async isVisible() {
      return true;
    },
  };
  const page = {
    locator(selector) {
      if (selector.includes("data-message-author-role")) {
        return { async count() { return 0; } };
      }
      if (selector.includes("MarkdownRoot-")) return assistantTurns;
      if (selector.includes("[role=\"alert\"]") || selector.includes("data-testid")) return interruption;
      throw new Error(`Unexpected locator: ${selector}`);
    },
    getByRole(role, options) {
      if (role === "button" && options.name.source.includes("Stop generating")) return stopButton;
      if (role === "button" && options.name.source.includes("Regenerate response")) return responseAction;
      if (role === "textbox") return composer;
      throw new Error(`Unexpected role lookup: ${role}`);
    },
    url() {
      return "https://chatgpt.com/c/probe";
    },
    async waitForTimeout() {},
  };

  const result = await waitForReviewCompletion(page, {
    baseline: { assistantTurnCount: 0 },
    timeoutMs: 100,
  });

  assert.equal(result.status, "confirmed");
  assert.equal(result.response, "Finding: exact revision confirmed.");
});

test("completion timeout preserves visible partial assistant text", async () => {
  const assistantTurn = {
    async getAttribute(attribute) {
      return attribute === "data-message-id" ? "assistant-1" : null;
    },
    async innerText() {
      return "Partial finding before timeout.";
    },
  };
  const assistantTurns = {
    async count() {
      return 1;
    },
    nth() {
      return assistantTurn;
    },
  };
  const interruption = {
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
  const stopButton = {
    first() {
      return this;
    },
    async isVisible() {
      return true;
    },
  };
  const responseAction = {
    last() {
      return this;
    },
    async isVisible() {
      return false;
    },
  };
  const composer = {
    first() {
      return this;
    },
    async isVisible() {
      return false;
    },
  };
  const page = {
    locator(selector) {
      if (selector.includes("data-message-author-role")) return assistantTurns;
      if (selector.includes("[role=\"alert\"]") || selector.includes("data-testid")) return interruption;
      throw new Error(`Unexpected locator: ${selector}`);
    },
    getByRole(role, options) {
      if (role === "button" && options.name.source.includes("Stop generating")) return stopButton;
      if (role === "button" && options.name.source.includes("Regenerate response")) return responseAction;
      if (role === "textbox") return composer;
      throw new Error(`Unexpected role lookup: ${role}`);
    },
    url() {
      return "https://chatgpt.com/c/probe";
    },
    async waitForTimeout() {},
  };

  const result = await waitForReviewCompletion(page, {
    baseline: { assistantTurnCount: 0 },
    timeoutMs: 0,
  });

  assert.equal(result.status, "incomplete");
  assert.equal(result.response, "Partial finding before timeout.");
});

test("completion returns immediately on a visible interruption", async () => {
  let waitCalls = 0;
  const emptyTurns = {
    async count() { return 0; },
  };
  const interruption = {
    first() { return this; },
    async count() { return 1; },
    async isVisible() { return true; },
  };
  const hidden = {
    first() { return this; },
    last() { return this; },
    async count() { return 0; },
    async isVisible() { return false; },
  };
  const page = {
    locator(selector) {
      if (selector === INTERRUPTION_UI_SELECTOR) return interruption;
      if (selector === ASSISTANT_TURN_SELECTOR) return emptyTurns;
      return hidden;
    },
    getByRole(role, options) {
      if (role === "button") return hidden;
      if (role === "textbox") return { first() { return { async isVisible() { return true; } }; } };
      throw new Error(`Unexpected role lookup: ${role}`);
    },
    url() { return "https://chatgpt.com/c/interrupted"; },
    async waitForTimeout() { waitCalls += 1; },
  };

  const result = await waitForReviewCompletion(page, {
    baseline: { assistantTurnCount: 0 },
    timeoutMs: 900000,
  });

  assert.equal(result.status, "interrupted");
  assert.equal(result.failureReason, "visible response interruption");
  assert.equal(waitCalls, 0);
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
    review_index: null,
    request_provenance: {
      prompt_file: null,
      prompt_sha256: null,
      repository: null,
      commit_sha: null,
      review_urls: [],
    },
  });
});

test("result records sanitized immutable request provenance", () => {
  const result = createResult({
    model: "GPT-6",
    effort: "High",
    prompt: "review prompt",
    promptFile: "review.md",
    repository: "longdang193/project-OS-starter",
    commitSha: "c163271b437046c61daab974a190dc9bc4764d57",
    reviewUrls: ["https://github.com/longdang193/project-OS-starter/blob/c163271b437046c61daab974a190dc9bc4764d57/README.md"],
    reviewIndex: 2,
  });

  assert.equal(result.review_index, 2);
  assert.equal(result.request_provenance.prompt_file, "review.md");
  assert.equal(result.request_provenance.prompt_sha256.length, 64);
  assert.equal(result.request_provenance.repository, "longdang193/project-OS-starter");
  assert.equal(result.request_provenance.commit_sha, "c163271b437046c61daab974a190dc9bc4764d57");
  assert.deepEqual(result.request_provenance.review_urls, [
    "https://github.com/longdang193/project-OS-starter/blob/c163271b437046c61daab974a190dc9bc4764d57/README.md",
  ]);
});

test("completion observer failure preserves acknowledged submission and records completion stage", async () => {
  const parent = await mkdtemp(join(tmpdir(), "github-review-observer-failure-"));
  try {
    const result = await runReviewTransaction({}, {
      effort: "High",
      model: "GPT-6",
      outputDir: parent,
      prompt: "review",
      dependencies: {
        runReviewPromptInNewTab: async (_context, options) => {
          await options.beforeSubmit();
          return {
            effort: "High",
            model: "GPT-6",
            page: { async close() {} },
            promptSubmitted: true,
            submission: "acknowledged",
          };
        },
        waitForReviewCompletion: async () => {
          throw new Error("completion observer failed");
        },
      },
    });

    const persisted = JSON.parse(await readFile(join(result.output_dir, "result.json"), "utf8"));
    assert.equal(result.status, "incomplete");
    assert.equal(result.failure_stage, "completion");
    assert.equal(result.submission, "acknowledged");
    assert.equal(result.cleanup_status, "completed");
    assert.equal(persisted.submission, "acknowledged");
    assert.equal(persisted.failure_stage, "completion");
  } finally {
    await rm(parent, { recursive: true, force: true });
  }
});

test("selection failure is not reported as submission ambiguity", async () => {
  const parent = await mkdtemp(join(tmpdir(), "github-review-selection-failure-"));
  try {
    const result = await runReviewTransaction({}, {
      effort: "High",
      model: "GPT-6",
      outputDir: parent,
      prompt: "review",
      dependencies: {
        runReviewPromptInNewTab: async () => {
          throw Object.assign(new Error("model selection failed"), {
            failureScope: "review",
          });
        },
      },
    });

    assert.equal(result.status, "blocked");
    assert.equal(result.failure_stage, "selection");
    assert.equal(result.failure_scope, "review");
    assert.equal(result.submission, "not_started");
    assert.equal(result.cleanup_status, "not_needed");
  } finally {
    await rm(parent, { recursive: true, force: true });
  }
});

test("unacknowledged submission remains ambiguous at the submission stage", async () => {
  const parent = await mkdtemp(join(tmpdir(), "github-review-submission-failure-"));
  try {
    const result = await runReviewTransaction({}, {
      effort: "High",
      model: "GPT-6",
      outputDir: parent,
      prompt: "review",
      dependencies: {
        runReviewPromptInNewTab: async (_context, options) => {
          await options.beforeSubmit();
          throw new Error("prompt acknowledgement failed");
        },
      },
    });

    assert.equal(result.status, "incomplete");
    assert.equal(result.failure_stage, "submission");
    assert.equal(result.submission, "ambiguous");
  } finally {
    await rm(parent, { recursive: true, force: true });
  }
});

test("ambiguous submission preserves the owned page and visible completion evidence", async () => {
  const parent = await mkdtemp(join(tmpdir(), "github-review-ambiguous-evidence-"));
  let closeCount = 0;
  let completionCalls = 0;
  try {
    const page = {
      url() {
        return "https://chatgpt.com/c/ambiguous";
      },
      async close() {
        closeCount += 1;
      },
    };
    const result = await runReviewTransaction({}, {
      effort: "High",
      model: "GPT-6",
      outputDir: parent,
      prompt: "review",
      dependencies: {
        runReviewPromptInNewTab: async (_context, options) => {
          await options.beforeSubmit();
          const error = new Error("prompt acknowledgement failed");
          error.reviewPage = page;
          error.reviewBaseline = {
            assistantTurnCount: 0,
            conversationId: "ambiguous",
            conversationUrl: page.url(),
          };
          error.submissionAttempted = true;
          throw error;
        },
        waitForReviewCompletion: async () => {
          completionCalls += 1;
          return {
            assistantMessageId: "assistant-ambiguous",
            assistantTurnIndex: 1,
            conversationId: "ambiguous",
            currentUrl: page.url(),
            response: "preserved response",
            status: "confirmed",
          };
        },
      },
    });

    const persisted = JSON.parse(await readFile(join(result.output_dir, "result.json"), "utf8"));
    assert.equal(completionCalls, 1);
    assert.equal(closeCount, 1);
    assert.equal(result.status, "incomplete");
    assert.equal(result.submission, "ambiguous");
    assert.equal(result.completion, "confirmed");
    assert.equal(result.assistant_message_id, "assistant-ambiguous");
    assert.equal(await readFile(join(result.output_dir, "response.md"), "utf8"), "preserved response\n");
    assert.equal(persisted.submission, "ambiguous");
    assert.equal(persisted.completion, "confirmed");
  } finally {
    await rm(parent, { recursive: true, force: true });
  }
});

test("browser context loss remains a shared-context failure at submission time", async () => {
  const parent = await mkdtemp(join(tmpdir(), "github-review-context-loss-"));
  try {
    const result = await runReviewTransaction({}, {
      effort: "High",
      model: "GPT-6",
      outputDir: parent,
      prompt: "review",
      dependencies: {
        runReviewPromptInNewTab: async () => {
          throw new Error("Target page, context or browser has been closed");
        },
      },
    });

    assert.equal(result.status, "blocked");
    assert.equal(result.failure_scope, "shared_context");
    assert.equal(result.failure_stage, "selection");
  } finally {
    await rm(parent, { recursive: true, force: true });
  }
});

test("browser context loss remains a shared-context failure at completion time", async () => {
  const parent = await mkdtemp(join(tmpdir(), "github-review-completion-context-loss-"));
  try {
    const result = await runReviewTransaction({}, {
      effort: "High",
      model: "GPT-6",
      outputDir: parent,
      prompt: "review",
      dependencies: {
        runReviewPromptInNewTab: async (_context, options) => {
          await options.beforeSubmit();
          return {
            effort: "High",
            model: "GPT-6",
            page: { async close() {} },
            promptSubmitted: true,
            submission: "acknowledged",
          };
        },
        waitForReviewCompletion: async () => {
          throw new Error("Browser context has been disconnected");
        },
      },
    });

    assert.equal(result.status, "incomplete");
    assert.equal(result.failure_scope, "shared_context");
    assert.equal(result.failure_stage, "completion");
  } finally {
    await rm(parent, { recursive: true, force: true });
  }
});

test("pre-submit checkpoint failure is classified as an artifact failure", async () => {
  const parent = await mkdtemp(join(tmpdir(), "github-review-pre-submit-artifact-failure-"));
  let writeCount = 0;
  try {
    const result = await runReviewTransaction({}, {
      effort: "High",
      model: "GPT-6",
      outputDir: parent,
      prompt: "review",
      dependencies: {
        runReviewPromptInNewTab: async (_context, options) => {
          await options.beforeSubmit();
          throw new Error("send should not run");
        },
        writeResult: async (outputDir, value) => {
          writeCount += 1;
          if (writeCount === 2) throw new Error("checkpoint write failed");
          await writeResult(outputDir, value);
        },
      },
    });

    assert.equal(result.status, "blocked");
    assert.equal(result.failure_stage, "artifacts");
    assert.equal(result.submission, "attempted");
  } finally {
    await rm(parent, { recursive: true, force: true });
  }
});

test("response artifact failure is classified separately after acknowledged submission", async () => {
  const parent = await mkdtemp(join(tmpdir(), "github-review-artifact-failure-"));
  try {
    const result = await runReviewTransaction({}, {
      effort: "High",
      model: "GPT-6",
      outputDir: parent,
      prompt: "review",
      dependencies: {
        runReviewPromptInNewTab: async (_context, options) => {
          await options.beforeSubmit();
          return {
            effort: "High",
            model: "GPT-6",
            page: { async close() {} },
            promptSubmitted: true,
            submission: "acknowledged",
          };
        },
        waitForReviewCompletion: async () => ({
          currentUrl: "https://chatgpt.com/c/review",
          response: "response",
          status: "confirmed",
        }),
        writeResponse: async () => {
          throw new Error("response write failed");
        },
      },
    });

    assert.equal(result.status, "blocked");
    assert.equal(result.failure_stage, "artifacts");
    assert.equal(result.submission, "acknowledged");
  } finally {
    await rm(parent, { recursive: true, force: true });
  }
});

test("cleanup failure preserves completed review and records a cleanup warning", async () => {
  const parent = await mkdtemp(join(tmpdir(), "github-review-cleanup-failure-"));
  try {
    const result = await runReviewTransaction({}, {
      effort: "High",
      model: "GPT-6",
      outputDir: parent,
      prompt: "review",
      dependencies: {
        runReviewPromptInNewTab: async (_context, options) => {
          await options.beforeSubmit();
          return {
            effort: "High",
            model: "GPT-6",
            page: {
              async close() {
                throw new Error("page close failed");
              },
            },
            promptSubmitted: true,
            submission: "acknowledged",
          };
        },
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

    const persisted = JSON.parse(await readFile(join(result.output_dir, "result.json"), "utf8"));
    assert.equal(result.status, "incomplete");
    assert.equal(result.failure_scope, "shared_context");
    assert.equal(result.cleanup_status, "failed");
    assert.equal(result.cleanup_warning, "page close failed");
    assert.equal(persisted.status, "incomplete");
    assert.equal(persisted.cleanup_status, "failed");
    assert.equal(persisted.cleanup_warning, "page close failed");
  } finally {
    await rm(parent, { recursive: true, force: true });
  }
});

test("successful transaction writes the pending cleanup checkpoint once", async () => {
  const parent = await mkdtemp(join(tmpdir(), "github-review-pending-checkpoint-"));
  const writes = [];
  try {
    const result = await runReviewTransaction({}, {
      effort: "High",
      model: "GPT-6",
      outputDir: parent,
      prompt: "review",
      dependencies: {
        runReviewPromptInNewTab: async (_context, options) => {
          await options.beforeSubmit();
          return {
            effort: "High",
            model: "GPT-6",
            page: { async close() {} },
            promptSubmitted: true,
            submission: "acknowledged",
          };
        },
        waitForReviewCompletion: async () => ({ response: "response", status: "confirmed" }),
        writeResult: async (outputDir, value) => {
          writes.push({ cleanup_status: value.cleanup_status, status: value.status });
          await writeResult(outputDir, value);
        },
      },
    });

    assert.equal(result.status, "completed");
    assert.equal(writes.filter((write) => write.cleanup_status === "pending").length, 1);
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

test("failed context cleanup does not mark the context closed", async () => {
  const attached = {
    context: {
      async close() {
        throw new Error("context close failed");
      },
    },
    ownsContext: true,
  };

  await assert.rejects(() => closeContext(attached), /context close failed/);
  assert.equal(attached.closed, undefined);
});

test("failed owned context cleanup retains the profile lease", async () => {
  const parent = await mkdtemp(join(tmpdir(), "github-review-context-lease-"));
  const profile = join(parent, "profile");
  try {
    const profileLease = await acquireProfileLease(profile);
    const attached = {
      context: {
        async close() {
          throw new Error("context close failed");
        },
      },
      ownsContext: true,
      profileLease,
    };

    await assert.rejects(() => closeContext(attached), /context close failed/);
    assert.ok((await readFile(profileLease.lockPath, "utf8")).includes(profileLease.token));
    await profileLease.handle.close().catch(() => {});
    await rm(profileLease.lockPath, { force: true });
  } finally {
    await rm(parent, { recursive: true, force: true });
  }
});

test("batch main delegates context cleanup to the batch owner", async () => {
  const parent = await mkdtemp(join(tmpdir(), "github-review-main-batch-"));
  try {
    await writeFile(join(parent, "review.md"), "review\n", "utf8");
    await writeFile(join(parent, "reviews.json"), JSON.stringify({
      reviews: [{ model: "GPT-6", effort: "High", prompt_file: "review.md" }],
    }), "utf8");
    let outerCleanupCalls = 0;

    const exitCode = await main([
      "--user-data-dir", "github-review/project",
      "--batch-file", join(parent, "reviews.json"),
    ], {
      openReviewContext: async () => ({ context: {}, ownsContext: true }),
      runReviewBatch: async () => [{ status: "completed", output_dir: "run-a" }],
      closeContext: async () => {
        outerCleanupCalls += 1;
      },
    });

    assert.equal(exitCode, 0);
    assert.equal(outerCleanupCalls, 0);
  } finally {
    await rm(parent, { recursive: true, force: true });
  }
});

test("owned context cleanup failure makes the CLI invocation nonzero", async () => {
  const parent = await mkdtemp(join(tmpdir(), "github-review-main-cleanup-"));
  try {
    const promptFile = join(parent, "review.md");
    await writeFile(promptFile, "review\n", "utf8");

    const exitCode = await main([
      "--user-data-dir", "github-review/project",
      "--model", "GPT-6",
      "--effort", "High",
      "--prompt-file", promptFile,
    ], {
      openReviewContext: async () => ({ context: {}, ownsContext: true }),
      runReviewTransaction: async () => ({ status: "completed", output_dir: "run-a" }),
      closeContext: async () => {
        throw new Error("context close failed");
      },
    });

    assert.equal(exitCode, 1);
  } finally {
    await rm(parent, { recursive: true, force: true });
  }
});

test("termination cleanup is installed and can be removed without duplicating ownership", () => {
  const originalOnce = process.once;
  const originalRemoveListener = process.removeListener;
  const registered = [];
  const removed = [];
  process.once = (signal, handler) => {
    registered.push({ signal, handler });
    return process;
  };
  process.removeListener = (signal, handler) => {
    removed.push({ signal, handler });
    return process;
  };
  try {
    const remove = installTerminationCleanup({ context: {} }, async () => {});
    assert.deepEqual(registered.map(({ signal }) => signal), ["SIGINT", "SIGTERM"]);
    remove();
    assert.equal(removed.length, 2);
  } finally {
    process.once = originalOnce;
    process.removeListener = originalRemoveListener;
  }
});

test("final result persistence failure makes a completed response incomplete", async () => {
  const parent = await mkdtemp(join(tmpdir(), "github-review-final-persistence-failure-"));
  let writeCount = 0;
  try {
    const result = await runReviewTransaction({}, {
      effort: "High",
      model: "GPT-6",
      outputDir: parent,
      prompt: "review",
      dependencies: {
        runReviewPromptInNewTab: async (_context, options) => {
          await options.beforeSubmit();
          return {
            effort: "High",
            model: "GPT-6",
            page: { async close() {} },
            promptSubmitted: true,
            submission: "acknowledged",
          };
        },
        waitForReviewCompletion: async () => ({ response: "response", status: "confirmed" }),
        writeResult: async (outputDir, value) => {
          writeCount += 1;
          if (writeCount === 5) throw new Error("final result write failed");
          await writeResult(outputDir, value);
        },
      },
    });

    assert.equal(writeCount, 5);
    assert.equal(result.status, "incomplete");
    assert.equal(result.failure_stage, "artifacts");
    assert.match(result.failure_reason, /final result persistence failed/);
  } finally {
    await rm(parent, { recursive: true, force: true });
  }
});

test("batch context-open failure accounts for every requested review as skipped", async () => {
  const parent = await mkdtemp(join(tmpdir(), "github-review-batch-open-failure-"));
  const promptFile = join(parent, "review.md");
  const manifestFile = join(parent, "reviews.json");
  const logged = [];
  const originalLog = console.log;
  try {
    await writeFile(promptFile, "review\n", "utf8");
    await writeFile(manifestFile, JSON.stringify({
      reviews: [
        { model: "GPT-6", effort: "High", prompt_file: "review.md" },
        { model: "GPT-5.6-Sol", effort: "High", prompt_file: "review.md" },
      ],
    }), "utf8");
    console.log = (value) => logged.push(value);

    const exitCode = await main([
      "--user-data-dir", "github-review/project",
      "--batch-file", manifestFile,
    ], {
      openReviewContext: async () => {
        throw new Error("context unavailable");
      },
    });

    const result = JSON.parse(logged[0]);
    assert.equal(exitCode, 1);
    assert.equal(result.status, "blocked");
    assert.equal(result.requested_count, 2);
    assert.equal(result.attempted_count, 0);
    assert.equal(result.skipped_count, 2);
    assert.deepEqual(result.reviews.map((review) => review.status), ["skipped", "skipped"]);
  } finally {
    console.log = originalLog;
    await rm(parent, { recursive: true, force: true });
  }
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

test("review batch stops after a shared-context failure", async () => {
  const context = {};
  const attached = { context, ownsContext: true };
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
      return review.prompt === "first"
        ? { status: "blocked", failure_scope: "shared_context" }
        : { status: "completed" };
    },
  });

  assert.deepEqual(attempted, ["first"]);
  assert.equal(results.length, 2);
  assert.equal(results[1].status, "skipped");
  assert.equal(results[1].model_requested, "GPT-6");
  assert.equal(results[1].effort_requested, "High");
  assert.equal(results[1].review_index, 1);
  assert.match(results[1].failure_reason, /Skipped after review 1/);
  assert.equal(closeCount, 1);
});

test("batch continues after an explicit review-scoped failure", async () => {
  const context = {};
  const attached = { context, ownsContext: true };
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
      return review.prompt === "first"
        ? { status: "blocked", failure_scope: "review" }
        : { status: "completed" };
    },
  });

  assert.deepEqual(attempted, ["first", "second"]);
  assert.equal(results.length, 2);
  assert.equal(closeCount, 1);
});

test("batch stops after an unknown failure scope", async () => {
  const context = {};
  const attached = { context, ownsContext: true };
  const attempted = [];
  context.close = async () => {};

  const results = await runReviewBatch({
    attached,
    outputDir: "review-output",
    reviews: [
      { model: "GPT-6", effort: "High", prompt: "first" },
      { model: "GPT-6", effort: "High", prompt: "second" },
    ],
    runTransaction: async (_reviewContext, review) => {
      attempted.push(review.prompt);
      return { status: "blocked", failure_scope: "unknown" };
    },
  });

  assert.deepEqual(attempted, ["first"]);
  assert.equal(results.length, 2);
  assert.equal(results[1].status, "skipped");
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

test("profile lease fails closed for stale ownership that cannot be reclaimed atomically", async () => {
  const parent = await mkdtemp(join(tmpdir(), "github-review-stale-profile-"));
  const profile = join(parent, "profile");
  const lockPath = `${resolve(profile)}.codex-review-profile.lock`;
  try {
    await writeFile(lockPath, `${JSON.stringify({
      pid: 999999,
      profile: resolve(profile),
      token: "stale-token",
    })}\n`, "utf8");

    await assert.rejects(
      acquireProfileLease(profile, { isProcessAlive: async () => false }),
      /profile is already in use|Stale profile lease|stale profile lease|ambiguous profile lease/,
    );
    assert.match(await readFile(lockPath, "utf8"), /stale-token/);
  } finally {
    await rm(parent, { recursive: true, force: true });
  }
});

test("profile lease removes a lock created by a failed metadata publication", async () => {
  const parent = await mkdtemp(join(tmpdir(), "github-review-metadata-failure-"));
  const profile = join(parent, "profile");
  const lockPath = `${resolve(profile)}.codex-review-profile.lock`;
  try {
    await assert.rejects(
      acquireProfileLease(profile, {
        writeMetadata: async () => {
          throw new Error("metadata write failed");
        },
      }),
      /metadata write failed/,
    );
    await assert.rejects(readFile(lockPath, "utf8"), { code: "ENOENT" });
  } finally {
    await rm(parent, { recursive: true, force: true });
  }
});

test("profile lease refuses malformed ownership metadata", async () => {
  const parent = await mkdtemp(join(tmpdir(), "github-review-malformed-profile-"));
  const profile = join(parent, "profile");
  const lockPath = `${resolve(profile)}.codex-review-profile.lock`;
  try {
    await writeFile(lockPath, "not-json\n", "utf8");
    await assert.rejects(
      acquireProfileLease(profile, { isProcessAlive: async () => false }),
      /profile is already in use|ambiguous profile lease/,
    );
    assert.equal(await readFile(lockPath, "utf8"), "not-json\n");
  } finally {
    await rm(parent, { recursive: true, force: true });
  }
});

test("profile lease release preserves a replacement owner's lock", async () => {
  const parent = await mkdtemp(join(tmpdir(), "github-review-replacement-profile-"));
  const profile = join(parent, "profile");
  const lockPath = `${resolve(profile)}.codex-review-profile.lock`;
  try {
    const lease = await acquireProfileLease(profile);
    await writeFile(lockPath, `${JSON.stringify({
      pid: process.pid,
      profile: resolve(profile),
      token: "replacement-token",
    })}\n`, "utf8");
    await releaseProfileLease(lease);
    assert.match(await readFile(lockPath, "utf8"), /replacement-token/);
    await rm(lockPath, { force: true });
  } finally {
    await rm(parent, { recursive: true, force: true });
  }
});

test("batch context cleanup failure retains completed review results", async () => {
  const context = {
    async close() {
      throw new Error("context close failed");
    },
  };
  const attached = { context, ownsContext: true };

  await assert.rejects(
    () => runReviewBatch({
      attached,
      outputDir: "review-output",
      reviews: [{ model: "GPT-6", effort: "High", prompt: "review" }],
      runTransaction: async () => ({ status: "completed", output_dir: "run-a" }),
    }),
    (error) => {
      assert.equal(error.message, "Batch context cleanup failed: context close failed");
      assert.deepEqual(error.results, [{
        status: "incomplete",
        output_dir: "run-a",
        cleanup_status: "failed",
        cleanup_warning: "context close failed",
        failure_scope: "shared_context",
        failure_stage: "cleanup",
        failure_reason: "context close failed",
      }]);
      return true;
    },
  );
});

test("batch stops after uncertain page cleanup", async () => {
  const context = {};
  const attached = { context, ownsContext: true };
  const attempted = [];
  context.close = async () => {};

  const results = await runReviewBatch({
    attached,
    outputDir: "review-output",
    reviews: [
      { model: "GPT-6", effort: "High", prompt: "first" },
      { model: "GPT-6", effort: "High", prompt: "second" },
    ],
    runTransaction: async (_reviewContext, review) => {
      attempted.push(review.prompt);
      return review.prompt === "first"
        ? { status: "incomplete", failure_scope: "shared_context", failure_stage: "cleanup" }
        : { status: "completed" };
    },
  });

  assert.deepEqual(attempted, ["first"]);
  assert.equal(results.length, 2);
  assert.equal(results[1].status, "skipped");
});

test("batch continues after a review-scoped fresh-tab readiness failure", async () => {
  const context = {};
  const attached = { context, ownsContext: true };
  const attempted = [];
  context.close = async () => {};

  const results = await runReviewBatch({
    attached,
    outputDir: "review-output",
    reviews: [
      { model: "GPT-6", effort: "High", prompt: "first" },
      { model: "GPT-6", effort: "High", prompt: "second" },
    ],
    runTransaction: async (_reviewContext, review) => {
      attempted.push(review.prompt);
      return review.prompt === "first"
        ? { status: "blocked", failure_scope: "review", failure_stage: "page_readiness" }
        : { status: "completed" };
    },
  });

  assert.deepEqual(attempted, ["first", "second"]);
  assert.equal(results.length, 2);
});
