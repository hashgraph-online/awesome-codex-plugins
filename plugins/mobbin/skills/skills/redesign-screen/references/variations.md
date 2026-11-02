# Explore: up to three variations, one side each

An open-ended request ("make this better") names no fault, so one design has to guess the direction as well as build it, and the guess is usually the additive one. Explore mode hands the choice to the user: up to three variations, each built whole from one side of the Mobbin references, shown as mockups beside the baseline. Nothing is applied until one is picked.

The skill's Mode section sends a run here. The sections below replace the skill's steps 2 to 8 where they say so. Everything they do not mention holds as the skill states it.

## What holds

- Ground rules, Inputs, and writing under `plain-writing`.
- The Preserve list and how Apply holds it.
- [taste.md](taste.md), and step 4's cuts for stock details and dropped content.
- **Every variation is backed by precedent:** two or more products on its side, each a screen you looked at. A side only one product shows is an example, not a direction, so it is not shown. The exception is when the user chose to stay within a collection that fell short (section 3).

## 1. Scope

After Mode, ask Target and Preserve as [scoping-round.md](scoping-round.md) words them. There is no Problems question: the user named no fault, and picking three from a list is the decision this mode exists to avoid.

- **The line before the questions** says what the run returns: "An iOS paywall screen. I'll show up to three directions to pick from."
- **A proposed scope** carries **Mode.**, **Source.** when the codebase question applies, **Target.** and **Holds.**, and no fix list.

Still write the job and walk the path, in your notes. The candidates are not a work list here. They decide whether a component beyond the axis may change (section 4), and section 5 checks each variation against the same six checks. They go to the Deferred record as usual.

## 2. Freeze the baseline

As the skill's step 2, without the problem list. Read the design system from the source, since every variation is a mockup in it: the tokens or visible palette, the type and spacing scale, and the components. In a design file, that is the variables and components the design tool's read calls return.

The **BEFORE pane** is the user's input as given: their screenshot, or a capture of the running screen, with its own time and status bar, blurry if it came blurry. Nothing is redrawn on it. When the input is several screenshots of one scrolling screen, `before` lists them in scroll order, each labelled after the first ("Scrolled"), and the board shows each as its own card. Never join them into one image: the tab bar and headers that stay on screen would land mid-page, and the parts they share would show twice. The baseline mockup still rebuilds the screen as one full-height page.

Then build the **shell** every variation starts from, so the variations differ only where their sides do. Copy the skill's `assets/shell.html` and `assets/chrome/` next to the captures and fill it in:

- **Device.** The input's width in points (CSS pixels on the web) and the platform. There is no height: the baseline mockup and each variation are as tall as their own content, whatever height the input or its frame has.
- **System chrome.** On iOS, the status bar, home indicator and keyboard come from `chrome/`, drawn at 9:41 with full signal, wifi and battery, whatever the input showed. Set the keyboard only when the input shows one, light or dark as it is. Set the glyph colour from the input's top background. Never crop system chrome from the input into a mockup.
- **Frame.** Everything outside the region, rebuilt from the input in the design system: navigation, tab bar, the parts of the screen the target leaves alone.
- **Region.** The target, rebuilt as the input has it, between the region markers.

The filled shell is the **baseline mockup**. It is a working file, not shown on the board. Capture it and compare it with the input outside the system chrome. Fix in the shell any difference in layout, type or colour a reader would see at the board's scale, before any variation starts, since every variation inherits it.

## 3. Search wide and find the axis

Aim the search at the target's job, not at faults, so the results are broad enough to disagree:

- two or three queries: the target as a state, the target by the decision it turns on, and the journey it sits in;
- then one more pull of unseen results: one of those queries sent again, as Mobbin's `search` skill sets out.

Every query here runs `deep`, since each side has to show a decision. Everything else in the `search` skill holds. Look at every image and count products, not captures.

**From a collection.** When the user points at their saves, read them as [collections.md](collections.md) sets out, in place of the queries above. The axis and sides below are found within it, and a search joins only where that file allows, with the queries aimed at the missing side.

**Find one axis.** A screen makes many structural decisions (how plans are chosen, where the action sits, what leads the top). Sides per component would multiply into combinations no one can compare, or blend into a remix. So a run explores one axis: the decision the results split on most that also shapes most of the target.

