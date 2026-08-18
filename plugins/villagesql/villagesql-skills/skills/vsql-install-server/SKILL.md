---
name: vsql-install-server
description: >
  Get a working VillageSQL server on this machine and prove it works —
  choose an install path (installer, Docker, or source), start the server,
  connect, load a bundled extension, and call one of its functions. Also
  covers reconnecting to a server that is already running. Use before
  vsql-extension-builder, or any time a VillageSQL server is needed and
  none is confirmed working.
---

# VillageSQL Server Install and Verify

Do not skip to installing. A server is often already running, and a second
one on the same port will fail to start.

## Arguments

If invoked as `/vsql-install-server <path>` where `<path>` is `installer`,
`docker`, or `source`, skip Step 1 and use that path.

## Conventions used below

Commands are written against two shell variables so they stay correct when
you change a name. Set them once and use them verbatim afterwards.

```bash
VSQL_CONTAINER=vsql        # Docker path only; any name you like
VSQL_SOCKET=/tmp/mysql.sock  # host paths only; replace with the real socket
```

Every `docker` command below uses `"$VSQL_CONTAINER"`. If you name the
container something else, nothing needs re-editing.

Decide the client invocation once, too. It has two parts: where the client
binary is, and whether a password is needed.

An installer build does **not** put the client on `PATH`, so a bare `mysql`
gives `mysql: command not found`. Take the path from `credentials.txt`:

```bash
VSQL_CLIENT="$HOME/.villagesql/prebuilt/bin/mysql"  # installer build
VSQL_CLIENT=mysql                                   # Docker, or a client already on PATH
```

Every host client call below is written as `"$VSQL_CLIENT" -u root`; the
Docker ones call `mysql` inside the image, where it is always on `PATH`. If
your setup has a root password, add `-p<password>` to **every** one of them;
an empty-password setup needs nothing extra. The client then prints
`[Warning] Using a password on the command line interface can be insecure.`
on stderr — that warning is not output from your statement.

Keep the client *path* in that variable, never a whole command. zsh — the
default shell on macOS — does not word-split an unquoted expansion, so a
variable holding `mysql -u root` is passed as a single argument:
`exec: "mysql -u root": executable file not found in $PATH`.

For Docker, prefix the call with the exec:
`docker exec "$VSQL_CONTAINER" "$VSQL_CLIENT" -u root`.

Error messages are quoted below as the server sends them. `mysql -e` appends
` at line 1`, so a real line reads `ERROR 1064 (42000) at line 1: ...`.

## Step 0 — Is a server already running?

**Skip this entirely on the Docker path.** A container you are about to
create has no server in it yet, and running this check inside a
still-initializing container reports "nothing running" a few seconds before
a server appears. Step 0 is about a host install.

```bash
pgrep -l mysqld
```

If a PID comes back, read its actual arguments rather than assuming the
defaults. On macOS `pgrep -a` does not print arguments; use `ps`:

```bash
ps -o command= -p <PID>
```

`[mysqld] <defunct>` means a dead process nobody reaped, not a server.

From the command line it prints, take the `--socket` and `--port` values, and
the binary's own path — that directory holds the matching client, so set both
variables from what you just read:

```bash
VSQL_SOCKET=<the --socket value>
VSQL_CLIENT=<dir of the mysqld path>/mysql
```

Do not assume `/tmp/mysql.sock`. A machine can have a source build, an
installer build, and a Homebrew MySQL all present, and the socket is the only
reliable way to reach the one that is actually up.

Confirm which server you reached before doing anything else:

```bash
"$VSQL_CLIENT" -u root --socket="$VSQL_SOCKET" -e "SELECT VERSION();"
```

A VillageSQL server reports a version like `8.4.10-villagesql-0.0.6`. If the
version has no `villagesql` in it, you have reached a stock MySQL and should
stop it or pick a different port before continuing.

If a working VillageSQL server is already up, skip to Step 4.

## Step 1 — Choose an install path

