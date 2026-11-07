// Purpose: call the Jev judgment API over plain HTTP with the global fetch, validate every
// answer against the documented contract, then turn each answer into an act or review decision.
// Fill in: the STATE record below with your own input, and the questions and thresholds in
// constants.template.ts. The route, its endpoint, and its key environment variable live here.
// A live call only after the user consents: this file sends nothing until LIVE_CALL_APPROVED is
// turned on, and the key is read from the environment at call time and never printed.

import { MODEL, QUESTIONS, THRESHOLDS } from "./constants.template";

// The direct TypeSafe route and the b.ai route share one request shape and differ in the
// endpoint they POST to, the model ids they accept, and the variable that holds the key.
type RouteName = "direct" | "bai";

interface Route {
  readonly label: string;
  readonly url: string;
  readonly keyEnvVar: string;
}

const ROUTES: Record<RouteName, Route> = {
  direct: {
    label: "TypeSafe direct",
    // Snapshot 2026-10-01, re-check before a live call: references/providers.md
    url: "https://api.typesafe.ai/v1/systemone",
    keyEnvVar: "TYPESAFE_API_KEY"
  },
  bai: {
    label: "b.ai Decisions",
    // Snapshot 2026-10-01, re-check before a live call: references/providers.md
    url: "https://api.b.ai/v1/decisions",
    keyEnvVar: "BAI_API_KEY"
  }
};

// Pick the route here. Which model ids each route accepts, and the method and stream rules, are in
// references/providers.md; this file does not restate them.
const ROUTE: RouteName = "direct";

// Consent gate. Leave this false until the person has agreed to a live call and knows its cost.
const LIVE_CALL_APPROVED = false;

const STATE = {
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
function assertProbabilities(value: unknown, path: string): void {
  if (!isRecord(value)) {
    fail(path, "the direct and b.ai APIs return a probability for every option or level");
  }
  const keys = Object.keys(value);
  if (keys.length === 0) fail(path, "the probability map is empty");
  let sum = 0;
  for (const key of keys) {
    sum += readNumber(value[key], `${path}.${key}`);
  }
  if (Math.abs(sum - 1) > 1e-4) {
    fail(path, `the probabilities must sum to 1 within 1e-4, but they sum to ${sum}`);
  }
}

/** Checks that a choice or score answer carries the required confidence, between 0 and 1. */
function assertConfidence(value: unknown, path: string): void {
  if (typeof value !== "number" || !Number.isFinite(value) || value < 0 || value > 1) {
    fail(path, "a choice or score answer must carry a confidence between 0 and 1");
  }
}

/**
 * Validates a parsed response against the questions that were sent, and returns its answers.
 * Every requested id must be present, the answer type must match the question type, a choice
 * must be one of the criteria keys, a noul must sit in 0..1, and a score must sit between 0 and
 * the last level index. A choice or score answer must also carry a confidence between 0 and 1 and
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
    if (questionType !== "noul" && questionType !== "choice" && questionType !== "score") {
      fail(`$.questions.${id}`, "this question has no recognised type to check an answer against");
    }

    const answer = answers[id];
    if (answer === undefined) fail(`$.answers.${id}`, "the response is missing this answer");
    if (!isRecord(answer)) fail(`$.answers.${id}`, "the answer must be a JSON object");
    if (answer.type !== questionType) {
      fail(`$.answers.${id}.type`, `the answer type must match the question type ${questionType}`);
    }

    if (questionType === "noul") {
      const noul = readNumber(answer.noul, `$.answers.${id}.noul`);
      if (noul < 0 || noul > 1) fail(`$.answers.${id}.noul`, "a noul value must sit between 0 and 1");
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
      assertConfidence(answer.confidence, `$.answers.${id}.confidence`);
      continue;
    }

    const levels = isRecord(question) ? question.criteria : undefined;
    if (!Array.isArray(levels)) fail(`$.questions.${id}.criteria`, "a score question needs a level array");
    const score = readNumber(answer.score, `$.answers.${id}.score`);
    const highestLevel = levels.length - 1;
    if (score < 0 || score > highestLevel) {
      fail(`$.answers.${id}.score`, `a score must sit between 0 and ${highestLevel}`);
    }
    assertProbabilities(answer.probabilities, `$.answers.${id}.probabilities`);
    assertConfidence(answer.confidence, `$.answers.${id}.confidence`);
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
  readonly signal: number;
  readonly threshold: number;
}

/**
 * Turns validated answers into decisions. A noul answer is its yes probability, so it acts only
 * at or above the noul threshold, and a confident no falls below that line; choice and score
 * answers act on the model's confidence.
 */
export function decide(answers: JsonRecord, questions: JsonRecord): Decision[] {
  const decisions: Decision[] = [];
  for (const id of Object.keys(questions)) {
    const question = questions[id];
    const answer = answers[id];
    if (!isRecord(question) || !isRecord(answer)) fail(`$.answers.${id}`, "the answer is missing or malformed");

    if (question.type === "noul") {
      const signal = readNumber(answer.noul, `$.answers.${id}.noul`);
      decisions.push({
        question: id,
        outcome: signal >= THRESHOLDS.noulActAtOrAbove ? "act" : "review",
        signal,
        threshold: THRESHOLDS.noulActAtOrAbove
      });
      continue;
    }

    const signal = readNumber(answer.confidence, `$.answers.${id}.confidence`);
    decisions.push({
      question: id,
      outcome: signal >= THRESHOLDS.answerConfidenceAtOrAbove ? "act" : "review",
      signal,
      threshold: THRESHOLDS.answerConfidenceAtOrAbove
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

/** Sends one consented request, validates the response, and prints the decisions. */
async function main() {
  const route = ROUTES[ROUTE];
  const key = readKey(route.keyEnvVar);
  const response = await fetch(route.url, {
    method: "POST",
    headers: {
      "Content-Type": "application/json",
      Authorization: `Bearer ${key}`
    },
    body: JSON.stringify({ state: STATE, model: MODEL, questions: QUESTIONS })
  });

  // Read the status before the body: a rate-limited response can arrive with an empty body.
  if (!response.ok) {
    throw new Error(`${route.label} returned HTTP ${response.status}.`);
  }

  const decisions = decide(validateResponse(await response.json(), QUESTIONS), QUESTIONS);
  for (const decision of decisions) {
    console.log(`${decision.question}: ${decision.outcome} (signal ${decision.signal}, threshold ${decision.threshold})`);
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
  console.log(`Selected route: ${ROUTES[ROUTE].label}. No call was made.`);
  console.log(`Set LIVE_CALL_APPROVED to true only after the user consents; the key is read from ${ROUTES[ROUTE].keyEnvVar} and never printed.`);
}
