// Purpose: call a decision model through the Vercel AI SDK, which wraps native decision providers and
// language-model adapters behind one function. Validate every answer here, then turn each answer into
// an act or review decision, branching on whether the route returned a distribution at all.
//
// Experimental API: `experimental_decide` and `Experimental_DecisionModelV4` can change in a patch
// release, so pin the versions you install. Observed on 2026-11-06: `ai` 7.0.164,
// `@ai-sdk/typesafe-ai` 3.0.34, `@ai-sdk/provider` 4.0.36.
// The previous name `experimental_evaluate` still exists as a deprecated alias. Use
// `experimental_decide`, and note that the provider factory was renamed from `evaluationModel` to
// `decisionModel` in the same change.
//
// Fill in: the INPUT record and the QUESTIONS below, and keep the thresholds in step with
// constants.template.ts. A live call only after the user consents. The TypeSafe provider reads its
// key from TYPESAFE_AI_API_KEY, which is deliberately a different variable from the direct SDK's
// TYPESAFE_API_KEY; the value is never printed here.

import { experimental_decide } from "ai";
import { typeSafeAi } from "@ai-sdk/typesafe-ai";
import { MODEL, THRESHOLDS } from "./constants.template";

// Snapshot 2026-11-08, re-check before the first live call: references/providers.md and
// references/official/jev-platform.md. The model id appears once, here.
const MODEL_ID = MODEL;
const KEY_ENV_VAR = "TYPESAFE_AI_API_KEY";

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

// The AI SDK keeps the neutral type names: boolean, choice, score, and box. Only the TypeSafe provider
// accepts box, so a request that needs box cannot move to another provider unchanged.
const QUESTIONS = {
  needs_human: {
    type: "boolean" as const,
    instructions: "Does this ticket need a human agent, rather than an automated reply?"
  },
  any_queue_fits: {
    type: "boolean" as const,
    instructions:
      "Does this ticket belong to one of the queues listed in the companion routing question " +
      "(billing, technical, account, other)? Answer no when no listed queue describes the work."
  },
  queue: {
    type: "choice" as const,
    instructions:
      "Which queue should own this ticket? Pick the closest queue; the companion boolean decides " +
      "whether any queue actually fits.",
    criteria: {
      billing: "Charges, payouts, invoices, refunds.",
      technical: "Bugs, outages, integrations, API errors.",
      account: "Login, plan changes, team membership.",
      other: "A last resort: real work, but no listed queue describes it."
    }
  },
  urgency: {
    type: "score" as const,
    instructions: "How urgent is this ticket for the customer right now?",
    criteria: [
      "Can wait: no money or access is blocked this week.",
      "Time-boxed: money or access is blocked within the next few days.",
      "Blocking: the customer cannot operate and is losing money today."
    ]
  }
};

type JsonRecord = Record<string, unknown>;

interface Decision {
  readonly question: string;
  readonly outcome: "act" | "review";
  readonly signal: number | null;
  readonly threshold: number;
  readonly reason: string;
}

/** Reports whether a value is a plain JSON object. */
function isRecord(value: unknown): value is JsonRecord {
  return typeof value === "object" && value !== null && !Array.isArray(value);
}

/**
 * Reads the provider's per-question confidence map. The documented path is
 * `result.providerMetadata?.typesafe?.confidence`, keyed by question id. The SDK does not promise
 * that confidence is comparable across providers, so it stays a vendor-tagged statistic here.
 */
function readConfidence(typesafeMetadata: unknown): JsonRecord {
  if (!isRecord(typesafeMetadata)) return {};
  const byQuestion = typesafeMetadata.confidence;
  return isRecord(byQuestion) ? byQuestion : {};
}

/**
 * Returns the value only when it is a finite number inside 0..1. A missing value returns null, which
 * always becomes review and never act.
 */
function validatedSignal(value: unknown): number | null {
  return typeof value === "number" && Number.isFinite(value) && value >= 0 && value <= 1 ? value : null;
}

