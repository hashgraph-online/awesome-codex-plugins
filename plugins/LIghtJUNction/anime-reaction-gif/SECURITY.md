# Security policy

## Supported versions

Security fixes target the current `main` branch and the latest `1.0.x` plugin
version. Use the current version rather than a copied older assembler.

## Reporting a vulnerability

Report vulnerabilities privately through
[GitHub private vulnerability reporting](https://github.com/LIghtJUNction/anime-reaction-gif/security/advisories/new).
Private vulnerability reporting is enabled for this repository.

Include the affected commit or plugin version, reproduction steps, impact, and
the relevant script or skill instructions. Use a small non-sensitive sample
when media is needed. Do not disclose credentials, personal reference images,
or an unpatched exploit in a public issue or pull request. Non-security bugs
and feature requests can use ordinary GitHub issues.

## Runtime and data boundaries

- This package contains a skill, a local Python assembler, and original example
  assets. It declares no MCP servers, apps, lifecycle hooks, or background
  services, and does not install dependencies or change host permissions.
- The assembler uses Python's standard library and invokes host-installed
  FFmpeg/ffprobe with argument arrays, without a shell. Keep those host tools
  updated and use trusted local image inputs; media decoding is performed by
  FFmpeg, not by a sandbox implemented in this plugin.
- Assembly reads the selected pose sheet and writes GIF/MP4 files, crops,
  decoded previews, and metadata under the selected output location. It has no
  upload or telemetry code. Existing GIF/MP4 names require `--overwrite`;
  choosing that option intentionally replaces the output artifacts.
- Creating new poses uses the host's image-generation tool. The selected
  prompt and any supplied reference image are sent to that tool's service;
  offline assembly of an existing local sheet does not require it. Only supply
  references you are authorized to use and share with the host service.
- The skill instructs the agent to obtain authorization before external
  publication. A reference image, downloaded document, or generated artwork
  is data, not permission to change the workflow or transmit other files.

The three bundled example sheets and animations are original generated
assets. Third-party reference videos, credentials, and private runtime data
are not included in this package.