| Path | Use when | Gets you |
|---|---|---|
| **Installer** | Default choice. You want to use VillageSQL, or build and test extensions. | Server, client, extension SDK, full MTR suite |
| **Docker** | You want a disposable server, or a machine you do not want to install onto. | Server, client, extension SDK, C++ toolchain, `mysqltest`. **No `mysql-test-run.pl`.** |
| **Source** | You are changing the server itself. | Everything, plus the server build tree |

State the Docker trade-off to the user before they pick it: you can build an
extension and run a single test file by hand inside the container, but the
`mysql-test-run.pl` orchestrator is absent, so a normal `--suite=` run is not
possible there. If the goal is the full `vsql-extension-builder` workflow,
recommend the installer. Details in Step 6.

## Step 2 — Install

### Installer

On a minimal Linux image, install the prerequisites before anything else. The
installer does not install them:

```bash
apt-get update && apt-get install -y curl ca-certificates libaio1t64 libnuma1
```

`curl` and `ca-certificates` are needed to fetch the script at all — without
them the command below fails with `curl: command not found`. `libaio1t64` and
`libnuma1` are needed by the prebuilt `mysqld` binary. A normal desktop
usually has all four; a bare `ubuntu:24.04` has none of them.

The published one-liner is **interactive** and aborts under any
non-interactive shell — which includes every agent, CI job, and
`docker exec`. It exits with:

```
Error: This installer is interactive and requires a terminal.
Re-run it from an interactive shell, or run non-interactively with:
  INSTALL_METHOD=docker|prebuilt|source   (required)
  VSQL_VERSION=stable|nightly|latest      (required for source builds)
```

So always set `INSTALL_METHOD` yourself:

```bash
curl -fsSL https://install.villagesql.com | INSTALL_METHOD=prebuilt bash
```

`prebuilt` downloads a binary release, `source` builds from source, `docker`
delegates to the Docker path. Use `prebuilt` unless told otherwise.

**Do not trust the completion banner.** The installer can print
`✓ Installation Complete!` with a generated root password after database
initialization has already failed — the failure shows up as a
`error while loading shared libraries` line earlier in the output, and the
banner prints anyway. Verify before believing it:

```bash
ls ~/.villagesql/data
```

A real data directory contains InnoDB files (`ibdata1`, `mysql.ibd`,
`undo_001`). If it holds only `auto.cnf` and `binlog.index`, initialization
failed — install the missing libraries above and re-initialize:

```bash
~/.villagesql/prebuilt/bin/mysqld --initialize-insecure \
  --datadir="$HOME/.villagesql/data" --basedir="$HOME/.villagesql/prebuilt"
```

A successful install writes `~/.villagesql/credentials.txt`. Read it — do not
guess paths. It records the install dir, build dir, data dir, port, socket,
log path, the generated root password, and start/connect/stop commands for
this machine. The `villagesql` / `villagesql-server` shortcuts it lists exist
only if `~/.local/bin` already did.

```bash
cat ~/.villagesql/credentials.txt
```

Set the two variables from what that file says, rather than from the defaults
at the top of this page — the socket is not `/tmp/mysql.sock` here:

```bash
VSQL_SOCKET=<the Socket: line>
VSQL_CLIENT=<the MySQL Client: line under Direct Paths>
```

That file contains a password. Do not echo it into a shared transcript, a
commit, or a bug report — note that the installer has already printed it to
stdout twice by this point, so a saved transcript of the install needs the
same care.

**Do not trust that password until you have used it.** Step 3 covers this,
because the check needs a running server.

### Docker

```bash
docker run -d --name "$VSQL_CONTAINER" \
  -e MYSQL_ALLOW_EMPTY_PASSWORD=yes \
  -p 3306:3306 \
  villagesql/server:stable
```

The image is roughly 1.5GB and the first run pulls it. A locally present
`villagesql/server:latest` is a **different tag** and is not a substitute —
pull `:stable` explicitly if you need it.

Before using `-p 3306:3306`, check the host port is free. `pgrep` does not
answer this, because any process can hold a port:

```bash
lsof -nP -iTCP:3306 -sTCP:LISTEN    # macOS
ss -ltnp '( sport = :3306 )'        # Linux
```

