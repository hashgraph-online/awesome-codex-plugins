# CLI Reference (generated — do not edit)

> Regenerate: `python api/scripts/skill-truth/generate.py`. CI enforces freshness.

## `admin`

```
Usage: admin [OPTIONS] COMMAND [ARGS]...

  Platform administration.

Options:
  --json  Emit JSON instead of human-readable output.
  --help  Show this message and exit.

Commands:
  authz  Inspect runtime credentials and the authority version.
```

### `admin authz`

```
Usage: admin authz [OPTIONS] COMMAND [ARGS]...

  Inspect runtime credentials and the authority version.

Options:
  --json  Emit JSON instead of human-readable output.
  --help  Show this message and exit.

Commands:
  legacy-status  List live runs and remote launchers still on legacy...
```

#### `admin authz legacy-status`

```
Usage: admin authz legacy-status [OPTIONS]

  List live runs and remote launchers still on legacy runtime credentials.

  Restart a listed service attempt through the normal service restart (it
  relaunches with new-format credentials) and upgrade a listed launcher;
  legacy workflow runs end on their own.

Options:
  --json  Emit JSON instead of human-readable output.
  --help  Show this message and exit.
```

## `agents`

```
Usage: agents [OPTIONS] COMMAND [ARGS]...

  Manage agents.

Options:
  --json  Emit JSON instead of human-readable output.
  --help  Show this message and exit.

Commands:
  create  Create a new agent.
  delete  Permanently delete an agent.
  get     Get a single agent by UUID or name.
  list    List active agents by default.
  update  Update an agent.
```

### `agents create`

```
Usage: agents create [OPTIONS]

  Create a new agent.

  ``--system-prompt @file.md`` loads the prompt from disk. ``--tool-ids`` and
  ``--delegated-agent-ids`` resolve each entry via the ref resolver before the
  body is sent.

  Org targeting follows the unified ``--org`` standard: HOME (omit) scopes the
  agent to the caller's org, ``--global`` makes it global, ``--org <id|name>``
  scopes it to that org. (Non-admins may only create private agents in their
  own org regardless.)

Options:
  --name TEXT                     name  [required]
  --description TEXT              description
  --system-prompt TEXT            system_prompt  [required]
  --channels TEXT                 channels (repeat for multiple).
  --access-level [authenticated|everyone|role_based|private]
                                  access_level
  --tool-ids TEXT                 tool_ids (repeat for multiple; comma-split
                                  also accepted).
  --delegated-agent-ids TEXT      delegated_agent_ids (repeat for multiple;
                                  comma-split also accepted).
  --role-ids TEXT                 role_ids (repeat for multiple; comma-split
                                  also accepted).
  --knowledge-sources TEXT        knowledge_sources (repeat for multiple).
  --system-tools TEXT             system_tools (repeat for multiple).
  --mcp-connection-ids TEXT       mcp_connection_ids (repeat for multiple;
                                  comma-split also accepted).
  --llm-profile-id TEXT           llm_profile_id (UUID).
  --llm-max-tokens INTEGER        llm_max_tokens
  --max-iterations INTEGER        max_iterations
  --max-token-budget INTEGER      max_token_budget
  --global                        Target global scope (org=NULL). Alias for
                                  --org global.
  --org, --organization, --scope TEXT
                                  Org UUID/name, or 'none'/'global' for global
                                  scope. Omit = your org. (--organization /
                                  --scope are synonyms.)
  --json                          Emit JSON instead of human-readable output.
  --help                          Show this message and exit.
```

### `agents delete`

```
Usage: agents delete [OPTIONS] REF

  Permanently delete an agent.

  ``REF`` is a UUID or agent name. The server returns ``204 No Content`` on
  success; the CLI reports the resolved UUID.

Options:
  --json  Emit JSON instead of human-readable output.
  --help  Show this message and exit.
```

### `agents get`

```
Usage: agents get [OPTIONS] REF

  Get a single agent by UUID or name.

Options:
  --json  Emit JSON instead of human-readable output.
  --help  Show this message and exit.
```

### `agents list`

```
Usage: agents list [OPTIONS]

  List active agents by default.

Options:
  --include-inactive  Include inactive agents.
  --json              Emit JSON instead of human-readable output.
  --help              Show this message and exit.
```

### `agents update`

```
Usage: agents update [OPTIONS] REF

  Update an agent.

  ``REF`` is a UUID or agent name. Names are resolved via
  :class:`RefResolver`; ambiguous names fail loudly with the candidate list.
  The verb is **PUT** per the cli-mutation-surface audit correction.

  Passing ``--org``/``--global`` re-scopes the agent (HOME leaves the scope
  unchanged, since omitting org sends no ``organization_id``).

Options:
  --name TEXT                     name
  --description TEXT              description
  --system-prompt TEXT            system_prompt
  --channels TEXT                 channels (repeat for multiple).
  --access-level [authenticated|everyone|role_based|private]
                                  access_level
  --is-active / --no-is-active    is_active (tri-state; omit to leave
                                  unchanged).
  --tool-ids TEXT                 tool_ids (repeat for multiple; comma-split
                                  also accepted).
  --delegated-agent-ids TEXT      delegated_agent_ids (repeat for multiple;
                                  comma-split also accepted).
  --role-ids TEXT                 role_ids (repeat for multiple; comma-split
                                  also accepted).
  --knowledge-sources TEXT        knowledge_sources (repeat for multiple).
  --system-tools TEXT             system_tools (repeat for multiple).
  --mcp-connection-ids TEXT       mcp_connection_ids (repeat for multiple;
                                  comma-split also accepted).
  --clear-roles / --no-clear-roles
                                  clear_roles (tri-state; omit to leave
                                  unchanged).
  --llm-profile-id TEXT           llm_profile_id (UUID).
  --llm-max-tokens INTEGER        llm_max_tokens
  --max-iterations INTEGER        max_iterations
  --max-token-budget INTEGER      max_token_budget
  --global                        Target global scope (org=NULL). Alias for
                                  --org global.
  --org, --organization, --scope TEXT
                                  Org UUID/name, or 'none'/'global' for global
                                  scope. Omit = your org. (--organization /
                                  --scope are synonyms.)
  --json                          Emit JSON instead of human-readable output.
  --help                          Show this message and exit.
```

## `app`

```
Usage: app [OPTIONS] COMMAND [ARGS]...

  Create, bind, run, and deploy an App project.

Options:
  --help  Show this message and exit.

Commands:
  bind        Bind a cloned Vite project to an existing App.
  create      Create a Vite project and its remote App record.
  deploy      Build and atomically deploy the current App project.
  migrate     Migrate a pulled v1 App directory into an independent V2...
  start       Run the local Vite App against live Bifrost resources.
  swap-slugs  Atomically exchange v1 and independent V2 App slugs during...
```

### `app bind`

```
Usage: app bind [OPTIONS] REF [PATH]

  Bind a cloned Vite project to an existing App.

Options:
  --url TEXT  Bifrost instance URL.
  --help      Show this message and exit.
```

### `app create`

```
Usage: app create [OPTIONS] [PATH]

  Create a Vite project and its remote App record.

Options:
  --name TEXT  App display name (default: directory name).
  --slug TEXT  URL slug (default: derived from name).
  --org TEXT   Organization UUID or name.
  --global     Create a globally visible App.
  --url TEXT   Bifrost instance URL.
  --help       Show this message and exit.
```

### `app deploy`

```
Usage: app deploy [OPTIONS] [PATH]

  Build and atomically deploy the current App project.

Options:
  --help  Show this message and exit.
```

### `app migrate`

```
Usage: app migrate [OPTIONS] SOURCE PATH

  Migrate a pulled v1 App directory into an independent V2 App project.

Options:
  --name TEXT  App display name (default: destination name).
  --slug TEXT  Temporary V2 URL slug (default: derived from name).
  --org TEXT   Organization UUID or name.
  --global     Create a globally visible App.
  --url TEXT   Bifrost instance URL.
  --help       Show this message and exit.
```

### `app start`

```
Usage: app start [OPTIONS] [PATH]

  Run the local Vite App against live Bifrost resources.

Options:
  --org TEXT         Run against another authorized organization.
  --port INTEGER     [default: 3000]
  --host TEXT        [default: 127.0.0.1]
  --public-url TEXT
  --help             Show this message and exit.
```

### `app swap-slugs`

```
Usage: app swap-slugs [OPTIONS] APP_A APP_B

  Atomically exchange v1 and independent V2 App slugs during cutover.

Options:
  --url TEXT  Bifrost instance URL.
  --help      Show this message and exit.
```

## `apps`

```
Usage: apps [OPTIONS] COMMAND [ARGS]...

  Manage applications.

Options:
  --json  Emit JSON instead of human-readable output.
  --help  Show this message and exit.

Commands:
  create    Create a new application, optionally seeding npm dependencies.
  delete    Delete an application.
  get       Get a single application by slug, UUID, or name.
  list      List all applications (wrapped ``{applications, total}``...
  publish   Rebuild and publish an application, polling durable progress.
  replace   Repoint an application's source directory.
  sdk       Inspect or update deployed App SDK bundles.
  set-deps  Replace an application's npm dependencies.
  source    Download retained deployed App source artifacts.
  update    Update application metadata (patch-without-draft).
```

### `apps create`

```
Usage: apps create [OPTIONS]

  Create a new application, optionally seeding npm dependencies.

  ``--organization`` accepts a UUID or org name. ``--role-ids`` accepts
  repeated values or a comma-separated list; entries may be role names or
  UUIDs.

  When ``--deps`` is passed this runs as a two-call orchestration: the app is
  created first, then a ``PUT /dependencies`` applies the parsed dependency
  dict. If the deps call fails after the create succeeded, the command prints
  both the created app and the deps error, exits non-zero, and leaves the app
  in place — there is no rollback.

Options:
  --name TEXT          name  [required]
  --description TEXT   description
  --slug TEXT          slug  [required]
  --access-level TEXT  access_level
  --app-model TEXT     app_model
  --role-ids TEXT      role_ids (repeat for multiple; comma-split also
                       accepted).
  --organization TEXT  org ref (UUID or name) for organization_id.
  --deps TEXT          Dependencies as a JSON literal or @path to a
                       package.json / {name: version} file. Triggers a follow-
                       up PUT to /dependencies after the app is created.
  --json               Emit JSON instead of human-readable output.
  --help               Show this message and exit.
```

### `apps delete`

```
Usage: apps delete [OPTIONS] REF

  Delete an application.

  ``REF`` is a slug, UUID, or application name.

Options:
  --json  Emit JSON instead of human-readable output.
  --help  Show this message and exit.
```

### `apps get`

```
Usage: apps get [OPTIONS] REF

  Get a single application by slug, UUID, or name.

  The public per-record endpoint is keyed by slug. For slug refs we hit ``GET
  /api/applications/{slug}`` directly. For UUID / name refs we resolve to a
  UUID then locate the matching record from the list payload so this command
  works with any ref shape :class:`RefResolver` accepts.

  Inside a BOUND solution workspace (BIFROST_SOLUTION_ID set), the install's
  OWN apps are preferred: a generic ref like "portal" must not silently
  resolve an unrelated global app when the workspace's app matches by slug or
  name.

Options:
  --json  Emit JSON instead of human-readable output.
  --help  Show this message and exit.
```

### `apps list`

```
Usage: apps list [OPTIONS]

  List all applications (wrapped ``{applications, total}`` payload).

Options:
  --json  Emit JSON instead of human-readable output.
  --help  Show this message and exit.
```

### `apps publish`

```
Usage: apps publish [OPTIONS] REF

  Rebuild and publish an application, polling durable progress.

  ``REF`` is a slug, UUID, or application name. The enqueue request returns
  quickly; this command then polls short status requests, so a multi-minute
  build cannot hit the client's per-request 30-second timeout.

Options:
  --message TEXT  Optional publish message (maximum 500 characters).
  --json          Emit JSON instead of human-readable output.
  --help          Show this message and exit.
```

### `apps replace`

```
Usage: apps replace [OPTIONS] REF

  Repoint an application's source directory.

  ``REF`` is a slug, UUID, or application name. ``--repo-path`` must be the
  workspace-relative path to the new source directory. By default the path
  must already contain files; ``--force`` bypasses that check (and uniqueness
  / nesting checks) for repointing ahead of a push.

Options:
  --repo-path TEXT  Workspace-relative path to the new source directory (e.g.
                    apps/my-app-v2).  [required]
  --force           Bypass the uniqueness, nesting, and source-exists checks.
                    Use when repointing before files are pushed.
  --json            Emit JSON instead of human-readable output.
  --help            Show this message and exit.
```

### `apps sdk`

```
Usage: apps sdk [OPTIONS] COMMAND [ARGS]...

  Inspect or update deployed App SDK bundles.

Options:
  --json  Emit JSON instead of human-readable output.
  --help  Show this message and exit.

Commands:
  status  Show SDK provenance/status for one deployed App, or all visible...
  update  Queue deployed App SDK rebuild/update jobs and follow their...
```

#### `apps sdk status`

