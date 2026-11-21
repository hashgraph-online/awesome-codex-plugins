# Security policy

## Reporting a vulnerability

Report a vulnerability in FigureAtlas by opening a GitHub security advisory on [TardisBooo/figureatlas](https://github.com/TardisBooo/figureatlas/security/advisories/new). If that form is unavailable, open a public issue and leave out exploit details, credentials, and private data.

Please include the figure id, the command you ran, and the version from `package.json`. Do not include unpublished manuscripts, access tokens, or patient data.

The skill reads a figure id from the local catalog and writes HTML or SVG on the machine where it runs. It does not phone home, and it does not ask for an API key. Treat exported HTML as local content: open it only from a file you generated.

## Supported versions

| Version | Supported |
| --- | --- |
| 2.0.x | yes |
| older | no |
