---
name: human-pass
description: "Guide real-build acceptance: literal taps, real inputs, expected outcomes, worst case first, one sitting. Triggers: testflight, human pass, acceptance test, before we ship, hand it to the user, what should I test, release checklist, device test."
allowed-tools: Read, Bash, Grep, Glob, Write, Edit
kernel:
  kind: methodology
  version: 1
  side_effects: none
  confirmation: none
---

<skill id="human-pass">

<purpose>
A release that only machines have checked has not been checked. The human is the
only instrument that can see whether the thing FEELS broken, whether an upgrade
ate real data, and whether an error message is honest. This skill turns that
irreplaceable half hour into a designed pass instead of random clicking.
</purpose>

<why>
A 15-minute guided pass on a real device found a false paywall, a broken
selection interaction, reversed ordering, and two dead source paths. None were
visible to CI. In a parallel project, 7 defects found on a phone had been sitting
under 506 green tests. The gap is not test coverage; it is that some properties
only exist on the far side of a real screen and real data.
</why>

<scope>
Only what the human alone can verify:
- upgrade survival against THEIR real data, before anything else
- rendering, motion, and feel on the actual device
- whether failure states are honest (a fake success is worse than an error)
- flows that cross apps, accounts, or hardware
Everything a machine can check stays in CI. A pass that spends the human's
attention on something a test could have caught has wasted the only instrument
that cannot be automated.
</scope>

<form>
Literal or it does not count. The first draft of the founding example was
rejected in four words: "not a script, literally what to tap."

Each step gives:
1. The exact control, named as it appears on screen. Mine the real labels from
   the UI source; never invent or paraphrase them.
2. The exact input, paste-ready. Real URLs, real ids, real values, one per line.
3. What should happen, in one sentence.
4. What counts as a bug, when that is not obvious. Known rough edges get named so
   the human does not go hunting for something already on the board.
</form>

<ordering>
Worst case first. Data survival before features: if an upgrade ate the library,
the pass stops there and nothing else matters. Then the paths the release
actually touched, drawn from the diff, not from a generic checklist. Then the
cheap wide sweep for feel. Destructive or irreversible actions come last and are
usually skipped outright: never ask a human to gamble production data to test a
restore path.
</ordering>

<bundling>
Attention is the scarce resource, so the count of passes matters as much as
coverage. State the time cost up front and design to ONE sitting. Batch every
question that needs the same build, the same device, and the same state, so the
human is never called back for something that could have ridden along.

The tension is real and worth naming when it bites: more coverage per pass, or
more passes. Prefer one thorough pass over three thin ones. When a finding will
obviously force a rebuild, say so in the same breath, so the next pass is
expected rather than a surprise.
</bundling>

<close>
The pass ends with a verdict, not a vibe: a thumbs-up, or findings. Findings come
back as prose and screenshots; converting them into issues is the agent's job,
not the human's. Record the verdict as a state-change receipt on the release
issue, and say plainly what the thumbs-up unlocks (the next build, the
submission, the deploy promotion).

Until that verdict exists, the release is not done, whatever CI says.
</close>

<anti-patterns>
- Generic checklists ("test the main flows"). If it could have been written
  without reading this diff, it is not a pass.
- Steps whose outcome is unstated, so any result looks like a result.
- Asking for something CI already proves.
- Silent scope: if the pass skips an area, say which and why.
- Assuming the human will improvise around a broken step. They will report it as
  a bug in the pass, and they will be right.
</anti-patterns>

<on_complete>
Report where the guide is, the time it should cost, the single worst-case check
it opens with, and what the verdict unlocks.
</on_complete>

</skill>
