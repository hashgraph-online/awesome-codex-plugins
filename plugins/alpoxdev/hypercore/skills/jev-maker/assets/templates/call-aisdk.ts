// Purpose: call Jev through the Vercel AI SDK evaluation API.
// experimental API: pin the package versions you install, because this evaluation API and its
// model specification can change in a patch release.
// Fill in: the STATE record and the question set below, and the thresholds, which must stay in
// step with constants.template.ts in this folder. A string model id resolves through Vercel AI
// Gateway, which reads its key from AI_GATEWAY_API_KEY. A live call only after the user consents,
// and the key is read from the environment at call time and never printed.

import { experimental_evaluate } from "ai";
import { THRESHOLDS } from "./constants.template";

// Consent gate. Leave this false until the person has agreed to a live call and knows its cost.
const LIVE_CALL_APPROVED = false;

// Snapshot 2026-10-01, re-check before a live call: references/providers.md
const MODEL_ID = "typesafe-ai/jev";
const KEY_ENV_VAR = "AI_GATEWAY_API_KEY";

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

interface Decision {
  readonly question: string;
  readonly outcome: "act" | "review";
  readonly signal: number | null;
  readonly threshold: number;
}

/**
 * Reads the provider's per-question confidence map. The documented path
 * result.providerMetadata?.typesafe?.confidence holds a map keyed by question id.
 */
function readConfidence(typesafeMetadata: unknown): JsonRecord {
  if (typeof typesafeMetadata !== "object" || typesafeMetadata === null || Array.isArray(typesafeMetadata)) {
    return {};
  }
  const byQuestion = (typesafeMetadata as JsonRecord)["confidence"];
  if (typeof byQuestion !== "object" || byQuestion === null || Array.isArray(byQuestion)) {
    return {};
  }
  return byQuestion as JsonRecord;
}

/**
 * Validates one decision signal: a value that is not a finite number inside 0..1 returns null,
 * which always becomes review, never act.
 */
function validatedSignal(value: unknown): number | null {
  return typeof value === "number" && Number.isFinite(value) && value >= 0 && value <= 1 ? value : null;
}

/** Reads one question's provider confidence, or null when the provider did not report a valid one. */
function confidenceOf(byQuestion: JsonRecord, questionId: string): number | null {
  return validatedSignal(byQuestion[questionId]);
}

/** Turns one answer value into a decision; a signal that fails validation goes to review. */
function decisionFor(question: string, value: unknown, threshold: number): Decision {
  const signal = validatedSignal(value);
  return {
    question,
    signal,
    threshold,
    outcome: signal !== null && signal >= threshold ? "act" : "review"
  };
}

/** Sends one consented request and prints one act or review decision per question. */
async function main() {
  const key = process.env[KEY_ENV_VAR];
  if (typeof key !== "string" || key.trim().length === 0) {
    throw new Error(`Environment variable ${KEY_ENV_VAR} is not set; the Gateway reads it at call time and never prints it.`);
  }

  const result = await experimental_evaluate({
    model: MODEL_ID,
    state: STATE,
    questions: {
      // This route names the yes/no type boolean; the direct and b.ai routes name it noul.
      needs_human: {
        type: "boolean",
        instructions: "Does this ticket need a human agent, rather than an automated reply?"
      },
      queue: {
        type: "choice",
        instructions: "Which queue should own this ticket?",
        criteria: {
          billing: "Charges, payouts, invoices, refunds.",
          technical: "Bugs, outages, integrations, API errors.",
          account: "Login, plan changes, team membership.",
          other: null
        }
      },
      urgency: {
        type: "score",
        instructions: "How urgent is this ticket for the customer right now?",
        criteria: [
          "Can wait: no money or access is blocked this week.",
          "Time-boxed: money or access is blocked within the next few days.",
          "Blocking: the customer cannot operate and is losing money today."
        ]
      }
    }
  });

  // A boolean answer carries a probability, which is not a confidence and is not calibrated.
  const needsHuman = result.answers.needs_human.probability;
  const confidenceByQuestion = readConfidence(result.providerMetadata?.typesafe);

  const confidenceDecision = (question: string): Decision => {
    const signal = confidenceOf(confidenceByQuestion, question);
    const threshold = THRESHOLDS.answerConfidenceAtOrAbove;
    // A missing or below-threshold confidence is not a licence to act, so it goes to review.
    return {
      question,
      signal,
      threshold,
      outcome: signal !== null && signal >= threshold ? "act" : "review"
    };
  };

  // The boolean answer's probability goes through the same 0..1 guard, so an invalid value
  // becomes a review instead of being compared against the threshold.
  const decisions: Decision[] = [
    confidenceDecision("queue"),
    confidenceDecision("urgency"),
    decisionFor("needs_human", needsHuman, THRESHOLDS.noulActAtOrAbove)
  ];

  for (const decision of decisions) {
    console.log(`${decision.question}: ${decision.outcome} (signal ${decision.signal}, threshold ${decision.threshold})`);
  }
  console.log(`Chosen queue: ${result.answers.queue.choice}`);
}

if (LIVE_CALL_APPROVED) {
  main().catch(() => {
    console.error("The call failed; no response was acted on. Check the status and the route in references/providers.md.");
    process.exitCode = 1;
  });
} else {
  console.log("No call was made. Set LIVE_CALL_APPROVED to true only after the user consents.");
  console.log(`The Gateway reads the key from ${KEY_ENV_VAR} at call time and never prints it.`);
}
