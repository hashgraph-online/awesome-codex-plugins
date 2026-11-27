# Security Policy

design-helper is a plugin of six skills made of instructions and a small kit in
[`shared/assets/`](shared/assets/). The code it runs:

- a Python server bound to `127.0.0.1` that serves the comparison sheet from a temporary
  folder outside the project (see [`liveview.md`](shared/liveview.md))
- Node scripts that open a headless browser with Playwright to measure and screenshot the
  sheet (`check.cjs`, `walk.cjs`, `pixel.cjs`, `motion.cjs`)
- `npm pack` downloads of public packages the project doesn't have (icon sets, GSAP,
  Motion, typefaces, opentype.js), unpacked into that temporary folder. Nothing is
  installed into the project; the libraries only run inside the comparison pages in your
  local browser.

Report anything that could make it expose files, listen beyond localhost, write into the
project before you pick, fetch from anywhere but the npm registry, or leave processes or
files behind.

## Supported versions

Only the latest release receives fixes.

## Reporting a vulnerability

Report privately through GitHub:
[Security → Report a vulnerability](https://github.com/Dessert99/design-helper/security/advisories/new).
Please don't open a public issue for a security problem.

You can expect a first response within a week.
