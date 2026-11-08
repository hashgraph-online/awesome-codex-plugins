# Desktop Platform Checklist

Load this file only when the PRD's decided platforms include desktop. It owns the items that fill the platform requirements block and its release gate table for macOS, Windows, and Linux desktop builds: distribution channel, signing and notarization, auto-update, and desktop integration.

## Contents

- How to use
- Distribution channel
- Signing and notarization
- Auto-update
- Desktop integration
- Release gate rule
- Sources

## How to use

- Copy the items into the platform requirements block and answer each one in the PRD's own words. Do not paste this table into the PRD.
- The grade decides what the release gate table must contain: every `[M]` and `[M-조건]` item gets a conclusion (applies / not applicable with a reason / `[확인 필요]`). A `[G]` item is written only when it is relevant to the product.
- `[M-조건]` items carry their condition in the sentence. When the condition is false, write "not applicable" and the reason in the gate table instead of deleting the row.
- An item that cannot be verified as written is not a requirement. "Follow the store guidelines" is forbidden; name the clause and the observable state.
- Every numeric target in the PRD carries a threshold, a measurement method, and a percentile. "Fast enough" is not a target.
- The check date is 2026-11-07 for every row. Store policy values and their dates change; re-check each row every quarter and update the date.

## Distribution channel

Decide the channel before the rest of this file; the signing and update items depend on it.

| Id | Grade | What the PRD must settle | Source | Checked |
|---|---|---|---|---|
| D1 | `[M]` | macOS channel: Mac App Store or Developer ID direct distribution. Write the choice, the account owner, and what the choice forces for signing and updates. | https://developer.apple.com/documentation/security/notarizing-macos-software-before-distribution | 2026-11-07 |
| D2 | `[M]` | Windows channel: Microsoft Store or a direct installer. Write the choice, the account owner, and which installer formats are published. | https://v2.tauri.app/distribute/windows-installer/ | 2026-11-07 |
| D3 | `[M]` | Linux channel: Flathub or another package source. Write the choice, who publishes the package, and how the package is updated. | https://docs.flathub.org/docs/for-app-authors/requirements | 2026-11-07 |
| D4 | `[M-조건]` | Condition: macOS with Developer ID distribution. Every build is notarized before distribution. Record who holds the notary credentials and whether the ticket is stapled as a release step. | https://developer.apple.com/documentation/security/notarizing-macos-software-before-distribution | 2026-11-07 |
| D5 | `[M-조건]` | Condition: macOS through the Mac App Store. D4 is not applicable; write that reason in the gate table and record the store submission obligations instead. | https://developer.apple.com/documentation/security/notarizing-macos-software-before-distribution | 2026-11-07 |
| D6 | `[M-조건]` | Condition: Linux through Flathub. Submit with static permissions kept to an absolute minimum; list each requested permission and the feature that needs it. | https://docs.flathub.org/docs/for-app-authors/requirements | 2026-11-07 |

## Signing and notarization

| Id | Grade | What the PRD must settle | Source | Checked |
|---|---|---|---|---|
| D7 | `[M]` | Windows: record the certificate owner and the signing identity, and use SHA256 as the digest algorithm. SignTool states the recommendation. | https://learn.microsoft.com/en-us/windows/win32/seccrypto/signtool | 2026-11-07 |
| D8 | `[M]` | Windows: state which artifacts are signed (installer, executable, update package) and how a signature failure is detected before release. | https://learn.microsoft.com/en-us/windows/win32/seccrypto/signtool | 2026-11-07 |
| D9 | `[G]` | macOS: record the minimum supported macOS version and the architectures shipped (Intel, Apple silicon, or both), and whether each architecture is notarized and stapled. | https://developer.apple.com/documentation/security/notarizing-macos-software-before-distribution | 2026-11-07 |

## Auto-update

