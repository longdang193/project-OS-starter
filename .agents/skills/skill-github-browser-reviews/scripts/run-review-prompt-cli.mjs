#!/usr/bin/env node

import { readFile } from "node:fs/promises";
import process from "node:process";

import {
  probeReviewModelInNewTab,
  runReviewPromptInNewTab,
} from "./run-review-prompt.mjs";
import {
  SUPPORTED_EFFORTS,
  SUPPORTED_MODELS,
} from "./select-review-model.mjs";

const DEFAULT_CONTEXT_INDEX = 0;
const USAGE = "Usage: node run-review-prompt-cli.mjs (--user-data-dir <path> | --cdp-endpoint <url>) --model <GPT-5.6-Sol|GPT-6> --effort <Instant|Medium|High> [--probe-only] [--prompt-file <path>] [--context-index <number>]";
const FLAG_ARGUMENTS = new Set(["--probe-only"]);

function usageError(message) {
  throw new Error(`${message}\n${USAGE}`);
}
function parseArguments(argv) {
  const argumentsByName = new Map();
  for (let index = 0; index < argv.length; index += 1) {
    const argument = argv[index];
    if (!argument.startsWith("--")) {
      usageError(`Unexpected argument: ${argument}`);
    }
    if (FLAG_ARGUMENTS.has(argument)) {
      if (argumentsByName.has(argument)) {
        usageError(`Duplicate argument: ${argument}`);
      }
      argumentsByName.set(argument, true);
      continue;
    }
    const value = argv[index + 1];
    if (!value || value.startsWith("--")) {
      usageError(`Missing value for argument: ${argument}`);
    }
    if (argumentsByName.has(argument)) {
      usageError(`Duplicate argument: ${argument}`);
    }
    argumentsByName.set(argument, value);
    index += 1;
  }

  const cdpEndpoint = argumentsByName.get("--cdp-endpoint");
  const userDataDir = argumentsByName.get("--user-data-dir");
  const model = argumentsByName.get("--model");
  const effort = argumentsByName.get("--effort");
  const promptFile = argumentsByName.get("--prompt-file");
  const probeOnly = argumentsByName.has("--probe-only");
  const contextIndexValue = argumentsByName.get("--context-index");

  if (!cdpEndpoint && !userDataDir) usageError("Missing one of: --cdp-endpoint or --user-data-dir");
  if (cdpEndpoint && userDataDir) usageError("Use only one of: --cdp-endpoint or --user-data-dir");
  if (!cdpEndpoint && contextIndexValue !== undefined) {
    usageError("--context-index requires --cdp-endpoint");
  }
  if (!model) usageError("Missing required argument: --model");
  if (!effort) usageError("Missing required argument: --effort");
  if (!probeOnly && !promptFile) usageError("Missing required argument: --prompt-file");
  if (!SUPPORTED_MODELS.has(model)) usageError(`Unsupported model: ${model}`);
  if (!SUPPORTED_EFFORTS.has(effort)) usageError(`Unsupported effort: ${effort}`);

  const contextIndex = contextIndexValue === undefined
    ? DEFAULT_CONTEXT_INDEX
    : Number(contextIndexValue);
  if (!Number.isInteger(contextIndex) || contextIndex < 0) {
    usageError(`Invalid context index: ${contextIndexValue}`);
  }

  return { cdpEndpoint, contextIndex, effort, model, probeOnly, promptFile, userDataDir };
}
async function main(argv) {
  if (argv.length === 1 && ["-h", "--help"].includes(argv[0])) {
    console.log(USAGE);
    return;
  }
  const options = parseArguments(argv);
  const prompt = options.probeOnly ? undefined : await readFile(options.promptFile, "utf8");
  if (!options.probeOnly && !prompt.trim()) usageError("Prompt file must not be empty");

  let chromium;
  try {
    ({ chromium } = await import("playwright"));
  } catch (error) {
    const detail = error instanceof Error ? `: ${error.message}` : "";
    throw new Error(`Playwright is required for the Node review runner${detail}`);
  }

  let browser;
  let context;
  let ownsContext = false;
  if (options.cdpEndpoint) {
    browser = await chromium.connectOverCDP(options.cdpEndpoint);
    const contexts = browser.contexts();
    context = contexts[options.contextIndex];
    if (!context) {
      throw new Error(
        `Authenticated browser context not found at index ${options.contextIndex}; available contexts: ${contexts.length}`,
      );
    }
  } else {
    try {
      context = await chromium.launchPersistentContext(options.userDataDir, {
        headless: false,
      });
      ownsContext = true;
    } catch (error) {
      const detail = error instanceof Error ? `: ${error.message}` : "";
      throw new Error(`Could not launch the Playwright browser profile${detail}`);
    }
  }

  try {
    const { page, ...result } = options.probeOnly
      ? await probeReviewModelInNewTab(context, {
        effort: options.effort,
        model: options.model,
      })
      : await runReviewPromptInNewTab(context, {
        effort: options.effort,
        model: options.model,
        prompt,
      });
    const expectedSubmissionState = options.probeOnly ? false : true;
    if (result.promptSubmitted !== expectedSubmissionState) {
      throw new Error(
        options.probeOnly
          ? "Model and effort probe was not confirmed by the helper"
          : "Review prompt submission was not confirmed by the helper",
      );
    }
    console.log(JSON.stringify({ ...result, pageUrl: page.url() }));
  } finally {
    if (ownsContext) {
      await context.close();
    } else {
      await browser.close();
    }
  }
}

try {
  await main(process.argv.slice(2));
} catch (error) {
  const message = error instanceof Error ? error.message : String(error);
  console.error(message);
  process.exitCode = 1;
}