- On a paywall it is usually how the plan is chosen: a comparison table, stacked plan rows, or one card with a toggle. For a component target, it is that component's main decision.
- When the screens differ most in how they're arranged (what comes first, how big each part is, where the action sits), make the arrangement the axis, even if their controls differ too. Each variation copies its side's whole arrangement, including where the action sits: if its products keep the action visible without scrolling, so does the variation.
- When the request was a look word, the axis is the one [scope-and-preserve.md](scope-and-preserve.md) maps it to (colour placement, density or restraint). Sides are still what two or more products visibly do, never a mood.
- **The axis line** names it for the report as the choice the user makes: "Pick how the plan is chosen." It never narrates what the screens or the variations did ("They differ in…", "The screens split…").

**Record the sides.** A side is a control pattern and hierarchy on the axis, visible in two or more products. Record each like the skill's step 3: its apps, the decision they share, and per screen the `mobbin_url`, `image_url`, take and leave.

- The side the baseline already follows is not a variation. Within a collection, a side whose one product makes the decisions the baseline already makes, on the axis and on the parts the screen shows, is the baseline's side too: it would build a look-alike.
- Keep up to three sides, the most different from each other first. Fewer sides means fewer variations, never a padded one.
- One side is shown alone, and the line under **Variations** says it was the only direction with precedent.
- If no side has precedent, say so in one line, build nothing, and offer a targeted run in the closing menu. If the user chose to stay within a collection, follow the next bullet instead.
- **Staying within a collection.** If the user chose to stay within a collection that fell short, also build each side that only one of its products shows, next to any side with precedent, as [collections.md](collections.md) says. Section 4 says how to build it. If the only side left is the one the baseline already follows, say so in one line, build nothing, and recommend a Mobbin search in the closing menu.

## 4. Build each variation from its side

A variation is its side taken whole, as the skill's step 3 defines it. Nothing in it comes from another side. Away from the axis, change a component only to fix a break the walk found, and only the way a product on its side fixes it. One product is enough, and the entry's Also: line says the change rests on one of its apps. Otherwise keep the component as the baseline has it, because a difference between variations with no reason makes them harder to compare. A side from one collection app is the exception, as the next paragraph says.

The exception is a side that one collection product shows, built because the user chose to stay within the collection. That one product is the whole side, so the variation follows it across the screen. Every part that both the target and the product's screen have follows the product's decision, built as [taste.md](taste.md) sets out and within the Preserve list. Parts that only the product has are left out. Without this, the variation would differ from the baseline only on the axis, which is too little for the user to judge that app's approach. Parts that only the target has stay, and the product's treatment is fitted around them: if the product's button is narrow because it has no fields above it, the target's button stays as wide as the target's fields.

Each variation has its own move table, as the skill's step 4 writes one, with two changes:

- the problem column holds the step of the job the move changes (for the axis move, the step the axis decides);
- every roll call comes from that side's products only.

**Mockups, for every source.** A variation is a copy of the baseline mockup with only its region changed, in the design system, captured at the input's scale factor.

- Nothing outside the region markers changes, except `data-glyphs` when the top background turns from light to dark or back. The chrome, frame and device size stay as the shell has them.
- The height follows the content. A variation that drops parts is shorter, one that adds parts is longer, and none is padded to match.
- The source is not touched: no code edits and no design-file frame until a variation is applied. So all of them are built the same way and in parallel.
- No interactions: a mockup is a picture of the state the baseline was captured in.

**In parallel where the host can.** When the host runs subagents (an `Agent` or task tool), start one per variation in the same turn, each with a brief that stands alone:

- the job, the Preserve list, the design system and the input;
- the baseline mockup's path to copy, and the rule that only its region changes;
- its side: the decision, and each screen's downloaded `image_url` file, take and leave;
- its move table;
- the path to [taste.md](taste.md) and the mockup rules above;
- what to return: the mockup's path, its capture's path, the move table as built, and which parts were judgement.

A subagent does not search, read the other sides, touch the chrome or frame, or write to the source. Without subagents, build them one after another.

## 5. Check each variation

Read each capture as the person the job names, through the six checks of the job walk plus three for the mockup alone:

- it carries only its side's decisions;
- nothing outside the region differs from the baseline mockup;
- no dealbreaker in [taste.md](taste.md) is broken.

