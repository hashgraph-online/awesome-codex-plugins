# Progressive Disclosure: research and cross-domain reference

A reference complementing the `progressive-disclosure` SKILL.md with deeper grounding from HCI research and cross-domain application.

## Research lineage

- **The Xerox Star user interface** (Xerox PARC, 1981). The first commercial system to apply progressive disclosure as a deliberate design strategy. The Star's properties dialogs showed common settings by default and offered detailed controls behind a "More" button — a pattern adopted by Apple's Lisa (1983), Macintosh (1984), Microsoft Windows, and most subsequent UI conventions. The Star's design philosophy is documented in: Johnson, J. et al., "The Xerox Star: A Retrospective," in *Human-Computer Interaction: Toward the Year 2000* (1995).
- **Carroll, J. M. & Carrithers, C.** (1984). "Training Wheels in a User Interface." *Communications of the ACM* 27(8). The "training wheels" concept: progressively introduce features so novices aren't overwhelmed. Closely related to progressive disclosure as a learnability strategy.
- **Carroll, J. M.** *The Nurnberg Funnel* (MIT Press, 1990). Argued for "minimalist instruction" — showing learners only what they need now, in a context where they need it. Anticipates much modern onboarding-as-progressive-disclosure thinking.
- **Sweller, J.** (1988) and the cognitive-load theory tradition. Provides the theoretical mechanism: working memory has limits; visible elements impose load even when ignored; reducing visible elements reduces extraneous load.
- **Lidwell, Holden & Butler**, *Universal Principles of Design* (2003) compactly articulated progressive disclosure as a unified design strategy spanning software UIs, instructional materials, and physical environments.
- **Nielsen, J.** has written multiple NN/g articles on progressive disclosure as a UX technique, particularly for forms, settings, and learnability.

## The Xerox Star pattern in detail

The Star's "More" button pattern works because of several design choices:

- The default view shows the most-frequent options. New users see only what they need.
- The "More" button is consistently labeled and consistently placed (right edge of the dialog).
- Expanding "More" doesn't lose state — fields the user filled in stay filled.
- The expansion is reversible — "More" becomes "Fewer" and the user can collapse.
- The same dialog shape works for every property type, so users learn the pattern once.

These properties make the affordance learnable by exposure. After encountering "More" in a few dialogs, users predict what's behind it elsewhere.

## When progressive disclosure outperforms its alternatives

Common alternatives to progressive disclosure include:

- **Show everything by default.** Pro: maximally discoverable. Con: cognitive load on every visit; novices overwhelmed.
- **Wizard / multi-step flow.** Pro: imposes structure, no decision overload at any step. Con: feels patronizing for power users; loses ability to skip-around.
- **Search-only ("just search for what you need").** Pro: scales to any IA depth. Con: requires user to know what to search; bad for discovery.

Progressive disclosure occupies a useful middle ground: it shows the typical case, surfaces the rest on demand, supports both novice and expert with the same surface. Its trade-offs:

- **Power users pay a click** to reach disclosed content. Mitigations: keyboard shortcuts, remembered disclosure state.
- **Novices may not discover** the deeper content exists. Mitigations: clear disclosure labels, contextual prompts ("More options").

## Cross-domain examples

### Theme park line design

Theme parks engineer queues to disclose only a small portion of the line at any time. Visitors at the entrance see a manageable wait; visitors deep in the line don't see how much remains. Patterns:

- **Serpentine layouts** that fold long lines into compact spaces.
- **Walls and partitions** that block sightlines.
- **Status signs** that give the user some information ("Are you ready for...") without exposing the full line.
- **Distractions** (videos, themed environments) that occupy time without adding wait stress.

The progressive-disclosure principle: visitors agree to a long wait one segment at a time, never seeing the whole length. If they saw the whole line, more would balk.

### Restaurant menus

Many restaurants use progressive disclosure in menus. The main menu shows entrées; the wine list is a separate document; specials are announced verbally; the dessert menu arrives after dinner. Each layer is delivered at the moment it's relevant.

A "single big menu" approach (everything on one page, including beverages, desserts, mods) overwhelms diners. The staged approach respects when each decision is made.

### Application installation

Modern installers often hide most options behind an "Advanced" or "Custom" button. Default installation accepts sensible defaults; advanced installation lets the user pick install location, components, etc. The disclosure mirrors usage: most users want the default; few want to customize.

### Tutorials and education

Good educational design uses progressive disclosure: introduce a concept simply, let the learner practice, then introduce nuance and edge cases. Programming tutorials especially benefit — "Here's a function" before "Here's how function scope and closure interact."

The ill-fit is the textbook that introduces all the formalism on page 1 before showing what it's for. Few learners survive the first chapter.

### Maps and zoom

Digital maps progressively disclose detail by zoom level. At country zoom, only major cities and freeways are labeled. Zooming in reveals streets, then building names, then individual addresses. Showing all detail at all zooms would be unreadable.

The same logic applies to dashboards: high-level KPIs at the page top; click into each to drill down to the contributing details.

## Common patterns across domains

| Domain | Primary layer | Secondary layer | Affordance |
|---|---|---|---|
| Software dialog | Common settings | Advanced settings | "More" button |
| Settings page | Frequently-changed | Power-user / rare | Accordion or tab |
| Theme park queue | Current segment | Full line | Walls / serpentine layout |
| Restaurant | Entrée menu | Wine, dessert, specials | Separate documents / staff timing |
| Map app | High-level | Detail | Zoom |
| Tutorial | Core concept | Edge cases / advanced | Subsequent chapters |
| Help center | Top issues | Long-tail issues | Search / category drill-down |
| Tax form | Common income types | Unusual situations | Schedules / supplemental forms |

The same principle, instantiated differently per medium.

## Failure modes

- **All-collapsed default.** A page where every section starts collapsed reads as empty. Open the first section so the user has somewhere to land.
- **Disclosure stacking.** Collapsed → "More" → "Even More" → "Advanced." Each click adds friction; the deeper content is effectively hidden.
- **Hiding the required.** Required fields tucked behind disclosure. Users submit and fail.
- **No memory.** Every page load resets disclosed state. Users who frequently expand the same section grow frustrated.
- **Unlabeled disclosure.** "More options" with no hint of what's behind. Users won't expand unless desperate.
- **Disclosure as dark pattern.** Burying important information (fees, terms, opt-outs) behind disclosure. Users feel cheated when they expand.

## Heuristics

1. **The Pareto check.** What fraction of users engage with each control? If <20%, candidate for tucking. If >80%, must be primary. The middle is judgment.
2. **The expert-vs-novice test.** Walk a novice through the surface; then a power user. Ideally both succeed without friction, the novice via primary chrome and the power user via disclosure.
3. **The "did they find it?" check.** For tucked content, can users locate it when they need it? If they search instead of finding the disclosure, the affordance is too quiet.
4. **The "wait, where did that go?" check.** Long-time users are sensitive to controls being moved into disclosure. Migration UX matters.

## Resources

- **NN/g articles on progressive disclosure** — many publicly available.
- **Tidwell, J.** *Designing Interfaces* (2010). Pattern catalog including disclosure patterns.
- **Cooper, A. et al.** *About Face* — chapter on disclosure and density.

## Closing

Progressive disclosure is among the best-understood and most-applied principles in modern UI design — and yet still routinely violated by surfaces that show everything, by accordions hiding the required, by "Advanced" tabs holding what should be primary. The discipline is not in knowing the pattern; it's in applying the editorial judgment of *what belongs where* on every surface.
