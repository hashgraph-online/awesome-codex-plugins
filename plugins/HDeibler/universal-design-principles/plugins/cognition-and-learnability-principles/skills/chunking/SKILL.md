---
name: chunking
description: 'Use this skill whenever the user must hold a sequence of items in working memory — phone numbers, OTP codes, account IDs, address strings, multi-step instructions, long forms, navigation menus with many items. Trigger when designing OTP / verification UIs, formatting numeric strings, breaking long forms into sections, grouping nav items, or reviewing surfaces that "have too many things at once." Chunking is one of the foundational principles in ''Universal Principles of Design'' (Lidwell, Holden, Butler 2003), grounded in Miller''s classic working-memory research.'
---

# Chunking

Chunking is the practice of grouping a long string of items into a smaller number of meaningful units, each containing a few items. The classic insight: working memory can hold only a handful of independent items, but each "item" can itself be a chunk containing several pieces. Phone numbers are easier to remember as `555-867-5309` (three chunks) than as `5558675309` (ten digits). The same principle applies broadly across UI design.

## Definition (in our own words)

Working memory is a small, short-lived store for the items the user is actively manipulating. Its capacity is roughly four to seven independent units. When information is presented as one long unbroken sequence, the user has to hold all of it as separate units and quickly hits the limit. When information is grouped into a few meaningful chunks, the same total content fits within the working-memory budget. Chunking is the design technique for fitting information to that budget.

## Origins and research lineage

- **George Miller**, "The Magical Number Seven, Plus or Minus Two: Some Limits on Our Capacity for Processing Information." *Psychological Review*, 1956, vol. 63, p. 81–97. The foundational paper. Miller observed that across many tasks (recalling lists, distinguishing tones, judging quantities), people maxed out at about 7 ± 2 items. The paper introduced "chunk" as the unit of measurement: an item could itself be made up of smaller items, but it counted as one chunk if treated as a unit.
- **Nelson Cowan**, "The Magical Number Four in Short-Term Memory: A Reconsideration of Mental Storage Capacity." *Behavioral and Brain Sciences*, 2001, vol. 24, p. 87–114. Refined Miller's estimate downward. Cowan's analysis found that when chunks are *truly* independent (not aided by rehearsal or grouping), capacity is closer to 4 ± 1 than 7 ± 2. The "magical number" is now usually given as 4.
- **Alan Baddeley**, *Working Memory* (1986) and *Working Memory, Thought, and Action* (2007). The standard reference work on the structure and limits of working memory.
- **Lidwell, Holden & Butler** (2003) compactly summarized the design implications and warned about misapplication: chunking is for tasks involving *memory*, not for tasks involving *scanning* (like consulting a reference list).

## Why chunking matters

When users must hold multiple items in mind — to dial a phone number, type a confirmation code, follow multi-step directions, complete a multi-part form — the amount they can hold determines whether they succeed. Exceeding working memory means they make mistakes, look back, or give up.

Chunking expands the effective capacity by packing more information into each chunk. A user can hold roughly 4 chunks; if each chunk contains 3 digits, that's 12 digits total — meaningful for phone numbers. Without chunking, 12 raw digits is well past the limit.

Chunking also accelerates learning: chunked patterns become familiar units (the "555" prefix becomes one chunk, not three) and free up capacity for new information.

## When to apply

- **Numeric strings the user must type or read** — phone numbers, OTP codes, account numbers, IDs, dates, currency.
- **Long forms** — group fields into named sections of 4–6 fields each.
- **Navigation menus** — group items into named sections of 4–7 items each.
- **Multi-step instructions** — break a 12-step process into three groups of four steps.
- **Tables with many columns** — visually group columns by category if they're related.
- **Dashboards with many widgets** — group widgets into themed regions.

## When NOT to apply

The book's specific warning: don't chunk reference content the user *scans* rather than *memorizes*.

