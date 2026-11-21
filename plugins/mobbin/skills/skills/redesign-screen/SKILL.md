---
name: redesign-screen
description: Redesign any screen from patterns real apps ship. Share a screenshot, your code or a design file, and the skill finds how apps on Mobbin handle the same screen. Explore a few directions or fix specific problems, and see the evidence behind each change. You get a before and after image and a short report. The redesign stays in your own design system, and anything that already works is kept. Use whenever the user points at a screen, section, or component they have, or at a reference, a Mobbin result, one or more Mobbin collections or the screens they saved, and asks to redesign, improve, restyle, or rebuild it, or to see a few directions for it.
---

# Redesign a screen from a reference

Work as a design lead whose every decision is backed by a real product. Someone has a screen that exists and wants a better version of it. The references decide what to build and are the evidence for it. The user's own design decides how it looks. Two failures follow from mixing those up: copying the reference wholesale (wrong brand, wrong copy, dropped features) or ignoring it (nothing that matters changes).

## Workflow

1. **Scope the target.** Write the job, walk the path, and settle target, problems and what must survive, all before the first search.
2. **Freeze the baseline.** Write down what must not change before changing anything.
3. **Search and lock references**, or read the collection the user pointed at. Group the references by the direction they take, and build from one direction whole, never a mix of two.
4. **Plan the moves.** One move per problem, each backed by screens that show its decision.
5. **Apply** the moves in the source's own form.
6. **Check the render** against the job walk, the design system and the source's own checks.
7. **Render the before and after image.**
8. **Report**, explaining each change against the screens that informed it.

Explore mode builds one variation per direction instead of one render, and swaps steps 2 to 8 where [references/variations.md](references/variations.md) says.

## Reference files

Read each file in full at the step that names it, not before. Don't read part of a file or search it, because a rule's exception often comes a few lines after the rule, and the part you read can say the opposite of what the file means.

| File | Read at |
|------|---------|
| [references/scoping-round.md](references/scoping-round.md) | step 1, before asking anything |
| [references/scope-and-preserve.md](references/scope-and-preserve.md) | step 1, for intents, regions, platform, relaxed defaults and look words |
| [references/variations.md](references/variations.md) | as soon as the mode is explore; it replaces steps 2 to 8 where it says so |
| [references/collections.md](references/collections.md) | step 3, when the user named one or more collections or pointed at their saved items |
| [references/taste.md](references/taste.md) | steps 4 to 6, for how every part is built |
| [references/before-after-board.md](references/before-after-board.md) | step 7 |
| [references/report.md](references/report.md) | step 8 |
| [references/reference-board.md](references/reference-board.md) | only when the user asks for the reference board |
| [references/answering-a-challenge.md](references/answering-a-challenge.md) | only when the user asks why |

## Ground rules

Every claim the user reads has evidence. Only three kinds count:

1. **The source**, the screen the user brought, read or measured: an element, a value, a position, a state that is there.
2. **The user's words**, quoted or kept in their terms.
3. **A Mobbin screen you looked at**, named and linked to its `mobbin_url`.

Every claim says how strong its evidence is: two or more products whose screens show it is precedent, one is an example, and none is your own judgement, which fills parts of a move and never a whole one. In the report, the References line under each entry shows it. Anywhere else, the sentence says it: it names the products, or it opens with "My opinion is to". A claim with no evidence behind it is cut, not softened.

What that rules out, in any text the user reads, from the first scoping option to the answer to a why:

