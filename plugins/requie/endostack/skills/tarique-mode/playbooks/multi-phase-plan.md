# Multi-phase plan

Your deliverable here is the plan; someone else writes the code. When work runs across several phases or a chain of stacked PRs, you produce an executable plan: a checklist that each owner ticks off one box at a time and that the operator can audit against recorded proof. Implementation is out of scope for this playbook.

[../scripts/PLAN-FORMAT.md](../scripts/PLAN-FORMAT.md) defines the exact headings, the fixed sentences, and every marker the checker searches for. This playbook explains the job each part does. If the two ever disagree, follow the format file and the checker, and correct this playbook in its own PR.

## Steps

1. **Decide whether a plan is warranted.** When the work touches one or two files and the approach is plain, tell the operator a plan is unnecessary and end there.
2. **Answer open questions with experiments.** Each open question gets its own [prototype.md](prototype.md) run. Hold on to the branch, SHA, and screenshots from every prototype, because the experiment-results appendix cites them. Reserve questions to the operator for product or taste calls that no experiment can answer, and offer concrete options when you ask (`principle-never-block-on-the-human`).
3. **Map the code with subagents.** Send out read-only subagents (`tarique-agent`, with the model chosen explicitly per the policy in [../SKILL.md](../SKILL.md) and effort and speed set to suit each job) to survey the codebase (`principle-guard-the-context-window`). Ask each one to come back with entry points, file pointers, the repo's conventions, and the commands that run its tests. Reject pasted file dumps.
4. **Threat-model the whole run.** When any PR in the run crosses a trust boundary, run the `threat-model` skill once across all of the PRs together. Every highly ranked threat goes to the PR that introduces its boundary, where it becomes one box under Changes and one box under a proof block. List each threat and its PR in the risk register appendix.
5. **Fill in every part of the skeleton.** Keep all headings and labelled blocks, in their order. Save the plan in a docs folder inside your agent store unless the operator gives another path. Give each PR its own section, and scope each PR to a single change that carries its own proof (`principle-sequence-verifiable-units`). The reading section names the execution playbook: [autopilot-full.md](autopilot-full.md) or [autopilot-stack.md](autopilot-stack.md), chosen by the selection rule in autopilot-stack, or [orchestrate.md](orchestrate.md) when the run is a standing program.
6. **Edit the prose.** Apply the `technical-writing` skill completely, and after it the `unslop` skill. Write the main body as instructions a reader follows. Put background and reference material in the appendices. Phrase each heading as a task or a finding. The checker fails long dashes and colons in the middle of a sentence, so leave both out.
7. **Run the plan checker** against the file and fix each line it flags (`principle-encode-lessons-in-structure`). PLAN-FORMAT.md gives the command.
8. **Hand the plan over and stop.** Post the plan's path along with the checker output. Nothing executes until the operator says go, and execution then follows the playbook that the plan names.

## The proof rule

PLAN-FORMAT.md defines a single fixed rule sentence that every plan carries. In substance it says green tests alone never prove a PR. Proof requires every box in the PR's unit, live, and perf blocks to be ticked (`principle-prove-it-works`). The sentence appears in the reading section, and each proof block begins with it. The checker compares it exactly, so paste it from the format file instead of retyping it.

**Every PR gets live proof.** Following the `swarm` skill and running on the `swarm-workers` role, ten lanes exercise the real surface at the PR head through that surface's control skill. A lane is a single checkbox that names a specific scenario, the screenshot file it produces, and the condition under which it passes.

**Lane 1 checks trunk for regressions.** It runs the scenario the change depends on most, once against trunk and once against the head. When trunk does not have the feature yet, the lane writes that down and instead tests the new behavior together with the final state the user is waiting to reach. Do not make up a trunk result.

**Security lanes.** When step 4 assigned a threat to a PR, one or more of its ten lanes carries out that attack against the live surface (a malicious input, a request without authorization, an instruction planted in fetched content). The lane passes when the mitigation stops it.