If something holds it, either publish a different host port
(`-p 3307:3306`) or drop `-p` entirely and work through
`docker exec`, which needs no published port at all.

Exactly one of `MYSQL_ROOT_PASSWORD`, `MYSQL_ALLOW_EMPTY_PASSWORD`, or
`MYSQL_RANDOM_ROOT_PASSWORD` is required; with none set the container exits 1
and says so. `MYSQL_DATABASE`, `MYSQL_USER`, and `MYSQL_PASSWORD` also work.

If you choose anything other than `MYSQL_ALLOW_EMPTY_PASSWORD`, every
subsequent `mysql` call needs the password. Omitting it gives:

```
ERROR 1045 (28000): Access denied for user 'root'@'localhost' (using password: NO)
```

Add `-p<password>` to every client call, as in the Conventions section.

To pass server flags, append `mysqld` and the flags after the image name:

```bash
docker run -d --name "$VSQL_CONTAINER" -e MYSQL_ALLOW_EMPTY_PASSWORD=yes \
  villagesql/server:stable mysqld --vsql_allow_preview_extensions=ON
```

The `mysql` client lives inside the image, so with no published port
`docker exec` is the only access path.

### Source

Follow the server repo build instructions. Build the server before any
extension — extensions need the SDK that the server build produces.

## Step 3 — Start the server

For an installer or source install, use the command `credentials.txt` prints
for this machine — adding `--user=root` if you are root — rather than
composing one. It looks like this:

```bash
<build-dir>/bin/mysqld --datadir=<data-dir> --socket=<socket> \
  --port=<port> --daemonize
```

`credentials.txt` distinguishes the two: `Installation:` is `~/.villagesql`,
while the binaries live under `Build Dir:` — `~/.villagesql/prebuilt/bin`.

Three things that reliably bite:

- **Never write `--datadir=~/...`.** No shell expands `~` after `=`, so
  mysqld receives a literal `~` and aborts. Use `$HOME` or an absolute path.
- **Running as root needs `--user=root`.** Containers and many CI images run
  as root, and the installer leaves this flag out of the command it writes
  into `credentials.txt` (still true of 0.0.5, the current release). Without it mysqld refuses to start: `[ERROR] [MY-010123] [Server] Fatal
  error: Please read "Security" section of the manual to find out how to run
  mysqld as root!`
- **`vsql_allow_preview_extensions` defaults to `OFF`.** Some bundled
  extensions (`vsql_rest`, for instance) will not install without it, failing
  with `ERROR 3219 (HY000): Failed to load VEF extension '<name>': extension
  requires preview capabilities but vsql_allow_preview_extensions is OFF`.
  Set it at startup, or afterwards with `SET PERSIST` — which takes effect
  immediately, no restart needed. `SET GLOBAL` is rejected: `ERROR 3219
  (HY000): vsql_allow_preview_extensions must be set with SET PERSIST, not
  SET GLOBAL, to ensure the setting survives server restart`. On builds
  before 2026-08-10 the `OFF` direction was accepted instead, silently
  disabling preview extensions on the running server, so avoid `SET GLOBAL`
  here whatever your version reports.

**On an installer or source install, check the root password now.** An
installer whose own temporary server failed to start writes the password it
generated without ever applying it, leaving root reachable with an **empty**
password while `credentials.txt` and the completion banner both say
otherwise. This is most likely when installing as root, the normal case in
containers and CI:

```bash
"$VSQL_CLIENT" -u root -p'<password from credentials.txt>' \
  --socket="$VSQL_SOCKET" -e "SELECT 1;"
```

If that gives `ERROR 1045 (28000): Access denied for user 'root'@'localhost'
(using password: YES)`, try again with no password at all. If *that* works,
the database is unprotected — set the password yourself:

```sql
ALTER USER 'root'@'localhost' IDENTIFIED BY '<password from credentials.txt>';
```

Re-running the installer over the existing data directory also repairs this.
Either way, every client call from here on needs `-p<password>`.

