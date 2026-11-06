# ASO Benchmarks: How to Use Them

Third-party ASO benchmarks (category conversion rates, rating lift, video lift,
screenshot scroll rates) come from vendor panels with different markets,
traffic sources, and definitions. They shift every year and rarely publish
methodology. Suede rules:

1. **Never score a listing against a vendor benchmark.** Scores come from the
   rubric in `scoring-criteria.md` and the listing evidence.
2. **Never quote a benchmark number to a client** unless you re-checked the
   source, its date, market, and definition in this session. Name all four.
3. **The user's own console data beats any benchmark.** App Store Connect
   (impressions, product page views, conversion rate by source, Product Page
   Optimization results) and Play Console (store listing acquisitions,
   conversion by source and country, store listing experiments) are the
   baseline for every target.

## Directional patterns that hold across sources

These are safe to state as tendencies, not as numbers:

- **Ratings**: conversion and featuring eligibility both suffer below roughly
  4 stars, and the first visible reviews shape trust. Prompt for ratings at
  moments of success, within platform limits (Apple: system prompt at most 3
  times per 365 days).
- **First impression**: most visitors decide from the icon, title, subtitle or
  short description, and the first two or three screenshots. Optimize those
  before anything below the fold.
- **Video**: on iOS, app previews autoplay muted, so the first seconds carry
  the message. On Google Play, the video does not autoplay in the listing and
  far fewer visitors watch it; weight effort toward screenshots there.
- **Screenshots**: one benefit per screen, captions in the searcher's words,
  outcome first. Order matters more than count past the first few.
- **Custom pages**: Apple custom product pages and Google Play custom store
  listings let traffic from ads, keywords (Apple), or countries see matched
  messaging. Measure each against the default page in console.
- **Events and promotional content**: Apple in-app events and Google Play
  promotional content can earn extra placements while active; the lift ends
  when the event ends.
- **Experiments**: treat small differences as noise. Use the console's own
  confidence reporting (Apple Product Page Optimization, Play store listing
  experiments) and run long enough to cover weekday and weekend traffic.

## Official figures worth knowing

- Google Play: apps with promotional content that gets featured saw "over twice
  as many explore acquisitions during featuring" (Google Play Console help,
  promotional content). Re-check the page before quoting.
- Android vitals: bad-behavior thresholds (user-perceived crash rate 1.09%,
  ANR rate 0.47% overall; 8% per device) can reduce visibility. See
  `google-play-specs.md`.

## Building a client benchmark set

When the user needs targets, build them from:

1. Their own trailing 90 days in App Store Connect or Play Console, by source.
2. Two or three named competitors' public listing facts (rating, rating count,
   screenshot count, update recency), captured with a date.
3. Any third-party figure only with source, date, market, and definition, and
   labeled as external context.
