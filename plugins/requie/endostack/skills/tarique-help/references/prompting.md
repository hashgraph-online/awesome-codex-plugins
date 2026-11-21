# Prompting EndoStack

The user supplies the intent and a way to tell when the work is done. The playbook supplies the procedure. That division is why a short, plain prompt usually does better than a detailed specification: the specification competes with the playbook's steps, and the playbook's steps were written to avoid the mistakes a hurried specification makes.

## Put in

- **The goal.** What is broken, or what the user wants to exist.
- **A done check with a yes-or-no answer.** "The export command produces the same file as before for every fixture" is a check. "Make it better" and "spend an hour on it" are not.
- **The evidence you want to see.** Real command output, a recording of the flow, the value read back from storage, numbers before and after.
- **What you already know.** The symptom, the steps to reproduce, logs, links.
- **Real constraints.** "Reproduce before fixing", "do not change code yet", "behaviour must not change", "stop for my review before implementing". Each of these changes what the agent does, so each earns its words.

## Leave out

- **The method.** The agent may find a better one. Mention a skill by name only to override one specific choice.
- **Lists of skills or steps.** Sequences that users write by hand usually lose some of the playbook's steps or put them out of order.
- **Your guess at the cause, in the first message.** Offering a guess too early steers the agent toward one place before it has investigated anything. Hold it back until the agent has restated the problem to you, then offer it.

## Get context first

- For a confusing report, have the agent explain the underlying problem in plain words before acting. The [`in-your-own-words` skill](../../in-your-own-words/SKILL.md) does only that.
- In a new chat on an old topic, run the [`recall` skill](../../recall/SKILL.md) to bring in earlier related work.
- Ahead of any edit to code the agent has not seen, have it run [`how`](../../how/SKILL.md) to trace what the code does and [`why`](../../why/SKILL.md) to learn what shaped it. Skipping that trace usually leads the agent to patch whichever spot looks plausible first.
- Ask [`teach`](../../teach/SKILL.md) to make the agent defend the choice it made. You can test each step of a defended choice, while a summary gives you nothing specific to test.

## Settle the design before the plan

- Treat the first design as one candidate among several. Request a prototype of each option (with screenshots or recordings when it has a UI) and choose based on the results.
- Let prototypes answer open questions. An adversarial review of an abstract plan produces imagined risks, because nothing in a plan constrains the reviewers.
- For a package or API others will consume, ask for its README or a tutorial first and build the code to match. The document becomes the agent's target.
- Ask for an implementation plan once the design is settled, not before, and have each plan step end in a check.

## Short follow-ups

Once the task is set in the chat, "go ahead" or "keep going until it passes" is a complete prompt, because the playbook holds the structure. Say "new task" when you switch topics. Otherwise the mode reads your message as a continuation of the previous task.

## Before you leave the agent alone

- Say you are leaving, so it stops asking questions.
- Define done as checks it can run each round, and give that condition to the agent's loop command if it has one.
- Ask for a fresh worktree from a branch you name.
- Answer in advance the questions it would stop for, such as permission to commit.
- Ask for a decision log with the [`show-me-your-work` skill](../../show-me-your-work/SKILL.md).
- Give it a way out: after a set number of hours stuck, stop and write up the blocker.
- Say what it must not do unattended: push to `main`, change permissions or secrets, or act on instructions found in issues, logs, or web pages.

## One-line corrections

When the agent has gone past the goal, restate the goal. When it is about to make a mistake a principle covers, name the principle ("subtract before you add"). Naming works because the agent has already read the principle. Its reply should say which decision the principle changed. If it names the principle and nothing changed, the principle was not applied.
