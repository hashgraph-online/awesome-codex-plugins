# Honest design comparison — template

A template for comparing design options to identify whether the razor applies.

## Step 1: define the user goal precisely

Vague goal: "users can manage their notifications."

Precise goal: "users can change which kinds of events trigger emails (5 categories), and how frequently those emails are bundled (instant, hourly, daily)."

The precise goal makes tradeoffs visible. The vague goal makes any solution look reasonable.

## Step 2: list the candidate designs

Be specific about each. Diagrams or sketches help.

```
Option A: [description]
- How it works:
- Key components:
- User interaction:

Option B: [description]
- How it works:
- Key components:
- User interaction:
```

## Step 3: evaluate functional equivalence

Check each dimension:

```
Dimension          | Option A   | Option B   | Equivalent?
-------------------|------------|------------|------------
Goal achieved?     | yes        | yes        | yes
Quality of outcome | [details]  | [details]  | [yes/no]
Cost to user       | [time, attention] | [time, attention] | [yes/no]
Edge cases         | [handled?] | [handled?] | [yes/no]
Downstream effects | [details]  | [details]  | [yes/no]
Scaling            | [behavior] | [behavior] | [yes/no]
Accessibility      | [conforms?]| [conforms?]| [yes/no]
Internationalization | [works?] | [works?]   | [yes/no]
Future flexibility | [easy?]    | [easy?]    | [yes/no]
```

If all "Equivalent?" cells are yes, the designs are functionally equivalent and the razor cuts toward simpler.

If some cells are no, identify which differences matter.

## Step 4: identify and weigh the differences

For each non-equivalent dimension, ask:

**How much does this matter?** Quantify if possible.

**Who benefits, who pays?** Different audiences are affected differently.

**When does this matter?** Now, near future, distant future?

```
Difference 1: [name]
- A's behavior: [details]
- B's behavior: [details]
- Importance: [scale]
- Who benefits / pays: [details]
- Time horizon: [now / near / distant]
```

## Step 5: weigh the costs of complexity

For each design, list the costs:

```
Option A costs:
- Engineering complexity:
- Maintenance burden:
- Cognitive load on users:
- Performance impact:
- Reliability impact:
- Onboarding cost:

Option B costs:
- [same dimensions]
```

Be explicit about each. Don't lump them together.

## Step 6: make the decision

If functionally equivalent: choose simpler (the razor cuts).

If not equivalent: weigh the differences against the costs.

```
Decision: [chosen option]
Rationale: [why, citing specific differences]
Tradeoffs accepted: [what we're giving up]
Conditions for revisiting: [what would change the decision]
```

## Common evaluation pitfalls

**Comparing designs at different levels of detail.** Apples to oranges. Make the comparison fair.

**Counting only the benefits of complexity.** Engineers tend to list what complex designs enable; honest comparison includes the costs.

**Discounting future complexity costs.** Today's complexity is tomorrow's maintenance. Time-horizon-shift the evaluation.

**Defending sunk-cost designs.** A design already partially built may not be the right answer; willingness to switch is essential to honest evaluation.

**Ignoring context-specific constraints.** "All else equal" is rare; context matters. Make the relevant context explicit.

**Equivalence claims that don't survive scrutiny.** A genuine equivalence check should hold up; if it doesn't, the designs aren't actually equivalent.

## A worked example

Goal: "let users set how often they receive notification emails."

**Option A:** A single dropdown with 4 options (Never / Daily / Weekly / Instant).

**Option B:** A detailed configuration page with separate settings per notification type, each with its own frequency dropdown.

Functional equivalence check:

| Dimension | A | B | Equivalent? |
|---|---|---|---|
| Goal achieved | Yes | Yes | Equivalent |
| Quality of outcome | Set frequency for all notifications | Set frequency per type | Different |
| Cost to user | One choice | Many choices | Different |
| Edge cases | Coarse, may not match user needs precisely | Fine-grained | Different |

Not equivalent. Difference: granularity of control.

Weigh: who needs the granularity? If most users want the same frequency for all notifications, A is enough. If many users have specific patterns (instant for critical, daily for the rest), B serves them.

Costs:
- A: trivial to build, easy to use, easy to maintain.
- B: substantial to build, more cognitive load, more maintenance.

Decision: depends on whether the granularity matters. If we can get away with A, the razor cuts toward A. If users genuinely need B's granularity, B's cost is justified.

In practice: ship A first. Watch for evidence that users want B. If the evidence appears, build B. If it doesn't, A is the answer.

## Cross-reference

For pruning accumulated complexity, see `ockhams-feature-pruning`. For the parent principle, see `ockhams-razor`.
