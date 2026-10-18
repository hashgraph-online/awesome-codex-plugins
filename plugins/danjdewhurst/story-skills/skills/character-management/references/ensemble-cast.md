# Ensemble Cast

Guidance for managing multiple significant characters — ensemble stories, large casts, multi-POV novels. Each member still gets a full character file; this reference covers how the cast works as a unit.

## Anchor Character

Designate one anchor character: the POV or emotional center the reader returns to. The anchor carries the main thematic question and gets the most page time. Without an anchor, ensembles drift — every scene feels like a reset. Record the anchor in `story.md` under `## Notes`, or inside the Relationship Map or Family Trees sections of `characters/_index.md`. `story reindex` rewrites that index but keeps those two sections and any other `## ` section it does not generate, such as `## Notes`, moving the extra ones after the generated sections. Weigh scene count against the anchor during revision.

## A/B/C Story Braiding

Give each major character their own story thread (A = main plot, B = secondary, C = tertiary). Braid them so chapters alternate threads and each thread's escalation lands at a different point — two threads peaking simultaneously dilutes both. Track each thread as its own arc in `plot/arcs/`.

## Per-Character Thematic Relevance

Every significant character must connect to the story's central value question. If a character can be removed without changing what the story argues, their role is not load-bearing — cut them, merge them, or rewrite their role so their arc takes a position in the debate.

## Merge-Characters Discipline

When two characters serve one function — same role in the plot, same relationship to the protagonist, same thematic position — merge them into one. A smaller cast of stronger characters beats a large cast of thin ones. Before merging, check: do both characters have distinct goals? If not, they are already the same character wearing two names. Move the useful traits to the survivor, update all cross-references, then run `story reindex .`, `story wordcount . --write`, and `story check .`.
