# Environment & Commands

## Build workflow

`build.sh` **must be run from the repo root** — the directory that contains
`CMakeLists.txt`. Running it from a subdirectory will fail with "No such
file or directory."

```bash
export VillageSQL_BUILD_DIR=/path/to/villagesql/build
cd extension-name/           # repo root — contains CMakeLists.txt
./build.sh                   # Produces build/<extension_name>.veb
cd build && make install     # Copies .veb to VEB directory
mysql -u root -e "INSTALL EXTENSION <extension_name>;"
```

`build.sh` template: use the version already in the cloned template — it
is correct. Verify it has `set -euo pipefail`, reads `VillageSQL_BUILD_DIR`,
and runs `cmake` + `cmake --build`. If it differs from the template,
update it.

## Test suite layout

```
mysql-test/
├── suite.opt   # Optional suite-wide flags (e.g. --log-error-verbosity=3)
├── t/          # *.test files
└── r/          # *.result files (generated via --record)
```

The suite directory must be named `mysql-test/` to match all other
VillageSQL extensions. Never `test/`.

## Run MTR from `{build_dir}/mysql-test`

Run MTR from `{build_dir}/mysql-test/`. For **prebuilt installs**
(`~/.villagesql/prebuilt/`), this is required — the script uses relative
`@INC` paths that only resolve from within that directory, and running from
anywhere else fails with `Can't locate My/ConfigFactory.pm`. For dev builds,
a wrapper script handles the `chdir` automatically, so working directory
doesn't matter.

```bash
cd {build_dir}/mysql-test
perl mysql-test-run.pl --suite=/absolute/path/to/extension-name/mysql-test
perl mysql-test-run.pl --suite=/absolute/path/to/extension-name/mysql-test --record
```

The `--suite` path must be absolute. A relative path resolves against
`{build_dir}/mysql-test/`, not the extension directory.

## MTR test file syntax

**Comments:** use `#` for comments, not `--`. A bare `--` prefix is not
a comment — it is parsed as a command prefix and will cause a syntax
error or unexpected behaviour.

```
# This is a correct comment
-- This is NOT a comment — do not use this form
```

**`--echo` is a directive, not a comment prefix.** It prints its
argument to the test output and appears in the `.result` file.

**A failing VDF surfaces error 3200 (`ER_UDF_ERROR`).** Both forms work
in a test file: `--error ER_UDF_ERROR` (preferred) or `--error 3200`.

**MySQL reserved words cannot be bare column aliases.** `SELECT 1 AS
generated` is a syntax error in a `.test` file just as in the client —
backtick-quote the alias or pick a different word.

## Common mysqltest directives

```
--echo message
--error ER_WRONG_ARGUMENTS
--disable_warnings / --enable_warnings
--replace_result $MYSQLTEST_VARDIR MYSQLTEST_VARDIR
```

Always use fully-qualified function names: `SELECT vsql_foo.my_func(...)`.
Install at test top, uninstall at bottom (or use `suite.opt`).

## Outbound network calls in tests

Tests that need a local HTTP endpoint must start it deterministically —
hardcoded ports and `--exec ... &` plus a sleep are both flaky under
parallel MTR runs and on slow CI machines:

- **Never hardcode a port.** Bind port 0 (OS-assigned), have the helper
  write the actual port to `$MYSQLTEST_VARDIR/tmp/<name>_port.inc` as a
  `let $port = N;` statement, and `--source` that file in the test. Pass
  the URL to SQL via a session variable set under `--disable_query_log`
  so the port never appears in the `.result` file.
- **Launch with a foreground `--exec` that blocks until ready.** The
  launcher spawns a detached child and exits 0 only after the child has
  bound its port and written the readiness `.inc`. MTR blocks on
  foreground exec, so the helper is listening before the next line runs.
  Do not use `--exec ... &` plus a sleep or poll.
- **Never send the helper's output to `/dev/null`.** Log to a file under
  `$MYSQLTEST_VARDIR/tmp/` so a startup failure is diagnosable, and have
  the launcher print that log on failure.
- **Give the detached child a self-exit watchdog** so it cannot outlive
  an aborted test run.

See `mysql-test/t/vsql_http_requests.test` in
[vsql-http](https://github.com/villagesql/vsql-http) for a complete
reference implementation of this pattern.

## Key paths

- Staged SDK: `{build_dir}/villagesql-extension-sdk-*/` (highest semver —
  filter to directories only, extract MAJOR.MINOR.PATCH, select the max)
- SDK version: `{sdk_dir}/bin/villagesql_config --version`
- SDK headers: `{sdk_dir}/include/` and `{sdk_dir}/include-dev/` (typed
  API may live in either; check both — see Phase 2 bootstrap)
- mysql (dev build): `{build_dir}/runtime_output_directory/mysql`
- mysqld (dev build): `{build_dir}/runtime_output_directory/mysqld`
- VEB directory: query the server (`SHOW VARIABLES LIKE 'veb_dir'`) —
  that value is authoritative. Typical dev-build location is
  `{build_dir}/villagesql/lib/veb/` but production installs vary.

## Row size limit for fixed-length custom types

InnoDB's maximum row size is ~65535 bytes. Fixed-length types (where
`persisted_length` is a constant, not variable) consume their full
allocation in every row regardless of actual content. A single column
of `persisted_length = 65535` will fail `CREATE TABLE` with
`ERROR 1118: Row size too large`.

**Before finalizing `persisted_length` in Phase 1:** run a quick
sanity check — attempt `CREATE TABLE t (col <extension>.<type>)` with
the proposed value. If it fails, reduce the value (65000 is a safe
ceiling that leaves room for row overhead and additional columns). Do
not skip this test — the failure only surfaces at table-creation time,
not at build or install time.

## DDL syntax for custom types

```sql
CREATE TABLE t (col vsql_hstore.hstore);
CREATE TABLE t (col vsql_tvector.tvector(128));              -- integer shorthand
CREATE TABLE t (col vsql_tvector.tvector('dimension=128'));  -- key=value string
```

Extension name must be the install name (e.g., `vsql_hstore`).

CAST is unsupported in **both** directions — custom types aren't wired
into MySQL's CAST grammar. `CAST(... AS <custom_type>)` fails, and so
does `CAST(<custom_column> AS CHAR)` (`ERROR 1221: Incorrect usage of
cast_as_char and <type>`). Other charset-aware string functions
(`CONVERT`, `CHARSET`, `JSON_QUOTE`) fail the same way on custom-type
values. To get a value of a custom type, insert into a column of that
type or call the type's constructor VDF directly; to render one as
text, `SELECT` the column or the constructor result directly — decode
runs automatically. Write acceptance criteria and tests with plain
`SELECT`, not `CAST(... AS CHAR)`.

## Useful commands

- Verify loaded: call one of its functions. There is no `SHOW EXTENSIONS`.
- Uninstall: `UNINSTALL EXTENSION <extension_name>;` — no `IF EXISTS`.
  Use `|| true` in shell. ERROR 3219 when uninstalling a not-installed
  extension is safe to ignore.
- Reinstall (shell): run `UNINSTALL` and `INSTALL` as separate `mysql -e`
  calls.
- Remove cache: `rm -rf <veb_dir>/_expanded/<extension_name>`
- VEB contents: `make show_veb` (from build dir)
- Symbols: `nm -gU <extension>.so | grep vef_register`
