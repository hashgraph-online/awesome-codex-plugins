# What the privacy page must say

The agent drafts this text; a lawyer reviews it before it goes live. Every
sentence must be true of the code and settings as built. Re-check it after
every change, and never call the data "anonymous" or the site "GDPR
compliant".

## Checklist

**1. Who and how to reach them.**

- The controller: a name or company, an address and a contact e-mail
  ("[controller], [address], [e-mail]").
- Where to object, ask or delete.
- The supervisory authority the visitor can complain to.

**2. What is measured, exactly.** List what k.js reports. Use the list below
and remove what the site does not use:

- the page you viewed;
- which parts of the page were on your screen, and for how many active
  seconds;
- how far you scrolled;
- the kind of link or button you clicked: within the site, to other sites,
  e-mail, phone, downloads, named buttons;
- clicks you made on things that are not links;
- whether you copied text (only whether an e-mail address was copied and
  how long the selection was, never the text);
- whether you printed the page;
- [only with `data-kform`] that a form (by its name, such as "contact")
  was sent, never what you wrote in it;
- whether you played a video;
- the site you came from (its address only) and the campaign tag; when you
  reach a goal (a sign-up, a booking), the kind of site the visit came from
  (a search engine, an AI assistant, social media, a newsletter, direct)
  is counted with it, never the site itself;
- [only with `data-consent-counts="on"`] whether the consent banner was
  shown and whether it was accepted, declined or withdrawn: counted per
  day, never tied to a visit, also after you accept, and not at all with
  Global Privacy Control or Do Not Track;
- your browser's language;
- [only with `data-errors="on"`] errors in the site's own scripts: the error
  message with quoted text, numbers, addresses and codes removed, the
  script's file name and line, and the page. Counted per day, never tied
  to a visit, even with consent; one example of each error is kept for
  [180 days];
- [only with `data-vitals="on"`] how fast the page loaded and answered
  (Core Web Vitals, as ranges such as "2.5 to 3 seconds", not exact
  values) and which part of the page was slowest. Counted per day and
  device type, never tied to a visit.

From the server: the country, as resolved by the hosting provider or CDN,
and the device type (phone, tablet, computer). Say what is **not** collected:

- no cookies, nothing stored in the browser (or exactly what is, see 7);
- no IP address stored by the collector. Say how long it is held in memory
  for abuse protection: about 10 minutes on a Node server; on serverless
  runtimes, until the instance is recycled (usually minutes). If PostHog or
  Umami is used, the IP also goes to them (see 5);
- no full user-agent string stored;
- nothing on private pages.

**3. The model, in plain words.**

- **A.** "We count totals: how many visits, from where, what was read. Nothing
  in them describes one visit."
