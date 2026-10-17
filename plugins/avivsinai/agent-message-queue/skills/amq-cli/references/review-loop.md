# Delegated review loops

Use a separate worker for a multi-round review when the host provides one and
the user or repository permits delegation. Otherwise keep the review in the
current session. AMQ does not create background workers or grant edit authority.

## Ownership

Give the worker the file or worktree paths, review scope, reviewer handle,
thread, permitted actions, and stopping condition. Use a distinct assigned
AMQ handle and resolve its full context before it sends or receives. Do not
let a worker and the main agent compete to drain the same mailbox.

A review-only worker reports findings; it does not apply fixes. An authorized
implementation worker may fix findings within its assigned files. Review
approval does not grant permission to commit, push, merge, or expand scope.

## Message flow

1. Send a `review_request` with paths and the user-visible change.
2. Keep the existing thread. The reviewer returns `review_response`.
3. Apply authorized findings, then request review of the changed files.
4. Stop when review is complete, the assigned limit is reached, or a decision
   requires the owner. Return the result, unresolved findings, and checks that
   were not performed.

When work starts, reply with `kind=status` and an ETA. Use `urgent` only for
work that must interrupt the current activity.

Reply to the initiator, preserve the existing thread, send status at start and
phase boundaries, and finish with changes and verification.

## Receive without a second consumer

With a live injecting wake, yield after independent work and drain on its
doorbell. Do not add `watch`, `monitor`, or a background polling loop to that
mailbox. Without a wake, a bounded wait may be used within the assigned task.

Select worker tools from the host's actual interface. Tool names and
background-task support are host features, not part of the AMQ protocol.
