# The accuracy critic

A science film made from code looks authoritative, so a wrong claim travels further than a wrong claim
in a sketch. The critic is a **fresh** subagent: it has not seen the build, has no stake in the film and
reads only the fact sheet (pass 1) and later the frames (pass 2). The agent that wrote the sheet does
not grade it.

Why it is mandatory: @anxuanng's viral 3D film "Zeno's paradox: why your fingers never really touch"
([x.com/anxuanng/status/2120088745139638375](https://x.com/anxuanng/status/2120088745139638375), 586k
views) zoomed beautifully into atoms, and the replies took it apart: fingers do not touch because of
electrostatic repulsion between electron clouds and the Pauli exclusion principle, not because of Zeno's
paradox, which is about dividing distances and has nothing to do with contact. The picture was fine; the
*mechanism* was wrong, and the mechanism is what the title promised. A critic reading the sheet would
have caught it in one line ("the claimed cause is not the physical cause").

## Pass 1: the fact sheet (before any 3D work)

Spawn with the Agent tool (general-purpose, web access on), paste the prompt, fill the two paths.

```text
You are a strict science editor reviewing the fact sheet of a short 3D explainer video before it is
built. You did not write it. Your job is to stop false or misleading claims from reaching the screen.

Read: <ABSOLUTE PATH>/factsheet.md

For EVERY row of "On-screen claims" and "Real sizes used in the model":
1. Is the claim true as worded? Check the cited source yourself (fetch it). A source that does not
   say it, or says something narrower, is a FAIL even if the claim is "commonly said".
2. Is the MECHANISM right, not just the picture? (Classic failures: "fingers never touch because of
   Zeno's paradox" (it is electrostatic repulsion + Pauli exclusion); "mitochondria are the only
   source of ATP"; "electrons orbit like planets"; "the nucleus is the brain of the cell" when the
   claim is about decisions; "black holes suck things in".)
3. Units and orders of magnitude: nm vs µm, diameter vs radius, area vs length, real vs model size.
4. Wording that overclaims: "all", "only", "always", "the", a count or colour presented as real.
5. Do the model sizes agree with each other (ratios, volume fractions) and with the on-screen text?
6. Is every simplification that a viewer could mistake for a fact listed under "Simplifications"?
7. Anything a specialist would expect that is missing or misplaced (a part in the wrong place,
   a missing caveat on screen)?

Answer in this format, nothing else:
VERDICT: PASS | PASS WITH FIXES | FAIL
| ID | Verdict (OK / FIX / FAIL) | Problem | Exact replacement text (≤ 50 characters for on-screen) | Source checked |
Then up to 5 bullets of other issues. Keep on-screen replacements short and plain.
```

Apply every FIX to the sheet (and the film text) before the build; re-run the critic if anything was
FAIL. Paste the verdict, verbatim, under "Critic log" in the sheet.

## Pass 2: the frames (after the render)

Same fresh-agent rule (a new subagent, not the pass-1 one, which now has a stake).

```text
You are checking a rendered science explainer against its approved fact sheet.
Read the fact sheet: <PATH>/factsheet.md
Look at these frames with the Read tool: <PATH>/qa/sheet.png and <PATH>/qa/phone.png
(also the stills in <PATH>/qa/stills/ if you need detail).

1. Does every on-screen text match the sheet word for word? List any that does not.
2. Does any picture contradict the sheet (a part drawn in the wrong place, wrong relative size beyond the
   listed simplifications, a label pointing at the wrong part, a scale bar that cannot be right)?
3. Is the "simplified" caveat on screen long enough to read?
4. Are labels readable on the phone-size sheet?
VERDICT: SIGN OFF | FIX FIRST, then a table | Time (s) | Problem | Fix |.
```

## What the critics caught on the animal cell (2026-11-10)

- Pass 1 (sheet, PASS WITH FIXES, ~10 min, 51 tool calls) found:
  - an overclaim ("Holds the DNA": mitochondria have DNA too);
  - a wrong mechanism ("acidic enzymes": they are hydrolases in an acidic lumen);
  - a quote no longer in its source ("most of the cell's ATP");
  - a length quoted from an area (mitochondria);
  - misquoted book titles;
  - a scale bar that would contradict enlarged ribosomes;
  - five simplifications missing from the list.
- Pass 2 (frames, FIX FIRST, ~5 min) found:
  - a label lingering over the wrong part;
  - two leader dots on the wrong thing (empty space; a mitochondrion in front of the microtubule);
  - the scale bar back while "25–30 nm" was on screen;
  - end-card leaders crossing a dot;
  - untracked on-screen numerals;
  - a caveat too small for a phone;
  - two more unlisted enlargements.

  None of these were catchable by the scripts alone; the scripts now check the numerals.

Verbatim logs: "Critic log" in `examples/animal-cell/factsheet.md`.
