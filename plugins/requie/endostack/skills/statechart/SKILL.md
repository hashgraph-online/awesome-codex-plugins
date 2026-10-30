---
name: statechart
description: Model-check a TLA+ spec with TLC and turn the result into a reader-labeled Mermaid state diagram plus a report of the shortest path to every violated rule. Use on /statechart, to explain a bug as a walk through states, or to read any TLA+ result (formal verify skills route here).
disable-model-invocation: true
---

# statechart

Run TLC on a TLA+ spec of anything with discrete states (a signup flow, a network protocol, a job queue) and present the result in the terms of the person who has to judge it. The tool writes a Mermaid state diagram and a markdown report that gives, for every violated rule, the shortest sequence of steps that reaches the violation.

Verify skills produced by the `create-formal-verification-skill` skill ([../create-formal-verification-skill/SKILL.md](../create-formal-verification-skill/SKILL.md)) send their TLA+ results here. Do not use this skill for other formalisms or for systems with no meaningful discrete state.

The CLI is `scripts/statechart`. Its flags, environment variables, and exit codes are documented in [scripts/README.md](scripts/README.md) and in its usage text; this file covers how to use it well.

## Running it

1. Copy the spec and its config into a throwaway directory outside the repo (`mktemp -d`), so generated files never land in a commit.
2. Run `scripts/statechart <spec.tla>`, adding the config, view, and output-folder flags from the README as needed. By default it reads the `.cfg` beside the spec and writes to a new `<spec>-chart` folder. The output folder must be absent or empty.
3. The first run downloads a pinned TLA+ tools jar (checked against a SHA-256), so it needs network access once. It never installs Java: you need Java 11 or later on `PATH`, or `JAVA` pointing at one. Read the README for the variables that point it at a jar you already have or block the download.

## Writing the spec

- **Every rule the reader cares about is an INVARIANT.** Rules can be about what a screen shows, an outcome, stored data, or a message sent. If no variable models what a rule talks about, add one. Never weaken a rule until it holds.
- **Write Next as an explicit disjunction of named actions** (`Next == Submit \/ Retry \/ Expire`). If Next is one opaque formula, TLC credits every transition to that single name and the diagram loses its step labels.
- **Allow legitimate final states.** TLC's deadlock check flags any state without a successor, including a finished checkout. Add an action enabled only in final states that leaves every variable unchanged (`Done == status = "complete" /\ UNCHANGED vars`), and give it a readable label in the view. The report lists the deadlock rule as `NoDeadlock`. If the spec already has an invariant or property with that name, the report uses TLC's config keyword `CHECK_DEADLOCK` for it instead.
- **Keep the state space finite.** TLC keeps exploring past a violation, so an unbounded model can run forever. Use small constants or a `CONSTRAINT`.

## The view module

You supply the human judgment through a JavaScript view module passed with the view flag. It decides what states and transitions are called, how states group into colored phases, and the diagram title. Every export is optional. Any other export is an error that lists the allowed names.

**`state(vars)`** gets one model state's variables and returns its label. The return type picks the layout:

- a string gives a flat diagram;
- an array of strings gives nested composite states, outermost first;
- an object gives concurrent regions, one per key, with each value as that region's label.

Values arrive as JavaScript: TLA+ sequences and tuples become objects keyed from 1, and sets become arrays. Labels name what the reader sees or cares about ("Cart has items", "Payment declined"), never variable names. Without a view, each state is labeled with its raw values.

**`step(action, from, to)`** gets TLC's action name and the variables before and after, and returns the transition label, or `null` to hide it.

- Phrase labels as events the user notices ("clicks Pay", "card is declined"), not code or action names.
- Give actions with the same visible effect the same label so they merge into one arrow.
- If the transition happens only under a condition, append it in square brackets in reader terms: "clicks Pay [card saved]".
- In a region layout, the tool already appends conditions that depend on sibling regions, using their labels. A hand-written bracket replaces that text and can make two arrows out of one state look identical, so do not bracket sibling-region conditions yourself there.
- If a value the labels hide decides where the transition goes, put the outcome into the label ("submits, order confirmed" versus "submits, out of stock").

**`group(vars)`** returns a phase name. A drawn state takes its phase's color. If the model states merged into one drawn state disagree on phase, it stays uncolored.

**`colors`** maps phase names to one of seven palette classes: `blue`, `orange`, `purple`, `yellow`, `teal`, `tan`, `pink`. It is an error to export `group` without `colors`, to use any other color, or to return a phase from `group` that `colors` does not list.

**`title`** is text shown above the diagram.

Results are cached: each model state reaches `state` and `group` no more than one time, each transition reaches `step` no more than one time, and the diagram and report share those cached answers. Write all three as pure functions of their arguments.

A minimal view for a checkout spec:

