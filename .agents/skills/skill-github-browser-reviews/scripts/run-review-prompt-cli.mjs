#!/usr/bin/env node

import { mkdir, mkdtemp, open, readFile, rename, rm, writeFile } from "node:fs/promises";
import process from "node:process";
import { pathToFileURL } from "node:url";
import { basename, dirname, join, relative, resolve } from "node:path";

import {
  runReviewPromptInNewTab,
  waitForReviewCompletion,
} from "./run-review-prompt.mjs";
import {
  SUPPORTED_EFFORTS,
  SUPPORTED_MODELS,
} from "./select-review-model.mjs";

const DEFAULT_CONTEXT_INDEX = 0;
const DEFAULT_OUTPUT_DIR = "review-output";
const PROFILE_LEASE_SUFFIX = ".codex-review-profile.lock";
const USAGE = "Usage: node run-review-prompt-cli.mjs (--user-data-dir <path> | --cdp-endpoint <url>) (--model <GPT-5.6-Sol|GPT-6> --effort <Instant|Medium|High> --prompt-file <path> | --batch-file <path>) [--output-dir <path>] [--context-index <number>]";
const FLAG_ARGUMENTS = new Set();

function usageError(message) {
  throw new Error(`${message}\n${USAGE}`);
}

export function parseArguments(argv) {
  const argumentsByName = new Map();
  for (let index = 0; index < argv.length; index += 1) {
    const argument = argv[index];
    if (!argument.startsWith("--")) usageError(`Unexpected argument: ${argument}`);
    if (FLAG_ARGUMENTS.has(argument)) {
      if (argumentsByName.has(argument)) usageError(`Duplicate argument: ${argument}`);
      argumentsByName.set(argument, true);
      continue;
    }

    const value = argv[index + 1];
    if (!value || value.startsWith("--")) usageError(`Missing value for argument: ${argument}`);
    if (argumentsByName.has(argument)) usageError(`Duplicate argument: ${argument}`);
    argumentsByName.set(argument, value);
    index += 1;
  }

  const cdpEndpoint = argumentsByName.get("--cdp-endpoint");
  const userDataDir = argumentsByName.get("--user-data-dir");
  const model = argumentsByName.get("--model");
  const effort = argumentsByName.get("--effort");
  const promptFile = argumentsByName.get("--prompt-file");
  const batchFile = argumentsByName.get("--batch-file");
  const contextIndexValue = argumentsByName.get("--context-index");
  const outputDir = argumentsByName.get("--output-dir") || DEFAULT_OUTPUT_DIR;

  if (!cdpEndpoint && !userDataDir) usageError("Missing one of: --cdp-endpoint or --user-data-dir");
  if (cdpEndpoint && userDataDir) usageError("Use only one of: --cdp-endpoint or --user-data-dir");
  if (!cdpEndpoint && contextIndexValue !== undefined) usageError("--context-index requires --cdp-endpoint");
  if (batchFile && (model || effort || promptFile)) usageError("Single-review arguments cannot be combined with --batch-file");
  if (!batchFile && !model) usageError("Missing required argument: --model");
  if (!batchFile && !effort) usageError("Missing required argument: --effort");
  if (!batchFile && !promptFile) usageError("Missing required argument: --prompt-file");
  if (model && !SUPPORTED_MODELS.has(model)) usageError(`Unsupported model: ${model}`);
  if (effort && !SUPPORTED_EFFORTS.has(effort)) usageError(`Unsupported effort: ${effort}`);

  const contextIndex = contextIndexValue === undefined ? DEFAULT_CONTEXT_INDEX : Number(contextIndexValue);
  if (!Number.isInteger(contextIndex) || contextIndex < 0) usageError(`Invalid context index: ${contextIndexValue}`);

  return {
    cdpEndpoint,
    contextIndex,
    effort,
    model,
    batchFile,
    outputDir,
    promptFile,
    userDataDir,
  };
}

export function createResult(options) {
  return {
    status: "running",
    run_id: options.runId || null,
    model_requested: options.model,
    model_verified: null,
    effort_requested: options.effort,
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
  };
}

export async function createRunOutputDirectory(parentDir) {
  const parent = resolve(parentDir);
  await mkdir(parent, { recursive: true });
  const outputDir = await mkdtemp(join(parent, "run-"));
  return { outputDir, runId: basename(outputDir) };
}

export async function atomicWrite(filePath, content) {
  const tempPath = `${filePath}.${process.pid}.tmp`;
  try {
    await writeFile(tempPath, content, "utf8");
    await rename(tempPath, filePath);
  } finally {
    await rm(tempPath, { force: true }).catch(() => {});
  }
}

