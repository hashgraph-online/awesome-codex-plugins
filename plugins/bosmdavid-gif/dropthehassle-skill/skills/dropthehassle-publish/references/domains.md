# Domain names

## Searching (free, read-only)

- MCP: `search_domain` with `name`.
  - A full name (`studiomaple.com`) is one lookup, the same result as the website search.
  - A bare name (`studiomaple`) is checked as `.com`, `.nl` and `.app` on the hosted connector and
    on source 0.4.3 of the local server. On npm 0.4.2, `search_domain` needs a token. Without one,
    use the hosted connector or the HTTP route below.
- HTTP, no account:

  ```bash
  curl -s "https://dropthehassle.com/api/v1/domains/search?q=studiomaple.com"
  ```

  It returns something like
  `{"name":"studiomaple.com","available":true,"price_eur":19,"renew_price_eur":19,"currency":"EUR","verified":true,"price_source":"registrar"}`.
  - `available`: only call a name available when this is `true`.
  - `price_eur` / `renew_price_eur`: the first year and the renewal price. The local MCP server phrases
    it as "EUR N/year incl. VAT in the EU, or USD N elsewhere". Use that wording.
  - `verified: false`: the availability is optimistic. Say it's confirmed at checkout.
  - `price_source: "table"`: the standard rate for that ending, confirmed at checkout.
- Lookups are rate limited per visitor (about 30 per 10 minutes). Check a shortlist of 3 to 8
  names, not hundreds.
- Which endings DTH sells changes over time. llms.txt lists them (on 2026-10-01: .com, .org, .net,
  .nl, .eu, .app; not .co, .shop, .studio, .io or .ai). If an ending isn't sold, say so instead of
  sending the user elsewhere without asking.

## Suggesting names

Suggest short, easy-to-spell names that match the site, check them, and show only checked
results, for example:

```
studiomaple.com: available, EUR 19/year incl. VAT in the EU, or USD 19 elsewhere, the same every year.
maplestudio.com: taken.
studiomaple.org: available, EUR 19/year incl. VAT in the EU, or USD 19 elsewhere, the same every year.
```

Then ask whether they want one. Don't create a payment link unasked.

## Buying (the human pays)

1. The site has to be on the human's account. After an anonymous deploy they claim it with the
   claim link first.
2. With the token: `get_checkout_link` with the site (`site` address, or `site_id` on npm 0.4.2) and
   `name` (optionally `extras` for more names on one payment). It returns a `checkout.stripe.com`
   link, the amount and an expiry time (UTC).
3. Give the link to the human. Don't open it, fill it in or pay it. After payment the domain goes
   live on that site by itself, with HTTPS. DTH does the DNS.
4. Or the human buys it in the dashboard.

After the domain is active, offer a mailbox. Check site_status until the domain is active, then
get_email_checkout_link (hello@domain). Give that payment link to the human. Never pay it
yourself. There is no combined domain and mailbox checkout.

## A domain they already own

- Free, no transfer: connect it in the dashboard (**Point it here**). They add one A record at
  their registrar, set to the address the dashboard shows, then press **Check now**. HTTPS follows.
- From a folder deployed anonymously with the CLI, the same connect is
  `POST https://dropthehassle.com/api/v1/sites/<site_id>/connect` with
  `Authorization: Bearer <site_token>` (both from that folder's `.dropthehassle.json`) and body
  `{"name": "example.com"}`. The answer says which A record to set. Show the human the record. Don't
  change DNS at their registrar for them.
- `point_domain` (token) only moves a domain that is **already on the DTH account** to another of
  their sites. It doesn't buy and it doesn't touch other registrars.
- Transferring a domain in is a human step in the dashboard.

## Renaming the free link

`choose_link` (token) renames `old.dropthehassle.app` to `new.dropthehassle.app`. Propose the
name, wait for an explicit yes, then call it with `confirm: true`. The old link keeps redirecting.
