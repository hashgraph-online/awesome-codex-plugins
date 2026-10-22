# Distribution, Pricing, And Launch Plan

Save the plan to `publishing/launch-plan.md`. Every choice here belongs to
the author; lay out the trade-offs and record the decision. Royalty rates,
fees, and program terms change: treat every figure as a starting point and
have the author check the retailer's current terms.

## Plan File

```markdown
---
type: launch-plan
story: {story-id}
updated: YYYY-MM-DD
---

# Launch Plan: {Title}

## Decisions

- Formats: {ebook, paperback, hardcover, audio}
- Distribution: {routes}; exclusivity: {KDP Select or wide}
- Launch date: {publication-date}; preorder: {yes/no, from date}
- Prices: {format and territory: price}

## Timeline

| Date | Task | Owner | Status |
|------|------|-------|--------|

## Ad Tests

| Start | Platform | Variable tested | Budget | Stop rule | Result |
|-------|----------|-----------------|--------|-----------|--------|

## Lessons
```

Status values: `todo`, `doing`, `done`, `dropped`. Fill Result and Lessons
only from what the author reports.

## Distribution

| Route | What it covers | Notes |
|-------|----------------|-------|
| **KDP** (Amazon) | Kindle ebook, paperback, hardcover | The largest ebook market in many countries. Optional KDP Select exclusivity for the ebook. |
| **IngramSpark** | Print (and ebook) to bookstores and libraries | Wider print distribution, returns and wholesale discount settings, hardcover options. Bookstores rarely stock POD titles without returns. |
| **Draft2Digital** and other aggregators | Ebook (and print, audio through some) to many retailers and library platforms | One upload, many stores; takes a share of royalties. |
| **Direct to retailers** | Apple Books, Kobo, Google Play, Barnes & Noble | Higher share than an aggregator, more dashboards. |
| **Direct sales** | The author's own store (with a delivery service such as BookFunnel for ebooks) | Highest margin and the customer's email; the author handles payments, tax, and support. |

A common print setup uses KDP for Amazon and IngramSpark for everywhere
else, with separate ISBNs or the same author-owned ISBN; check each
platform's current rules for sharing an ISBN.

### Outside the US and UK

The table above reflects the English-language self-publishing market.
Where the book's readers live, and what language it is in, change the
routes:

- **Amazon** publishes to its country stores (Germany, France, Spain,
  Italy, Japan, Brazil, Mexico, and others) through the same KDP account,
  but supports only some languages. Check KDP's current list of supported
  languages for the book's `language` before planning around it.
- **Kobo Writing Life** reaches Kobo and the partner stores Kobo supplies
  in several countries.
- **tolino media** publishes to the tolino stores in German-speaking
  countries (such as Thalia and Hugendubel).
- **Subscription services** (Storytel, BookBeat, Nextory) are a large
  share of ebook and audiobook reading in the Nordic countries and reach
  other markets; most take books through aggregators.
- **Regional aggregators and distributors** serve markets the US
  aggregators reach poorly. Ask the author what authors publishing in
  their language use, and check each one's current store list.

Some countries fix book prices by law (Germany and France among them,
for print and ebooks): the publisher sets one price that every retailer
charges, which changes how launch discounts and price promotions work.
Check the rules with the distributor or an author organization in that
market.

### Exclusivity

- **KDP Select / Kindle Unlimited:** the ebook must be exclusive to Amazon
  for each enrollment term (90 days, auto-renewing unless turned off). Print
  and audio are not covered. Pays per page read from a shared fund, plus
  promotion tools.
- **Wide:** the ebook sells everywhere, including libraries. Slower to
  build, less dependent on one company's program changes.
- Genres with heavy subscription readership (romance, some fantasy and
  thriller sub-genres) often do well in KU; others often do better wide.
  Look at what successful comparable authors do, and note that switching
  later is possible between terms.
- Exclusivity breaches (the ebook still live elsewhere, even a free
  sample chapter longer than allowed) can cost the account. Check the
  current terms before enrolling.

## Pricing Considerations

There is no formula. Weigh:

- **Comparable books:** what successful books in the same sub-genre and
  length charge, in the same format.
