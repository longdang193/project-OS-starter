#!/usr/bin/env node

import { createHash, randomUUID } from "node:crypto";
import { existsSync, realpathSync } from "node:fs";
import { mkdir, mkdtemp, open, readFile, rename, rm, writeFile } from "node:fs/promises";
import process from "node:process";
import { pathToFileURL } from "node:url";
import { basename, dirname, join, relative, resolve } from "node:path";

import {
  captureVisibleEvidence,
  runReviewPromptInNewTab,
  preflightAuthenticatedContext,
  AMBIGUOUS_DISPATCH_TIMEOUT_MS,
  waitForReviewCompletion,
} from "./run-review-prompt.mjs";
import {
  SUPPORTED_EFFORTS,
  SUPPORTED_MODELS,
} from "./select-review-model.mjs";

const DEFAULT_CONTEXT_INDEX = 0;
const DEFAULT_OUTPUT_DIR = "review-output";
const PROFILE_LEASE_SUFFIX = ".codex-review-profile.lock";
const PROJECT_PROFILE_MARKER = "github-review";
const VALUE_ARGUMENTS = new Set([
  "--cdp-endpoint",
  "--commit-sha",
  "--context-index",
  "--effort",
  "--model",
  "--output-dir",
  "--prompt-file",
  "--project-key",
  "--repository",
  "--review-url",
  "--batch-file",
  "--user-data-dir",
]);
const USAGE = "Usage: node run-review-prompt-cli.mjs (--user-data-dir <path> | --cdp-endpoint <url>) [--project-key <owner-repository>] (--model <GPT-5.6-Sol|GPT-6> --effort <Instant|Medium|High> --prompt-file <path> --repository <owner/repository> --commit-sha <sha> --review-url <url>...) | --batch-file <path>) [--output-dir <path>] [--context-index <number>]";
const FLAG_ARGUMENTS = new Set();
const FULL_SHA_PATTERN = /^[0-9a-f]{40}$/i;
const GITHUB_BLOB_URL_PATTERN = /https:\/\/github\.com\/[^\s<>"']+/gi;

function usageError(message) {
  throw new Error(`${message}\n${USAGE}`);
}

export function parseArguments(argv) {
  const argumentsByName = new Map();
  for (let index = 0; index < argv.length; index += 1) {
    const argument = argv[index];
    if (!argument.startsWith("--")) usageError(`Unexpected argument: ${argument}`);
    if (!FLAG_ARGUMENTS.has(argument) && !VALUE_ARGUMENTS.has(argument)) usageError(`Unknown argument: ${argument}`);
    if (FLAG_ARGUMENTS.has(argument)) {
      if (argumentsByName.has(argument)) usageError(`Duplicate argument: ${argument}`);
      argumentsByName.set(argument, true);
      continue;
    }

    const value = argv[index + 1];
    if (!value || value.startsWith("--")) usageError(`Missing value for argument: ${argument}`);
    if (argument === "--review-url") {
      const reviewUrls = argumentsByName.get(argument) || [];
      reviewUrls.push(value);
      argumentsByName.set(argument, reviewUrls);
    } else {
      if (argumentsByName.has(argument)) usageError(`Duplicate argument: ${argument}`);
      argumentsByName.set(argument, value);
    }
    index += 1;
  }

  const cdpEndpoint = argumentsByName.get("--cdp-endpoint");
  const commitSha = argumentsByName.get("--commit-sha");
  const userDataDir = argumentsByName.get("--user-data-dir");
  const model = argumentsByName.get("--model");
  const effort = argumentsByName.get("--effort");
  const promptFile = argumentsByName.get("--prompt-file");
  const projectKey = argumentsByName.get("--project-key");
  const repository = argumentsByName.get("--repository");
  const reviewUrls = argumentsByName.get("--review-url") || [];
  const batchFile = argumentsByName.get("--batch-file");
  const contextIndexValue = argumentsByName.get("--context-index");
  const outputDir = argumentsByName.get("--output-dir") || DEFAULT_OUTPUT_DIR;

  if (!cdpEndpoint && !userDataDir) usageError("Missing one of: --cdp-endpoint or --user-data-dir");
  if (cdpEndpoint && userDataDir) usageError("Use only one of: --cdp-endpoint or --user-data-dir");
  if (userDataDir && !projectKey) usageError("Missing required argument: --project-key for --user-data-dir");
  if (cdpEndpoint && projectKey) usageError("--project-key requires --user-data-dir");
  if (userDataDir) argumentsByName.set("--user-data-dir", validateProjectProfilePath(userDataDir));
  if (!cdpEndpoint && contextIndexValue !== undefined) usageError("--context-index requires --cdp-endpoint");
  if (batchFile && (model || effort || promptFile || repository || commitSha || reviewUrls.length > 0)) {
    usageError("Single-review arguments cannot be combined with --batch-file");
  }
  if (!batchFile && !model) usageError("Missing required argument: --model");
  if (!batchFile && !effort) usageError("Missing required argument: --effort");
  if (!batchFile && !promptFile) usageError("Missing required argument: --prompt-file");
  if (model && !SUPPORTED_MODELS.has(model)) usageError(`Unsupported model: ${model}`);
  if (effort && !SUPPORTED_EFFORTS.has(effort)) usageError(`Unsupported effort: ${effort}`);
  if (!batchFile && !repository) usageError("Missing required argument: --repository");
  if (!batchFile && !commitSha) usageError("Missing required argument: --commit-sha");
  if (!batchFile && reviewUrls.length === 0) usageError("Missing required argument: --review-url");

  const contextIndex = contextIndexValue === undefined ? DEFAULT_CONTEXT_INDEX : Number(contextIndexValue);
  if (!Number.isInteger(contextIndex) || contextIndex < 0) usageError(`Invalid context index: ${contextIndexValue}`);

  return {
    cdpEndpoint,
    contextIndex,
    contextIndexProvided: contextIndexValue !== undefined,
    commitSha,
    effort,
    model,
    batchFile,
    outputDir,
    promptFile,
    projectKey,
    repository,
    reviewUrls,
    userDataDir: userDataDir ? resolve(userDataDir) : undefined,
  };
}

export function deriveProjectKey(repository) {
  if (typeof repository !== "string") throw new Error("repository must be an owner/repository identifier");
  const match = repository.trim().match(/^([^/\s]+)\/([^/\s]+)$/);
  if (!match) throw new Error("repository must use the owner/repository form");
  return `${match[1]}-${match[2]}`.toLowerCase();
}

function normalizeUrlCandidate(value) {
  return value.replace(/[),.;:!?]+$/g, "");
}

