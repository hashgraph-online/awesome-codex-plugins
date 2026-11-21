import test from "node:test";
import assert from "node:assert/strict";
import { mkdtemp, mkdir, readFile, symlink, rm, readdir, writeFile } from "node:fs/promises";
import path from "node:path";
import { tmpdir } from "node:os";

const api = await import("../lib/offline-reports.mjs").catch(() => ({}));

test("offline reports render source-controlled Markdown as inert text", () => {
  assert.equal(typeof api.markdownText, "function", "offline report text formatter is absent");
  const text = api.markdownText('![link](https://evil.test) <img> | `x`\\\nnext');
  assert.ok(!text.includes("![link]("));
  assert.ok(!text.includes("<img>"));
  assert.ok(!text.includes("|"));
  assert.ok(!text.includes("\n"));
});

test("offline report bundle writes a fresh directory and refuses existing output", async () => {
  assert.equal(typeof api.writeOfflineReports, "function", "offline report writer is absent");
  const root = await mkdtemp(path.join(tmpdir(), "offline-output-"));
  try {
    const repo = path.join(root, "repo"); await mkdir(repo);
    const out = path.join(repo, "reports", "one");
    await api.writeOfflineReports(out, { "result.json": '{"ok":true}\n', "result.md": "A report\n" }, repo);
    assert.equal(await readFile(path.join(out, "result.md"), "utf8"), "A report\n");
    await assert.rejects(api.writeOfflineReports(out, { "result.md": "replacement" }, repo), /exists|existing/i);
    assert.equal(await readFile(path.join(out, "result.md"), "utf8"), "A report\n");
  } finally { await rm(root, { recursive: true, force: true }); }
});

test("offline reports refuse protected source and symlink ancestors before creating directories", async () => {
  assert.equal(typeof api.writeOfflineReports, "function", "offline report writer is absent");
  const root = await mkdtemp(path.join(tmpdir(), "offline-protect-"));
  try {
    const repo = path.join(root, "repo"); const source = path.join(repo, "src");
    await mkdir(source, { recursive: true });
    await mkdir(path.join(repo, "reports"));
    await symlink(source, path.join(repo, "reports", "alias"));
    for (const output of [path.join(source, "new"), path.join(repo, "reports", "alias", "new", "out")]) {
      await assert.rejects(api.writeOfflineReports(output, { "result.md": "bad" }, repo), /source|reports/i);
    }
    assert.deepEqual(await readdir(source), []);
    await writeFile(path.join(root, "input.json"), "input");
    await assert.rejects(api.writeOfflineReports(path.join(root, "input.json"), { "result.md": "bad" }, repo), /exists|existing/i);
  } finally { await rm(root, { recursive: true, force: true }); }
});
