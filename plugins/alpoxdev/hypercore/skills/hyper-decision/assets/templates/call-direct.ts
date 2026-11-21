// Purpose: call a decision API in the TypeSafe System One dialect over plain HTTP with the global
// fetch, validate every answer against the documented contract, then turn each answer into an act or
// review decision.
// Fill in: the INPUT record below with your own shared input, and the questions and thresholds in
// constants.template.ts. Any endpoint that speaks this dialect works by changing BASE_URL: the
// TypeSafe direct API, a Gateway TypeSafe-compatible path, an OpenRouter System One path, or a
// self-hosted implementation.
// A live call only after the user consents: this file sends nothing until LIVE_CALL_APPROVED is
// turned on, and the key is read from the environment at call time and never printed.

import { MODEL, QUESTIONS, THRESHOLDS } from "./constants.template";

// Snapshot 2026-11-08, re-check before the first live call:
// references/official/jev-platform.md, which carries the endpoint, its request shape, and the
// documented status codes.
// The base URL, the path, and the model id each appear once in this file, in this block.
const BASE_URL = "https://api.typesafe.ai/v1";
const PATH = "/systemone";
const MODEL_ID = MODEL;

// The variable that holds the key. The value is read at call time and never echoed.
const KEY_ENV_VAR = "TYPESAFE_API_KEY";

// Consent gate. Leave this false until the person has agreed to a live call and knows its cost.
const LIVE_CALL_APPROVED = false;

const INPUT = {
  ticket: {
    channel: "email",
    subject: "Payouts have been failing since Monday",
    message:
      "My payouts have been failing since Monday. I already re-entered my bank details twice. " +
      "I have supplier invoices due this week."
  },
  customer: { plan: "growth" }
};

type JsonRecord = Record<string, unknown>;

/** Raised when a response does not match the documented answer contract. */
export class ResponseValidationError extends Error {
  readonly path: string;

  constructor(path: string, message: string) {
    super(`${path}: ${message}`);
    this.name = "ResponseValidationError";
    this.path = path;
  }
}

/** Stops validation, naming the JSON path of the offending value. */
function fail(path: string, message: string): never {
  throw new ResponseValidationError(path, message);
}

/** Reports whether a value is a plain JSON object. */
function isRecord(value: unknown): value is JsonRecord {
  return typeof value === "object" && value !== null && !Array.isArray(value);
}

/** Reads a finite number, or fails with the JSON path that should have held one. */
function readNumber(value: unknown, path: string): number {
  if (typeof value !== "number" || !Number.isFinite(value)) {
    fail(path, "expected a finite number");
  }
  return value;
}

/** Checks that a probability map covers its keys with finite values summing to 1 within 1e-4. */
function assertProbabilities(value: unknown, path: string): JsonRecord {
  if (!isRecord(value)) {
    fail(path, "this dialect returns a probability for every option or level");
  }
  let sum = 0;
  for (const key of Object.keys(value)) {
    sum += readNumber(value[key], `${path}.${key}`);
  }
  if (Math.abs(sum - 1) > 1e-4) {
    fail(path, `the probabilities must sum to 1 within 1e-4, but they sum to ${sum}`);
  }
  return value;
}

/** Checks that a confidence, when the route reports one, sits between 0 and 1. */
function readOptionalConfidence(value: unknown, path: string): number | null {
  if (value === undefined || value === null) return null;
  if (typeof value !== "number" || !Number.isFinite(value) || value < 0 || value > 1) {
    fail(path, "a confidence must be a number between 0 and 1 when present");
  }
  return value;
}

/** Checks that a box answer keeps all four edges inside the normalized 0..1 frame. */
function assertBoxEdges(value: unknown, path: string): void {
  if (!isRecord(value)) fail(path, "a box answer carries four named edges");
  for (const edge of ["top", "bottom", "left", "right"]) {
    const edgeValue = readNumber(value[edge], `${path}.${edge}`);
    if (edgeValue < 0 || edgeValue > 1) {
      fail(`${path}.${edge}`, "a box edge must sit inside the normalized frame, between 0 and 1");
    }
  }
}

/**
 * Validates a parsed response against the questions that were sent, and returns its answers.
 * Every requested id must be present, the answer type must match the question type, a choice must be
 * one of the criteria keys, a boolean must sit in 0..1, a score must sit between 0 and the last level
 * index, and a box must keep its edges inside 0..1. Choice and score answers must also carry
 * probabilities summing to 1 within 1e-4, and the response may carry no answer for an id that was
 * not sent.
 */
