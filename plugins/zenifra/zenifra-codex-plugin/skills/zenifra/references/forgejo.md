# Forgejo source deployments

Use this workflow only for a Forgejo repository source. Keep GitHub projects on the existing GitHub commands in `SKILL.md`.

## Check the effective target and support

For normal end-user use, Forgejo source operations require a published `@zenifra/cli` version 0.5.0 or later. Installing this plugin does not install or update the CLI. Check the version and help of the CLI that will actually run before using a command. If it does not expose the operation, report that limitation; do not substitute an undocumented API or private endpoint. In a development workspace the user explicitly authorized, a local CLI build is appropriate when its actual version and help expose the operation.

Before reading catalogs or mutating, inspect the effective profile, API, authentication mode, and organization with `zenifra whoami --json`. If the user has selected another saved profile for this target, use `zenifra profile list`, then `zenifra profile use <name>`, and re-read `whoami`. Do not pass `--profile` to Git, project-source, or deploy commands. Environment overrides can change the effective API or authentication; never print their values or inspect the local profile file.

Read the supported providers and their current capabilities, available build runtimes, and saved connections:

```bash
zenifra git providers --json
zenifra git runtimes --json
zenifra git connections --json
```

Proceed only when Forgejo is available and the reported capabilities cover the requested source and deployment mode. A provider name alone does not prove that the required capability is enabled. Use the runtime and version reported by the CLI, not a guessed value. Confirm the selected organization and current plan capabilities before creating a project or changing a trigger.

## Connect Forgejo and grant repository access

The owner must create, rotate, or revoke Forgejo credentials through the Zenifra Console using the owner's interactive account session. The Zenifra CLI does not perform those credential operations. An organization API key or a delegated session cannot replace the required owner session. Reuse a connection that already exists when it is the intended one; otherwise direct the owner to connect Forgejo in the Console, then re-read `zenifra git connections --json` and select a connection whose status is `active`. Do not ask the user to repeat a general authorization they have already given; ask only for a missing connection choice or repository scope.

Use the least permission the selected mode requires, scoped to only the named repository or repositories:

- A manual build needs a token with `read:repository`.
- Automatic branch, tag, or release triggers need `write:repository` and an account that can administer repository hooks. `write:repository` alone does not grant hook administration.

For Forgejo 16, a token set to **Specific repositories** cannot perform repository administration such as managing hooks, even when the token owner can administer them. For automated triggers, use a dedicated account limited to the repositories it needs, grant it hook administration on those repositories, and create an **All (public, private, and limited)** token with `write:repository`. Do not use a site administrator account. For a manual read-only connection, **Specific repositories** with `read:repository` can be scoped to the selected repository. The selected repository must be included in the connection's allowed repositories.

Use an HTTPS Forgejo base URL with a valid, trusted certificate that Zenifra can reach. Verify the connection status through the supported product surface. For automatic deployments, confirm before setup that Forgejo can reach the HTTPS webhook address supplied by Zenifra. The source attachment registers the hook; an existing hook is not a prerequisite for project creation. After attachment and a matching event, inspect the hook's delivery history in Forgejo and follow the resulting build. A successful API connection from Zenifra does not prove webhook delivery. If HTTPS reachability or the certificate is unavailable, stop and report the connection blocker.

Never ask for a personal access token in chat. Never place it in a CLI argument, project config, environment file, shell history, logs, or examples. Do not read a local profile file or try to extract a Console or browser session. The token is handled only by the supported owner connection flow; it is distinct from `ZENIFRA_API_KEY`.

## Select an explicit repository and branch

The repository resolver accepts a path the user selected; it does not discover or list repositories. Resolve that exact path with the chosen connection:

```bash
zenifra git repositories resolve --connection <connection-id> --path <owner/repository> --json
zenifra git branches --connection <connection-id> --repository <opaque-repository-id> --json
```

The connections response returns a connection object with an `id`; the repository resolver returns a repository object with an `id`. In project config, set `source.connection_id` from the selected `connection.id` and `source.repository_id` from the resolved repository `id`. The branch command also expects that opaque repository ID. Do not substitute a guessed ID or pass the owner/repository path where an ID is required. Select an existing branch the user named or chose. If the request is to create a new repository, make that intent and the owner, name, and visibility explicit; the Zenifra CLI only resolves existing repositories, so the repository owner must first create it through Forgejo.

## Create a project from Forgejo

The interactive project wizard currently covers OCI and GitHub sources. Use a config file for a Forgejo source, and use only fields documented by the installed CLI. The repository includes a complete HTTP example at [`examples/http-forgejo-project.json`](../../../examples/http-forgejo-project.json). It illustrates a public HTTP app using branch-triggered builds; its IDs are placeholders and its runtime, commands, port, instance count, storage, environment, and network policy are sample values. Replace them with values chosen for this application. In particular, do not inherit public exposure, the open ingress rule, plan, or payment mode unless the user selected them:

```bash
zenifra create project --name <project-name> --plan <user-selected-plan> --payment-mode <hourly|monthly|yearly> --config @examples/http-forgejo-project.json --idempotency-key <idempotency-key>
```

