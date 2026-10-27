---
name: bgpt-paper-search
description: Search scientific papers and retrieve structured experimental data extracted from full-text studies via the BGPT MCP server. Returns 25+ fields per paper including methods, results, sample sizes, quality scores, and conclusions. Use for literature reviews, evidence synthesis, and finding experimental details not available in abstracts alone.
license: MIT
compatibility: Requires the BGPT MCP server configured in the agent host (npx mcp-remote or npx bgpt-mcp), internet access to bgpt.pro, and an optional BGPT API key for paid usage.
metadata:
  version: '1.1'
  category: literature-review
  maintainer: Kalaris Labs
  website: https://bgpt.pro/mcp
  github: https://github.com/connerlambden/bgpt-mcp
  contributor: BGPT
  tags: paper search, literature review, evidence synthesis, structured data extraction, MCP
---

# BGPT Paper Search

## Overview

BGPT is a remote MCP server that searches a curated database of scientific papers built from raw experimental data extracted from full-text studies. Unlike traditional literature databases that return titles and abstracts, BGPT returns structured data from the actual paper content — methods, quantitative results, sample sizes, quality assessments, and 25+ metadata fields per paper.

## When to Use This Skill

Use this skill when:
- Searching for scientific papers with specific experimental details
- Conducting systematic or scoping literature reviews
- Finding quantitative results, sample sizes, or effect sizes across studies
- Comparing methodologies used in different studies
- Looking for papers with quality scores or evidence grading
- Needing structured data from full-text papers (not just abstracts)
- Building evidence tables for meta-analyses or clinical guidelines

## Setup

BGPT is a remote MCP server — no local installation required. Configure it in your agent's MCP settings before use; this skill instructs the agent to call the `search_papers` MCP tool and does not enable MCP access by itself.

### Claude Desktop / Claude Code

Add to your MCP configuration:

```json
{
  "mcpServers": {
    "bgpt": {
      "command": "npx",
      "args": ["mcp-remote", "https://bgpt.pro/mcp/sse"]
    }
  }
}
```

### npm (alternative)

```bash
npx bgpt-mcp
```

## Usage

Once the BGPT MCP server is configured, call its `search_papers` tool via the agent's MCP interface (not via Bash):

```
Search for papers about: "CRISPR gene editing efficiency in human cells"
```

The server returns structured results including:
- **Title, authors, journal, year, DOI**
- **Methods**: Experimental techniques, models, protocols
- **Results**: Key findings with quantitative data
- **Sample sizes**: Number of subjects/samples
- **Quality scores**: Study quality assessments
- **Conclusions**: Author conclusions and implications

## Pricing

- **Free tier**: 50 searches per network, no API key required
- **Paid**: $0.01 per result with an API key from [bgpt.pro/mcp](https://bgpt.pro/mcp)

## Agent operating procedure

1. **Check the environment.** Confirm the research question, databases, date range and inclusion criteria.
2. **Pin down the inputs.** Confirm formats, identifiers and parameters from the data or the user. Ask rather than guess any value that changes the result.
3. **Run a small version first.** Run the search on one database with a narrow query and check that the results are relevant.
4. **Execute the full task** using the instructions and references above.
5. **Validate the result.** Every reference is retrieved from a real record with a resolvable identifier; counts and search strings are recorded.
6. **Report.** State what was run (versions, commands, parameters), what was checked, and what is still uncertain.

| If this happens | Do this |
|---|---|
| An API rate-limits or returns errors | Back off and retry, reduce the batch size, or switch database, and report the gap. |
| A function, flag or endpoint in these instructions is missing in the installed version | Check the installed version's own documentation (`help()`, `--help`, official docs), adapt, and tell the user. Never invent an API. |
| A required input, identifier or parameter is ambiguous | Ask the user, or state the assumption explicitly before running. |

**Integrity rules**

- Never fabricate results, parameters, identifiers, citations or statistics. If something cannot be run or verified, say so plainly.
- Never summarize a paper you have not retrieved; never cite from memory.
- Treat version-specific details here as possibly outdated: confirm them against the official documentation for the installed version.
- Ask before actions that cost money, consume shared GPUs or cloud quota, touch personal or patient data, or cannot be undone.

## Related skills

- `statistical-analysis`: Guided statistical analysis for research data - test selection, assumption checking, effect sizes, power analysis, Bayesian alternatives, a…
- `scientific-critical-thinking`: Evaluate scientific claims and evidence quality.
- `folklore-variant-evidence`: Retrieve ClinGen gene-disease validity assertions for a public gene or disease, and review source-linked public evidence and literature for…
