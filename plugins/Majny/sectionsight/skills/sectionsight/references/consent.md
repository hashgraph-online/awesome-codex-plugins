# The consent banner

Model B needs one. In models A and C, k.js itself needs none; the owner
decides (see `decisions.md`). Any other tool that stores or reads something on the device
(PostHog, ads, chat widgets) needs consent before it loads.

## The rules it follows

These are this skill's design rules. They are based on the EDPB's
cookie-banner taskforce report (adopted 17 January 2023), which calls its
own positions a minimum, not a safe harbour, and on national guidance
(for example France's CNIL and other national authorities).
Some are stricter than any regulator requires, which is deliberate.
None of this is legal advice; the owner's counsel decides.

1. **Refusing is as easy as accepting.** Two buttons on the first layer, the
   same size and weight, and here the same colour too. The taskforce judges
   colour case by case; identical buttons avoid the question. Decline comes
   first, or sits level with Accept. There is no "X" that means neither, and no "Accept"
   hidden behind "Settings".
2. **Nothing that needs consent runs before Accept.** No script loaded, no
   cookie or storage written, no request sent. Storing the answer itself is
   fine: it is needed to honour the answer.
3. **Informed.** The text says what Accept turns on, by name, for example
   "a recording of the screen with form text hidden, through PostHog (EU
   servers)". It says how long data is kept, what happens without consent,
   and where the choice can be changed. It links to the privacy page. Vague
   "to improve your experience" text does not make consent informed.
4. **Withdrawing is as easy as consenting.** That is the requirement; how
   is up to the site. The taskforce report (para 35) names a floating
   withdrawal icon as one option, not a requirement. Here: a "Privacy
   settings" link or button at the bottom of every page, the 404 page
   included, brings the banner back. Decline then withdraws. Withdrawal
   stops everything at once, in every open tab, and deletes what was stored.
5. **The answer is remembered, a refusal included.** Asking again on every
   page pressures people into accepting. consent.js asks again after 12
   months (`maxAgeDays`). CNIL recommends keeping a choice, consent and
   refusal alike, for 6 months before asking again (Recommendation
   2020-092, consolidated 16 January 2026); use the period the owner's
   regulator expects.
6. **Global Privacy Control and Do Not Track count as a refusal.** No banner
   for those browsers, the tracker and PostHog stay off, and `get()` answers
   `'denied'` even if an older Accept is stored. This is the skill's choice,
   not an EU rule: US state laws (California's CCPA regulations §7025,
   Colorado since 1 July 2024, and others) require honouring GPC for sale,
   sharing and targeted advertising, but no EU law makes it a binding
   refusal. The skill treats it as one anyway.
7. **No banner on private pages.** Analytics never runs there anyway.
8. **No dark patterns.** No pre-ticked boxes and no "legitimate interest"
   toggles that default to on. Scrolling, closing or continuing to browse is
   not consent, and the banner does not block reading the page.
9. **In the page's language.** Ship the texts for every language the site has.

## Using consent.js

Load it in the `<head>` of every page, before anything that waits for consent:

```html
<script>window.consentConfig = {
  skip: '^/(account|reset)(/|$)',      // ONE regex (or an array of them)
  detailsHref: '/privacy',             // also accepted inside texts
  texts: { title: '…', body: '…', decline: 'Decline', accept: 'Accept', details: 'Details' },
  onGranted: () => { /* start what needs consent, e.g. startPostHog(site, load) */ },
  onDecline: () => purgePostHog(),     // a first refusal: clear what an older setup stored
  onWithdraw: () => stopPostHog(),     // may return a promise; the page reloads after it, even if it throws
};</script>
<script src="/consent.js" defer></script>   <!-- before k.js and the PostHog module -->
```

**Options** (`data-*` on the tag, or `consentConfig`):

