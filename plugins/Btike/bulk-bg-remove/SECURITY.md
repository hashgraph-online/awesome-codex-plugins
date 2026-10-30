# Security policy

## Reporting a vulnerability

Please report it privately through
[GitHub's private vulnerability reporting](https://github.com/Btike/bulk-bg-remove/security/advisories/new),
never in a public issue, discussion or pull request. Include the version
(`bulk-bg-remove --version`), the platform and the steps or file that trigger it.

The report stays private in the advisory until a fix is released.

## Supported versions

Fixes ship as a new release on [PyPI](https://pypi.org/project/bulk-bg-remove/).
Upgrade with `uv tool upgrade bulk-bg-remove`.

## What is in scope

bulk-bg-remove runs on your machine and uploads nothing. The parts worth a look:

- **The local UI** (`bulk-bg-remove` with no arguments, or `--ui`): it listens on `127.0.0.1`
  only, every API call needs the random token from the URL the CLI opened, and the
  `Host` header must be the local address. A way around any of these is in scope.
- **Reading images**: a crafted image that runs code, writes outside the output folder
  or reads files it should not.
- **Paths**: any way an input or output path makes the engine modify, move or delete an
  original, or write outside the output folder (`<name>-no-bg/` next to the input, the
  `-o` folder, or `~/Downloads` for the UI) and the temporary folder it uses for sheets
  and uploads.
- **The agent skill**: instructions in `SKILL.md` that would lead an agent to run
  commands outside the skill's `allowed-tools` without asking the user.

Model weights are downloaded by [rembg](https://github.com/danielgatis/rembg) on first
use; issues in rembg, ONNX Runtime, Pillow or pillow-heif themselves belong to those
projects, but tell us if bulk-bg-remove uses them unsafely.