**Perf is measured on trunk and head.** The named metric has to be measurable on both. When trunk has no version of the feature, measure the added work by itself and give it an absolute budget, plus one for the end state the user sees. A ratio between two different scenarios is meaningless, so never report one. The perf block lists four things: the metric, an interleaved probe, a trunk baseline taken before the head run, and the budget that fails the PR.

**Operator review.** When a PR changes how a user interacts with the product, the operator reviews it in chat before it merges, using screenshots and a video. When a PR changes no interaction, its review block says so in one line and contains no boxes.

## Choosing control skills

Pick the control skill by surface. A UI control skill drives web pages, browser apps, and Electron apps. A CLI control skill drives command-line and terminal UIs. For native mobile, use the simulator skill the repo supplies. A PR that touches two surfaces runs lanes on each. If a surface has no control skill, record it as a risk in the risk register, and still describe in the live block how each lane will drive that surface.

## What the plan contains

This section describes the job of each part. PLAN-FORMAT.md holds the exact headings and markers.

### Title and intro

The H1, followed by fewer than ten lines that say what the program changes, which users it affects, which rule it holds every PR to, and the sequence of PR ids.

### Reading this plan

Lays out the conventions. Each box is one task, each box cites the proof that closes it, and boxes nested under another box are its sub-steps. Nobody ticks a box until its proof exists, and that proof can be a SHA, a test run, a saved file, a screenshot, or a quoted log line. Instructions belong in the main body, and background and records belong in the appendices. The section also gives the execution playbook's path, says who merges, and lists the PR ids that the operator owns, which halt at merge-ready. It includes the proof rule sentence.

### Run checklist

Five subsections, in the order below.

**Start the run.** Walk the operator through the protocol and the plan, then wait for an explicit go. Read these from trunk with `git show` at startup and again each tick, because a local checkout can be out of date: the execution playbook, the `swarm` skill, the control skill, [opening-a-pr.md](opening-a-pr.md), and any other leaf skill the run depends on. Once the go arrives, set up an hourly audit through the host's scheduled-task feature. Its tick prompt is fixed and written out in the plan, so nobody has to remember it. On each tick, the prompt:
- loads the execution playbook again from trunk;
- checks for drift and repairs it within the same tick;
- inspects each active lane and judges it only by what it has produced;
- shuts down any lane that is stuck and starts its replacement right away;
- sends a brief status message only when the audit turned up a tracked change that no earlier message covered, listing only those changes and leaving out tables, lists of merged PRs, and blockers that have not moved. Tracked changes are: a PR was opened, a head reached code-ready, a round started or finished, a verdict came in, a PR merged, an agent got stuck (and what was done about it), a blocker appeared or cleared, or a choice arose that is reserved for the operator;
- finishes the turn without any reply text if nothing changed;
- writes the tick's row to the decision trail every time, naming what it reported or "none".

When the run is put on hold or stood down, send every owner an order to stop all writes immediately.

**Assign owners.** Each PR gets one owner, who carries it through the whole lifecycle that the execution playbook describes. Spell out the dependency graph: which PRs have no dependencies and branch from main first, and which PR follows which. A dependent PR starts only once its parent has merged, or, when the playbook stacks PRs, it bases on the parent's branch. State the file boundaries for each PR or class of PR, and list the PRs that need operator review. Each owner's credentials cover only that owner's branches.

**Branch and PR rules** (apply to every PR).
- Pick the forge one time. The GitHub CLI is the default; use another forge when one is installed and can resolve the repo, write the fallback down, and do not depend on a stacking tool.
- Open each PR in the ready state, never as a draft, following [opening-a-pr.md](opening-a-pr.md). If the host ships its own PR tool, use that. Without one, run the forge's create command and set the base branch. A child in a stack targets its parent.
- Before the push that the PR will show, run lint and the type checker one time, then push with hooks turned on.
- Before each commit, run the slop-strip pass. Before code-ready, run `security-review`. Before review, run `no-comments`.
- Handle each comment from a bot or a security reviewer as described in [../references/review-bot-triage.md](../references/review-bot-triage.md).
- Rebase onto trunk before reporting code-ready and before babysitting starts, and keep that base through fix rounds. Rebase again only for merge prep, when `git merge-tree` shows a conflict with trunk, or when CI fails because of a change on trunk.