```
Usage: apps sdk status [OPTIONS] [REF]

  Show SDK provenance/status for one deployed App, or all visible Apps.

Options:
  --help  Show this message and exit.
```

#### `apps sdk update`

```
Usage: apps sdk update [OPTIONS] [REF]

  Queue deployed App SDK rebuild/update jobs and follow their progress.

Options:
  --all   Update every actionable visible App.
  --help  Show this message and exit.
```

### `apps set-deps`

```
Usage: apps set-deps [OPTIONS] REF

  Replace an application's npm dependencies.

  ``REF`` is a slug, UUID, or application name. The ``--deps`` value is either
  a JSON object literal or ``@path/to/package.json``; package.json's
  ``dependencies`` key is extracted automatically.

Options:
  --deps TEXT  Dependencies as a JSON literal or @path to a package.json /
               {name: version} file.  [required]
  --json       Emit JSON instead of human-readable output.
  --help       Show this message and exit.
```

### `apps source`

```
Usage: apps source [OPTIONS] COMMAND [ARGS]...

  Download retained deployed App source artifacts.

Options:
  --json  Emit JSON instead of human-readable output.
  --help  Show this message and exit.

Commands:
  export  Write the retained deployed source zip for an independent App.
```

#### `apps source export`

```
Usage: apps source export [OPTIONS] REF DESTINATION

  Write the retained deployed source zip for an independent App.

Options:
  --help  Show this message and exit.
```

### `apps update`

```
Usage: apps update [OPTIONS] REF

  Update application metadata (patch-without-draft).

  ``REF`` is a slug, UUID, or application name. Unset flags are omitted from
  the payload so the server only applies the fields the user explicitly
  passed. Per the audit this is PATCH directly on the live application —
  there's no draft-staging step.

  When ``--deps`` is passed this runs the same two-call orchestration as
  ``apps create --deps``: the metadata PATCH first, then a ``PUT
  /dependencies`` applies the parsed dict. If the deps call fails after the
  patch succeeded, the command prints both outcomes, exits non-zero, and
  leaves the metadata change in place — there is no rollback.

Options:
  --name TEXT          name
  --slug TEXT          slug
  --description TEXT   description
  --scope TEXT         scope
  --access-level TEXT  access_level
  --role-ids TEXT      role_ids (repeat for multiple; comma-split also
                       accepted).
  --deps TEXT          Dependencies as a JSON literal or @path to a
                       package.json / {name: version} file. Triggers a follow-
                       up PUT to /dependencies after the metadata patch.
                       Mirrors `apps create --deps`.
  --json               Emit JSON instead of human-readable output.
  --help               Show this message and exit.
```

## `audit`

```
Usage: audit [OPTIONS] COMMAND [ARGS]...

  Read the audit log and explain access decisions.

Options:
  --json  Emit JSON instead of human-readable output.
  --help  Show this message and exit.

Commands:
  explain  Explain a stored access check: how it was decided then, and...
  list     List audit log entries, group them, or aggregate access checks...
```

### `audit explain`

```
Usage: audit explain [OPTIONS] EVENT_ID

  Explain a stored access check: how it was decided then, and how it would be
  now.

Options:
  --json  Emit JSON instead of human-readable output.
  --help  Show this message and exit.
```

### `audit list`

```
Usage: audit list [OPTIONS]

  List audit log entries, group them, or aggregate access checks by time.

Options:
  --action TEXT                   Action prefix, e.g. 'user.' or
                                  'access.check'.
  --outcome [success|failure]     Only successes or failures.
  --resource-type TEXT            Only events on this resource type.
  --user TEXT                     Acting user: UUID, email, or identity name.
  --execution TEXT                Workflow execution ID.
  --workflow TEXT                 Only events naming this workflow: UUID,
                                  name, or path::function.
  --org TEXT                      Only events in this organization: UUID or
                                  name, or 'global'.
  --since TEXT                    Start of the time range (ISO 8601,
                                  inclusive).
  --until TEXT                    End of the time range (ISO 8601, inclusive).
  --search TEXT                   Free-text search on actor, organization,
                                  action, resource type, IP, and details.
  --group-by [workflow|action|resource_type|outcome|user|organization]
                                  Count matching events per value instead of
                                  listing them.
  --aggregate [1h|6h|24h]         Group exact access checks into fixed UTC
                                  windows.
  --limit INTEGER RANGE           Maximum entries to return (server default
                                  50).  [1<=x<=500]
  --json                          Emit JSON instead of human-readable output.
  --help                          Show this message and exit.
```

## `claims`

```
Usage: claims [OPTIONS] COMMAND [ARGS]...

  Manage custom claims.

Options:
  --json  Emit JSON instead of human-readable output.
  --help  Show this message and exit.

Commands:
  create  Create a custom claim.
  delete  Delete a custom claim by name.
  get     Get a custom claim by name.
  list    List custom claims (superusers see all orgs by default).
  update  Update a custom claim by name.
```

### `claims create`

```
Usage: claims create [OPTIONS]

  Create a custom claim.

Options:
  --name TEXT                     name  [required]
  --description TEXT              description
  --type [list|scalar]            type
  --query TEXT                    query as JSON literal or @path to a
                                  YAML/JSON file.  [required]
  --global                        Target global scope (org=NULL). Alias for
                                  --org global.
  --org, --organization, --scope TEXT
                                  Org UUID/name, or 'none'/'global' for global
                                  scope. Omit = your org. (--organization /
                                  --scope are synonyms.)
  --json                          Emit JSON instead of human-readable output.
  --help                          Show this message and exit.
```

### `claims delete`

```
Usage: claims delete [OPTIONS] NAME

  Delete a custom claim by name.

Options:
  --global                        Target global scope (org=NULL). Alias for
                                  --org global.
  --org, --organization, --scope TEXT
                                  Org UUID/name, or 'none'/'global' for global
                                  scope. Omit = your org. (--organization /
                                  --scope are synonyms.)
  --json                          Emit JSON instead of human-readable output.
  --help                          Show this message and exit.
```

### `claims get`

```
Usage: claims get [OPTIONS] NAME

  Get a custom claim by name.

Options:
  --global                        Target global scope (org=NULL). Alias for
                                  --org global.
  --org, --organization, --scope TEXT
                                  Org UUID/name, or 'none'/'global' for global
                                  scope. Omit = your org. (--organization /
                                  --scope are synonyms.)
  --json                          Emit JSON instead of human-readable output.
  --help                          Show this message and exit.
```

### `claims list`

```
Usage: claims list [OPTIONS]

  List custom claims (superusers see all orgs by default).

Options:
  --global                        Target global scope (org=NULL). Alias for
                                  --org global.
  --org, --organization, --scope TEXT
                                  Org UUID/name, or 'none'/'global' for global
                                  scope. Omit = your org. (--organization /
                                  --scope are synonyms.)
  --json                          Emit JSON instead of human-readable output.
  --help                          Show this message and exit.
```

### `claims update`

```
Usage: claims update [OPTIONS] NAME

  Update a custom claim by name.

Options:
  --description TEXT              description
  --type [list|scalar]            type
  --query TEXT                    query as JSON literal or @path to a
                                  YAML/JSON file.
  --global                        Target global scope (org=NULL). Alias for
                                  --org global.
  --org, --organization, --scope TEXT
                                  Org UUID/name, or 'none'/'global' for global
                                  scope. Omit = your org. (--organization /
                                  --scope are synonyms.)
  --json                          Emit JSON instead of human-readable output.
  --help                          Show this message and exit.
```

## `configs`

```
Usage: configs [OPTIONS] COMMAND [ARGS]...

  Manage configuration values.

Options:
  --json  Emit JSON instead of human-readable output.
  --help  Show this message and exit.

Commands:
  create  Create a new configuration value.
  delete  Delete a configuration value by UUID or key.
  get     Get a single configuration value by UUID or key.
  list    List all configuration values.
  set     Upsert a configuration value (catalog open question #2: yes).
  update  Update a configuration value.
```

### `configs create`

```
Usage: configs create [OPTIONS]

  Create a new configuration value.

Options:
  --key TEXT                      key  [required]
  --value TEXT                    value as JSON literal or @path to a
                                  YAML/JSON file.  [required]
  --config-type [string|int|bool|json|secret]
                                  config_type
  --description TEXT              description
  --global                        Target global scope (org=NULL). Alias for
                                  --org global.
  --org, --organization, --scope TEXT
                                  Org UUID/name, or 'none'/'global' for global
                                  scope. Omit = your org. (--organization /
                                  --scope are synonyms.)
  --json                          Emit JSON instead of human-readable output.
  --help                          Show this message and exit.
```

### `configs delete`

```
Usage: configs delete [OPTIONS] REF

  Delete a configuration value by UUID or key.

  Secret-type configs require ``--confirm`` so a typo'd ``bifrost configs
  delete`` doesn't silently wipe an encrypted value that cannot be recovered
  from the server.

Options:
  --confirm  Required when deleting a secret-type config (safety guard).
  --json     Emit JSON instead of human-readable output.
  --help     Show this message and exit.
```

### `configs get`

```
Usage: configs get [OPTIONS] REF

  Get a single configuration value by UUID or key.

  Resolves the ref via :class:`RefResolver`, then reads ``GET
  /api/config/{uuid}`` directly.

Options:
  --json  Emit JSON instead of human-readable output.
  --help  Show this message and exit.
```

### `configs list`

```
Usage: configs list [OPTIONS]

  List all configuration values.

Options:
  --json  Emit JSON instead of human-readable output.
  --help  Show this message and exit.
```

### `configs set`

```
Usage: configs set [OPTIONS] KEY

  Upsert a configuration value (catalog open question #2: yes).

  Looks up an existing config matching ``(key, organization_id)`` by listing
  ``/api/config`` client-side — the endpoint does not accept a ``key`` query
  parameter, so filtering happens in the CLI. PUTs the existing row if found;
  POSTs otherwise. The result is idempotent from the caller's perspective.

  Org targeting follows the unified ``--org`` standard: HOME (omit) targets
  the caller's org, ``--global`` targets global, ``--org <id|name>`` targets
  that org. The scope filter only narrows the upsert to an explicit scope when
  one was given (GLOBAL or ORG); HOME falls back to key-only matching.

Options:
  --value TEXT                    Config value (plain string).  [required]
  --global                        Target global scope (org=NULL). Alias for
                                  --org global.
  --org, --organization, --scope TEXT
                                  Org UUID/name, or 'none'/'global' for global
                                  scope. Omit = your org. (--organization /
                                  --scope are synonyms.)
  --type [string|int|bool|json|secret]
                                  Config type (enum). On create, defaults to
                                  'string'. On update, omit to preserve the
                                  existing type.
  --description TEXT              Optional description of this config entry.
  --json                          Emit JSON instead of human-readable output.
  --help                          Show this message and exit.
```

### `configs update`

```
Usage: configs update [OPTIONS] REF

  Update a configuration value.

  ``REF`` is a UUID or config key. Names are resolved via
  :class:`RefResolver`; ambiguous keys fail loudly with the candidate list.

  Omitting ``--value`` preserves the stored value (server-side omit-unset
  behaviour — particularly important for ``secret``-type configs, where the
  plaintext value is never returned and cannot be round-tripped).

Options:
  --value TEXT                    value as JSON literal or @path to a
                                  YAML/JSON file.
  --config-type [string|int|bool|json|secret]
                                  config_type
  --description TEXT              description
  --json                          Emit JSON instead of human-readable output.
  --help                          Show this message and exit.
```

## `events`

```
Usage: events [OPTIONS] COMMAND [ARGS]...

  Manage event sources and subscriptions.

Options:
  --json  Emit JSON instead of human-readable output.
  --help  Show this message and exit.

Commands:
  create-graph-source  Create a Microsoft Graph webhook source with...
  create-source        Create a new event source.
  delete-source        Delete an event source after its provider...
  get-source           Get a single event source by UUID or name.
  get-subscription     Get a single subscription by source ref +...
  list-sources         List all event sources (wrapped ``{items, total}``...
  list-subscriptions   List subscriptions for an event source.
  resubscribe-source   Replace an event source's external provider...
  rotate-secret        Generate a new signing secret for a webhook source.
  subscribe            Subscribe a workflow or agent to an event source.
  update-source        Update an event source.
  update-subscription  Update an event subscription.
```

### `events create-graph-source`

```
Usage: events create-graph-source [OPTIONS]

  Create a Microsoft Graph webhook source with first-class flags.

  ``--user-id`` is the Microsoft Graph object ID, not a Bifrost user ID. HOME
  scopes the source to the caller organization; use ``--org`` to target
  another organization. Microsoft Graph sources cannot be global.

Options:
  --name TEXT                     Event source name.  [required]
  --integration TEXT              Microsoft integration UUID or name.
                                  [required]
  --user-id TEXT                  Microsoft Graph user object ID.  [required]
  --resource [messages|events|mailFolders|contacts]
                                  User resource collection to monitor.
                                  [required]
  --change-type [created|updated|deleted]
                                  Graph change type. Repeat for multiple
                                  values.  [default: created]
  --global                        Target global scope (org=NULL). Alias for
                                  --org global.
  --org, --organization, --scope TEXT
                                  Org UUID/name, or 'none'/'global' for global
                                  scope. Omit = your org. (--organization /
                                  --scope are synonyms.)
  --json                          Emit JSON instead of human-readable output.
  --help                          Show this message and exit.
```

