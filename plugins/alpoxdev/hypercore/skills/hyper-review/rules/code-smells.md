# Code smells

Measurable triggers, not taste. Each trigger names the measurement, the threshold, and what counts as an exception. Report the measurement, so the author can disagree with a number instead of an opinion.

## Contents

1. Size
2. Parameters
3. Redundant re-verification
4. Negative-form names
5. Duplication
6. Nesting and control flow
7. Comment and naming hygiene
8. Reporting a trigger

## 1. Size

| Trigger | Threshold | Measurement |
|---|---|---|
| Long function | More than 250 lines of pure code in one function or method | Count lines excluding blank lines, comment-only lines, and lines that close a block by themselves |
| Long file | More than 800 lines in one source file | Whole-file line count excluding blank and comment-only lines |
| Long parameter list body | More than 80 lines after the signature with three or more levels of indentation | Indentation depth inside the function body plus pure line count |
| Wide surface | More than 20 exported or public members in one module | Count declarations the module exposes |

A generated file, a table, a migration, a fixture, and a vendored file are exceptions: say so and move on. A function that is long only because it is a flat switch or a lookup is a `note`, not a blocker, unless the change adds to it.

## 2. Parameters

| Trigger | Threshold | Measurement |
|---|---|---|
| Too many parameters | More than three parameters | Count the declared parameters, excluding `self`, `this`, and a receiver |
| Boolean parameter that selects behavior | Any boolean parameter whose value changes what the function does | A call site passing a literal `true` or `false` where the two branches differ |
| Optional parameter pile | More than two optional or defaulted parameters | Count parameters with a default value |
| Parameter object used as a grab bag | A parameter object with more than five fields where each call uses a different subset | Count fields and distinct call subsets |

An exception is a fixed interface the change must keep: a callback signature, a framework hook, a foreign API. Name the constraint.

The fix is not "wrap it in an object" by reflex. Prefer deleting the parameter, splitting the function by what it does, or moving the selection to the caller with a named function.

## 3. Redundant re-verification

| Trigger | Threshold | Measurement |
|---|---|---|
| Repeated validation of the same value | The same check on the same value appears two or more times in one call path | Follow the value from entry to use; count checks |
| Defensive check that cannot fail | A null or bounds check on a value that the previous line guarantees is present | The producing statement is in the same block and cannot return empty |
| Re-parse or re-decode | The same input is parsed, decoded, or normalized more than once | Count conversions of the same value on one path |
| Double fetch | The same remote or database read happens twice for one request | Count calls with the same key on one path |

An exception is a boundary you do not control: a public function, a callback from foreign code, a value read from disk or the network. Verification at a trust boundary is not redundant.

## 4. Negative-form names

| Trigger | Measurement | Why |
|---|---|---|
| Negated boolean name | An identifier starting with `not`, `no`, `never`, `disable`, or ending in `Disabled`, `Off`, `Excluded` | Every call site needs a double negative to reason about it |
| Double negation | A condition with two negations, such as `!notReady` or `if not disabled` | The reader has to compute the truth twice |
| Negative prefix with a positive default | `noCache = false` meaning "cache is on" | The default is unreadable without the doc |
| Name that states the absence of a behavior | `doNotRetry`, `skipValidation`, `withoutLogging` | It names what does not happen, so the positive path is unnamed |

A name from a foreign API or a wire format is an exception. Report it as `note` and keep the name at the boundary; rename only inside the project's own code.

## 5. Duplication

| Trigger | Threshold | Measurement |
|---|---|---|
| Copied block | More than 10 consecutive meaningful lines appear twice with only identifier changes | Count the lines in each copy |
| Parallel structure | Two functions with the same shape where only one expression differs, each over 20 lines | Compare the control flow |
| Second implementation of an existing behavior | The change re-implements something the project already has | Name the existing location |

Duplication under 10 lines is not automatically a finding: two three-line blocks are cheaper to read than an abstraction. Report the count so the tradeoff is visible.

## 6. Nesting and control flow

| Trigger | Threshold | Measurement |
|---|---|---|
| Deep nesting | Three or more levels of nested conditionals inside one function | Count the maximum indentation depth of conditionals |
| Long conditional chain | More than four `else if` branches on one value | Count branches |
| Loop with more than one exit besides the loop condition | Two or more `break`, `return`, or `continue` statements inside one loop where they overlap | Trace each exit |
| Swallowed error | An empty catch, a catch that logs and continues, or a default returned in place of a failure | Inspect every catch and every error-returning call |

A parser, a state machine, and a table-driven dispatcher are exceptions to the nesting and chain triggers when the shape mirrors the problem.

## 7. Comment and naming hygiene

| Trigger | Measurement |
|---|---|
| Comment restates the code | The comment paraphrases the next line with no added reason |
| Stale comment | The comment describes a behavior the code no longer has |
| Commented-out code | A block of code disabled by comment markers, with no explanation |
| Debug leftover | A print, log, or trace that exists only for the author |
| Abbreviation that is not standard in this project | A short name whose expansion is not obvious from the module |

## 8. Reporting a trigger

```text
Smell: long function | 287 pure lines | billing.ts:41-330 | blocker: should fix
Smell: four parameters | buildInvoice(a, b, c, d) | billing.ts:88 | should fix
Smell: redundant re-verification | amount validated at :92 and :101, same value | should fix
Smell: negative-form name | `noRetry` used as `if (!noRetry)` at :140 | note
```

Severity:

- `blocker` when the trigger hides a likely defect: a swallowed error, a defensive check that would mask a broken contract, a duplicated money or permission rule.
- `should fix` when the threshold is crossed and the fix is local.
- `note` when the project's conventions explain the shape.

Thresholds are guidance. A project convention, a language idiom, or a stated constraint outranks a number here, and the report says which one applied.

## Sources

> Checked 2026-11-10.

| Claim | Source |
|---|---|
| The 250-line function trigger | `dbc-hbin/omp-ulw@74df40f programming/references/code-smells.md` (mechanism reference, re-authored) |
| The more-than-three-parameters trigger | same source, re-authored |
| The redundant re-verification trigger | same source, re-authored |
| The negative-form name trigger | same source, re-authored |
| The additional size, duplication, nesting, and hygiene triggers | this package's chosen design |
| Treating the numbers as guidance that a project convention can outrank | this package's chosen design |

### Evidence grade

`MECHANISM` for the four source triggers. `LOCAL` for the rest of the table and the thresholds. None of the numbers is a measured optimum; they are thresholds chosen so that a finding can be argued with.
