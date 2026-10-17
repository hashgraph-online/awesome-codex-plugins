<h1 align="center">Security</h1>

---

<p align="center"><strong>Report a vulnerability privately, never in a public issue.</strong> Use
<a href="https://github.com/awss1i/assay/security/advisories/new">Report a vulnerability</a>
on the Security tab. A fix goes out as a new release on PyPI.</p>

---

## Contents

- [What the Plugin Does](#what-the-plugin-does)
- [Supported Versions](#supported-versions)

---

## What the Plugin Does

This plugin adds a hook for Claude Code and the DeepSeek Harness. After a turn
that changed a page, the hook runs the `assay` command on that page and reports
what it found. It runs nothing else, and it never edits code.

assay serves the folder over loopback only (`127.0.0.1`, on a random port) and
opens the page in Chromium through Playwright. It never runs a build or
installs anything. The full boundaries are in the repository's
[SECURITY.md](https://github.com/awss1i/assay/blob/main/SECURITY.md).

The hook running anything other than `assay`, or assay reaching outside that
folder or outside loopback, is a vulnerability. Anything a page can normally do
inside a browser is not.

---

## Supported Versions

The latest release on PyPI.