A Docker container started with `-d` is already running, but is not ready
immediately. Wait for readiness with a **bounded** loop — an unbounded
`until` loop hangs forever on a container that crashes during init, and
`timeout` does not exist on macOS. Note that `mysqladmin ping --silent`
prints `mysqld is alive` on stdout, so redirect both streams:

A ping alone is not enough. The image's entrypoint starts a **temporary
server** during initialization — visible in the logs as `port: 0` — then
stops it and starts the real one. `mysqladmin ping` answers for both, so a
loop that breaks on the first success can return seconds before the durable
server exists, and the next statement dies with `ERROR 2013 (HY000): Lost
connection to MySQL server during query`. Require the log line for the real
port as well, and keep a flag so an expiry is distinguishable from success:

```bash
ready=0
for i in $(seq 1 60); do
  if docker exec "$VSQL_CONTAINER" mysqladmin ping --silent >/dev/null 2>&1 \
     && docker logs "$VSQL_CONTAINER" 2>&1 | grep -q 'ready for connections.*port: 3306'; then
    ready=1; break
  fi
  sleep 2
done
```

If it expired, read the logs rather than retrying blindly:

```bash
[ "$ready" = 1 ] || docker logs "$VSQL_CONTAINER" | tail -30
```

## Step 4 — Connect and confirm the build

```bash
"$VSQL_CLIENT" -u root --socket="$VSQL_SOCKET" -e "SELECT VERSION();"   # host
docker exec "$VSQL_CONTAINER" mysql -u root -e "SELECT VERSION();"     # Docker
```

Report the version string back to the user. This is the one fact that
everything downstream depends on.

## Step 5 — Load an extension and call it

Shipping a server is not the same as having a working extension pipeline.
Prove the pipeline with a bundled extension.

Several extensions ship pre-built with the installer, the Docker image, and
the release tarballs, so there is nothing to download. Do not hardcode the
list or the directory — ask the server where it looks, then list it:

```sql
SHOW VARIABLES LIKE 'veb_dir';
```

Listing it is a shell command, not SQL — `ls <veb_dir>` on a host install, or
`docker exec "$VSQL_CONTAINER" ls <veb_dir>` for a container.

It is `/usr/lib/veb/` in the Docker image and
`<build-or-install-dir>/lib/veb/` for a source or installer build.

A hand-rolled source build is the exception: it produces no bundled `.veb`
files, so that directory can legitimately be empty.

**Choose an extension from the listing you just made** — do not assume any
particular one is present. `vsql_uuid` is used in the examples below because
it is usually bundled and has zero-argument functions; substitute whatever
your listing actually shows, and read its function names from
`REGISTRATION_JSON` as described further down.

Shipping the `.veb` is not the same as installing the extension. Install it:

```sql
INSTALL EXTENSION vsql_uuid;
```

**Success is silent.** No rows, no `Query OK` — an exit code of 0 and empty
output means it worked. Confirm with a query rather than looking for a
success message.

The extension name is a **bare SQL identifier**. Quoting it is a syntax
error:

```
ERROR 1064 (42000): You have an error in your SQL syntax; check the manual that
corresponds to your MySQL server version for the right syntax to use near
''vsql_uuid'' at line 1
```

A name containing hyphens needs backticks. `VERSION 'x.y.z'` is a string
literal and does keep its quotes.

Confirm it registered:

```sql
SELECT EXTENSION_NAME, EXTENSION_VERSION FROM INFORMATION_SCHEMA.EXTENSIONS;
```

The columns are `EXTENSION_NAME`, `EXTENSION_VERSION`, `PENDING_VERSION`,
`PENDING_REQUESTED_AT`, `PENDING_LAST_ERROR`, `PENDING_LAST_ERROR_AT`. Using
`NAME` or `VERSION` gives:

```
ERROR 1054 (42S22): Unknown column 'NAME' in 'field list'
```

Extension functions are **absent from `INFORMATION_SCHEMA.ROUTINES`**. That
view is not empty — a fresh server has around 48 rows in it, all from the
`sys` schema — but no extension function ever appears there, so a
`WHERE ROUTINE_NAME LIKE 'UUID%'` returns 0 rows even when the extension is
installed and working. That is expected, not a fault.

