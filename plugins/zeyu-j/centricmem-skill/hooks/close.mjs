import { spawn } from "node:child_process";
import { hasCredential, hooksDisabled, hooksDryRun, dontLog } from "../tools/ambient.mjs";
// SessionEnd / close hook: file the unit that just finished, the way Cursor's installed hooks do.
//
// Cursor has had this pair all along (sessionStart -> `centricmem ambient --write`, sessionEnd ->
// `centricmem log-session --auto`). This is the same second half for the clients whose lifecycle events
// include SessionEnd: Claude Code and Codex both do, and Codex's own documentation puts it as "when the main
// thread ends, doesn't run for subagents" - once per session, not once per turn.
//
// Rules, same as the ambient hooks: never fail, and say nothing when there is nothing to say. A close hook
// that exits non-zero can break somebody's session end, and one that runs on every turn would file a card
// per turn, which is why Stop is deliberately not used here.
//
// Filing the session is the point of the product, so this does not ask permission - but it does honour the
// switches mimocode documents (CENTRICMEM_HOOK_DISABLE, CENTRICMEM_DONT_LOG, CENTRICMEM_HOOK_DRY_RUN), so a
// user who set one does not get a different answer on the next host along.
//
// The child is spawned detached and unref'd, as the dsh close-half does: filing is allowed to take its time,
// but the session must not sit waiting for it. Diagnostics go to stderr, because on goose stdout is the
// hook decision channel and a stray line there reads as a decision.

const TIMEOUT_MS = 20000;

const run = (args) => {
  let child;
  try {
    // On Windows the CLI arrives as a .cmd shim, and a .cmd spawned with shell:false throws EINVAL - which
    // the catch below swallows, so the hook looked silent and healthy while doing nothing (seen on dsh and
    // on Claude Code). shell on Windows only, with a fixed argument list.
    const exe = process.platform === "win32" ? "centricmem.cmd" : "centricmem";
    child = spawn(exe, args, {
      detached: true,
      stdio: "ignore",
      shell: process.platform === "win32",
      windowsHide: true,
    });
  } catch {
    return;
  }
  child.on("error", () => {});
  const timer = setTimeout(() => {
    try {
      child.kill();
    } catch {
      /* gone */
    }
  }, TIMEOUT_MS);
  timer.unref?.();
  child.on("exit", () => clearTimeout(timer));
  child.unref();
};

try {
  // No switch and no key means no session to file: looking for a credential in a hook would be guessing.
  if (!hooksDisabled() && !dontLog() && hasCredential()) {
    if (hooksDryRun()) process.stderr.write("centricmem: dry run, would file this session\n");
    else run(["log-session", "--auto"]);
  }
} catch {
  // never fail somebody else's session
}
process.exit(0);
