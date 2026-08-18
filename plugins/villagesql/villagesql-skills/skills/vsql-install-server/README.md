# vsql-install-server

A skill that gets a working VillageSQL server onto a machine and proves it
works, ending with a bundled extension installed and one of its functions
returning a value.

Use it before [`vsql-extension-builder`](../vsql-extension-builder/), or any
time a VillageSQL server is needed and none is confirmed running.

## What it does

1. Checks whether a server is already running, and reads its real socket and
   port from the process arguments instead of assuming defaults
2. Picks an install path — installer, Docker, or source — and explains the
   trade-off before installing anything
3. Installs and starts the server
4. Connects and confirms the build is actually VillageSQL
5. Installs a bundled extension and calls one of its functions
6. Reports paths, version, and the exact connect command for this machine

## Prerequisites

None beyond a shell. The skill installs what it needs. For the Docker path,
a running Docker daemon.

## Install paths, and what each one gives you

| Path | Server | Extension SDK | `mysqltest` | `mysql-test-run.pl` |
|---|---|---|---|---|
| Installer (`install.villagesql.com`) | yes | yes | yes | yes |
| Docker (`villagesql/server`) | yes | yes | yes | **no** |
| Source build | yes | yes | yes | yes |

The Docker image ships the SDK headers, its CMake package, a C++ toolchain,
and a `vsql-build-extension.sh` helper, so building and installing an
extension inside the container works. It is built with
`-DINSTALL_MYSQLTESTDIR=""` and excludes the test suites, so the
`mysql-test-run.pl` orchestrator is absent — but `mysqltest` itself is
present, so a single `.test`/`.result` pair can be run by hand against the
running server. A normal `--suite=` run, anything using
`$MYSQLTEST_VARDIR`, and the `vsql-extension-builder` test phase need the
installer or a source build.

The installer has two traps worth knowing before you start: its published
one-liner is interactive and aborts under any agent or CI shell unless you set
`INSTALL_METHOD`, and it can print a success banner over a failed database
initialization. The skill handles both.

## Extensions, plugins, and components

The skill does not re-explain this. VEF extensions are the model for adding
functionality to VillageSQL and the only one that can define custom column
types; MySQL plugins and components still work because VillageSQL is a
drop-in replacement. The comparison lives in the documentation, at
[Extensions or Plugins and Components](https://villagesql.com/docs/mysql-8.4/stable/extensions-or-plugins).

## Entry point

The agent loads [`SKILL.md`](SKILL.md).

## Invoking

```
/vsql-install-server
/vsql-install-server docker
```

Passing `installer`, `docker`, or `source` skips the path question.
