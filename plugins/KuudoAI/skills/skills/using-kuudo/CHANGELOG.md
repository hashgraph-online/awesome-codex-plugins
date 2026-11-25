# Changelog

## [0.5.0] - 2026-11-25

From a client session on 2026-11-25 with the plugin and the Kuudo Amazon Ads
server connected.

### Added

- "Already connected": when the tools are present and the user only asks to
  connect or to see what they can reach, confirm it read-only (identities,
  then the server's own listing tool) and ask which account or marketplace to
  work in. On Selling Partner the check selects the identity and a marketplace
  in the same `execute` block as the read, because that server keeps a
  selection for one block and routes to North America by default. The setup
  steps are now under "Not connected".
- Duplicates: when a task is covered twice (a skill under several prefixes, an
  older upload under another name, a second Amazon MCP server), use the
  `kuudo-skills:` skill and Kuudo's servers unless the user names another, and
  mention the duplicates once.
- The `list_identities` warning carries the measured counts: 7 profiles in the
  identity listing against 16 in `ac_listProfiles`. The agent in that session
  had shown the 7 as the full list.
- "Hosts" covers chat in the Claude Desktop app, claude.ai, and the mobile
  apps, where no hook runs, and Cowork and Gemini CLI.
- Downloads: Kuudo's `execute` block can't fetch URLs, so a signed link is
  downloaded in the client's own environment, and a link that arrives
  HTML-escaped needs `&amp;` turned back into `&`. One line here covers every
  skill that downloads a report or result.

### Changed

- The skill loaded twice in that session: once from the session hook and again
  from a Skill call. The top of the skill and the hook's preamble now say it
  is already loaded. The host notes moved from `references/claude-code.md` and
  `references/codex.md` into "Hosts", because the hook injects this file
  without its directory, so the injected text could not lead to a reference.

### Removed

- The "1% chance" block, the "Common rationalizations" table, and the examples
  list. They cost tokens on every Amazon request and did not change routing.
- The exact `Using [skill] to [purpose].` announcement. The agent did not
  print it in that session. The skill now asks only that the user be told
  which skill is in use.

## [0.4.0] - 2026-11-21

### Added

- Connecting Kuudo: when Kuudo's tools are missing or the user asks how to
  connect, give the managed MCP endpoints (`ads.kuudo.com/mcp`,
  `sp.kuudo.com/mcp`), the per-client connector steps, Kuudo sign-in, and the
  separate Amazon authorization in Kuudo. Replaces the removed
  `connect-to-kuudo` skill for this case. The description now covers
  connection questions.

## [0.3.0] - 2026-11-02

### Added

- "Identities": identities come from the login, each identity is for one
  provider, and each server shows the one or more for its provider. Resolve
  scope from the top down, ask when there are several, and name the identity
  searched in counts and "not found" replies.

## [0.2.1] - 2026-10-28

### Added

- `metadata.display-name` "Using Kuudo": a human-readable label for catalogs
  and skill pickers. Instructions and triggering are unchanged.

## [0.2.0] - 2026-10-18

### Changed

- Preserve stricter repository controls, including production-write bans and additional organizational approvals; skill safety rules are minimum safeguards.
- Limit repository overrides to workflow and presentation defaults; preserve skill safety boundaries for approvals, trusted targets, and unattended writes.
- Explicitly preserve later-message confirmations, typed shipment confirmations, separate DSP activation approval, and the exact seller-authored messaging exception.
