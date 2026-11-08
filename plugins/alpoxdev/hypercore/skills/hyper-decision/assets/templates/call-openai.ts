// Purpose: call the OpenAI Decisions API through the official JavaScript SDK, validate every answer
// against the documented contract (including refusal, which is its own answer type), then turn each
// answer into an act, review, or refused outcome.
// Fill in: the INPUT string and the QUESTIONS array below with your own. The SDK reads the key from
// OPENAI_API_KEY, so no key value appears in this file.
// A live call only after the user consents: this file sends nothing until LIVE_CALL_APPROVED is
// turned on.

import OpenAI from "openai";
import { MODEL_OPENAI, THRESHOLDS } from "./constants.template";

// Snapshot 2026-11-08, re-check before the first live call:
// references/official/openai-decisions.md carries the endpoint, the request shape, the answer union
// with refusal, the limits, and the status of this API.
// gpt-6-luna is the only model the Decisions API documents as supported. The method exists in
// openai-node 7.30.0 and later, per the Azure page that documents the same contract.
const MODEL_ID = MODEL_OPENAI;

// Consent gate. Leave this false until the person has agreed to a live call and knows its cost.
const LIVE_CALL_APPROVED = false;

// One string is the simplest input. The API also accepts an array of input items, including messages
// and tool calls, and an `input_json` part with its own smaller size caps.
const INPUT =
  "Channel: email\n" +
  "Subject: Payouts have been failing since Monday\n" +
  "Message: My payouts have been failing since Monday. I already re-entered my bank details twice. " +
  "I have supplier invoices due this week.\n" +
  "Customer plan: growth";

// This dialect names the questions in an array, and every entry needs a unique `name` because the
// answer keys on it. An unnamed question comes back with `name: null` and cannot be acted on.
const QUESTIONS = [
  {
    type: "predicate" as const,
    name: "needs_human",
    instructions:
      "Does this ticket need a human agent, rather than an automated reply? A manual payout retry, a " +
      "refund, or anything only a person can decide counts as yes; a help article or the account " +
      "data in the input answering it counts as no."
  },
  {
    type: "predicate" as const,
    name: "any_queue_fits",
    instructions:
      "Does this ticket belong to one of the queues listed in the companion routing question " +
      "(billing, technical, account, other)? Answer no when no listed queue describes the work, so " +
      "a person has to decide where it goes."
  },
  {
    type: "choice" as const,
    name: "queue",
    instructions:
      "Which queue should own this ticket? Pick the closest queue; the companion predicate decides " +
      "whether any queue actually fits.",
    choices: [
      { value: "billing", description: "Charges, payouts, invoices, refunds." },
      { value: "technical", description: "Bugs, outages, integrations, API errors." },
      { value: "account", description: "Login, plan changes, team membership." },
      { value: "other", description: "A last resort: real work, but no listed queue describes it." }
    ]
  },
  {
    type: "score" as const,
    name: "urgency",
    instructions:
      "How urgent is this ticket for the customer right now? Use the level that describes the " +
      "customer's situation today, not the tone of the message.",
    levels: [
      { label: "can_wait", description: "No money or access is blocked this week." },
      { label: "time_boxed", description: "Money or access is blocked within the next few days." },
      { label: "blocking", description: "The customer cannot operate and is losing money today." }
    ]
  }
];

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

/**
 * Checks a `probabilities` array: each entry carries a `value` and a `probability` between 0 and 1,
 * the entries sum to 1 within 1e-4. With `keyed`, each entry must also carry a unique `value`, and the
 * function returns value to probability so a caller can read one option's probability directly. A
 * score answer's entries are checked for mass only, because the snapshot does not document which key
 * a score distribution uses.
 */
