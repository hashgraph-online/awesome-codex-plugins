# Scoping rules

A redesign goes wrong before the first reference is opened. The intent was fuzzy, so more was redesigned than was asked for, or the right thing was redesigned and its neighbours were rebuilt with it. This file holds the rules the scoping answers lean on, for whatever form the source takes. How the questions are asked is in [scoping-round.md](scoping-round.md).

## Three intents

| Intent | What the user points at | Mobbin tool | The failure it invites |
|--------|-------------------------|-------------|------------------------|
| **Screen** | a route, a file or a full image of one view | `search_screens` (platform required) | rebuilding the shell (nav, header) the screen shares with every other screen |
| **Component** | one region inside a screen: a table, a card, a form, a sidebar | `search_screens` on the screen the component lives on, then read the region | changes leaking outside the region; a shared component rebuilt, and every screen that renders it changing with it |
| **Section** | one block of a web page: hero, pricing, feature grid, testimonial, footer | `search_sections` (web only, no platform argument) | treating a section reference as a screen reference and inheriting the page's whole layout |

Decide which one this is, say it in the Scope line, and never mix references across two of them. A section reference tells you nothing reliable about a component. A whole-screen reference pulls a component redesign outward into the chrome around it.

## Naming a region

For a component, the region has to be nameable, so the render can be checked for anything outside it that moved. Name it three ways in the Scope line:

1. **By the marker the source carries.** In a codebase, the file and symbol, or a wrapper, a `data-` attribute or a named slot the source already has. In an image, the visible boundary: the edge of the card, the rule above the table, the frame of the panel.
2. **By what the user sees.** "The table and its filter row, from the tab strip down to the pagination footer."
3. **By what is outside it.** "The page title, the search box above the tabs, and the sidebar are not part of this."

A wrapper shared with other screens is outside the region.

**A shared component** is rendered by other screens too. Stop and say so: redesigning it is a design-system change, because every screen that renders it inherits it. The user chooses between a local variant for this screen and a shared change every one of those screens takes on. Do not choose for them. In an image-only run, ask whether the same component appears elsewhere in the product; when the user does not know, treat it as local and say so in the Scope line.

## Platform

Read the platform off the source as one of the two values the tools take:

- **`web`**: a web viewport or a web framework.
- **`ios`**: a phone frame or a status bar. An Android source searches `ios` too, the only phone platform the corpus carries, and the Scope line says so.

When it is not clear, fold it into the first scoping question as a single-select. Pass it to `search_screens` and `search_flows` so references come back in the right form factor.

Write the moves in the platform's words: click, hover and viewport on web; tap, thumb and sheet on a phone. Discard a decision that rests only on a form-factor fact the platform does not have (thumb reach under a pointer, a bottom sheet on desktop).

## Crops

A fragment (content cut at the frame edge, or one region lifted out with no chrome around it) is a section of a screen, not a screen. Say so once. Judge only what is in the frame, and never call something missing that could sit off-frame. If whether an element exists matters to a move, ask.

## Relaxing a default

Three defaults hold in every run: the design system and theme, the data and routes, and no new dependencies. A user who asks to relax one is asking a question, not granting a permission. Each request gets one follow-up before scoping continues, and the answer goes into the Scope line.

- **Design system and theme.** Ask: "Do you want this to take on the reference's look?" A yes is a theme change, a separate job with its own scope, and the Scope line says so; the redesign itself still ships inside the user's design system. A no, or a shrug, keeps the default, and you say nothing more about it.
- **Data and routes.** Ask which values or destinations may change, and why. A move that needs different data (a new derived value, a different sort) goes into the Scope line as the exception. A change to the data itself, or to where a control goes, is a separate job, and the Scope line says so.
- **No new dependencies.** Ask which additions are allowed (a library, a typeface, an icon set). Record them in the Scope line as the exceptions; everything unnamed stays out.

**Copy left unticked** is not a relaxed default; it means what it says. Text may change where a move needs it, and every change is named: a new element gets a label, and an element a move restructures may get a shorter or clearer one. Each added or changed string is listed in the Preserve list as changed text and marked as new in the report. Ticked or not:

- the domain never changes: no string swaps the product's entity or job for the reference's ("New customer" becoming "Create post", the reference's tagline, its plan names, its example rows). That is a copy job, scoped separately;
- numbers, names and routes stay as they are.

## Look words

A look word ("more vibrant", "less cluttered", "more professional", "less slop") names no part and no fault, but it points at one kind of decision on the screen. Before the mode is picked, translate the word into what it reads as on this screen, and let that decide the mode and, in explore, the axis. The user's word stays theirs in every line they read; the report says what moved.

| The user says | It reads on the screen as | Mode | Axis or problems |
|---------------|---------------------------|------|------------------|
| more vibrant, bolder, more colour, more playful | where the product's existing colour roles sit | explore | colour placement: which surfaces and parts carry the accent and the system's other colour roles (a filled header, a tinted plan surface, coloured icons) |
| less cluttered, cleaner, simpler, more minimal | how many things compete, and how they are grouped | explore | density: what the side merges, groups or leaves out, with all content kept as step 4 requires |
| more professional, more polished, more premium, more serious | how consistently and sparingly the screen is treated | explore | restraint: how much colour, how many type sizes and treatments, how much ornament the side's screens carry for the same job |
| less slop, less generic, less AI-looking | the habits [taste.md](taste.md) names, found on the baseline: gradients, pill badges, an icon beside every label, a subtitle restating its title, a card around everything, emoji, filler copy | targeted | each habit found is a candidate, named by the part that carries it, and the Problems question lists them; each fix is a move whose roll call shows the same part without the habit |

- **Colour placement spends only the colour roles the system already has**: no new hue, no gradient it does not carry. When it has none to spend (a monochrome system, one accent already on everything), the Preserve follow-up runs before scoping continues, since a new palette is a theme change and a separate job.
- **Slop is targeted** because its fixes are a list, not a direction: three variations of removing the same gradient differ in nothing.
- **A word the table does not carry**, or one the baseline shows nothing for ("more professional" on a screen that is already sparse), gets one question before the round: what on the screen reads that way, single-select, the options drawn from what the source shows. The answer maps to the nearest row.

## The user's register

How the request is worded predicts how the redesign will go wrong, and which guardrail to lean on:

- **"Redesign my X."** No reference, no constraint. Left alone, the render gains elements nobody asked for. Ask the full round, lean on the Preserve list, and cap the moves.
- **"Using this as reference, redesign my X."** A reference, no style constraint. The reference's brand bleeds in here: the background flipped from light to dark, the accent changed, its typeface and wordmark appearing. Lean on step 5's rule to take the reference's structure, not its look.
- **"The Y in my X is the problem, help me with that."** The user brings the diagnosis. Take it word for word as the first problem, aim the search at it, and answer it first. Add what you see beside it, marked as yours. Never rank your reading above theirs, or widen the job past what they pointed at without saying so.
- **"Rebuild my X to match the structure and layout of this, keeping our own styling."** The explicit form, and the one every run is held to, whatever the user's wording.
