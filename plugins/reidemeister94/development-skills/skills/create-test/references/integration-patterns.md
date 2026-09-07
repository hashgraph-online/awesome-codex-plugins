# Deep Integration

Use the real engine, protocol, and serialization at the boundary under test. Don't point a test at production unless explicitly requested and confirmed from the user.

Guard database fixtures with an allow-list for test or development hosts and databases. Fail before setup if the target is not explicitly safe.

Choose db isolation from the behavior under test:

- no commit: wrap each test in a transaction and roll it back;
- code commits: clean owned tables with `TRUNCATE … CASCADE`;
- DDL or full isolation: clone a prepared test database.