export async function writeResult(outputDir, result) {
  await atomicWrite(join(outputDir, "result.json"), `${JSON.stringify(result, null, 2)}\n`);
}

function errorMessage(error) {
  return error instanceof Error ? error.message : String(error);
}

export async function readBatchReviews(batchFile) {
  const manifestPath = resolve(batchFile);
  let manifest;
  try {
    manifest = JSON.parse(await readFile(manifestPath, "utf8"));
  } catch (error) {
    throw new Error(`Could not read batch manifest ${manifestPath}: ${errorMessage(error)}`);
  }

  if (!manifest || typeof manifest !== "object" || !Array.isArray(manifest.reviews) || manifest.reviews.length === 0) {
    throw new Error("Batch manifest must contain a non-empty reviews array");
  }

  return Promise.all(manifest.reviews.map(async (review, index) => {
    if (!review || typeof review !== "object") {
      throw new Error(`Batch review ${index + 1} must be an object`);
    }
    if (!SUPPORTED_MODELS.has(review.model)) {
      throw new Error(`Batch review ${index + 1} has unsupported model: ${review.model}`);
    }
    if (!SUPPORTED_EFFORTS.has(review.effort)) {
      throw new Error(`Batch review ${index + 1} has unsupported effort: ${review.effort}`);
    }
    if (typeof review.prompt_file !== "string" || !review.prompt_file.trim()) {
      throw new Error(`Batch review ${index + 1} must provide prompt_file`);
    }

    const promptFile = resolve(dirname(manifestPath), review.prompt_file);
    let prompt;
    try {
      prompt = await readFile(promptFile, "utf8");
    } catch (error) {
      throw new Error(`Could not read prompt file for batch review ${index + 1}: ${errorMessage(error)}`);
    }
    if (!prompt.trim()) throw new Error(`Prompt file for batch review ${index + 1} must not be empty`);

    return {
      effort: review.effort,
      model: review.model,
      prompt,
      promptFile,
    };
  }));
}

export function summarizeBatchResults(results) {
  const completedCount = results.filter((result) => result.status === "completed").length;
  return {
    status: completedCount === results.length ? "completed" : "incomplete",
    review_count: results.length,
    completed_count: completedCount,
    failed_count: results.length - completedCount,
    reviews: results,
  };
}

function profileLeasePath(userDataDir) {
  return `${resolve(userDataDir)}${PROFILE_LEASE_SUFFIX}`;
}

export async function acquireProfileLease(userDataDir) {
  const profilePath = resolve(userDataDir);
  const lockPath = profileLeasePath(profilePath);
  await mkdir(dirname(profilePath), { recursive: true });

  let handle;
  try {
    handle = await open(lockPath, "wx");
    await handle.writeFile(`${JSON.stringify({ pid: process.pid, profile: profilePath })}\n`, "utf8");
    return { handle, lockPath };
  } catch (error) {
    await handle?.close().catch(() => {});
    if (error?.code === "EEXIST") {
      throw new Error(`Browser profile is already in use: ${profilePath}`);
    }
    throw error;
  }
}

export async function releaseProfileLease(lease) {
  if (!lease) return;
  await lease.handle?.close().catch(() => {});
  await rm(lease.lockPath, { force: true });
}

export async function persistCleanupFailure(result, outputDir, cleanupReason) {
  result.status = "incomplete";
  result.cleanup_status = "failed";
  result.cleanup_warning = cleanupReason;
  result.failure_stage = "cleanup";
  result.failure_reason = cleanupReason;
  if (outputDir) await writeResult(outputDir, result);
}

function structuredFailure({ error, failureStage, outputDir }) {
  return {
    status: "blocked",
    failure_stage: failureStage,
    failure_reason: error instanceof Error ? error.message : String(error),
    output_dir: outputDir || null,
  };
}

async function loadPlaywright() {
  try {
    const { chromium } = await import("playwright");
    return chromium;
  } catch (error) {
    const detail = error instanceof Error ? `: ${error.message}` : "";
    throw new Error(`Playwright is required for the Node review runner${detail}`);
  }
}