### `events create-source`

```
Usage: events create-source [OPTIONS]

  Create a new event source.

  Flat-to-nested flags: ``--cron`` / ``--timezone`` / ``--schedule-enabled``
  collapse into the schedule config; ``--adapter`` / ``--webhook-integration``
  / ``--webhook-config`` collapse into the webhook config. At least one of
  each group is required when ``--source-type`` is ``schedule`` or
  ``webhook``, respectively — the API validates the shape.

  Org targeting follows the unified ``--org`` standard: HOME (omit) scopes the
  source to the caller's org, ``--global`` makes it global, ``--org
  <id|name>`` scopes it to that org.

Options:
  --name TEXT                     name  [required]
  --source-type [webhook|schedule|topic]
                                  source_type  [required]
  --event-type TEXT               event_type
  --cron TEXT                     Cron expression, e.g. '*/5 * * * *'
                                  (collapses into schedule config).
  --timezone TEXT                 Schedule timezone, e.g. 'UTC' (collapses
                                  into schedule config).
  --schedule-enabled / --no-schedule-enabled
                                  Whether the schedule is enabled (collapses
                                  into schedule config).
  --adapter TEXT                  Webhook adapter name (collapses into webhook
                                  config).
  --webhook-integration TEXT      Integration ref (UUID or name) for OAuth-
                                  based adapters (collapses into webhook
                                  config).
  --webhook-config TEXT           Webhook adapter config as JSON literal or
                                  @path/to/file.yaml (collapses into webhook
                                  config).
  --global                        Target global scope (org=NULL). Alias for
                                  --org global.
  --org, --organization, --scope TEXT
                                  Org UUID/name, or 'none'/'global' for global
                                  scope. Omit = your org. (--organization /
                                  --scope are synonyms.)
  --json                          Emit JSON instead of human-readable output.
  --help                          Show this message and exit.
```

### `events delete-source`

```
Usage: events delete-source [OPTIONS] REF

  Delete an event source after its provider subscription is removed.

Options:
  --json  Emit JSON instead of human-readable output.
  --help  Show this message and exit.
```

### `events get-source`

```
Usage: events get-source [OPTIONS] REF

  Get a single event source by UUID or name.

Options:
  --json  Emit JSON instead of human-readable output.
  --help  Show this message and exit.
```

### `events get-subscription`

```
Usage: events get-subscription [OPTIONS] SOURCE_REF SUBSCRIPTION_ID

  Get a single subscription by source ref + subscription UUID.

Options:
  --json  Emit JSON instead of human-readable output.
  --help  Show this message and exit.
```

### `events list-sources`

```
Usage: events list-sources [OPTIONS]

  List all event sources (wrapped ``{items, total}`` payload).

Options:
  --json  Emit JSON instead of human-readable output.
  --help  Show this message and exit.
```

### `events list-subscriptions`

```
Usage: events list-subscriptions [OPTIONS] SOURCE_REF

  List subscriptions for an event source.

  ``SOURCE_REF`` is a UUID or event source name.

Options:
  --json  Emit JSON instead of human-readable output.
  --help  Show this message and exit.
```

### `events resubscribe-source`

```
Usage: events resubscribe-source [OPTIONS] REF

  Replace an event source's external provider subscription.

Options:
  --json  Emit JSON instead of human-readable output.
  --help  Show this message and exit.
```

### `events rotate-secret`

```
Usage: events rotate-secret [OPTIONS] REF

  Generate a new signing secret for a webhook source.

  The output's ``raw_secret`` is the only time the new secret is shown;
  configure it in the sending service before it is lost. Requests signed with
  the previous secret are rejected from now on.

Options:
  --json  Emit JSON instead of human-readable output.
  --help  Show this message and exit.
```

### `events subscribe`

```
Usage: events subscribe [OPTIONS] SOURCE_REF

  Subscribe a workflow or agent to an event source.

  ``SOURCE_REF`` is a UUID or event source name. Supply exactly one of
  ``--workflow`` or ``--agent`` (portable refs). ``target_type`` is inferred
  from which flag was used and overrides any ``--target-type`` the DTO
  generator may surface.

Options:
  --target-type TEXT        target_type
  --workflow TEXT           workflow ref (UUID or name) for workflow_id.
  --agent TEXT              agent ref (UUID or name) for agent_id.
  --event-type TEXT         event_type
  --filter-expression TEXT  filter_expression
  --input-mapping TEXT      input_mapping as JSON literal or @path to a
                            YAML/JSON file.
  --json                    Emit JSON instead of human-readable output.
  --help                    Show this message and exit.
```

### `events update-source`

```
Usage: events update-source [OPTIONS] REF

  Update an event source.

  ``REF`` is a UUID or event source name. Flat-to-nested flags behave the same
  as on ``create-source`` — if any flat schedule / webhook flag is supplied,
  the corresponding nested object is rebuilt and patched.

  Passing ``--org``/``--global`` re-scopes the source (HOME leaves the scope
  unchanged, since omitting org sends no ``organization_id``).

Options:
  --name TEXT                     name
  --is-active / --no-is-active    is_active (tri-state; omit to leave
                                  unchanged).
  --cron TEXT                     Cron expression, e.g. '*/5 * * * *'
                                  (collapses into schedule config).
  --timezone TEXT                 Schedule timezone, e.g. 'UTC' (collapses
                                  into schedule config).
  --schedule-enabled / --no-schedule-enabled
                                  Whether the schedule is enabled (collapses
                                  into schedule config).
  --adapter TEXT                  Webhook adapter name (collapses into webhook
                                  config).
  --webhook-integration TEXT      Integration ref (UUID or name) for OAuth-
                                  based adapters (collapses into webhook
                                  config).
  --webhook-config TEXT           Webhook adapter config as JSON literal or
                                  @path/to/file.yaml (collapses into webhook
                                  config).
  --global                        Target global scope (org=NULL). Alias for
                                  --org global.
  --org, --organization, --scope TEXT
                                  Org UUID/name, or 'none'/'global' for global
                                  scope. Omit = your org. (--organization /
                                  --scope are synonyms.)
  --json                          Emit JSON instead of human-readable output.
  --help                          Show this message and exit.
```

### `events update-subscription`

```
Usage: events update-subscription [OPTIONS] SOURCE_REF SUBSCRIPTION_ID

  Update an event subscription.

  ``SOURCE_REF`` is a UUID or event source name; ``SUBSCRIPTION_ID`` is the
  subscription's UUID. Only filter / delivery fields are mutable —
  ``--workflow`` / ``--agent`` / ``--target-type`` are surfaced only so we can
  refuse the attempt with a clear error. Delete and recreate if you need to
  change the target.

Options:
  --event-type TEXT               event_type
  --filter-expression TEXT        filter_expression
  --is-active / --no-is-active    is_active (tri-state; omit to leave
                                  unchanged).
  --input-mapping TEXT            input_mapping as JSON literal or @path to a
                                  YAML/JSON file.
  --workflow TEXT                 Rejected: changing the target workflow
                                  requires delete + recreate.
  --agent TEXT                    Rejected: changing the target agent requires
                                  delete + recreate.
  --target-type [workflow|agent]  Rejected: changing the target type requires
                                  delete + recreate.
  --json                          Emit JSON instead of human-readable output.
  --help                          Show this message and exit.
```

## `files`

```
Usage: files [OPTIONS] COMMAND [ARGS]...

  Read, write, list, search files and manage file policies.

  Without --solution, commands target the instance _repo source file scope
  (location "workspace" by default). With --solution <slug|id>,
  read/write/list target that Solution install's runtime file scope and
  default the location to "solutions". Solution source files are deployed from
  the local workspace with `bifrost solution deploy`; `bifrost files
  --solution ...` is for runtime/user file bytes after install, not for
  editing deploy-owned source.

  `bifrost files` is the direct authoring surface for instance _repo text
  source and managed runtime/user files. For an existing file, record its
  version with `files stat`, read it, then write with `--expected-version`.
  For a new path, use `--create-only`. A conflict never overwrites the remote
  file.

  Examples:
    bifrost files list workflows/              # instance _repo files
    bifrost files write notes.txt --content hi --create-only
    bifrost files stat workflows/contact.py --json
    bifrost files read apps/desk/pages/App.tsx # instance _repo file
    bifrost files list --solution desk         # Solution runtime files
    bifrost files read notes/today.txt --solution desk

Options:
  --json  Emit JSON instead of human-readable output.
  --help  Show this message and exit.

Commands:
  delete    Delete a workspace file, optionally guarded by its current...
  exists    Check if a file exists.
  list      List files in a directory (default: location root).
  move      Move one file within a location as a durable server-side job.
  policies  Manage file access policies.
  read      Read a workspace file and write its contents to stdout.
  search    Search workspace and Solution source like grep, one page at a...
  stat      Show existence, version, size, and last-edit metadata without...
  write     Write to a workspace file.
```

### `files delete`

```
Usage: files delete [OPTIONS] PATH

  Delete a workspace file, optionally guarded by its current version.

Options:
  --location TEXT          Storage location. Special: "workspace" (default),
                           "temp", "uploads". Custom names (e.g. "reports")
                           are accepted; "_repo", "_tmp", and "_apps" are
                           blocked.
  --expected-version TEXT  Delete only if the remote file still has this
                           version from `files stat`.
  --json                   Emit JSON instead of human-readable output.
  --help                   Show this message and exit.
```

### `files exists`

```
Usage: files exists [OPTIONS] PATH

  Check if a file exists. Exits 0 if yes, 1 if no (script-friendly).

Options:
  --location TEXT  Storage location. Special: "workspace" (default), "temp",
                   "uploads". Custom names (e.g. "reports") are accepted;
                   "_repo", "_tmp", and "_apps" are blocked.
  --json           Emit JSON instead of human-readable output.
  --help           Show this message and exit.
```

### `files list`

```
Usage: files list [OPTIONS] [DIRECTORY]

  List files in a directory (default: location root).

  Pass ``--solution`` to target a solution install's file scope.

Options:
  --location TEXT  Storage location. Special: "workspace" (default), "temp",
                   "uploads". Custom names (e.g. "reports") are accepted;
                   "_repo", "_tmp", and "_apps" are blocked.
  --solution TEXT  Solution install slug or UUID. When given, targets that
                   install's file scope (location defaults to "solutions").
                   Slug resolved via GET /api/solutions.
  --json           Emit JSON instead of human-readable output.
  --help           Show this message and exit.
```

### `files move`

```
Usage: files move [OPTIONS] SOURCE DESTINATION

  Move one file within a location as a durable server-side job.

  The file is copied server-side, its metadata follows it, and the original is
  deleted only after the copy is verified. Workspace files cannot be moved.
  Prints the final path.

Options:
  --location TEXT  Storage location. Special: "workspace" (default), "temp",
                   "uploads". Custom names (e.g. "reports") are accepted;
                   "_repo", "_tmp", and "_apps" are blocked.  [required]
  --solution TEXT  Solution install slug or UUID. When given, targets that
                   install's file scope (location defaults to "solutions").
                   Slug resolved via GET /api/solutions.
  --rename         If the destination exists, use the next free 'name (n).ext'
                   instead of failing.
  --timeout FLOAT  Seconds to follow the move job; the job keeps running after
                   the CLI stops waiting.  [default: 14400]
  --json           Emit JSON instead of human-readable output.
  --help           Show this message and exit.
```

### `files policies`

```
Usage: files policies [OPTIONS] COMMAND [ARGS]...

  Manage file access policies.

Options:
  --json  Emit JSON instead of human-readable output.
  --help  Show this message and exit.

Commands:
  delete  Delete the file policy for a path prefix.
  get     Get the file policy for a path prefix.
  list    List file policies for a location and optional org scope.
  set     Create or replace the file policy for a path prefix.
```

#### `files policies delete`

```
Usage: files policies delete [OPTIONS] PATH

  Delete the file policy for a path prefix.

Options:
  --location TEXT  Storage location. Special: "workspace" (default), "temp",
                   "uploads". Custom names (e.g. "reports") are accepted;
                   "_repo", "_tmp", and "_apps" are blocked.
  --scope TEXT     Organization UUID for org-scoped policies.
  --help           Show this message and exit.
```

#### `files policies get`

```
Usage: files policies get [OPTIONS] PATH

  Get the file policy for a path prefix.

Options:
  --location TEXT  Storage location. Special: "workspace" (default), "temp",
                   "uploads". Custom names (e.g. "reports") are accepted;
                   "_repo", "_tmp", and "_apps" are blocked.
  --scope TEXT     Organization UUID for org-scoped policies.
  --help           Show this message and exit.
```

#### `files policies list`

