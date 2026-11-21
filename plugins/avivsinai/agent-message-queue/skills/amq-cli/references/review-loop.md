# Delegated review loops

For an independent review, select a seat that did not build the change. The
current session can review if it meets that condition. If no eligible reviewer is
available, record the pending review and continue other work. Use the host's
permitted delegation mechanism.

## Ownership

Give the worker the file or worktree paths, review scope, reviewer handle,
thread, permitted actions, and stopping condition. Use a distinct assigned
AMQ handle and resolve its full context before it sends or receives. Do not
let a worker and the main agent compete to drain the same mailbox.

A review-only worker reports findings; it does not apply fixes. An authorized
implementation worker may fix findings within its assigned files. Review
approval does not grant permission to commit, push, merge, or expand scope.

## Message flow

1. Send the reviewer the proposed head, base, paths, user-visible change and
   requested checks.
2. Reply to the review request ID with `review_response`. Name the inspected
   commit, findings, checks and omissions.
3. Return findings to the builder. Request review on the resulting head after changes.
4. The authorized merger confirms the current head matches the reviewed head and
   its required checks passed. Record the merge result and user-visible proof in
   the assignment.

Report progress as in the [co-op progress protocol](coop-mode.md#progress-protocol).

## Receive without a second consumer

With a live injecting wake, yield after independent work and drain on its
doorbell. Do not add `watch`, `monitor`, or a background polling loop to that
mailbox. Without a wake, a bounded wait may be used within the assigned task.

Select worker tools from the host's actual interface. Tool names and
background-task support are host features, not part of the AMQ protocol.
