# Software references

Copy only applicable blocks to the named workspace destinations. Replace placeholders with confirmed facts or explicit unknown/pending state. These are templates, not authorization to execute commands.

## software/README.md

```markdown
# Software

Read this index and the relevant application topic before changes. Add only deliberately managed applications or closely related groups; maintain links after moves/removals. No application inventory has been verified yet.
```

## software/{{APPLICATION_SLUG}}.md

```markdown
# {{APPLICATION_NAME}}

- Purpose and observed/intended status: {{STATUS}}.
- Executable/version/source/update/removal method: {{VERIFIED_DETAILS_DATE_SOURCE}}.
- Important configuration/data/service locations and current preferences: {{DETAILS_OR_UNKNOWN}}.
- Known limitations and relevant verification: {{DETAILS}}.
- Reproduction procedure: {{UPSTREAM_OR_INSTALLATION_REFERENCE}}.

Record completed work and decision rationale in dated history, not an accumulating worklog here.
```
