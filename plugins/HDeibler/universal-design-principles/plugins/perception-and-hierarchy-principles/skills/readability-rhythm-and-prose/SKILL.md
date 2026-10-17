---
name: readability-rhythm-and-prose
description: 'Apply paragraph rhythm and prose-level readability — calibrating leading, paragraph spacing, subheading frequency, and visual breathing room so that long-form text reads smoothly without fatigue. Use when designing article layouts, documentation, reports, transcripts, or any context with sustained prose. Beyond line length and legibility, the rhythm of prose layout — the rest points provided by paragraph breaks, the hierarchy provided by subheadings, the breathing room provided by margins — determines whether readers stay engaged with long content.'
---

# Readability — rhythm and prose

Beyond line length, readability is determined by the rhythm of prose layout: the spacing between lines, the spacing between paragraphs, the frequency of subheadings, the visual breathing room around the text. Together these create a reading experience that either flows or stutters, that either invites continued reading or discourages it.

The right rhythm makes long content feel approachable. The wrong rhythm makes the same content feel like a wall.

## Leading (line height) for prose

Leading is the vertical space between baselines of consecutive lines. For body prose:

**1.5× to 1.7×** the font size is the comfortable range. So 16px text needs 24–28px line height; 18px text needs 27–31px line height.

Why this range:

- Tighter than 1.4× makes ascenders and descenders crowd, the eye drift to adjacent lines, and reading slow.
- Looser than 1.8× makes lines feel disconnected from each other; the prose breaks into discrete strips rather than flowing.
- The comfortable range balances visual flow (lines connected enough) and visual separation (lines distinct enough).

For UI and dense text (tables, captions, helper text), tighter leading (1.3–1.4×) is often appropriate because the text is shorter and scanned rather than read continuously.

For display sizes (headlines, hero text), tighter leading (1.0–1.2×) keeps the headline feeling unified.

## Paragraph spacing

The space between paragraphs creates the rest points that prose depends on. For body prose:

**0.75em to 1em** of vertical space between paragraphs (in addition to the line-height of the last line of the previous paragraph). So 16px text typically has 12–16px of space between paragraphs.

This makes paragraph breaks visible from a distance — the reader can see paragraph structure even when scanning. Without enough space, paragraphs blur together visually.

The alternative pattern (used in print books) is first-line indent: each new paragraph starts with a small indent (typically 1em) and there's no extra space between paragraphs. This is appropriate for traditional book layouts but rare on the web; block paragraphs with space between are the modern web convention.

## Subheading frequency

Long content needs structural breaks beyond paragraphs. Subheadings provide:

**Structural navigation.** The reader can scan the subheadings to understand the article's structure and find the section they want.

**Visual rest.** A subheading creates a break point that gives the eye a moment to recover before continuing.

**Cognitive chunking.** Each section under a subheading is a discrete unit that the reader can process and set aside.

Frequency: **every 3–5 paragraphs is a comfortable rhythm** for most prose. Articles longer than ~500 words benefit from at least one subheading. Articles longer than ~1500 words need multiple levels of hierarchy (h2 sections, possibly h3 subsections).

## Visual breathing room

The space around the text block matters too:

**Margins.** Body prose should have visible margins on all sides, not just left and right. Padding above and below the article, not just within paragraphs.

**Container structure.** Article layouts work best when the prose has a clear single-column structure with little visual competition. Sidebars, ads, and pop-ups all reduce reading focus.

**Section breaks.** Major sections within an article can have additional vertical space, decorative dividers, or other visual signals that mark a transition.

## Other rhythm considerations

**Sentence length variety.** Not strictly typography, but related to perceived rhythm: prose that varies sentence length feels more readable than prose with all-similar sentences. (This is the writer's job, not the designer's, but layout can support it by not breaking sentences awkwardly with hard line breaks.)

**Word and character spacing in prose.** Use the typeface's defaults; don't tweak letter or word spacing for body prose unless you have a specific reason. The typeface designer has already calibrated these.

**Drop caps and pull quotes.** Editorial conventions that can punctuate long prose, but use sparingly. Heavy use feels overdesigned; light use can mark the start of a major section or highlight a key passage.

## Diagnosing rhythm problems

Symptoms of prose-rhythm issues:

**The page feels intimidating before reading starts.** A wall of text without visible structure. Add subheadings, more paragraph breaks, or more vertical breathing room.

