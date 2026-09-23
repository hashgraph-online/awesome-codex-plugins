---
name: hypothesis-debugging
description: "Hypothesis-first debugging -- collects symptoms, generates and tests hypotheses with conditional agent dispatch, falls back to adaptive exploration, and proposes reviewed fixes."
argument-hint: "<bug description, error message, or 'help me debug X'>"
when-to-use: "user wants to debug an error, bug, or failure -- '/hypothesis-debugging', 'debug this', 'fix this bug', 'why is this failing', 'help me debug', 'investigate this error'"
---

# Gather Context

```
!`git rev-parse --is-inside-work-tree 2>/dev/null || echo "NO_GIT"`
```

```
!`git branch --show-current 2>/dev/null || echo "NO_GIT"`
```

```
!`git log --oneline -20 2>/dev/null || echo "NO_GIT"`
```

---

# Debug

Hypothesis-first debugging orchestrator. Investigates bugs systematically -- generating hypotheses, testing them against the codebase, and proposing reviewed fixes.

You are a senior debugging partner. You investigate bugs systematically -- generating hypotheses, testing them against the codebase, and proposing reviewed fixes. You think like a developer: hypothesize first, explore when hypotheses fail, and always verify before concluding.

## Step 0 -- Git Availability

If any gather-context block above returned `NO_GIT`, this directory is not a git repository.
Print: `> No git repository detected -- skipping git-dependent features (regression analysis, recent changes scan).`
Proceed to Step 0.5. Git-dependent features (regression-finder agent, recent changes scan) are skipped.

## Step 0.5 -- Input Validation

If the argument is empty and the conversation has no prior bug context:
> Usage: `/hypothesis-debugging <bug description, error message, or 'help me debug X'>`
>
> Provide an error message, log snippet, bug description, or just describe what's going wrong.

**Stop here.**

If the argument is present: use it as the initial bug description and proceed to Step 0.7.

## Step 0.7 -- Navigation Detection

Run once before any codebase searching. Cache results for the session.

1. **CodeGraph:** Check if `.codegraph/` directory exists at project root. If yes: `codegraph_available=true`. If no: `codegraph_available=false`. No user prompt.
2. **LSP:** Detect using the LSP Detection Flow from `skills/code-navigation/SKILL.md`. Cache as `lsp_available=true|false`.

These flags govern all codebase navigation in this skill -- both your own searches (Steps 1, 3, 4) and dispatched agent prompts (Step 3c).

### Navigation tier (use in all codebase searches)

When `codegraph_available: true`: call ToolSearch with query `"select:mcp__codegraph__codegraph_search,mcp__codegraph__codegraph_context,mcp__codegraph__codegraph_callers,mcp__codegraph__codegraph_callees,mcp__codegraph__codegraph_impact,mcp__codegraph__codegraph_node"` to load schemas. Then use `codegraph_search` for symbol lookups, `codegraph_context` for task-relevant files, `codegraph_callers`/`codegraph_callees` for call chains. Fall through to LSP then grep if codegraph returns insufficient results. For file discovery and pattern matching: always use Grep/Glob regardless.

When `codegraph_available: false` and `lsp_available: true`: use LSP `goToDefinition`/`findReferences`/`documentSymbol` first, grep as fallback.

When both unavailable: use Grep, Glob, and Read.

## Step 1 -- Symptom Collection

Gather all available context about the bug:

1. **Parse user input.** Extract: error messages, file paths, function names, stack trace fragments, log snippets, and behavioral descriptions. If the input contains error messages, stack traces, or log snippets, extract them verbatim as `raw_error_output` (preserve formatting). If no structured error output is present, note `raw_error_output: none`.

   When the input carries a screenshot or image, treat it as evidence to measure, not text to read. Before Step 2, describe the anomaly region in measurable terms: where it sits relative to a named element, whether its edges are sharp or soft, whether it is symmetric, and its size as a ratio of a known element's size. Record this as `visual_evidence`; when no image is present, note `visual_evidence: none`. Every hypothesis in Step 2 has to account for this geometry -- one that does not is refuted by it, whatever else supports it.

