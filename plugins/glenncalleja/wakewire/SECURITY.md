# Security

This plugin's MCP server talks only to the local wakewire daemon over
127.0.0.1 with a bearer token; it exposes no network services and stores no
secrets (secrets live in the OS keychain via the daemon). For the full threat
model and disclosure policy, see the repository's
[SECURITY.md](https://github.com/glenncalleja/wakewire/blob/main/SECURITY.md).
Report vulnerabilities via GitHub security advisories on the main repository.
