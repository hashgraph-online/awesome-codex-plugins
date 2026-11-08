#!/usr/bin/env node
// SessionStart hook, for Claude Code and for hosts that run a Claude Code hooks.json through a bridge
// (DeepSeek Harness does exactly that) - and, in a different shape, for goose.
//
// Claude Code adds plain stdout to the session, but a bridge codec may accept only
// hookSpecificOutput.additionalContext, and it drops the whole reply when hookEventName is not exactly
// "SessionStart". One shape works for both, so that is the shape we print.
//
// goose does not read that envelope at all. Its hook stdout is the decision channel - {"decision":"block"}
// and nothing else - so a JSON reply there is discarded, and the ambient text would be fetched and thrown
// away. goose's equivalent of "add this to the session" is the built-in Top Of Mind extension, which
// injects the file named by GOOSE_MOIM_MESSAGE_FILE into every turn. On goose this hook writes that file
// instead of printing, and leaves stdout empty.
//
// With no credential nothing is written or printed, and the exit code is 0 either way - a hook that cannot
// reach the librarian must not break the session.

import { fetchAmbient, hooksDisabled, writeMoim } from "../tools/ambient.mjs";

if (hooksDisabled()) process.exit(0);

// goose sets PLUGIN_ROOT for a plugin hook and knows nothing of CLAUDE_PLUGIN_ROOT, which is the one
// Claude Code sets. Presence of the first without the second is goose.
const onGoose = !process.env.CLAUDE_PLUGIN_ROOT && !!process.env.PLUGIN_ROOT;

const r = await fetchAmbient().catch(() => null);
if (!r) process.exit(0);

if (onGoose) {
  // Top Of Mind reads this file, so the same refresh the scheduler would do happens for free at session
  // start. Never let it break the session.
  if (!hooksDisabled() && r) {
    try {
      writeMoim(r);
    } catch {
      /* a card is not worth a session */
    }
  }
  process.exit(0);
}

if (r.state === "ok" && r.text) {
  process.stdout.write(
    JSON.stringify({ hookSpecificOutput: { hookEventName: "SessionStart", additionalContext: r.text } }),
  );
}
process.exit(0);