```
Usage: files policies list [OPTIONS]

  List file policies for a location and optional org scope.

Options:
  --location TEXT  Storage location. Special: "workspace" (default), "temp",
                   "uploads". Custom names (e.g. "reports") are accepted;
                   "_repo", "_tmp", and "_apps" are blocked.
  --scope TEXT     Organization UUID for org-scoped policies.
  --help           Show this message and exit.
```

#### `files policies set`

```
Usage: files policies set [OPTIONS] PATH

  Create or replace the file policy for a path prefix.

Options:
  --location TEXT  Storage location. Special: "workspace" (default), "temp",
                   "uploads". Custom names (e.g. "reports") are accepted;
                   "_repo", "_tmp", and "_apps" are blocked.
  --scope TEXT     Organization UUID for org-scoped policies.
  --file FILE      JSON/YAML policy document to store.  [required]
  --help           Show this message and exit.
```

### `files read`

```
Usage: files read [OPTIONS] PATH

  Read a workspace file and write its contents to stdout.

  Text files only. The SDK has `read_bytes` for binary; this CLI verb does
  not. Pass ``--solution`` to target a solution install's file scope.

Options:
  --location TEXT  Storage location. Special: "workspace" (default), "temp",
                   "uploads". Custom names (e.g. "reports") are accepted;
                   "_repo", "_tmp", and "_apps" are blocked.
  --solution TEXT  Solution install slug or UUID. When given, targets that
                   install's file scope (location defaults to "solutions").
                   Slug resolved via GET /api/solutions.
  --json           Emit JSON instead of human-readable output.
  --help           Show this message and exit.
```

### `files search`

```
Usage: files search [OPTIONS] QUERY

  Search workspace and Solution source like grep, one page at a time.

  Examples:
    bifrost files search get_client --include '*.py'
    bifrost files search 'def .*_sync' --regex --files
    bifrost files search halo --solution covi-psa

Options:
  --regex                         Treat query as a Python regex.
  --case-sensitive
  --include TEXT                  ripgrep-style glob over paths, e.g. '*.py',
                                  'workflows/**', '*.{ts,tsx}'.
  --source [all|workspace|solutions]
                                  Search workspace source, Solution source, or
                                  both.  [default: all]
  --solution TEXT                 Restrict to one Solution install's deployed
                                  source (slug or UUID). Unlike other files
                                  verbs, this targets Solution source, not
                                  runtime files.
  --files                         List matching files instead of lines.
  -C, --context INTEGER RANGE     [default: 1; 0<=x<=5]
  --limit INTEGER RANGE           Results per page.  [default: 25; 1<=x<=200]
  --cursor TEXT                   next_cursor from the previous page (printed
                                  under 'More results').
  --json                          Emit JSON instead of human-readable output.
  --help                          Show this message and exit.
```

### `files stat`

```
Usage: files stat [OPTIONS] PATH

  Show existence, version, size, and last-edit metadata without content.

Options:
  --location TEXT  Storage location. Special: "workspace" (default), "temp",
                   "uploads". Custom names (e.g. "reports") are accepted;
                   "_repo", "_tmp", and "_apps" are blocked.
  --solution TEXT  Solution install slug or UUID. When given, targets that
                   install's file scope (location defaults to "solutions").
                   Slug resolved via GET /api/solutions.
  --json           Emit JSON instead of human-readable output.
  --help           Show this message and exit.
```

### `files write`

```
Usage: files write [OPTIONS] PATH [SOURCE]

  Write to a workspace file. Source: --content, --from-file, or `-` for stdin.

  Text files only. Pass --content "" to truncate an existing file. Use
  --create-only for a new path or --expected-version for a guarded
  replacement. Pass ``--solution`` to target a solution install's file scope.

Options:
  --content TEXT           Inline content to write.
  --from-file FILE         Read content from a local file.
  --location TEXT          Storage location. Special: "workspace" (default),
                           "temp", "uploads". Custom names (e.g. "reports")
                           are accepted; "_repo", "_tmp", and "_apps" are
                           blocked.
  --solution TEXT          Solution install slug or UUID. When given, targets
                           that install's file scope (location defaults to
                           "solutions"). Slug resolved via GET /api/solutions.
  --expected-version TEXT  Write only if the remote file still has this
                           version from `files stat`.
  --create-only            Create a new file; fail if the path already exists.
  --json                   Emit JSON instead of human-readable output.
  --help                   Show this message and exit.
```

## `forms`

```
Usage: forms [OPTIONS] COMMAND [ARGS]...

  Manage forms.

Options:
  --json  Emit JSON instead of human-readable output.
  --help  Show this message and exit.

Commands:
  create  Create a new form.
  delete  Delete (soft-delete) a form.
  get     Get a single form by UUID or name.
  list    List all forms.
  update  Update a form.
```

### `forms create`

```
Usage: forms create [OPTIONS]

  Create a new form.

  ``--workflow`` / ``--launch-workflow`` accept a UUID, name, or
  ``path::func`` ref. ``--form-schema`` accepts a JSON literal or
  ``@path/to/schema.yaml`` — the file is loaded and embedded as a dict.

  Org targeting follows the unified ``--org`` standard: HOME (omit) scopes the
  form to the caller's org, ``--global`` makes it global, ``--org <id|name>``
  scopes it to that org.

Options:
  --name TEXT                     name  [required]
  --description TEXT              description
  --confirmation-markdown TEXT    confirmation_markdown
  --workflow TEXT                 workflow ref (UUID or name) for workflow_id.
  --launch-workflow TEXT          workflow ref (UUID or name) for
                                  launch_workflow_id.
  --default-launch-params TEXT    default_launch_params as JSON literal or
                                  @path to a YAML/JSON file.
  --allowed-query-params TEXT     allowed_query_params (repeat for multiple).
  --form-schema TEXT              form_schema as JSON literal or @path to a
                                  YAML/JSON file.  [required]
  --access-level [authenticated|everyone|role_based]
                                  access_level
  --role-ids TEXT                 role_ids (repeat for multiple; comma-split
                                  also accepted).
  --global                        Target global scope (org=NULL). Alias for
                                  --org global.
  --org, --organization, --scope TEXT
                                  Org UUID/name, or 'none'/'global' for global
                                  scope. Omit = your org. (--organization /
                                  --scope are synonyms.)
  --json                          Emit JSON instead of human-readable output.
  --help                          Show this message and exit.
```

### `forms delete`

```
Usage: forms delete [OPTIONS] REF

  Delete (soft-delete) a form.

  ``REF`` is a UUID or form name. Matches the API default (is_active=False);
  use the REST endpoint directly with ``?purge=true`` to hard-delete.

Options:
  --json  Emit JSON instead of human-readable output.
  --help  Show this message and exit.
```

### `forms get`

```
Usage: forms get [OPTIONS] REF

  Get a single form by UUID or name.

Options:
  --json  Emit JSON instead of human-readable output.
  --help  Show this message and exit.
```

### `forms list`

```
Usage: forms list [OPTIONS]

  List all forms.

Options:
  --json  Emit JSON instead of human-readable output.
  --help  Show this message and exit.
```

### `forms update`

```
Usage: forms update [OPTIONS] REF

  Update a form.

  ``REF`` is a UUID or form name. Names are resolved via :class:`RefResolver`;
  ambiguous names fail loudly with the candidate list. Unset flags are omitted
  from the payload so only the supplied fields are patched.

  Passing ``--org``/``--global`` re-scopes the form (HOME leaves the scope
  unchanged, since omitting org sends no ``organization_id``).

Options:
  --name TEXT                     name
  --description TEXT              description
  --confirmation-markdown TEXT    confirmation_markdown
  --workflow TEXT                 workflow ref (UUID or name) for workflow_id.
  --launch-workflow TEXT          workflow ref (UUID or name) for
                                  launch_workflow_id.
  --default-launch-params TEXT    default_launch_params as JSON literal or
                                  @path to a YAML/JSON file.
  --allowed-query-params TEXT     allowed_query_params (repeat for multiple).
  --form-schema TEXT              form_schema as JSON literal or @path to a
                                  YAML/JSON file.
  --is-active / --no-is-active    is_active (tri-state; omit to leave
                                  unchanged).
  --access-level [authenticated|everyone|role_based]
                                  access_level
  --clear-roles / --no-clear-roles
                                  clear_roles (tri-state; omit to leave
                                  unchanged).
  --role-ids TEXT                 role_ids (repeat for multiple; comma-split
                                  also accepted).
  --global                        Target global scope (org=NULL). Alias for
                                  --org global.
  --org, --organization, --scope TEXT
                                  Org UUID/name, or 'none'/'global' for global
                                  scope. Omit = your org. (--organization /
                                  --scope are synonyms.)
  --json                          Emit JSON instead of human-readable output.
  --help                          Show this message and exit.
```

## `integrations`

```
Usage: integrations [OPTIONS] COMMAND [ARGS]...

  Manage integrations.

Options:
  --json  Emit JSON instead of human-readable output.
  --help  Show this message and exit.

Commands:
  add-mapping     Create a mapping between an integration and an...
  create          Create a new integration.
  get             Get a single integration by UUID or name (with mappings...
  list            List all integrations (wrapped ``{items, total}``...
  update          Update an integration.
  update-mapping  Update an existing integration mapping.
```

### `integrations add-mapping`

```
Usage: integrations add-mapping [OPTIONS] INTEGRATION_REF

  Create a mapping between an integration and an organization.

  ``INTEGRATION_REF`` is a UUID or integration name. ``--organization`` is a
  UUID or org name (resolved via :class:`RefResolver`).

  ``--oauth-token-id`` is an opt-in flag outside the DTO-generated flag set —
  the DTO excludes ``oauth_token_id`` to avoid accidentally surfacing the UI-
  managed OAuth handshake data as a writable CLI field.

Options:
  --organization TEXT    org ref (UUID or name) for organization_id.
                         [required]
  --entity-id TEXT       entity_id  [required]
  --entity-name TEXT     entity_name
  --config TEXT          config as JSON literal or @path to a YAML/JSON file.
  --oauth-token-id TEXT  OAuth token UUID (opt-in; empty means leave unset).
  --json                 Emit JSON instead of human-readable output.
  --help                 Show this message and exit.
```

### `integrations create`

```
Usage: integrations create [OPTIONS]

  Create a new integration.

  ``--config-schema`` accepts a JSON literal or ``@path/to/schema.yaml``. The
  file's top level may be a list of schema items or a dict with a ``schema`` /
  ``config_schema`` / ``items`` list.

Options:
  --name TEXT               name  [required]
  --description TEXT        description
  --config-schema TEXT      config_schema (repeat for multiple).
  --entity-id TEXT          entity_id
  --entity-id-name TEXT     entity_id_name
  --default-entity-id TEXT  default_entity_id
  --json                    Emit JSON instead of human-readable output.
  --help                    Show this message and exit.
```

### `integrations get`

```
Usage: integrations get [OPTIONS] REF

  Get a single integration by UUID or name (with mappings + OAuth config).

Options:
  --json  Emit JSON instead of human-readable output.
  --help  Show this message and exit.
```

### `integrations list`

```
Usage: integrations list [OPTIONS]

  List all integrations (wrapped ``{items, total}`` payload).

Options:
  --json  Emit JSON instead of human-readable output.
  --help  Show this message and exit.
```

### `integrations update`

```
Usage: integrations update [OPTIONS] REF

  Update an integration.

  ``REF`` is a UUID or integration name. When ``--config-schema`` drops keys
  that have saved ``Config`` values, the server refuses with 409 unless
  ``--force-remove-keys`` is passed — removed keys cascade-delete related
  ``Config`` rows (integration-level defaults and per-org overrides).

Options:
  --force-remove-keys             Proceed even when the new --config-schema
                                  drops keys currently present on the
                                  integration (cascade-deletes related
                                  configs).
  --name TEXT                     name
  --description TEXT              description
  --list-entities-data-provider TEXT
                                  workflow ref (UUID or name) for
                                  list_entities_data_provider_id.
  --config-schema TEXT            config_schema (repeat for multiple).
  --entity-id TEXT                entity_id
  --entity-id-name TEXT           entity_id_name
  --default-entity-id TEXT        default_entity_id
  --json                          Emit JSON instead of human-readable output.
  --help                          Show this message and exit.
```

### `integrations update-mapping`

```
Usage: integrations update-mapping [OPTIONS] INTEGRATION_REF

  Update an existing integration mapping.

  Resolves ``INTEGRATION_REF`` + ``--organization`` to the mapping UUID via
  ``GET /api/integrations/{id}/mappings/by-org/{org_id}``, then PUTs the
  update body. ``oauth_token_id`` is only sent when ``--oauth-token-id`` is
  explicitly passed — this preserves the server's existing token on unrelated
  updates (it's set by the OAuth flow, not by CLI users).

Options:
  --organization TEXT    organization ref (UUID or name) — identifies the
                         mapping to update.  [required]
  --entity-id TEXT       entity_id
  --entity-name TEXT     entity_name
  --config TEXT          config as JSON literal or @path to a YAML/JSON file.
  --oauth-token-id TEXT  OAuth token UUID (opt-in; omitted means leave
                         unchanged).
  --json                 Emit JSON instead of human-readable output.
  --help                 Show this message and exit.
```