function readProbabilities(value: unknown, path: string, keyed: boolean): Map<string, number> {
  if (!Array.isArray(value)) {
    fail(path, "this dialect returns probabilities as an array of { value, probability } entries");
  }
  const byValue = new Map<string, number>();
  let sum = 0;
  value.forEach((entry, index) => {
    const entryPath = `${path}[${index}]`;
    if (!isRecord(entry)) fail(entryPath, "each probability entry must be an object");
    const probability = readNumber(entry.probability, `${entryPath}.probability`);
    if (probability < 0 || probability > 1) {
      fail(`${entryPath}.probability`, "a probability must sit between 0 and 1");
    }
    sum += probability;
    if (!keyed) return;
    const raw = entry.value;
    const key = typeof raw === "string" ? raw : typeof raw === "number" ? String(raw) : null;
    if (key === null) fail(`${entryPath}.value`, "a choice probability entry needs a string or number value");
    if (byValue.has(key)) fail(`${entryPath}.value`, "two probability entries share this value");
    byValue.set(key, probability);
  });
  if (value.length === 0) fail(path, "the probabilities array is empty");
  if (Math.abs(sum - 1) > 1e-4) {
    fail(path, `the probabilities must sum to 1 within 1e-4, but they sum to ${sum}`);
  }
  return byValue;
}

/** Reads a confidence, which this dialect returns on choice and score answers and never on predicate. */
function readConfidence(value: unknown, path: string): number {
  if (typeof value !== "number" || !Number.isFinite(value) || value < 0 || value > 1) {
    fail(path, "a choice or score answer carries a confidence between 0 and 1");
  }
  return value;
}

export type AnswerOutcome = "act" | "review" | "refused";

export interface Answer {
  readonly name: string;
  readonly type: "predicate" | "choice" | "score" | "refusal";
  readonly outcome: AnswerOutcome;
  readonly signal: number | null;
  readonly threshold: number;
  readonly reason: string;
}

/**
 * Validates a parsed response against the questions that were sent, then turns each answer into one
 * outcome.
 * Rules: every sent name comes back exactly once and no unknown name appears; the answer type matches
 * the question type or is `refusal`; a predicate probability sits in 0..1; a choice value is one of
 * the declared choice values and its probabilities sum to 1; a score sits between 0 and the last level
 * index and its probabilities sum to 1; choice and score answers carry a confidence.
 * A refusal is its own outcome. It is never turned into probability 0, the first choice, or a zero
 * score, because "the model declined" and "the model said no" are different decisions.
 */
