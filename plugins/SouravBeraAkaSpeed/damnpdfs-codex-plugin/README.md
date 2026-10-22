# DamnPDFs plugin package

This folder is the installable Codex package: `.codex-plugin/plugin.json`, `.mcp.json`, dependency-free `mcp/` bridge, branded `assets/` and the `file-tools` skill.

Install the marketplace `SouravBeraAkaSpeed/damnpdfs-codex-plugin`, then `damnpdfs@damnpdfs`, or upload the release ZIP through Codex's **Plugins → Add → Upload plugin archive**. Requires Node.js 22+ and a connected DamnPDFs browser tab. Begin with connection status and the public catalog check; no file upload happens until requested.

Read [connection and privacy](skills/file-tools/references/connection.md) before processing sensitive files. Only upload files you own or have permission to process. Import uses temporary cloud storage; export creates new local files and refuses overwriting. The bridge does not read Codex account files or persist session credentials. To disconnect, deliberately invoke `session_revoke` or use the website's Agent access Disconnect action.

Visit [DamnPDFs](https://damnpdfs.com/), [support](https://damnpdfs.com/contact), [privacy](https://damnpdfs.com/privacy) or [terms](https://damnpdfs.com/terms). See the repository's README for installation, testing and limitations.