/**
 * Reads the probability of one option or level out of an answer's distribution. The distribution is
 * optional in the SDK contract because the Anthropic and Google adapters return no probabilities at
 * all: they adapt a language model's structured output, so a choice answer carries only the chosen
 * option. A missing distribution therefore means "this route has no signal", not "this answer is bad".
 */
function probabilityOf(distribution: unknown, key: string): number | null {
  if (!isRecord(distribution)) return null;
  const value = distribution[key];
  return validatedSignal(value);
}

/** Builds one decision from a signal that may be null; a null signal is always review. */
function decisionFor(question: string, signal: number | null, threshold: number, why: string | null): Decision {
  if (signal === null) {
    return { question, outcome: "review", signal: null, threshold, reason: why ?? "no usable signal, so a person decides" };
  }
  return signal >= threshold
    ? { question, outcome: "act", signal, threshold, reason: "at or above the threshold" }
    : { question, outcome: "review", signal, threshold, reason: "below the threshold" };
}

/** Sends one consented request and prints one act or review decision per question. */
async function main() {
  const key = process.env[KEY_ENV_VAR];
  if (typeof key !== "string" || key.trim().length === 0) {
    throw new Error(`Environment variable ${KEY_ENV_VAR} is not set; the provider reads it at call time and never prints it.`);
  }

  const result = await experimental_decide({
    model: typeSafeAi.decisionModel(MODEL_ID),
    state: INPUT,
    questions: QUESTIONS
  });

  const confidenceByQuestion = readConfidence(result.providerMetadata?.typesafe);
  // The answered model id is read defensively: a gateway route can lose the version, and the result
  // envelope is not part of the documented decision contract the way the answers are.
  const answered = result as unknown as { modelId?: unknown };
  console.log(`answer from ${typeof answered.modelId === "string" ? answered.modelId : "unreported"} (requested ${MODEL_ID})`);

  const needsHuman = result.answers.needs_human as JsonRecord;
  const anyQueueFits = result.answers.any_queue_fits as JsonRecord;
  const queue = result.answers.queue as JsonRecord;
  const urgency = result.answers.urgency as JsonRecord;

  const decisions: Decision[] = [
    // A boolean answer's probability is P(true). It is a prompted estimate on a language-model
    // adapter and a native number on a decision provider, and neither is promised to be calibrated.
    decisionFor(
      "needs_human",
      validatedSignal(needsHuman.probability),
      THRESHOLDS.booleanActAtOrAbove,
      null
    ),
    decisionFor(
      "any_queue_fits",
      validatedSignal(anyQueueFits.probability),
      THRESHOLDS.booleanActAtOrAbove,
      null
    ),
    // Act on the chosen option's probability, not on the confidence beside it.
    decisionFor(
      "queue",
      probabilityOf(queue.probabilities, String(queue.choice)),
      THRESHOLDS.choiceProbabilityAtOrAbove,
      isRecord(queue.probabilities)
        ? "the chosen option carries no probability, so a person decides"
        : "this route returned no distribution, so the answer goes to a person"
    ),
    // A score's confidence is the only portable signal; without it the answer goes to review.
    decisionFor(
      "urgency",
      validatedSignal(confidenceByQuestion.urgency),
      THRESHOLDS.scoreConfidenceAtOrAbove,
      "this route reported no confidence, so a person decides"
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
  // Reading the chosen option directly is safe only after the answer was validated; the SDK types it,
  // but a caller that swaps the model must still check the value against its own option set.
  console.log(`Chosen queue: ${String(queue.choice)}`);
}

if (LIVE_CALL_APPROVED) {
  main().catch((error: unknown) => {
    console.error("The call failed; no response was acted on.", error instanceof Error ? error.message : "");
    console.error("Check the status and the route in references/providers.md.");
    process.exitCode = 1;
  });
} else {
  console.log(`Model: ${MODEL_ID} through the TypeSafe decision provider. No call was made.`);
  console.log(`Set LIVE_CALL_APPROVED to true only after the user consents; the key is read from ${KEY_ENV_VAR}.`);
}
