# Densification: research and patterns

A reference complementing `snr-densification` with research on optimal information density and case studies of density redesigns.

## Research on density

The density "right answer" depends entirely on the user's task and proficiency. A few findings worth knowing:

- **Bloomberg terminal users** (high-frequency professional traders) consistently reject "simplified" redesigns. Density is feature, not bug — a single screen showing 200+ data points outperforms a clean dashboard for the use case.
- **NN/g studies on dashboards** repeatedly find that under-dense dashboards force users to cross-reference multiple screens, increasing total task time even when each screen is faster to read.
- **Hick & Hyman**: decision time grows with options *visible at the moment of choice*. Forcing the user to navigate to find the option introduces a different cost (recall + Fitts's distance) that often exceeds the Hick's tax of just showing more.

The lesson: density isn't bad. *Disorganized* density is bad.

## What earns density

Densification works when:

- **A consistent grid holds the layout together.** High density without alignment is chaos.
- **Type and color reduce noise.** Smaller type, more neutrals, less ornament.
- **Repetition aids scanning.** Same column structure across rows lets the eye find the third column instantly.
- **Hierarchy ranks within the density.** Even a Bloomberg terminal has primary numbers and secondary metadata.

## Cross-domain examples

### Newspaper sports pages

A sports section's box scores are extreme density: dozens of players, multiple stats per player, multiple games per page. They work because:

- Strict columnar layout.
- Tabular numerals.
- Fixed type size, fixed row height.
- Consistent abbreviations (BB, RBI, HR).

Daily readers parse box scores in seconds. The density rewards practice.

### Aircraft cockpits

A 737 cockpit has hundreds of indicators. Pilots learn the layout as spatial memory; in an emergency they "fly to" the indicator without reading. The density is essential — separating the indicators across multiple screens would slow critical responses.

### IDE / code editor density

VS Code, JetBrains IDEs ship dense by default — file tree, editor, terminal, problems panel, debug panel — because expert users want it all visible. Casual users (Markdown editing, simple edits) often prefer a "Zen mode" — same software, lower density.

## When users complain about density

Two symptoms, two diagnoses:

- **"It feels overwhelming."** Probably *poor structure*, not too much content. Reorganize before reducing.
- **"I'm scrolling forever."** Probably *too sparse* — content is well-organized but spread out. Densify.

The wrong fix is usually applied to the wrong symptom: people densify "overwhelming" pages (making them worse) and de-densify "scrolling forever" pages (making *them* worse).

## Patterns

### The Bloomberg / spreadsheet pattern

Tabular layout, 16–24px row heights, tabular numerals, color-coded categories, sparse decoration. Use for: high-frequency power-user tools, monitoring dashboards.

### The Linear / Notion pattern

Single-column with strong hierarchy; modest density per screen but very fast inter-screen navigation. Use for: moderate-density apps where users move between objects more than they scan a single dense screen.

### The Slack / chat pattern

Vertical timeline with tight message spacing; sidebar for channels; many things visible at once. Use for: communication and stream apps.

## Resources

- **Few, S.** *Information Dashboard Design* (2006). Practical density-tuning for monitoring dashboards.
- **Tognazzini, B.** "First Principles of Interaction Design" — discusses density tuning across user types.
- **Refactoring UI** — chapter on density and breathability.

## Closing

Density is the only SNR move that adds rather than subtracts. The trick is to add *signal*, not chrome.
