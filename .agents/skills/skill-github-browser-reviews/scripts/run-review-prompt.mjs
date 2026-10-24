import { MENU_TRANSITION_TIMEOUT_MS, selectReviewModel } from "./select-review-model.mjs";

const CHATGPT_URL = "https://chatgpt.com/";
export const UI_ACTION_TIMEOUT_MS = 5000;
export const COMPOSER_READINESS_TIMEOUT_MS = 10000;
export const ASSISTANT_TURN_SELECTOR = '[data-message-author-role="assistant"]:visible:not([data-message-author-role="assistant"] [data-message-author-role="assistant"])';
const ASSISTANT_FALLBACK_SELECTOR = 'main [class*="MarkdownRoot-"]:visible:not(.rich-text-user-turn)';
export const INTERRUPTION_PATTERN = /(?:something went wrong|network error|response interrupted|stopped responding)/i;
export const INTERRUPTION_UI_SELECTOR = '[data-testid="conversation-turn-error"]:visible, [data-testid="response-error"]:visible, [data-testid="error-message"]:visible';
const GENERIC_ALERT_SELECTOR = '[role="alert"]:visible';
const COMPLETION_TIMEOUT_MS = 900000;
const COMPLETION_INITIAL_BACKOFF_MS = 250;
const COMPLETION_MAX_BACKOFF_MS = 1000;

export class ReviewPromptError extends Error {
  constructor(message, failureScope, cause) {
    super(message);
    this.name = "ReviewPromptError";
    this.failureScope = failureScope;
    if (cause) this.cause = cause;
  }
}

function withFailureScope(error, failureScope) {
  if (error?.failureScope) return error;
  const message = error instanceof Error ? error.message : String(error);
  return new ReviewPromptError(message, failureScope, error);
}

function normalizeComposerText(value) {
  return value.replace(/\s+/g, " ").trim();
}
function assertPrompt(prompt) {
  if (typeof prompt !== "string" || prompt.trim() === "") {
    throw new Error("prompt must be a non-empty string");
  }
}

async function openChatGPT(page) {
  if (!page.url().startsWith("https://chatgpt.com/")) {
    await page.goto(CHATGPT_URL, { timeout: COMPOSER_READINESS_TIMEOUT_MS });
  }

  const composer = page.getByRole("textbox", { name: "Ask ChatGPT" }).first();
  try {
    await composer.waitFor({ state: "visible", timeout: COMPOSER_READINESS_TIMEOUT_MS });
  } catch {
    throw new Error("Authenticated ChatGPT composer was not found");
  }
  if (!(await composer.isVisible())) throw new Error("Authenticated ChatGPT composer was not found");
  return composer;
}

/**
 * Open a new ChatGPT tab from an existing authenticated Playwright context.
 * The context must already own the user's authenticated session.
 */
export async function openReviewTab(context) {
  let page;
  try {
    page = await context.newPage();
  } catch (error) {
    throw withFailureScope(error, "shared_context");
  }
  try {
    await openChatGPT(page);
    return page;
  } catch (error) {
    await page.close().catch(() => {});
    throw withFailureScope(error, "shared_context");
  }
}

async function closeModelMenu(page) {
  const menu = page.getByRole("menu", { name: "Select ChatGPT model" }).first();
  if (!(await menu.isVisible())) return;

  await page.keyboard.press("Escape", { timeout: MENU_TRANSITION_TIMEOUT_MS });
  await menu.waitFor({ state: "hidden", timeout: MENU_TRANSITION_TIMEOUT_MS });
}

