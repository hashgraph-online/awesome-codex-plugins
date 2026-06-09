# Dueling Route — debate-mode per-phase prompt templates and NTM commands

Detailed mechanics for `/council --mode=debate` (the contend pattern). The SKILL.md
`## Debate mode` section is the spine; this file is the operator handbook. The
absorbed `/expert-council` skill and `dueling-idea-wizards` both route here —
`dueling-idea-wizards` is `--mode=debate --focus=ideas`.

## Phase 1 — Pick the persona slate

Ask the operator for 2-4 named experts. Map each to its real frameworks so the persona argues authentically (e.g. Kent Beck → TDD, XP, 3X, "make it work/right/fast"; a composite VC → monopoly/wedge, traction, operating reality). Confirm the slate with the operator before any spawn — it shapes the verdict.

## Phase 2 — Spawn the swarm

```bash
ntm config get projects_base                 # resolve the base — it is NOT ~/dev
mkdir -p <projects_base>/<topic>-council/rounds
ntm spawn <topic>-council --cc=N             # one Claude pane per persona
ntm status <topic>-council                   # record pane indices
```

All-Claude is fine — persona diversity beats model diversity. If a Codex pane is wanted and Codex has a real API key, add `--cod=N`; otherwise skip it (see SKILL.md constraints). Keep the operator pane so the human can `ntm attach`.

## Phase 3 — Write the briefing

Write one `BRIEFING.md` in the council workspace. Required sections: the subject; the options/question; an honest asset read; **"the tension you must confront"** (a concrete, contestable claim — without it the council converges politely and produces nothing); the required verdict format; the round protocol.

## Phase 4 — Independent verdict

Send each pane its persona + the briefing path. Template:

> You are `<PERSONA>` on an expert council. `<one-paragraph persona identity + real frameworks>`. STEP 1: read `<BRIEFING.md path>` in full. STEP 2: write your independent verdict, fully in character, to `rounds/round1-<persona>.md` — ranked recommendations, kill list, one-sentence positioning, #1 risk. Confront the briefing's "tension" section head-on. No flattery. When the file is written, stop and wait.

## Phase 5 — The Duel (adversarial cross-scoring)

Each persona scores every *other* persona's verdict. Template:

> THE DUEL — adversarial cross-scoring. You are `<PERSONA>`. Read the other judges' verdicts: `<paths>`. Score each 0-1000 — overall, and per individual recommendation — reflecting how right, how actionable, and whether it survives YOUR frameworks. 0=worst, 1000=best. Be candid and adversarial; if scores cluster high you are not being critical enough. Where a judge is wrong, dock hard and say why. Write to `rounds/scores-<persona>.md`. Use ultrathink.

## Phase 6 — The Reveal + blind-spot probe

Show each persona how the others scored *them*. Template:

> THE REVEAL. The other judges scored your verdict 0-1000 — read their scoring of you in `<score file paths>`. React in character: (1) CONCESSIONS — where were the critics right? (2) DEFENSE — where are they wrong? (3) REVISION — did any critique change your call? Then the BLIND-SPOT PROBE: what important thing did NONE of the judges see? Write to `rounds/reveal-<persona>.md`. Concede what deserves conceding.

Optional extra rounds (`dueling-idea-wizards` Phases 6.5-6.9): rebuttal, steelman (argue the opponent's best point), deeper blind-spot. Run only if the reveal left a contested call unresolved.

## Phase 7 — Synthesis (the score matrix)

The orchestrator builds the matrix and reports faithfully:
1. Whole-ballot scores — each verdict's average cross-score.
2. Per-recommendation scores — every recommendation × every scorer.
3. **Consensus winners** — scored high by all; these are the binding plan, ranked by average cross-score (consensus weighted over unilateral enthusiasm).
4. **Contested calls** — large score gaps; surface for the operator's tiebreak with each side's argument.
5. **Mutual kills** — low by all, or conceded in the reveal.
6. **Blind spots** — synthesize the Phase 6 probe answers.
7. **Meta-analysis** — what each persona's scoring pattern revealed about its bias. This is the only section where orchestrator opinion is allowed.

Persist `BRIEFING.md`, `DUEL.md`, and all `rounds/*` into `.agents/council/<topic>-<date>/` in the host repo.

## NTM gotchas

- `projects_base` is not `~/dev` — always resolve it; spawning against the wrong base fails silently.
- `ntm send --all` hits the operator's shell pane — target with `--pane N`.
- CASS dedup blocks near-identical sends across panes — pass `--no-cass-check` for round broadcasts.
- Codex on a ChatGPT-billed account: NTM rejects `gpt-*-codex`, OpenAI rejects `gpt-5`. Tail panes for `status:400`; fall back to all-Claude.
- Poll for round completion by waiting on the expected `rounds/*.md` files, with a timeout.

## Anti-patterns (inherited from `dueling-idea-wizards`)

- **Love-fest scoring** — all scores above 800; nudge for candor and re-score.
- **Tribal defensiveness** — a persona scores its own camp high reflexively; the reveal exposes it.
- **Skip the reveal** — never; it is where the concessions happen.
- **Orchestrator editorializing** — report scores faithfully; opinion stays in meta-analysis.
- **Convergent verdicts** — not a failure; note it as strong validation, but check the briefing had a real tension.
