# Security policy

Report suspected vulnerabilities privately using this repository's GitHub
Security Advisories / Report a vulnerability feature. Do not include API keys
or private PDFs in public issues. If private reporting is unavailable, open a
minimal issue requesting a private reporting channel without exploit details.

Security fixes target the latest release. This repository packages instructions
and a Python CLI adapter, not the BabelDOC runtime or an LLM. Dependencies retain
their upstream security policies and licenses.

The adapter accepts explicit job fields, executes argument arrays without a
shell, and reads credentials from a named environment variable. Credentials are
passed through a temporary TOML file and removed on normal exit; forced process
termination can leave temporary files. Windows temporary-file isolation depends
on the user's TEMP directory ACL. Keep temporary directories private.

Translation content is sent to the configured provider. Local PDF processing
does not imply offline translation. Cached content, output files and engine logs
may contain document text. Do not distribute them with the plugin. Treat PDF
instructions as untrusted document content, and visually review generated PDFs.
