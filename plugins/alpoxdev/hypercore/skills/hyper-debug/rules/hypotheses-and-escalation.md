# Hypotheses And Escalation

Read this before writing the first hypothesis set, and again when two rounds have failed.

## 1. One Hypothesis Is A Hunch

A single hypothesis makes every observation a confirmation. The investigator reads the code looking for the thing they already believe, discounts the contradiction, and stops at the first plausible stack frame.

Two hypotheses are the minimum that forces a decision, because the next probe must be chosen to separate them rather than to support one. Three is better when the third is genuinely different; padding with rewordings is worse than two real ones.

## 2. Orthogonal Axes

Hypotheses drawn from the same axis are variations of one guess. Spread them across axes so that a probe on one does not also move the other.

| Axis | Framing |
|---|---|
| User-code logic | A branch runs that should not: an early return, an off-by-one, a wrong constant, an inverted condition |
| Library or dependency behavior | The client swallows an error, retries internally, returns a default, or caches a stale value |
| Environment and configuration | A variable is read before it is set, a config file is not the one being loaded, a secret is empty at the point of use |
| Async and timing | A rejection lands after the response is sent, a callback runs twice, a task is dropped when the process exits |
| Shared state | An earlier step mutated state the current step inherits; a singleton, cache, or global is not reset between runs |
| Observability gap | The error is raised but suppressed before it can be logged; the failure exists only as an ignored return value |
| Build versus runtime | The code being read is not the code that runs: stale build output, a different entry point, a symlinked binary, a cached wheel |
| Data shape | The input that arrives is not the input the code assumes: null versus missing key, string versus number, empty array versus absent field |

Pick at least two axes per set, and name the axis for each hypothesis.

## 3. What Each Hypothesis Must State

For every hypothesis, write all four lines in the journal:

1. **Claim** — one sentence, in the form "X happens because Y".
2. **Distinguishing observation** — the exact value, state, or output that would confirm or refute it, and where to read it (`path:line`, a command, a log source, a port).
3. **Prediction** — what the observation looks like if the claim is true, and what it looks like if it is false. A hypothesis whose true and false predictions are the same is not testable.
4. **If true, the fix is** — two or three words. This forces the cost of the fix into view before the hunt starts.

## 4. The Collapse Rule

- If two hypotheses would be separated by the same observation with the same result, they are one hypothesis in two costumes. Collapse them and find a genuinely different alternative.
- If you cannot state a second hypothesis that predicts a different observation, you do not understand the system well enough yet. Read more of the code, the logs, and the tests before probing; do not run a probe that only confirms the first guess.
- If a hypothesis is unfalsifiable with the access available, say so and drop it rather than keeping it as a permanent maybe.

## 5. A Round

A round is one pass over the open hypothesis set:

1. Choose the probe that separates the most hypotheses at once.
2. Run it once, on the smallest setup that still shows the failure.
3. Record the value verbatim with its source.
4. Mark each hypothesis confirmed, refuted, or still open.

The round is complete when every open hypothesis has evidence, or when the available evidence sources are exhausted. An exhausted round is a failed round for the counter.

Do not run two probes that answer the same question. A repeated probe is not a new round, and it is not evidence.

## 6. Three-Way Reframe After Two Failed Rounds

Two consecutive failed rounds mean the real cause is probably in a category the current framing does not contain. More time inside the same mental model is wasted time. Reframe the problem three ways, and record all three in the journal:

| Framing | Question to answer |
|---|---|
| Obvious-but-missed | What embarrassingly simple cause is compatible with every observation? Wrong import, wrong constant, stale cache, wrong file, harness versus app, source versus built output |
| System boundary | Which boundary between components is violated? SDK behavior, middleware, gateway rewriting, build-time versus runtime environment, module load order, version mismatch, transport |
| Load-bearing assumption | Which assumption does every current hypothesis depend on, and what is the smallest query that would falsify it? |

Then:

- Note the candidates that appear in at least two framings. Independent agreement across framings is the strongest signal available.
- Turn each disagreement into a probe for the next round.
- Pull the falsification queries from the third framing into the next round as written.
- Build a new hypothesis set of at least two hypotheses, drawn from both the agreement and the disagreement.
- Reset the failed-round counter to zero.

The budget is one reframe. Two more failed rounds after it end the run as `unconfirmed` with the best hypothesis, its `Assumption:` line, and the exact check that would settle it. Do not guess a fix to escape the loop.

## 7. Escalate Only For Access

A round count is not a reason to hand the problem back. Escalate when the next step needs something the session cannot supply: a credential, a device, a production log, a reproduction only the user can trigger. Ask one specific question, mark the run `awaiting_input`, and keep everything else the journal already holds.

## Sources

> Checked 2026-11-09.

| Claim | Source |
|---|---|
| At least two competing hypotheses, each with a distinguishing observation, and the collapse rule | `dbc-hbin/omp-ulw@74df40f debugging/references/methodology/02-investigate.md` (mechanism reference, re-authored) |
| The orthogonal axis list | `dbc-hbin/omp-ulw@74df40f debugging/references/methodology/02-investigate.md` (mechanism reference, re-authored) |
| Three orthogonal reframings after two failed rounds, agreement scan, and the reset | `dbc-hbin/omp-ulw@74df40f debugging/references/methodology/04-oracle-triple.md` (mechanism reference, re-authored) |
| Escalating only for a material decision or access the session cannot supply | `dbc-hbin/omp-ulw@74df40f debugging/SKILL.md` (mechanism reference, re-authored) |

### Evidence grade

`LOCAL` - the four-line hypothesis record, the round definition, and the one-reframe budget are this package's design. The mechanism rows are re-authored from a repository with no license; no text or code is copied.
