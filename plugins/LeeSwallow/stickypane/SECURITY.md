# Security

## What stickypane promises

- On the board, a script note (`.sh`, `.ps1`) or an `.http` request runs
  only after the user says yes, each time. From the command line, only the
  command that names it runs it (`stickypane api`); nothing runs a note by
  itself.
- The board and its commands write only inside the project's notes folder
  and the files linked from it.
- `stickypane watch --exec` runs a command only when the user started that
  watch with it.

A way around any of these is a security problem, and so is anything else
that lets a note, a file or an agent do what the user did not allow.

## Reporting one

Report it privately: on GitHub, **Security → Report a vulnerability**
([new advisory](https://github.com/LeeSwallow/stickypane/security/advisories/new)),
or email the address on the maintainer's GitHub profile. Do not open a
public issue.

You will hear back within a week. A fix goes into the next release, and the
advisory is published with it, crediting you unless you would rather not.
Fixes are best effort; there is no bounty.

## Supported versions

Only the latest release. stickypane is before 1.0, so a fix is not
backported.
