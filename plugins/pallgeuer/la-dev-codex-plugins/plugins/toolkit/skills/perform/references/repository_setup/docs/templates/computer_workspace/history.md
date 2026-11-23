# Dated decisions and work

Copy only applicable blocks to the named workspace destinations. Replace placeholders with confirmed facts or explicit unknown/pending state. These are templates, not authorization to execute commands.

## history/README.md

```markdown
# History

Dated decisions, rationale, completed work and actual verification grouped by year. Current state belongs in topic notes. Link populated year indexes here; split growing indexes when useful.
```

## history/{{YEAR}}/README.md

```markdown
# {{YEAR}}

- [{{TASK_TITLE}}]({{DATE}}-{{TASK_SLUG}}.md)
```

## history/{{YEAR}}/{{DATE}}-{{TASK_SLUG}}.md

```markdown
# {{TASK_TITLE}}

- Approved scope and consequential decisions/rationale: {{DETAILS}}.
- Completed work and deviations: {{ACTUAL_WORK}}.
- Verification, source/date and limitations: {{ACTUAL_CHECKS}}.
- Current references, unresolved task and relevant evidence links: {{LINKS}}.
- Cleanup assessment and any explicitly approved deletion: {{OUTCOME}}.
```
