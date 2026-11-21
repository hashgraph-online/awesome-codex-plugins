// Purpose: call the decision API through the official TypeScript SDK, which reads the key from
// TYPESAFE_API_KEY, retries rate limits for you, and types each answer by question id.
// The SDK types the answer shape but does not range-check the values, so every signal is validated
// here before it can reach a decision: a value that is not a finite number inside 0..1 becomes a
// review, never an act.
// Fill in: the INPUT record and the questions below, and the thresholds in constants.template.ts.
// A live call only after the user consents, and only then.
//
// Snapshot 2026-11-08, re-check before the first live call: references/providers.md and
// references/official/jev-platform.md.
// SDK notes: `@typesafe-ai/sdk` 0.7.0 (2026-10-14) requires Node.js 22 or newer and adds `box`
// questions. The default retry policy is two retries on 408, 429, and 5xx with a bounded backoff, so
// this file adds none of its own. The client reads TYPESAFE_API_KEY and TYPESAFE_BASE_URL; the key is
// never printed here.

import { choice, TypeSafeClient } from "@typesafe-ai/sdk";
import { MODEL, THRESHOLDS } from "./constants.template";

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

// The option set and the level list are defined once, so the check on the response reads the same
// keys and the same level count the question was built from.
const QUEUE_OPTIONS = {
  billing: "Charges, payouts, invoices, refunds.",
  technical: "Bugs, outages, integrations, API errors.",
  account: "Login, plan changes, team membership.",
  other: "A last resort: real work, but no listed queue describes it."
};

const URGENCY_LEVELS: readonly [string, string, ...string[]] = [
  "Can wait: no money or access is blocked this week.",
  "Time-boxed: money or access is blocked within the next few days.",
  "Blocking: the customer cannot operate and is losing money today."
];

const QUEUE_OPTION_KEYS = Object.keys(QUEUE_OPTIONS);

interface Decision {
  readonly question: string;
  readonly outcome: "act" | "review";
  readonly signal: number | null;
  readonly threshold: number;
  readonly reason: string;
}

/**
 * Reads a decision signal, refusing any value the SDK type cannot guarantee at runtime: a value that
 * is not a finite number inside 0..1 returns null, which always becomes review, never act.
 */
function validatedSignal(value: unknown): number | null {
  if (typeof value !== "number" || !Number.isFinite(value) || value < 0 || value > 1) return null;
  return value;
}

/** Turns one answer value into a decision; a signal that fails validation goes to review. */
function decisionFor(question: string, value: unknown, threshold: number): Decision {
  const signal = validatedSignal(value);
  if (signal === null) {
    return { question, outcome: "review", signal: null, threshold, reason: "the value is missing or outside 0..1, so a person decides" };
  }
  if (signal >= threshold) {
    return { question, outcome: "act", signal, threshold, reason: "at or above the threshold" };
  }
  return { question, outcome: "review", signal, threshold, reason: "below the threshold" };
}

/** Reports whether an answered choice is one of the option keys its question was built from. */
function choiceIsAllowed(value: unknown, optionKeys: readonly string[]): boolean {
  return typeof value === "string" && optionKeys.includes(value);
}

/** Reports whether an answered score is a finite number inside 0..(levelCount - 1). */
function scoreIsAllowed(value: unknown, levelCount: number): boolean {
  return typeof value === "number" && Number.isFinite(value) && value >= 0 && value <= levelCount - 1;
}

/**
 * Turns one answered value into a decision, after checking the answer against the set its question
 * was built from: a choice outside the option keys, or a score outside the level range, is a review
 * and never an act.
 */
function answerDecisionFor(question: string, value: unknown, threshold: number, allowed: boolean): Decision {
  if (!allowed) {
    return {
      question,
      outcome: "review",
      signal: null,
      threshold,
      reason: "the value is missing or outside the allowed set, so a person decides"
    };
  }
  return decisionFor(question, value, threshold);
}