**Verification and landing** (apply to every PR).
- Run one full swarm once the head reaches code-ready. Repeat it only when the PR gains new behavior, gets redesigned, or grows by a large new diff. After a rebase, a conflict fix, or a small change, one verifier at the new head is enough.
- Following the `swarm` skill, a full swarm contains a gates lane, the ten live lanes, a perf lane, and at least two audit lanes. Each audit lane has its own focus, reads the diff and the receipts, and does not trust the PR description. When a PR carries assigned threats, one of its audit lanes is a security audit.
- Before giving a verdict, the root reviews the receipts attached to the owner's merge-ready report. A verdict is clean only if all lanes passed.
- Send every finding back to the owner, even a defect that a lane recorded only as a note.
- Each new head needs its own verdict, unless the patch-identity rule in [shipping.md](shipping.md) lets earlier results carry over. After that, follow the execution playbook's rule for merging or appending.

**Lane setup** (apply to every live lane).
- Every lane gets its own remote machine running the PR head. When the host offers no remote machines, give each lane an isolated local environment and add that to the risk register.
- Fetch the head branch, then check out the head SHA.
- Bring up the backend and the surface and wait for both to report ready.
- Send all input through the control skill. List which read-only diagnostics the lane is allowed to use.
- Store each screenshot in a temp directory scoped to the PR and the worker, and return the file paths.
- Give lanes test credentials only. Production secrets never reach a lane.

### One section per PR

Title each section with a verb phrase followed by the PR id. It holds nine bold labelled blocks, in this order:

1. **Needs.** The PR ids this one depends on, or none.
2. **Touches.** A checkbox per file the PR edits, creates, or deletes.
3. **Changes.** A box per change, each naming the symbol and its file. Mitigations for threats assigned in step 4 go here.
4. **Observable result.** A box per result someone can observe, quoting the precise log line or screen state.
5. **Unit proof.** The rule sentence, then the test file, the test case, and the command that runs it.
6. **Live proof.** The rule sentence and the ten-lanes line with a real model filled in, then lanes 1 to 10. Every lane names what it exercises, which screenshot file it writes, and the condition it must meet to pass. Lane 1 is the trunk regression lane.
7. **Perf proof.** The rule sentence, then four boxes in order: metric, probe, baseline, budget.
8. **Operator review.** Either the one-line statement that the PR needs no review, with no boxes, or boxes that copy the lane screenshots to a media path, capture a video of 30 to 60 seconds on a lane machine, post both in chat, and then halt at merge-ready until the operator responds.
9. **Landing.** A clean verdict from the root at the exact head SHA, bot triage finished, and a rebase onto trunk after the verdict that leaves patch identity unchanged. Then either the owner squash-merges, or the root appends the PR to the stack and the operator lands the stack from the bottom up.

### Finish the run

Confirm that each box is ticked and its proof is recorded, then send the operator the closing report that the execution playbook specifies.

### Appendices, in order

- **A. Experiment results.** For each question a prototype settled, the branch, the SHA, and links to its artifacts. Also every question that is still unproven.
- **B. Options considered and dropped**, with the reason each one lost.
- **C. Risk register.** Every risk, the PR that carries it, and what that PR's owner should keep an eye on. Threats from step 4 and their PRs are listed here, along with any surface that has no control skill.
- **D. Sources and pre-reading.** The material an editor should study first, the PRs that receive `how` and `interrogate`, and the decision trail kept per `show-me-your-work`.

## Subagents

You spawn two kinds here: read-only explorers that come back with pointers, and one prototype run for each open question. The plan describes the owners and swarm lanes, but this playbook does not spawn them.

## Reply

Give the plan's path; the PR ids and how they depend on each other; which PRs need operator review; the threats and which PR carries each one; what the prototypes established and what is still unproven; and the checker output, pasted exactly as printed.
