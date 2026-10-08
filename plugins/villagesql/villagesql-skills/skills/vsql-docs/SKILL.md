---
name: vsql-docs
description: >
  Answer a VillageSQL question from the published documentation at
  villagesql.com/docs. Use when the user asks how a VillageSQL feature,
  extension, SQL statement, system variable, or error message works.
argument-hint: "[question or keyword]"
---

# VillageSQL Docs

Answer from the docs, not from memory. VillageSQL changes every release, and
names carried over from MySQL or PostgreSQL are often wrong here.

1. **Pick the docs version.** If a server is already connected, run
   `SELECT VERSION();`. `8.4…` means `mysql-8.4`, `9.7…` means `mysql-9.7`,
   and `-dev` in the version means `dev`; otherwise `stable`. With no
   server, use `mysql-8.4` and `stable`, and say so.

2. **Search.** Use the VillageSQL docs search tool if you have it. Its name
   contains `search_village_sql_server_for_my_sql`. Ignore results under a
   different `mysql-*/<stable|dev>/` path. Pages under `guides/`,
   `tutorial/`, and `extensions/` apply to every version.

   Without that tool, read the version's page index, which is linked from
   <https://villagesql.com/docs/llms.txt>, and pick the pages from it.

3. **Read the whole page** before answering. Take the page address, remove
   any `#anchor`, and add `.md`, for example
   <https://villagesql.com/docs/mysql-8.4/stable/install.md>. Do not use
   the docs file tool for this: its copies of long pages are incomplete.

4. **Answer.** Link each page you used. Copy commands and error messages
   exactly from the page. Say which docs version you used. If nothing
   answers the question, say that the search found nothing. Do not say the
   feature does not exist.