/** Sends one consented request and prints one act or review decision per question. */
async function main() {
  const client = new TypeSafeClient();
  const modelId: string = MODEL;

  const response = await client.systemOne({
    model: modelId,
    state: INPUT,
    questions: {
      // `choice()` is the helper the SDK pages document, so the choice question uses it with the same
      // option object the response check reads its keys from. The boolean and score questions stay
      // plain objects, because the snapshot documents the two helpers without a signature and a plain
      // object is always accepted.
      needs_human: {
        type: "noul" as const,
        instructions: "Does this ticket need a human agent, rather than an automated reply?",
        criteria: {
          true: "The customer asks for something only a person can decide, such as a manual payout retry or a refund.",
          false: "The help article or the account data in state answers the question."
        }
      },
      any_queue_fits: {
        type: "noul" as const,
        instructions:
          "Does this ticket belong to one of the queues listed in the companion routing question " +
          "(billing, technical, account, other)? Answer no when no listed queue describes the work.",
        criteria: {
          true: "At least one listed queue describes the work this ticket needs.",
          false: "No listed queue describes it, so a person has to decide where it goes."
        }
      },
      queue: choice("Which queue should own this ticket?", QUEUE_OPTIONS),
      urgency: {
        type: "score" as const,
        instructions: "How urgent is this ticket for the customer right now?",
        criteria: URGENCY_LEVELS
      }
    }
  });

  // Log the model id that answered. An alias resolves to a version, and the answered id is where that
  // version is recorded. The field is read defensively because the SDK types an answer, not the
  // response envelope.
  const answered = response as unknown as { model?: unknown };
  const answeredModel = typeof answered.model === "string" ? answered.model : "unreported";
  console.log(`answer from ${answeredModel} (requested ${modelId})`);

  const needsHuman = response.answers.needs_human;
  const anyQueueFits = response.answers.any_queue_fits;
  const queue = response.answers.queue;
  const urgency = response.answers.urgency;

  // A boolean answer is the yes probability; a choice acts on the probability of the option it is
  // about to take; a score acts on its confidence. Every value is validated before the comparison, so
  // a bad value can never route to act, and an answered choice or score is checked against the set its
  // question was built from first.
  const decisions = [
    decisionFor("needs_human", "noul" in needsHuman ? needsHuman.noul : undefined, THRESHOLDS.booleanActAtOrAbove),
    decisionFor("any_queue_fits", "noul" in anyQueueFits ? anyQueueFits.noul : undefined, THRESHOLDS.booleanActAtOrAbove),
    answerDecisionFor(
      "queue",
      "probabilities" in queue && typeof queue.choice === "string"
        ? (queue.probabilities as Record<string, unknown>)[queue.choice]
        : undefined,
      THRESHOLDS.choiceProbabilityAtOrAbove,
      choiceIsAllowed(queue.choice, QUEUE_OPTION_KEYS)
    ),
    answerDecisionFor(
      "urgency",
      "confidence" in urgency ? urgency.confidence : undefined,
      THRESHOLDS.scoreConfidenceAtOrAbove,
      scoreIsAllowed(urgency.score, URGENCY_LEVELS.length)
    )
  ];

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
  // An answer that is not one of the option keys is printed as invalid, never as itself.
  console.log(`Chosen queue: ${choiceIsAllowed(queue.choice, QUEUE_OPTION_KEYS) ? String(queue.choice) : "invalid"}`);
}

if (LIVE_CALL_APPROVED) {
  main().catch((error: unknown) => {
    console.error("The call failed; no response was acted on.", error instanceof Error ? error.message : "");
    console.error("Check the status and the route in references/providers.md.");
    process.exitCode = 1;
  });
} else {
  console.log(`No call was made. The SDK would answer ${MODEL} for ${Object.keys(INPUT).length} top-level input fields.`);
  console.log("Set LIVE_CALL_APPROVED to true only after the user consents; the SDK reads TYPESAFE_API_KEY and never prints it.");
}