```js
export const title = "Checkout";
export const colors = { browsing: "blue", paying: "orange", done: "teal" };

export function state(v) {
	if (v.status === "cart") return v.items.length ? "Cart has items" : "Cart empty";
	if (v.status === "paying") return "Waiting for payment";
	return v.paid ? "Order confirmed" : "Order failed";
}

export function group(v) {
	return v.status === "cart" ? "browsing" : v.status === "paying" ? "paying" : "done";
}

export function step(action, from, to) {
	switch (action) {
		case "AddItem": return "adds an item";
		case "Pay": return "clicks Pay";
		case "Settle": return to.paid ? "card is charged" : "card is declined";
		case "Done": return null;
		default: return action;
	}
}
```

## Keeping the diagram readable

A transition whose source and target have the same label is not drawn. If the reader needs to see it, split the label.

Aim for about twenty arrows or fewer.

1. First make `state` coarser. Give the same label to values that behave the same, and drop details the reader can ignore (an outstanding request whose reply changes nothing). Never coarsen away a state on a violation path or a marked state. Do not merge so that a state where every model state violates a rule becomes one where only some do, and do not merge states that violate different rules. Either change hides where a rule fails.
2. If it is still crowded, return `null` from `step` for transitions the reader can do without: a reset reachable from everywhere, or an arrow that repeats information already shown. When you hide transitions:
   - every drawn state must stay reachable from an initial state along drawn arrows;
   - every drawn state that has an outgoing transition in the model keeps at least one outgoing arrow;
   - hide every transition behind an arrow, never only some, because hiding part of an arrow narrows its condition without saying so;
   - list what you hid in the hand-off.

## Reading the output

**Marks.** A drawn state where every merged model state violates a rule gets the `breaks` class. One where only some do gets `mayBreak`. States on a shortest violation path get `bugPath`, and states in the repeating cycle of a temporal counterexample get `repeats`. A legend shows one sample of each mark used. If two rules produce the same mark, the legend names both of them, and the hand-off then has to spell out the rule each marked state violates. For a diagram divided into regions, a state inside a region gets a mark if each combination containing it is able to break a rule. When some violating combination ends up with none of its members marked, every member of that combination receives the mark.

**After the violation.** TLC keeps going past a violating state, so the diagram also shows what happens after the defect.

**VIEW and SYMMETRY.** These make TLC collapse equivalent states into one representative, so an arrow may point at the representative instead of the literal next state. The report says when this applies.

**CONSTRAINT and ACTION_CONSTRAINT.** TLC evaluates rules in states past the boundary but does not expand them or check them for deadlock. If a rule's shortest violation ends in a state past the boundary, or on a transition an ACTION_CONSTRAINT excludes, the diagram includes it and the report shows the path. Other states past the boundary are left out, and deadlocks there cannot appear.

**Several violations.** The first TLC run uses the config unchanged with one worker. Each time a rule is violated, the tool removes it from the config and runs TLC again, until nothing is violated. Runs after the first violation are cut off once they reach 100,000 distinct states, which keeps big models from running indefinitely. Rules left unchecked because a run hit that limit or errored appear in a "not checked" section with no marks; they could go either way. To check them, remove the already-violated rules from the config or shrink the model. The limit is implemented with a helper module that changes TLC's variable order, so a temporal property's counterexample can differ from what an unlimited run would print.

**Raw logs.** `tlc.out` is TLC's output for the unmodified config. When the diagram cannot show a violated rule's path, `tlc-<RULE>.out` holds the log of the run that found it. With the JVM's parallel GC option set, stock TLC can print its first warning twice; the tool's copy has it once. Without that option, TLC's first warning is a single suggestion to turn it on.

**Size cap.** A diagram may hold up to 500 states, using the count TLC reports when run against the original config. Above the cap the diagram shows only the violation paths, and with no violations no `chart.mmd` is written. Every rule is still checked, and the report still gives the state count and every path. Shrink the model to see everything.

## Presenting the result

Show the contents of `chart.mmd` in a `mermaid` code fence. If the user wants an image, or the Mermaid text is too large to read, render it as described in [references/render.md](references/render.md). Use a different renderer only if the user asks.

The hand-off contains:

- each diagram and its Mermaid source;
- for every violation, one line with the rule, what it means in plain words, and its path using the report's step numbers;
- what the model leaves out;
- any transitions you hid;
- the exact command that regenerates the output into a new folder.

When the model stands for real code, replay every violation path against that code, by writing a test or by reproducing it live, with each action mapped to one code step. If a path does not reproduce, assume the model is wrong until shown otherwise, and say so.

## Done when

The tool exits 0 or 1 and writes its output folder; the diagram has about twenty arrows or fewer without losing violation-path states or marks; and, when the model represents code, every violation was replayed against that code.
