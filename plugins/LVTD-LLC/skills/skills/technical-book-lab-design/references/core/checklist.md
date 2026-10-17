# Technical Book Lab Design Checklist

Use this checklist when reviewing a technical chapter, lab, or tutorial.

## Outcome

- [ ] The lab has one primary reader outcome.
- [ ] The reader can verify the outcome.
- [ ] The chapter title or opening states the value.
- [ ] The lab avoids unnecessary adjacent goals.

## Starting State

- [ ] Reader prerequisites are explicit.
- [ ] OS, version, architecture, accounts, tools, and permissions are stated where relevant.
- [ ] Required files, directories, secrets, and network access are listed.
- [ ] Missing prerequisites are linked, compressed, or moved earlier.

## Steps

- [ ] Each major step has a purpose.
- [ ] Commands or UI actions are complete enough to run.
- [ ] Placeholders are named consistently.
- [ ] Expected output or state is shown.
- [ ] Checkpoints occur before long sequences continue.

## Failure Handling

- [ ] Common errors have troubleshooting notes.
- [ ] Risky actions have warnings before the action.
- [ ] Cleanup or rollback exists where needed.
- [ ] Security, data loss, public exposure, and cost risks are marked.
- [ ] Readers know when not to continue.

## Learning Transfer

- [ ] The lab explains what the reader should understand now.
- [ ] The final state is summarized.
- [ ] Next safe variations are suggested.
- [ ] Maintenance, updates, monitoring, or backups are addressed when relevant.

## Red Flags

- Many commands appear before the first check.
- The reader must already understand the thing being taught.
- Failure handling says only "check logs" without saying what to look for.
- The lab changes production systems without rollback.
- The lab works only in the author's environment.

## Quality Rubric

| Dimension | Strong | Weak |
|-----------|--------|------|
| Outcome | Observable reader result | Topic coverage |
| Pacing | Frequent verified progress | Long setup before payoff |
| Safety | Risk boundaries explicit | Risk discovered by accident |
| Failure | Symptoms mapped to causes | Generic troubleshooting |
| Transfer | Reader can adapt the pattern | Reader can only copy commands |
