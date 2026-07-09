# Spike De-Spike Patterns

## Spike Rules

A spike is for learning, not shipping. Keep it time-boxed and reversible:

- Use a branch or isolated commit range.
- Name the question being answered.
- Avoid polishing incidental code.
- Capture setup commands and surprising constraints.
- Stop when the question is answered.

## De-Spike Sequence

1. Summarize what the spike proved.
2. Write an outer behavior test from the useful workflow.
3. Revert or set aside spike code.
4. Rebuild the first small production slice.
5. Add lower-level tests as design emerges.
6. Refactor only under green tests.
7. Delete spike-only scaffolding.

## Passwordless/Auth Flow Slices

For authentication-style features, split behavior into slices:

- Login UI accepts an email address.
- View sends a message through a mail boundary.
- Token model records a unique login token.
- Link authenticates the user or shows a safe failure.
- Session/logout behavior works through Django auth.

Use real Django auth behavior for integration checks. Fake only external email delivery.

## Learning Capture

Before reverting a spike, keep:

- The desired user flow.
- New model fields or constraints that are truly needed.
- External service API facts.
- Settings or environment variables required.
- Error cases discovered.

Do not keep:

- Hardcoded secrets or tokens.
- Throwaway templates.
- Print-debugging and console experiments.
- Broad mocks that bypass the workflow.

## De-Spike Checklist

- [ ] Spike question answered.
- [ ] Behavior expressed as tests.
- [ ] Exploratory code removed or isolated.
- [ ] Production implementation rebuilt in small slices.
- [ ] External boundaries tested with fakes or mocks.
- [ ] Auth/session behavior covered with real Django integration where relevant.
