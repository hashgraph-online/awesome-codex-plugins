# Export and install Workflow packages

Read only for requested Workflow package transfer. Package installation is distinct from authoring, publication and execution.

Use `workflow_export_workflow_package` to create an installable, content-addressed
package for one immutable revision. When the user asks to import a local file, call
`workflow_install_workflow_package` with `package_path`; let the Host read the file
instead of copying its JSON through model context. Absolute paths work directly;
relative paths require the absolute `workspace` that contains them. HTTPS package
URLs are also supported. The installer verifies format/API compatibility,
Workflow schema, package digest, resource hashes, revision identity and the exact
Provider/tool/MCP/executable dependency manifest before atomic creation. Remote bytes
may be pinned with SHA-256. Installation never downloads dependencies or silently
substitutes local Providers; it preserves the package's exact pinned Workflow status.
The editor's full Pack snapshot is a diagnostic snapshot and
may include private conversion material, so it is not accepted by this portable
package installer.