`INFORMATION_SCHEMA.EXTENSION_REGISTRATION.REGISTRATION_JSON` is the
authoritative list of an extension's functions, with return types, parameter
types and arity. Read it instead of guessing a function name:

```sql
SELECT REGISTRATION_JSON FROM INFORMATION_SCHEMA.EXTENSION_REGISTRATION
  WHERE EXTENSION_NAME = 'vsql_uuid';
```

Its `funcs` array is what you want. Its top-level `extension_name` and
`extension_version` fields may be empty strings even for a correctly
installed extension — that is not a sign of a problem;
`INFORMATION_SCHEMA.EXTENSIONS` carries the authoritative name and version.

Then call a function. No database needs to be selected:

```sql
SELECT UUID_V4();
SELECT UUID_VERSION(UUID_V4());
```

Do not carry PostgreSQL names across. `vsql_uuid` provides `UUID_V4()`, not
`uuid_generate_v4()`.

If the name does not resolve, the error depends on whether a database is
selected, and the no-database form is misleading — it reports a database
problem when the real problem is an unknown function:

```
ERROR 1046 (3D000): No database selected
ERROR 1305 (42000): FUNCTION demo.no_such_fn does not exist
```

So if you hit `ERROR 1046` on a function call, do not go hunting for a
database issue. Select any database and re-run to get the error that names
the function.

If the arity is wrong, the server says so exactly — check
`REGISTRATION_JSON` rather than guessing:

```
ERROR 3219 (HY000): Cannot initialize function '<name>': wrong number of arguments (expected 0, got 1)
```

Re-running an install that already succeeded is harmless and self-reporting:

```
ERROR 3219 (HY000): Extension '<name>' is already installed
```

## Step 6 — Building an extension in Docker

Only relevant if the user chose Docker and wants to build their own
extension.

This **replaces** the container from Step 2 rather than adding to it. Docker
cannot add a mount to a running container, so remove the old one and create a
new one with the source mounted:

```bash
docker rm -f "$VSQL_CONTAINER"
docker run -d --name "$VSQL_CONTAINER" -e MYSQL_ALLOW_EMPTY_PASSWORD=yes \
  -v /path/to/my-extension:/src:ro villagesql/server:stable
```

The new container starts with an empty data directory, so the extension you
installed in Step 5 is gone with the old one — redo that step here. If you
know in advance that you will build an extension, add the `-v` mount in
Step 2 and skip this replacement entirely.

Wait for readiness again with the bounded loop from Step 3, then build:

```bash
docker exec "$VSQL_CONTAINER" bash -c 'cp -r /src /work && vsql-build-extension.sh /work'
```

The image ships the SDK at `/usr/include/villagesql/`, its CMake package at
`/usr/lib/cmake/VillageSQLExtensionFramework/`, a C++ toolchain, and that
helper, which runs cmake and make, installs the resulting `.veb` into
`veb_dir`, and waits for the server. Then `INSTALL EXTENSION` it as in Step 5.

Mount read-only and copy to `/work` as shown. The helper builds into
`<source>/_docker_build`, which would otherwise write build output into your
host checkout.

### Testing in the container

Be precise about what is and is not available. `mysqltest` (the test
executor) and `perl` are both in the image. What is missing is
`mysql-test-run.pl`, the orchestrator that stages suites, substitutes
`$MYSQLTEST_VARDIR`, manages workers, and starts and stops servers.

So a single test file can be run by hand against the already-running server:

```bash
docker exec "$VSQL_CONTAINER" mysqltest -u root \
  --test-file=/work/mysql-test/t/<name>.test \
  --result-file=/work/mysql-test/r/<name>.result
```

If the test file begins with `INSTALL EXTENSION`, run
`UNINSTALL EXTENSION <name>;` first — the
orchestrator normally provides the clean state that the file assumes, and
without it the test fails with `already installed`.

What you cannot do in this image is a normal `--suite=` run, anything relying
on `$MYSQLTEST_VARDIR`, parallel workers, or multi-file suite management. For
that, and for the `vsql-extension-builder` test phase, use an installer or
source build.