export function validateResponse(payload: unknown, questions: JsonRecord): JsonRecord {
  if (!isRecord(payload)) fail("$", "the response body must be a JSON object");
  const answers = payload.answers;
  if (!isRecord(answers)) fail("$.answers", "the response must carry an answers object");

  for (const id of Object.keys(questions)) {
    const question = questions[id];
    const questionType = isRecord(question) ? question.type : undefined;
    if (
      questionType !== "noul" &&
      questionType !== "choice" &&
      questionType !== "score" &&
      questionType !== "box"
    ) {
      fail(`$.questions.${id}`, "this question has no recognised type to check an answer against");
    }

    const answer = answers[id];
    if (answer === undefined) fail(`$.answers.${id}`, "the response is missing this answer");
    if (!isRecord(answer)) fail(`$.answers.${id}`, "the answer must be a JSON object");
    if (answer.type !== questionType) {
      fail(`$.answers.${id}.type`, `the answer type must match the question type ${questionType}`);
    }

    if (questionType === "noul") {
      const probability = readNumber(answer.noul, `$.answers.${id}.noul`);
      if (probability < 0 || probability > 1) {
        fail(`$.answers.${id}.noul`, "a boolean probability must sit between 0 and 1");
      }
      continue;
    }

    if (questionType === "choice") {
      const criteria = isRecord(question) ? question.criteria : undefined;
      if (!isRecord(criteria)) fail(`$.questions.${id}.criteria`, "a choice question needs an options object");
      const picked = answer.choice;
      if (typeof picked !== "string" || !Object.prototype.hasOwnProperty.call(criteria, picked)) {
        fail(`$.answers.${id}.choice`, "the chosen option is not one of the criteria keys");
      }
      assertProbabilities(answer.probabilities, `$.answers.${id}.probabilities`);
      readOptionalConfidence(answer.confidence, `$.answers.${id}.confidence`);
      continue;
    }

    if (questionType === "score") {
      const levels = isRecord(question) ? question.criteria : undefined;
      if (!Array.isArray(levels)) fail(`$.questions.${id}.criteria`, "a score question needs a level array");
      const score = readNumber(answer.score, `$.answers.${id}.score`);
      const highestLevel = levels.length - 1;
      if (score < 0 || score > highestLevel) {
        fail(`$.answers.${id}.score`, `a score must sit between 0 and ${highestLevel}`);
      }
      assertProbabilities(answer.probabilities, `$.answers.${id}.probabilities`);
      readOptionalConfidence(answer.confidence, `$.answers.${id}.confidence`);
      continue;
    }

    // Box is a TypeSafe Jev 1.14 feature. Its confidence may be null when the object is absent.
    assertBoxEdges(answer.box, `$.answers.${id}.box`);
    readOptionalConfidence(answer.confidence, `$.answers.${id}.confidence`);
  }

  for (const id of Object.keys(answers)) {
    if (!Object.prototype.hasOwnProperty.call(questions, id)) {
      fail(`$.answers.${id}`, "the response carries an answer for a question that was not sent");
    }
  }

  return answers;
}

export interface Decision {
  readonly question: string;
  readonly outcome: "act" | "review";
  readonly signal: number | null;
  readonly threshold: number;
  readonly reason: string;
}

/**
 * Turns validated answers into decisions.
 * A boolean acts on its own probability, not on a confidence it does not carry. A choice acts on the
 * probability of the option it is about to take, because confidence for a fixed option set is a
 * transform of that same top probability and adds nothing. A score acts on its confidence where the
 * route reports one, and a box does the same with an edge confidence that may be null.
 * Any signal that is missing, outside 0..1, or below its threshold becomes review, never act.
 */
export function decide(answers: JsonRecord, questions: JsonRecord): Decision[] {
  const decisions: Decision[] = [];
  for (const id of Object.keys(questions)) {
    const question = questions[id];
    const answer = answers[id];
    if (!isRecord(question) || !isRecord(answer)) {
      fail(`$.answers.${id}`, "the answer is missing or malformed");
    }

    if (question.type === "noul") {
      const signal = readNumber(answer.noul, `$.answers.${id}.noul`);
      const threshold = THRESHOLDS.booleanActAtOrAbove;
      decisions.push({
        question: id,
        outcome: signal >= threshold ? "act" : "review",
        signal,
        threshold,
        reason: signal >= threshold ? "the yes probability is at or above the threshold" : "the yes probability is below the threshold"
      });
      continue;
    }

    if (question.type === "choice") {
      const picked = answer.choice;
      const probabilities = isRecord(answer.probabilities) ? answer.probabilities : {};
      const signal =
        typeof picked === "string" ? readNumber(probabilities[picked], `$.answers.${id}.probabilities.${picked}`) : null;
      const threshold = THRESHOLDS.choiceProbabilityAtOrAbove;
      decisions.push({
        question: id,
        outcome: signal !== null && signal >= threshold ? "act" : "review",
        signal,
        threshold,
        reason:
          signal === null
            ? "the chosen option carries no probability, so a person decides"
            : signal >= threshold
              ? "the chosen option's probability is at or above the threshold"
              : "the chosen option's probability is below the threshold"
      });
      continue;
    }

    const signal = readOptionalConfidence(answer.confidence, `$.answers.${id}.confidence`);
    const threshold = THRESHOLDS.scoreConfidenceAtOrAbove;
    decisions.push({
      question: id,
      outcome: signal !== null && signal >= threshold ? "act" : "review",
      signal,
      threshold,
      reason:
        signal === null
          ? "this route reported no confidence, so a person decides"
          : signal >= threshold
            ? "the confidence is at or above the threshold"
            : "the confidence is below the threshold"
    });
  }
  return decisions;
}

