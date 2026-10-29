# Security

Report suspected vulnerabilities privately to **support@bindry.ai**. Include the plugin version,
affected workflow, and a minimal reproduction. Do not include API keys or private Binder content.

This plugin runs local Node.js scripts. Pinned compilation writes skills and instruction files in
the selected project; live mode also connects to the configured Bindry MCP endpoint. A workspace
API key is required for private content and live mode. Keep keys outside source control and
public issue reports, and revoke an exposed key from the workspace that issued it.

Treat downloaded skills as instructions to review before use. A successful compilation or drift
check does not establish that a skill is safe or that an assistant will follow it.