export function normalizeGitHubBlobUrl(value) {
  if (typeof value !== "string" || !value.trim()) throw new Error("review URLs must be non-empty strings");
  const candidate = normalizeUrlCandidate(value.trim());
  let parsed;
  try {
    parsed = new URL(candidate);
  } catch (error) {
    throw new Error(`Invalid GitHub review URL: ${value}`, { cause: error });
  }
  const segments = parsed.pathname.split("/").filter(Boolean);
  if (parsed.protocol !== "https:" || parsed.hostname.toLowerCase() !== "github.com" || segments.length < 5 || segments[2] !== "blob" || !segments[3] || !segments.slice(4).join("/")) {
    throw new Error(`Review URL must be a commit-pinned GitHub blob URL: ${value}`);
  }
  if (!FULL_SHA_PATTERN.test(segments[3])) throw new Error(`Review URL must contain a full commit SHA: ${value}`);
  return `https://github.com/${segments[0].toLowerCase()}/${segments[1].toLowerCase()}/blob/${segments[3].toLowerCase()}/${segments.slice(4).join("/")}`;
}

export function extractPromptGitHubBlobUrls(prompt) {
  if (typeof prompt !== "string") return [];
  return [...prompt.matchAll(GITHUB_BLOB_URL_PATTERN)]
    .map((match) => normalizeUrlCandidate(match[0]))
    .filter((value) => value.includes("/blob/"));
}

export function validateReviewProvenance({ repository, commitSha, reviewUrls, prompt }) {
  const normalizedRepository = typeof repository === "string" ? repository.trim().toLowerCase() : "";
  const repositoryMatch = normalizedRepository.match(/^([^/\s]+)\/([^/\s]+)$/);
  if (!repositoryMatch) throw new Error("repository must use the owner/repository form");
  if (!FULL_SHA_PATTERN.test(commitSha || "")) throw new Error("commit_sha must be a full 40-character hexadecimal SHA");
  const normalizedSha = commitSha.toLowerCase();
  if (!Array.isArray(reviewUrls) || reviewUrls.length === 0) throw new Error("review_urls must contain at least one pinned GitHub URL");

  const normalizedUrls = [...new Set(reviewUrls.map(normalizeGitHubBlobUrl))];
  for (const url of normalizedUrls) {
    const parsed = new URL(url);
    const segments = parsed.pathname.split("/").filter(Boolean);
    if (`${segments[0]}/${segments[1]}` !== normalizedRepository || segments[3] !== normalizedSha) {
      throw new Error(`Review URL does not match repository or commit SHA: ${url}`);
    }
  }

  if (!prompt.includes(commitSha) && !prompt.includes(normalizedSha)) {
    throw new Error("Prompt must contain the declared full commit SHA");
  }
  const promptUrls = extractPromptGitHubBlobUrls(prompt).map(normalizeGitHubBlobUrl);
  if (promptUrls.length === 0) throw new Error("Prompt must contain at least one commit-pinned GitHub blob URL");
  const declaredSet = new Set(normalizedUrls);
  for (const url of promptUrls) {
    if (!declaredSet.has(url)) throw new Error(`Prompt contains an undeclared or conflicting review URL: ${url}`);
  }
  for (const url of normalizedUrls) {
    if (!promptUrls.includes(url)) throw new Error(`Declared review URL is missing from the prompt: ${url}`);
  }

  return {
    repository: `${repositoryMatch[1]}/${repositoryMatch[2]}`,
    commitSha: normalizedSha,
    reviewUrls: normalizedUrls,
    projectKey: deriveProjectKey(`${repositoryMatch[1]}/${repositoryMatch[2]}`),
  };
}