- **Royalty bands:** some retailers pay a higher rate only within a price
  band (KDP has long paid its higher ebook rate only between about $2.99
  and $9.99). Check the current band before pricing outside it.
- **Print cost floor:** the printer's print cost plus its share sets the
  minimum list price. Page count and trim drive the cost; get it from the
  printer's calculator after the PDF is final.
- **Series strategy:** a lower-priced or free first book can feed later
  books; it only pays if read-through is real. Track it.
- **Territories:** set local prices rather than accepting automatic
  conversion (a converted price like 4.37 looks odd). Where the law fixes
  book prices, one price applies at every retailer; see Outside the US
  and UK.
- **Launch pricing:** a discounted launch or preorder price can help
  rank; plan when it ends.
- Taxes (VAT, sales tax, withholding) affect list prices and income. That
  is for the author's accountant, not this skill.

## Timeline

Adjust to the author's date. Record each task with an owner and a date.

### T-90 to T-60

- Final manuscript locked; copyedit and proofread scheduled.
- Cover commissioned or final; `cover-alt` written.
- Metadata filled and the metadata sheet clean; ISBNs assigned.
- Decide distribution and exclusivity. Set up preorders if using them
  (check each retailer's preorder deadlines and penalties).
- Reader magnet chosen: a short story, novella, or bonus scene offered for
  newsletter sign-up. It should be in the same genre and voice as the book.
- Newsletter service chosen; welcome sequence drafted. Only email people
  who opted in, and follow the email and privacy law that applies to the
  author's readers.

### T-60 to T-30

- ARC team recruited. Options: BookFunnel (delivery and sign-up pages),
  BookSprout (review team management), NetGalley (librarians, booksellers,
  reviewers; costlier, sometimes shared through co-ops). Recruit from the
  newsletter first.
- ARC copies built with `story build . --format epub` from the final
  text; note that an ARC may still carry typos.
- ARC reader instructions: when to review, where, and the retailer's rule
  on disclosing a free copy. Never ask for positive reviews, pay for
  reviews, or trade reviews; retailers remove them and can penalize the
  account.
- Street team (the most engaged readers) given shareable graphics,
  quotes, and dates.
- Retailer copy final; A+ or enhanced content prepared.
- Print proof ordered and read.

### T-30 to T-1

- Final files uploaded before the retailer's deadline; previews checked
  on the live page.
- Newsletter: cover reveal, excerpt, preorder link.
- Ads prepared (see Ads); nothing spends until launch unless preorders
  are a deliberate target.
- Launch-day email and social posts drafted.

### Launch Week (T0 to T+7)

- Launch email; street team posts; ARC readers reminded to post.
- Check every retailer page: price, description, series link, look inside.
- Start ad tests.
- Record daily sales and rank only if the author finds it useful; the
  numbers that matter come later.

### T+7 to T+30

- Ads: cut losers, scale winners slowly (see Ads).
- Back-matter call to action checked: every book ends with a newsletter
  link and a link to the next book.
- Consider a price promotion or a promo newsletter feature once reviews
  have accumulated.
- Write down what worked for the next launch.

## Ads

- **Amazon Ads:** sponsored products on Amazon search and product pages.
  Start with automatic targeting to discover search terms, then move
  proven terms and competing books into manual campaigns.
- **Meta (Facebook and Instagram):** audience targeting and creative-led;
  works best when the ad image and first line sell the trope or hook.
- **BookBub Featured Deals** are editorially selected promotions of a
  discounted or free book to BookBub's lists; the author applies and pays
  only if accepted. **BookBub Ads** are self-serve ads to the same readers,
  bought by bid, with no editorial gate. They are different products.
- Other promo newsletters sell discount features; results vary widely.

### Testing Discipline

- Set a total test budget the author can lose without harm, and a daily
  cap.
- Change one thing at a time: image, headline, targeting, or price.
- Decide the stop rule before starting: for example, stop an ad after a
  set spend with no sale, or when its cost per sale exceeds the book's
  royalty plus expected read-through.
- Judge on read-through for series: a first book can lose money on ads
  and the series still profit, only if later books sell.
- Give each test enough spend and time to mean something, then record the
  result in `publishing/launch-plan.md`.
- Ads do not fix a weak cover, blurb, or first chapter. If clicks do not
  turn into sales, fix the page before spending more.
