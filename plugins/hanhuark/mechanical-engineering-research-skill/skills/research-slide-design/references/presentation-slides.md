# Research Presentation Slides

Use this reference when creating or revising research presentations, slide outlines, slide content, speaker notes, animation plans, or visual-story plans.

## Core Principle

Design slides and spoken narration as complementary parts of one argument.

Slides should show the evidence, structure, and take-home message. The presenter should explain the logic, transitions, mechanisms, and implications. Do not make the presenter read slide text aloud.

## Logic Flow

Build the presentation so the audience can anticipate the next slide.

- Each slide should answer a question raised by the previous slide or prepare the audience for the next question.
- When saying "Slide N," the audience should have a reasonable expectation of what belongs on "Slide N+1."
- Use a clear chain: motivation, gap, approach, method, baseline case, key result, mechanism, comparison, implication, conclusion, next step.
- Avoid abrupt topic jumps. If a jump is necessary, add a transition slide or visual bridge.

For each slide, define:

- The question this slide answers.
- The single take-home message.
- The figure, animation, video, schematic, or data view that carries the message.
- The one sentence the presenter should say to transition to the next slide.

## Slide Cleanliness

Make slides feel clean and relaxed.

- Ensure each content block can be visually wrapped in a rectangle.
- Keep rectangles separated; do not let text, plots, arrows, captions, and images collide.
- Align edges and use consistent margins.
- Use whitespace as structure, not as leftover space.
- Avoid placing small text in corners or squeezing labels into crowded figures.
- Remove decorative elements that do not support the message.

A quick layout test: if the slide content cannot be divided into a few non-contacting rectangles, simplify the slide or split it into multiple slides.

## Graphics-Focused Communication

Prefer graphics over text.

Use:

- Schematics to explain systems, mechanisms, geometry, test facilities, and models.
- Figures and plots to show evidence and trends.
- Photos or microscopy images to show samples, hardware, or fabrication.
- Videos or animations to show time-dependent behavior, bubble dynamics, flow, deformation, moving interfaces, or experimental procedures.
- Sequential builds to reveal complex ideas step by step.

Use text only for information that the visual cannot convey clearly:

- Key labels.
- Essential assumptions.
- A concise take-home message.
- Critical numbers or comparisons.
- A short note that prevents misinterpretation.

## Text Discipline

Keep slides light on text.

- Use short phrases rather than full paragraphs.
- Prefer one main message per slide.
- Put detailed explanation in speaker notes, not on the slide.
- Avoid copying manuscript text onto slides.
- Do not include text that the presenter will simply read aloud.

If a slide needs many words, the idea is probably not yet visualized well enough.

## Speaker Notes

Write speaker notes to complement the slide.

Speaker notes should:

- Explain the transition from the previous slide.
- Describe what the audience should notice in the figure.
- Add physical explanation, context, and implications.
- Mention caveats or details that would clutter the slide.
- End with a bridge to the next slide.

Speaker notes should not duplicate the exact slide text.

## Technical Research Talk Structure

Use this structure as a default for thermal-fluid research talks:

1. Motivation: Why the application or scientific question matters.
2. State of the art: What is known and what remains unresolved.
3. Gap or challenge: Why the issue remains difficult.
4. Proposed approach: What method, diagnostic, model, or experiment addresses the gap.
5. Facility or model overview: Show the system visually.
6. Baseline case: Demonstrate the analysis workflow on one representative case.
7. Key results: Show the most important trends through figures.
8. Mechanism: Explain the physics behind the trends.
9. Literature comparison: Position the result against existing work.
10. Impact: State what is now understood, enabled, or improved.
11. Conclusions and next steps: Give a compact set of takeaways and future work.

Adjust the structure for the audience. For expert audiences, shorten broad motivation and add more mechanism, uncertainty, and comparison. For general audiences, add more schematics and reduce equations.

## Group Presentation Style Patterns

When preparing talks in the style of the provided thermal-fluid conference examples, prefer this rhythm:

1. Title slide with speaker, collaborators, institution, conference/session identifier, and a precise technical title.
2. Motivation slide that ties the topic to applications using recognizable systems, photos, or schematics.
3. Background physics slide that introduces the key phenomenon, regime transition, metric, or bottleneck visually.
4. Research-question slide that states a small number of concrete questions the talk will answer.
5. Experimental setup, model system, or data-source slide that makes the workflow visually inspectable.
6. Representative raw-data or baseline-case slide that shows what was measured before showing processed trends.
7. Regime, mechanism, or analysis-pipeline slide that explains how raw data becomes interpretable events or metrics.
8. Parametric result slides that vary one meaningful factor at a time and preserve visual comparability.
9. Mechanism or synthesis slide that turns observations into physical understanding.
10. Literature or benchmark comparison slide when positioning, generalizability, or contribution needs support.
11. Conclusions slide with concise takeaways, sponsors, team, and acknowledgments as appropriate.
12. Backup slides for detailed equations, material-property tables, additional curves, sensitivity checks, or derivations.

