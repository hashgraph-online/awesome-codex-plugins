import { randomUUID } from "node:crypto";
import {
  existsSync,
  mkdirSync,
  readdirSync,
  readFileSync,
  unlinkSync,
  writeFileSync,
} from "node:fs";
import { resolve } from "node:path";

function alive(pid) {
  try {
    process.kill(pid, 0);
    return true;
  } catch (error) {
    return error.code !== "ESRCH";
  }
}
function unlink(path) {
  try {
    unlinkSync(path);
  } catch (error) {
    if (error.code !== "ENOENT") throw error;
  }
}
function activeClaims(path) {
  const claims = [];
  for (const name of readdirSync(path)) {
    const match = /^(\d+)-[0-9a-f-]{36}\.claim$/u.exec(name);
    if (match) {
      if (alive(Number(match[1]))) claims.push(name);
      else unlink(resolve(path, name));
    } else if (name === "owner.json") {
      // Upgrade the old single-owner format without waiting 30 minutes.
      try {
        const owner = JSON.parse(readFileSync(resolve(path, name), "utf8"));
        if (Number.isSafeInteger(owner.pid) && owner.pid > 1 && alive(owner.pid)) claims.push(name);
        else unlink(resolve(path, name));
      } catch (error) {
        if (error.code !== "ENOENT") claims.push(name);
      }
    }
  }
  return claims;
}

// Unique claim filenames prevent two stale-lock reapers from deleting a new owner's lock.
// The empty directory is retained; it is not itself the lock.
export async function acquireRuntimeLock(path, options = {}) {
  const deadline = Date.now() + (options.timeoutMs ?? 180_000);
  const name = `${process.pid}-${randomUUID()}.claim`;
  const claimPath = resolve(path, name);
  mkdirSync(path, { recursive: true, mode: 0o700 });
  let published = false;
  try {
    for (;;) {
      if (options.ready?.()) {
        if (published) unlink(claimPath);
        return null;
      }
      let current = activeClaims(path);
      if (!published && current.length === 0) {
        writeFileSync(claimPath, "", { flag: "wx", mode: 0o600 });
        published = true;
        current = activeClaims(path);
      }
      if (published) {
        const others = current.filter((candidate) => candidate !== name);
        if (others.length === 0 && existsSync(claimPath)) {
          return () => unlink(claimPath);
        }
        // Concurrent newcomers elect one waiter; an existing owner is never evicted.
        if (others.some((candidate) => candidate < name)) {
          unlink(claimPath);
          published = false;
        }
      }
      if (Date.now() >= deadline)
        throw new Error(options.timeoutCode ?? "GOAL_PROGRESS_SOURCE_LOCK_TIMEOUT");
      await new Promise((done) => setTimeout(done, 50));
    }
  } catch (error) {
    if (published) unlink(claimPath);
    throw error;
  }
}
