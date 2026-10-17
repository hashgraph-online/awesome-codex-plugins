# Prose layout patterns

Patterns for laying out specific kinds of long-form content, with notes on the rhythm choices that work for each.

## Pattern: long-form article

A 1500–5000-word article on a content site.

**Body type:** 17–20px serif or humanist sans-serif. Slightly larger than UI body text because the reader is committing to sustained reading.

**Line height:** 1.5–1.7×.

**Line length:** 60–70 characters (use `max-width: 65ch` or similar).

**Paragraph spacing:** 0.8–1em between paragraphs (visible breaks).

**Subheading frequency:** every 3–5 paragraphs. Use h2 for major sections, h3 for sub-sections within them.

**Structure:** single column, centered in the page, with significant whitespace on the sides.

**Interruptions:** minimize. Pull-quotes and inline images are fine; sticky banners and pop-ups disrupt reading.

## Pattern: documentation page

Technical documentation with prose, code blocks, and supporting content.

**Body type:** 15–17px sans-serif. Slightly smaller than article prose because the reader is often scanning for specific information rather than reading continuously.

**Line height:** 1.5–1.6×.

**Line length:** 60–80 characters for prose. Code blocks can extend wider (90–120ch).

**Subheading frequency:** every 2–4 paragraphs. Documentation is often heavily structured; subheadings double as in-page navigation targets.

**Code blocks:** use monospace, slight background tint, generous leading (1.5–1.6×). Add padding around code blocks (1em vertical space above/below).

**Callouts:** info, warning, tip boxes. Use sparingly; too many disrupt rhythm.

**Sidebar navigation:** common in documentation, with table of contents. Keep the body column centered or slightly left-of-center to maintain reading focus.

## Pattern: blog post

A 500–2000-word post on a personal or company blog.

**Body type:** 18–20px serif (for personal/editorial feel) or sans-serif (for company/product feel).

**Line height:** 1.5–1.7×.

**Line length:** 60–70 characters.

**Paragraph spacing:** 1em between paragraphs.

**Subheading frequency:** less critical than for long articles; can be optional for shorter posts. For posts over 1000 words, use h2 every 3–5 paragraphs.

**Author / date metadata:** subtle, not competing with the content. Smaller font, muted color, well above or below the prose.

## Pattern: email body

An email read in client UIs of varying widths and conventions.

**Body type:** 14–16px sans-serif. (Serif can render poorly in some email clients.)

**Line height:** 1.5×.

**Column width:** 600px is the conventional desktop standard. Mobile clients reflow to whatever width they render at.

**Paragraph spacing:** clear visible breaks (about 1em between paragraphs).

**Constraints:** email clients render CSS inconsistently. Use inline styles, simple layouts, and test in major clients (Gmail, Apple Mail, Outlook).

**No reliance on CSS-only effects:** background images, custom fonts, and complex layouts often fail. Design for the most conservative client and progressively enhance.

## Pattern: report or whitepaper

A long-form formal document, often viewed on desktop and printed.

**Body type:** 11–12pt serif (for print) or 16px serif (for web). Choose based on primary medium.

**Line height:** 1.4–1.5× (slightly tighter than blog prose; reports are often more formal).

**Line length:** 60–75 characters.

**Subheading frequency:** every 3–6 paragraphs. Reports often have rich hierarchy (chapters, sections, sub-sections).

**Footnotes and citations:** common; use a smaller size (10–12pt) and clear visual separation from body.

**Tables and figures:** common; ensure they're integrated with the prose layout, not floating awkwardly.

## Pattern: newsletter

A periodic email or web post combining multiple short pieces.

**Body type:** 14–16px.

**Line height:** 1.5×.

**Line length:** 60–70 characters per piece.

**Structure:** distinct sections per piece, with clear visual separation (subheadings, dividers, or extra spacing).

**Skimmability:** newsletter readers often scan more than read. Clear subheadings, brief introductions, and prominent links to "read more" support scanning.

## Pattern: transcript or chat log

Long-form conversational content.

**Body type:** 14–16px sans-serif.

**Line height:** 1.5×.

**Speaker attribution:** clear visual distinction (name in bold, in a colored badge, or aligned to one side).

**Paragraph spacing:** clear breaks between speaker turns.

**Time stamps:** subtle, not competing with the content.

**Reading rhythm:** transcripts often have a different rhythm than article prose — short turns, frequent speaker changes, sometimes pauses or interruptions noted. Layout should accommodate this naturally.

## Pattern: book / e-book

Long-form sustained reading.

**Body type:** 16–20px serif (print convention transferred to digital).

**Line height:** 1.5–1.7×.

**Line length:** 50–65 characters.

**Paragraph spacing:** can use first-line indents (book convention) or block paragraphs with space (web convention).

**Margins:** generous on all sides; the text block should feel framed by white space.

**Chapter structure:** clear chapter breaks with visual emphasis (page break in print; significant vertical space online).

**User control:** allow users to adjust font size, line height, and column width. Different readers want different settings.

## Pattern: dashboard with explanatory text

A data dashboard that includes paragraphs of context or commentary.

**Body type:** 14–15px sans-serif (matches UI text).

**Line height:** 1.5×.

**Line length:** 60–80 characters; cap with max-width even if the container is wider.

**Position:** explanatory text should be near the data it explains, not in a separate panel.

**Length:** keep prose short; dashboards are scanned, not read. Long explanations should be expandable ("read more") rather than always-visible.

## Pattern: terms of service / legal document

Long-form formal content that users sometimes need to actually read.

**Body type:** 14–16px sans-serif.

**Line height:** 1.5×.

**Line length:** 65–75 characters.

**Hierarchy:** rich. Numbered sections, sub-sections, sub-sub-sections. Each level visually distinguished.

**Tables of contents:** essential. Users navigate to specific sections; provide jump links.

**Subheadings:** every few paragraphs at minimum. Long unbroken sections of legal prose are notoriously bad to read.

**Plain-language summary at top:** supports reading by giving users the gist before they decide to read the details.

## Pattern: FAQ

Question-and-answer pairs.

**Question:** 16px medium weight, slightly larger than the answer.

**Answer:** 15–16px regular weight, 1.5 line height.

**Spacing:** 0.5em between question and answer; 2em between Q+A pairs.

**Structure:** consider grouping questions by topic with subheadings, especially for FAQ pages with more than 10 questions.

**Search or filter:** for FAQ pages with many questions, provide a search or category filter.

## Anti-patterns

**Reusing UI text settings for long prose.** UI text is calibrated for short, scannable text. Long prose needs different settings (larger size, more leading, more breathing room).

**Reusing print typography for digital.** Print uses tighter leading and smaller text than digital reading can support comfortably. Calibrate for the medium.

**Forgetting mobile.** Long-form layouts often look great on desktop and break on mobile. Test reading experience at all the widths your users will use.

**Burying the article in chrome.** Sticky headers, sidebars, ads, and pop-ups all reduce reading focus. Long-form deserves a clean reading experience.

## Cross-reference

For line length specifically, see `readability-line-length`. For the parent principle, see `readability`.