function canonicalProfilePath(userDataDir) {
  let currentPath = resolve(userDataDir);
  const missingSegments = [];
  while (!existsSync(currentPath)) {
    const parentPath = dirname(currentPath);
    if (parentPath === currentPath) return currentPath;
    missingSegments.unshift(basename(currentPath));
    currentPath = parentPath;
  }
  const resolvedExistingPath = (realpathSync.native || realpathSync)(currentPath);
  return resolve(resolvedExistingPath, ...missingSegments);
}

export function validateProjectProfilePath(userDataDir, expectedProjectKey) {
  if (typeof userDataDir !== "string" || !userDataDir.trim()) {
    usageError("--user-data-dir must point to a dedicated project profile");
  }

  const profilePath = canonicalProfilePath(userDataDir);
  const segments = profilePath.split(/[\\/]+/).filter(Boolean);
  const markerIndex = segments.findIndex((segment) => segment.toLowerCase() === PROJECT_PROFILE_MARKER);
  const normalProfile = segments.some((segment) => {
    const normalized = segment.toLowerCase();
    return normalized === "user data" || normalized === "default" || /^profile \d+$/.test(normalized);
  });

  if (normalProfile || markerIndex < 0 || markerIndex === segments.length - 1) {
    usageError("--user-data-dir must resolve to a dedicated github-review/<project> profile, not the normal Chrome profile");
  }
  if (expectedProjectKey && basename(profilePath).toLowerCase() !== expectedProjectKey.toLowerCase()) {
    usageError(`--user-data-dir terminal directory must match project key: ${expectedProjectKey}`);
  }

  return profilePath;
}

export function createResult(options) {
  const prompt = typeof options.prompt === "string" ? options.prompt : "";
  const promptHash = prompt ? createHash("sha256").update(prompt, "utf8").digest("hex") : null;
  return {
    status: "running",
    run_id: options.runId || null,
    model_requested: options.model,
    model_verified: null,
    effort_requested: options.effort,
    effort_verified: null,
    submission_attempted: false,
    submission: "not_started",
    dispatch_state: "not_dispatched",
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
    visible_evidence: null,
    review_index: options.reviewIndex ?? null,
    request_provenance: {
      prompt_file: options.promptFile || null,
      prompt_sha256: promptHash,
      repository: options.repository || null,
      commit_sha: options.commitSha || null,
      review_urls: Array.isArray(options.reviewUrls) ? [...options.reviewUrls] : [],
    },
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

    const provenance = validateReviewProvenance({
      repository: review.repository,
      commitSha: review.commit_sha || review.commitSha,
      reviewUrls: review.review_urls,
      prompt,
    });

    return {
      effort: review.effort,
      model: review.model,
      prompt,
      promptFile,
      repository: provenance.repository,
      commitSha: provenance.commitSha,
      reviewUrls: provenance.reviewUrls,
      projectKey: provenance.projectKey,
      reviewIndex: index,
    };
  }));
}

export function summarizeBatchResults(results, requestedCount = results.length) {
  const completedCount = results.filter((result) => result.status === "completed").length;
  const skippedCount = results.filter((result) => result.status === "skipped").length;
  const attemptedCount = results.filter((result) => result.status !== "skipped").length;
  return {
    status: completedCount === requestedCount ? "completed" : "incomplete",
    review_count: requestedCount,
    requested_count: requestedCount,
    attempted_count: attemptedCount,
    completed_count: completedCount,
    failed_count: results.filter((result) => result.status !== "completed" && result.status !== "skipped").length,
    skipped_count: skippedCount,
    reviews: results,
  };
}

export function validateReviewBatch(reviews, { projectKey, repository } = {}) {
  if (!Array.isArray(reviews) || reviews.length === 0) {
    throw new Error("reviews must contain at least one review");
  }
  const expectedProjectKey = projectKey?.toLowerCase() || (repository ? deriveProjectKey(repository) : null);
  if (!expectedProjectKey) throw new Error("runReviewBatch requires an attached project key or repository");
  const expectedRepository = repository?.toLowerCase() || null;

  return reviews.map((review, index) => {
    if (!review || typeof review !== "object") throw new Error(`Review ${index + 1} must be an object`);
    if (!SUPPORTED_MODELS.has(review.model)) throw new Error(`Review ${index + 1} has unsupported model: ${review.model}`);
    if (!SUPPORTED_EFFORTS.has(review.effort)) throw new Error(`Review ${index + 1} has unsupported effort: ${review.effort}`);
    const provenance = validateReviewProvenance({
      repository: review.repository,
      commitSha: review.commitSha || review.commit_sha,
      reviewUrls: review.reviewUrls || review.review_urls,
      prompt: review.prompt,
    });
    if (expectedRepository && provenance.repository.toLowerCase() !== expectedRepository) {
      throw new Error(`Review ${index + 1} repository does not match the attached project: ${provenance.repository}`);
    }
    if (provenance.projectKey !== expectedProjectKey) {
      throw new Error(`Review ${index + 1} project key does not match the attached project: ${provenance.projectKey}`);
    }
    return { ...review, ...provenance };
  });
}