## `orgs`

```
Usage: orgs [OPTIONS] COMMAND [ARGS]...

  Manage organizations.

Options:
  --json  Emit JSON instead of human-readable output.
  --help  Show this message and exit.

Commands:
  create  Create a new organization.
  delete  Delete (soft-delete) an organization.
  get     Get a single organization by UUID or name.
  list    List all organizations.
  update  Update an organization.
```

### `orgs create`

```
Usage: orgs create [OPTIONS]

  Create a new organization.

Options:
  --name TEXT                   name  [required]
  --is-active / --no-is-active  is_active (tri-state; omit to leave
                                unchanged).
  --json                        Emit JSON instead of human-readable output.
  --help                        Show this message and exit.
```

### `orgs delete`

```
Usage: orgs delete [OPTIONS] REF

  Delete (soft-delete) an organization.

  ``REF`` is a UUID or organization name.

Options:
  --json  Emit JSON instead of human-readable output.
  --help  Show this message and exit.
```

### `orgs get`

```
Usage: orgs get [OPTIONS] REF

  Get a single organization by UUID or name.

Options:
  --json  Emit JSON instead of human-readable output.
  --help  Show this message and exit.
```

### `orgs list`

```
Usage: orgs list [OPTIONS]

  List all organizations.

Options:
  --json  Emit JSON instead of human-readable output.
  --help  Show this message and exit.
```

### `orgs update`

```
Usage: orgs update [OPTIONS] REF

  Update an organization.

  ``REF`` is a UUID or organization name. Names are resolved via
  :class:`RefResolver`; ambiguous names fail loudly with the candidate list.

Options:
  --name TEXT                   name
  --is-active / --no-is-active  is_active (tri-state; omit to leave
                                unchanged).
  --json                        Emit JSON instead of human-readable output.
  --help                        Show this message and exit.
```

## `permissions`

```
Usage: permissions [OPTIONS] COMMAND [ARGS]...

  Inspect the permission catalog.

Options:
  --json  Emit JSON instead of human-readable output.
  --help  Show this message and exit.

Commands:
  list  List checked permissions by area, with name, scope and enforcement.
```

### `permissions list`

```
Usage: permissions list [OPTIONS]

  List checked permissions by area, with name, scope and enforcement.

Options:
  --json  Emit JSON instead of human-readable output.
  --help  Show this message and exit.
```

## `policy-rule`

```
Usage: policy-rule [OPTIONS] COMMAND [ARGS]...

  Manage named, reusable policy rules.

Options:
  --json  Emit JSON instead of human-readable output.
  --help  Show this message and exit.

Commands:
  create  Create a named policy rule.
  delete  Delete a named policy rule.
  get     Get a single policy rule by domain and name.
  list    List named policy rules.
  update  Update a named policy rule.
  usages  Show all file-policies and tables that reference a rule.
```

### `policy-rule create`

```
Usage: policy-rule create [OPTIONS]

  Create a named policy rule.

  ``--body`` accepts a JSON literal or ``@path/to/file.yaml``.

  Example:

  \b     bifrost policy-rule create --name read_all --domain file \
  --body '{"actions": ["read"], "when": null}'

  Org targeting follows the unified ``--org`` standard.

Options:
  --name TEXT                     name  [required]
  --domain [file|table]           domain  [required]
  --description TEXT              description
  --body TEXT                     body as JSON literal or @path to a YAML/JSON
                                  file.  [required]
  --global                        Target global scope (org=NULL). Alias for
                                  --org global.
  --org, --organization, --scope TEXT
                                  Org UUID/name, or 'none'/'global' for global
                                  scope. Omit = your org. (--organization /
                                  --scope are synonyms.)
  --json                          Emit JSON instead of human-readable output.
  --help                          Show this message and exit.
```

### `policy-rule delete`

```
Usage: policy-rule delete [OPTIONS] {file|table} NAME

  Delete a named policy rule.

  ``DOMAIN`` is 'file' or 'table'. ``NAME`` is the rule's name. Fails with 409
  if the rule is read-only (built-in) or in use.

Options:
  --scope TEXT  Organization UUID for org-scoped rules.
  --json        Emit JSON instead of human-readable output.
  --help        Show this message and exit.
```

### `policy-rule get`

```
Usage: policy-rule get [OPTIONS] {file|table} NAME

  Get a single policy rule by domain and name.

  Reads ``GET /api/policy-rules/{domain}/{name}`` directly. Solution-managed
  rules are readable (writes stay blocked).

Options:
  --scope TEXT  Organization UUID for org-scoped rules.
  --json        Emit JSON instead of human-readable output.
  --help        Show this message and exit.
```

### `policy-rule list`

```
Usage: policy-rule list [OPTIONS]

  List named policy rules.

Options:
  --domain [file|table]  Filter by domain ('file' or 'table').
  --scope TEXT           Organization UUID to filter by scope.
  --json                 Emit JSON instead of human-readable output.
  --help                 Show this message and exit.
```

### `policy-rule update`

```
Usage: policy-rule update [OPTIONS] {file|table} NAME

  Update a named policy rule.

  ``DOMAIN`` is 'file' or 'table'. ``NAME`` is the rule's name. Unset flags
  are omitted; the server preserves existing values.

Options:
  --name TEXT         name
  --description TEXT  description
  --body TEXT         body as JSON literal or @path to a YAML/JSON file.
  --scope TEXT        Organization UUID for org-scoped rules.
  --json              Emit JSON instead of human-readable output.
  --help              Show this message and exit.
```

### `policy-rule usages`

```
Usage: policy-rule usages [OPTIONS] {file|table} NAME

  Show all file-policies and tables that reference a rule.

Options:
  --scope TEXT  Organization UUID for org-scoped rules.
  --json        Emit JSON instead of human-readable output.
  --help        Show this message and exit.
```

## `requirements`

```
Usage: requirements [OPTIONS] COMMAND [ARGS]...

  Manage the workspace's Python requirements.txt (workers auto-recycle).

Options:
  --json  Emit JSON instead of human-readable output.
  --help  Show this message and exit.

Commands:
  install  Install a package or recycle workers from current...
  list     List installed Python packages on the platform.
  remove   Remove a package from requirements.txt and recycle workers.
```

### `requirements install`

```
Usage: requirements install [OPTIONS] [SPEC]

  Install a package or recycle workers from current requirements.txt.

  Examples:

    bifrost requirements install                  # warm cache + recycle
    workers   bifrost requirements install reportlab        # append, then
    recycle   bifrost requirements install httpx==0.27.0    # pin version,
    then recycle

Options:
  --json  Emit JSON instead of human-readable output.
  --help  Show this message and exit.
```

### `requirements list`

```
Usage: requirements list [OPTIONS]

  List installed Python packages on the platform.

Options:
  --json  Emit JSON instead of human-readable output.
  --help  Show this message and exit.
```

### `requirements remove`

```
Usage: requirements remove [OPTIONS] PACKAGE_NAME

  Remove a package from requirements.txt and recycle workers.

Options:
  --json  Emit JSON instead of human-readable output.
  --help  Show this message and exit.
```

## `retention`

```
Usage: retention [OPTIONS] COMMAND [ARGS]...

  Show and change how long runs, events, and audit events are kept.

Options:
  --json  Emit JSON instead of human-readable output.
  --help  Show this message and exit.

Commands:
  preview  Show what a retention run would do now, without changing...
  run      Run retention now: delete expired runs and events, or archive...
  set      Change a retention window.
  show     Show the retention windows, what the oldest data is, and the...
```

### `retention preview`

```
Usage: retention preview [OPTIONS] {runs|audit}

  Show what a retention run would do now, without changing anything.

Options:
  --json  Emit JSON instead of human-readable output.
  --help  Show this message and exit.
```

### `retention run`

```
Usage: retention run [OPTIONS] {runs|audit}

  Run retention now: delete expired runs and events, or archive aged audit
  events.

Options:
  --json  Emit JSON instead of human-readable output.
  --help  Show this message and exit.
```

### `retention set`

```
Usage: retention set [OPTIONS] COMMAND [ARGS]...

  Change a retention window.

Options:
  --json  Emit JSON instead of human-readable output.
  --help  Show this message and exit.

Commands:
  audit  Set the audit database window, the archive window, or both.
  runs   Set how long finished runs and their events are kept.
```

#### `retention set audit`

```
Usage: retention set audit [OPTIONS]

  Set the audit database window, the archive window, or both.

  A window you leave out keeps its current value.

  Examples:
    bifrost retention set audit --database 60
    bifrost retention set audit --archive forever

Options:
  --database INTEGER      Days audit events stay in the database before they
                          are archived.
  --archive DAYS|FOREVER  Days archived audit events are kept before deletion,
                          or 'forever'.
  --json                  Emit JSON instead of human-readable output.
  --help                  Show this message and exit.
```

#### `retention set runs`

```
Usage: retention set runs [OPTIONS]

  Set how long finished runs and their events are kept.

  Examples:
    bifrost retention set runs --days 60
    bifrost retention set runs --forever

Options:
  --days INTEGER  Keep finished runs and events this many days (30 to 3650).
  --forever       Keep finished runs and events forever.
  --json          Emit JSON instead of human-readable output.
  --help          Show this message and exit.
```

### `retention show`

```
Usage: retention show [OPTIONS]

  Show the retention windows, what the oldest data is, and the last run of
  each.

Options:
  --json  Emit JSON instead of human-readable output.
  --help  Show this message and exit.
```

## `roles`

```
Usage: roles [OPTIONS] COMMAND [ARGS]...

  Manage roles.

Options:
  --json  Emit JSON instead of human-readable output.
  --help  Show this message and exit.

Commands:
  create  Create a new role.
  delete  Delete a role.
  get     Get a single role by UUID or name.
  list    List all roles.
  update  Update a role.
```

### `roles create`

```
Usage: roles create [OPTIONS]

  Create a new role.

Options:
  --name TEXT         name  [required]
  --description TEXT  description
  --json              Emit JSON instead of human-readable output.
  --help              Show this message and exit.
```

### `roles delete`

```
Usage: roles delete [OPTIONS] REF

  Delete a role.

  ``REF`` is a UUID or role name. CASCADE removes all role assignments.

Options:
  --json  Emit JSON instead of human-readable output.
  --help  Show this message and exit.
```

### `roles get`

```
Usage: roles get [OPTIONS] REF

  Get a single role by UUID or name.

Options:
  --json  Emit JSON instead of human-readable output.
  --help  Show this message and exit.
```

### `roles list`

```
Usage: roles list [OPTIONS]

  List all roles.

Options:
  --json  Emit JSON instead of human-readable output.
  --help  Show this message and exit.
```

### `roles update`

```
Usage: roles update [OPTIONS] REF

  Update a role.

  ``REF`` is a UUID or role name. Names are resolved via :class:`RefResolver`;
  ambiguous names fail loudly with the candidate list.

Options:
  --name TEXT         name
  --description TEXT  description
  --json              Emit JSON instead of human-readable output.
  --help              Show this message and exit.
```

## `services`

```
Usage: services [OPTIONS] COMMAND [ARGS]...

  Manage supervised services.

Options:
  --json  Emit JSON instead of human-readable output.
  --help  Show this message and exit.

Commands:
  attempts  List attempt history newest-first for a service.
  disable   Disable a service: stops the live attempt, blocks future claims.
  enable    Enable a service (distinct from start: no desired-state change).
  get       Get a single service by definition UUID or workflow name.
  list      List service definitions (wrapped ``{items, total}`` payload).
  logs      List trailing persisted logs for a service.
  restart   Rolling restart: stays desired-running, stops the live...
  start     Request running: clears suppression so the claim loop picks...
  stop      Request stopped: durable desire is stored before termination.
  update    Update a service's lifecycle policy.
```

### `services attempts`

```
Usage: services attempts [OPTIONS] REF

  List attempt history newest-first for a service.

  ``REF`` is a definition UUID or workflow name.

Options:
  --limit INTEGER   Max results (server default 100, max 1000).
  --offset INTEGER  Skip results.
  --json            Emit JSON instead of human-readable output.
  --help            Show this message and exit.
```

### `services disable`

```
Usage: services disable [OPTIONS] REF

  Disable a service: stops the live attempt, blocks future claims.

Options:
  --json  Emit JSON instead of human-readable output.
  --help  Show this message and exit.
```

### `services enable`

```
Usage: services enable [OPTIONS] REF

  Enable a service (distinct from start: no desired-state change).

Options:
  --json  Emit JSON instead of human-readable output.
  --help  Show this message and exit.
```

### `services get`

```
Usage: services get [OPTIONS] REF

  Get a single service by definition UUID or workflow name.

Options:
  --json  Emit JSON instead of human-readable output.
  --help  Show this message and exit.
```

### `services list`

```
Usage: services list [OPTIONS]

  List service definitions (wrapped ``{items, total}`` payload).

Options:
  --limit INTEGER   Max results (server default 100, max 1000).
  --offset INTEGER  Skip results.
  --json            Emit JSON instead of human-readable output.
  --help            Show this message and exit.
```

### `services logs`

