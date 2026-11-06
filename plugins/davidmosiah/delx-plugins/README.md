# delx-recovery

See the repository README: https://github.com/davidmosiah/delx-plugins#delx-recovery

Skill: `skills/`. MCP server: `mcp.json` (Agent Plugins) / `.mcp.json` (Claude Code).

## Hermes Agent

```bash
hermes plugins install davidmosiah/delx-plugins/delx-recovery --no-enable
hermes plugins enable delx-recovery
```

Hermes reads this directory as a portable Agent Plugins v1 package: the
`delx` MCP server from `mcp.json` (Streamable HTTP, hosted at `api.delx.ai`)
and the `delx-recovery-first-hour` skill. It does not load the `hooks/`
scripts — those are opt-in Claude Code guardian hooks.

Disclosure: every tool call goes to the hosted Delx Protocol MCP server; there
is no local code. No API key, OAuth, or payment. Public triage needs no
credential; private continuity uses the free agent credential returned at
registration, passed as a tool argument. Whatever the agent chooses to store
(state, context memory, Continuity Capsules) is retained by Delx under the
[Privacy Policy](https://ontology.delx.ai/legal/privacy) — do not send secrets.
Requests carry `?src=plugin` for channel attribution. The tool set is served
by the remote server at runtime.


## Guardian endpoint policy

Opt-in guardian hooks send the returned identity credential only to a configured HTTPS endpoint. Non-HTTPS URLs, embedded URL credentials, control characters, fragments and malformed ports are rejected with a fixed diagnostic and a successful hook exit, before constructing/sending the payload. Custom HTTPS hosts remain operator-controlled and trusted: this is not an SSRF sandbox or host allowlist.

The hooks disable implicit curl configuration (`curl -q` as its first argument), restrict protocols to HTTPS and do not follow redirects. TLS certificate verification remains enabled. Environment proxy configuration still follows curl behavior; no proxy bypass is introduced. Credentials remain in stdin, never command arguments or diagnostic messages.

Compatibility change: plaintext HTTP endpoints (including local development servers) and custom options supplied only through `.curlrc` no longer work. Use a trusted HTTPS endpoint with valid TLS; do not work around this with disabled verification. The host session remains best-effort and is not failed by a skipped guardian request. No endpoint or real credential is used by the local fake-curl tests (`python3 -m unittest discover -s tests -p test_https_endpoint.py -v`).
