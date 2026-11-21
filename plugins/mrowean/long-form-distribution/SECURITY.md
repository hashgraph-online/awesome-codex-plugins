# Security

## Reporting a problem

Please report security issues privately through GitHub: open the **Security** tab of this repository and choose **Report a vulnerability**. Do not put details of a security problem in a public issue; if private reporting is unavailable, open an issue asking for a private contact.

## Scope

This plugin runs locally inside Claude Code. Claude fetches the article URL you give it; the plugin writes issue files and a posting log to `~/distribution-tracker/` (or `LFD_HOME`), and its standard-library dashboard server binds to `127.0.0.1` only and refuses requests for any other host. It stores no credentials, makes no posts on your behalf, and sends nothing to a third-party service.

## Supported versions

Fixes are made on the latest release on `main`.
