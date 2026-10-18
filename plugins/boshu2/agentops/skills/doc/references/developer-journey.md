# Developer journey

Use this method when the caller asks whether an advertised cold install,
upgrade or first-success path works. Check the actual selected package in an
appropriate disposable environment, then correct a demonstrated misleading
instruction at its existing documentation owner. This is conditional Doc
work; it adds no documentation pack, score or required Test invocation.

## Select the journey before running it

- Reuse the accepted audience, starting state and journey. Name the observable
  result advertised as first success and the current published instructions to
  follow. Distinguish a cold install from an upgrade; they need different states.
- Identify the intended artifact: distribution/source location, exact version,
  build and platform, identity of the package bytes (digest when available), and
  installer or install command selected by the instructions. Keep these
  identities separate from the checkout. Record an unavailable identity as unknown.
- Establish the actual host and disposable environment: OS, architecture,
  runtime, package manager and relevant environment state. Confirm that it can
  exercise the promised path. A container does not by itself test host app or
  shell discovery. Use only available, authorized resources.
- Confirm authority for the specific installation, network access and state
  changes. A disposable environment does not grant permission for accounts,
  sign-in, credentials or production installation. Keep human-only setup with
  the caller's AI Partner workflow; do not automate it through this method.

If the selected artifact, environment or authority is unavailable, narrow the
claim to the inspected documentation and mark the unexecuted journey
`not_checked`. State the missing input or capability. Do not substitute a
checkout build, another version or an existing installation without agreement.

## Follow the advertised path

Use the current published instructions as the reader would encounter them;
record their URL or file and revision/access date. Execute the real commands
or actions in order, including stated prerequisites. Capture the exact command
or action, observed result and actual error at the step where it occurs.
Do not repair an instruction silently and call the original path successful.

For a cold install, establish the claimed clean starting state before the first
action, including absence of a prior installation and relevant user config.
For an upgrade, begin with the selected supported prior version and authorized
representative user state. Record that state before changing it and compare it
afterward against the promised preservation behavior. Avoid using private or
production state as a convenient fixture. Use a backup or rollback only when
it is supported and authorized; never assume a downgrade is safe.

Check what actually ran: the installed command or entrypoint location, its
reported version/build and its relationship to the selected package. Assert
the advertised effect, such as the generated file, stored setting or useful
command result, rather than treating an exit code or help screen as first
success. [Test's oracle guidance](../../test/SKILL.md#oracle-strength-hierarchy)
can help choose the observation without making Test a required wrapper.

Measure elapsed time only from execution: record the start immediately before
the first advertised action and the end at the promised result or actual
blockage. State the start/end events, timestamps and elapsed duration; disclose
interruptions and whether their time is included. Estimated step times are
estimates and cannot be presented as this measurement.

## Correct the owning instruction

Within the authorized documentation scope, make the smallest correction that
addresses the observed misleading instruction, prerequisite or advertised
result. Preserve the original accepted journey. A product defect is not fixed
by rewriting its promise; repair it only within existing implementation
authority, otherwise return its reproducer and the unresolved claim.

When the environment and artifact remain available, repeat the original
journey with the corrected instruction and confirm the same advertised effect.
Record a verification that could not run as `not_checked`. Leave existing user
state intact; clean up disposable resources only within the authorized scope.

Return these facts in the existing response or handoff: selected package and
installed identity, instructions and starting state, commands/actions and
observed effect, measured timing or unavailable measurement, actual failures,
changed owner and checked/`not_checked` scope. Create no separate report tree.

## Claims this check cannot support

- Checkout tests passing do not prove a fresh installed command exists or works.
- Upgrade success requires the promised user state to survive, not just startup.
- An imagined novice walkthrough is not observed onboarding. An operator-run
  journey alone does not establish independent novice success.
- Untried hosts and versions stay `not_checked`; one working environment does
  not prove cross-host portability or general usability.
