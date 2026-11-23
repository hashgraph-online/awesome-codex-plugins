# Computer administration workspace templates

Use these with the [workspace recipe](../computer_setup_recipe.md). Each linked document contains fenced initial content for named destinations, not an executable generator. Keep the source-relative structure when reading the bundled offline copies. Create only applicable records with real content, replace every placeholder with confirmed facts or explicit unknown/pending state, and preserve existing files and decisions.

The copyright holder grants template-specific permission to use/adapt these templates without retaining copyright/license notices or adding a license file in the resulting workspace; see [LICENSE](https://github.com/pallgeuer/la-dev-codex-plugins/blob/main/LICENSE). This is not a licensing requirement for a private workspace. Record source URL, revision/retrieval date and local deviations for operational traceability; that recordkeeping rule is not a license condition. All unrelated material retains its existing license.

| Template group                                     | Workspace destinations / applicability                               |
|----------------------------------------------------|----------------------------------------------------------------------|
| [Instructions](computer_workspace/instructions.md) | AGENTS.md                                                            |
| [Navigation](computer_workspace/navigation.md)     | README.md and paths.md                                               |
| [System](computer_workspace/system.md)             | system overview, workspace and index                                 |
| [Software](computer_workspace/software.md)         | software index and actual application topics                         |
| [Automation](computer_workspace/automation.md)     | automation context; add helper notes only for actual deployments     |
| [History](computer_workspace/history.md)           | history index, populated year index and actual work note             |
| [Tasks](computer_workspace/tasks.md)               | task index and actual pending tasks                                  |
| [Artifacts](computer_workspace/artifacts.md)       | local/README.md, .gitignore and task-bundle README when needed       |
| [Installation](computer_workspace/installation.md) | installation.md only when a new regular file was selected            |
| [Maintenance](computer_workspace/maintenance.md)   | repo Perform action/config when Toolkit is installed and available   |
| [Maintainer](computer_workspace/maintainer.md)     | upstream/ and AGENTS extension ONLY after explicit maintainer opt-in |

For an external installation document, create a tracked absolute symlink instead of copying the installation template. Unavailable targets stay explicitly pending; do not create a competing record. The maintenance and maintainer groups are independent: Toolkit availability does not imply maintainer opt-in. Preserve existing repository config/action definitions and resolve conflicts instead of overwriting them.
