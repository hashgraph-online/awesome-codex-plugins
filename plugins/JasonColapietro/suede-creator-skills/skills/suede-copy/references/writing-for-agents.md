# Suede Agent-Doc Method

Read this when the document's reader is a model: a `SKILL.md`, a `CLAUDE.md`,
an `AGENTS.md`, or a reference file a skill points to. Human copy competes for
attention. Agent docs spend it: every always-loaded line costs tokens on every
turn, used or not. The target is a repeatable route through the document, so
run 12 behaves like run 1.

## 1. Trigger lines

A trigger line is any text resident in the agent's context that names material
outside it and says when to go get it. A skill `description` is one. So is an
`AGENTS.md` line that names a doc.

The wording of the trigger line, more than the material behind it, decides
whether the agent reaches that material. Must-reach content behind a vague
trigger gets found on some runs and missed on others. Sharpen the trigger
before you inline the content.

A good trigger line does two jobs: names what the material is, and lists each
distinct case that should fire it.

| Problem | Repair |
|---|---|
| The deciding word sits mid-sentence | Move it to the front |
| Two phrases name the same case | Keep one |
| The trigger repeats what the body already says about itself | Cut it from the trigger |

Weak: "Can be used for a variety of documentation tasks."
Strong: "Use when authoring a skill, fixing a trigger that misfires, or
splitting a long agent doc."

## 2. Two budgets

Every addition spends one of two budgets. Name which before you add it.

- **Resident cost:** tokens loaded every turn (descriptions, `AGENTS.md`
  lines, anything always in context).
- **Recall cost:** what the human must remember (which docs exist, when to
  reach for each).

Recall cost is not waste. It is where human judgment lives. Spend it where a
person should decide; remove it where nobody needs to.

## 3. Three shelves

Each piece of a document sits on one of three shelves:

1. **Steps in the file:** what the agent does, in order.
2. **Reference in the file:** facts consulted on demand. A flat list of peers
   is fine here.
3. **Reference behind a pointer:** a separate file loaded only when the trigger
   fires.

The branching test decides the shelf: keep in the file what every path needs;
move out what only some paths use. Keep a concept's definition, rules, and
exceptions under one heading so reading one part brings the rest.

Suede thresholds: reference over about 100 lines moves to `references/` with a
contents list; under about 50 stays inline; in between, stay inline unless it
pushes `SKILL.md` past 500 lines. A document can be too long even when every
line is live. The fix is moving reference down a shelf, not trimming words.

## 4. Done tests

Every step ends on a test the agent can check.

**Make it checkable.** "Once the code is understood" lets the agent stop early
because the next step is already pulling at it. "Every exported function has a
one-line note naming its callers" does not. Sharpen the test first. Split the
sequence across a real handoff (a subagent or a new session) only when the test
cannot be sharpened and you have watched the agent rush it. An inline call does
not hide later steps; they are still in context.

**Make it demanding.** "Every modified model accounted for" drives the digging
that "list the changes" never triggers. A rule list works the same way:
"every rule applied" binds as hard as "every step done".

## 5. When to split a document

A split spends a budget, so it has to pay for itself.

- **Split a sequence** when later steps tempt the agent to rush the current
  one. Merging two sequences invites the same rush.
- **Split off a new skill** when a distinct phrase should fire it on its own,
  or another skill must reach it. The price is one more resident description.

## 6. Anchor words

An anchor word is a short concept the model already knows that it can think
with while it works: *tight*, *red*, *tracer*, *ledger*. Repeat the word; do
not keep re-explaining it. Each repetition pulls the same behavior.

- "fast, deterministic, low overhead" → a *tight* loop
- "a check you actually trust" → the test goes *red* on the bug, or it does not

A coined word works only after you define it, and you pay for that definition
in tokens. A familiar word arrives with its meaning already loaded. When the
same word appears in prompts, docs, and code, it also helps the agent connect
a request to the right material.

## 7. Write the target, not the ban

Telling a model what not to do puts the unwanted behavior into context. State
the behavior you want.

Weak: "Don't write long rambling comments."
Strong: "Write one-line comments."

Keep a prohibition only for a hard guardrail with no positive phrasing, and
put the positive target next to it.

## 8. Pruning

- **One meaning, one place.** Duplicates cost tokens, drift apart, and make a
  minor rule look major.
- **Let the environment speak.** `package.json`, config, directory layout, and
  `--help` already answer many questions. Restate them only when the lookup is
  expensive. Write down what no file reveals: the unwritten convention, the
  reason for a choice, the trap.
- **Clear stale layers.** Lines that no longer bear on the task pile up because
  adding feels safe and deleting feels risky. Delete them.
- **Cut sentences the model already obeys.** Test each line against the
  model's default behavior. If removing it changes nothing, remove the whole
  sentence. A weak instruction ("be thorough") fails this test too; replace it
  with a stronger, more specific demand.

## 9. Who can fire the skill

| | Model-invoked | User-invoked only |
|---|---|---|
| Claude Code frontmatter | no `disable-model-invocation` | `disable-model-invocation: true` |
| Codex `agents/openai.yaml` | `allow_implicit_invocation: true` | `allow_implicit_invocation: false` |
| `description` | written for the model, lists trigger cases | a one-line label for humans |
| Resident cost | every turn | none |
| Recall cost | none | the human must remember it |

Model-invoked skills stay reachable by name, too. Choose user-invoked when a
skill should only ever run on request (a code grade, a destructive cleanup).
Shared reference that two user-invoked skills both need belongs in a plain
file outside either skill, because neither can fire the other. When
user-invoked skills grow past what a person can remember, add a router skill
that names them and when to use each.

## Deliverable

Return the revised document, then counts: trigger lines sharpened, duplicate
cases merged, done tests sharpened, restatements collapsed into anchor words,
no-op sentences cut. Then the Ship Gate score.
