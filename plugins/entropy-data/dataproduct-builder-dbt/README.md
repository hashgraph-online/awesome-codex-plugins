# dataproduct-builder-dbt

Skills for your favorite coding agent that helps you implement data products with [dbt](https://www.getdbt.com/), compliant to your organization's conventions, and fully integrated with [Entropy Data](https://entropy-data.com).

<img width="1076" height="627" alt="Screenshot 2026-05-16 at 10 59 52" src="https://github.com/user-attachments/assets/026899ee-2a67-4b02-86e0-0e372be9b648" />

It also supports a contract-driven approach: specify your requirements as a [data contract](https://datacontract.com), and the builder implements the data product in minutes.

## Skills

The plugin ships seven skills:

- **[dataproduct-bootstrap](https://github.com/entropy-data/dataproduct-builder-dbt/blob/main/skills/dataproduct-bootstrap/SKILL.md)** scaffolds a new dbt data product from scratch: `dbt_project.yml`, model layout, README, `profiles.yml.example`, and more.
- **[dataproduct-implement](https://github.com/entropy-data/dataproduct-builder-dbt/blob/main/skills/dataproduct-implement/SKILL.md)** analyzes the data product input and output data contract, and implements the dbt models.
- **[dataproduct-exampledata](https://github.com/entropy-data/dataproduct-builder-dbt/blob/main/skills/dataproduct-exampledata/SKILL.md)** extracts sample rows, drops PII columns flagged in the contract (and obvious name-based PII), and uploads the scrubbed sample to Entropy Data. 
- **[datacontract-edit](https://github.com/entropy-data/dataproduct-builder-dbt/blob/main/skills/datacontract-edit/SKILL.md)** edits an output-port `models/output_ports/v<N>/*.odcs.yaml` using natural language.
- **[datacontract-test](https://github.com/entropy-data/dataproduct-builder-dbt/blob/main/skills/datacontract-test/SKILL.md)** runs `datacontract test` to verify the live data still matches the schema and quality rules. 
- **[entropy-data-sync](https://github.com/entropy-data/dataproduct-builder-dbt/blob/main/skills/entropy-data-sync/SKILL.md)** integrate existing dbt project to the Entropy Data reference layout, set up GitHub Actions workflow, and synchronize all metadata.
- **[entropy-data-teams](https://github.com/entropy-data/dataproduct-builder-dbt/blob/main/skills/entropy-data-teams/SKILL.md)** lists the teams configured in Entropy Data so the user can pick an owner.

## Install

The skills are plain markdown, any coding agent that can read instruction files can run them. 

For major coding agents, those can be installed as a plugin:

### Claude Code

Inside your terminal:

```
/plugin marketplace add https://github.com/entropy-data/dataproduct-builder-dbt
/plugin install dataproduct-builder-dbt@dataproduct-builder-dbt
```

### OpenAI Codex

Add the marketplace from the terminal:

```
codex plugin marketplace add https://github.com/entropy-data/dataproduct-builder-dbt
```

Then open Codex, run `/plugins`, and pick `dataproduct-builder-dbt` from the directory.

### GitHub Copilot CLI

Inside your terminal:

```
/plugin marketplace add https://github.com/entropy-data/dataproduct-builder-dbt
/plugin install dataproduct-builder-dbt@dataproduct-builder-dbt
```
### Other agents (Cursor, Aider, etc.)

Any agent that reads `AGENTS.md` picks up the routing manifest. 
Alternatively, copy the `skills` to the directory that your coding agent expects.


### Connect

The skills authenticate against Entropy Data through a connection registered with the [entropy-data CLI](https://github.com/entropy-data/entropy-data-cli) (requires [uv](https://docs.astral.sh/uv/)).

Create a user-scoped key in the Entropy Data web UI (**Organization Settings → API Keys → Create new API key**, scope `User (personal token)`) and add the connection:

```
uv tool install --upgrade entropy-data
entropy-data connection add default --api-key <your-api-key> --host <your-entropy-data-host>
```

For CI workflows, add a connection with a team-scoped or organization-scoped API key.


## Use

Ask the agent:

> Implement the data product *url or id or new name*.

Or:

> Add the property *name* to the data contract and find data products that we could use as input ports. Request access and implement the dbt pipeline.

## Customization

Organizations with their own data-product stack and naming conventions are encouraged to **fork or copy this repository** and adapt it to their environment.

Common extension points:

- **Templates** under [`skills/dataproduct-bootstrap/templates/`](skills/dataproduct-bootstrap/templates/) and [`skills/entropy-data-sync/templates/`](skills/entropy-data-sync/templates/) ship the ODPS, ODCS, OpenLineage transport, GitHub Actions workflow, and dbt project skeleton that the bootstrap and sync skills install. Replace any of them to match your conventions (e.g. swap GitHub Actions for Airflow, change the model layer naming, embed company-specific tags).
- **Skills**: add your own `skills/<name>/SKILL.md` for stack-specific flows: specific skills for your data platform, internal data-quality checks, governance approvals, downstream sync to your data catalog, etc. Update `AGENTS.md` and `.github/copilot-instructions.md` so the routing tables surface them.
- **Hooks**: extend [`hooks/hooks.json`](hooks/hooks.json) with additional `PostToolUse` validators (e.g. an internal lint on `models/**/*.sql`, or a check that team names match your IdP).
- **Subagents**: add subagents under `agents/` for specialist roles (e.g. a PII scanner tuned to your classification taxonomy, a contract-review specialist for your terms-of-use boilerplate).

After customizing, rename the plugin in [`.claude-plugin/plugin.json`](.claude-plugin/plugin.json) and [`.codex-plugin/plugin.json`](.codex-plugin/plugin.json), then publish under your own GitHub organization or GitLab repository. 
Update the installation instructions and usage instructions in Entropy Data.

If a change you've made is broadly useful, [open an issue or PR upstream](https://github.com/entropy-data/dataproduct-builder-dbt/issues), generic improvements are very welcome.

## License

MIT
