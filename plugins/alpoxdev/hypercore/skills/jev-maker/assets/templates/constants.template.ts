// Purpose: the single place holding the question set and the decision thresholds for the
// ticket-triage example, so the call templates and the routing table share one source.
// Fill in: replace the questions with your own judgments and the thresholds with your own
// values, and keep this file in step with request.json next to it.
// A live call only after the user consents, and only from one of the call templates.

// Snapshot 2026-10-01, re-check before a live call: references/providers.md
export const MODEL = "jev-latest";

// The questions sent with every request. Each one is an atomic judgment about the shared state.
// A question id is never sent to the model, so each instruction has to stand on its own.
export const QUESTIONS = {
  needs_human: {
    type: "noul",
    instructions: "Does this ticket need a human agent, rather than an automated reply?",
    criteria: {
      true: "The customer asks for something only a person can decide, such as a manual payout retry or a refund.",
      false: "The linked help article or the account data in state answers the question."
    }
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
} as const;

// The decision thresholds are assumed before tuning, so evaluate on your own data before
// trusting them, and never read a high value as permission to act.
// A noul answer is the yes probability, so it acts only at or above noulActAtOrAbove; a
// confident no falls below that same line, so add your own no-branch rule if it should act.
// Choice and score answers act only at or above answerConfidenceAtOrAbove.
export const THRESHOLDS = {
  noulActAtOrAbove: 0.6,
  answerConfidenceAtOrAbove: 0.7
} as const;