```
Usage: services logs [OPTIONS] REF

  List trailing persisted logs for a service.

  ``REF`` is a definition UUID or workflow name. Page through older lines by
  passing the previous response's ``continuation_token`` back via
  ``--continuation-token``.

Options:
  --attempt-id TEXT               Scope to one attempt UUID.
  --level TEXT                    Level allowlist, e.g. INFO. Repeat for
                                  multiple values.
  --start-date TEXT               ISO timestamp lower bound.
  --end-date TEXT                 ISO timestamp upper bound.
  --limit INTEGER                 Max lines per page (server default 200, max
                                  1000).
  --continuation-token TEXT       Keyset cursor from the previous page (load-
                                  older paging).
  --order [chronological|newest_first]
                                  Log order (server default chronological).
  --json                          Emit JSON instead of human-readable output.
  --help                          Show this message and exit.
```

### `services restart`

```
Usage: services restart [OPTIONS] REF

  Rolling restart: stays desired-running, stops the live attempt if any.

Options:
  --json  Emit JSON instead of human-readable output.
  --help  Show this message and exit.
```

### `services start`

```
Usage: services start [OPTIONS] REF

  Request running: clears suppression so the claim loop picks it up.

Options:
  --json  Emit JSON instead of human-readable output.
  --help  Show this message and exit.
```

### `services stop`

```
Usage: services stop [OPTIONS] REF

  Request stopped: durable desire is stored before termination.

Options:
  --json  Emit JSON instead of human-readable output.
  --help  Show this message and exit.
```

### `services update`

```
Usage: services update [OPTIONS] REF

  Update a service's lifecycle policy.

  ``REF`` is a definition UUID or workflow name. Unset flags are omitted from
  the payload so only the supplied fields are patched.

Options:
  --startup-policy [automatic|manual]
                                  startup_policy
  --restart-policy [always|on_failure|never]
                                  restart_policy
  --graceful-shutdown-seconds INTEGER
                                  graceful_shutdown_seconds
  --startup-grace-seconds INTEGER
                                  startup_grace_seconds
  --restart-backoff-initial-seconds INTEGER
                                  restart_backoff_initial_seconds
  --restart-backoff-max-seconds INTEGER
                                  restart_backoff_max_seconds
  --crash-loop-max-restarts INTEGER
                                  crash_loop_max_restarts
  --crash-loop-window-seconds INTEGER
                                  crash_loop_window_seconds
  --json                          Emit JSON instead of human-readable output.
  --help                          Show this message and exit.
```

## `solution`

```
Usage: solution [OPTIONS] COMMAND [ARGS]...

  Manage Solution installs (installable surfaces).

Options:
  --help  Show this message and exit.

Commands:
  bind              Bind this local Solution workspace to an existing...
  capture           Adopt loose _repo/ entities into an install (migration).
  create            Create a Solution workspace and remote install.
  deploy            Non-interactive full-replace deploy of the current...
  export            Download a Solution's workspace zip (shareable or...
  git               Connect or disconnect a managed Solution repository.
  import-workspace  Import a Solution package as unattached workspace...
  init              Alias for `solution create`: scaffold and create a...
  install           Install a Solution from a workspace zip...
  install-repo      Install a Solution from a repository and make Git its...
  migrate-app       Migrate a v1 inline App directory to a scaffolded V2...
  pull              Pull captured entities into the local .bifrost/...
  pull-manifests    Pull captured entities into the local .bifrost/...
  scaffold-app      Scaffold a standalone_v2 React app (package.json,...
  sdk               Manage the app's vendored Bifrost SDK.
  start             Run the app's dev server + local workflows on one...
  swap-slugs        Atomically exchange two apps' slugs (v1→v2 migration...
  sync              Update a Git-connected Solution from its configured ref.
  update            Edit install-local fields (name, scope, access gates)...
```

### `solution bind`

```
Usage: solution bind [OPTIONS] [PATH]

  Bind this local Solution workspace to an existing install.

Options:
  --solution TEXT  Install id or unique slug.  [required]
  --url TEXT       Bifrost instance URL (default: current profile).
  --help           Show this message and exit.
```

### `solution capture`

```
Usage: solution capture [OPTIONS] SOLUTION_ID

  Adopt loose _repo/ entities into an install (migration). --dry-run previews
  the dependency closure + outside references first.

Options:
  --workflow TEXT                 Workflow name or id (repeatable).
  --table TEXT                    Table name or id (repeatable).
  --app TEXT                      App name or id (repeatable).
  --form TEXT                     Form name or id (repeatable).
  --agent TEXT                    Agent name or id (repeatable).
  --claim TEXT                    Custom-claim name or id (repeatable).
  --config TEXT                   Config key (repeatable).
  --include-imports / --no-include-imports
                                  Also bundle the transitive modules/ import
                                  closure of captured workflows.  [default:
                                  no-include-imports]
  --dry-run                       Preview the dependency closure + outside
                                  references; capture nothing.
  --yes                           Skip the confirmation prompt (capture is
                                  terminal).
  --help                          Show this message and exit.
```

### `solution create`

```
Usage: solution create [OPTIONS] [PATH]

  Create a Solution workspace and remote install.

Options:
  --slug TEXT                     Solution slug (definition identity).
                                  [required]
  --name TEXT                     Display name (defaults to slug).
  --version TEXT                  Bundle version recorded on the install at
                                  deploy time.  [default: 0.1.0]
  --allow-outbound-access / --no-allow-outbound-access
                                  Let the install fall back to shared _repo
                                  resources.
  --allow-inbound-access / --no-allow-inbound-access
                                  Let other installs target this one via per-
                                  call solution refs.
  --url TEXT                      Bifrost instance URL (default: current
                                  profile).
  --global                        Target global scope (org=NULL). Alias for
                                  --org global.
  --org, --organization, --scope TEXT
                                  Org UUID/name, or 'none'/'global' for global
                                  scope. Omit = your org. (--organization /
                                  --scope are synonyms.)
  --help                          Show this message and exit.
```

### `solution deploy`

```
Usage: solution deploy [OPTIONS] [PATH]

  Non-interactive full-replace deploy of the current Solution workspace. If no
  install matches, --org or --global is required before one is created.

Options:
  --solution TEXT                 Install id or unique slug.
  --url TEXT                      Bifrost instance URL (default: current
                                  profile).
  --force                         Apply even if the bundle version is older
                                  than the installed version (downgrade).
  --global                        Target global scope (org=NULL). Alias for
                                  --org global.
  --org, --organization, --scope TEXT
                                  Org UUID/name, or 'none'/'global' for global
                                  scope. Omit = your org. (--organization /
                                  --scope are synonyms.)
  --help                          Show this message and exit.
```

### `solution export`

```
Usage: solution export [OPTIONS] SOLUTION_REF

  Download a Solution's workspace zip (shareable or full backup).

Options:
  --mode [shareable|full]  shareable (code+schema, no password) or full
                           (+secrets+data, password required).  [default:
                           shareable]
  --password TEXT          Required for --mode full; encrypts the secrets
                           blob.
  --include-data           Include table row data and solution files in the
                           encrypted tier. Requires --mode full.
  --out TEXT               Output zip path (default: <slug>-<version>.zip in
                           the current directory).
  --help                   Show this message and exit.
```

### `solution git`

```
Usage: solution git [OPTIONS] COMMAND [ARGS]...

  Connect or disconnect a managed Solution repository.

Options:
  --help  Show this message and exit.

Commands:
  connect     Connect an existing install; repository updates become its...
  disconnect  Disconnect Git so future updates are manual Solution...
  sources     List authorized private repository source IDs in a scope.
```

#### `solution git connect`

```
Usage: solution git connect [OPTIONS] SOLUTION_REF REPOSITORY_URL

  Connect an existing install; repository updates become its sole writer.

Options:
  --subpath TEXT        Solution workspace path inside the repository.
  --ref TEXT            Git ref to update from.  [default: main]
  --git-source-id TEXT  Authorized Solution GitHub App source UUID. Omit for a
                        public repository.
  --help                Show this message and exit.
```

#### `solution git disconnect`

```
Usage: solution git disconnect [OPTIONS] SOLUTION_REF

  Disconnect Git so future updates are manual Solution deployments.

Options:
  --help  Show this message and exit.
```

#### `solution git sources`

```
Usage: solution git sources [OPTIONS]

  List authorized private repository source IDs in a scope.

Options:
  --global                        Target global scope (org=NULL). Alias for
                                  --org global.
  --org, --organization, --scope TEXT
                                  Org UUID/name, or 'none'/'global' for global
                                  scope. Omit = your org. (--organization /
                                  --scope are synonyms.)
  --help                          Show this message and exit.
```

### `solution import-workspace`

```
Usage: solution import-workspace [OPTIONS] [ARCHIVE]

  Import a Solution package as unattached workspace content (one-time
  snapshot).

Options:
  --repo TEXT           Solution git repository URL (snapshot import; mutually
                        exclusive with ARCHIVE).
  --ref TEXT            Git ref to import (default branch when omitted).
  --path TEXT           Package subfolder within the repository.
  --org TEXT            Target organization name or UUID for scoped
                        definitions. Omit for global workspace content.
  --global              Target global workspace content (the default).
  --keep-all            Keep every conflicting destination item.
  --replace-all         Replace every conflicting destination item.
  --decisions FILE
  --preview             Print the staged collision preview without queuing an
                        import.
  --json                Emit raw preview and terminal job JSON.
  --git-source-id TEXT  Authorized Solution GitHub App source UUID; requires
                        --repo.
  --help                Show this message and exit.
```

### `solution init`

```
Usage: solution init [OPTIONS] [PATH]

  Alias for `solution create`: scaffold and create a remote install.

Options:
  --slug TEXT                     Solution slug (definition identity).
                                  [required]
  --name TEXT                     Display name (defaults to slug).
  --version TEXT                  Bundle version recorded on the install at
                                  deploy time.  [default: 0.1.0]
  --allow-outbound-access / --no-allow-outbound-access
                                  Let the install fall back to shared _repo
                                  resources.
  --allow-inbound-access / --no-allow-inbound-access
                                  Let other installs target this one via per-
                                  call solution refs.
  --url TEXT                      Bifrost instance URL (default: current
                                  profile).
  --global                        Target global scope (org=NULL). Alias for
                                  --org global.
  --org, --organization, --scope TEXT
                                  Org UUID/name, or 'none'/'global' for global
                                  scope. Omit = your org. (--organization /
                                  --scope are synonyms.)
  --help                          Show this message and exit.
```

### `solution install`

```
Usage: solution install [OPTIONS] ZIP_PATH

  Install a Solution from a workspace zip (drag-and-drop equivalent).

Options:
  --global                        Target global scope (org=NULL). Alias for
                                  --org global.
  --org, --organization, --scope TEXT
                                  Org UUID/name, or 'none'/'global' for global
                                  scope. Omit = your org. (--organization /
                                  --scope are synonyms.)
  --set TEXT                      Config value KEY=VALUE (repeatable). Applied
                                  atomically with the deploy.
  --password TEXT                 Decryption password for a full-backup zip
                                  (required when the zip carries secrets).
  --replace-secrets               Overwrite existing config values when the
                                  zip carries conflicting secret values.
  --replace-data                  Overwrite existing table data when the zip
                                  carries conflicting rows.
  --reactivate                    Reactivate an existing inactive
                                  (uninstalled) install of the same slug
                                  rather than refusing.
  --help                          Show this message and exit.
```

### `solution install-repo`

```
Usage: solution install-repo [OPTIONS] REPOSITORY_URL

  Install a Solution from a repository and make Git its sole writer.

Options:
  --subpath TEXT                  Solution workspace path inside the
                                  repository.
  --ref TEXT                      Git ref to install.  [default: main]
  --git-source-id TEXT            Authorized Solution GitHub App source UUID.
  --global                        Target global scope (org=NULL). Alias for
                                  --org global.
  --org, --organization, --scope TEXT
                                  Org UUID/name, or 'none'/'global' for global
                                  scope. Omit = your org. (--organization /
                                  --scope are synonyms.)
  --help                          Show this message and exit.
```

### `solution migrate-app`

```
Usage: solution migrate-app [OPTIONS] SOURCE V2_SLUG

  Migrate a v1 inline App directory to a scaffolded V2 App: scaffold + port
  source + rewrite imports + install shadcn. STOPS before build/wire and
  prints a checklist of the judgment steps left to you.

Options:
  --title TEXT  App display title (default: the v2 slug).
  --help        Show this message and exit.
```

### `solution pull`

```
Usage: solution pull [OPTIONS] [PATH]

  Pull captured entities into the local .bifrost/ manifest (does not touch
  source code).

Options:
  --solution TEXT                 Target install id (override when ambiguous).
  --global                        Target global scope (org=NULL). Alias for
                                  --org global.
  --org, --organization, --scope TEXT
                                  Org UUID/name, or 'none'/'global' for global
                                  scope. Omit = your org. (--organization /
                                  --scope are synonyms.)
  --help                          Show this message and exit.
```

### `solution pull-manifests`

