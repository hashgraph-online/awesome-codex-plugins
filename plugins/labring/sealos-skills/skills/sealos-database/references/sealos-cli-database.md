# sealos-cli Database Reference

Use `sealos-cli` as the execution layer for Sealos Cloud database work. It is a Node.js Commander CLI whose database commands call `dbprovider.<region>/api/v2alpha` with auth from `~/.sealos/kubeconfig`.

## Install and Auth

Prefer an existing binary:

```bash
sealos-cli --version
sealos-cli whoami
```

Use one-off execution when the binary is missing:

```bash
npx -y sealos-cli@latest --version
```

Authenticate and choose the workspace:

```bash
sealos-cli login https://usw-1.sealos.io
sealos-cli workspace list
sealos-cli workspace switch <workspace-id-or-team-name>
sealos-cli workspace current
```

`sealos-cli` stores auth metadata at `~/.sealos/auth.json` and the active workspace kubeconfig at `~/.sealos/kubeconfig`. Do not print or commit these files.

## Provider Host Resolution

Database commands use this precedence:

1. `SEALOS_DATABASE_HOST` if set.
2. `SEALOS_REGION` if set, rewritten to `dbprovider.<region-host>`.
3. Region saved by `sealos-cli login`, rewritten to `dbprovider.<region-host>`.
4. Default region.

## Read Commands

Use JSON for automation:

```bash
sealos-cli database list -o json
sealos-cli database versions -o json
sealos-cli database versions --type postgresql -o json
sealos-cli database get <name> -o json
sealos-cli database connection <name> -o json
sealos-cli database backups <name> -o json
```

`database connection` may return private and public connection fields. Prefer private details for apps running inside Sealos/Devbox. Public access may be disabled by default.

## Create and Update

Create with conservative development resources unless project needs say otherwise:

```bash
sealos-cli database create postgresql --name <name> --cpu 1 --memory 1 --storage 3 --replicas 1 -o json
```

Supported create types:

- `postgresql`
- `mongodb`
- `mysql`
- `apecloud-mysql`
- `redis`
- `kafka`
- `qdrant`
- `nebula`
- `weaviate`
- `milvus`
- `pulsar`
- `clickhouse`

Useful options:

```bash
--version <version>
--cpu <cpu>
--memory <gb>
--storage <gb>
--replicas <count>
--termination-policy <delete|wipeout>
--backup-start
--backup-type <day|hour|week>
--backup-week <day>
--backup-hour <00-23>
--backup-minute <00-59>
--backup-save-time <count>
--backup-save-type <days|hours|weeks|months>
--param KEY=VALUE
```

Update resources:

```bash
sealos-cli database update <name> --cpu 2 --memory 4 --storage 10 -o json
```

## Operations

Non-destructive lifecycle operations:

```bash
sealos-cli database start <name> -o json
sealos-cli database pause <name> -o json
sealos-cli database restart <name> -o json
```

Backups:

```bash
sealos-cli database backup <name> --name <backup-name> -o json
sealos-cli database backups <name> -o json
sealos-cli database restore <name> --from <backup-name> --name <restored-name> -o json
```

Public access:

```bash
sealos-cli database enable-public <name> -o json
sealos-cli database disable-public <name> -o json
```

Ask before enabling public access. Disable it after local-machine testing when it is no longer needed.

Destructive commands require explicit user confirmation:

```bash
sealos-cli database delete <name> -o json
sealos-cli database backup-delete <databaseName> <backupName> -o json
```

## Logs

Discover log files before reading logs:

```bash
sealos-cli database log-files <pod-name> --db-type postgresql --log-type runtimeLog -o json
sealos-cli database logs <pod-name> --db-type postgresql --log-type runtimeLog --log-path <path> -o json
```

Supported log DB types are `postgresql`, `mongodb`, `mysql`, and `redis`. Supported log types are `runtimeLog`, `slowQuery`, and `errorLog`.

## Response Handling

Expect JSON by default. Treat operation responses with `status: "requested"` as asynchronous. Poll `database get` or `database connection` until the database status and connection fields are ready.

Do not rely on table output for automation. Table output is only for human inspection with `-o table`.
