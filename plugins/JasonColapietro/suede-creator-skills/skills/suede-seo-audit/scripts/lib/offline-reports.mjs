import { lstat, mkdir, mkdtemp, realpath, rename, rm, writeFile } from "node:fs/promises";
import path from "node:path";

export function markdownText(value) {
  return String(value ?? "").replace(/&/g, "&amp;").replace(/</g, "&lt;").replace(/>/g, "&gt;")
    .replace(/[\\`*_\[\]()!|]/g, (char) => `&#${char.charCodeAt(0)};`).replace(/[\r\n]+/g, " ");
}

function within(candidate, root) {
  const rel = path.relative(root, candidate);
  return rel === "" || (!rel.startsWith(`..${path.sep}`) && rel !== ".." && !path.isAbsolute(rel));
}

async function physicalPath(target) {
  const tail = [];
  let current = path.resolve(target);
  while (true) {
    try { return path.join(await realpath(current), ...tail.reverse()); }
    catch (error) {
      if (error.code !== "ENOENT") throw error;
      tail.push(path.basename(current));
      const parent = path.dirname(current);
      if (parent === current) throw error;
      current = parent;
    }
  }
}

// New directories only. Report output may live in ignored reports/ or outside
// the repository; resolve existing ancestors before mkdir to protect source.
export async function writeOfflineReports(output, files, repoRoot) {
  const destination = path.resolve(output);
  const root = path.resolve(repoRoot);
  const allowed = path.join(root, "reports");
  const safe = (target, protectedRoot, reportRoot) => {
    if (within(target, protectedRoot) && (!within(target, reportRoot) || target === reportRoot)) {
      throw new Error("Offline reports cannot overwrite source; choose a new reports/ subdirectory or an external directory");
    }
  };
  safe(destination, root, allowed);
  safe(await physicalPath(destination), await realpath(root), path.join(await realpath(root), "reports"));
  try { await lstat(destination); throw new Error(`Output already exists: ${destination}`); }
  catch (error) { if (error.code !== "ENOENT") throw error; }
  const entries = Object.entries(files);
  if (!entries.length || entries.some(([name, contents]) => !/^[a-z0-9][a-z0-9_.-]*$/i.test(name) || typeof contents !== "string")) {
    throw new Error("Offline reports require plain filenames and text contents");
  }
  const parent = path.dirname(destination);
  await mkdir(parent, { recursive: true });
  const scratch = await mkdtemp(path.join(parent, ".seo-review-"));
  try {
    for (const [name, contents] of entries) await writeFile(path.join(scratch, name), contents, { flag: "wx" });
    await rename(scratch, destination);
  } catch (error) { await rm(scratch, { recursive: true, force: true }); throw error; }
  return destination;
}