```
Usage: solution pull-manifests [OPTIONS] [PATH]

  Pull captured entities into the local .bifrost/ manifest (does not touch
  source code).

Options:
  --solution TEXT                 Target install id (override when ambiguous).
  --global                        Target global scope (org=NULL). Alias for
                                  --org global.
  --org, --organization, --scope TEXT
                                  Org UUID/name, or 'none'/'global' for global
                                  scope. Omit = your org. (--organization /
                                  --scope are synonyms.)
  --help                          Show this message and exit.
```

### `solution scaffold-app`

```
Usage: solution scaffold-app [OPTIONS] SLUG

  Scaffold a standalone_v2 React app (package.json, vite, main.tsx, App.tsx).

Options:
  --path TEXT  App dir inside the solution workspace (default: apps/<slug>
               under the solution root).
  --help       Show this message and exit.
```

### `solution sdk`

```
Usage: solution sdk [OPTIONS] COMMAND [ARGS]...

  Manage the app's vendored Bifrost SDK.

Options:
  --help  Show this message and exit.

Commands:
  deployed-status  Show deployed SDK status for Apps owned by a Solution...
  deployed-update  Queue deployed SDK update jobs for Apps owned by a...
  update           Re-vendor the Bifrost SDK into the app (re-download +...
```

#### `solution sdk deployed-status`

```
Usage: solution sdk deployed-status [OPTIONS] SOLUTION_REF

  Show deployed SDK status for Apps owned by a Solution install.

Options:
  --help  Show this message and exit.
```

#### `solution sdk deployed-update`

```
Usage: solution sdk deployed-update [OPTIONS] SOLUTION_REF

  Queue deployed SDK update jobs for Apps owned by a Solution install.

Options:
  --help  Show this message and exit.
```

#### `solution sdk update`

```
Usage: solution sdk update [OPTIONS] [PATH]

  Re-vendor the Bifrost SDK into the app (re-download + reinstall).

Options:
  --app TEXT  standalone_v2 app slug (required when the Solution has multiple
              apps).
  --url TEXT  Bifrost instance URL (default: current profile).
  --help      Show this message and exit.
```

### `solution start`

```
Usage: solution start [OPTIONS] [APP_SLUG]

  Run the app's dev server + local workflows on one stable origin. Preview
  credentials are renewed automatically.

Options:
  --solution TEXT    Install id or unique slug.
  --url TEXT         Bifrost instance URL (default: current profile).
  --port INTEGER     Stable local proxy origin port; reuse it across restarts.
                     [default: 3000]
  --host TEXT        Address for the local origin to bind.  [default:
                     127.0.0.1]
  --public-url TEXT  Browser-visible origin for the local proxy, e.g.
                     https://dev.example.
  --help             Show this message and exit.
```

### `solution swap-slugs`

```
Usage: solution swap-slugs [OPTIONS] APP_A APP_B

  Atomically exchange two apps' slugs (v1→v2 migration cutover).

Options:
  --help  Show this message and exit.
```

### `solution sync`

```
Usage: solution sync [OPTIONS] SOLUTION_REF

  Update a Git-connected Solution from its configured ref.

Options:
  --help  Show this message and exit.
```

### `solution update`

```
Usage: solution update [OPTIONS] [PATH]

  Edit install-local fields (name, scope, access gates) of an existing
  install.

Options:
  --solution TEXT                 Install id or unique slug (default:
                                  workspace binding or descriptor slug).
  --name TEXT                     New display name.
  --allow-outbound-access / --no-allow-outbound-access
                                  Let the install fall back to shared _repo
                                  resources.
  --allow-inbound-access / --no-allow-inbound-access
                                  Let other installs target this one via per-
                                  call solution refs.
  --url TEXT                      Bifrost instance URL (default: current
                                  profile).
  --global                        Target global scope (org=NULL). Alias for
                                  --org global.
  --org, --organization, --scope TEXT
                                  Org UUID/name, or 'none'/'global' for global
                                  scope. Omit = your org. (--organization /
                                  --scope are synonyms.)
  --help                          Show this message and exit.
```

## `tables`

```
Usage: tables [OPTIONS] COMMAND [ARGS]...

  Manage tables.

Options:
  --json  Emit JSON instead of human-readable output.
  --help  Show this message and exit.

Commands:
  create    Create a new table.
  delete    Delete a table and all its documents.
  get       Get a single table by UUID or name.
  list      List all tables (wrapped ``{tables, total}`` payload from the...
  policies  Manage table access policies.
  update    Update a table.
```

### `tables create`

```
Usage: tables create [OPTIONS]

  Create a new table.

  ``--schema`` accepts a JSON literal or ``@path/to/schema.yaml`` — the file
  is loaded and embedded as the table schema dict. ``--policies`` accepts the
  same shape and embeds row-level access policies; see
  ``docs/superpowers/specs/2026-04-30-table-policies-design.md``.

  Org targeting follows the unified ``--org`` standard: HOME (omit) scopes the
  table to the caller's org, ``--global`` makes it global, ``--org <id|name>``
  scopes it to that org.

Options:
  --name TEXT                     name  [required]
  --description TEXT              description
  --schema TEXT                   schema as JSON literal or @path to a
                                  YAML/JSON file.
  --policies TEXT                 policies as JSON literal or @path to a
                                  YAML/JSON file.
  --global                        Target global scope (org=NULL). Alias for
                                  --org global.
  --org, --organization, --scope TEXT
                                  Org UUID/name, or 'none'/'global' for global
                                  scope. Omit = your org. (--organization /
                                  --scope are synonyms.)
  --json                          Emit JSON instead of human-readable output.
  --help                          Show this message and exit.
```

### `tables delete`

```
Usage: tables delete [OPTIONS] REF

  Delete a table and all its documents.

  ``REF`` is a UUID or table name. Cascade deletes the table's documents at
  the DB level — irreversible.

Options:
  --json  Emit JSON instead of human-readable output.
  --help  Show this message and exit.
```

### `tables get`

```
Usage: tables get [OPTIONS] REF

  Get a single table by UUID or name.

Options:
  --json  Emit JSON instead of human-readable output.
  --help  Show this message and exit.
```

### `tables list`

```
Usage: tables list [OPTIONS]

  List all tables (wrapped ``{tables, total}`` payload from the API).

Options:
  --json  Emit JSON instead of human-readable output.
  --help  Show this message and exit.
```

### `tables policies`

```
Usage: tables policies [OPTIONS] COMMAND [ARGS]...

  Manage table access policies.

Options:
  --json  Emit JSON instead of human-readable output.
  --help  Show this message and exit.

Commands:
  get  Get the access policies for a table.
  set  Set the access policies for a table.
```

#### `tables policies get`

```
Usage: tables policies get [OPTIONS] REF

  Get the access policies for a table.

  ``REF`` is a UUID or table name. Returns the ``policies`` field from the
  table record, which may contain inline policy objects and/or ``{"$ref":
  "rule-name"}`` references to named policy rules.

Options:
  --help  Show this message and exit.
```

#### `tables policies set`

```
Usage: tables policies set [OPTIONS] REF

  Set the access policies for a table.

  ``REF`` is a UUID or table name. ``--file`` must be a JSON or YAML document
  whose ``policies`` key (or top-level list) contains policy objects and/or
  ``{"$ref": "rule-name"}`` references to named policy rules. The document is
  round-tripped unchanged — ``$ref`` entries are stored and later resolved at
  query time.

Options:
  --file FILE  JSON/YAML policy document to store. May contain ``{"$ref":
               "rule-name"}`` entries.  [required]
  --help       Show this message and exit.
```

### `tables update`

```
Usage: tables update [OPTIONS] REF

  Update a table.

  ``REF`` is a UUID or table name. Names are resolved via
  :class:`RefResolver`; ambiguous names fail loudly with the candidate list.
  Unset flags are omitted from the payload so only the supplied fields are
  patched.

  If ``--name`` changes the table's current name, a prominent warning is
  printed to stderr — workflow SDK code that looks up tables by name will
  break on rename. No confirmation is required; the warning just nudges the
  caller to grep their workspace before committing.

  Passing ``--org``/``--global`` re-scopes the table (HOME leaves the scope
  unchanged, since omitting org sends no ``organization_id``).

Options:
  --name TEXT                     name
  --description TEXT              description
  --schema TEXT                   schema as JSON literal or @path to a
                                  YAML/JSON file.
  --policies TEXT                 policies as JSON literal or @path to a
                                  YAML/JSON file.
  --global                        Target global scope (org=NULL). Alias for
                                  --org global.
  --org, --organization, --scope TEXT
                                  Org UUID/name, or 'none'/'global' for global
                                  scope. Omit = your org. (--organization /
                                  --scope are synonyms.)
  --json                          Emit JSON instead of human-readable output.
  --help                          Show this message and exit.
```

## `users`

```
Usage: users [OPTIONS] COMMAND [ARGS]...

  Show and change what a user can do, and ask what their access would be.

Options:
  --json  Emit JSON instead of human-readable output.
  --help  Show this message and exit.

Commands:
  access    Show a user's access, or check what it would allow.
  create    Create a custom identity in --org, or Global.
  defaults  Read or set the base role assigned to new users and custom...
  list      List the people you may read, or with --identities the...
  roles     Show and replace a user's roles.
```

### `users access`

```
Usage: users access [OPTIONS] COMMAND [ARGS]...

  Show a user's access, or check what it would allow.

Options:
  --json  Emit JSON instead of human-readable output.
  --help  Show this message and exit.

Commands:
  check  Show how the access model decides USER performing --operation in...
  show   Show what USER can do, and where.
```

#### `users access check`

```
Usage: users access check [OPTIONS] USER

  Show how the access model decides USER performing --operation in --org.

  USER is a UUID, email, or identity name.

  Examples:

    bifrost users access check ada@contoso.test --org global --operation tables.documents.create
    bifrost users access check ada@contoso.test --org Contoso --operation tables.documents.create --workflow "Sync Invoices"

Options:
  --org TEXT        Organization UUID or name, or 'global'.  [required]
  --operation TEXT  Catalog operation id or 'METHOD /api/path'.  [required]
  --workflow TEXT   Workflow whose powers apply (UUID, name, or path::func).
                    Omit to act directly.
  --json            Emit JSON instead of human-readable output.
  --help            Show this message and exit.
```

#### `users access show`

```
Usage: users access show [OPTIONS] USER

  Show what USER can do, and where.

  Lists every place the user reaches and the permissions held there. `bifrost
  users access USER` is the same as `bifrost users access show USER`.

  USER is a UUID, email, or identity name.

  Example:

    bifrost users access ada@contoso.test

Options:
  --json  Emit JSON instead of human-readable output.
  --help  Show this message and exit.
```

### `users create`

```
Usage: users create [OPTIONS]

  Create a custom identity in --org, or Global.

  The identity starts with the configured default base role and no additional
  roles. Use --base-role to select a different base role, then point a
  workflow at it with `bifrost workflows update --run-as`.

  Example:

    bifrost users create --identity --org Contoso --name "Contoso Nightly"

Options:
  --identity        Create an identity (the only thing created here).
                    [required]
  --org TEXT        Organization UUID or name, or 'global'.  [required]
  --name TEXT       The identity's name.  [required]
  --base-role TEXT  Explicit base role UUID or name; omit for the configured
                    default.
  --json            Emit JSON instead of human-readable output.
  --help            Show this message and exit.
```

### `users defaults`

```
Usage: users defaults [OPTIONS] COMMAND [ARGS]...

  Read or set the base role assigned to new users and custom identities.

Options:
  --json  Emit JSON instead of human-readable output.
  --help  Show this message and exit.

Commands:
  get  Show the configured and effective default base role.
  set  Choose a default for new accounts; existing accounts are unchanged.
```

#### `users defaults get`

```
Usage: users defaults get [OPTIONS]

  Show the configured and effective default base role.

Options:
  --org TEXT  Organization UUID or name; omit for the instance default.
  --json      Emit JSON instead of human-readable output.
  --help      Show this message and exit.
```

#### `users defaults set`

```
Usage: users defaults set [OPTIONS]

  Choose a default for new accounts; existing accounts are unchanged.

Options:
  --org TEXT   Organization UUID or name; omit for the instance default.
  --role TEXT  Default base role UUID or name.
  --inherit    Clear an org override, or reset the instance default to User.
  --json       Emit JSON instead of human-readable output.
  --help       Show this message and exit.
```

### `users list`

```
Usage: users list [OPTIONS]

  List the people you may read, or with --identities the identities.

  Identities are the accounts that run work no person started: each
  organization's default, the global default, and custom ones.

Options:
  --identities  List identities instead of people.
  --json        Emit JSON instead of human-readable output.
  --help        Show this message and exit.
```

### `users roles`

```
Usage: users roles [OPTIONS] COMMAND [ARGS]...

  Show and replace a user's roles.

Options:
  --json  Emit JSON instead of human-readable output.
  --help  Show this message and exit.

Commands:
  get  Show USER's base role and additional roles, with the places each...
  set  Replace USER's additional roles, and optionally their base role.
```

#### `users roles get`