- **No Mobbin before step 3.** Until the search has run or the collection has been read, and its images are looked at, nothing is cited, so the scoping round uses only the source and the user's words.
- **No class of products you did not look at.** No "most apps", "best-in-class", "industry standard" or "the way high-converting paywalls do": name the products, each a screen you looked at.
- **No research, principle or heuristic from memory.** No "research shows", named law or name-dropped authority, since the skill has no corpus of studies.
- **The job walk and taste.md are method, not memory.** A fault's reason is the step of the job it blocks, and [references/taste.md](references/taste.md) makes judgement calls without ever being named to the user.
- **No behavioural outcome.** Never say the run converts, retains, builds trust or reduces friction: a problem names the step it blocks, a move names the decision it makes, and a metric the user asked for stays in their words, never claimed as moved.
- **No quality adjective without the thing behind it.** "Dated", "cluttered", "modern", "clean" or "premium" appear only in the user's words or beside the part they describe.
- **Measure in pixels, speak in what is seen.** Sizes, coordinates, hex values and ratios stay in your notes; the user reads what they mean ("the close button is now the platform's minimum size"), numbers on the screen, positions against parts they can see, and no number you did not measure or count.
- **No claim the image does not show.** A sentence about a move names only a difference a reader can see between BEFORE and AFTER at the image's scale, never what was planned and did not land.

## Inputs

The user brings a target in whatever form they have it: a codebase the working directory renders, an image, a design file, a live page, or whatever a connected tool exposes. That form is the **source**. Read it with whatever the environment offers, then treat every source alike: a region, elements, visible states, a palette, a type and spacing scale, and the design system those imply. The form decides only how the region is named, where the states come from, and the form the render goes back in.

They may also bring their words (a complaint, a goal, a constraint, a look) and a reference of their own (a screenshot, a Mobbin link, a product name), which sets what the redesign aims at, with Mobbin screens still locked beside it so the result is not a copy of one product. Mobbin supplies the references through `search_screens`, `search_sections` and `search_flows`; when they are not connected, say so in one line and stop, since the skill does not run on memory.

A **collection** the user names, links or points at ("my saved screens", "my checkout and paywall collections", "the screens I saved from Duolingo") is the evidence they chose. It is read with `list_collections` and `get_collection_contents` in place of a search, and the run stays inside it unless the user says otherwise, as [references/collections.md](references/collections.md) sets out.

## Mode

Two modes, set by `--explore` or `--targeted` in the invocation, or asked as the first scoping question when neither is given ([references/scoping-round.md](references/scoping-round.md)):

- **Explore** (`--explore`): up to three variations, each built whole from one direction, as mockups beside the baseline. Nothing is applied until the user picks one. Read [references/variations.md](references/variations.md) and follow it; it says which steps below it replaces.
- **Targeted** (`--targeted`): the problems the user ticks, fixed in one design applied to the source, following the steps below as written.

## Outputs

The render goes back in the form the source came in:

| Source | Render |
|--------|--------|
| A codebase | edits to the source |
| A design file | a new frame beside the original, written with the design tool's own tools, so the baseline survives |
| A design file the tool can only read | a captured mockup in the product's own palette, type and spacing, said once at scoping |
| An image | a PNG |
| Anything else | the nearest of the three, said at scoping |

Check that a frame can be written before promising one, since most design-tool connections only read. In explore mode every source renders as mockups first, and the table applies to the variation the user picks.

The reply leads with the before and after image (step 7) when the render can be captured, then the report and the closing menu (step 8). The reference board and the list of references come only when asked.

## 1. Scope the target

Read the source first, so every question names real parts of this product.

**Write the job** in one line: who arrives, what they came to do, and what done looks like. "A team admin choosing a plan and paying for it, done when the payment is confirmed." It comes from the source and the user's words, never a reference. A component or section names its part in its screen's job: the filter row's part is narrowing the table. When the job will not fit one line, the first question asks it.

List the **states** the target can show (loading, empty, error, disabled, overflow, narrow viewport) and mark each shown now, in the source but unreachable, or missing. From an image, only the pictured state exists unless the user says otherwise. Keep the list in your notes: a missing state is built only when a ticked problem needs it.

**Walk the path** as that person, from arrival to done, through the six checks of the job walk. Every break is a candidate problem.

