# Connection diagnosis

Inspect `mcp-startup.jsonl` in the plugin user-data directory and host startup logs.
The bootstrap resolves the currently registered installation at each handshake.
It captures marketplace identity from the initial cache namespace, then moves its
working directory to existing user-data storage outside the entire replaceable
cache entry. Retaining the namespace itself as cwd also locks CLI cache backup on
Windows; retaining only the version's parent is insufficient.
An older host may retain an obsolete entrypoint; the supported
`scripts/install-local.mjs` update restores compatibility entrypoints. MCP reload
alone may retain the host's old plugin catalog. Do not repeat an ineffective reload
or retry a deterministic process exit by sleeping.

Normal installation preserves current-version MCP processes, including when the
CLI fails with a sharing violation. Do not kill those processes to make an update
appear successful. Successful obsolete-version retirement can release its exact
old processes and reports `mcp_connection_refresh_required`. This flag records
forced disconnection; false does not prove a live process loaded updated code.
Existing task clients may retain a closed connection even after the new installation
passes a standalone handshake. Prefer the host's MCP reload/reconnect mechanism
and verify a real tool call in the intended execution session. Refreshing the Skill
catalog alone does not establish MCP reconnection. Complete all code changes and
installation before creating user-authorized experimental sessions; restarting
code during their trial invalidates the connection preflight.

After installing or updating desktop plugin metadata, use the supported catalog
reload and reopen the embedded workbench. Request an application restart only if
the relevant reload is unavailable or demonstrably ineffective; a failed tool call
alone does not establish that. Opening the App does not require creating another task. Use the
standalone console only when requested or when the host lacks App support; do not
silently replace a failed embedded view with a browser page.

Report the failed call and diagnostic evidence. A Workflow validation blocker
means the connection works. Never claim connection recovery before a host tool call
succeeds, or start a substitute server and claim the Workflow ran.