```
Usage: users roles get [OPTIONS] USER

  Show USER's base role and additional roles, with the places each applies.

  USER is a UUID, email, or identity name.

Options:
  --json  Emit JSON instead of human-readable output.
  --help  Show this message and exit.
```

#### `users roles set`

```
Usage: users roles set [OPTIONS] USER

  Replace USER's additional roles, and optionally their base role.

  USER is a UUID, email, or identity name.

  The --role options replace the additional roles; --no-roles removes them
  all. With only --base, the additional roles stay as they are.

  Examples:

    bifrost users roles set ada@contoso.test --role Helpdesk=org:Contoso,org:Fabrikam
    bifrost users roles set ada@contoso.test --base User --role Auditor=all
    bifrost users roles set ada@contoso.test --no-roles

Options:
  --base TEXT           Base role (UUID or name). Omit to keep the current
                        one.
  --role ROLE[=PLACES]  Additional role, repeatable. PLACES is a comma list of
                        org:<organization>, customers, global or all; omit it
                        for the role's default (the user's home organization).
  --no-roles            Remove every additional role.
  --json                Emit JSON instead of human-readable output.
  --help                Show this message and exit.
```

## `workflows`

```
Usage: workflows [OPTIONS] COMMAND [ARGS]...

  Manage workflows.

Options:
  --json  Emit JSON instead of human-readable output.
  --help  Show this message and exit.

Commands:
  convert          Analyze, review and convert workflow permissions.
  delete           Delete a workflow by removing its function from the...
  execute          Execute a registered workflow remotely and stream logs...
  get              Get a single workflow by UUID, name, or ``path::func``...
  grant            Grant the identity a workflow runs as what Recommended...
  grant-role       Grant a role access to a workflow.
  list             List all workflows visible to the caller.
  list-orphaned    List all orphaned workflows (backing file deleted or...
  recommendations  Show what the identity a workflow runs as would also...
  register         Register a decorated function from an existing...
  remap            Move references from one workflow ID to another active...
  replace          Repoint an orphaned workflow to a new file location.
  revoke-role      Revoke a role's access from a workflow.
  update           Update a workflow's editable properties.
```

### `workflows convert`

```
Usage: workflows convert [OPTIONS] COMMAND [ARGS]...

  Analyze, review and convert workflow permissions.

Options:
  --json  Emit JSON instead of human-readable output.
  --help  Show this message and exit.

Commands:
  analyze  Start durable read-only analysis.
  apply    Apply explicitly reviewed proposals; stale proposals are refused.
  cutover  Request the final reviewed platform switch.
  report   Read a page of a saved analysis without restarting it.
```

#### `workflows convert analyze`

```
Usage: workflows convert analyze [OPTIONS]

  Start durable read-only analysis. Observe it with platform-jobs get.

Options:
  --workflow TEXT     Workflow UUID, name or path::function. Repeat for a
                      selection.
  --scope TEXT        all, global, or an organization UUID when no workflows
                      are selected.
  --platform-cutover  Prepare a platform-wide readiness review; does not
                      change the default.
  --json              Emit JSON instead of human-readable output.
  --help              Show this message and exit.
```

#### `workflows convert apply`

```
Usage: workflows convert apply [OPTIONS] JOB_ID

  Apply explicitly reviewed proposals; stale proposals are refused.

Options:
  --review-file FILENAME  JSON reviewed selections, fingerprints and explicit
                          acknowledgements from the saved report.  [required]
  --json                  Emit JSON instead of human-readable output.
  --help                  Show this message and exit.
```

#### `workflows convert cutover`

```
Usage: workflows convert cutover [OPTIONS] JOB_ID

  Request the final reviewed platform switch. Analysis alone never switches
  it.

Options:
  --acknowledge-platform-cutover  Explicitly request Declared Permissions as
                                  the platform default after readiness is
                                  revalidated.  [required]
  --json                          Emit JSON instead of human-readable output.
  --help                          Show this message and exit.
```

#### `workflows convert report`

```
Usage: workflows convert report [OPTIONS] JOB_ID

  Read a page of a saved analysis without restarting it.

Options:
  --offset INTEGER RANGE  [x>=0]
  --limit INTEGER RANGE   [1<=x<=200]
  --json                  Emit JSON instead of human-readable output.
  --help                  Show this message and exit.
```

### `workflows delete`

```
Usage: workflows delete [OPTIONS] REF

  Delete a workflow by removing its function from the source file.

  ``REF`` is a UUID, workflow name, or ``path::func`` locator. Without
  ``--force``, the API performs a deactivation-protection pre-check and
  returns 409 if the workflow has dependents; pass ``--force`` to bypass.

Options:
  --force / --no-force  Skip the deactivation protection check and delete the
                        workflow even if it has dependent forms/apps/agents.
  --json                Emit JSON instead of human-readable output.
  --help                Show this message and exit.
```

### `workflows execute`

```
Usage: workflows execute [OPTIONS] REF

  Execute a registered workflow remotely and stream logs as it runs.

  ``REF`` is a workflow UUID, name, or ``path::func`` locator. The command:

  1. Resolves ``REF`` and posts to ``/api/workflows/execute`` (async — does
  not block the platform). 2. Connects to ``/ws/execution/{id}`` and prints
  log lines as they arrive. 3. Exits when the execution reaches a terminal
  status, after a final GET    to backfill any logs that emitted before the
  WebSocket connected and    to fetch the final result.

  Use ``bifrost run <file> --workflow <name>`` for local-file iteration —
  ``execute`` targets workflows already registered on the platform.

Options:
  --params TEXT       JSON object of input parameters (e.g. --params
                      '{"name":"World"}').
  --params-file FILE  Path to a JSON file with input parameters. Mutually
                      exclusive with --params.
  --org TEXT          Override execution org context (UUID or name). Requires
                      workflow execution permission at a reachable
                      organization. Omit to use the caller's default org.
  --json              Emit JSON instead of human-readable output.
  --help              Show this message and exit.
```

### `workflows get`

```
Usage: workflows get [OPTIONS] REF

  Get a single workflow by UUID, name, or ``path::func`` ref.

  Resolves ``REF`` via :class:`RefResolver`, then calls ``GET
  /api/workflows/{uuid}`` directly (platform admin only; admins can read any
  org's workflow by id).

Options:
  --json  Emit JSON instead of human-readable output.
  --help  Show this message and exit.
```

### `workflows grant`

```
Usage: workflows grant [OPTIONS] REF

  Grant the identity a workflow runs as what Recommended Access recommends.

  Each grant is merged into the identity's existing assignment of that role. A
  recommendation without a grant needs a role chosen: use `bifrost users roles
  set`. A default identity is shared by every workflow that runs as it, so
  granting to one needs --yes.

  Examples:

    bifrost workflows grant "Sync Invoices" --recommendation 1
    bifrost workflows grant "Sync Invoices" --all
    bifrost workflows grant "Sync Invoices" --recommendation 1 --yes

Options:
  --recommendation N  Number of a recommendation from `workflows
                      recommendations`, repeatable.
  --all               Apply every recommendation that has a grant.
  --yes               Confirm granting to a default identity, which other
                      workflows share.
  --json              Emit JSON instead of human-readable output.
  --help              Show this message and exit.
```

### `workflows grant-role`

```
Usage: workflows grant-role [OPTIONS] REF ROLE_REF

  Grant a role access to a workflow.

  ``REF`` is a workflow UUID / name / ``path::func``. ``ROLE_REF`` is a role
  UUID or role name. The underlying endpoint accepts a batch of role IDs —
  this command sends a single-element list for simplicity.

Options:
  --json  Emit JSON instead of human-readable output.
  --help  Show this message and exit.
```

### `workflows list`

```
Usage: workflows list [OPTIONS]

  List all workflows visible to the caller.

Options:
  --json  Emit JSON instead of human-readable output.
  --help  Show this message and exit.
```

### `workflows list-orphaned`

```
Usage: workflows list-orphaned [OPTIONS]

  List all orphaned workflows (backing file deleted or function removed).

  Orphaned workflows are workflows whose source file no longer exists or no
  longer contains the decorated function. They can be repointed with ``bifrost
  workflows replace``.

Options:
  --json  Emit JSON instead of human-readable output.
  --help  Show this message and exit.
```

### `workflows recommendations`

```
Usage: workflows recommendations [OPTIONS] REF

  Show what the identity a workflow runs as would also need.

  Recommended Access, based on the access checks the workflow's recent runs
  recorded: reach into other organizations, roles its policies look for, and
  the workflow's own roles. Empty until runs are observed. Apply the grants
  with `bifrost workflows grant`.

  ``REF`` is a UUID, workflow name, or ``path::func`` locator.

Options:
  --json  Emit JSON instead of human-readable output.
  --help  Show this message and exit.
```

### `workflows register`

```
Usage: workflows register [OPTIONS]

  Register a decorated function from an existing workspace ``.py`` file.

  The file must already exist in the workspace. Write it directly with
  ``bifrost files write`` or the file editor first. This command indexes a
  ``@workflow`` / ``@tool`` / ``@data_provider`` function so it becomes
  executable via the API.

  Omit the target to preserve an inactive workflow's organization. New
  registrations default to the caller's runtime or home organization.
  ``--global`` makes it global; ``--org <id|name>`` scopes it to that org.

  ``--access-level`` and ``--role-ids`` set the workflow's access controls at
  registration time, mirroring the create-time surface for forms and apps.
  Role refs accept names or UUIDs and are resolved before the request.

Options:
  --path TEXT                     Workspace-relative path to the .py file
                                  containing the decorated function.
                                  [required]
  --function-name TEXT            Name of the decorated function to register.
                                  [required]
  --global                        Target global scope (org=NULL). Alias for
                                  --org global.
  --org, --organization, --scope TEXT
                                  Org UUID/name, or 'none'/'global' for global
                                  scope. Omit = your org. (--organization /
                                  --scope are synonyms.)
  --access-level [authenticated|everyone|role_based]
                                  Access level for the workflow. Omit to leave
                                  at default.
  --role-ids TEXT                 Role refs (UUID or name) for role_based
                                  access. Repeat the flag for multiple, or
                                  pass a comma-separated list.
  --json                          Emit JSON instead of human-readable output.
  --help                          Show this message and exit.
```

### `workflows remap`

```
Usage: workflows remap [OPTIONS] SOURCE_REF

  Move references from one workflow ID to another active workflow ID.

Options:
  --to TEXT  Active workflow ref (UUID, name, or path::func) to receive
             references.  [required]
  --json     Emit JSON instead of human-readable output.
  --help     Show this message and exit.
```

### `workflows replace`

```
Usage: workflows replace [OPTIONS] REF

  Repoint an orphaned workflow to a new file location.

  ``REF`` is a UUID or workflow name (use ``bifrost workflows list-orphaned``
  to find orphaned UUIDs). The target file must exist in the workspace and
  contain a ``@workflow``, ``@tool``, ``@data_provider``, or ``@service``
  decorated function with the given name. The workflow UUID is preserved so
  form/agent references remain intact.

Options:
  --path TEXT           Workspace-relative path to the .py file containing the
                        decorated function.  [required]
  --function-name TEXT  Name of the decorated function to point this workflow
                        at.  [required]
  --allow-type-change   Allow the decorator type to change (e.g. @workflow →
                        @data_provider). Off by default to prevent silently
                        breaking form bindings.
  --json                Emit JSON instead of human-readable output.
  --help                Show this message and exit.
```

### `workflows revoke-role`

```
Usage: workflows revoke-role [OPTIONS] REF ROLE_REF

  Revoke a role's access from a workflow.

  ``REF`` is a workflow UUID / name / ``path::func``. ``ROLE_REF`` is a role
  UUID or role name.

Options:
  --json  Emit JSON instead of human-readable output.
  --help  Show this message and exit.
```

### `workflows update`

```
Usage: workflows update [OPTIONS] REF

  Update a workflow's editable properties.

  ``REF`` is a UUID, workflow name, or ``path::func`` locator. See
  :mod:`bifrost.refs` for resolution rules.

Options:
  --run-as TEXT                   Identity the workflow runs as when no person
                                  starts it: UUID, name, or name with its
                                  place, e.g. 'Default Identity (Contoso)'.
  --run-as-default                Run as the organization's default identity
                                  again.
  --organization-id TEXT          organization_id
  --access-level TEXT             access_level
  --clear-roles / --no-clear-roles
                                  clear_roles (tri-state; omit to leave
                                  unchanged).
  --role-ids TEXT                 role_ids (repeat for multiple; comma-split
                                  also accepted).
  --name TEXT                     name
  --description TEXT              description
  --category TEXT                 category
  --timeout-seconds INTEGER       timeout_seconds
  --memory-request-mib INTEGER    memory_request_mib
  --tags TEXT                     tags (repeat for multiple).
  --endpoint-enabled / --no-endpoint-enabled
                                  endpoint_enabled (tri-state; omit to leave
                                  unchanged).
  --public-endpoint / --no-public-endpoint
                                  public_endpoint (tri-state; omit to leave
                                  unchanged).
  --json                          Emit JSON instead of human-readable output.
  --help                          Show this message and exit.
```

