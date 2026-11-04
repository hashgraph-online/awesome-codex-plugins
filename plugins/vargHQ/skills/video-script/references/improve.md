# Improve this skill

Two loops. The script loop runs on every script (SKILL.md, step 6). The guide loop below changes this skill, and it
only changes it on evidence. Most ideas that sound better lose: only a third of the ideas Microsoft tested improved
the metric they were built for ([Kohavi et al., KDD 2013](https://exp-platform.com/Documents/2013%20controlledExperimentsAtScale.pdf)).

## 1. Keep a test set

`references/test-briefs.md` holds six briefs, one per format. Before you edit this skill, write all six with the
current version and keep the files as the baseline. "Create evaluations BEFORE writing extensive documentation"
([Anthropic, skill best practices](https://platform.claude.com/docs/en/agents-and-tools/agent-skills/best-practices)).

## 2. Log every script that ships

One line per script in `scripts-log.jsonl` next to the project (not in this skill):

```json
{"date":"2026-11-03","format":"ad","strategy":"problem-agitate-solve","hook":"My shoes were still wet from Sunday.","length_s":30,"words":71,"check":"0 fail 1 warn","approved_by":"user","posted":"tiktok","metrics":{}}
```

Fill `metrics` when the numbers come back. Log the losers too; they are half the lesson.

## 3. Read the number, fix only the part it grades

| Number | Grades | Change |
|---|---|---|
| Shorts "viewed vs swiped away", 3-second hold | the hook (first beat) | rewrite the first beat; keep the body |
| Long-form "Intro" (still watching at 30 s) | whether the opening keeps the title's promise | deliver the promise sooner |
| A dip in the retention graph | that beat | cut it or tighten it |
| A top moment late in the video | the order | move it earlier |
| A spike | either a great moment or a confusing one | rewatch it before copying it |
| CTR, downloads, sales, "what is this?" comments | the ending, the offer, product clarity | rewrite the last two beats |

Sources: [YouTube Help, key moments](https://support.google.com/youtube/answer/9314415),
[YouTube Help, Shorts analytics](https://support.google.com/youtube/answer/12942217); practitioners on X map the same
way (views grade the hook, downloads the CTA, revenue the funnel:
[@gregisenberg](https://x.com/gregisenberg/status/2031107609852325980); rewrite only the hook or cliffhanger when a
video misses 2.5% CTR or 55% 3-second through-play: [@RohanNayak2](https://x.com/RohanNayak2/status/2098104784264065525)).

## 4. Test one thing at a time

Same body, new hook. Same script, new ending. Pick the metric before posting. On paid platforms use the platform's own
split test ([Meta split testing](https://developers.facebook.com/docs/marketing-api/guides/split-testing/)), which
keeps audiences apart.

## 5. Judge drafts the way that works

The full protocol, the bias table and both judge prompts are in `judge.md`. In short:


- Turn the brief into YES/NO checks and answer each with one line of reason
  ([TICK](https://arxiv.org/abs/2410.03608)).
- Compare two drafts pairwise, in both orders; count a win only if it holds both ways
  ([MT-Bench](https://arxiv.org/abs/2306.05685)). Match their length first.
- Use a judge from a different model family, because models prefer their own text
  ([Panickssery et al.](https://arxiv.org/abs/2404.13076)).
- Treat any model judge as triage. Judges agree with people only about 73% of the time on stories
  ([LitBench](https://arxiv.org/abs/2507.00769)); the audience and the person decide.
- Edit by quoting the failing line and naming the change, at most three rounds
  ([Self-Refine](https://arxiv.org/abs/2303.17651)). "Re-read and improve" without an outside signal can make it worse
  ([Huang et al., ICLR 2024](https://arxiv.org/abs/2310.01798)).

## 6. When a lesson goes into the skill

Promote a lesson from the log into SKILL.md or a reference file only when one of these holds:

- it won a clean one-variable test;
- the same note came from the person twice;
- two independent credible sources say it and nothing here contradicts it.

Then:

1. Write the rule in one imperative sentence, with the reason and the source link.
2. Put it in the narrowest file that needs it (a format file before SKILL.md).
3. Re-run the six test briefs with a fresh agent that has only the skill loaded ("Claude B"), compare to the baseline
   with the judge protocol above, and keep the change only if it does not lose on any brief
   ([Anthropic, Claude A / Claude B](https://platform.claude.com/docs/en/agents-and-tools/agent-skills/best-practices)).
   With two runs per brief, two scripts from the same version differ by up to about one point; count a loss only when
   the new version is lower by more than that on a brief, or when both judges rank it lower.
4. Delete a rule nobody can trace to evidence. Keep SKILL.md under 500 lines.

## 7. Add a new format

Copy the shape of `references/ad.md`: when to use it, the beats in seconds, the word budget, three rules with sources,
one full example script in the table format, and the checks. Link it from the format table in SKILL.md.

## 8. Refresh the evidence

Every few weeks, or when a new model changes how videos are made:

- Search X for the format plus "script", "hook", "retention" in the last 7 days and the last 4 months, sort by
  bookmarks, read the top 50, copy quotes verbatim, record followers and numbers, and drop bait accounts
  ("comment X to get", bookmarks far above likes on a small account).
- Re-read [Wikipedia: Signs of AI writing](https://en.wikipedia.org/wiki/Wikipedia:Signs_of_AI_writing). The phrases
  models overuse change with each generation; update the list in `scripts/check_script.py`.
- Check the clip lengths in the varg model specs ([index](https://varg.ai/models/llms.txt)) and update the shot table.

## The loop in practice (2026-11-03)

This skill was built this way. The briefs are in `test-briefs.md`.

1. **Round 1.** Four fresh agents (Claude Sonnet) wrote the six test briefs, two without the skill and two with it.
   Two blind judges (Claude Opus and Claude Sonnet) scored all 24 scripts.
   - Score out of 10: 7.54 with the skill, 6.40 without. The skill's script was ranked best in 10 of 12 brief and
     judge pairs (sign test p = 0.04). The lowest score was 6.0 with the skill and 4.5 without.
   - The checker failed 5 of 12 scripts written without the skill (lines too long for their seconds) and none with it.
   - Outside the drama brief, the judges flagged 36 invented facts without the skill and 14 with it.
   - The skill lost on one brief, the plane-windows short: its hooks hid the topic ("A corner.") and read flight
     numbers aloud. Other notes: an ad dropped the UGC voice, an offer lost its "first order" condition, and a drama
     spent the series reveal in episode 1.
2. **The fix.** Five rules, each tied to a note: name the topic in the first line; codes on screen, not in the voice;
   offers keep their conditions; UGC with an AI presenter keeps the first person in the present tense; don't spend the
   series payoff in episode 1.
3. **Round 2.** Two more fresh agents wrote the three weak briefs with the fixed skill; the judges ranked six versions
   per brief blind. Scores out of 10: fixed skill 6.92, first version 6.75, no skill 6.08. The fixed skill had the best
   average rank and the highest floor (6 against 5). The plane-windows brief rose from 5.75 to 7.0, still below the
   best script written without the skill (8); the drama dipped from 7.75 to 7.0, inside the run-to-run spread.

Limits: the judges are models of the same family as the writers (self-preference); two runs per brief; no audience
numbers yet. Treat these as triage, and replace them with platform results when scripts ship.

Lessons logged, not yet promoted (each needs a test):

- Start from something the viewer can check right now ("look at the window next to you"); the best plane-windows
  script did, and both judges ranked it first.
- A spoken AI or ad disclosure in the hook ("This is an ad for DryDock") reads stiff; try the label on screen and a
  natural spoken line.
