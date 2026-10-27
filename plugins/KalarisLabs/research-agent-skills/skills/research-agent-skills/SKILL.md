---
name: research-agent-skills
description: Navigate the Research Agent Skills collection by Kalaris Labs for academia across AI, machine learning, biology, chemistry, medicine, physics, and academic writing. Use when a researcher needs to choose a field of study, identify relevant specialist SKILL.md files, or coordinate a cross-disciplinary research workflow. For a narrow task with a matching specialist skill already available, use that skill directly.
license: MIT
compatibility: The skill index works offline. Specialist skills must be available in the agent's environment before use.
metadata:
  version: '1.0'
  category: research-automation
  maintainer: Kalaris Labs
  tags: academia, research agents, scientific research, academic writing, skill collection, AI, machine learning, biology, chemistry, medicine, physics
---

# Research Agent Skills by Kalaris Labs

This is the collection index for the specialist research skills maintained by
Kalaris Labs. It helps an agent choose the right skill for a research task.

## Choose a skill

1. Identify the research deliverable and domain. Examples include a literature
   review in medicine, an ML experiment, a chemistry analysis, or a physics figure.
2. Read only the relevant section of [the bundled skill index](references/catalog.md).
   Select the smallest set of specialist skills that covers the task.
3. Read the selected specialists' `SKILL.md` files if they are available in the
   current agent environment. Otherwise, identify the skill names for the
   researcher and refer them to the repository's installation documentation.
4. Keep claims and citations tied to checked sources. A skill's presence does
   not establish that an analysis or scientific claim is correct.

Use the specialist skill directly for ordinary single-domain work. This entry
is useful when the request spans skills or concerns collection setup.

Before selecting skills, check:

- [ ] Which research field and deliverable does the researcher need?
- [ ] Is one specialist enough, or does the work cross fields?
- [ ] Are the selected specialist folders available in this environment?

## Verify the handoff

State which specialist skills you selected and why. Check that each selected
skill folder contains `SKILL.md` before claiming it is available. This index
does not replace any specialist's scripts or references.
