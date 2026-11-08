// Purpose: the single place holding the question set, the model id, and the decision thresholds for
// the ticket-triage example, so the call templates and the routing table share one source.
// Fill in: replace the questions with your own judgments and the thresholds with your own values,
// and keep this file in step with request.json (TypeSafe dialect) and request-openai.json (OpenAI
// dialect) next to it.
// A live call only after the user consents, and only from one of the call templates.
//
// Snapshot 2026-11-08, re-check before the first live call: references/official/jev-platform.md
// This id is the versioned TypeSafe id; an alias such as jev-latest moves when a release ships, and a
// threshold tuned against one version does not carry over to the next without re-measuring.
export const MODEL = "jev-1.14.0";

// The same model id in the OpenAI Decisions dialect. gpt-6-luna is the only model that dialect
// documents as supported on 2026-11-08; see references/official/openai-decisions.md.
export const MODEL_OPENAI = "gpt-6-luna";

// The neutral question types are boolean, choice, score, and box. Each dialect spells them its own
// way, and this file keeps the TypeSafe spelling because request.json is the TypeSafe request:
// boolean -> noul, choice -> choice, score -> score. The AI SDK keeps boolean, and the OpenAI dialect
// uses predicate for boolean, choices[] for a choice, and levels[] for a score.
// Box exists on TypeSafe Jev 1.14 only; no other dialect in this package accepts it.
//
// The questions sent with every request. Each one is an atomic judgment about the shared input.
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
  // The companion boolean: a choice always returns one of its options, so a separate question asks
  // whether any option fits at all. A catch-all option competes with the real options for probability.
  any_queue_fits: {
    type: "noul",
    instructions:
      "Does this ticket belong to one of the queues listed in the companion routing question: " +
      "billing, technical, account, or other?",
    criteria: {
      true: "At least one listed queue describes the work this ticket needs.",
      false: "No listed queue describes the work this ticket needs, so a person has to decide where it goes."
    }
  },
  queue: {
    type: "choice",
    instructions: "Which queue should own this ticket? Pick the closest queue; the companion question decides whether any queue actually fits.",
    criteria: {
      billing: "Charges, payouts, invoices, refunds.",
      technical: "Bugs, outages, integrations, API errors.",
      account: "Login, plan changes, team membership.",
      other: "A last resort: the ticket is real work but no listed queue describes it."
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

// The decision thresholds are pre-tuning assumptions, so evaluate them on your own labeled cases
// before trusting them, and never read a high value as permission to act.
// A boolean answer is the yes probability, so it acts only at or above booleanActAtOrAbove; a
// confident no falls below that same line, so add your own no-branch rule if it should act.
// A choice acts on the probability of the option it is about to take, not on confidence; a score
// acts on its own confidence where the route reports one. A route that returns no distribution (a
// language-model adapter) has nothing to compare, so it always takes the review path.
export const THRESHOLDS = {
  booleanActAtOrAbove: 0.6,
  choiceProbabilityAtOrAbove: 0.7,
  scoreConfidenceAtOrAbove: 0.7
} as const;
