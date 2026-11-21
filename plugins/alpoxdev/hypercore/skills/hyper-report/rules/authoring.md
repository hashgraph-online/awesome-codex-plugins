# Authoring the report

The report earns its page count. Every section either moves the reader toward the decision in the brief or gets cut.

## 1. The brief block

Fix five things before the first sentence. They become the opening of the source file, not a separate planning document.

| Field | Question it answers | Bad answer | Good answer |
|---|---|---|---|
| Decision | What does the reader do after reading? | "Understand the market" | "Approve the A plan at the 8-week scope" |
| Audience | Who reads it, and what do they already know? | "Stakeholders" | "The CFO, who knows the budget but not the technical constraints" |
| So what | What changes if they believe you? | "It is informative" | "We stop spending on B and move the team to A" |
| Evidence base | What can you actually show? | "Research" | "Three vendor quotes, our Q3 numbers, two customer interviews" |
| Budget | How long may it be? | "As long as needed" | "Five A4 pages, one page of appendix" |

An unanswerable field is a finding, not a blocker: write the best answer, mark it as assumed, and say so in the delivery note.

## 2. The shape of the document

```
Cover            title, subtitle, audience, date, author
Conclusion       the answer, in the first page, in plain sentences
Key numbers      at most four figures that carry the conclusion
Body             one message per section, each opening with its own conclusion
Evidence         tables, figures, quotes, each with a caption that interprets
Risks & limits   what would make the conclusion wrong
Next step        the single action the reader takes
Sources          every marker resolves here
```

### The conclusion block

Three to five sentences. State the recommendation, the reason, and the cost or condition. No throat-clearing, no restatement of the brief, no "this report examines".

> We should take plan A at an eight-week scope. It costs 1.2bn KRW against plan B's 0.9bn, but it ships in eight weeks instead of fourteen, and the two customer interviews put the delay cost above the price gap. The condition is that the design freeze holds to week three.

That paragraph is the whole report for a reader who stops there, and the rest of the document exists to defend it. Write it last if it helps, then move it to the front.

### Section shape

Every section repeats the pattern at its own scale:

1. **One-sentence claim** — what this section establishes.
2. **The evidence** — the table, figure, or quote that supports it.
3. **What follows** — the implication, one or two sentences.

A section that only reports findings without saying what follows is a data dump. A section that repeats the conclusion is padding.

### Section order

Order by what the reader needs to decide, not by the order you found things. If the reader must accept the cost model before the timeline matters, the cost model comes first even though the timeline was easier to research.

## 3. Tables

A table earns its place when the reader compares rows on the same columns.

- One idea per table. Two tables beat one table with a divider row.
- The compared quantity sits in a column, never in prose inside a cell.
- Numeric columns are right-aligned; the pipeline does this from the `---:` separator.
- Units live in the header, not in every cell: `Cost (KRW)` not `1,200,000,000원` eleven times.
- Round to the precision that changes a decision. Three significant figures is almost always enough.
- Never put a total row in a table of unrelated rows; if the rows sum, say what the sum means.
- A table with two columns and four rows is usually a sentence.

## 4. Figures

A figure earns its place when the shape of the data is the point: a trend, a distribution, a break, a ranking.

- Every figure has a caption that interprets it: what the reader should see, not what it is. "Churn falls sharply once onboarding drops under four minutes" beats "Churn by onboarding time".
- One message per figure. If the caption needs "and", split the figure.
- Never chart numbers that a table already gives. Pick one form per idea.
- Alt text describes the figure for a reader who cannot see it; the caption states the message.
- Charts are authored elsewhere and placed as an image file beside the source. The pipeline embeds the file; it does not draw the chart.

## 5. The one-page summary

The summary is the report compressed to exactly one page, and it is a separate authored file, not a truncation of the body.

```
Conclusion       two or three sentences
Key numbers      three figures, no more
What it rests on two or three bullets naming the evidence
What to do next  one sentence
Where to read    the page numbers of the three sections that matter
```

If the content does not fit one page, cut content; do not shrink type. A 7-point summary is unreadable in print and dishonest about its length.

## 6. What gets cut

Before delivery, delete each of these:

- The background section that restates what the reader already asked for.
- Any sentence that begins with the report talking about itself.
- Adverbs that soften a claim the evidence supports, and hedges that hide a claim the evidence does not support.
- The second example when the first one already made the point.
- Any number in the body that is not in the source list or measured here.
- The summary that repeats the conclusion verbatim instead of compressing it.

## Sources

> Checked 2026-11-13.

| Claim | Source |
|---|---|
| Conclusion-before-evidence structure, and one message per section | Barbara Minto, *The Pyramid Principle* — the ordering principle is referenced; no text was copied |
| Numeric-column alignment and unit placement in headers | <https://www.nngroup.com/articles/data-tables/> |
| Figure captions that interpret rather than label | <https://www.nngroup.com/articles/choosing-chart-types/> |
| One form per idea, and not charting what a table already states | This package's contract, stated in `rules/format-routes.md` |