function profileLeasePath(userDataDir) {
  return `${canonicalProfilePath(userDataDir)}${PROFILE_LEASE_SUFFIX}`;
}

export async function acquireProfileLease(
  userDataDir,
  { writeMetadata = defaultWriteLeaseMetadata, isProcessAlive = defaultIsProcessAlive } = {},
) {
  const profilePath = canonicalProfilePath(userDataDir);
  const lockPath = profileLeasePath(profilePath);
  await mkdir(dirname(profilePath), { recursive: true });

  let handle;
  try {
    handle = await open(lockPath, "wx");
  } catch (error) {
    if (error?.code !== "EEXIST") throw error;
    let metadata;
    try {
      metadata = JSON.parse(await readFile(lockPath, "utf8"));
    } catch (metadataError) {
      throw new Error(`ambiguous profile lease ownership: ${profilePath}`, { cause: metadataError });
    }
    if (!metadata || !Number.isInteger(metadata.pid) || typeof metadata.token !== "string" || metadata.profile !== profilePath) {
      throw new Error(`ambiguous profile lease ownership: ${profilePath}`);
    }
    const ownerAlive = await isProcessAlive(metadata.pid);
    if (ownerAlive) {
      throw new Error(`Browser profile is already in use: ${profilePath}`);
    }
    throw new Error(`Stale profile lease requires operator-confirmed recovery: ${profilePath}; lock path: ${lockPath}; after confirming PID ${metadata.pid} is dead, run Remove-Item -LiteralPath '${lockPath}'`);
  }

  const token = randomUUID();
  try {
    await writeMetadata(handle, { pid: process.pid, profile: profilePath, token, started_at: new Date().toISOString() });
    return { handle, lockPath, profilePath, token };
  } catch (error) {
    await handle.close().catch(() => {});
    await rm(lockPath, { force: true }).catch(() => {});
    throw error;
  }
}

async function defaultWriteLeaseMetadata(handle, metadata) {
  await handle.writeFile(`${JSON.stringify(metadata)}\n`, "utf8");
}

async function defaultIsProcessAlive(pid) {
  try {
    process.kill(pid, 0);
    return true;
  } catch (error) {
    return error?.code !== "ESRCH";
  }
}

export async function releaseProfileLease(lease) {
  if (!lease) return;
  await lease.handle?.close().catch(() => {});
  if (!lease.token) return;
  let metadata;
  try {
    metadata = JSON.parse(await readFile(lease.lockPath, "utf8"));
  } catch (error) {
    if (error?.code === "ENOENT") return;
    throw new Error(`Profile lease ownership is ambiguous: ${lease.profilePath || lease.lockPath}`, { cause: error });
  }
  if (metadata?.token !== lease.token) return;
  await rm(lease.lockPath, { force: true });
}