/** Reads the key from the named environment variable, never echoing its value. */
function readKey(name: string): string {
  const value = process.env[name];
  if (typeof value !== "string" || value.trim().length === 0) {
    fail(`env.${name}`, "export the key in the calling shell; never paste it into a file, a prompt, or a log");
  }
  return value;
}

// How long to wait before each retry, in milliseconds. A bounded ladder, so a failing call gives up
// instead of looping and billing every attempt.
const RETRY_DELAYS_MS = [500, 1500] as const;

// Statuses that are worth one bounded retry. 413, 415, and 422 are request defects: the same body will
// fail the same way, so they are reported and never retried.
const RETRYABLE_STATUSES = new Set([429, 529]);

function sleep(ms: number): Promise<void> {
  const { promise, resolve } = Promise.withResolvers<void>();
  setTimeout(resolve, ms);
  return promise;
}

/** Sends one consented request, validates the response, and prints the decisions. */
async function main() {
  const key = readKey(KEY_ENV_VAR);
  const url = `${BASE_URL}${PATH}`;
  const body = JSON.stringify({ model: MODEL_ID, state: INPUT, questions: QUESTIONS });

  let response: Response | null = null;
  for (let attempt = 0; attempt <= RETRY_DELAYS_MS.length; attempt += 1) {
    response = await fetch(url, {
      method: "POST",
      headers: { "Content-Type": "application/json", Authorization: `Bearer ${key}` },
      body
    });
    if (response.ok || !RETRYABLE_STATUSES.has(response.status) || attempt === RETRY_DELAYS_MS.length) {
      break;
    }
    await sleep(RETRY_DELAYS_MS[attempt]);
  }

  if (response === null) {
    throw new Error("no request was sent");
  }

  // Read the status before the body: a rate-limited response can arrive with an empty body.
  if (!response.ok) {
    const detail =
      response.status === 413
        ? "the request body is too large; trim the input or split the questions"
        : response.status === 415
          ? "the content type or encoding is not accepted"
          : response.status === 422
            ? "the body failed the API's own schema check; run the offline request checker"
            : response.status === 429
              ? "rate limited after the bounded retry ladder; wait and re-run deliberately"
              : response.status === 529
                ? "the service is overloaded after the bounded retry ladder; wait and re-run deliberately"
                : "see the endpoint's documented status codes";
    throw new Error(`decision call returned HTTP ${response.status}: ${detail}`);
  }

  const payload: unknown = await response.json();
  // Log the model id that answered. An alias such as jev-latest resolves to a version, and the
  // answered id is the only place that version is recorded.
  const answeredModel = isRecord(payload) && typeof payload.model === "string" ? payload.model : "unreported";
  console.log(`answer from ${answeredModel} (requested ${MODEL_ID})`);

  const decisions = decide(validateResponse(payload, QUESTIONS), QUESTIONS);
  for (const decision of decisions) {
    const shown = decision.signal === null ? "null" : decision.signal;
    console.log(
      `${decision.question}: ${decision.outcome} (signal ${shown}, threshold ${decision.threshold}) - ${decision.reason}`
    );
  }
  const review = decisions.filter((decision) => decision.outcome === "review");
  if (review.length > 0) {
    console.log(`Send ${review.map((decision) => decision.question).join(", ")} to the human review path.`);
  }
}

if (LIVE_CALL_APPROVED) {
  main().catch(() => {
    console.error("The call failed; no response was acted on. Check the status and the route in references/providers.md.");
    process.exitCode = 1;
  });
} else {
  console.log(`Endpoint: ${BASE_URL}${PATH}, model ${MODEL_ID}. No call was made.`);
  console.log(`Set LIVE_CALL_APPROVED to true only after the user consents; the key is read from ${KEY_ENV_VAR} and never printed.`);
}
