---
name: graphify
description: Query Graphify for the code graph, Memory, and PR review status of repositories indexed in the user's Graphify workspace.
---

# Use Graphify

Use Graphify's MCP tools when the user asks about a repository indexed in Graphify: where code lives, what a change could affect, what the team saved in Memory, or the status of a Graphify pull request review.

## What the tools cover

- The code graph: find symbols and files, trace callers and dependencies, and check impact and linked tests.
- Memory: recall decisions, incidents and lessons the team saved in Graphify.
- `review_status`: read the status, gate result and top findings of Graphify's review of a pull request.

Wiki is not served over MCP. It lives in the Graphify app at https://app.graphify.com.

## How to answer

- Name the repository you are querying. If none is selected, call `list_repositories` first.
- Cite files and symbols the tools return. Do not invent paths or review results.
- Repository graph tools are read-only: they do not edit files, open pull requests or start reviews. Some Memory tools can write workspace notes, so describe that request before you approve it.
- Answers cover repositories already indexed in Graphify. A newly added repository has to finish indexing first.
- If a tool fails, report the error and the next step from the [Codex setup guide](https://docs.graphify.com/integrations/codex). Do not guess.
