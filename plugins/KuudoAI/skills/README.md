![Kuudo Amazon Skills](kuudo-skills.png)

# Amazon Skills for Advertising, Sellers, and Vendors

**Give your AI agent the know-how to run your Amazon business.**

Kuudo is a collection of skills for Amazon advertising, seller and vendor operations. It gives your agent the workflows, reference material, and calculation tools to audit campaigns, improve listings, understand profit, and turn commerce data into clear next steps.

Bring the question. Kuudo helps your agent do the work.

> “Find wasted spend in my Sponsored Products search terms.”
>
> “Review this listing and show me what to improve.”
>
> “What price does this product need to be profitable?”

[Get started](#get-started) · [Explore the skills](#what-you-can-do) · [How it works](#how-it-works) · [Create or request a skill](#creating-skills)

## How it works

Install Kuudo in your AI client, then describe what you want to accomplish. Your agent selects the relevant skill and follows its workflow: gathering the right inputs, checking the data, and working toward a useful result.

For a campaign audit, that means examining campaign structure, budget utilization, and inactive campaigns, then producing a portfolio health report. For profitability, it means working through costs, fees, and advertising to calculate margins and break-even prices. Each skill brings a specific method to the task, so you don't have to explain the process every time.

Some skills work with uploaded reports or figures you provide. Live account analysis and changes need the appropriate Amazon connection in your client. See [Connect your Amazon tools](#connect-your-amazon-tools).

## What you can do

| Your goal | Skills to get you there |
| --- | --- |
| Find advertising waste and opportunities | [Sponsored Products campaign audits](skills/amazon-ads-sp-campaign-auditor/), [search term analysis](skills/amazon-ads-sp-search-term-explorer/), [Sponsored Brands reviews](skills/amazon-ads-sb-performance-review/) |
| Keep spend on plan | [Budget pacing and daily budget proposals](skills/amazon-ads-budget-pacing/) |
| Get the right advertising data | [Account and marketplace selection](skills/amazon-ads-accounts/), [Amazon Ads reporting](skills/amazon-ads-reporting/) |
| Go deeper on audiences and attribution | [Amazon Marketing Cloud analysis, SQL, and audiences](skills/amazon-ads-marketing-cloud/) |
| Build campaigns and creative | [DSP Performance+ and Brand+ setup](skills/amazon-ads-create-dsp-campaign/), [Review Requests campaigns for new-product reviews](skills/amazon-ads-review-requests/), [ad images and copy](skills/amazon-ads-creative-assets/) |
| Improve your product pages | [Listing and A+ Content optimization](skills/amazon-sp-listing-optimizer/), [listing compliance checks](skills/amazon-sp-listing-compliance/), [product image creation and review](skills/amazon-product-image/) |
| Understand what drives sales and returns | [Sales and traffic analysis](skills/amazon-sp-sales-traffic-analyzer/), [refund and return monitoring](skills/amazon-sp-refund-return-monitor/) |
| Protect your margins | [Profitability and break-even calculations](skills/amazon-profitability-calculator/), [repricing strategy](skills/amazon-sp-repricing/) |
| Keep FBA stock flowing | [Stockout risk and restock timing](skills/amazon-sp-stockout-prevention/), [FBA inbound shipments](skills/amazon-sp-fba-inbound/) |
| Keep buyers informed | [Buyer messaging for delays, confirmations, invoices, and warranties](skills/amazon-sp-messaging-api/) |

Browse the full collection in [`skills/`](skills/). Every skill's instructions are available to read before you install it.

## Get started

Install the whole suite in **Claude Code, Codex, or Gemini CLI**, or choose **one portable skill** for another compatible client. Use one installation mode per client to avoid duplicate skills.

The commands below use a local copy of this repository. Replace `/absolute/path/to/skills` with its location on your computer. To install straight from GitHub instead, see the [installation guide](docs/plugin-installation.md) for Claude Code, Codex, and Gemini CLI, or install by name with the Skills CLI below.

### Claude Code

Launch Claude Code with the suite loaded:

```bash
claude --plugin-dir /absolute/path/to/skills
```

Kuudo's startup instructions are loaded automatically for that session. Ask a question such as:

```text
Audit my Sponsored Products campaigns.
```

To select a skill explicitly, use its [plugin command](https://code.claude.com/docs/en/plugins):

```text
/kuudo-skills:amazon-ads-sp-campaign-auditor
```

For installation that persists across launches, see the [marketplace setup](docs/plugin-installation.md#whole-suite-in-claude-code).

### Codex

Register the local marketplace and install the suite from your terminal:

```bash
codex plugin marketplace add /absolute/path/to/skills
codex plugin add kuudo-skills@kuudo-skills-dev
```

Start a new Codex session. Codex discovers the installed skills and can select them for relevant requests. To explicitly start with Kuudo's guidance, try:

```text
Use using-kuudo to review this Seller Central listing.
```

You can also name a skill directly: “Use amazon-profitability-calculator to calculate this product's break-even price.” See the [Codex installation notes](docs/plugin-installation.md#whole-suite-in-codex) for CLI version details.

### Gemini CLI

Link the local copy as a Gemini CLI extension:

```bash
gemini extensions link /absolute/path/to/skills
```

Start a new Gemini CLI session. Gemini CLI discovers the suite's skills and can activate them for relevant requests. As with Codex, you can start with Kuudo's guidance by asking it to use `using-kuudo`, or name a skill directly. To install from GitHub, see the [Gemini CLI installation notes](docs/plugin-installation.md#whole-suite-in-gemini-cli).

### Other Agent Skills-compatible clients

Install an individual skill from your local copy with the [Skills CLI](https://skills.sh/docs/cli), then select your client when prompted:

```bash
npx skills add /absolute/path/to/skills --skill amazon-profitability-calculator
```

You can also install straight from GitHub, by name or package URL:

```bash
npx skills add KuudoAI/skills --skill <skill-name>
npx skills add https://github.com/KuudoAI/skills/tree/main/skills/<skill-name>
```

Replace `<skill-name>` with a name from the collection. Start a new session and ask your agent to use that skill. Discovery and activation depend on the client; individual installation supplies the selected skill without the suite's startup instructions.

Kuudo packages follow the open [Agent Skills](https://agentskills.io/home) [specification](https://agentskills.io/specification), so the same workflow can travel with you across compatible clients.

## Connect your Amazon tools

To work with live accounts, connect the Amazon Ads or Selling Partner API tools required by your chosen skill through your client's MCP settings. MCP lets your agent access those services. Installation of the skills and connection of your accounts are separate steps.

Kuudo provides Amazon MCP connections for the major surfaces these skills work across:

- [Amazon Ads MCP](https://www.kuudo.com/features/amazon-ads-mcp/) for Sponsored Products, Sponsored Brands, Sponsored Display, DSP, and advertising operations.
- [Amazon Selling Partner API (SP-API) MCP](https://www.kuudo.com/features/amazon-selling-partner-mcp/) for Seller Central orders, listings, inventory, fees, and feeds.
- [Amazon Vendor Central MCP](https://www.kuudo.com/features/amazon-vendor-central-mcp/) for purchase orders, advance shipment notices, invoices, and vendor analytics.
- [Amazon Marketing Cloud (AMC)](https://www.kuudo.com/features/amc/) for audiences, attribution, incrementality, and AMC analysis.

Follow the [MCP configuration guide](docs/mcp-configuration.md) for client setup. Each skill describes its requirements; several also support reports or manual inputs, so you can start with data you already have.

## Skill quality

- **Certified** skills have been reviewed and certified by KuudoAI, pass repository validation, and include cases checking when they should and should not activate.
- **KuudoAI Reference Skills** are first-party reference implementations maintained by KuudoAI that have not yet completed certification.
- **Community** skills are third-party contributions that have not been KuudoAI-certified.

Browse the generated [skill catalog](catalog/skills.json) for each skill's standard description, compatibility, status, source, and license. The governance records behind it live in [catalog/entries/](catalog/entries/). Review instructions and bundled scripts before use, especially for third-party skills.

## Creating skills

Have a workflow you wish your agent knew? Turn it into a skill of your own, or ask us to help.

### Create your own

A skill starts with a `SKILL.md` file describing when to use it and how to do the work. Explain the inputs it needs, the steps to follow, and what a useful result looks like. Add examples, references, or scripts where they help. You can write it yourself or ask your agent to help turn your process into clear instructions.

To create a skill in this repository, run:

```bash
npm run skill:new -- your-skill-name
```

Fill in the generated instructions, try the skill on realistic requests, and follow the [contribution guide](CONTRIBUTING.md) to validate and share it through a pull request.

### Ask us for a skill or an improvement

[Open a skill request](https://github.com/KuudoAI/skills/issues/new) for a new workflow or changes to an existing skill. Tell us:

- What you want to accomplish and where the current process falls short.
- An example request you would give your agent and the result you want back.
- What data, reports, or connected tools the workflow should use.
- For an existing skill, its name and what you would like changed.

A concrete example helps us understand the need and shape the right workflow.

## Contribute

Have an Amazon workflow worth sharing, or a way to improve an existing skill? Start with the [contribution guide](CONTRIBUTING.md) for authoring, importing, and review. Contributors can run `npm run smoke` for an offline distribution check; the guide covers the full validation workflow.

Report vulnerabilities privately using [SECURITY.md](SECURITY.md).

## Releases

Kuudo uses versioned GitHub releases such as `v0.2.0`. Releases are automated with release-please: Conventional Commit messages on `main` drive a release pull request that bumps the synchronized package and plugin versions and writes [RELEASE-NOTES.md](RELEASE-NOTES.md), and merging it tags and publishes the release. Each skill also carries its own version, which pull requests must bump when they change the skill. See the [release process](CONTRIBUTING.md#releases) for details.

## License and acknowledgments

All KuudoAI-authored content in this repository is licensed under the [PolyForm Shield License 1.0.0](licenses/PolyForm-Shield-1.0.0.md): use it freely, including in paid Amazon work for yourself or your clients, but not to build a competing product. [LICENSE.md](LICENSE.md) records the required notice and KuudoAI's additional permission for customers. Imported third-party skills retain their upstream terms, recorded in [THIRD_PARTY_NOTICES.md](THIRD_PARTY_NOTICES.md).
