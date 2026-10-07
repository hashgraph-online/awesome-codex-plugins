"use strict";

const POLICY = "Be concise without omitting necessary explanations, uncertainty, evidence, security or useful code comments. Lead with the result; avoid filler and repetition. Preserve the user's language and accents. Prefer the smallest correct change and targeted checks. Do not delegate trivial tasks. Delegated agents keep the session model unless the user chooses another one. Without asking, you may send independent read-only research whose output would flood the context, or that needs more than about ten tool calls, to a read-only research agent (espresso:scout in Claude Code) running in the background, and keep working with the user; ask before delegating edits. Keep edits on the main thread; parallel edits only in isolated worktrees after a commit. Research agents use medium effort; raise effort for verification, security and edge cases, not by default. Never claim measured savings without measurements. User and project rules take precedence over Ponytail, including on tests and comments. Active skills own their workflow: Arsenal selects skills; Ship or the selected skill retains approval gates, solo flags, specialized agents and models, output schemas, artifact states, verification and commit rules. These override Espresso recommendations, including automatic delegation. Never add a competing team or reviewer. Never use an external worker to bypass a controlled runtime. These workflows remain independent of Espresso.";

function rewriteCommand(command) {
  // Only simple read-only Git commands: preserve raw diffs, errors and scripts.
  if (typeof command !== "string" || !/^(?:git status(?: --short| --branch| -s| -b)*|git log --oneline(?: -[0-9]+| --max-count=[0-9]+)?)$/.test(command)) return null;
  const result = require("node:child_process").spawnSync("rtk", ["rewrite", command], {
    encoding: "utf8", timeout: 1000, windowsHide: true,
  });
  const rewritten = result.stdout?.trim();
  return result.status === 0 && rewritten?.startsWith("rtk git ") ? rewritten : null;
}

module.exports = { POLICY, rewriteCommand };