async function openContext(chromium, options) {
  if (options.cdpEndpoint) {
    const browser = await chromium.connectOverCDP(options.cdpEndpoint);
    const contexts = browser.contexts();
    const context = contexts[options.contextIndex];
    if (!context) {
      await browser.close().catch(() => {});
      throw new Error(`Authenticated browser context not found at index ${options.contextIndex}; available contexts: ${contexts.length}`);
    }
    return { browser, context, ownsContext: false };
  }

  const profileLease = await acquireProfileLease(options.userDataDir);
  try {
    const context = await chromium.launchPersistentContext(options.userDataDir, { headless: false });
    return { browser: null, context, ownsContext: true, profileLease };
  } catch (error) {
    await releaseProfileLease(profileLease).catch(() => {});
    const detail = error instanceof Error ? `: ${error.message}` : "";
    throw new Error(`Could not launch the Playwright browser profile${detail}`);
  }
}

export async function openReviewContext(options) {
  const chromium = await loadPlaywright();
  return openContext(chromium, options);
}

export async function closeContext({ browser, context, ownsContext, page, profileLease }) {
  let cleanupError;
  try {
    if (ownsContext && context) {
      await context.close();
    } else {
      try {
        if (page) await page.close();
      } catch (error) {
        cleanupError = error;
      }
      try {
        if (browser) await browser.close();
      } catch (error) {
        cleanupError ||= error;
      }
    }
  } catch (error) {
    cleanupError ||= error;
  }
  try {
    await releaseProfileLease(profileLease);
  } catch (error) {
    cleanupError ||= error;
  }
  if (cleanupError) throw cleanupError;
}

export async function runReviewTransaction(context, options) {
  const dependencies = options.dependencies || {};
  const runPrompt = dependencies.runReviewPromptInNewTab || runReviewPromptInNewTab;
  const waitForCompletion = dependencies.waitForReviewCompletion || waitForReviewCompletion;
  const persistResult = dependencies.writeResult || writeResult;
  const writeResponse = dependencies.writeResponse || ((filePath, content) => atomicWrite(filePath, content));
  const closePage = dependencies.closePage || ((reviewPage) => reviewPage.close());
  let result = createResult(options);
  let outputDir;
  let runId;
  let page;
  let failure;

  try {
    ({ outputDir, runId } = await createRunOutputDirectory(options.outputDir));
    result = createResult({ ...options, runId });
    result.response_path = relative(process.cwd(), join(outputDir, "response.md"));
    await persistResult(outputDir, result);

    const review = await runPrompt(context, {
      effort: options.effort,
      model: options.model,
      prompt: options.prompt,
      beforeSubmit: async () => {
        result.submission_attempted = true;
        result.submission = "attempted";
        await persistResult(outputDir, result);
      },
    });
    page = review.page;
    if (review.promptSubmitted !== true) throw new Error("Review prompt submission was not confirmed by the helper");
    result.model_verified = review.model;
    result.effort_verified = review.effort;
    result.submission = review.submission;
    result.completion = "waiting";
    result.cleanup_status = "pending";
    await persistResult(outputDir, result);

    const completion = await waitForCompletion(page, { baseline: review });
    result.completion = completion.status;
    result.conversation_url = completion.currentUrl || null;
    result.conversation_id = completion.conversationId || null;
    result.assistant_message_id = completion.assistantMessageId || null;
    result.assistant_turn_index = completion.assistantTurnIndex ?? null;

    if (completion.response) await writeResponse(join(outputDir, "response.md"), `${completion.response}\n`);
    if (completion.status === "confirmed") {
      result.status = "completed";
    } else {
      result.status = "incomplete";
      result.failure_scope = "review";
      result.failure_stage = "completion";
      result.failure_reason = completion.failureReason || "Review completion was not confirmed";
    }
  } catch (error) {
    failure = error;
    result.status = result.submission_attempted ? "incomplete" : "blocked";
    result.failure_stage = result.submission_attempted ? "submission" : "browser";
    result.failure_scope = result.submission_attempted ? "review" : "shared_context";
    result.failure_reason = error instanceof Error ? error.message : String(error);
    result.submission = result.submission_attempted ? "ambiguous" : result.submission;
  } finally {
    if (page) result.cleanup_status = "pending";
    try {
      if (page) {
        await closePage(page);
        result.cleanup_status = "completed";
      } else {
        result.cleanup_status = "not_needed";
      }
    } catch (error) {
      const cleanupReason = error instanceof Error ? error.message : String(error);
      result.cleanup_status = "failed";
      result.cleanup_warning = cleanupReason;
      if (!failure && result.status === "completed") {
        result.status = "incomplete";
        result.failure_scope = "review";
        result.failure_stage = "cleanup";
        result.failure_reason = cleanupReason;
      } else {
        result.failure_reason = `${result.failure_reason || "Review transaction failed"}; cleanup failed: ${cleanupReason}`;
      }
    }

    try {
      if (!outputDir) throw new Error("Review output directory was not allocated");
      await persistResult(outputDir, result);
    } catch (error) {
      console.error(JSON.stringify(structuredFailure({
        error,
        failureStage: "artifacts",
        outputDir,
      })));
      result.status = "blocked";
      result.failure_stage = "artifacts";
      result.failure_reason = error instanceof Error ? error.message : String(error);
    }
  }

  return {
    ...result,
    output_dir: outputDir ? relative(process.cwd(), outputDir) : null,
  };
}