function extractConversationIdentity(url) {
  const match = url.match(/\/c\/([^/?#]+)/);
  return match ? match[1] : null;
}

async function readVisibleAssistantTurns(page) {
  const assistantMessages = page.locator(ASSISTANT_TURN_SELECTOR);
  if (await assistantMessages.count()) return assistantMessages;
  return page.locator(ASSISTANT_FALLBACK_SELECTOR);
}

export async function readVisibleInterruption(page) {
  const interruption = page.locator(INTERRUPTION_UI_SELECTOR).first();
  if ((await interruption.count()) > 0 && await interruption.isVisible()) return true;

  const alert = page.locator(GENERIC_ALERT_SELECTOR).first();
  if ((await alert.count()) === 0 || !(await alert.isVisible())) return false;
  return INTERRUPTION_PATTERN.test(normalizeComposerText(await alert.innerText({ timeout: UI_ACTION_TIMEOUT_MS })));
}

async function readVisibleAssistantMessage(page, { includeText = true } = {}) {
  const turns = await readVisibleAssistantTurns(page);
  const count = await turns.count();
  if (count === 0) {
    return {
      assistantMessageId: null,
      assistantText: "",
      assistantTurnCount: 0,
    };
  }

  const selected = turns.nth(count - 1);
  let assistantMessageId = null;
  for (const attribute of ["data-message-id", "data-turn-id", "data-testid", "id"]) {
    const value = await selected.getAttribute(attribute, { timeout: UI_ACTION_TIMEOUT_MS });
    if (value) {
      assistantMessageId = value;
      break;
    }
  }

  return {
    assistantMessageId,
    assistantText: includeText ? (await selected.innerText({ timeout: UI_ACTION_TIMEOUT_MS })).trim() : "",
    assistantTurnCount: count,
  };
}

export async function isPromptVisibleInComposer(composer, prompt) {
  const expectedPrompt = normalizeComposerText(prompt);

  try {
    if (normalizeComposerText(await composer.inputValue()) === expectedPrompt) return true;
  } catch {
    // Contenteditable composers do not expose inputValue.
  }

  return normalizeComposerText(await composer.innerText()) === expectedPrompt;
}

async function readCompletionSnapshot(page, { includeText } = {}) {
  const stopButton = page.getByRole("button", { name: /^(Stop generating|Stop response)$/i }).first();
  const generating = await stopButton.isVisible();
  const assistantMessage = await readVisibleAssistantMessage(page, {
    includeText: includeText ?? !generating,
  });
  const responseAction = page.getByRole("button", { name: /^(Regenerate response|Rate response)$/i }).last();
  const composer = page.getByRole("textbox", { name: "Ask ChatGPT" }).first();
  const currentUrl = page.url();
  const conversationId = extractConversationIdentity(currentUrl);

  return {
    ...assistantMessage,
    composerReady: await composer.isVisible() && !generating,
    conversationId,
    currentUrl,
    generating,
    interrupted: await readVisibleInterruption(page),
    responseActionsReady: await responseAction.isVisible(),
  };
}

export function evaluateReviewCompletion({
  assistantMessageId,
  assistantText,
  assistantTurnCount,
  baselineAssistantTurnCount,
  composerReady,
  conversationId,
  generationObserved,
  generating,
  interrupted,
  responseActionsReady,
  stableSampleCount,
}) {
  return !generating
    && composerReady
    && !interrupted
    && Boolean(conversationId)
    && Boolean(assistantMessageId)
    && generationObserved
    && assistantTurnCount > baselineAssistantTurnCount
    && Boolean(assistantText.trim())
    && stableSampleCount >= 2;
}

export async function submitPrompt(page, composer, prompt, { beforeSubmit } = {}) {
  await composer.fill(prompt, { timeout: UI_ACTION_TIMEOUT_MS });

  if (!(await isPromptVisibleInComposer(composer, prompt))) {
    throw new Error("Prompt was not visibly entered");
  }

  const sendButton = page.getByRole("button", { name: /^(Send|Send message|Submit)$/i }).first();
  if (beforeSubmit) await beforeSubmit();
  if (await sendButton.isVisible()) {
    await sendButton.click({ timeout: UI_ACTION_TIMEOUT_MS });
  } else {
    await composer.press("Enter", { timeout: UI_ACTION_TIMEOUT_MS });
  }

  await page.waitForTimeout(250);
  if (await isPromptVisibleInComposer(composer, prompt)) {
    throw new Error("Prompt submission was not visibly acknowledged");
  }

  return { submission: "acknowledged" };
}

async function prepareReviewPrompt(page, { model, effort }) {
  const composer = await openChatGPT(page);
  try {
    await selectReviewModel(page, { model, effort });
  } catch (error) {
    throw withFailureScope(error, "review");
  }
  await closeModelMenu(page);
  return { composer, effort, model };
}

/**
 * Navigate an existing authenticated ChatGPT page, select the requested
 * review model and effort, fill the prompt, and submit it exactly once.
 *
 * The caller owns the browser session. This helper never launches a browser,
 * authenticates, retries, or reruns a review request.
 */
export async function waitForReviewCompletion(page, {
  baseline,
  timeoutMs = COMPLETION_TIMEOUT_MS,
} = {}) {
  if (!baseline) throw new Error("baseline is required for completion observation");

  const deadline = Date.now() + timeoutMs;
  let backoffMs = COMPLETION_INITIAL_BACKOFF_MS;
  let previousText = "";
  let previousMessageId = null;
  let generationObserved = false;
  let stableSampleCount = 0;
  let snapshot;

  while (Date.now() <= deadline) {
    snapshot = await readCompletionSnapshot(page);
    generationObserved ||= snapshot.generating;
    const sameMessage = !snapshot.assistantMessageId
      || !previousMessageId
      || snapshot.assistantMessageId === previousMessageId;
    if (snapshot.assistantText === previousText && sameMessage && snapshot.assistantText) {
      stableSampleCount += 1;
    } else {
      stableSampleCount = 0;
      previousText = snapshot.assistantText;
    }
    previousMessageId = snapshot.assistantMessageId;

    if (evaluateReviewCompletion({
      ...snapshot,
      baselineAssistantTurnCount: baseline.assistantTurnCount,
      generationObserved,
      stableSampleCount,
    })) {
      return {
        ...snapshot,
        assistantTurnIndex: snapshot.assistantTurnCount - 1,
        response: snapshot.assistantText,
        status: "confirmed",
      };
    }

    await page.waitForTimeout(backoffMs);
    backoffMs = Math.min(backoffMs * 2, COMPLETION_MAX_BACKOFF_MS);
  }

  const finalSnapshot = await readCompletionSnapshot(page, { includeText: true });
  return {
    ...finalSnapshot,
    response: finalSnapshot.assistantText,
    status: "incomplete",
    failureReason: "bounded completion timeout or ambiguous response association",
  };
}

export async function runReviewPrompt(page, { beforeSubmit, model, effort, prompt }) {
  assertPrompt(prompt);
  const { composer } = await prepareReviewPrompt(page, { model, effort });
  const baselineTurns = await readVisibleAssistantTurns(page);
  const baseline = {
    assistantTurnCount: await baselineTurns.count(),
    conversationId: extractConversationIdentity(page.url()),
    conversationUrl: page.url(),
  };
  const submission = await submitPrompt(page, composer, prompt, { beforeSubmit });

  return { ...baseline, ...submission, model, effort, promptSubmitted: true };
}

export async function runReviewPromptInNewTab(context, options) {
  const page = await openReviewTab(context);
  try {
    return { page, ...(await runReviewPrompt(page, options)) };
  } catch (error) {
    await page.close().catch(() => {});
    throw withFailureScope(error, "review");
  }
}