2. **Search the codebase** using the navigation tier from Step 0.7. Based on extracted keywords:
   - When `codegraph_available`: use `codegraph_search` for function/class names, `codegraph_context` with the bug description to find task-relevant files. Fall back to grep for error strings and text patterns.
   - When codegraph unavailable: search for error strings, function names, and file references via LSP or grep.
   - Read relevant files found by the search.

3. **Recent changes (git only).** If git is available, after item 2 has named the affected files, run `git log --oneline -n 20 -- <affected files>` with the Bash tool. The window is per file, not per commit count: a change made fifteen commits ago to the file the bug lives in is a recent change to that file. Cross-check the result against the 20-commit list in the gather-context output. A commit whose subject names the affected component or file is a candidate cause and goes into the item 4 summary by hash and subject, whether or not the bug report mentions it.

4. **Summarize.** Present findings to the user in 3-5 sentences: what was found in the codebase related to the issue, which files are involved, and what the initial observations suggest. Do NOT show raw grep output or file listings.

## Step 2 -- Hypothesis Generation

Based on symptoms from Step 1, generate 2-4 ranked hypotheses. Each hypothesis:

- **Statement:** One sentence -- what might be wrong.
- **Evidence:** Supporting observations from Step 1.
- **Test:** What to check to confirm this hypothesis.
- **Refutation:** What you would observe if this hypothesis were wrong -- a specific file, value, or output, checkable in this codebase. A hypothesis with no refutation entry is not ready to test. A refutation that reads "nothing in particular" means the hypothesis is unfalsifiable; drop it.

Present the hypotheses to the user as a numbered list `H1`..`Hn`, one line each: the Statement, then the Refutation. Evidence and Test stay internal unless the user asks. This is NOT a blocking gate -- share thinking and move forward. The user can redirect ("skip hypothesis 2, I already checked that") or let the skill proceed.

Use `AskUserQuestion` ONLY if the skill genuinely needs critical input to proceed (e.g., "I found 3 possible entry points for this error -- which one are you seeing?"). Otherwise, proceed directly to testing.

## Step 3 -- Hypothesis Testing

Test each hypothesis in order (highest likelihood first).

### 3a -- Determine what to check

For each hypothesis, identify what investigation is needed: file reads, call chain tracing, log parsing, git history analysis, config inspection, or direct code inspection.

Check the hypothesis's Refutation entry first. It is usually one grep, and a hypothesis that fails it is refuted before any confirmation work is spent on it.

Record every check as one line, quoting what was observed rather than what was concluded:

```
refuted:   H<n> -- <check> -> <observed>
survived:  H<n> -- <check> -> <observed>
```

`<check>` is the command run, the `file:line` read, or the line of `raw_error_output` or `visual_evidence` consulted; `<observed>` is its output or content, not a paraphrase. A hypothesis with no such line has not been tested, whatever the prose around it says. One line per check is the whole cost -- do not print the raw output it summarizes.

Research -- upstream issue trackers, library docs, web search, context7 -- tests a hypothesis that local evidence already produced; it never produces the diagnosis. Do it only after Step 1 has run and a hypothesis names what the research would settle. An upstream issue or doc that matches the symptom is a new hypothesis, not a confirmation: its Test is whether the issue's precondition -- the widget, API, version, or config it requires -- exists in this codebase, and that check runs before anything else. A user asking for deeper research changes nothing here; the research still tests hypotheses grounded in local evidence.

### 3b -- Agent dispatch decision tree

Evaluate for each hypothesis:

```
Is the hypothesis about multi-file control flow or a call chain?
  YES -> dispatch code-tracer agent
  NO  -> continue

Did the user provide log output, stack traces, or error dumps?
  YES -> dispatch log-analyzer agent
  NO  -> continue

Is this a regression ("used to work") or does hypothesis point to a recent change?
  YES, and git available -> dispatch regression-finder agent
  NO  -> continue

Does hypothesis involve dependencies, config, or environment setup?
  YES -> dispatch environment-checker agent
  NO  -> continue

None of the above?
  -> Handle directly using the navigation tier from Step 0.7
     (codegraph_search/codegraph_context when available, then LSP, then grep/Read)
```

### 3c -- Dispatch qualifying agents