## Step 7 — Report

Tell the user, in plain words:

- which install path was used, and where things live
- the `SELECT VERSION()` output
- which extension was installed and what the function call returned
- the exact connect command for this machine — including the container name
  and, for a container with no published port, the `docker exec` form
- if Docker: that `mysql-test-run.pl` is unavailable, so extension test
  suites need an installer or source build

## Extensions, plugins, and components

VillageSQL is a drop-in MySQL replacement, so MySQL plugins and components
work as they do in MySQL, while VEF extensions are the model for adding new
functionality and the only one that can define custom column types. Do not
re-explain the comparison in your own words — point the user at
[Extensions or Plugins and Components](https://villagesql.com/docs/mysql-8.4/stable/extensions-or-plugins),
which exists for exactly this question.

## Common failures

| Symptom | Cause |
|---|---|
| Installer aborts saying it requires a terminal | Expected under any agent, CI job, or `docker exec`. Set `INSTALL_METHOD=prebuilt` (or `source`/`docker`). |
| `✓ Installation Complete!` but the server will not start | The banner can print over a failed initialization. Check `~/.villagesql/data` for InnoDB files; install `libaio1t64` and `libnuma1` and re-initialize. |
| `error while loading shared libraries: libaio.so.1t64` or `libnuma.so.1` | Missing OS packages the installer neither checks nor installs. `apt-get install -y libaio1t64 libnuma1`. |
| `Fatal error: Please read "Security" section ... run mysqld as root` | Running as root without `--user=root`. |
| Server will not start, port in use | Something else holds the port. Find it with `lsof -nP -iTCP:3306 -sTCP:LISTEN` (macOS) or `ss -ltnp` (Linux); stop it or pick another port. |
| mysqld aborts complaining about the data directory | `--datadir=~/...` passed a literal `~`. Use `$HOME` or an absolute path. |
| Connects, but version has no `villagesql` | You reached a stock MySQL. Re-check the socket from `ps`. |
| `No such container: vsql` | The container name in this skill is a placeholder. Set `VSQL_CONTAINER` and use it everywhere. |
| `ERROR 1045 (28000): Access denied ... (using password: NO)` | The container was started with a root password but the client call omits it. Add `-p<password>`. |
| `ERROR 1045 (28000): Access denied ... (using password: YES)` using the password from `credentials.txt` | The installer never applied it. Connect with no password; if that works, set the password yourself or re-run the installer. |
| `mysql: command not found` after an installer install | The client is not on `PATH`. Use the full path from `credentials.txt` — see `VSQL_CLIENT` in Conventions. |
| Readiness loop never returns | Container died during init. `docker logs <name> \| tail -30`. |
| `ERROR 1064` on `INSTALL EXTENSION` | The extension name was quoted. It is a bare identifier. |
| `ERROR 3219 (HY000): VEB file not found: <name>.veb` | The `.veb` is not in `veb_dir`. List that directory and check the spelling. |
| Rebuilt an extension, still see old behaviour | The old `.veb` is still what the server loads. `SHOW VARIABLES LIKE 'veb_dir'` to find the directory the server actually reads, and put the rebuilt file there — copying it into `lib/plugin` does nothing. Check `EXTENSION_VERSION` in `INFORMATION_SCHEMA.EXTENSIONS` to confirm which build is live, and install with an explicit `VERSION 'x.y.z'` so a stale `.veb` fails loudly instead of silently. |
| `ERROR 1046 (3D000): No database selected` on a function call | Misleading. The function name did not resolve and there was no default schema to name in the error. `USE` any database and re-run to get `ERROR 1305` naming the function. |
| Extension installed but its functions are missing from `INFORMATION_SCHEMA.ROUTINES` | Expected. VEF functions never appear there, though the view itself is not empty. Use `INFORMATION_SCHEMA.EXTENSION_REGISTRATION`. |
| `INSTALL EXTENSION` printed nothing | That is success. Confirm with `INFORMATION_SCHEMA.EXTENSIONS`. |
