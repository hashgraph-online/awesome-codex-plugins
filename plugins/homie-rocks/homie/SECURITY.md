# Security

Please report a vulnerability privately, never in a public issue or pull request:

- **GitHub private vulnerability reporting:** on this repository's **Security** tab,
  choose **Report a vulnerability**; or
- **email security@homie.rocks**.

**In scope:** the Homie plugin and both marketplace files in this repository, and
`@homie-rocks/studio` (the `homie-studio` CLI, the studio site Worker, the netplay relay
and game helper, and the Gem Rush starter).

The hosted services at homie.rocks (the directory and the MCP server the plugin
connects to) are not in this repository. Report problems with them the same way.

A useful report has:

- the version (`packages/studio/package.json`, or the plugin's `plugin.json`);
- what you did, what happened, and what you expected;
- the shortest reproduction you can make, with no real key, token or password in it.

Please give us a chance to ship a fix before you tell anyone else. Fixes go into the
latest release of each package.
