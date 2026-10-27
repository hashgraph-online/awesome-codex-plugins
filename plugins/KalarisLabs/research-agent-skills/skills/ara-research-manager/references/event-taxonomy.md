# Event Taxonomy & Routing Rules

## Event Classification

When you observe activity in the coding session, classify it into one of these event types.
Use the **signals** column to identify events from conversation and code context.

### Research Events (Route to `trace/exploration_tree.yaml`)

| Type | Signals | Example |
|------|---------|---------|
| **question** | User asks "what if...", "should we...", "how does..." about research direction | "Should we use attention or convolution for the encoder?" |
| **decision** | User chooses between alternatives, commits to a direction | "Let's go with GQA instead of MHA — lower memory footprint" |
| **experiment** | Code runs a test/benchmark, user reports results | "The learning rate sweep shows 3e-4 is optimal" |
| **dead_end** | Approach abandoned, hypothesis falsified, "this doesn't work" | "Tried FP16 but the loss diverges after 1k steps" |
| **pivot** | Major direction change triggered by evidence | "The attention approach is too slow — switching to state space models" |

### Knowledge Events (Route to `logic/`)

| Type | Signals | Routes To |
|------|---------|-----------|
| **claim** | "I believe...", "The system achieves...", assertion about capability/property | `logic/claims.md` |
| **heuristic** | "The trick is...", "You need to...", implementation insight | `logic/solution/heuristics.md` |
| **concept** | New term defined, disambiguation needed | `logic/concepts.md` |
| **constraint** | "This only works when...", boundary condition | `logic/solution/constraints.md` |
| **architecture** | System design, component relationships | `logic/solution/architecture.md` |

### Evidence Events (Route to `evidence/`)

| Type | Signals | Routes To |
|------|---------|-----------|
| **result_table** | Tabular data, benchmark numbers, comparison matrix | `evidence/tables/table{N}.md` |
| **result_figure** | Plot data, visualization, chart values | `evidence/figures/fig{N}.md` |
| **metric** | Single quantitative measurement | Inline in experiment node or evidence file |

### Process Events (Route to `trace/sessions/`)

| Type | Signals | Routes To |
|------|---------|-----------|
| **ai-action** | Agent wrote code, ran command, created file | Session record |
| **ai-suggestion** | Agent proposed direction, hypothesis, approach | Session record (ai_suggestions_pending) |
| **user-direction** | User gives high-level instruction or corrects | Session record (events_logged with provenance: user) |

### Staging Events (Route to `staging/`)

| Type | Signals | Routes To |
|------|---------|-----------|
| **observation** | Doesn't clearly fit above categories; interesting but unstructured | `staging/observations.yaml` |

## Routing Decision Tree

```
Is it about a choice between alternatives?
  → YES: decision (trace)
  → NO: ↓

Is it a quantitative result or experimental outcome?
  → YES: experiment (trace) + evidence data (evidence/)
  → NO: ↓

Is it an abandoned approach with a reason?
  → YES: dead_end (trace)
  → NO: ↓

Is it a falsifiable assertion about the system/method?
  → YES: claim (logic/claims.md)
  → NO: ↓

Is it an implementation trick with rationale?
  → YES: heuristic (logic/solution/heuristics.md)
  → NO: ↓

Is it a major direction change?
  → YES: pivot (trace)
  → NO: ↓

Is it a research question being explored?
  → YES: question (trace)
  → NO: → observation (staging)
```

## Provenance Assignment

```
Who generated this information?

User said it directly (typed it, stated it, confirmed it)
  → provenance: user

AI inferred it from code, output, or conversation context
  → provenance: ai-suggested

AI performed an action (wrote code, ran test, made edit)
  → provenance: ai-executed

User modified an AI suggestion ("no, actually..." / "more like...")
  → provenance: user-revised
```

## ID Conventions

| Type | Prefix | Example | Scope |
|------|--------|---------|-------|
| Exploration node | N | N01, N02 | Global (across all sessions) |
| Claim | C | C01, C02 | Global |
| Heuristic | H | H01, H02 | Global |
| Experiment plan | E | E01, E02 | Global |
| Observation | O | O01, O02 | Global |
| Session | date_seq | 2026-03-11_001 | Unique by date |

**Auto-increment**: Always read the existing file to find the highest ID before creating a new one.

## Forensic Binding Checklist

When logging any event, establish these bindings immediately:

- [ ] **Claim → Proof**: If a claim is created, what evidence would prove/disprove it? Set `Proof: [pending]` if no evidence yet.
- [ ] **Experiment → Claim**: Which claims does this experiment test? Link via `Claims tested:`.
- [ ] **Heuristic → Code**: Where in the codebase is this implemented? Set `Code ref:`.
- [ ] **Decision → Evidence**: What evidence or reasoning drove this decision?
- [ ] **Dead End → Lesson**: What was learned? Could this knowledge prevent future mistakes?

If a binding can't be established now, add a `<!-- TODO: bind to {target} -->` comment as a trackable obligation.
