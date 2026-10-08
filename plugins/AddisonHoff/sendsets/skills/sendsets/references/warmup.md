# Warmup and sender health

Use `sendsets mailbox warmup status MAILBOX_ID --json` and `sendsets mailbox health MAILBOX_ID --json` to inspect readiness. `sendsets mailbox warmup enable MAILBOX_ID` enables warmup; pause or resume it when the user asks or the account needs attention. Keep warmup running while a healthy mailbox campaigns.

Start fresh mailboxes conservatively. The CLI reference describes a 50 campaign email daily default and 600 seconds between sends, with roughly 10 to 20 daily sends for a fresh sender. Do not raise limits because a campaign has a large list. If bounces or complaints rise, stop the campaign and report the sender state.
