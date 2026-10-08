# vsql-docs

A skill that answers VillageSQL questions from the published docs at
[villagesql.com/docs](https://villagesql.com/docs) instead of from the model's
memory. It picks the docs version that matches the connected server, reads
the full page, and links every page it used.

The Claude Code plugin also adds the docs search server
(`https://villagesql.com/docs/mcp`). Other agents can add that server too;
without it, the skill reads the docs page index instead.
