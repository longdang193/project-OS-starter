import assert from "node:assert/strict";
import { mkdtemp, readFile, rm } from "node:fs/promises";
import { tmpdir } from "node:os";
import { join } from "node:path";
import test from "node:test";

import {
  ASSISTANT_TURN_SELECTOR,
  INTERRUPTION_PATTERN,
  evaluateReviewCompletion,
  isPromptVisibleInComposer,
  openReviewTab,
} from "../.agents/skills/skill-github-browser-reviews/scripts/run-review-prompt.mjs";
import {
  atomicWrite,
  createResult,
  parseArguments,
  writeResult,
} from "../.agents/skills/skill-github-browser-reviews/scripts/run-review-prompt-cli.mjs";
import {
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
    stableSampleCount: 2,
  }), false);
});

test("assistant fallback excludes rich-text user turns", () => {
  assert.match(ASSISTANT_TURN_SELECTOR, /:not\(\.rich-text-user-turn\)/);
});

test("interruption detection ignores ordinary assistant text containing try again", () => {
  assert.equal(INTERRUPTION_PATTERN.test("You can try again with a narrower question."), false);
  assert.equal(INTERRUPTION_PATTERN.test("Something went wrong. Please try again."), true);
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
    model_requested: "GPT-5.6-Sol",
    model_verified: null,
    effort_requested: "High",
    effort_verified: null,
    submission_attempted: false,
    submission: "not_started",
    completion: "not_started",
    conversation_url: null,
    conversation_id: null,
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
