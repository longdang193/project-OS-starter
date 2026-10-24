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
  closeContext,
  createResult,
  createRunOutputDirectory,
  parseArguments,
  writeResult,
} from "../.agents/skills/skill-github-browser-reviews/scripts/run-review-prompt-cli.mjs";
import {
  findModelOption,
  openModelList,
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

test("runner contract uses completed as its successful terminal state", async () => {
  const runner = await readFile(
    new URL("../.agents/skills/skill-github-browser-reviews/scripts/run-review-prompt-cli.mjs", import.meta.url),
    "utf8",
  );

  assert.match(runner, /result\.status = "completed"/);
  assert.match(runner, /return result\.status === "completed" \? 0 : 1/);
  assert.doesNotMatch(runner, /result\.status = "verified"/);
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
    failure_stage: null,
    failure_reason: null,
  });
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