export async function runReviewBatch({ attached, outputDir, reviews, runTransaction = runReviewTransaction }) {
  if (!attached?.context) throw new Error("attached authenticated context is required");
  if (!Array.isArray(reviews) || reviews.length === 0) throw new Error("reviews must contain at least one review");

  const results = [];
  try {
    for (const review of reviews) {
      const result = await runTransaction(attached.context, {
        ...review,
        outputDir,
      });
      results.push(result);
      if (result.failure_scope === "shared_context") break;
    }
  } finally {
    try {
      await closeContext(attached);
    } catch (error) {
      const cleanupReason = error instanceof Error ? error.message : String(error);
      for (const result of results) {
        if (result.output_dir) {
          await persistCleanupFailure(result, resolve(result.output_dir), cleanupReason);
        }
      }
      const batchError = new Error(`Batch context cleanup failed: ${cleanupReason}`);
      batchError.cause = error;
      batchError.results = results;
      throw batchError;
    }
  }
  return results;
}

export async function main(argv, dependencies = {}) {
  if (argv.length === 1 && ["-h", "--help"].includes(argv[0])) {
    console.log(USAGE);
    return 0;
  }

  const openContextForReview = dependencies.openReviewContext || openReviewContext;
  const closeAttachedContext = dependencies.closeContext || closeContext;
  const runBatch = dependencies.runReviewBatch || runReviewBatch;
  const runTransaction = dependencies.runReviewTransaction || runReviewTransaction;
  const options = parseArguments(argv);
  const reviews = options.batchFile
    ? await readBatchReviews(options.batchFile)
    : [{
      effort: options.effort,
      model: options.model,
      prompt: await readFile(options.promptFile, "utf8"),
      promptFile: options.promptFile,
    }];
  if (!options.batchFile && !reviews[0].prompt.trim()) usageError("Prompt file must not be empty");

  let result;
  let attached;

  try {
    attached = await openContextForReview(options);
    if (options.batchFile) {
      result = summarizeBatchResults(await runBatch({
        attached,
        outputDir: options.outputDir,
        reviews,
      }));
    } else {
      result = await runTransaction(attached.context, {
        effort: options.effort,
        model: options.model,
        outputDir: options.outputDir,
        prompt: reviews[0].prompt,
      });
    }
  } catch (error) {
    if (options.batchFile && Array.isArray(error.results)) {
      const cleanupReason = errorMessage(error.cause || error);
      result = {
        ...summarizeBatchResults(error.results),
        status: "incomplete",
        failure_stage: "cleanup",
        failure_reason: cleanupReason,
        cleanup_status: "failed",
        cleanup_warning: cleanupReason,
      };
    } else {
      result = {
        ...createResult(options),
        status: "blocked",
        failure_stage: "browser",
        failure_scope: "shared_context",
        failure_reason: errorMessage(error),
        output_dir: null,
      };
    }
  } finally {
    try {
      if (attached && !options.batchFile) await closeAttachedContext(attached);
    } catch (error) {
      const cleanupReason = error instanceof Error ? error.message : String(error);
      if (!result) {
        result = {
          ...createResult(options),
          status: "incomplete",
          failure_stage: "cleanup",
          failure_scope: "shared_context",
          failure_reason: cleanupReason,
          output_dir: null,
        };
      } else {
        const priorReason = result.failure_reason;
        await persistCleanupFailure(
          result,
          result.output_dir ? resolve(result.output_dir) : null,
          `${priorReason || ""}${priorReason ? "; " : ""}cleanup failed: ${cleanupReason}`,
        );
      }
    }
  }

  console.log(JSON.stringify(result));
  return result.status === "completed" ? 0 : 1;
}

if (process.argv[1] && import.meta.url === pathToFileURL(process.argv[1]).href) {
  try {
    process.exitCode = await main(process.argv.slice(2));
  } catch (error) {
    console.error(error instanceof Error ? error.message : String(error));
    process.exitCode = 1;
  }
}
