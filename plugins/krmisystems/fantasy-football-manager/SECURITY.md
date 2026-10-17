# Security reporting

Report security concerns against the current source or the latest published package.
Include the affected version, the expected behavior, and reproduction steps with fictional data.
The source release candidate and the published package can have different capabilities.
See [validation status](https://github.com/krmisystems/fantasy-football-manager/blob/main/docs/VALIDATION.md).

Use the repository's private vulnerability reporting option when it is available.
If that option is unavailable, open an [issue](https://github.com/krmisystems/fantasy-football-manager/issues)
that requests a private reporting channel. Do not include vulnerability details in that request.
Do not publish ESPN cookies, credentials, private team records, or server addresses.

The local MCP servers can read private fantasy data and submit authorized ESPN actions.
Keep credential files outside the checkout. Restrict access to their operating-system account.
Use saved automation limits and review exact proposals before approving consequential actions.
The dashboard should listen on localhost unless an authenticated gateway protects access.
See the [privacy guide](https://github.com/krmisystems/fantasy-football-manager/blob/main/docs/PRIVACY.md).

Automated scanner results describe the checks that ran. They do not prove that the project is free of vulnerabilities.
Live-provider validation and unattended operation have separate evidence limits in the validation guide.
