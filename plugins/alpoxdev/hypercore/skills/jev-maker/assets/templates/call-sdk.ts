// Purpose: call Jev through the official TypeScript SDK, which reads the key from
// TYPESAFE_API_KEY, retries rate limits for you, and types each answer by question id.
// The SDK types the answer shape but does not range-check the values, so every signal is
// validated here before it can reach a decision: a value that is not a finite number inside
// 0..1 becomes a review, never an act.
// Fill in: the STATE record and the questions below, and the thresholds in
// constants.template.ts. A live call only after the user consents, and only then.
// The key is read from the environment by the SDK and is never printed here.

import { choice, TypeSafeClient } from "@typesafe-ai/sdk";
import { MODEL, THRESHOLDS } from "./constants.template";

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

// The option set and the level list are defined once here, so the check on the response reads the
// same keys and the same level count the question was built from.
const QUEUE_OPTIONS = {
  billing: "Charges, payouts, invoices, refunds.",
  technical: "Bugs, outages, integrations, API errors.",
  account: "Login, plan changes, team membership.",
  other: null
};

const QUEUE_OPTION_KEYS = Object.keys(QUEUE_OPTIONS);

// The SDK types a score rubric as a tuple of at least two entries, so the level list carries that
// type as well as being the single source of the level count.
const URGENCY_LEVELS: readonly [string, string, ...string[]] = [
  "Can wait: no money or access is blocked this week.",
  "Time-boxed: money or access is blocked within the next few days.",
  "Blocking: the customer cannot operate and is losing money today."
];

interface Decision {
  readonly question: string;
  readonly outcome: "act" | "review";
  readonly signal: number | null;
  readonly threshold: number;
  readonly reason: string;
}

/**
 * Reads a decision signal, refusing any value the SDK type cannot guarantee at runtime: a value
 * that is not a finite number inside 0..1 returns null, which always becomes review, never act.
 */
function validatedSignal(value: unknown): number | null {
  if (typeof value !== "number" || !Number.isFinite(value) || value < 0 || value > 1) return null;
  return value;
}

/** Turns one answer value into a decision; a signal that fails validation goes to review. */
function decisionFor(question: string, value: unknown, threshold: number): Decision {
  const signal = validatedSignal(value);
  if (signal === null) {
    return {
      question,
      outcome: "review",
      signal: null,
      threshold,
      reason: "the value is missing or outside 0..1, so a person decides"
    };
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
 * Turns one answered value into a decision, after checking the answer itself against the set its
 * question was built from: a choice outside the option keys, or a score outside the level range,
 * is a review and never an act, so an out-of-set value can never be printed as a valid answer.
 */
function answerDecisionFor(
  question: string,
  value: unknown,
  threshold: number,
  allowed: boolean
): Decision {
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

  const response = await client.systemOne({
    model: MODEL,
    state: STATE,
    questions: {
      // The SDK page documents the choice() helper, so the choice question uses it, with the same
      // option object the response check reads its keys from.
      queue: choice("Which queue should own this ticket?", QUEUE_OPTIONS),
      // noul and score stay plain question objects, as the HTTP API reference writes them.
      needs_human: {
        type: "noul",
        instructions: "Does this ticket need a human agent, rather than an automated reply?",
        criteria: {
          true: "The customer asks for something only a person can decide, such as a manual payout retry or a refund.",
          false: "The linked help article or the account data in state answers the question."
        }
      },
      urgency: {
        type: "score",
        instructions: "How urgent is this ticket for the customer right now?",
        criteria: URGENCY_LEVELS
      }
    }
  });

  // A noul answer is the yes probability; a choice or score answer carries the model's confidence.
  // Each value is validated before the comparison, so a bad value can never route to act, and an
  // answered choice or score is checked against the set its question was built from first.
  const decisions = [
    decisionFor("needs_human", response.answers.needs_human.noul, THRESHOLDS.noulActAtOrAbove),
    answerDecisionFor(
      "queue",
      response.answers.queue.confidence,
      THRESHOLDS.answerConfidenceAtOrAbove,
      choiceIsAllowed(response.answers.queue.choice, QUEUE_OPTION_KEYS)
    ),
    answerDecisionFor(
      "urgency",
      response.answers.urgency.confidence,
      THRESHOLDS.answerConfidenceAtOrAbove,
      scoreIsAllowed(response.answers.urgency.score, URGENCY_LEVELS.length)
    )
  ];

  for (const decision of decisions) {
    console.log(
      `${decision.question}: ${decision.outcome} (signal ${decision.signal}, threshold ${decision.threshold}) - ${decision.reason}`
    );
  }
  // An answer that is not one of the option keys is printed as invalid, never as itself.
  const chosenQueue = choiceIsAllowed(response.answers.queue.choice, QUEUE_OPTION_KEYS)
    ? response.answers.queue.choice
    : "invalid";
  console.log(`Chosen queue: ${chosenQueue}`);
}

if (LIVE_CALL_APPROVED) {
  main().catch(() => {
    console.error("The call failed; no response was acted on. Check the status and the route in references/providers.md.");
    process.exitCode = 1;
  });
} else {
  console.log("No call was made. Set LIVE_CALL_APPROVED to true only after the user consents.");
  console.log("The SDK reads the key from TYPESAFE_API_KEY at call time and never prints it.");
}
