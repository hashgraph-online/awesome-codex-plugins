# Banking Access Index — plugin

A skill for Claude Code, Cowork and Codex that answers questions from the Global Solo Banking
Access Index. The index records what 19 US business banking providers publish about applicants
who are not US tax residents but own a US LLC, across 8 countries (India, China, UK, Canada,
Pakistan, Nigeria, Turkey, Brazil). Every cell carries the source URL it came from and the date
that URL was read. A country missing from a provider's prohibited list is reported as
`no_published_restriction`, never as acceptance.

The plugin holds no code. Its one skill tells the agent where the public dataset lives
(`globalsolo.global/data/banking-access-index.csv` and `.json`), how to read a single cell with
its evidence, and how to report the status vocabulary without turning silence into a yes.

## Install

Claude Code:

```
/plugin install banking-access-index --marketplace global-solo/banking-access-index-mcp
```

Codex:

```bash
codex plugin marketplace add global-solo/banking-access-index-mcp
codex plugin add banking-access-index@global-solo
```

For structured tool calls instead of a skill, the same data is served by the MCP server at the
root of [this repository](https://github.com/global-solo/banking-access-index-mcp)
(`npx github:global-solo/banking-access-index-mcp`).

Dataset: CC BY 4.0, archived with a DOI ([10.5281/zenodo.21336392](https://doi.org/10.5281/zenodo.21336392)).
Plugin: MIT.
