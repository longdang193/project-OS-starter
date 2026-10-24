import assert from "node:assert/strict";
import { mkdtemp, readFile, rm } from "node:fs/promises";
import { tmpdir } from "node:os";
import { join } from "node:path";
import test from "node:test";

import {
  evaluateReviewCompletion,
  isPromptVisibleInComposer,
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

test("output directory remains optional and probe-only stays prompt independent", () => {
  const parsed = parseArguments([
    "--probe-only",
    "--cdp-endpoint", "http://127.0.0.1:1",
    "--model", "GPT-6",
    "--effort", "High",
    "--output-dir", "probe-output",
  ]);

  assert.equal(parsed.probeOnly, true);
  assert.equal(parsed.promptFile, undefined);
  assert.equal(parsed.outputDir, "probe-output");
});

test("model selection keeps the simple picker view when model radios are visible", async () => {
  let modelControlClicked = false;
  const menu = {
    locator(selector) {
      assert.equal(selector, '[role="menuitemradio"]:visible');
      return { count: async () => 2 };
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
    result.status = "verified";
    result.submission = "acknowledged";
    result.completion = "confirmed";

    await writeResult(outputDir, result);
    await atomicWrite(join(outputDir, "response.md"), "Finding at line 12.\n");

    assert.equal(JSON.parse(await readFile(join(outputDir, "result.json"), "utf8")).status, "verified");
    assert.equal(await readFile(join(outputDir, "response.md"), "utf8"), "Finding at line 12.\n");
  } finally {
    await rm(outputDir, { recursive: true, force: true });
  }
});