- **B.** "Without your consent: only those totals. With your consent: a
  record of your visit (pages, time per part, clicks in order) kept for [N]
  days, [a recording of your screen with form fields hidden, through
  PostHog], [and a one-line summary posted to our team's Slack workspace]."
- **C.** "We follow one visit through the site using a visitor ID computed on
  our server from a shortened IP address and your browser's user agent with
  a secret key. It changes every day; without our key it cannot practically
  be turned back into an address, and visits on different days cannot be linked."

**4. Legal basis per purpose.**

- Consent for anything that waits for the banner (rows, replay, Slack lines),
  with how to withdraw it ("Privacy settings" at the bottom of every page).
- For what runs without consent (the totals in A and B, the visits in C):
  **the basis the owner chose with counsel.** Do not pick one for them. Two
  sets of rules apply:
  - **The ePrivacy rule** on reading from or storing on the device (EDPB
    Guidelines 2/2023, final version 2.0 adopted 7 October 2024, count a
    script that makes the browser send data, para 33). It
    needs consent unless an exemption applies, and a GDPR "legitimate
    interest" cannot replace that consent.
  - **The GDPR basis** for what is then processed.

  Write down the reasoning the owner settled on.
- Say plainly that Global Privacy Control and Do Not Track are honoured as
  a refusal. US state laws (California's CCPA regulations §7025, Colorado
  since 1 July 2024, and others) require honouring GPC for sale, sharing
  and targeted advertising; no EU law makes it a binding refusal. The skill
  treats it as one by choice, so word it as a promise, not a legal duty.

**5. Recipients and processors**, each with **everything it receives**:

- the host and CDN (IP addresses and request data, security cookies);
- the database provider;
- PostHog (EU Cloud): page views, clicks, heatmaps, dead clicks, [errors,
  only with `site.exceptions`] [page speed, only with `site.webVitals`], the
  **full IP** (forwarded by the proxy for the location lookup), and masked
  recordings. Say that PostHog drops the IP after deriving an approximate
  location only once the owner has confirmed "Discard client IP data" is on
  in the project settings; until then, it keeps it;
- Umami: the path, referrer site, language, the IP shortened to its /24
  (IPv6 /48) and the **full user agent**, from which it builds a visitor id
  that changes monthly;
- Slack: the visit lines, with exactly what a line contains;
- the e-mail provider.

Remove processors no code uses. Add one *before* the feature flag that
enables it goes on.

**6. Transfers outside the EEA.** For each US recipient: the EU-U.S. Data
Privacy Framework (if certified) or Standard Contractual Clauses, and "a copy
is available on request at <contact>".

**7. Cookies and browser storage, complete**, each with purpose and
lifetime. Grep the code for `document.cookie`, `localStorage` and
`sessionStorage`, and list what third-party scripts write (auth libraries
often set CSRF and callback cookies on the first page view). The analytics
entries:

| Name | Where | Purpose | Lifetime |
|---|---|---|---|
| `analytics-consent`, `analytics-consent-at` | localStorage | your answer and its date | until changed; asked again after [12 months] |
| `k-off` | localStorage | the site owner's own browsers (only when opened with `?k=off`) | until removed |
| `k-visit` | sessionStorage | only with `data-visit-store="session"` and consent: ties a visit's page loads together | until the tab closes or 30 idle minutes |
| `ph_<token>_posthog` + `ph_*` keys | cookie, localStorage | PostHog, only with consent | [1 year: check the PostHog setting] |
| `ph-fresh` | localStorage | marks that PostHog started fresh after consent | until withdrawal |
| `__ph_opt_in_out_<token>` | localStorage | remembers a withdrawal, so other open tabs stop too | stays after withdrawal; no identifier |

**8. Retention, a period for every store**, and how it is enforced. Write
the periods that are actually enforced (`retention.mjs`, Mongo TTL indexes,
`retentionStatus` shows the oldest day kept), not the ones intended:

- totals: 2 years (deleted daily, or by the database's TTL);
- rows: 180 days (the same);
- error examples (with `data-errors`): the rows' period, 180 days by default;
- deploy markers (a commit hash and a time, nothing about visitors): with
  the totals;
- Analytics Engine, if used: 3 months, fixed by Cloudflare;
- PostHog: recordings and events as the PostHog plan keeps them (e.g. 30
  days for recordings on some plans): check the plan, and update the text
  when it changes;
- Slack and e-mail copies: a real period. Slack visit lines are deleted
  after N days by `deleteOldSlackLines` (e.g. 30 or 90); e-mail copies need
  the mailbox's own rule;
- the IP in memory: about 10 minutes (Node), or until the serverless
  instance is recycled;
- the consent answer: 12 months.

"As long as necessary" is not a period.

Not about visitors, so not in the list of what is measured, but worth one
sentence if the owner wants to be complete: AI crawlers' requests may be
counted by the name they give (`crawlers.mjs`), without their address; and
Google Search Console's aggregated search figures may be stored for 16
months (`gsc.mjs`).

**9. Rights.** Access, deletion, objection and withdrawal. Note that data not
tied to a name may not be findable. Say how deletion really works:

- **Model B with the button:** "Under *Privacy settings* at the bottom of
  every page, *Delete my visit data* deletes the record of your current
  visit [in this tab] and withdraws your consent. Earlier visits used other
  random identifiers that your browser does not keep, so we cannot find
  them; they are deleted after [180 days]. The totals contain no
  identifier and are not affected." Name the button exactly as on the site.
  Add how recordings are deleted (on request, by e-mail) if PostHog is used.
- **Model C:** "Because the identifier changes every day and is computed
  from your network address and browser, we can delete only today's
  records, from the same network and browser [with the button on this
  page]. Older records are deleted after [N days]."
- **Without the button:** "write to us"; `assets/dsar.mjs` exports or
  deletes a visit when the visitor can give its id.
- **Analytics Engine:** records cannot be deleted before its 3 months.

**10. Changes.** The date of this version.

## Things a privacy page gets wrong easily

- **Pseudonymous, not anonymous.** With consent the data is pseudonymous
  (PostHog keeps an id; a replay shows what was on screen).
- **One term per store.** Use distinct names: "visit records" (our rows) are
  not "session recordings" (PostHog). Keep the terms consistent in every
  language.
- **Every language.** Publish the policy in every language the site and the
  banner use, with the same structure. Check the built HTML for glued words:
  JSX drops whitespace next to tags and entities.
- **No contradictions.** Every other page that makes privacy claims (a
  security page, FAQ, terms, meta descriptions) must agree with the policy.
- **Deletion as it really works.** If deletion is on request, say "write to us".
- **A real page, not an afterthought.** It is indexable, in the sitemap,
  with its own `<title>`, meta description, `lang` and canonical like the
  site's other pages (the same head pattern: structured data, `og:*`), and
  linked from every footer, the 404 page included. Its sitemap `lastmod`
  comes from the build or the file's history, never an invented time.
- **Fix flows, not text.** When a data flow breaks a platform's data-use
  policy, change the flow; do not document it.
