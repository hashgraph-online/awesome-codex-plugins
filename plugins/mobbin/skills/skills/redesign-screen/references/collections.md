# Redesigning from a collection

When the user points at what they saved on Mobbin, those screens are the evidence they chose. Step 3 reads them with `list_collections` and `get_collection_contents`, under those tools' own rules, in place of a search. Explore's step 3 uses this file the same way.

## What the user pointed at

Everything the user pointed at is **the collection** in this file, however many collections it spans:

- **One collection**, by name or link.
- **Several collections** ("my checkout and paywall collections"). Read each and combine them. A screen saved in more than one counts once.
- **Saves described in words**: by app ("the screens I saved from Duolingo"), by pattern ("my saved login screens"), or both. Read `all-saved` and keep the items whose `app_name`, `screen_patterns`, `ui_elements` or flow `actions` match.
- **A teammate's saves** ("collections saved by <name>"). The tools don't record who saved what, so take the collections whose name includes the person ("<name>'s login", "settings (<name>)"), and say in one line which ones you took. If no name matches, say so and ask which collections to use.
- **Any mix of these**, combined the same way.

If nothing matches, say in one line what you looked for and ask whether to search Mobbin instead. Build nothing before the answer.

Name the collection to the user in their words: "your saved Duolingo screens", "your "Checkout" and "Paywalls" collections".

## When a search may run

- **Collection only** ("use my checkout collection", "from my saved screens"). Run no search unless the user picks one at the gap question.
- **Collection first, then search** ("use my collection and anything else on Mobbin", "add more if you need"). Read the collection, then search only for what it lacks, without asking.

"Go ahead without asking" skips the scoping round only. It doesn't allow a search.

If the collection tools aren't connected, say so in one line and ask whether to search Mobbin instead. Build nothing before the answer.

## What to read

- **Content type.** Screens for a screen or component, sections for a web section. A target that spans steps (an onboarding, a checkout across pages) reads flows too. If the collection holds only flows for a screen target, read them and count each flow screen as a screen.
- **Platform.** Read the target's platform first, then the same content type on the other platform if the collection holds it. Cite those screens for structure only, like a screen from another domain, and say so once in the report.
- **Size.** Follow the tool's limits on how much to read, and ask before reading further when the tool says to. Say in one line how many items there are and what you're looking for.

## Notes on saved screens

A comment on a saved item, a **note** here, counts like a reference the user brought in the prompt. Read every note and match it to the part of its screen it names. A note that names nothing visible ("good one", "check later") changes nothing.

A note decides:

- **The take.** The move carries the part the note points at, not another part you noticed.
- **The anchors.** On the taken side, a screen with a note is an anchor before one without.
- **A tie between sides.** When two sides fix the problems about equally, take the side with the noted screens.

A note doesn't decide:

- **The problems.** A liked part that fixes no ticked problem is not a move. It goes to the Deferred record with its note, and the closing menu offers it as a next pass.
- **The look.** A note that likes a reference's accent, typeface or illustration doesn't bring it into the product's design system. The Preserve list holds.
- **The side, against the problems.** When noted screens sit on the side that fixes fewer problems, the problems win, and the report names the note not followed.
- **Which sides explore shows.** Sides with noted screens come first, and every other side with precedent is still shown.

The problems settle notes that point at different sides, like any other split. Screens without notes count as usual.

## Is it enough?

Sort the collection's screens into sides and take a stand as step 3 does, from the collection alone. Then check it against what the run has to build:

- **Every part of every problem.** A problem is covered only when collection screens show a fix for each part of it, as the user put it. "No period or trend" needs both a period and a trend shown. Never split, merge or narrow a problem to fit the collection.
- **Products, not captures.** Count products as step 3 does, and only those on the target's platform. Screens from the other platform can still be cited for structure.

The bar a collection must pass:

- **Targeted:** every ticked problem has a move citing at least one collection screen, and the taken side has two or more products.
- **Explore:** at least two sides, each shown by two or more products, not counting the side the baseline already follows.

If it passes, build from the collection alone: no search and no gap question.

## The gap question

If it falls short and the user already allowed a search, skip the question and search for what's missing, as [When a search joins](#when-a-search-joins) says. If it falls short because the user asked to build from one app in their saves ("like the Locket screen I saved", "only my Locket saves"), skip the question and stay within the collection, as option 2 below sets out, since they already chose that app. Otherwise ask one question before planning any move, with the question tool as [scoping-round.md](scoping-round.md) sets out. Ask it even when the prompt said not to ask questions, because searching beyond what the user named is their decision.

Keep it short; the user knows what they saved. Two short sentences and the ask, at most 25 words: what the collection has, counted by product, and what it lacks, in the problem's terms. Don't describe the screens or explain the bar. "Your "Paywalls" collection has one iOS paywall (Calm). None shows a trial timeline. How should I fill the gap?"

Single-select, in this order, each description one short sentence:

1. **Search Mobbin for the gaps** (recommended). "Only for what's missing. Your screens still lead." Search as [When a search joins](#when-a-search-joins) says.
2. **Stay within the collection.** "Build from what it shows, even one app." For this run the bar drops to one product: build any move, or in explore any side, that one collection product shows, as an example rather than precedent. In explore, each side becomes a variation, and a one-app variation follows that app across the screen as [variations.md](variations.md) sets out. A problem no collection screen shows keeps its report entry as one that stayed. Leave this option out when it would build nothing: no collection screen shows anything the target needs, or in explore the only side it shows is the baseline's.
3. **I'll add to the collection.** "I'll wait, then read it again." Wait, and read the collection again when the user says it's ready. For saves described in words, the label is **I'll save more**.

Without a question tool, put the same three in a text round that asks for a word, and build nothing before the answer. If the call fails or returns no answer, stay within the collection, since that goes no further than the user asked.

## When a search joins

- **Aim it at the gap.** Search under step 3 and the `search` skill: one query per problem the collection doesn't cover, or one for a missing side. If every problem is covered but the taken side has one product, query that side's decision to find a second.
- **Collection screens come first.** A collection screen is an anchor wherever it shows the decision. A searched screen is an anchor only where no collection screen shows it, and the side is still taken whole.
- **Note each screen's origin**, collection or search, for the report.

## In the report

- **A change or variation built from a note** says so in the user's terms: "The total now sits above Pay, as your note pointed out." The sentence doesn't name the app; it stays on the References line as usual.
- **A note not followed** gets one clause in the plain line after the entries: the note, quoted, and why the problems went the other way. So does a note that likes a look the Preserve list keeps out: "Your note "love this green" likes a look; the redesign keeps your palette."
- **Where the references came from.** The plain line after the entries says so, as [report.md](report.md) sets out. When every reference is from the collection: "Every change draws on your "Checkout" collection." When a search joined, it names the changes that cite screens from outside it: "Changes 2 and 3 also draw on screens from outside your collection."
- **What the collection left out.** When the run stayed within a collection that fell short, the Degraded line names what it didn't cover and each change or variation built from one app. The closing menu offers a Mobbin search for each problem it didn't cover.
- **Search terms.** After a run that read only the collection, the closing menu's search terms are the queries that would cover what it lacked.
- **The boards.** The variations board and the reference board show the collections as chips on the title line, as [variations.md](variations.md) and [reference-board.md](reference-board.md) set out.