export function validateAndDecide(payload: unknown, questions: readonly JsonRecord[]): Answer[] {
  if (!isRecord(payload)) fail("$", "the response body must be a JSON object");
  const rawAnswers = payload.answers;
  if (!Array.isArray(rawAnswers)) fail("$.answers", "the response must carry an answers array");

  const questionsByName = new Map<string, JsonRecord>();
  for (const question of questions) {
    const name = question.name;
    if (typeof name !== "string" || name.trim().length === 0) {
      fail("$.questions", "every question needs a non-empty name");
    }
    questionsByName.set(name, question);
  }

  const seen = new Set<string>();
  const answers: Answer[] = [];
  rawAnswers.forEach((entry, index) => {
    const path = `$.answers[${index}]`;
    if (!isRecord(entry)) fail(path, "each answer must be an object");
    const name = entry.name;
    if (typeof name !== "string" || name.trim().length === 0) {
      fail(`${path}.name`, "an answer with a null name cannot be matched to a question");
    }
    if (!questionsByName.has(name)) fail(`${path}.name`, "the response carries an answer that was not asked for");
    if (seen.has(name)) fail(`${path}.name`, "the response carries two answers for the same name");
    seen.add(name);

    const question = questionsByName.get(name) as JsonRecord;
    const answerType = entry.type;
    if (answerType === "refusal") {
      answers.push({
        name,
        type: "refusal",
        outcome: "refused",
        signal: null,
        threshold: THRESHOLDS.booleanActAtOrAbove,
        reason: "the model declined to answer, so a person decides"
      });
      return;
    }
    if (answerType !== question.type) {
      fail(`${path}.type`, `the answer type must match the question type ${String(question.type)}, or be refusal`);
    }

    if (answerType === "predicate") {
      const signal = readNumber(entry.probability, `${path}.probability`);
      if (signal < 0 || signal > 1) fail(`${path}.probability`, "a predicate probability must sit between 0 and 1");
      const threshold = THRESHOLDS.booleanActAtOrAbove;
      answers.push({
        name,
        type: "predicate",
        outcome: signal >= threshold ? "act" : "review",
        signal,
        threshold,
        reason:
          signal >= threshold
            ? "the predicate probability is at or above the threshold"
            : "the predicate probability is below the threshold"
      });
      return;
    }

    if (answerType === "choice") {
      const choices = Array.isArray(question.choices) ? question.choices : [];
      const allowed = new Set<string>(
        choices
          .map((choice) => (isRecord(choice) && typeof choice.value === "string" ? choice.value : null))
          .filter((value): value is string => value !== null)
      );
      const picked = entry.choice;
      if (typeof picked !== "string" || !allowed.has(picked)) {
        fail(`${path}.choice`, "the chosen value is not one of the declared choice values");
      }
      const probabilities = readProbabilities(entry.probabilities, `${path}.probabilities`, true);
      readConfidence(entry.confidence, `${path}.confidence`);
      // Act on the probability of the chosen option. Confidence for a fixed option set is a transform
      // of that top probability, so thresholding both adds nothing.
      const signal = probabilities.get(picked) ?? null;
      const threshold = THRESHOLDS.choiceProbabilityAtOrAbove;
      answers.push({
        name,
        type: "choice",
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
      return;
    }

    const levels = Array.isArray(question.levels) ? question.levels : [];
    const score = readNumber(entry.score, `${path}.score`);
    if (score < 0 || score > levels.length - 1) {
      fail(`${path}.score`, `a score must sit between 0 and ${levels.length - 1}`);
    }
    // The score is a probability-weighted mean of level indices, so it can fall between levels. The
    // snapshot does not document which key a score's probability entries use, so this caller branches
    // on the score and keeps the distribution only for reporting.
    readProbabilities(entry.probabilities, `${path}.probabilities`, false);
    const signal = readConfidence(entry.confidence, `${path}.confidence`);
    const threshold = THRESHOLDS.scoreConfidenceAtOrAbove;
    answers.push({
      name,
      type: "score",
      outcome: signal >= threshold ? "act" : "review",
      signal,
      threshold,
      reason:
        signal >= threshold ? "the confidence is at or above the threshold" : "the confidence is below the threshold"
    });
  });

  for (const name of questionsByName.keys()) {
    if (!seen.has(name)) fail(`$.answers.${name}`, "the response is missing an answer for this name");
  }

  return answers;
}

/** Sends one consented request and prints one outcome per question. */
async function main() {
  if (typeof process.env.OPENAI_API_KEY !== "string" || process.env.OPENAI_API_KEY.trim().length === 0) {
    throw new Error("OPENAI_API_KEY is not set. Export it in the calling shell; never paste the key into a file or a log.");
  }

  // Two retries at most, so a rate-limited call gives up instead of looping and billing every attempt.
  const client = new OpenAI({ maxRetries: 2 });
  const payload: unknown = await client.decisions.create({
    model: MODEL_ID,
    input: INPUT,
    questions: QUESTIONS
  });

  if (isRecord(payload) && typeof payload.model === "string") {
    console.log(`answer from ${payload.model} (requested ${MODEL_ID})`);
  }

  const answers = validateAndDecide(payload, QUESTIONS);
  for (const answer of answers) {
    const shown = answer.signal === null ? "null" : answer.signal;
    console.log(
      `${answer.name}: ${answer.outcome} (signal ${shown}, threshold ${answer.threshold}) - ${answer.reason}`
    );
  }
  const routed = answers.filter((answer) => answer.outcome !== "act");
  if (routed.length > 0) {
    console.log(`Send ${routed.map((answer) => answer.name).join(", ")} to the human review path.`);
  }
}

if (LIVE_CALL_APPROVED) {
  main().catch((error: unknown) => {
    // Status handling: 401 is a credential problem, 422 is a request that failed the API's own schema
    // check, and 429 is a rate limit the SDK has already retried. None of them is a reason to loop.
    console.error("The call failed; no response was acted on.", error instanceof Error ? error.message : "");
    console.error("Check the status and the route in references/official/openai-decisions.md.");
    process.exitCode = 1;
  });
} else {
  console.log(`Model: ${MODEL_ID}, ${QUESTIONS.length} questions. No call was made.`);
  console.log("Set LIVE_CALL_APPROVED to true only after the user consents; the SDK reads OPENAI_API_KEY and never prints it.");
}
