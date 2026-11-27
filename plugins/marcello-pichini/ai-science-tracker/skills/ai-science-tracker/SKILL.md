---
name: ai-science-tracker
description: Answer questions about scientific discoveries made with AI, or software vulnerabilities found with AI, from the AI Science Tracker catalog, citing the original sources and their caveats.
---

Use the AI Science Tracker MCP tools when the user asks what AI has discovered, which AI models or organizations contributed to a result, or whether a vulnerability or CVE was found with AI.

1. Search first. Use `search_discoveries` with short English topic words, a DOI, a year, a field (`list_fields` gives the names) or an organization. Use `search_vulnerabilities` with words, a product, an AI system or a CVE ID.
2. Open the records you cite with `get_discovery` or `get_vulnerability` to read the original source, evidence notes and limitations.
3. In the answer, link each result's original source and its catalog page, give the publication or disclosure date, and keep the stated caveats. Figures come from the linked sources and are not independently verified; do not present them as confirmed.
4. If a search returns `partial_match` or nothing, say so and suggest narrower or different words rather than inventing results. The catalog is curated and not exhaustive.