- **Long lists the user filters or searches** — a contact list with 200 entries shouldn't be chunked into "Contacts A–E, F–J, K–O..." because the user isn't memorizing it; they're scanning or searching. Forced chunking adds visual noise without cognitive benefit.
- **Reference material the user looks up** — dictionary entries, documentation pages, settings pages where the user knows what they want. Search and clear labeling beat chunking.
- **Continuous prose** — chunking sentences into "first 4 words, next 4 words, next 4 words" damages reading. Body text follows its own rhythm.

The discriminator: are users *holding* the items in mind (apply chunking) or *finding* them (don't)?

## Optimal chunk size

Different sources give different numbers; the working consensus:

- **Each chunk: 3–5 items.** More than 5 risks overflow within the chunk.
- **Total chunks visible: 4–7.** More than 7 risks overflow across chunks.
- **For numeric strings: typically 3–4 digits per chunk.** Phone numbers, credit cards, OTP codes all converged on this.

These are heuristics; specific tasks may justify different sizes. The grouping should always be perceptually clear (visual gap, dash, slot separation).

## Worked examples

### Example 1: phone numbers

Most common chunking case. A 10-digit US phone number formatted three ways:

```
5558675309        ← unchunked: 10 digits, hard to verify or recall
555-867-5309      ← three chunks: 3-3-4
(555) 867-5309    ← same three chunks, with area code marked
555 867 5309      ← spaces instead of dashes
```

The chunked versions are easier to read aloud, easier to verify, easier to remember briefly. Most international phone formats follow similar logic.

### Example 2: OTP / verification codes

A 6-digit OTP entered into a single field is hard to verify mid-entry. Chunked input fields make each digit's position visible:

```html
<input type="text" inputmode="numeric" maxlength="6" />  <!-- unchunked -->

<!-- vs. chunked input -->
<div class="otp-input" role="group" aria-label="Verification code">
  <input type="text" inputmode="numeric" maxlength="1" />
  <input type="text" inputmode="numeric" maxlength="1" />
  <input type="text" inputmode="numeric" maxlength="1" />
  <span class="separator" aria-hidden>—</span>
  <input type="text" inputmode="numeric" maxlength="1" />
  <input type="text" inputmode="numeric" maxlength="1" />
  <input type="text" inputmode="numeric" maxlength="1" />
</div>
```

The chunked version (3-3) helps users verify they typed the right digits and matches the chunked format that's typically displayed in the originating email or SMS.

### Example 3: long forms broken into sections

A 24-field signup form is overwhelming. Group into 4 sections of ~6 fields each, with named headings:

```html
<form>
  <section>
    <h2>Account</h2>
    <!-- 5 fields: email, password, name, etc. -->
  </section>
  <section>
    <h2>Profile</h2>
    <!-- 4 fields: title, bio, photo, etc. -->
  </section>
  <section>
    <h2>Workspace</h2>
    <!-- 6 fields: workspace name, members, etc. -->
  </section>
  <section>
    <h2>Preferences</h2>
    <!-- 5 fields: notifications, language, etc. -->
  </section>
</form>
```

The user holds in mind "I'm in the workspace section" rather than "I'm at field 17 of 24." Each section is a manageable chunk.

### Example 4: navigation grouped by purpose

A sidebar with 18 nav items is hard to scan; grouped into 3 themed sections of 6 items each:

```html
<nav>
  <h3>Workspace</h3>
  <ul>
    <li><a href="/dashboard">Dashboard</a></li>
    <li><a href="/projects">Projects</a></li>
    <li><a href="/team">Team</a></li>
    <li><a href="/calendar">Calendar</a></li>
    <li><a href="/files">Files</a></li>
    <li><a href="/inbox">Inbox</a></li>
  </ul>
  <h3>Reports</h3>
  <ul>...</ul>
  <h3>Settings</h3>
  <ul>...</ul>
</nav>
```

Users learn the section structure quickly and use it to predict where things live.

### Example 5: address strings

An address string is a chunked structure even when displayed compactly:

```
1234 Main Street, Apt 5B
San Francisco, CA 94110
```

Two-line break separates "street" chunk from "city/state/zip" chunk. The internal commas chunk apartment from street and city from state from zip. Users parse and recall this far better than the same characters in one continuous line.

### Example 6: multi-step instruction

"To set up your account: Open Settings, click Notifications, choose Email, set frequency, save changes" — five steps in one sentence. Chunked as a numbered list:

```
1. Open Settings
2. Click Notifications
3. Choose Email
4. Set frequency
5. Save changes
```

Easier to follow; users can mark progress and look back at any step.

## Cross-domain examples

### Music

Western music notation chunks notes into measures (typically 3 or 4 beats). Beats group into bars; bars group into phrases; phrases group into sections. Musicians read music as nested chunks, not as individual notes.

### Reading

Skilled readers don't process individual letters; they process chunks (common letter combinations, then whole words, then phrases). Speed reading techniques are largely about recognizing larger chunks more efficiently.

### Chess

Expert chess players recall positions vastly better than novices — not because their working memory is larger, but because they chunk pieces into meaningful patterns (a defensive formation, an opening structure). De Groot's classic studies (1965) showed that experts and novices recalled random piece arrangements equally; the expert advantage came entirely from recognizing meaningful chunks.

### Telephone area codes

Area codes are mnemonic chunks that group geography into recognizable units. "212" is Manhattan; "415" is San Francisco. The numeric chunk doubles as a categorical signal.

## Anti-patterns

- **Chunking what should be searched.** Forcing a long list into chunks the user must navigate when search would do.
- **Chunks too large.** A "section" containing 20 items isn't a chunk; it's a list.
- **Chunks too small.** A "section" containing 2 items isn't worth its overhead. Combine.
- **Inconsistent chunk sizes within a sequence.** A 10-digit string chunked 5-2-3 is harder than 3-3-4 because the rhythm is irregular.
- **Visual chunking that contradicts logical chunking.** Visual separators in places that don't match meaning ("123-4567-89" is structurally awkward even if visually chunked).
- **Decorative grouping with no labels.** Grouping must be communicated via headings or visible regions. Just "putting space between things" without naming the groups misses the cognitive benefit.

## Heuristics

1. **Count chunks visible.** More than ~7? Reorganize or split.
2. **Count items per chunk.** More than ~5? Split that chunk.
3. **The "what's in this group?" test.** Can you name each chunk in 2–3 words? If yes, the chunking is meaningful. If no, the chunks are arbitrary; rethink.
4. **The scanning vs. memorizing diagnostic.** Is the user holding this in mind, or finding it? If finding, chunking may be noise; replace with search and clear labeling.

## Related principles

- **`performance-load`** — chunking is the canonical reduction of cognitive load.
- **`hicks-law`** — fewer visible options means faster decisions; chunking and Hick's Law often combine in nav design.
- **`progressive-disclosure`** — disclosure works *between* chunks (show one section, hide others); chunking works *within* the visible content.
- **`mnemonic-device`** — chunking is itself a mnemonic technique; explicit mnemonics layer on top.
- **`signal-to-noise-ratio`** (perception) — well-chunked content has less perceptual noise.
- **`proximity`** (perception) — proximity is the visual mechanism for showing chunks: closer items group, gaps mark boundaries.
- **`hierarchy`** (perception) — chunked content carries a hierarchy of structure (sections > items).

## Sub-aspect skills

- **`chunking-form-grouping`** — applying chunking to long forms.
- **`chunking-numeric-and-otp`** — applying chunking to numeric strings, OTP codes, and identifiers.

## Closing

Chunking is the cheapest cognitive lift available in design — it costs only structure, not new content. The discipline is recognizing when content is being held in working memory (chunk it) versus scanned for retrieval (don't add chunks; use search). When applied correctly, chunking turns "too much to hold" into "manageable."
