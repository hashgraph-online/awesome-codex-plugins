# Hermes Tweet, the Hermes Agent plugin for Twitter search & X actions

[![OpenSSF Best Practices](https://www.bestpractices.dev/projects/13725/badge)](https://www.bestpractices.dev/projects/13725)
[![PyPI](https://img.shields.io/pypi/v/hermes-tweet.svg)](https://pypi.org/project/hermes-tweet/)

Add Twitter API search, monitoring, and approved X actions to
[Hermes Agent](https://github.com/NousResearch/hermes-agent).

Xquik is the world's fastest and cheapest X Twitter scraper service with the most complete X data.
Xquik charges only for delivered, unique, filter-matching results and never pads rows.

Explore 102 OpenAPI-generated endpoints, including 33 prepaid reads and 7 direct MPP routes.
Reads and actions use separate tools. Actions stay disabled by default.
The plugin bundles a Hermes Skill and 2 slash commands.

<!-- trust:start -->

## Trust & usage

[![Twitter API package downloads](https://img.shields.io/endpoint?url=https%3A%2F%2Fxquik.com%2Fbadges%2Fdownloads.json)](https://xquik.com/trust#downloads)
[![Twitter scraper users on Apify](https://img.shields.io/endpoint?url=https%3A%2F%2Fxquik.com%2Fbadges%2Fapify-users.json)](https://apify.com/xquik)
[![Twitter scraper runs on Apify](https://img.shields.io/endpoint?url=https%3A%2F%2Fxquik.com%2Fbadges%2Fapify-runs.json)](https://apify.com/xquik)
[![Tweet scraper rating on Apify](https://img.shields.io/endpoint?url=https%3A%2F%2Fxquik.com%2Fbadges%2Fapify-rating.json)](https://apify.com/xquik/x-tweet-scraper/reviews)
[![Xquik Twitter API accounts](https://img.shields.io/endpoint?url=https%3A%2F%2Fxquik.com%2Fbadges%2Faccounts.json)](https://xquik.com/trust#accounts)
[![Twitter Skill installs](https://img.shields.io/endpoint?url=https%3A%2F%2Fxquik.com%2Fbadges%2Fskill-installs.json)](https://xquik.com/trust#skill-installs)
[![Xquik verified revenue on TrustMRR](https://img.shields.io/endpoint?url=https%3A%2F%2Fxquik.com%2Fbadges%2Frevenue.json)](https://trustmrr.com/startup/xquik)
[![Twitter API median response time](https://img.shields.io/endpoint?url=https%3A%2F%2Fxquik.com%2Fbadges%2Frest-p50.json)](https://xquik.com/trust#speed)
[![Xquik GitHub stars](https://img.shields.io/endpoint?url=https%3A%2F%2Fxquik.com%2Fbadges%2Fgithub-stars.json)](https://github.com/Xquik-dev)
[![hermes-tweet downloads on PyPI](https://img.shields.io/endpoint?url=https%3A%2F%2Fxquik.com%2Fbadges%2Fpypi-hermes-tweet.json)](https://pypistats.org/packages/hermes-tweet)
[![hermes-tweet downloads on ClawHub](https://img.shields.io/endpoint?url=https%3A%2F%2Fxquik.com%2Fbadges%2Fclawhub-hermes-tweet.json)](https://clawhub.ai/xquik/skills/hermes-tweet)
[![hermes-tweet Skill installs on skills.sh](https://img.shields.io/endpoint?url=https%3A%2F%2Fxquik.com%2Fbadges%2Fskills-hermes-tweet.json)](https://skills.sh/xquik-dev/hermes-tweet)
[![OpenSSF Best Practices](https://www.bestpractices.dev/projects/13725/badge)](https://www.bestpractices.dev/projects/13725)

- 51,000+ downloads of Xquik's Twitter API packages on npm, PyPI, RubyGems, NuGet, Packagist & Terraform ([source](https://xquik.com/trust#downloads)) <!-- trust:downloads 51020 -->
- 7,800+ users of Xquik's Twitter scraper Actors on Apify ([source](https://apify.com/xquik)) <!-- trust:apify-users 7800 -->
- 5,700,000+ runs of Xquik's Twitter scraper Actors on Apify ([source](https://apify.com/xquik)) <!-- trust:apify-runs 5704701 -->
- 4.66 of 5 for the X Tweet Scraper from 16 Apify reviews ([source](https://apify.com/xquik/x-tweet-scraper/reviews)) <!-- trust:apify-rating 4.66 16 -->
- 3,900+ accounts on xquik.com ([source](https://xquik.com/trust#accounts)) <!-- trust:accounts 3924 -->
- 1,600+ installs of Xquik's Twitter Skills on skills.sh ([source](https://xquik.com/trust#skill-installs)) <!-- trust:skill-installs 1612 -->
- $38,000+ in revenue verified by TrustMRR ([source](https://trustmrr.com/startup/xquik)) <!-- trust:revenue 38115 -->
- 501 ms median REST API read time over the last 7 days ([source](https://xquik.com/trust#speed)) <!-- trust:rest-p50 501 -->
- 370+ GitHub stars across Xquik's repos ([source](https://github.com/Xquik-dev)) <!-- trust:github-stars 374 -->
- 2,800+ downloads of hermes-tweet on PyPI ([source](https://pypistats.org/packages/hermes-tweet)) <!-- trust:pypi-hermes-tweet 2876 -->
- 1,100+ downloads of hermes-tweet on ClawHub ([source](https://clawhub.ai/xquik/skills/hermes-tweet)) <!-- trust:clawhub-hermes-tweet 1162 -->
- 7 installs of this repo's Skills on skills.sh ([source](https://skills.sh/xquik-dev/hermes-tweet)) <!-- trust:skills-hermes-tweet 7 -->
- This repo meets the OpenSSF Best Practices passing criteria ([source](https://www.bestpractices.dev/projects/13725)) <!-- trust:openssf-hermes-tweet 1 -->

Checked on 2026-10-15. See each number with its date & source on [xquik.com/trust](https://xquik.com/trust) or as [JSON](https://xquik.com/trust.json).

<!-- trust:end -->

## When to use Hermes Tweet

Use this plugin for X/Twitter search, reads, or monitoring in Hermes.
Choose an SDK for application code.

## Install

Install and enable the plugin.

```bash
hermes plugins install Xquik-dev/hermes-tweet --enable
```

Hermes scans plugins during install and update. Review any warning before
continuing. A dangerous verdict blocks installation or disables an update.

Hermes installs no extra Python package for this plugin. Hermes core already
ships `httpx`, its only dependency.

If you manage the Hermes Python environment yourself, add the `hermes-tweet`
PyPI package to it. Then enable the plugin.

```bash
hermes plugins enable hermes-tweet
```

Install a local checkout with this command.

```bash
hermes plugins install file:///absolute/path/to/hermes-tweet --force --enable
```

## Configure

Create an API key in Xquik. Then set it in your environment.

```bash
export XQUIK_API_KEY="xq_..."
```

These settings are optional.

```bash
export XQUIK_BASE_URL="https://xquik.com"
export HERMES_TWEET_ENABLE_ACTIONS="false"
```

Restart Hermes after changing environment variables.

## Tools

| Tool | Purpose |
| --- | --- |
| `tweet_explore` | Search the bundled catalog. Makes no API call. |
| `tweet_read` | Call catalog-listed read endpoints. |
| `tweet_action` | Call private or mutating endpoints. Disabled by default. |

Use `tweet_explore` first. Then pass a listed `/api/v1/...` path to the matching tool.

Copied Xquik URLs work when their paths match the catalog.

## Common Twitter API tasks

Start with `tweet_explore`. Invoke only the path returned by the catalog.

| Task | Catalog query | Tool |
| --- | --- | --- |
| Search X posts | `search tweets by query` | `tweet_read` |
| Read profile timelines | `list recent tweets posted by a user` | `tweet_read` |
| Export followers | `run extraction` | `tweet_action` |
| Export following accounts | `run extraction` | `tweet_action` |
| Monitor an account | `create monitor` | `tweet_action` |
| Post or reply | `create tweet` | `tweet_action` |

Set `include_actions` for extraction, monitoring, and writing searches.
`tweet_action` always follows the approval rules below.

## Safety

- Tools never accept credentials as arguments.
- The plugin injects `XQUIK_API_KEY` at request time.
- Admin, billing, credit, support, guest-wallet, and API-key routes stay hidden.
- Account re-authentication routes stay hidden.
- Binary downloads stay outside the agent catalog. Use REST for those files.
- Private reads and mutations use `tweet_action`.
- `tweet_action` requires `HERMES_TWEET_ENABLE_ACTIONS=true`.

Without an API key, Hermes exposes only `tweet_explore`.

## Slash commands

| Command | Purpose |
| --- | --- |
| `/xstatus` | Show Xquik account and usage status. |
| `/xtrends` | Show current X trends. |

## Development

Regenerate the catalog from the canonical OpenAPI schema.

```bash
python scripts/build_catalog.py ../xquik/openapi.yaml
```

Run all checks.

```bash
uv run --python 3.12 --group dev ruff format --check .
uv run --python 3.12 --group dev ruff check .
uv run --python 3.12 --group dev basedpyright
uv run --python 3.12 --group dev pytest --cov=hermes_tweet --cov=tests --cov-report=term-missing --cov-fail-under=100
uv run --python 3.12 --group dev bandit -c pyproject.toml -r hermes_tweet scripts fuzz
uv run --python 3.12 --group dev pip-audit
uv run --python 3.12 --group dev bash scripts/check_reproducible.sh
uv run --python 3.12 --group dev python -m build
uv run --python 3.12 --group dev twine check dist/*
```

## Links

- [Xquik API reference](https://docs.xquik.com/api-reference/overview)
- [Xquik authentication](https://xquik.com/auth.md)
- [Context7 guide](https://context7.com/xquik-dev/hermes-tweet)
- [Integration patterns](docs/INTEGRATION_PATTERNS.md)
- [Hermes runtime hosts](docs/HERMES_SURFACES.md)
- [Organization support policy](https://github.com/Xquik-dev/.github/blob/main/SUPPORT.md)
- [Security policy](SECURITY.md)
- [Contribution guide](https://github.com/Xquik-dev/.github/blob/main/CONTRIBUTING.md)

## More Xquik tools

- [X (Twitter) scraper API & Twitter MCP server](https://github.com/Xquik-dev/x-twitter-scraper) with REST, MCP & Skill setup.
- Twitter API SDKs for [TypeScript](https://github.com/Xquik-dev/x-twitter-scraper-typescript), [Python](https://github.com/Xquik-dev/x-twitter-scraper-python), [Go](https://github.com/Xquik-dev/x-twitter-scraper-go), [Ruby](https://github.com/Xquik-dev/x-twitter-scraper-ruby), [Java](https://github.com/Xquik-dev/x-twitter-scraper-java), [Kotlin](https://github.com/Xquik-dev/x-twitter-scraper-kotlin), [C#](https://github.com/Xquik-dev/x-twitter-scraper-csharp) & [PHP](https://github.com/Xquik-dev/x-twitter-scraper-php).
- [Twitter CLI & X CLI](https://github.com/Xquik-dev/x-twitter-scraper-cli) for terminal workflows.
- [Twitter advanced search operators](https://github.com/Xquik-dev/x-twitter-advanced-search) with tested examples.
- [Xquik X API & Twitter scraper](https://xquik.com) and the [Twitter API documentation](https://docs.xquik.com/api-reference/overview).

## License

[MIT](LICENSE)

Xquik is an independent third-party service. Not affiliated with X Corp. "Twitter" and "X" are trademarks of X Corp.
