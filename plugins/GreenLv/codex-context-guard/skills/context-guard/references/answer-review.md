# Independent answer review — source candidate

The task agent, after an adopted-policy commentary answer is delivered, owns
one `review-pending` invocation with the existing session/turn private token.
No Hook starts a model. No configured policy means no review authority. The
collector requires an operator-pinned executable and creates a separate fresh
reviewer; it never accepts the producer's self-verdict or an imported receipt.

`answer-review/v2` asks the independent reviewer to associate each candidate
message with exact question IDs/UTF-8 spans from its supplied root catalog, or
mark association unknown. Those are fallible semantic judgments, not Host
fields. A message may relate to several questions. Only a verdict for that
exact question can remove its information-only pending projection; actions,
proofs, waits and prohibitions remain unchanged. A correction, missing source,
conflict or revoked authority reopens only the information projection.

Each queue invocation makes at most one new model call. The same input is not
automatically retried after failure or partial coverage. New messages may be
reviewed once more, replacing only a validated unique same-question predecessor.
Do not loop until complete. Requests and model output remain in private local
captures; never publish them. The process has bounded input/output and a deadline.
The POSIX group route checks disappearance after cleanup; on macOS, a
remaining group must have no running members by complete system readback.
These are separate observations, and denied or unknown readback fails closed. The Windows route
starts suspended, assigns the process to a kill-on-close Job Object, then
resumes it; a zero-model native probe observed owned child exit after the
leader exited. Escaped descendants remain outside the verified route. Native
reviewer model behavior and skill-triggered scheduling remain unaccepted; do
not present source or zero-model tests as automatic incident closure.

The recovery display limit is not the reviewer input limit. The collector checks
the full transcript for conflicts before retaining the selected root's candidate
messages. Too many messages or too much text for that root remains unknown;
large unrelated history does not consume that root's review budget. Global
stream/identity limits still apply and must not be represented as passed review.