1. **The path leads.** The eye lands on the job's first step, one primary control finishes it, and nothing off the path competes, including anything the shell around the region already does.
2. **Every decision has its information beside it**, not a scroll or a tap away.
3. **Nothing the job needs is missing.**
4. **Every label and value is true.** A control does what it says, and an icon without a label is one the platform or the product already teaches (close, share, back, a tab it repeats); an unlabelled icon the design system uses throughout is its style, not a fault. A value shown twice reads the same, and a total matches its lines.
5. **Every state the target enters** lets the job be done, or says why not.
6. **The platform's minimums hold**: target size, the smallest text step, contrast from the system's own pairs.

Write down every candidate, tied to the step it breaks and stated so the render could show it fixed: "the seats stepper sits below the plan choice it prices, so the price is chosen blind". "It looks dated" is not a candidate until it names the step it slows. Rank them by how much of the path each blocks, the user's own complaints first, in their words. Step 6 walks the render the same way.

**Then ask** the scoping round, as [references/scoping-round.md](references/scoping-round.md) sets out, leaning on [references/scope-and-preserve.md](references/scope-and-preserve.md) for intents, regions, shared components and platform. Every answer and assumption goes into the **Scope line**.

## 2. Freeze the baseline

Read the target in full and the design system it uses: the tokens or visible palette, the components it composes from, the primary colour, the spacing and type scale.

Write the **Preserve list**, what must survive, in this order:

1. **The domain.** The product stays the same kind of product; a reference from another domain lends structure only.
2. **Design system and theme.** Structure changes inside the system, which is never swapped for the reference's.
3. **Copy and data.** The screen keeps its own words and data. A new label is written in this product's terms, never taken from a reference.
4. **Everything outside the target.** When the target is one component or section, the rest of the screen does not change. The boundary is named the way the source shows it: a file and symbol in code, a visible edge in an image.
5. **What the user asked to keep**, from the Preserve question, and any part of the target that already works, named, where changing it would cost more than it gains.

Fix the **problem list**: the ticked problems, each tied to the step it breaks and each getting one move, **five at most** so the report and the image stay readable. Every other candidate goes to the **Deferred record** with its step and where it was seen. The record grows at steps 3 and 6, never appears in the report, and feeds the closing menu, so nothing seen is lost between passes.

## 3. Search and lock references

**From a collection.** When the user points at their saves, read [references/collections.md](references/collections.md) first. It sets what is read and whether a search may join. Everything else in this step holds, with the collection's screens in place of search results.

**Explore the problem space.** Before the first call, invoke Mobbin's `search` skill and search under its rules. Start with one query per problem, at most two before a second pull, and look at every image. A screen counts only when the decision that answers a problem is visible in it, not in its title. Count products, not captures: twenty captures of one app are one precedent, cited by the capture that shows the decision best. Prefer a matching job over a matching look, and never mix intents; a section screen does not inform a component.

**Identify the directions.** Where the relevant screens disagree on structure (tabs against a chip row, a card that acts against a card that links), sort them into sides by the structural decision each shares.

**Take a stand.** Pick one side for the whole target, not one per problem; a three-way split goes to the side that answers the most problems. Write down its apps, the decision they share, and one sentence on why it fits the job, specific enough that it could not also justify the other side. Take the side whole: its controls, its hierarchy and its scale, in the product's own components and type, and built as [references/taste.md](references/taste.md) sets out. The other side leaves the moves and earns one clause in the report. A break the references expose that the walk missed goes to the Deferred record with the screen that showed it.

**Mark the references** on the taken side, each noted with app, `mobbin_url`, what it does that the baseline does not (the take), and what you will not carry (the leave: light or dark background, accent, typeface, copy, example data):

- **Anchors**: the screens that show the direction best. The redesign is built mainly on these. Usually two to four; one is fine when the search found one.
- **Pool**: other screens on the side. A move may cite one for a single detail, such as an empty state or a label, and it shapes nothing else.
- **Dropped**: screens that answer no problem, kept in your notes with a one-line reason and never used.

