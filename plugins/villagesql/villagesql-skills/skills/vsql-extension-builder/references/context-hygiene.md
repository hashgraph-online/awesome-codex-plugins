# Context Hygiene

Rules that apply throughout every phase. Read at the start of every phase
and keep active for the duration of the session.

- **Tracking files are the record; the conversation is the signal.**
  Verbose state (file contents read, agent findings, build output, test
  output, search results) goes to `.claude/tracking/`. The conversation
  gets a summary line.
- **Never paste source code into the conversation.** `.cc`, `.h`,
  `.test`, and `.result` files belong on disk, not in the conversation
  thread. When passing source files to a subagent, embed them in the
  subagent's prompt — do not print them in the conversation first.
  When implementing a function, state "implemented `func_name`" — do
  not print the implementation.
- **Do not echo any file contents into the conversation when reading.**
  Read headers, source files, and references silently. State what you
  found; do not paste what you read (except where a gate explicitly
  requires a verbatim excerpt).
- **Phase transitions are two lines maximum:** what gate evidence was
  met, and which phase is next. Not a recap of all work done.
- **Build failure output:** if cmake or make output exceeds 50 lines,
  save the full output to `.claude/tracking/build_output_<n>.txt` and
  paste only the error lines. Never paste a full cmake configuration
  trace into the conversation.
- **Proactive save:** if many phases have completed or many fix cycles
  have run, save current state to tracking files before continuing. The
  resume protocol reconstructs from tracking files — keeping them
  current reduces the cost of any compaction.
