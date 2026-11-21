# CLI

```bash
npx -y @theopenapps/cli@latest <command> [flags]
```

Type the whole command every time. Never put it in a variable or an alias: zsh doesn't split a variable into words, so the call fails. Save a large answer to a file and filter the file, rather than reading it again.

An operation's first `_` is a space and the rest are `-`: `charts_get` is `charts get`, `listings_ranks_history` is `listings ranks-history`, `mcp_toolset_get` is `mcp toolset-get`. `--help` on a command shows which parameters are positional, such as `charts get <store> <chart>`, `listings versions <ref>` and `mcp toolset-get <ref>`. The rest are flags, spelled the same way: `limit=20` is `--limit 20`, `diff_from=-7d` is `--diff-from=-7d`. Write relative times with `=`. `latest=true` is the bare flag `--latest`, and a value starting with `-` takes `=`: `--since=-7d`.

Sign in with `auth login`, or set `OPENAPPS_API_KEY`. `auth status` prints the plan and what's left, and costs one call.

## Output

Full JSON runs about ten times the size of the rows a list needs, so choose per call.

| You need | Flags | You get |
|---|---|---|
| Rows of `charts_get`, `changes_list`, `listings_search`, `new_list` or `tags_get` | `--format csv --fields <a,b>` | Rows on stdout, and on stderr the date, the next cursor and `truncated` |
| One value | `--path data.series[0].points` or `--path data.rows[].name` | That value as JSON; `[-1]` counts from the end |
| Anything else, or `meta` and `data` beyond the rows | None | The whole answer as JSON |

A wrong field name prints the allowed ones. When stderr says `truncated`, or a skill reads `data.total`, `data.since` or `data.held`, repeat the call without `--format` to read them. `meta.budget` in the JSON says what's left: `calls_hour`, `calls_day` and `rows_day`.

## Exit codes

A cut exits 0. Busy is 1 with "temporarily unavailable", not found is 3 with `Closest:` candidates, and budget spent is 4. A shell loop has to check for 4 after each call and `break`, because the shell carries on past a failed command.
