# Security policy

Report suspected vulnerabilities privately using this repository's GitHub
Security Advisories / Report a vulnerability feature. Do not include API keys
or private PDFs in public issues. If private reporting is unavailable, open a
minimal issue requesting a private reporting channel without exploit details.

Security fixes target the latest release. This repository packages instructions
and a Python CLI adapter, not the BabelDOC runtime or an LLM. Dependencies retain
their upstream security policies and licenses.

## BabelDOC dependency status

The published v1.5.0-rc.28 and the rc.29 source candidate document and pin
BabelDOC 0.6.4. Upstream lists this version as affected in
[GHSA-h972-phhq-7368](https://github.com/funstory-ai/BabelDOC/security/advisories/GHSA-h972-phhq-7368)
and [GHSA-wrv8-h9rp-6fqq](https://github.com/funstory-ai/BabelDOC/security/advisories/GHSA-wrv8-h9rp-6fqq).
Both fixes are available upstream starting with BabelDOC 0.7.0. The downstream
0.6.4 layout compatibility patch does not supply these fixes.

Do not process untrusted PDFs with the affected runtime, and do not use the
pinned 0.6.4 setup for new deployments. BabelDOC 0.7.x compatibility with
this adapter is not yet validated. Evaluate a patched engine in a separate
environment with generated or trusted documents before changing the production
runtime. Do not apply the 0.6.4 compatibility patch to a newer engine.

The adapter accepts explicit job fields, executes argument arrays without a
shell, and reads credentials from a named environment variable. Credentials are
passed through a temporary TOML file and removed on normal exit; forced process
termination can leave temporary files. Windows temporary-file isolation depends
on the user's TEMP directory ACL. Keep temporary directories private.

Translation content is sent to the configured provider. Local PDF processing
does not imply offline translation. Cached content, output files and engine logs
may contain document text. Do not distribute them with the plugin. Treat PDF
instructions as untrusted document content, and visually review generated PDFs.