Use slide numbers unobtrusively when helpful for conference navigation and discussion.

## Presentation Corpus Lessons

This guidance is calibrated against the investigator's conference talks, seminar decks, outreach decks, and posters. Apply the patterns as reusable presentation judgment; do not copy private slides, unpublished data, or sponsor-specific material into public examples.

The strongest recurring style is **visual evidence first, short text second, explanation spoken live**. Most technical talks use roughly 13-30 slides, with figures or images on most slides and only a few dense backup-style slides. The design language is restrained: clean white backgrounds, red/orange section titles or footer accents, institutional/team identity on title and acknowledgment slides, and technical figures that carry the argument.

### NED3 Talk Grammar

For a thermal-fluid conference or seminar talk, use this slide grammar unless the user gives a different venue constraint:

1. **Title and identity:** precise technical title, speaker, collaborators, department/institution, venue, date, and sponsor/team identity when appropriate.
2. **Motivation through recognizable systems:** show applications, hardware, energy/safety/reliability context, or mission relevance with photos, schematics, and one or two anchor numbers.
3. **Background physics:** introduce the phenomenon, bottleneck, regime transition, metric, or measurement challenge visually.
4. **Research question or gap:** state what the talk will answer, preferably as two or three concrete questions rather than a paragraph.
5. **Approach overview:** show the diagnostic, model, ML workflow, facility, or experimental logic as a compact schematic.
6. **Experimental setup or data source:** use labeled photos and diagrams so the audience can inspect sensors, sample, geometry, heating/cooling path, cameras, DAQ, or simulation domain.
7. **Baseline/raw-data slide:** show representative raw traces, images, videos, thermographs, spectrograms, or synchronized signals before showing processed trends.
8. **Metric extraction or analysis pipeline:** explain how the raw data becomes event labels, features, regimes, heat flux, HTC, temperature field, model input, or prediction target.
9. **Parametric result slides:** vary one meaningful factor at a time and preserve axes, colors, marker meanings, panel layout, and annotations across related slides.
10. **Mechanism synthesis:** turn observations into physical reasoning using schematics, highlighted regions, arrows, side-by-side comparisons, or simplified governing ideas.
11. **Comparison and implication:** benchmark against literature, baseline cases, physical models, or design targets when generalizability matters.
12. **Conclusion and acknowledgment:** provide concise takeaways, next steps, sponsor logos, collaborators, and a team/photo element when appropriate.

For 12-15 minute conference talks, compress motivation and literature into the first 3-4 slides and prioritize setup, baseline, 2-4 result slides, mechanism, and conclusion. For seminars, expand background, literature comparison, and method details.

### Visual Figure Patterns

Use figures as the slide's main object. Strong recurring figure types include:

- **Annotated facility photos:** test rig, sensor locations, heater, sample, optical/acoustic/IR hardware, and data path marked directly on the image.
- **Raw-to-processed panels:** raw image/video frame, time trace, extracted metric, and final trend shown in one reading path.
- **Synchronized multimodal data:** temperature, heat flux, pressure, acoustic energy, images, spectrograms, or ML predictions aligned by time or event.
- **Mechanism cartoons beside data:** schematic of bubble/interface/film/surface structure next to the plot it explains.
- **Small-multiple parameter sweeps:** repeated panels for pressure, surface structure, heat flux, mass flow, geometry, or model condition with fixed visual grammar.
- **Workflow diagrams:** experiment, data preprocessing, model, validation, and output connected in a left-to-right or top-to-bottom process.
- **Benchmark/literature plots:** symbols, colors, or annotations that clearly distinguish this work, baseline, and literature.

Every figure slide should have a short title that states the finding or question. Avoid slides where the first visible text is only a slide number, a generic topic label, or an unexplained plot title.

### Text And Annotation Style

Use red/orange for titles, section emphasis, arrows, borders, or key callouts, but keep the data and images visually dominant. Prefer short phrases and labels over full sentences on the slide. When a slide contains a dense plot, reduce surrounding text and use direct annotations on the figure itself.

Good slide text usually does one of three jobs:

- names the mechanism or comparison;
- tells the audience what to look at;
- states the take-home conclusion that the presenter will explain verbally.

Avoid putting the full physical explanation on the slide. Put that explanation in speaker notes or spoken narration.

### Result Slide Sequencing

Do not jump from setup directly to final aggregate conclusions. Use a sequence:

1. Representative raw case.
2. How the metric or label is extracted.
3. First trend under a simple condition.
4. Comparison across cases.
5. Mechanism explanation.
6. Literature/baseline comparison or design implication.

This structure lets the audience trust the analysis before accepting the conclusion. It is especially important for boiling, acoustic sensing, IR thermography, computer vision, sequence regression, POD/NN, and surrogate-model workflows.

### Poster Grammar

Posters in this corpus are one-slide, graphics-dense artifacts. They should not be built like a single enlarged talk slide. Use a poster-specific structure:

- **Top banner:** title, authors, affiliations, institutional/lab identity, and sponsor logos.
- **Three to four vertical columns:** motivation/background, methods/setup, results/analysis, conclusions/impact.
- **Central visual path:** large facility/photo/schematic/plot cluster that makes the project understandable from a distance.
- **Compact text blocks:** short paragraphs or bullets that explain only what the figures cannot.
- **Captioned figures:** each major figure needs a short local takeaway, not just a label.
- **Bottom rail:** acknowledgments, funding, QR/code/contact, and optional references.

For posters, preserve alignment and column boundaries. The same rectangle test still applies, but at poster scale: each column, figure group, title block, and acknowledgment block should occupy a clean non-overlapping region.

### Outreach And General-Audience Talks

For K-12, outreach, summer academy, or non-specialist audiences, simplify the physics but keep real visuals. Use photos, demonstrations, animations, and everyday objects before equations. Replace dense result plots with a visible phenomenon, a question, and a simple observation. The goal is curiosity and conceptual understanding, not exhaustive technical defense.

## Baseline And Raw-Data Slides

Include at least one slide that shows representative raw data, raw images/video, or the baseline case before polished aggregate plots.

Use this slide to:

- Build trust in the measurements or simulations.
- Demonstrate synchronization, event labels, regimes, or extracted metrics.
- Show how the audience should read later processed results.
- Introduce the visual language used later, such as colors, symbols, regimes, or annotations.

For boiling, two-phase, IR, acoustic, or image-sequence work, use videos, time traces, thermographs, spectrograms, event labels, or side-by-side raw/processed views when available.

## Visual Comparability Across Result Slides

For parameter studies, preserve visual comparability.

- Keep axis limits, color meanings, marker meanings, and panel layout consistent across related slides.
- Use repeated slide structure when comparing pressure, surface structure, flow rate, inlet temperature, material, or model dimension.
- Reveal differences by changing the data, not by changing the visual grammar.
- Use compact annotations such as arrows, regime labels, or highlighted regions to direct attention to the comparison.

If a slide series compares multiple cases, make each slide answer one comparison question and use the transition sentence to explain why the next case follows.

## Media-Rich Mechanism Slides

Use embedded videos, GIFs, or sequential frames for transient and spatial phenomena.

Good candidates include:

- Boiling regime transitions.
- Bubble departure, interface motion, vapor-film growth, or return to nucleate boiling.
- IR temperature fields and time histories.
- Acoustic or hydrophone signals synchronized with physical events.
- ML tracking outputs, segmentation masks, IDs, or model predictions over time.

Pair videos with a minimal schematic, trace, or label that tells the audience what to watch. Avoid asking the audience to infer the point from motion alone.

## Backup Slides

Use backup slides deliberately.

Put detailed material-property tables, derivations, additional validation plots, alternate cases, and extra comparison figures in backup rather than crowding the main talk. Main slides should carry the story; backup slides should support Q&A.

## Figure Slides

For each figure slide, use the same four-level thinking as results writing:

1. Description: What is shown?
2. Observation: What should the audience notice?
3. Physical explanation: Why does it happen?
4. Significance: Why does it matter for the research question?

The slide should usually show description and take-home message. The presenter should provide observation, physical explanation, and significance verbally unless short annotations are needed.

## Animation And Video

Use animations and videos to reveal logic, not to decorate.

Good uses include:

- Building a schematic from components to full system.
- Revealing one mechanism at a time.
- Showing experimental procedure or flow path.
- Comparing before/after states.
- Synchronizing data traces with physical events.
- Highlighting how a metric is extracted from raw data.

Avoid animations that slow the talk without improving understanding.

## Review And Revision Checklist

Before finalizing a presentation, check:

- Can the audience predict why the next slide follows from the current slide?
- Does each slide have one main message?
- Is the slide mostly carried by graphics, figures, videos, or animations?
- Can each content block be wrapped in a clean rectangle without touching another block?
- Is all text necessary, short, and complementary to the presenter?
- Are speaker notes explaining rather than repeating the slide?
- Are complex methods or results introduced first through a baseline case or visual demo?
- Does the talk end with clear takeaways rather than a dense summary slide?