Two rounds. A variation still failing is dropped and named in one line of the report.

Then check the variations against each other, not against BEFORE. The captures are the same width, and each file matches the baseline mockup outside its region markers, except `data-glyphs`.

- **Where the host can run a command,** diff the files, not the pixels. The status bar sits over the screen, so its pixels change with a variation's background, and a pixel diff there reports false faults.
- **Where nothing can run,** compare the status bar, home indicator and keyboard across the captures by eye at full size.
- **A variation that differs outside its region** is rebuilt from the baseline mockup with its region alone. The chrome is never patched to match.

## 6. The variations board

Copy the skill's `assets/variations.html` next to the captures, fill in its JSON and change nothing else. Capture it as [before-after-board.md](before-after-board.md) captures its board. The mockups, their captures and this board are the only files written to disk.

- **Panes.** BEFORE, then one pane per variation, headed by its letter alone. Above each screen sit the entry's name, what-it-does line and References line (each app's `mobbin_url`), so a reader meets the direction before the picture.
- **The rest of the JSON.** The title, the axis line, the theme and the meta line ("iOS paywall, 3 variations, 7 references").
- **Collections**, only when the run read the user's collections, even if a search joined them: each one's name and `mobbin_url`, shown as chips on the title line. Saves described in words are one chip, named as the user put it ("Saved Duolingo screens") and linking to All saved. A run built from a search alone leaves it out.
- **No marks or crops.** Unrelated redesigns share no numbered parts.

Then read it back. Each variation differs visibly from BEFORE and from the others on the axis. Two that read the same at the board's scale are one side, and the weaker is dropped.

Last, embed its images as [before-after-board.md](before-after-board.md) does, so the board file opens on its own.

## 7. Report

Written as [report.md](report.md) writes the report, to a cap of 150 words. In order: the file links (`See variations: [HTML](path) · [PNG](path)`), **Variations**, **Unchanged**, the Degraded line when there is one, then the closing menu. Headings, file links and the closing menu follow report.md. The entries follow `plain-writing`'s shape for options, with **Variations** in place of **Changes**.

**Variations** opens with the axis line, then one entry per variation. Its lines come in this order, and an optional line with nothing in it is left out:

1. **A bold short name** with its letter (**A. One card, two prices**), naming the side as it looks on this screen.
2. **What it does**, one sentence starting with the letter ("A puts both prices on one card with a yearly and monthly toggle."), checked against its pane. It describes this product, never a reference's labels or menu items. Skip it when the name already says it.
3. **References:** the apps on the side, each a link to its `mobbin_url`, each checked to show the side's decision, as report.md checks it. Apps are named on this line only, never inside a sentence.
4. **Downside:** the cost of this variation, as a fact its pane or its side's screens show. Optional.
5. **Also:** one fact that matters to the choice and fits no other line. Optional.
6. **My opinion is to** …: one sentence on this variation, when you have a view no reference backs. Optional.

Only the name is bold; the labels (References:, Downside:, Also:) are plain text. About 30 words per entry.

After the last entry, if the run read a collection, add one line on where the references came from, worded as in [report.md](report.md): "Every variation draws on your "Checkout" collection." or "Variation C also draws on screens from outside your collection." This line is required. Then two optional lines: an opinion on every variation, starting "My opinion is to", and "Not confirmed:" naming in a few words what the run did not confirm. No summary or comparison line after them. **Unchanged** lists what every variation kept.

The closing menu, filled from this run:

- **Apply one.** "Apply B" builds it in the source's form: edits for a codebase, a new frame beside the original in a design tool that can write one, a PNG for an image.
- **Combine.** "B with A's price line" applies B with one decision from another variation.
- **The reference board**, grouped by variation.
- **Search terms to keep going on Mobbin.**

## Applying a variation

Picking one runs targeted mode from the skill's step 4, with scope, Preserve list and references already locked. The variation's side is the taken direction, and its move table is the plan, each row's problem the step it changes.

- **A combination** adds one move for the borrowed decision, with its own roll call from the other side's products. It replaces what the chosen side did in that component only.
- **A borrowed decision that needs more than one component** is a new side, not a combination, and the reply says so.

Then the skill's steps 5 to 8 run as written: applied in the source's form, checked, the before and after board, and a targeted report.