| Id | Grade | What the PRD must settle | Source | Checked |
|---|---|---|---|---|
| D10 | `[G]` | Decide whether the app updates itself and over which channel, and name the owner of the update feed and the release cadence. | https://www.electronjs.org/docs/latest/api/auto-updater | 2026-11-07 |
| D11 | `[G]` | State the update mechanism per OS. Electron's built-in autoUpdater has no built-in support on Linux, so a Linux build either ships updates through its package source or needs a different mechanism. | https://www.electronjs.org/docs/latest/api/auto-updater | 2026-11-07 |
| D12 | `[M-조건]` | Condition: the Tauri updater plugin is used. Update signature verification cannot be disabled. Record who holds the update signing key, where it is stored, and how it is rotated. | https://v2.tauri.app/plugin/updater/ | 2026-11-07 |
| D13 | `[G]` | Rollout rule. This is a design recommendation for the PRD, with no store or vendor rule behind it: the PRD states its own update check cadence, wave share, and the metric that halts a wave, and the numbers are the PRD's choice rather than a quoted limit. The distribution page linked here covers channels and installers only and states no rollout rule. | https://v2.tauri.app/distribute/ | 2026-11-07 |
| D14 | `[G]` | State what the user sees when an update fails to download or install, and who can stop a rollout. | https://www.electronjs.org/docs/latest/api/auto-updater | 2026-11-07 |

## Desktop integration

| Id | Grade | What the PRD must settle | Source | Checked |
|---|---|---|---|---|
| D15 | `[G]` | Tray: decide whether the app has a tray icon, what its menu contains, and what closing the main window does (quit, or stay resident). | https://www.electronjs.org/docs/latest/tutorial/tray | 2026-11-07 |
| D16 | `[G]` | Protocol handler: decide the URL scheme, what each link does when the app is closed, and what the app shows for an unknown or malformed link. | https://www.electronjs.org/docs/latest/tutorial/launch-app-from-url-in-another-app | 2026-11-07 |
| D17 | `[G]` | Single instance: decide whether a second launch focuses the existing window, opens a new window, or is refused, and whether a protocol link reaches the running instance. | https://www.electronjs.org/docs/latest/tutorial/launch-app-from-url-in-another-app | 2026-11-07 |

## Release gate rule

Every `[M]` and `[M-조건]` row above appears in the PRD release gate table with one conclusion:

| Conclusion | When to write it |
|---|---|
| applies | The obligation holds and the PRD states the observable state that satisfies it. |
| not applicable + reason | The condition is false (another channel, another OS), and the reason names the decision. |
| `[확인 필요]` | The answer is not in the repository or the conversation; name who answers it. |

## Sources

> Checked 2026-11-07.

| Claim | Source |
|---|---|
| Notarization is required for Developer ID distribution | [Notarizing macOS software before distribution](https://developer.apple.com/documentation/security/notarizing-macos-software-before-distribution) - "all software built after June 1, 2019, and distributed with Developer ID must be notarized" |
| Windows signing digest recommendation | [SignTool](https://learn.microsoft.com/en-us/windows/win32/seccrypto/signtool) - "We recommend SHA256." |
| Electron has no Linux auto-update support | [Electron autoUpdater](https://www.electronjs.org/docs/latest/api/auto-updater) - "There is no built-in support for auto-updater on Linux" |
| Tauri update signatures are mandatory when the plugin is used | [Tauri updater plugin](https://v2.tauri.app/plugin/updater/) - "This cannot be disabled." |
| Desktop distribution channels and installers | [Tauri distribute](https://v2.tauri.app/distribute/) and [Windows installer](https://v2.tauri.app/distribute/windows-installer/) |
| Flathub permission budget | [Flathub app requirements](https://docs.flathub.org/docs/for-app-authors/requirements) - "Static permissions must be kept to an absolute minimum." |
| Tray menu behavior | [Electron tray](https://www.electronjs.org/docs/latest/tutorial/tray) |
| Protocol handling and single instance | [Launch app from URL in another app](https://www.electronjs.org/docs/latest/tutorial/launch-app-from-url-in-another-app) |

### Evidence grade

`LOCAL` - the id scheme, the grades, and the release gate rule are this package's design assembled from the sources above. The store and vendor sentences are quoted verbatim from the pages listed. Store policy values and dates change, so the quotes and the 2026-11-07 check date must be re-verified every quarter before a release gate is signed off.
