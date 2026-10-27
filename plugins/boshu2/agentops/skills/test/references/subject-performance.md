# Subject performance

Use this reference when the caller selects measurement of software performance,
including a suspected regression. Measure the subject on a named workload;
results do not establish that a skill, prompt or model caused a better outcome.
Those comparisons belong to [Skill Eval](../../skill-eval/SKILL.md).

## Select the comparison

Name a representative workload, its input size and shape, expected output and
the metric that answers the caller's question. State the unit and direction of
benefit: for example, completion time in milliseconds, successful records per
second or peak resident memory in bytes. Distinguish elapsed time from CPU time
and allocated memory from resident memory. Use existing repository measurement
tools rather than building a benchmark framework for a single comparison.

Identify the exact baseline and candidate source/build, toolchain and build
options, plus the input digest or exact generator identity and seed. A revision
name alone does not identify an uncommitted build. Keep setup costs inside or
outside the measured interval consistently and explain which work it includes.

Compare under equivalent relevant conditions: hardware, runtime, resource
limits, concurrent load, dependencies and cold or warmed state. State the cache
and initialization treatment instead of mixing first-use cost with steady use.
If conditions cannot be matched, disclose the confounder and limit the claim.
An unrelated historical number is not automatically a comparable baseline.

## Observe variability

Use repeated samples when scheduling, caching, network or other variability can
change the conclusion. Select the amount of observation for that variability,
the decision and real remaining bounds; no fixed sample count fits every task.
Keep comparable measurement treatment for baseline and candidate, and account
for drift or order effects when they matter. State sample counts and preserve
errors or unsuccessful work rather than timing only favorable completions.

Report the actual distribution or variability relevant to the metric, such as
individual timings and a range for a small sample, or a supported summary and
spread for a larger one. A lone timing is a single observation. Name the
aggregation method; do not invent percentiles, precision or confidence the data
cannot support. A timer result does not imply profiling was performed.

Compare the useful effect with measured noise and the caller's accepted budget
or practical need. Report an unclear difference as inconclusive. There is no
universal percentage that separates improvement from noise for every workload.
Equal performance is no improvement. Without a baseline, report absolute values
and comparison unavailable; a missing or zero baseline permits no percentage
improvement claim. Keep absolute differences and metric direction explicit.

## Explain a bottleneck only when needed

For a requested diagnosis, use profiling supported by the language, host and
permissions on the selected workload. Choose the measurement for the suspected
cost, such as CPU, allocation, waiting or I/O; verify that the profile covers the
work in question. Locate the expensive path in the measured evidence rather
than assuming a visually complicated function is the bottleneck.

Profiling overhead and a changed instrumentation build can distort timing.
Keep profiling evidence distinct from comparable performance samples, and
disclose unavailable symbols, sampling limits or missing facilities. No profile
means the hotspot explanation remains unproven; it does not authorize inventing
platform support or modifying system settings to obtain it.

## When improving product performance is authorized

When the caller authorizes optimization and the useful change is uncertain,
start with the cheapest available measurement that separates the suspected
cost by stage, call or query. Unavailable measurement limits attribution; it
is not evidence that visually complicated code is the bottleneck. Keep this
work within the actual authorized workload, resources and remaining bounds.

Before an experiment, state the predicted metric effect or its uncertainty.
Change one relevant factor when causal attribution matters; compare with the
identified baseline under equivalent conditions and the correctness guards
below. Retain a candidate as an improvement only when its useful effect is
supported beyond the observed noise. An inconclusive result is not a win.
When several retained changes accumulate, report the overall gain from one
comparison of the original baseline with the final candidate on the same
workload. Gains measured one change at a time do not add up, because changes
overlap or interfere; a change measured alone has not shown its contribution in
combination.

After an unsuccessful experiment, remove only its own changes when safe and
within authority; preserve other edits and useful evidence. A legitimate
caller-authorized rollback remains available. Do not reset a shared checkout
or undo unrelated work merely to recover a baseline. Stop at the accepted
target, no supported next experiment, an observed plateau or the real bound,
whichever comes first; a new hypothesis does not renew that bound. Implement
owns authorized source edits; no retry controller or new allowance is created.

## Guard the promised behavior

Check accepted outputs, ordering, errors and side effects as applicable before
calling a candidate faster. A candidate that skips records, weakens validation
or produces the wrong result fails the requested behavior despite a lower time.
Use existing correctness checks or a credible reference; baseline agreement
alone is insufficient when the baseline has a known defect.

Example: measure an authorized change to a catalog export on the same selected
catalog. Check the exported rows and their order, then compare build identities,
elapsed samples and relevant memory use. A shorter export that omits entries is
a failed candidate. A small timing decrease within observed variation supports
no clear gain; a missing baseline supports only an absolute measurement.

Measurement authority covers the selected workload and its necessary safe
checks. It grants no automatic optimization, system tuning, commits or delivery
transition. If a repair is already authorized, Implement owns the source change
and remeasurement stays on the original workload and correctness guards.

Return workload, identities, environment, metric/unit, measured samples or
summary, variability, correctness results and limits in the existing handoff.
Persist a profile or timing output only for a requested destination or declared
consumer. Add no report tree, gate or mandatory measurement phase.
