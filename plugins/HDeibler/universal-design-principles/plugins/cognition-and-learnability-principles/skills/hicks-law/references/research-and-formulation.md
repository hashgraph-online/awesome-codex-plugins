# Hick's Law: research and formulation

A reference complementing the `hicks-law` SKILL.md with the academic grounding and the limits of the law in practice.

## The original studies

- **Hick, W. E.** (1952). "On the rate of gain of information." *Quarterly Journal of Experimental Psychology*, 4(1), 11–26. Hick measured reaction time as a function of the number of equally-likely stimulus alternatives in a simple keypress task. He found a linear relationship between reaction time and `log₂(n)`, where n is the number of alternatives.
- **Hyman, R.** (1953). "Stimulus information as a determinant of reaction time." *Journal of Experimental Psychology*, 45(3), 188–196. Replicated and extended Hick's findings with varied stimulus types, supporting the general law.

The combined formulation is now usually called the Hick-Hyman Law. The Shannon-information formulation (T = a + b · log₂(n + 1)) became standard in HCI through Card, Moran & Newell's *The Psychology of Human-Computer Interaction* (1983).

## What the law actually predicts

Important: Hick's Law specifically predicts the time to *select* among options when:

1. The options are equally likely.
2. The user is highly practiced at the task.
3. The options are visually distinguishable but semantically simple (a labeled key to press, an arrow direction).
4. There's no additional cognitive processing beyond perceptual selection.

In real UI:

- Options are *not* equally likely (one is usually more popular).
- Users are *not* fully practiced (most users encounter most UIs casually).
- Options are *semantically rich* (the user has to read and understand each one).

So the strict Hick's Law math underpredicts time in real UI. The general *shape* (logarithmic growth, decision cost compounds with option count) holds; the specific values don't.

## Critiques and refinements

- **Seow, S. C.** (2005). "Information theoretic models of HCI: A comparison of the Hick-Hyman Law and Fitts' Law." *Human-Computer Interaction*. Reviews the conditions under which Hick's Law applies, and argues for caution in casual application.
- **Soegaard, M.** (Interaction Design Foundation summary). Notes that Hick's Law in UI design is best understood as a heuristic about cognitive load and option-set size, not a quantitative predictor.
- **Modern eye-tracking** suggests that for visually-rich option sets (e.g., menu items with icons and descriptions), the relevant time is *scanning* time more than *deciding* time, and scan time scales differently — closer to linear than logarithmic for short lists.

## When Hick's Law is the wrong model

- **Search**, not select. When users type to filter, Hick's Law collapses. Recognition over Recall is the relevant principle.
- **Dichotomous choice.** "Yes/No" / "Accept/Decline" — the law applies but the value is so small it doesn't matter.
- **Highly-trained expert tasks.** Power users in IDEs, DAWs, photo editors operate by spatial memory; Hick's Law cost approaches zero for the option set they know cold.
- **Cognitive evaluation tasks.** "Pick which essay is best." Hick's Law doesn't apply because the cost is in *evaluating* each option, not in *selecting* among recognized options.

## Cross-domain examples

### Restaurant menus

A 200-item Cheesecake Factory menu vs. a 6-item In-N-Out menu. Both successful businesses; very different decision experiences. Studies (Iyengar's "jam jar" experiment, 2000) suggest that beyond a certain point, more options actually *reduce* purchase rates — choice overload, a cousin of Hick's Law.

### Television channel lineup

A linear cable lineup of 200 channels vs. a Netflix front page of curated rows. Netflix's design replaces Hick's Law (200 channels) with a different problem (10 rows of 20 items each, each chosen by algorithm). Different cognition load; arguably less.

### Highway signs

US Interstate signs limit destinations to 3–4 per sign for a reason. A sign with 10 destinations would force drivers to take their eyes off the road too long. The Hick's Law cost (in seconds of attention) translates directly to safety risk.

### Phone IVR systems

"Press 1 for billing, press 2 for technical support…" — the canonical Hick's Law surface where designers can't even rely on visual scanning. Most IVRs cap menu depth at 3 levels and breadth at 5 options per level for this reason. Going deeper or broader produces measurable abandonment.

## Quantitative findings worth knowing

- **Time to select from a 5-item flat dropdown**: ~1.5 seconds for typical desktop users.
- **Time to select from a 20-item flat dropdown**: ~3.5 seconds (logarithmic scaling).
- **Time to select from a 20-item searchable combobox** (after a 4-character type): ~1.2 seconds (search collapses the cost).
- **Default-acceptance rate** for well-chosen defaults: 60–85% of users keep them — meaning most users pay near-zero Hick's Law cost.

## Closing

Hick's Law is the textbook principle most often invoked as a slogan ("more options = worse"). The reality is more nuanced: more options cost decision time, the cost grows sub-linearly, and good design (defaults, search, grouping) can shift the cost from "decide among N" to "recognize from N" or "evaluate the default."
