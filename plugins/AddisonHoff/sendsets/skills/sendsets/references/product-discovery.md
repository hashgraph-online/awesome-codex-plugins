# Product discovery before outbound

Read the README and product docs, package manifests, main pages and routes, API routes, schema and models, integrations, authentication and onboarding, and the core workflow. Follow the files that reveal what value the product creates. Do not read secrets or change code during this pass.

Explain in plain English:

1. What the product appears to do and who uses it.
2. Valuable actions it can perform for one prospect.
3. Events that could change a follow-up, with file paths supporting each finding.
4. Which useful actions or events already exist and which would need to be built.

Then propose five distinct outbound workflows. Each should follow this chain:

signal → prospect → external context → action in this product → useful artifact → Sendsets email → interaction → product event → follow-up, branch, or stop

For each, give a name, why the prospect would care, the exact workflow, a short realistic first email, what Sendsets does, and what needs to be built. Prefer a finished result the prospect can inspect before a meeting. Ground capabilities in code; mark unbuilt steps as proposed. Avoid generic website summaries, name personalization, generic icebreakers, hiring signals, and enrichment presented as the deliverable.

End with a clear choice. Do not implement a workflow, alter code, provision mailboxes, or send anything until the user chooses an idea. If the repo is unavailable, ask for a product description and label all assumptions.