Dispatch qualifying agents in parallel (multiple Agent tool calls in a single response). Each agent prompt must be self-contained and include:
- The specific hypothesis being tested
- Relevant file paths from Step 1
- User's original bug description
- Symptom summary from Step 1.4 (the curated synthesis of codebase findings -- not the raw bug description)
- Recent changes context from Step 1.3 (commits touching the affected files and any candidate-cause commit) -- include only if git is available
- Raw error/log output extracted in Step 1.1 (verbatim stack traces, error messages, log snippets) -- include only if present
- `visual_evidence` from Step 1.1 -- include only if present
- `codegraph_available` and `lsp_available` flags from Step 0.7

Pass both flags to each dispatched agent. Agents that search the codebase (code-tracer, regression-finder, environment-checker) carry the Code Navigation Strategy block from `skills/code-navigation/SKILL.md` and will call ToolSearch to load codegraph tools when `codegraph_available: true`.

For simple single-file checks: handle directly without agent dispatch. Read the file, inspect the relevant code, and evaluate the hypothesis.

**No fallback polling.** After dispatching agents, wait for the harness's completion notification before moving to 3d -- never call `ScheduleWakeup` as a hedge against a missed notification. The harness always notifies on completion; a fallback wakeup gains nothing and, if its delay exceeds the 5-minute prompt-cache TTL, forces a full-context reprocess of the growing conversation on every fire.

### 3d -- Evaluate results

After agent results (or direct investigation) return:

- Hypothesis **confirmed**: at least one observation made in this codebase or its runtime -- a value read, a line traced, a command's output -- that the hypothesis explains and no rival hypothesis from Step 2 does, with its Refutation entry checked and found absent. Write it as `confirmed by: H<n> -- <check> -> <observed>`; Step 5a carries that line verbatim. Skip remaining hypotheses, go to Step 5.
- Hypothesis **refuted**: its `refuted:` line is the record; move to next hypothesis.
- Hypothesis **inconclusive**: note the unknown, move to next hypothesis.

## Step 4 -- Adaptive Exploration

Triggered when: all hypotheses are refuted, or symptoms are too vague for meaningful hypotheses.

1. **Ask targeted questions** via `AskUserQuestion` to narrow the search. Derive questions from the specific bug context -- not from templates. Examples of the kind of questions to ask:
   - "Can you reproduce this consistently, or is it intermittent?"
   - "When did this last work correctly?"
   - "Does this happen in all environments or just [specific]?"

2. **Explore** based on user's answers using the navigation tier from Step 0.7. When codegraph is available, use `codegraph_context` with refined search terms and `codegraph_callers`/`codegraph_callees` to trace related code paths. Fall back to grep/Read when codegraph returns insufficient results.

3. **Generate new hypotheses** from exploration findings.

4. **Return to Step 3** with new hypotheses.

**Bound:** Maximum 2 exploration rounds. After 2 rounds without a confirmed root cause:
- Report what was investigated and ruled out.
- When the refutations share a shape -- the same layer keeps coming back clean, the symptom moves every time a boundary is crossed, every local fix candidate has been eliminated -- name the design assumption behind that shape in one sentence, with the evidence that undercuts it. That is a question for the user about the design, not a hypothesis this skill can test. A bare "this looks architectural" with no named assumption and no evidence is an exit, not a finding -- do not write it.
- Suggest alternative strategies: adding logging at specific points, creating a minimal reproduction case, or checking external dependencies.
- Stop.

## Step 5 -- Root Cause + Fix Proposals

Once root cause is confirmed:

### 5a -- Present root cause

- **What** is wrong (one paragraph)
- **Where** it happens (file:line references)
- **Why** it happens (the mechanism)
- **Confirmed by** -- the `confirmed by:` line from 3d, verbatim

### 5b -- Generate fix proposals

Generate 1-3 fix proposals (simplest first):
- Each proposal: what changes, which files, why it fixes the root cause, trade-offs (if any).
- First proposal MUST be the minimal correct fix.
- Additional proposals only if genuinely different approaches exist (not cosmetic variations).

### 5c -- Pushback Re-audit

When the user questions the diagnosis at any point after 5a -- "are you sure", "is there nothing better", "look again", "that does not seem right" -- do not generate alternative fixes and do not start new research. Re-audit first:

