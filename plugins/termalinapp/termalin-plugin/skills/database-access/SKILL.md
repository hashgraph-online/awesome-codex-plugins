---
name: database-access
description: Explore and query databases on the user's servers (Postgres, MySQL/MariaDB, Redis, MongoDB, SQLite) through Termalin without credentials in the chat. Use when the user asks what is in a database, wants a query, a count, a schema, a slow query check or a data fix on a server.
---

Termalin's `data_*` tools connect to the database on the server through the Connector, so no password is ever pasted here. The default is read-only.

Order of work:

1. `hosts_list` to pick the server, then `data_tables` with the `engine` and `database` to see what exists. Do not guess table names.
2. `data_schema` for each table the question touches: columns, types, keys, indexes, row estimate. Use the real column names in the query.
3. `data_query` for the actual question. Rules:
   - Always add `LIMIT` (default 50, at most 500) to row-returning queries; aggregate with `COUNT`, `GROUP BY`, `date_trunc` instead of pulling rows and counting in the chat.
   - Read-only unless the user explicitly asks for a change. A write (`INSERT`, `UPDATE`, `DELETE`, `ALTER`, `DROP`, Redis `SET`/`DEL`, Mongo updates) needs `allowWrites: true`, a connection with full access, and the user's yes to the exact statement; show the statement first, with a `WHERE` that matches what they described, and prefer a `SELECT COUNT(*)` with the same `WHERE` before the `UPDATE`/`DELETE`.
   - Wrap risky writes in a transaction when the engine supports it, and report the affected-row count after.
   - Long analytical queries (over a minute) time out; narrow the date range or run them as a background job on the server with `job_start` and the engine's CLI.
4. Present results as a compact table or a sentence with the number; name the database and server the answer came from.

Privacy: do not dump whole tables of personal data (emails, names, addresses, payment fields) into the chat. Aggregate, or select only the columns the question needs, and mask identifiers when the user only needs a count or a pattern.

Slow database: `data_query` with the engine's own views — Postgres `pg_stat_activity` (running queries, waits), `pg_stat_user_tables` (seq scans), `pg_stat_statements` if installed; MySQL `SHOW FULL PROCESSLIST`, `SHOW ENGINE INNODB STATUS`; Redis `INFO memory`, `SLOWLOG GET 10`. Pair with `server_metrics` to see whether the host is CPU-, memory- or disk-bound.
