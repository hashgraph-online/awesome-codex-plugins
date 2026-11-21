---
name: options-simulation
description: Simulate an underlying forward from its own realised behaviour using a Bayesian GARCH(1,1) model with Student-t innovations sampled by MCMC, then report the posterior predictive fan, value at risk, expected shortfall, and the profit distribution of any structures already built. Use when the user asks what the underlying might do, what the downside is, what value at risk or expected shortfall looks like, how likely a structure is to profit given how the stock actually moves, or asks for a Monte Carlo, a simulation, an MCMC, or a distribution of outcomes. Not for order placement and not for recommendations.
---

# Simulation

A second opinion on probability. Everything else in this desk prices from
the volatility the options are quoted at; this prices from the volatility
the underlying has actually shown.

## Execution route

Prefer the `option_simulate` MCP tool. If it is not available, use the
`optiondesk` command below. If neither MCP nor the CLI is available, say
that no fresh simulation can be produced; do not invent figures or present
an example or remembered result as a new analysis.

## Data boundary

Use fresh provider data only when the tool reports that access is allowed.
A local Yahoo adapter also requires the personal-use acknowledgement. A
hosted tool must use a provider that is approved for public display, derived
outputs, storage, and MCP delivery. Never bypass a provider refusal. When no
approved tool is available, analyse a snapshot that the user supplied and
had the right to share. Otherwise, state that current figures are unavailable.

## Run it

```
optiondesk simulate SPY --horizon 14
```

Options: `--paths` (default 20000, independent draws), `--draws` and
`--burn` per chain, `--chains` (default 2, needed for the R-hat
diagnostic), `--period` for how much history to fit, and
`--no-structures` to skip the per-structure distributions.

## What the model is

GARCH(1,1) with standardised Student-t innovations: volatility clusters
and the tail is fatter than a normal admits. Estimated by adaptive
random-walk Metropolis over model parameters. Each simulated path selects
a retained parameter draw, so the fan includes parameter uncertainty and
conditional shocks. Their relative contribution depends on the fitted
sample and horizon; the diagnostics do not establish market calibration.

## Convergence is not optional

Read `posterior.converged` before quoting a single quantile. It is false
when any parameter lacks finite split R-hat below 1.05 or ESS of at least
100, or when post-burn acceptance is zero. Say that the diagnostic gate
failed, and
suggest raising `--draws`, rather than reporting the numbers anyway.

## The comparison that matters

For every structure on disk, the output gives probability of profit under
realised volatility next to the same probability under implied. The gap
between them is the market's forecast disagreeing with the recent past.
Neither side is the truth. Report the gap as a disagreement, never as an
edge, and never as a reason to trade.

Value at risk and expected shortfall are on the underlying's return over
the horizon, using a loss sign convention. An all-gain sample can produce
negative values. They are model statistics, not worst-case limits.

The structure callback uses intrinsic payoff at the requested horizon.
It does not align each plan expiry or preserve surviving time value. State
that limitation when comparing simulated and analytic profit probabilities.
Under Student-t log returns, finite sample means of unbounded payoffs do
not establish finite model expectations. See `reference.md` for the scope.

## Reporting rules

These hold for every number this skill produces.

Cite the artifact path when reporting from it. The artifact is the record;
prose is a summary of it, and a number quoted without its source cannot be
checked later.

Read `degraded` before quoting anything. When it is true, say so and give
`degraded_reason` first, in the same breath as the number rather than as a
footnote. Every command carries both fields in the summary it prints, not
only in the artifact.

Do not re-derive numbers yourself. If a figure is not in the artifact, say
it is not there rather than computing a replacement, and never substitute a
default for a value the pipeline refused to produce.

Premiums are model values or mid quotes from delayed third-party data. They
are not fills, and a real entry crosses the spread on every leg.

Never recommend a trade, an entry, an exit or a size. This is research
software and it is not investment advice. Present the analysis and let the
reader decide.
The full terms are in DISCLAIMER.md, which ships beside this skill when it
is installed from a package and sits at the repository root otherwise. The
substance is already above: research software, not advice, modelled numbers
that are not fills.


## What an audit found in these numbers, and what to say about it

**Value at risk here is not drift free.** The posterior median drift on the
live SPY fit was about 26 percent a year, so a 30 day value at risk of 3.92
percent sits only 3.92 below spot while the distance from the median down
to the fifth percentile is 6.98 percentage points. Both numbers are
correct. If a reader hears "the 5 percent worst case is a 3.9 percent
fall", they are hearing something the artifact did not say, because roughly
half of that comfort is the fitted upward drift rather than a narrow
distribution. Quote the median return beside the tail figure.

**Paths are independent draws, not antithetic pairs.** Every artifact
written before September 2026 said `antithetic: true`. It was never true:
of ten thousand pairs, none shared a shock sequence. The construction has
been removed and the flag now reads false. If you are reading an older
artifact, treat that field as unreliable rather than as history.

**The reported ESS is the minimum estimate across individual chains.**
Each estimate truncates its autocorrelation sum, which can overstate ESS
when mixing is slow. Taking the minimum does not guarantee a conservative
result. Report it as this implementation's diagnostic estimate, not a
pooled or tail ESS.

**Persistence is the sum of the medians of alpha and beta**, not the median
of their sum. On this posterior the two differ by 7e-05, which is nothing,
but they are different quantities and the artifact stores no joint draws
for a reader to check.

## It is slow, and that is not a hang

The sampler is a Metropolis-Hastings walk written in pure Python. It is
single threaded, it uses no vectorisation and no C extension, and it prints
nothing between starting and finishing. The work is
(draws + burn) x chains iterations over every observation in the history.

Measured on an eighteen core arm64 machine with 1253 daily observations:
the default settings take about eight seconds, and draws 6000 with burn
2000 across four chains takes about twenty-seven. A slower or single core
machine takes proportionally longer, and a long history with a high draw
count can run for minutes.

The command prints one line to stderr before it starts, saying how many
iterations it is about to run and roughly how long that should take. When
you see it, wait. Do not kill the run, do not retry it with a smaller draw
count to make it finish, and do not report the tool as hung. A run
interrupted partway writes nothing. Fewer retained draws can reduce ESS;
inspect the diagnostics rather than assuming a lower draw count must fail.

If a user asks why it is taking so long, the answer is the iteration count
and the observation count, both of which are in the notice on stderr and in
the artifact's inputs block.


## Going deeper

- `reference.md`: the model, convergence gate, effective sample size limits, risk measures, and independent path generation.
- `workflows/run-a-projection.md`: running one and reporting it without overclaiming.
