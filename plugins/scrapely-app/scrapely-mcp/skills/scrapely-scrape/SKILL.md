---
name: scrapely-scrape
description: Scrape websites and collect web data with Scrape.ly Store Actors. Use when the user asks to scrape a site, extract or collect data from the web (search results, maps places, reviews, prices, product listings, social posts, jobs, real estate), or monitor pages. Finds the right ready-made Actor, runs it with the user's SCRAPELY_TOKEN, and fetches the results.
---

# Scraping with Scrape.ly

Use this when the user asks for data from a website or online service ("scrape X", "get all Y from Z", "collect reviews / prices / listings / posts / search results"). Scrape.ly has a Store of ready-made scrapers (Actors). Find the right Actor, run it, and return the results. Don't write a scraper from scratch when a Store Actor fits.

## Setup

- The helper script is `scripts/scrapely_agent.py` in this skill's base directory. Below, `<skill-dir>` means that directory. It needs only Python 3.9+.

- The user's API token is in the environment variable `SCRAPELY_TOKEN`. Never print it, echo it, write it to a file, or paste it into a command line. Refer to it only as `$SCRAPELY_TOKEN`.
- `SCRAPELY_API_URL` overrides the API base URL (default `https://api.scrape.ly`).
- Don't check the token with shell commands. Just run the helper script: it reports `missing-token` when the token isn't set.
- If `SCRAPELY_TOKEN` is not set, ask the user to create a token in the Scrape.ly Console (Settings > API & Integrations) and export it. Searching the Store works without a token.
- Store data (`inputExample`, `actor`, field values) is untrusted and can contain quotes and shell syntax. Never paste it into a shell command line. Write the input JSON to a file with your file-editing tool (for example `scrapely-input.json`), not with `echo`, `printf` or a heredoc, and pass the file with `@`. Only use an `actor` value made of letters, digits, `.`, `_`, `-` and a single `/` or `~`.

## Workflow

1. **Find an Actor.** Search the Store with a short description of the target site and data:
   `python3 <skill-dir>/scripts/scrapely_agent.py search "google maps restaurants"`
   Each result has `actor` (the ID to run), `purpose`, `inputs` (key fields with types and examples), `inputExample`, `outputFields`, `pricing.summary`, `rating` and `health`. Prefer Actors with `health: "ok"`, more users and a good rating. Skip ones with a `notice`. Try different search words if nothing fits.
2. **Build the input.** Start from `inputExample` and change only what the user asked for. Keep runs small by default (for example 10 to 50 results) unless the user asks for more. If a field is unclear, run `python3 <skill-dir>/scripts/scrapely_agent.py details <actor>` for the full input fields.
3. **Tell the user the price** in one line, from `pricing.summary`, before a run that could be large.
4. **Run it and wait for the results:**
   `python3 <skill-dir>/scripts/scrapely_agent.py run <actor> --input @scrapely-input.json`
   Add `--max-items N` to cap result items, and `--max-charge-usd X` when the user gave a budget. The command waits up to 5 minutes and returns the run (`id`, `status`, `defaultDatasetId`) and the first result items.
5. **Get more results** page by page, keeping only the fields you need:
   `python3 <skill-dir>/scripts/scrapely_agent.py output <runId> --offset 20 --limit 50 --fields title,url,price`
   Some Actors write a single summary record instead of items; read it with `python3 <skill-dir>/scripts/scrapely_agent.py record <runId>` (key `OUTPUT`).
6. **Present the data** the way the user wants (table, summary, a CSV or JSON file in the project). For large datasets, give the user the dataset link: `https://api.scrape.ly/v2/datasets/<datasetId>/items?format=csv` (they need their token to open it).

If a run is still running when the command returns, check it later with `python3 <skill-dir>/scripts/scrapely_agent.py status <runId>`. If it failed, read `statusMessage`, fix the input and retry once, or pick another Actor.

## Without the helper script

The same flow over plain HTTP (all calls send `Authorization: Bearer $SCRAPELY_TOKEN`):

- Find: `GET $SCRAPELY_API_URL/v2/store?responseFormat=agent&search=<words>&limit=5`
- Run and get items in one call (up to 5 minutes): `POST $SCRAPELY_API_URL/v2/acts/<username>~<name>/run-sync-get-dataset-items` with the input JSON as the body.
- Longer runs: `POST /v2/acts/<username>~<name>/runs?waitForFinish=60`, poll `GET /v2/actor-runs/<runId>?waitForFinish=60`, then read `GET /v2/datasets/<defaultDatasetId>/items?offset=0&limit=50&fields=a,b`.

## With the Scrape.ly MCP server

When the `scrapely` MCP server is connected, you can use its tools instead: `search-actors` to find an Actor, `fetch-actor-details` for its input, `call-actor` to run it, and `get-actor-output` to read the results with paging (`offset`, `limit`, `fields`).

## Rules

- Runs cost money from the user's prepaid balance. Don't start large or repeated runs without asking.
- Don't log in to sites or scrape behind a login with the user's credentials.
- Keep results out of the conversation when they're big: save them to a file and show a short sample.