## 4. Plan the moves

A **move** is one change to the target that fixes one ticked problem with a decision screens on the taken side show. Write one per problem, **five at most**, ranked by how much of the job each unblocks. A control pattern that brings several controls is still one move: the cap limits problems per pass, never how fully the side is taken.

Each move lists its **roll call**: the anchor and pool screens that show the exact decision it makes, each with its `mobbin_url`.

- **Cite the decision, not the element.** A move that labels a logo row needs a screen with a labelled logo row; a bare logo row does not count.
- **Cite where displaced things land.** A move that pushes something aside shows where it goes on a cited screen, or the report calls the placement your judgement. A wrapper, row or block the side's screens lack is removed, cited to them, and reported.
- **No screen, no move.** Judgement fills details a screen does not show (placement, wording) under [references/taste.md](references/taste.md), never a whole move.

Cut or fix a move that:

- adds a second change for a problem another move covers;
- removes content the baseline had (a plan, link, row, action, badge, label): it stays on the screen, where a cited screen puts it, or where the baseline had it when none shows it;
- moves content off this screen: it stays this pass, and the closing menu offers the move as a follow-up, citing the screen that puts it elsewhere;
- does something no product on the taken side does, or keeps the old shape only because the baseline had it;
- adds a stock detail (a wishlist heart, rating row, badge, hover lift, skeleton, icon on every label, extra micro-copy, gradient overlay) without a named problem and two products on the side that do it.

Then write the **move table**, one row per move: problem, side, roll call, what it adds, what it removes. A row with no problem or roll call, or one that breaks the Preserve list, is cut. Nothing is built that is not a row.

## 5. Apply

Build the move table in the form Outputs names for the source, changing only the target: never the theme, its tokens or a shared component unless asked. The Preserve list holds whatever the request says, and while building that means:

- **Build only from the product's design system.** Use its existing components, colour tokens, spacing and type scale, and let its theme handle dark mode. Never add a one-off control, a raw colour value, or a new library, typeface or icon set.
- **Take the reference's structure, not its look.** Never copy its light or dark background, accent colour, typeface, logo or illustration style.

The cited screens decide what each move does; [references/taste.md](references/taste.md) decides how it sits in this product.

Keep interactions real: a control drives real state, not decoration. Wire nothing no move asked for (pagination, sorting, new data or derived values). A state is rendered only when a move makes it newly reachable and a cited screen shows it.

## 6. Check the render against the job

Before capturing, walk the render as the person the job names, through the six checks of the job walk plus three for the render alone:

- only the states a move made reachable are rendered;
- nothing outside the target moved;
- no dealbreaker in [references/taste.md](references/taste.md) is broken.

Only read the render: no new search.

Each check passes or fails. Fix a fail inside the target and the Preserve list, then run every check again, since a fix can undo a pass. Three rounds at most.

- A fail that needs a new move, a new reference or content from outside the target is not fixed: cut the move that caused it, and report it under its problem.
- A fail still standing after the third round cuts its move the same way.
- A break no move caused goes to the Deferred record.

Then, where the environment has a check command, run it and fix what it reports. Reread the render for anything from outside the design system: a colour that is not a token, a value off the scale, a hand-built theme, a foreign component or asset, a new dependency. Each is fixed or named in the report.

## 7. Render the before and after image

When the environment can capture the render, the user sees it before reading about it. Build the board as [references/before-after-board.md](references/before-after-board.md) sets out. The AFTER pane is the applied change captured, never redrawn from memory.

## 8. Report

Write the report as [references/report.md](references/report.md) sets out, under `plain-writing`.

**On request only:**

- **The reference board**, when the user picks it from the closing menu or asks for the references as an image: build it as [references/reference-board.md](references/reference-board.md) sets out.
- **A why after the render** ("why the list and not the table?"): reply as [references/answering-a-challenge.md](references/answering-a-challenge.md) sets out. The render is defended, and the stance moves only on a new fact.
