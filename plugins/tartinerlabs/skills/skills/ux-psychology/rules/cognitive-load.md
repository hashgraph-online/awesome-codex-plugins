---
title: Cognitive Load
impact: HIGH
tags: memory, recognition, recall, complexity, chunking
---

**Rule**: People can hold only about four chunks in working memory. Let them recognise rather than recall, and never make them carry information from one screen to the next.

**Evidence**: Cowan 2001, "The magical number 4 in short-term memory" (*Behavioral and Brain Sciences*) — capacity is about 4 chunks, not Miller's often-quoted 7±2 (Miller 1956, *Psychological Review*, which was about memory span, never menu length). Sweller 1988, "Cognitive load during problem solving" (*Cognitive Science*) — extraneous load competes with the task. Nielsen's heuristic #6, recognition rather than recall. Reber, Schwarz & Winkielman 2004, "Processing fluency and aesthetic pleasure" (*Personality and Social Psychology Review*) — the easier something is to process, the more people like it, so low load is felt, not just measured.

### When Building

- **Show, don't make them remember** — keep the selected item, order summary, or earlier answers visible in later steps
- **Chunk** long numbers and codes (`4821 9930 1123`), long forms into labelled groups, and long flows into steps of a few decisions each
- **Recognition over recall** — recent items, suggestions, autocomplete, visible options instead of typed commands (expert shortcuts are an addition, not a replacement)
- **One task per screen** on mobile; on desktop, keep secondary information visually quieter than the task
- **Remove extraneous load** — decorative elements, duplicate labels, jargon, and unexplained abbreviations all compete with the task
- **Units and context next to numbers** — "3 seats left of 10", "+12% vs last week"
- **Cut before you hide** — remove content that serves no task on the screen; grouping and progressive disclosure are for what remains, not a way to tuck clutter behind a click
- **Budget interruptions** — toasts, badges, unread counts, banners, and modals on load each cost attention; too many teach users to ignore them all, including the one that matters. Interrupt only for what the user must act on now

### When Auditing

- A step that asks for something shown only on a previous screen (a code, an amount, a reference number)
- Instructions shown once and then removed while the user acts on them
- Screens mixing several unrelated tasks or decisions
- Unchunked codes and IDs the user must type or compare
- Content, widgets, or stats on a screen that no user task needs
- Badges, toasts, and banners that ask for attention but need no action

### Incorrect

```tsx
// Step 3 asks for the code that was only visible on step 1
<TextInput placeholder="Enter your reference code" />
```

### Correct

```tsx
<Text>Reference: <Text style={styles.mono}>KX4 92M</Text></Text>
<Button onPress={copyReference}>Copy</Button>
```

### Why This Matters

When working memory overflows, people make errors, slow down, or give up — and they experience it as "this app is confusing", not as a memory limit.

### Alternatives

Expert tools can rely on learned recall — keyboard shortcuts, command syntax, dense dashboards — because their users invest in learning them. Offer the recognition path alongside; never remove it for newcomers.
