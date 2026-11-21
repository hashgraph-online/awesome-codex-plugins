---
name: explain-diff
description: "Use when the user asks to explain, understand, or describe a code change: a branch, pull request, commit, diff, or patch, such as 'explain what branch X does' or 'what does this PR change', even when bro is also active or the diff is pasted inline. Also use it when the user did not understand a reply or a concept, or asks to explain it better or to give a real example; at the end of planned work, after its checks and review; and to write or update a pull request description."
argument-hint: "[--visual] [scope]"
user-invocable: true
allowed-tools: Glob, Grep, Read, Bash, Write, AskUserQuestion, Artifact, Skill
---

# Explain diff

People often no longer read the code that agents write.
This explanation is how a person learns what was built, how it works, and why, well enough to own it.
Write for someone who knows nothing about the project or the task: first invoke `development-skills:bro` for this output.

## Gather the facts

Use the scope the user names: a branch, range, pull request, commit, or patch. Default to the work just finished.
Read the request, the plan and chronicle, the final diff, the check results, and the review verdict.
Check the behavior you describe in the code, and in real data and logs when they settle a claim.
Call a claim you could not check unchecked, and say what is missing.
Change no repository file.

## Write the explanation

Write these parts in this order, and skip a part that has nothing to say:

1. **What changed:** the result for the people or systems that use it compared with before, and the problem it solves, in two or three sentences.
2. **Concepts:** each functional, business, or technical idea the solution rests on, such as an idempotency key or a dead-letter queue. Explain it in plain words, then say where this change uses it.
3. **Flow:** follow one real case from input to result, with real values from the data, tests, or logs. Show what is read, stored, sent, or shown at each step.
4. **Edge cases and errors:** what happens with missing or duplicate data, a timeout, or a failing dependency, and what a user or operator sees.
5. **Choices and limits:** the alternatives the work rejected and why, the trade-offs, and what stays unchecked.

Explain each term the first time it appears, including common technical ones such as hash, lock, or transaction.
Use the names a person sees or operates: endpoints, tables, queues, settings, screens, log messages.
Leave out internal files, functions, classes, variables, and code settings unless the user asks for them.
Draw a small text diagram when the flow branches.
For planned work, keep it to about one screen. For a small change, write a few lines.
At the end of planned work, give the explanation and the questions in their own message, before the next step such as `align-docs`.

## Explain a reply or a concept

When the user did not understand a reply or a concept, explain that point only.
Use the parts that fit and a real case from this project.
Keep every fact of the earlier reply, and ask no understanding questions unless the user asks for them.

## Check understanding

After planned work, ask two or three questions about the most important concepts: behavior, flow, or a technical choice.
The explanation alone must be enough to answer them, without opening the code.
Ask them in one call to the question tool.
Each question is a concrete scenario with three plausible answers: one correct, and two that a reasonable person could believe.
Shuffle the three answers and mark none as recommended. Add a fourth option last, "I don't know, explain", in the user's language.
The free text field stays open for another answer.

- Good: "A client sends the same order again after a timeout. How many orders are in the database?"
- Bad: "Which function handles the retry?"

## Recap the answers

After the user answers, write a recap in chat. For each question, show the question, the user's answer, and "correct", "wrong", or "skipped".
"I don't know, explain" counts as skipped. For a wrong or skipped answer, explain the correct answer with a different example.
A wrong answer can mean two things: the user lacks a concept, or the user wanted the system to behave that way.
For each wrong answer, say which one the answer suggests, and why.
When the user wanted a different behavior, check whether the code or the requirement is wrong before you correct the user.

Then ask with the question tool how to continue, and wait for the answer before the next step:

- All answers correct: continue (recommended), more questions, or more explanation.
- Some answers wrong: review the work on those points, more questions or explanation, or continue. Recommend the option that matches what the wrong answers suggest.

To review the work, settle the new requirement with the user, then change the work, repeat its checks and review, and explain the changed part again.

## Visual mode

With `--visual`, or when the user asks for it, also build a page the user can step through: read [visual mode](references/visual-mode.md).
When the flow has states, ordering, or branches that are hard to follow in text, offer the page in one line.

## Pull request description

Use the same parts for a reviewer who knows nothing about the project or the task: read [pull request](references/pull-request.md).