| Option | Default | Meaning |
|---|---|---|
| `key` | `analytics-consent` | storage key; `<key>-at` holds the date |
| `grantedValue` / `deniedValue` | `granted` / `denied` | the stored values (k.js `data-consent-value` must match) |
| `maxAgeDays` | `365` | the answer expires after this; expired keys are removed on load |
| `skip` | — | one regex of paths where the banner never shows; `'/^\/account(\/|$)/i'` (slashes and flags) for a case-insensitive one |
| `reloadOnWithdraw` | `true` | reload after a withdrawal |
| `deleteButton` | `true` | offer "Delete my visit data" in the reopened banner after an Accept (needs k.js on the page); `false` hides it |
| `mount` | `start` | `end` puts the banner at the end of `<body>`: required where a framework hydrates `<body>` (Next.js, React SSR), since a node before its children breaks hydration; the banner then takes focus when it shows by itself |
| `stylesheet` | — | a URL of `assets/consent.css` as the site serves it: loaded with a `<link>` instead of the `<style>` element, for a CSP without a nonce |
| `styles` | `true` | inject the default CSS in a `<style>` element |
| `styleNonce` | the nonce of consent.js's own `<script>` tag | the page's CSP nonce, put on that `<style>` element |
| `texts` | English placeholders | partial objects are fine; missing texts keep their defaults (`deleteData` is the delete button's label) |
| `onGranted`, `onDecline`, `onWithdraw` | — | hooks, read when they run, so the page may set them later |

Load it before the code that reads `window.analyticsConsent`: with `defer`
ahead of k.js and the PostHog module (they run in document order), or
`strategy="beforeInteractive"` in Next.js. Without `defer` it blocks
rendering; that is needed only when an inline script reads it during
parsing.

**Footer, on every page**:
`<button type="button" class="ph-no-capture" data-consent-open>Privacy settings</button>`

**API**:

- `window.analyticsConsent.get()` returns `'granted'`, `'denied'` or `null`.
- `.set(…)` records an answer; `.open()` reopens the banner.
- Events on `window`:
  - `consent:changed` (detail: the choice);
  - `k:consent` (k.js listens to it);
  - `consent:open` (opens the banner);
  - `consent:ui` (detail `shown`, `accept`, `decline` or `withdraw`; also
    kept, the last 8, in `window.__consentUi`): what the banner did, for
    k.js's optional counts (`data-consent-counts="on"`, `tracker.md`). A
    port (a re-implementation in a framework) that supports those counts
    must dispatch the same event.

**Storage**: `analytics-consent` (`granted` / `denied`) and
`analytics-consent-at` (ISO date) in localStorage. An answer found without
a date (left by an older setup) is dated on load, so it expires
`maxAgeDays` later. If storage is blocked,
the answer holds for that page load only.

**Styling**: the CSS variables `--consent-bg`, `--consent-fg` and
`--consent-z`, or `data-styles="false"` and your own CSS for `.consent-banner*`.
Keep in your own CSS what the default rules guarantee: the banner never
taller than the viewport (`max-height:100dvh; overflow-y:auto`, so it
stays readable at 400% zoom), and a visible edge on a dark page. The
banner's text is often the largest text in the first screen, so Lighthouse
may report it as the LCP element; a short body keeps that cheap. The
banner waits for the page's web fonts (at most 3 s) before it shows: a
bottom-anchored banner that reflows when a font swaps in grows upward,
which counts as a layout shift.
Keyboard: Escape closes a banner reopened from "Privacy settings" (not the
first one, which waits for an answer), and after an answer focus moves on
into the page.

**Content Security Policy.** By default consent.js adds a `<style>`
element, which a `style-src` without `'unsafe-inline'` blocks (the banner
then shows unstyled at the top of the page; verify fails it). On a static
host, with no per-request nonce, serve `assets/consent.css` and set
`stylesheet: '/consent.css'` (allowed by `style-src 'self'`, and not
render-blocking: the banner waits for it), or put the same rules in the
site's own CSS bundle with `styles: false`. With a per-request nonce, give consent.js's
script tag the page's nonce (`<script src="/consent.js" nonce="…">`, with
`style-src 'self' 'nonce-…'`): the style takes the same nonce. (`styleNonce`
sets another one; a nonce in a `data-*` attribute is readable by any script
on the page, so prefer the tag's own.) The inline
`window.consentConfig` script needs a nonce or hash in `script-src`, or
put the config in an external file (`<script src="/consent-config.js">`
before consent.js).

**z-index**: keep the banner under the site's menus, sheets and dialogs, so
it never takes a tap meant for them (for example 45 when menus use 50–60).
On phones, keep it clear of fixed bottom bars.

**Texts**: write them with the owner. An example, for
model B with PostHog:

> **We measure how people find their way around this site.** With your
> consent we keep a record of your visit for 180 days and use PostHog
> (servers in the EU), including a recording of the screen with form text
> hidden, so we can see where people get stuck. Without it we only count
> totals, with no cookies and no identifiers. You can change your choice
> any time at the bottom of the page. [Details]

## "Delete my visit data"

When a visitor who accepted reopens the banner ("Privacy settings"), it
shows a third button under Decline and Accept: **Delete my visit data**
(`texts.deleteData`; `data-consent-delete` on the element). It:

1. calls `window.__k.deleteMyData()`: k.js sends `{"del":"<visit id>"}` to the
   collector and forgets the id;
2. then withdraws consent exactly like Decline (the `onWithdraw` hook, the
   reload).

- **Equal weight stays.** It has the same class and style as Decline and
  Accept, sits below them, and never appears on the first question, so it
  cannot push anyone toward either answer. Focus still goes to Decline.
- **Only when it can work:** after an Accept, with k.js on the page and
  `window.__k.canDelete` true (k.js sets it false in mode `never` and with
  `data-delete="off"`). The collector cannot tell the page whether its store
  can delete (it answers 204 to everything), so with Analytics Engine, or
  with the collector's `deletion: false`, set `deleteButton: false` here and
  `data-delete="off"` on k.js.
- **What it deletes:** the rows of the current visit only (this page load,
  or the tab's visit with `data-visit-store="session"`). Earlier visits used
  other random ids nothing remembers; they expire with the rows' retention.
  Totals have no id and stay. PostHog recordings are not deleted by it (see
  `collector.md`, "Deletion", and `assets/dsar.mjs`). The privacy text must
  say exactly this (`privacy-policy.md`).
- **The trade-off of `window.__k`:** the API never returns the id, so no other
  script reads it from there; but scripts on the page can see k.js's reports
  anyway, and can call the function (which only deletes this visitor's own
  rows). Do not put scripts you do not trust on pages with analytics.
- verify.mjs clicks it and checks the request carries only the visit id
  (`verify.md`).

## Porting it to React, Vue or Svelte

Keep the behaviour; only the rendering moves into the framework.

- **Reading the answer.** It lives outside the framework, in localStorage.
  In React, read it with `useSyncExternalStore` (subscribe to
  `consent:changed` and `storage`; the server snapshot is "no banner"), so
  server render and hydration agree. A `useState` plus `useEffect` read
  flashes the banner or trips hydration warnings.
- **Answer helpers.** Export the get and set helpers from one module and use
  them everywhere: the banner, the PostHog guard, k.js's `consent` function.
- **Focus.** When "Privacy settings" opens the banner, move focus to
  Decline. After an answer, return focus to where it was. Render the banner
  inside an `aria-live="polite"` container that exists in the server HTML.
- **No recorded clicks on the consent UI.** Put `class="ph-no-capture"` on
  the banner and on "Privacy settings", so PostHog autocapture records no
  click on them.

## Withdrawal, step by step

When Decline is clicked after an earlier Accept:

1. Store `denied` and its date. Every tab reads it: tabs that run PostHog
   check consent in `before_send` on every event, so they stop immediately.
2. Stop PostHog in this order (`stopPostHog`):
   1. `stopSessionRecording()`;
   2. `reset(true)`;
   3. `opt_out_capturing()`, **last**, because `reset()` clears the opt-out.
3. Delete PostHog's cookie and storage, but **keep**
   `__ph_opt_in_out_<token>`: the PostHog instances in other tabs read it.
   Each other open tab also purges its own sessionStorage (PostHog's window
   id) when it sees the change.
4. k.js drops its stored visit id (`k:consent`). Its reports go back to
   carrying no ids.
5. Reload the page, so no code that was allowed to run stays in memory.

If the visitor never consented, Decline stores the answer and runs the
`onDecline` hook. Set it to `purgePostHog()` so whatever an older setup
wrote is cleared.

**Client-side routes**: consent.js follows `history`, so it shows or hides
the banner when a route enters or leaves a private page. If a router swaps
`<body>` (Astro's `<ClientRouter />`), it mounts the banner again.
