# Hermes Tweet

[![OpenSSF Best Practices](https://www.bestpractices.dev/projects/13725/badge)](https://www.bestpractices.dev/projects/13725)
[![CI](https://github.com/Xquik-dev/hermes-tweet/actions/workflows/ci.yml/badge.svg)](https://github.com/Xquik-dev/hermes-tweet/actions/workflows/ci.yml)
[![PyPI](https://img.shields.io/pypi/v/hermes-tweet.svg)](https://pypi.org/project/hermes-tweet/)

Add native Xquik tools to [Hermes Agent](https://github.com/NousResearch/hermes-agent).

Hermes Tweet includes:

- 102 agent-callable Xquik endpoints, generated from OpenAPI.
- 33 prepaid read endpoints, including 7 direct MPP routes.
- Separate read and action tools.
- Actions disabled by default.
- A bundled Hermes Skill and 2 slash commands.

## Install

Install and enable the plugin:

```bash
hermes plugins install Xquik-dev/hermes-tweet --enable
```

Or install the PyPI package into Hermes:

```bash
uv pip install --python ~/.hermes/hermes-agent/venv/bin/python hermes-tweet
hermes plugins enable hermes-tweet
```

Install a local checkout:

```bash
hermes plugins install file:///absolute/path/to/hermes-tweet --force --enable
```

## Configure

Create an API key in Xquik. Then set:

```bash
export XQUIK_API_KEY="xq_..."
```

Optional settings:

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

## Safety

- Tools never accept credentials as arguments.
- The plugin injects `XQUIK_API_KEY` at request time.
- Admin, billing, credit, support, guest-wallet, and API-key routes stay hidden.
- Account re-authentication routes stay hidden.
- Binary downloads stay outside the agent catalog. Use REST for those files.
- Private reads and mutations use `tweet_action`.
- `tweet_action` requires `HERMES_TWEET_ENABLE_ACTIONS=true`.

Without an API key, Hermes exposes only `tweet_explore`.

## Slash Commands

| Command | Purpose |
| --- | --- |
| `/xstatus` | Show Xquik account and usage status. |
| `/xtrends` | Show current X trends. |

## Develop

Regenerate the catalog from the canonical OpenAPI schema:

```bash
python scripts/build_catalog.py ../xquik/openapi.yaml
```

Run all checks:

```bash
uv run --python 3.12 --group dev ruff format --check .
uv run --python 3.12 --group dev ruff check .
uv run --python 3.12 --group dev basedpyright
uv run --python 3.12 --group dev pytest --cov=hermes_tweet --cov=tests --cov-report=term-missing --cov-fail-under=100
uv run --python 3.12 --group dev bandit -c pyproject.toml -r hermes_tweet scripts fuzz
uv run --python 3.12 --group dev pip-audit
uv run --python 3.12 --group dev python -m build
uv run --python 3.12 --group dev twine check dist/*
```

## Links

- [Xquik API reference](https://docs.xquik.com/api-reference/overview)
- [Xquik authentication](https://xquik.com/auth.md)
- [Context7 guide](https://context7.com/xquik-dev/hermes-tweet)
- [Integration patterns](docs/INTEGRATION_PATTERNS.md)
- [Hermes surfaces](docs/HERMES_SURFACES.md)

## License

[MIT](LICENSE)

Xquik is an independent third-party service. Not affiliated with X Corp. "Twitter" and "X" are trademarks of X Corp.
