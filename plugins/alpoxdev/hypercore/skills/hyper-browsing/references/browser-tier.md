# Browser Tier

> Tiers 3 and 4: a browser the run owns and throws away, or the user's own browser for their own account, never a copy of their session.

## 1. Capability Check

Before tier 3, find which browser capability the runtime exposes: a browser-automation tool or library the runtime already provides, or a headless browser binary already installed; never install one for this run. Record its name and version in the report. With none, mark tiers 3 and 4 `skipped` and end at `blocked` or `fetched_partial`; never describe a page as rendered from reasoning.

## 2. Tier 3: Owned Browser

1. Create a fresh profile directory under `.hyper/browsing/<slug>/profile/`. Never point the browser at the user's own profile.
2. Launch headless first through the runtime's own browser capability. Do not install a separate browser build, inject stealth scripts, or override `navigator.webdriver` by hand; a challenge the runtime's browser cannot pass ends the tier.
3. Navigate once, wait for the network to settle or up to 10 seconds, then read the page as text or an accessibility snapshot rather than a screenshot when text answers the request.
4. When the content is data, capture the page's own network requests and look for JSON calls (`/api/`, `/graphql`, `.json`). Re-request a JSON URL in tier 1; record it as provenance `api` when it is the platform's own call.
5. A challenge that remains after one reload and a 10-second wait ends the tier. A challenge that asks a human to act goes to `rules/access-policy.md` §4.
6. Take a screenshot only when the request needs one, and save it under `content/`.
7. Close the browser in a `finally` step and remove the profile directory; record the removal.

Pseudocode, for any automation library:

```text
profile = new dir .hyper/browsing/<slug>/profile
browser = launch(headless, user_data_dir=profile)
try:
  page = browser.open(url); page.wait(network_idle or 10s)
  text = page.text_or_snapshot(); requests = page.network_log()
  save(text, content/<name>.md)
finally:
  browser.close(); remove(profile)
```

## 3. Tier 4: Attached Browser

1. Use only the runtime's capability to attach to the browser the user already runs and is signed in to. Never launch against, copy, or export their profile.
2. Tell the user which host and which page will open, and that the run is read-only.
3. Navigate, read the page as text or a snapshot, and stop at any login, two-step code, or challenge: the user completes it themselves, then the run continues.
4. Do not click anything that writes (send, buy, post, delete, settings) unless the user asked for that exact action in this run.
5. Detach without closing the user's browser or tabs they had open, and without clearing any data.

## 4. Cookies

Cookies never move from the user's browser into the run. A cookie export from the user's live profile copies their session, so it is out of scope even when a tool exists for it. Cookies the owned browser receives stay in its throwaway profile and are deleted with it.

## Sources

> Checked 2026-11-07.

| Claim | Source |
|---|---|
| A browser with a task-owned profile, no injected stealth scripts, reading the page's JSON calls, the user's own signed-in browser for their account, and never copying or clearing the user's live profile | The `ultimate-browsing` skill in `code-yeongyu/oh-my-openagent` (branch `dev`), read 2026-11-07 |
| Reading network requests to find internal JSON endpoints | the same skill, read 2026-11-07 |
| The 10-second wait, the read-only default, and the capability check | this package's chosen design, not a validated optimum |
