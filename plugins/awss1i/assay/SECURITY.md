<h1 align="center">Security</h1>

<p align="center"><a href="../../README.md">assay</a> › <a href="README.md">The Skill &amp; Plugin</a> › Security</p>

<p align="center">How to report a vulnerability in the plugin, and what counts as one.</p>

---

## Contents

- [Reporting a vulnerability](#reporting-a-vulnerability)
- [What the plugin does](#what-the-plugin-does)
- [Supported versions](#supported-versions)

---

## Reporting a vulnerability

Report a vulnerability privately, never in a public issue. Use Report a
vulnerability on the repository's Security tab. A fix goes out as a new
release on PyPI.

[Report a vulnerability](https://github.com/awss1i/assay/security/advisories/new)

---

## What the plugin does

This plugin adds a `Stop` hook for every harness that runs Claude Code plugin
hooks. After a turn that changed a page, the hook runs the `assay` command on
that page and reports what it found. It runs nothing else, and it never edits
code.

assay serves the folder over loopback only (`127.0.0.1`, on a random port),
without its hidden files, and opens the page in Chromium through Playwright,
with Chromium's sandbox on wherever the system allows it. It never runs a
project's build or installs its dependencies.

The hook running anything other than `assay`, or assay reaching outside that
folder or outside loopback, is a vulnerability. Anything a page can normally do
inside a browser is not. assay's own security page has the full boundaries.

[assay's security page](https://github.com/awss1i/assay/blob/main/SECURITY.md)

---

## Supported versions

The latest release on PyPI.
