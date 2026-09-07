# CodexQuotaTitle

CodexQuotaTitle is a free, open-source Windows plugin for Codex Desktop. It automatically displays your remaining Codex quota in the title of the correctly correlated Codex window while preserving the title managed by Codex.

For example:

```text
Codex - Project | W 89% • 24/08 18:00
```

## Install in Codex Desktop

1. Open **Plugins** in Codex Desktop, then choose **Add Marketplace**.
2. Select **GitHub URL**.
3. Enter `https://github.com/nokisenpai/CodexQuotaTitle`.
4. Install **CodexQuotaTitle** from the marketplace and approve the requested plugin access.
5. Create or reopen a Codex Desktop task. The bundled MCP starts the profile-scoped helper automatically when the task/session is opened or resumed.

### Development installation

Development uses the local marketplace already configured on the developer machine. It is intentionally separate from the public marketplace above. Build the package locally with:

```powershell
.\scripts\publish-dev-plugin.ps1
```

## Automatic quota updates

The helper starts automatically when a Codex Desktop task/session is opened or resumed. It uses Codex App Server rate-limit updates and periodic resynchronization when App Server is available. If App Server cannot start or later becomes unavailable, the helper falls back to the newest profile-scoped quota snapshot from Codex session rollouts without discarding a newer App Server value. It updates a title only when it can correlate exactly one visible Codex Desktop window to the Desktop host process. If correlation is ambiguous, the title is left unchanged.

## Profile behavior

CodexQuotaTitle resolves the active profile from `CODEX_HOME`. When Codex Desktop does not pass that variable, it uses the current user's default `.codex` directory only if that directory exists. Each resolved profile has a stable, hashed `ProfileIdentity` and exactly one helper process, so separate Codex profiles keep separate settings and runtime state.

## Title template

The default template is:

```text
%base_title% | W %week_percent_remaining% • %week_reset_date%
```

`%base_title%` is the original Codex window title. This placeholder is optional; when omitted, the template becomes the complete visible window title. It can appear at most once. The renderer supports these quota placeholders:

- `%primary_percent_used%`, `%primary_percent_remaining%`, `%primary_reset_date%`
- `%secondary_percent_used%`, `%secondary_percent_remaining%`, `%secondary_reset_date%`
- `%5h_percent_used%`, `%5h_percent_remaining%`, `%5h_reset_date%`, `%5h_reset_relative%`
- `%week_percent_used%`, `%week_percent_remaining%`, `%week_reset_date%`, `%week_reset_relative%`

Missing quota values render as `—`. Unknown placeholders are retained literally so they remain visible for correction.

Examples:

```text
W %week_percent_remaining% | %base_title%
%base_title% | 5h %5h_percent_remaining% (%5h_reset_relative%)
Codex1 • %week_percent_remaining% • %week_reset_date%
```

## Configuration

Settings are profile-scoped and stored at:

```text
%LOCALAPPDATA%\CodexQuotaTitle\<ProfileIdentity>\settings.json
```

You can either ask Codex to **“Open my CodexQuotaTitle settings.”** (or equivalent), or open the file manually at the path above. The bundled `codex_quota_title_get_settings` MCP tool returns the exact resolved path for the current profile.

The file is created with these supported keys:

```json
{
  "template": "%base_title% | W %week_percent_remaining% • %week_reset_date%",
  "dateFormat": "dd/MM HH:mm",
  "enabled": true
}
```

When it is first created, `settings.json` includes a commented list of the supported placeholders. You can update the template through the bundled `codex_quota_title_set_template` MCP tool or by editing `settings.json`. The helper watches the file and applies valid changes without restarting.

## App Server and privacy

CodexQuotaTitle requires no API key. It launches the locally installed `codex app-server` for the active Codex profile and communicates with it through standard input/output to read the account summary and rate limits.

The plugin contains no custom telemetry, analytics SDK, HTTP client, or remote upload. Its diagnostics redact token-, cookie-, API-key-, and secret-like values. Codex App Server itself remains part of the Codex product and follows its own configuration and policies.

## Requirements and known limitations

- Windows and Codex Desktop are required; macOS and Linux are not supported.
- The plugin updates only one visible, unambiguously correlated Codex Desktop window. It does nothing when there are zero or multiple candidate windows.
- Codex Desktop must allow the bundled MCP. A usable Codex App Server provides the freshest values; session rollout snapshots are used as a fallback when it is unavailable.
- The rendered quota text depends on the quotas returned by the current Codex account; unavailable values display as `—`.
- Settings are local to the Windows user and the resolved Codex profile.

## Development

Prerequisites: Windows and the .NET 8 SDK.

```powershell
dotnet restore CodexQuotaTitle.sln
dotnet build CodexQuotaTitle.sln --configuration Release --no-restore
dotnet run --project tests\CodexQuotaTitle.Tests\CodexQuotaTitle.Tests.csproj --configuration Release --no-build
```

See [CONTRIBUTING.md](CONTRIBUTING.md) for contribution guidance.

## Support the project

CodexQuotaTitle is free and open source. If it is useful to you, you can support its development on [Ko-fi](https://ko-fi.com/nokisenpai).