**Reading time drops sharply over content length.** Readers fatigue earlier than the content warrants. Likely too-tight leading, too-long paragraphs, or insufficient subheadings.

**Readers complain that the content "feels long" even when it isn't.** A 1000-word article that feels like 3000 words. Often a rhythm problem; the content is fine but the layout doesn't break it up enough.

**Users reach for reader mode.** They're invoking the browser's tool for the reading experience your design failed to provide.

## Worked examples

### A blog post layout

A blog post container: 18px Georgia body type with 1.6 line height (29px), 65ch max-width, 0.8em paragraph spacing (~14px), subheadings (h2 in 24px) every 3–5 paragraphs, generous vertical margin around the article (4em above and below).

The reader can scan the subheadings to see the article's structure. Within each section, paragraphs are 3–5 sentences with comfortable spacing. The eye flows down the page without effort.

### An article with poor rhythm

A 2000-word article: 16px text with 1.2 line height (default browser), no max-width (full container width), single paragraphs of 10+ sentences with no spacing between, no subheadings. The page is one continuous block of text.

Readers open the article, see the wall, and leave. Even those who try to read tire quickly. The content may be excellent; the rhythm has destroyed it.

The fix: bump line-height to 1.6, cap max-width to 65ch, break paragraphs into 3-5 sentences each with visible spacing, add subheadings every 3–5 paragraphs.

### A documentation page

Documentation typically has more interruptions than article prose: code blocks, callouts, lists, tables. The rhythm needs to accommodate these.

A pattern that works:

- Body prose at 16px / 1.6 leading / 0.8em paragraph spacing / 65ch max-width.
- Code blocks at 90ch max-width with 1em vertical space above and below.
- Callouts (info, warning) with their own background tinting and 1em margins.
- Subheadings (h2, h3) with extra space before to create clear section breaks.

The result is a page that flows through prose, pauses for code or callouts, and resumes prose with clear visual boundaries.

### A FAQ layout

A FAQ page is structurally a sequence of question-answer pairs. Treat each Q+A as a distinct chunk:

- Question: 16px medium weight, with 1em margin below to attach answer.
- Answer: 16px regular weight, 1.5 line height, indented or visually distinct.
- Between Q+A pairs: 2em vertical space.

The rhythm makes the page scannable (jumping between questions) and readable within each answer.

## Anti-patterns

**Tight leading on body prose.** Browser default (~1.2) is too tight for sustained reading. Set explicit line-height for prose containers.

**No paragraph spacing.** Paragraphs visually merging together is one of the fastest ways to make prose feel impenetrable.

**No subheadings in long content.** Long articles without structural breaks are walls of text. Add hierarchy.

**Paragraphs that are too long.** A 12-sentence paragraph is intimidating regardless of layout. Shorter paragraphs (3–5 sentences) feel more approachable. (Writer's job, but designers can encourage by leaving room.)

**Text crammed into the available container.** No margin around the article, no space between sections. The text feels claustrophobic.

**Animation or interaction during reading.** Sticky headers, scroll-triggered animations, pop-ups during reading all interrupt rhythm. Long-form reading deserves a quiet layout.

**Justified text without proper hyphenation.** Justified text without good hyphenation produces uneven word spacing — "rivers" of white space that disrupt reading rhythm.

**Lists of bullet points used as a substitute for prose.** Bullet points break rhythm; they're lists, not prose. Use them when the content is genuinely a list, not as a way to avoid writing connected prose.

## Heuristic checklist

Before shipping long-form content, ask: **Is the leading at least 1.5× the font size for body prose?** Tighter is uncomfortable. **Is paragraph spacing visible from a distance?** It should clearly mark paragraph breaks. **Are there subheadings every 3–5 paragraphs?** Long content needs structural breaks. **Does the article have visible breathing room around it?** Cramped layouts cost reading comfort. **Does the page have any interruptions during reading?** Sticky headers, animations, pop-ups all disrupt rhythm; minimize during reading flow.

## Related sub-skills

- `readability` — parent principle on sustained-reading ease.
- `readability-line-length` — sibling skill on measure (line length).
- `chunking` — paragraphs and subheadings chunk content into readable units.
- `hierarchy` — subheadings express structural hierarchy.
- `signal-to-noise` — clean prose layouts maximize signal.

## See also

- `references/prose-layout-patterns.md` — patterns for specific kinds of long-form content.