export async function persistCleanupFailure(result, outputDir, cleanupReason) {
  result.status = "incomplete";
  result.cleanup_status = "failed";
  result.cleanup_warning = cleanupReason;
  result.failure_scope = result.failure_scope || "shared_context";
  result.failure_stage = "cleanup";
  result.failure_reason = cleanupReason;
  if (outputDir) await writeResult(outputDir, result);
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

export async function openContext(chromium, options) {
  if (options.cdpEndpoint) {
    const browser = await chromium.connectOverCDP(options.cdpEndpoint);
    const contexts = browser.contexts();
    if (contexts.length > 1 && !options.contextIndexProvided) {
      await browser.close().catch(() => {});
      throw new Error(`Explicit --context-index is required when multiple authenticated browser contexts exist; available contexts: ${contexts.length}`);
    }
    const context = contexts[options.contextIndex];
    if (!context) {
      await browser.close().catch(() => {});
      throw new Error(`Authenticated browser context not found at index ${options.contextIndex}; available contexts: ${contexts.length}`);
    }
    return { browser, context, ownsContext: false };
  }

  const derivedProjectKey = deriveProjectKey(options.repository);
  if (options.projectKey?.toLowerCase() !== derivedProjectKey) {
    throw new Error(`Project key does not match repository-derived key: expected ${derivedProjectKey}`);
  }
  const profilePath = validateProjectProfilePath(options.userDataDir, derivedProjectKey);
  const profileLease = await acquireProfileLease(profilePath);
  try {
    const context = await chromium.launchPersistentContext(profilePath, { headless: false });
    return {
      browser: null,
      context,
      ownsContext: true,
      profileLease,
      profilePath,
      projectKey: derivedProjectKey,
      repository: options.repository,
    };
  } catch (error) {
    await releaseProfileLease(profileLease).catch(() => {});
    const detail = error instanceof Error ? `: ${error.message}` : "";
    throw new Error(`Could not launch the Playwright browser profile${detail}`);
  }
}

export async function openReviewContext(options) {
  const chromium = await loadPlaywright();
  const attached = await openContext(chromium, options);
  try {
    await preflightAuthenticatedContext(attached.context);
    return attached;
  } catch (error) {
    await closeContext(attached).catch(() => {});
    throw error;
  }
}

export async function closeContext(attached) {
  if (attached?.closed) return;
  if (!attached) return;
  const { browser, context, ownsContext, page, profileLease } = attached;
  let cleanupError;
  let ownedContextClosed = !ownsContext;
  try {
    if (ownsContext && context) {
      await context.close();
      ownedContextClosed = true;
    }
  } catch (error) {
    cleanupError = error;
  }
  if (!ownsContext) {
    try {
      if (page) await page.close();
    } catch (error) {
      cleanupError ||= error;
    }
    try {
      if (browser) await browser.close();
    } catch (error) {
      cleanupError ||= error;
    }
  }
  if (ownedContextClosed) {
    try {
      await releaseProfileLease(profileLease);
    } catch (error) {
      cleanupError ||= error;
    }
  }
  if (cleanupError) throw cleanupError;
  attached.closed = true;
}

export function installTerminationCleanup(attached, closeAttachedContext = closeContext) {
  if (!attached) return () => {};

  const handlers = new Map();
  let cleanupPromise;
  for (const signal of ["SIGINT", "SIGTERM"]) {
    const handler = () => {
      process.exitCode = signal === "SIGINT" ? 130 : 143;
      cleanupPromise ||= Promise.resolve(closeAttachedContext(attached)).catch(() => {});
    };
    handlers.set(signal, handler);
    process.once(signal, handler);
  }

  return () => {
    for (const [signal, handler] of handlers) process.removeListener(signal, handler);
  };
}

async function isContextHealthy(context) {
  if (!context || typeof context.pages !== "function") return true;
  try {
    await context.pages();
    return true;
  } catch {
    return false;
  }
}

async function classifyFailureScope(stage, error, context) {
  if (error?.failureScope) return error.failureScope;
  if (!(await isContextHealthy(context))) return "shared_context";
  if (typeof context?.pages !== "function" && /(?:browser|context|target).*(?:closed|close|disconnect)|(?:closed|close|disconnect).*(?:browser|context|target)/i.test(errorMessage(error))) {
    return "shared_context";
  }
  if (stage === "selection") return error?.code === "MODEL_UNAVAILABLE" ? "shared_context" : "review";
  if (stage === "submission" || stage === "completion") return "review";
  return null;
}

function appendFailureReason(currentReason, suffix) {
  return `${currentReason || "Review transaction failed"}; ${suffix}`;
}

function markCleanupFailure(result, cleanupReason) {
  result.cleanup_status = "failed";
  result.cleanup_warning = cleanupReason;
  result.failure_scope = "shared_context";
  if (result.status === "completed") {
    result.status = "incomplete";
    result.failure_stage = "cleanup";
    result.failure_reason = cleanupReason;
  } else {
    result.failure_reason = appendFailureReason(result.failure_reason, `cleanup failed: ${cleanupReason}`);
  }
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
  let dispatchState = "not_dispatched";
  let stage = "artifacts";
  let resultPersisted = false;

  const persist = async () => {
    if (!outputDir) throw new Error("Review output directory was not allocated");
    await persistResult(outputDir, result);
    resultPersisted = true;
  };

  try {
    if (options.runOutputDir) {
      outputDir = resolve(options.runOutputDir);
      runId = options.runId || basename(outputDir);
    } else {
      ({ outputDir, runId } = await createRunOutputDirectory(options.outputDir));
    }
    result = createResult({ ...options, runId });
    result.response_path = relative(process.cwd(), join(outputDir, "response.md"));
    await persist();

    stage = "selection";
    const review = await runPrompt(context, {
      effort: options.effort,
      model: options.model,
      prompt: options.prompt,
      beforeSubmit: async () => {
        stage = "submission";
        result.submission_attempted = true;
        result.submission = "attempted";
        try {
          await persist();
        } catch (error) {
          stage = "artifacts";
          throw error;
        }
      },
    });
    page = review.page;
    if (review.promptSubmitted !== true) {
      stage = "submission";
      throw new Error("Review prompt submission was not confirmed by the helper");
    }
    result.model_verified = review.model;
    result.effort_verified = review.effort;
    result.submission = review.submission;
    dispatchState = review.dispatchState || "acknowledged";
    result.dispatch_state = dispatchState;
    result.completion = "waiting";
    stage = "artifacts";
    await persist();

    stage = "completion";
    const completion = await waitForCompletion(page, { baseline: review });
    result.completion = completion.status;
    result.conversation_url = completion.currentUrl || null;
    result.conversation_id = completion.conversationId || null;
    result.assistant_message_id = completion.assistantMessageId || null;
    result.assistant_turn_index = completion.assistantTurnIndex ?? null;

    if (completion.response) {
      stage = "artifacts";
      await writeResponse(join(outputDir, "response.md"), `${completion.response}\n`);
    }
    if (completion.status === "confirmed") {
      result.status = "completed";
    } else {
      result.status = "incomplete";
      result.failure_scope = "review";
      result.failure_stage = "completion";
      result.failure_reason = completion.failureReason || "Review completion was not confirmed";
    }
  } catch (error) {
    const transactionFailureReason = errorMessage(error);
    dispatchState = error.dispatchState
      || (error.submissionAttempted || (stage === "submission" && result.submission_attempted) ? "possibly_dispatched" : dispatchState);
    result.dispatch_state = dispatchState;
    if (error.visibleEvidence) result.visible_evidence = error.visibleEvidence;
    if (error?.reviewPage) {
      page = error.reviewPage;
      const baseline = error.reviewBaseline;
      let currentUrl = null;
      try {
        currentUrl = typeof page.url === "function" ? page.url() : null;
      } catch {
        currentUrl = null;
      }
      result.conversation_url = baseline?.conversationUrl || currentUrl;
      result.conversation_id = baseline?.conversationId || null;
      if (dispatchState !== "not_dispatched" && baseline) {
        try {
          const timeoutMs = dispatchState === "possibly_dispatched" && result.submission !== "acknowledged"
            ? AMBIGUOUS_DISPATCH_TIMEOUT_MS
            : undefined;
          const completion = await waitForCompletion(page, { baseline, timeoutMs });
          result.completion = completion.status;
          result.conversation_url = completion.currentUrl || result.conversation_url;
          result.conversation_id = completion.conversationId || result.conversation_id;
          result.assistant_message_id = completion.assistantMessageId || null;
          result.assistant_turn_index = completion.assistantTurnIndex ?? null;
          if (completion.response && outputDir) {
            await writeResponse(join(outputDir, "response.md"), `${completion.response}\n`);
          }
        } catch (preservationError) {
          result.failure_reason = appendFailureReason(transactionFailureReason, `evidence preservation failed: ${errorMessage(preservationError)}`);
        }
      }
    }
    if (page && !result.visible_evidence) {
      result.visible_evidence = await captureVisibleEvidence(page).catch(() => null);
    }
    result.status = stage === "artifacts" || stage === "selection" ? "blocked" : "incomplete";
    result.failure_scope = await classifyFailureScope(stage, error, context);
    result.failure_stage = stage;
    result.failure_reason ||= transactionFailureReason;
      if (stage === "submission" && result.submission !== "acknowledged" && dispatchState !== "not_dispatched") {
        result.submission = "ambiguous";
      }
  } finally {
    if (outputDir) {
      try {
        stage = "artifacts";
        result.cleanup_status = page ? "pending" : "not_needed";
        await persist();
      } catch (error) {
        const artifactReason = errorMessage(error);
        if (result.failure_stage !== "artifacts") {
          result.status = "blocked";
          result.failure_stage = "artifacts";
          result.failure_reason = artifactReason;
        } else {
          result.failure_reason = `${result.failure_reason}; result write failed: ${artifactReason}`;
        }
      }
    }

    try {
      if (page) {
        await closePage(page);
        result.cleanup_status = "completed";
      }
    } catch (error) {
      markCleanupFailure(result, errorMessage(error));
    }

    if (outputDir && resultPersisted && (result.cleanup_status === "completed" || result.cleanup_warning)) {
      try {
        await persistResult(outputDir, result);
      } catch (error) {
        const artifactReason = errorMessage(error);
        result.cleanup_warning = result.cleanup_warning
          ? `${result.cleanup_warning}; result update failed: ${artifactReason}`
          : `result update failed: ${artifactReason}`;
        result.status = "incomplete";
        result.failure_stage = "artifacts";
        result.failure_reason = appendFailureReason(result.failure_reason, `final result persistence failed: ${artifactReason}`);
      }
    }
  }

  return {
    ...result,
    output_dir: outputDir ? relative(process.cwd(), outputDir) : null,
  };
}

export async function runReviewBatch({ attached, outputDir, reviews, projectKey, repository, runTransaction = runReviewTransaction }) {
  const results = [];
  let cleanupError;
  try {
    if (!attached?.context) throw new Error("attached authenticated context is required");
    const validatedReviews = validateReviewBatch(reviews, {
      projectKey: projectKey || attached.projectKey,
      repository: repository || attached.repository,
    });

    for (let index = 0; index < validatedReviews.length; index += 1) {
      const review = validatedReviews[index];
      const result = await runTransaction(attached.context, {
        ...review,
        reviewIndex: review.reviewIndex ?? index,
        outputDir,
      });
      results.push(result);
      if (result.status !== "completed" && result.failure_scope !== "review") {
        for (let skippedIndex = index + 1; skippedIndex < validatedReviews.length; skippedIndex += 1) {
          const skippedReview = validatedReviews[skippedIndex];
          results.push({
            ...createResult({ ...skippedReview, reviewIndex: skippedReview.reviewIndex ?? skippedIndex }),
            status: "skipped",
            output_dir: skippedReview.runOutputDir ? relative(process.cwd(), skippedReview.runOutputDir) : null,
            failure_scope: "shared_context",
            failure_stage: "batch",
            failure_reason: `Skipped after review ${index + 1} stopped the shared batch`,
          });
          if (skippedReview.runOutputDir) {
            await writeResult(skippedReview.runOutputDir, results.at(-1)).catch(() => {});
          }
        }
        break;
      }
    }
  } finally {
    if (attached) {
      try {
        await closeContext(attached);
      } catch (error) {
        cleanupError = error;
      }
    }
  }
  if (cleanupError) {
    for (const result of results) {
      if (!result.output_dir) continue;
      try {
        await persistCleanupFailure(result, resolve(result.output_dir), errorMessage(cleanupError));
      } catch {
        // Preserve the batch cleanup error even if a partial result cannot be rewritten.
      }
    }
    const batchError = new Error(`Batch context cleanup failed: ${errorMessage(cleanupError)}`);
    batchError.cause = cleanupError;
    batchError.results = results;
    throw batchError;
  }
  return results;
}

async function allocateReviewArtifacts(
  reviews,
  parentDir,
  { createDirectory = createRunOutputDirectory, persistResult = writeResult } = {},
) {
  const allocated = [];
  try {
    for (const review of reviews) {
      const { outputDir, runId } = await createDirectory(parentDir);
      const allocatedReview = { ...review, runId, runOutputDir: outputDir };
      allocated.push(allocatedReview);
      const initial = createResult(allocatedReview);
      initial.response_path = relative(process.cwd(), join(outputDir, "response.md"));
      await persistResult(outputDir, initial);
    }
    return allocated;
  } catch (error) {
    error.allocatedReviews = allocated;
    throw error;
  }
}

async function settleArtifactAllocationFailure(reviews, allocatedReviews, failureReason) {
  const allocatedByIndex = new Map(allocatedReviews.map((review) => [review.reviewIndex, review]));
  const results = reviews.map((review, index) => {
    const allocated = allocatedByIndex.get(review.reviewIndex ?? index);
    const result = createResult({ ...review, runId: allocated?.runId, reviewIndex: review.reviewIndex ?? index });
    result.status = "blocked";
    result.output_dir = allocated?.runOutputDir ? relative(process.cwd(), allocated.runOutputDir) : null;
    result.failure_scope = "artifacts";
    result.failure_stage = "artifacts";
    result.failure_reason = `Review artifacts could not be allocated before dispatch: ${failureReason}`;
    return { result, allocated };
  });
  await Promise.all(results.map(async ({ result, allocated }) => {
    if (allocated?.runOutputDir) await writeResult(allocated.runOutputDir, result).catch(() => {});
  }));
  return results.map(({ result }) => result);
}

async function persistBatchSummary(outputDir, summary) {
  await atomicWrite(join(resolve(outputDir), "batch-result.json"), `${JSON.stringify(summary, null, 2)}\n`);
}

export async function main(argv, dependencies = {}) {
  if (argv.length === 1 && ["-h", "--help"].includes(argv[0])) {
    console.log(USAGE);
    return 0;
  }

  const openContextForReview = dependencies.openReviewContext || openReviewContext;
  const closeAttachedContext = dependencies.closeContext || closeContext;
  const installCleanup = dependencies.installTerminationCleanup || installTerminationCleanup;
  const runBatch = dependencies.runReviewBatch || runReviewBatch;
  const runTransaction = dependencies.runReviewTransaction || runReviewTransaction;

  const options = parseArguments(argv);
  let reviews;
  if (options.batchFile) {
    reviews = await readBatchReviews(options.batchFile);
  } else {
    const prompt = await readFile(options.promptFile, "utf8");
    const provenance = validateReviewProvenance({
      repository: options.repository,
      commitSha: options.commitSha,
      reviewUrls: options.reviewUrls,
      prompt,
    });
    reviews = [{
      effort: options.effort,
      model: options.model,
      prompt,
      promptFile: options.promptFile,
      ...provenance,
    }];
  }
  if (!options.batchFile && !reviews[0].prompt.trim()) usageError("Prompt file must not be empty");

  const projectKeys = [...new Set(reviews.map((review) => review.projectKey))];
  if (options.userDataDir) {
    if (projectKeys.length !== 1) usageError("Owned-profile batches must target one repository-derived project key");
    if (options.projectKey?.toLowerCase() !== projectKeys[0]) {
      usageError(`--project-key must match the repository-derived project key: ${projectKeys[0]}`);
    }
  }
  const contextOptions = {
    ...options,
    projectKey: options.projectKey || projectKeys[0],
    repository: reviews[0].repository,
  };

  let result;
  let attached;
  let removeTerminationCleanup = () => {};

  try {
    if (options.batchFile) {
      try {
        reviews = await allocateReviewArtifacts(reviews, options.outputDir, {
          createDirectory: dependencies.createRunOutputDirectory,
          persistResult: dependencies.writeResult,
        });
      } catch (error) {
        const allocationResults = await settleArtifactAllocationFailure(
          reviews,
          error.allocatedReviews || [],
          errorMessage(error),
        );
        error.artifactAllocation = true;
        error.results = allocationResults;
        throw error;
      }
    }
    attached = await openContextForReview(contextOptions);
    removeTerminationCleanup = installCleanup(attached, closeAttachedContext);
    if (options.batchFile) {
      result = summarizeBatchResults(await runBatch({
        attached,
        outputDir: options.outputDir,
        reviews,
        projectKey: contextOptions.projectKey,
        repository: contextOptions.repository,
      }));
      try {
        await persistBatchSummary(options.outputDir, result);
      } catch (error) {
        result = {
          ...result,
          status: "incomplete",
          failure_scope: "artifacts",
          failure_stage: "batch_summary",
          failure_reason: `Batch summary persistence failed: ${errorMessage(error)}`,
          batch_summary_persisted: false,
        };
      }
    } else {
      result = await runTransaction(attached.context, {
        effort: options.effort,
        model: options.model,
        outputDir: options.outputDir,
        prompt: reviews[0].prompt,
        promptFile: reviews[0].promptFile,
        repository: reviews[0].repository,
        commitSha: reviews[0].commitSha,
        reviewUrls: reviews[0].reviewUrls,
        runId: reviews[0].runId,
        runOutputDir: reviews[0].runOutputDir,
      });
    }
  } catch (error) {
    if (options.batchFile && error.artifactAllocation && Array.isArray(error.results)) {
      result = {
        ...summarizeBatchResults(error.results, reviews.length),
        status: "blocked",
        failure_scope: "artifacts",
        failure_stage: "artifacts",
        failure_reason: errorMessage(error),
      };
      await persistBatchSummary(options.outputDir, result).catch(() => {});
    } else if (options.batchFile && Array.isArray(error.results)) {
      const cleanupReason = errorMessage(error.cause || error);
      result = {
        ...summarizeBatchResults(error.results),
        status: "incomplete",
        cleanup_status: "failed",
        cleanup_warning: cleanupReason,
        failure_stage: "cleanup",
        failure_reason: cleanupReason,
      };
    } else if (options.batchFile) {
      const reason = errorMessage(error);
      const skipped = await Promise.all(reviews.map(async (review, index) => {
        const skippedResult = {
        ...createResult({ ...review, reviewIndex: review.reviewIndex ?? index }),
        status: "skipped",
        output_dir: relative(process.cwd(), review.runOutputDir),
        failure_scope: "shared_context",
        failure_stage: "browser",
        failure_reason: `Skipped because the shared batch context was unavailable: ${reason}`,
        visible_evidence: error.visibleEvidence || null,
        };
        await writeResult(review.runOutputDir, skippedResult).catch(() => {});
        return skippedResult;
      }));
      result = {
        ...summarizeBatchResults(skipped, reviews.length),
        status: "blocked",
        failure_scope: "shared_context",
        failure_stage: "browser",
        failure_reason: reason,
      };
      await persistBatchSummary(options.outputDir, result).catch(() => {});
    } else {
      result = {
        ...createResult({ ...reviews[0], reviewIndex: reviews[0].reviewIndex ?? 0 }),
        status: "blocked",
        output_dir: relative(process.cwd(), reviews[0].runOutputDir),
        failure_scope: "shared_context",
        failure_stage: "browser",
        failure_reason: errorMessage(error),
        visible_evidence: error.visibleEvidence || null,
      };
      await writeResult(reviews[0].runOutputDir, result).catch(() => {});
    }
  } finally {
    removeTerminationCleanup();
    try {
      if (attached && !options.batchFile) await closeAttachedContext(attached);
    } catch (error) {
      const cleanupReason = error instanceof Error ? error.message : String(error);
      if (!result) {
        result = {
          ...createResult(options),
          status: "incomplete",
          failure_scope: "shared_context",
          failure_stage: "cleanup",
          failure_reason: cleanupReason,
          output_dir: null,
        };
      } else {
        if (result.status === "completed") result.status = "incomplete";
        result.failure_stage = "cleanup";
        result.failure_reason = `${result.failure_reason || ""}${result.failure_reason ? "; " : ""}context cleanup failed: ${cleanupReason}`;
        result.cleanup_status = "failed";
        result.cleanup_warning = cleanupReason;
      }
      if (result.output_dir) {
        await persistCleanupFailure(result, resolve(result.output_dir), cleanupReason).catch(() => {});
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