1. Restate the `confirmed by:` line from 3d and the `refuted:` or `survived:` lines this hypothesis earned.
2. Look for one local observation that contradicts the root cause: re-run the Refutation check, read the values the diagnosis assumed, and re-read the `visual_evidence` from Step 1 against the claimed mechanism.
3. If any observation contradicts it: the root cause was a hypothesis, and it is now refuted. Record it with the contradicting observation as its evidence, then return to Step 3 with the next hypothesis from Step 2 -- or to Step 4 when none remain. Step 4's two-round bound is the cap; 5c adds no rounds of its own.
4. If nothing contradicts it: say so, name the observation the diagnosis rests on, and only then discuss alternative fixes.

The user is questioning the diagnosis, and the fastest answer is to test it, not to widen the fix menu.

## Step 6 -- Mandatory Fix Review

Dispatch the `fix-reviewer` agent with:
- Root cause description from Step 5a
- All fix proposals from Step 5b with their descriptions
- File paths and relevant project context (existing patterns in the affected area)

Integrate agent feedback:
- Proposals flagged as OVERENGINEERING or WORKAROUND: revise or drop.
- Proposals with SIDE_EFFECT flags: add the side effect to the proposal's trade-offs.
- Proposals that pass: present to user as-is.

## Step 7 -- Fix Application

Present reviewed proposals to user via `AskUserQuestion`:
- One button per approved proposal (label: proposal name)
- Final button: "None -- keep the diagnosis, skip the fix"

If user selects a proposal:
1. Resolve the test command by reading `skills/verification/SKILL.md` and following its Command Resolution.
2. When it resolved, follow the cycle in `skills/tdd/SKILL.md`: write a test that reproduces the root cause from Step 5a in the project's test layout, run the resolved command with the Bash tool, and print its `red:` line -- this run's exit code, the new test's name, and its first error line. When it resolved to `none`, print `skipped: test command none (<reason>)` and write no test.
3. Apply the code changes using Edit tool.
4. Read back modified files to verify changes.
5. When a command resolved, run it again and report the evidence line -- pass: exit code and the runner's summary line; fail: the first failing test name and the first error line. When it resolved to `none`, the reason was already printed at step 2 -- add only the manual check: "Check [specific behavior] manually."
6. **A failed run refutes the diagnosis, not the fix.** When step 5 fails, do not write a second patch. The fix was derived from the Step 5a root cause, and a fix that does not clear its own reproducing test is evidence that the root cause was wrong or incomplete. Reverse the code change with the Edit tool and read the file back; leave the reproducing test in place -- it is still red, and that is the sharpest symptom you now have. Record the Step 5a root cause as a refuted hypothesis with the failing output as its evidence, then return to Step 2 once. If the second pass also ends in a failed run, stop there: reverse that change too, and close as the Step 4 bound does -- what was ruled out, both refuted root causes, and the design assumption when the refutations point at one.

Neither the reproducing test nor the test runs are a new consent point -- the fix was gated by the `AskUserQuestion` above, the test file is part of the fix the user chose, and a test run changes no files.

If user selects "None": stop with a summary of the root cause.

---

## Anti-Patterns

- Don't ask more than 1 clarifying question per exploration round -- keep forward momentum
- Don't show raw agent output to the user -- synthesize into plain language
- Don't dispatch agents for simple single-file checks -- handle them directly
- Don't generate more than 3 fix proposals -- decision fatigue kills momentum
- Don't present unreviewed fixes -- every proposal goes through fix-reviewer
- Don't apply fixes without user approval
- Don't show internal routing decisions ("Dispatching code-tracer because...") -- implementation detail
- Don't continue debugging indefinitely -- 2 exploration rounds max before reporting partial findings
- Don't write a second patch after a failed fix -- the pull is strong because the failing output looks like a smaller problem than the original bug, but a fix that does not clear its own reproducing test has refuted the diagnosis, not missed a detail. Step 7 sends the run back to Step 2 once.
- Don't confirm by citation -- an upstream issue, a doc, or a forum answer that matches the symptom is a hypothesis, and the confirmation is its precondition found in this codebase (Step 3a). The pull is strong because the first authoritative-looking match reads like an answer, and it anchors the rest of the run.
- Don't research before local evidence -- research tests the hypotheses Step 1 produced; a run that opens with a web search produces a diagnosis shaped by whatever was found first.
