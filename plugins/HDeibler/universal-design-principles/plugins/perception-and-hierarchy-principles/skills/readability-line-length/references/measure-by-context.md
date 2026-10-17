# Line length — measure by context

Specific line-length recommendations for different content types, contexts, and audiences.

## Book typography (print)

**Body prose:** 60–66 characters per line. The classic book measure, refined over centuries. A typical paperback page has a text block ~10–12 cm wide at 9–11pt body type, producing this range.

**Children's books:** 30–50 characters per line. Younger readers benefit from shorter lines that reduce the cost of finding the next line.

**Reference books / textbooks:** 60–75 characters. Slightly wider than narrative prose; readers are often scanning rather than continuously reading.

**Two-column books (newspapers, journals):** 35–50 characters per column. The narrower columns are necessary for the multi-column layout; readers adapt.

## Web (single-column body content)

**Articles and long-form posts:** 60–70 characters per line. The web's default contexts. Use `max-width: 65ch` or similar.

**Blog posts and newsletters:** 60–70 characters per line. Same as articles.

**Documentation:** 60–80 characters per line. Slightly more permissive because users often scan rather than read continuously, and code examples sometimes need wider lines.

**Product descriptions:** 50–70 characters per line. Often shorter because they're embedded in product cards or galleries.

**Marketing copy:** 50–70 characters per line. Marketing prose is read more carefully than UI text and benefits from comfortable measure.

## Web (UI text)

**UI labels and short text:** measure mostly doesn't apply (these are too short for line-length to matter). Focus on legibility.

**Helper text and longer UI explanations:** 60–80 characters per line. Treat like compressed body prose.

**Modal and dialog content:** 50–70 characters per line. Modals are usually narrower than the main content, so this is often automatic.

**Toast notifications:** 40–60 characters. Shorter because users often glance at toasts rather than read them carefully.

## Email

**Plain-text email:** 65–75 characters per line. Many email clients still wrap at 72 or 80 characters; design within this constraint.

**HTML email body:** 600px column width is the conventional desktop standard, producing roughly 70–80 characters per line at 14–16px text. On mobile this reflows to whatever width the client renders.

**Newsletter:** 600–700px column width with 16–18px body text gives 60–70 characters per line at desktop. Test across major email clients.

## Mobile

**Mobile body prose:** mobile screen widths (320–430px depending on device) constrain line length to roughly 30–50 characters at 16px text. This is just below the comfortable minimum, but mobile readers are accustomed to it.

**To get back into the comfortable range on mobile:** reduce font size slightly (to 15px), increase typeface character density, or accept the cramped feel.

**Mobile-first design:** start with the mobile constraint and ensure the line length grows comfortably as the screen widens (use `max-width` capped at 65ch).

## E-readers

**E-reader default:** typically 50–65 characters per line. Users can adjust font size and column width independently.

**The takeaway from e-readers:** they default to comfortable line lengths and let users tune. Web design that gives users this control (or sets sensible defaults) treats them with similar respect.

## Code

**Inline code (in prose):** follows the prose's line length.

**Code blocks (multi-line code):** 80–120 characters per line is typical. Code conventions in many languages (PEP 8 for Python, various ESLint rules for JavaScript) recommend 80 or 100 characters per line.

**Reason for wider:** code needs to maintain alignment and indentation. Wrapping mid-line breaks readability more than long lines do.

**For code blocks:** use horizontal scroll when lines exceed the available width, rather than wrapping. Provide a visible scroll cue.

## Tables and data

**Cell text within tables:** measure mostly doesn't apply for short cell values. For cells containing prose (descriptions, comments), consider capping width.

**Wide tables:** if individual cells contain more than ~50 characters of prose, consider whether the data should be in a different layout (a card view, a detail panel) rather than a table.

## Captions and footnotes

**Captions under images:** 30–50 characters per line typical. Captions are short and embedded; line length matters less than legibility and proximity to the image.

**Footnotes:** 60–80 characters per line. Similar to body prose.

## Forms

**Field labels and helper text:** measure mostly doesn't apply (these are too short).

**Long-form text fields (textarea):** the field's width is its measure. Aim for 60–80 characters per line in the input area for comfortable composition.

**Long-form previews:** if the form is generating content (a comment, a post), preview the text at the line length it will be displayed at, not the line length it's being typed at.

## Dashboards and analytics

**Numeric data:** measure mostly doesn't apply.

**Commentary and explanations:** treat like compressed body prose. 60–75 characters per line if the explanation is more than a sentence.

**Dashboard descriptions:** often appear in side panels or expanded detail views. 50–70 characters per line.

## Specialty contexts

**Subtitles / captions on video:** 32–42 characters per line is the broadcasting convention. Two lines max per subtitle. Designed for fast reading at video pace.

**Marquee / scrolling text:** measure doesn't apply (one continuous line, but read as it scrolls). Pace and contrast matter more.

**Augmented reality / heads-up displays:** very short measure (20–30 characters per line) because users are also processing the real-world view.

## Anti-patterns

**Designing only for desktop and shipping to mobile.** Desktop-comfortable measure becomes mobile-cramped without intervention. Verify both.

**Wide-screen layouts without max-width.** Modern monitors are wide; without a cap, body text gets very long. Always set max-width on prose containers.

**Justified text at narrow widths.** Justified text needs comfortable line length to distribute spacing well. At narrow widths, justification produces uneven spacing. Use left-aligned.

**Forgetting that ch units depend on the typeface.** `max-width: 65ch` produces different actual widths in different typefaces. Test the actual rendered line length.

**Two-column layouts at desktop that produce too-narrow columns.** A 1024px page split into two columns of 30–40 characters each is harder to read than a single column at 65 characters.

## Cross-reference

For paragraph rhythm and breathing room, see `readability-rhythm-and-prose`. For the parent principle, see `readability`.
