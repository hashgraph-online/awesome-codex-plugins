# Hierarchy: research grounding and cross-domain examples

This reference complements the `hierarchy` SKILL.md by going deeper into the research grounding and showing how the same hierarchy principles operate across domains beyond software UI.

## Research grounding

### Eye-tracking studies

Decades of eye-tracking research consistently show that initial fixation patterns on novel pages are dominated by two factors: **bottom-up salience** (what's bright, large, high-contrast, isolated) and **top-down expectation** (where users have learned to expect certain things). Hierarchy is the design lever that aligns the two — making the salient elements *also* the meaningful ones.

Notable findings:

- **Pernice & Whitenton, NN/g eye-tracking studies (2014, 2017)** — users fixate first on items with strong visual contrast, large size, and isolation. F-pattern reading (top-left → right → down-left → right again) emerges only when no strong hierarchy directs attention otherwise.
- **Itti & Koch (2001)**, *Computational Modelling of Visual Attention* — saliency maps predict where the eye lands within ~200ms based on low-level features (color, intensity, orientation). Strong hierarchy *aligns* saliency with intended focal points.
- **Buscher, Cutrell, Morris (2009)**, "What do you see when you're surfing?" — a multi-page scan study showing that pages with stronger visual hierarchy are processed faster and with less re-fixation.

### Working memory and ranking

Hierarchy reduces cognitive load by externalizing the importance ranking. Without hierarchy, the user must hold the entire option set in working memory while evaluating; with hierarchy, the eye picks the primary first and only consults secondaries if needed.

This connects to **Sweller's cognitive load theory (1988)**, particularly the concept of *extraneous cognitive load*: load imposed by how information is presented rather than the information itself. Poor hierarchy is extraneous load.

### The "above the fold" myth

A persistent designer fear: critical content must be above the fold (visible without scrolling). Eye-tracking studies (NN/g) consistently find that users scroll readily when hierarchy invites them to. A poorly-hierarchical page above the fold loses more users than a well-hierarchical page that requires scrolling.

The corollary: don't compress hierarchy to fit the fold. Let the primary breathe.

## Cross-domain examples

### Print design

Hierarchy is the oldest design discipline, predating software by centuries. Examples that illuminate the principle:

- **Newspaper front pages.** The above-the-fold lead story has the largest headline, often a hero image, and the first columns of body. Smaller stories below, briefer headlines further. The whole front is a 3–5 tier hierarchy.
- **Book typography.** Title page → chapter opener → section heading → body → footnote → page number. Six tiers handled entirely with type size, weight, and white space.
- **Movie posters.** Title (largest), tagline (medium), credits (smallest, often in a "billing block" with strict legal sizing). The hero image dominates everything; type is secondary.

A useful exercise for designers: study a Penguin Modern Classics cover or a Swiss-style Helvetica poster from the 1960s. Hierarchy with very few tools, executed precisely.

### Wayfinding and signage

Airports, train stations, and roadways are pure hierarchy machines.

- **Highway signs.** Destination name (largest), route number (smaller), exit number (small badge), distance (smallest). Drivers parse this in 2 seconds at 70 mph because the hierarchy is unmistakable.
- **Airport terminal signs.** Gates (large), then concourse direction, then services (food, restrooms, baggage) at progressively smaller sizes and distinct colors.
- **Hospital wayfinding.** Department names large; sub-services smaller; navigation arrows in a separate visual register entirely.

What software UI can borrow: ruthless tier ranking, oversized primary information, simple color codes for category.

### Industrial product design

A car dashboard is an information-density problem solved with hierarchy:

- **Speedometer**: largest, centered, highest-contrast.
- **Tachometer, fuel, temperature**: secondary tier — visible but smaller.
- **Indicator lights**: tertiary; visible only when activated.
- **Navigation/infotainment**: separate region, separate hierarchy.

Failures: dashboards from the 2010s where every gauge was the same size in a digital display, requiring drivers to read labels to find the speed. Tesla's Model S had this issue early; later updates restored hierarchy.

### Architecture

A cathedral is hierarchy at scale: the entry pulls the eye to the altar (focal end of the nave); side aisles recede; chapels are tertiary spaces. The Gothic ribbed vault organizes the eye upward toward the boss at the keystone.

A modern open-plan office, by contrast, often has *no* hierarchy — every desk equivalent, every meeting room similar. Wayfinding fails; visitors get lost.

### Information graphics

Charles Joseph Minard's 1869 map of Napoleon's Russian campaign (the "best statistical graphic ever drawn," per Tufte) is hierarchy applied to data:

- The width of the army's path (representing troop strength) is the dominant visual.
- Geography is secondary — it's there for context, drawn with light strokes.
- Temperature curve at the bottom is tertiary, related to the path by date.

Six dimensions of data, three tiers of hierarchy, instantly readable.

### Music

Hierarchy isn't visual-only. A symphony has primary melody, supporting harmony, accompaniment, percussion — orchestrated so that the primary melody is always perceivable above the texture. Mixing engineers in popular music make the same choices: vocals foreground, drums and bass mid, pads recessed.

The principle is the same: a primary signal made unambiguously dominant against a quieter background.

## Quantitative findings to lean on

When a stakeholder pushes back on a hierarchy decision, these numbers can help:

- **F-pattern reading** (NN/g): on uniform pages, users read in an F-shape, missing 70%+ of bottom-right content. Strong hierarchy can override this.
- **3-second test**: shown for 3 seconds, users can recall the page's primary subject if hierarchy is strong; not if it's flat.
- **Scroll depth on long pages**: pages with strong hierarchy retain readers ~2x longer than flat pages of the same content (multiple agency case studies).
- **Conversion uplift from primary-CTA emphasis**: A/B tests consistently show 10–30% conversion lift from elevating the primary CTA's visual weight (size + color + isolation), holding all other content constant.

## Edge cases

- **Hierarchy in dense data tools.** Bloomberg terminals, IDEs, DAWs all violate "use only 3 tiers" because expert users don't *scan* — they fly to known locations. Hierarchy still exists but is more subtle and modal-context-sensitive.
- **Hierarchy in voice UI.** No visual hierarchy applies; replaced by narrative ordering ("most important first") and prosody. The same logic, different modality.
- **Hierarchy in print-on-demand and templating.** Templates impose a fixed hierarchy that can't accommodate every content type. Some content forces designers to fight the template; better to design templates with hierarchy *flexibility* (modular regions that can be promoted/demoted).

## Closing thought

Hierarchy is among the easiest principles to *demonstrate* and the hardest to *teach in the abstract*. The most effective learning is the squint test, repeated across many designs, until you can feel which one has hierarchy and which doesn't before you can articulate why.