Use the IDs from the connection and repository read results in `source.connection_id` and `source.repository_id` in that file. Check `zenifra git runtimes --json` and current plan capabilities, and update the example to match them. For manual mode, set `source.auto_deploy` to `false` and omit `source.version_deploy`. For tag or release mode, also set `source.auto_deploy` to `false` and include the matching `source.version_deploy` event. For example, replace the `source` block in the complete file with this release configuration when the initial project should also use Release mode:

```json
{
  "connection_id": "<selected connection.id>",
  "repository_id": "<resolved repository.id>",
  "branch": "main",
  "auto_deploy": false,
  "version_deploy": {
    "enabled": true,
    "event": "release",
    "tag_pattern": "v*",
    "include_prereleases": false
  }
}
```

The example is intentionally complete so the CLI does not have to infer project fields. Use the runtime and version reported by `zenifra git runtimes --json`, the current plan catalog and `capabilities.*`, and the installed command help. The config must not contain the Forgejo token. Treat application environment secrets separately and use the supported masked secret flow.

Choose an existing connection and repository or a new repository explicitly. Creating a Zenifra project and its initial build can incur cost and affect production behavior, so use the user's stated scope and values. Do not ask for broad permission again when it was already given; clarify only values that are missing or ambiguous, including plan/payment, repository, branch, runtime/build settings, exposure, and any cost-affecting settings. The initial build created with the project is separate from later automatic branch/tag/release triggers.

## Read or configure Forgejo deployment triggers

Read the project source first:

```bash
zenifra project source --project <project-id> --json
```

The generic source read is observational; it does not convert or migrate a project to a new source. A GitHub source may be returned with `provider_id: "github"`; the generic view does not prove that the project was migrated to a provider-neutral source. Use `zenifra project source deploy-settings set` only when the returned source explicitly identifies `provider_id` as `forgejo`. For GitHub, keep using `zenifra project github` and `zenifra project github deploy-settings set`.

For a confirmed Forgejo source, read its available branches and set one deployment mode:

```bash
zenifra project source branches --project <project-id> --json
zenifra project source deploy-settings set --project <project-id> --mode <manual|branch|tag|release> [--tag-pattern <pattern>] [--include-prereleases <true|false>] --json
zenifra project source deploy-settings set --project <project-id> --mode release --tag-pattern 'v*' --include-prereleases false --json
```

- `manual` sets `source.auto_deploy` to `false` and omits `source.version_deploy`; a manual deploy remains available.
- `branch` sets `source.auto_deploy` to `true` and omits `source.version_deploy`; pushes to the configured branch start a build.
- `tag` sets `source.auto_deploy` to `false` and enables `source.version_deploy` for the `tag` event.
- `release` sets `source.auto_deploy` to `false` and enables `source.version_deploy` for the `release` event. The published release must reference a matching tag; drafts do not trigger builds. Prereleases are excluded by default and require an explicit opt-in.

The modes are mutually exclusive: never enable `source.auto_deploy` and `source.version_deploy.enabled` together. For project creation, the source config selects the mode atomically; a project does not have to be created in Branch mode and changed to Release afterward. The first project build still starts from the initial branch even when later automatic deployment is disabled.

Use `--tag-pattern` only for `tag` and `release`, with the pattern the user chose. Matching is case-sensitive against the full tag name; `*` matches any sequence and `?` one character. Use `--include-prereleases true` only for `release` and only with explicit user intent. For Tag mode, push the tag to the Forgejo remote; a local-only tag does not trigger a build. For Release mode, publish the Forgejo release associated with the matching pushed tag; saving a draft does not trigger a build. Avoid editing this project's source or build settings in parallel while changing its trigger. Changing a mode changes future triggers; it does not prove that a build or deployment succeeded. Read the project source settings again after the mutation. Preserve the user's prior authorization for the deployment task, and clarify only an unspecified or ambiguous mode/pattern or a separately gated prerelease choice.

## Follow the build to the application

For a manual deploy, select a branch or provide the exact full commit SHA:

```bash
zenifra deploy --project <project-id> --branch <branch>
zenifra deploy --project <project-id> --commit-sha <full-commit-sha>
zenifra deploy watch --project <project-id> --build <build-id>
zenifra builds logs --project <project-id> --build <build-id> --follow
```

Use the returned `build_id` with the watch/log commands. Follow it to a terminal state, then compare the build's reported commit SHA with the requested full SHA. To resolve an annotated tag to its commit in a local checkout, use `git rev-parse 'v1.0.0^{commit}'`. A branch or release tag may resolve to a different commit than expected; preserve full SHAs exactly and verify the resolved commit before claiming that revision was deployed. A successful build alone does not establish that deployment completed or that the application is ready. Read the final project status and URL, then verify the product health or application response expected for its exposure.

## Boundaries

This documented Forgejo flow does not provide repository creation, GitLab source setup, SSH clone URLs, Git LFS, submodules, or Forgejo-native pull-request previews. Do not promise those capabilities unless the current provider catalog and published CLI documentation explicitly expose them. If a requested capability is absent, report the limitation rather than using private APIs or changing the repository through an undocumented route.
