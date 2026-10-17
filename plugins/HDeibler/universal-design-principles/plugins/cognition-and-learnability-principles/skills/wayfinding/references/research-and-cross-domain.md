# Wayfinding: research and cross-domain reference

A reference complementing the `wayfinding` SKILL.md with the academic grounding from environmental psychology and architecture, and a wider range of cross-domain examples.

## Research lineage

- **Kevin Lynch**, *The Image of the City* (MIT Press, 1960). The foundational text — Lynch interviewed residents of Boston, Jersey City, and Los Angeles to understand how they navigated their cities, and identified five elements of the cognitive map: **paths** (channels of movement: streets, walkways, transit lines), **edges** (boundaries that aren't paths: shorelines, walls, railroad cuts), **districts** (sections with shared character: a neighborhood, a downtown), **nodes** (focal points: junctions, plazas, transit stops), and **landmarks** (singular reference points: a tower, a statue, a distinctive building). These five categories still organize wayfinding research, and they map to software almost without translation: paths = navigation flows; edges = section boundaries; districts = sub-sections of an app; nodes = pages with many incoming and outgoing links; landmarks = distinctive pages or features users remember.
- **Romedi Passini**, *Wayfinding in Architecture* (Van Nostrand Reinhold, 1984). Translated Lynch's urban concepts into architectural design. Passini's framework explicitly covers indoor wayfinding — hospitals, airports, large public buildings — and is more directly applicable to software than Lynch's outdoor focus.
- **Paul Arthur and Romedi Passini**, *Wayfinding: People, Signs, and Architecture* (McGraw-Hill, 1992). The standard reference work; covers signs, maps, environmental cues, and the cognitive processes of wayfinding.
- **Roger Downs and David Stea**, *Cognitive Maps and Spatial Behavior* (Aldine, 1973). The cognitive-mapping research tradition: how people internally represent the spaces they navigate.
- **Steve Krug**, *Don't Make Me Think* (New Riders, 2000, 2014). The most-cited application of wayfinding to web design. Krug's "trunk test" — can a user landing on any page identify what site they're on, what page they're on, and what their main options are — is wayfinding distilled to a usability heuristic.
- **Lidwell, Holden & Butler**, *Universal Principles of Design* (Rockport, 2003), articulated the four-stage model (orientation, route decision, route monitoring, destination recognition) that compactly summarizes the wayfinding literature for designers.

## Lynch's five elements applied to software

| Lynch's element | Physical example | Software equivalent |
|---|---|---|
| **Paths** | Streets, sidewalks, transit lines | Primary navigation routes; the most-traveled flows through your IA |
| **Edges** | Shorelines, walls, railroads | Section boundaries; the line between marketing site and app, between free and paid, between domains |
| **Districts** | Neighborhoods, downtowns | Major sections of the app: Dashboard, Settings, Reports |
| **Nodes** | Plazas, transit hubs, intersections | Highly-connected pages: home, dashboard, search results |
| **Landmarks** | Distinctive buildings, statues | Memorable pages or features: the dashboard's primary KPI, the empty-state mascot, the unique feature page |

A productive design exercise: list each of these five for your app. If any category is empty (no clear landmarks, no nodes, no district boundaries), wayfinding is likely weak.

## Cross-domain examples

### Hospital wayfinding — high stakes, high-stress users

Hospitals are the canonical wayfinding-failure context. Visitors are anxious or unwell, often arriving for appointments at unfamiliar departments. Bad hospital wayfinding has measurable costs: late appointments, no-shows, confused emergency arrivals.

What works:

- **Color-coded zones.** Cardiology = blue, Oncology = green, etc. Color carries categorical information for users in low-bandwidth states.
- **"You are here" maps at every elevator landing.** Orientation made explicit at the most disorienting transitions.
- **Distinct landmarks at decision points.** A sculpture, a glass wall, a colored floor — perceptual cues that survive missed signs.
- **Greeters and information desks** as a redundant human wayfinding system.

Software lessons: clear section identity (color, icon), maps available at transitions (sitemap, breadcrumb on every page), distinct visual landmarks per section, and search/help as the human-greeter analog.

### Airport wayfinding — universal vocabulary

Airports succeed where hospitals struggle, partly because:

- **Small, repeated vocabulary.** Departures, Arrivals, Baggage Claim, Gates A/B/C. Users learn the vocabulary in one airport and apply it everywhere.
- **Frequent sign repetition.** No decision point lacks a sign.
- **Universal pictograms** that survive language barriers.
- **Multi-height signage** so signs are visible above crowds.

Software lessons: limit IA vocabulary; repeat orientation cues frequently; use universal iconic representations; place chrome where users look (typically top edge of viewport).

### Theme parks — wayfinding through architecture

Disney parks deliberately use sightlines and "weenies" — a Walt Disney term for distinctive structures placed at the end of paths to draw guests forward. Cinderella's Castle is the canonical weenie at Disneyland; the Tree of Life at Animal Kingdom does the same job.

The wayfinding is invisible because the architecture *is* the wayfinding. Visitors don't read signs to find the castle; the castle is visible from many vantage points and visually pulls them.

Software equivalent: a well-designed home page or landing screen shows users where they can go without explicit instruction. The visual hierarchy *is* the wayfinding.

### Universities — established district / landmark wayfinding

University campuses combine all of Lynch's elements: paths (walkways), edges (campus boundary, the bridge between the two halves), districts (the science quad, the humanities quad), nodes (the student union, the library), landmarks (the bell tower, the chapel, the unusual statue). Veteran students navigate by spatial memory; new students by signs and maps; both can succeed.

Software equivalent: experienced users navigate by muscle memory and keyboard shortcuts; new users by visible nav and search; both should succeed.

### Conference centers — temporary wayfinding

Conference signage solves a temporary version of the wayfinding problem: attendees who don't know the venue, navigating by session names that change room hourly. What works:

- **Master schedule maps** posted at central nodes.
- **"Now playing" indicators** outside each room.
- **Wayfinding apps** that show your personal schedule with directions.

Software equivalent: dynamic "what's happening here" indicators (notifications, in-app tutorials), personalized navigation based on user state.

## Quantitative findings worth knowing

- **Visitor surveys at large hospitals** consistently find ~30% of first-time visitors get lost on their way to appointments without staff intervention. Investments in wayfinding signage measurably reduce this.
- **Web wayfinding studies** (NN/g and others) show that users abandon sites within 10–20 seconds when they can't orient. Strong wayfinding chrome correlates with lower bounce rates.
- **Krug's "trunk test"** — open a random page; can you identify the site, page, section, primary actions in <5 seconds — fails on a substantial percentage of B2B SaaS apps that haven't invested in wayfinding chrome.

## Edge cases

### Wayfinding without a hierarchy

Some apps have *flat* IA — a single workspace, a single timeline, an inbox. Wayfinding still applies: orientation (where in the timeline?), route decision (filter, search, scroll), route monitoring (scroll position, "you're at the top"), destination recognition (you found the message you wanted).

The four-stage framework adapts; the navigation chrome is different.

### Wayfinding in agent-driven and AI interfaces

When an LLM or agent acts on the user's behalf and surfaces results, the user has *no path memory* for how they got there. Wayfinding implications:

- Agents should narrate ("I navigated to Settings → Notifications and changed the frequency").
- Results should include source paths so the user can verify.
- Recovery (undo, "show me what you did") is critical because the user didn't construct the path themselves.

### Wayfinding in voice interfaces

Voice has no visual chrome; orientation is purely auditory. Patterns:

- **Confirm location at the start of every interaction** ("You're in Settings.").
- **Echo state changes** ("I've changed your notification frequency to weekly.").
- **Always provide an exit** ("You can say 'main menu' to go back.").

## Resources

- **Lynch, K.** *The Image of the City* (1960). Short, readable, foundational. Worth a weekend read.
- **Arthur, P. & Passini, R.** *Wayfinding: People, Signs, and Architecture* (1992).
- **Krug, S.** *Don't Make Me Think* (2014, 3rd ed.). Web-applied wayfinding.
- **Garrett, J. J.** *The Elements of User Experience* (2010). The IA layer that wayfinding sits on top of.
- **NN/g articles on navigation** — many publicly available studies and writings.
- **Calori, C. & Vanden-Eynden, D.** *Signage and Wayfinding Design* (2015). Practical wayfinding-design reference for physical environments.

## Closing

Wayfinding is one of the cleanest cross-domain transfers in design. The same four stages apply to a hospital corridor, a museum, a university campus, an airport, a Trello board, a Notion workspace, a settings panel. The discipline is *not* in inventing new patterns — most patterns are well-established. It's in *using* them: putting orientation chrome on every page, naming things consistently, providing search as recovery, and noticing when a user gets lost (which is the bug, not the feature).
