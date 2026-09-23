import { spawnSync } from "node:child_process";
import { mkdtempSync, writeFileSync, chmodSync } from "node:fs";
import { tmpdir } from "node:os";
import { join, dirname } from "node:path";
import { fileURLToPath } from "node:url";
import assert from "node:assert/strict";
import { test } from "node:test";
import { extractFilePath } from "./read-hook.mjs";

const SCRIPT = join(dirname(fileURLToPath(import.meta.url)), "read-hook.mjs");
const DOC = "/tmp/example.md";

function runHook(payload, { transpileStdout = "<B>bridge</B>\n" } = {}) {
  const dir = mkdtempSync(join(tmpdir(), "read-hook-"));
  const fake = join(dir, "transpile");
  writeFileSync(fake, `#!/usr/bin/env node\nprocess.stdout.write(${JSON.stringify(transpileStdout)});\n`);
  chmodSync(fake, 0o755);
  return spawnSync(process.execPath, [SCRIPT], {
    input: JSON.stringify(payload),
    encoding: "utf8",
    env: { ...process.env, PATH: `${dir}:${process.env.PATH || ""}` },
    timeout: 5000,
  });
}

test("claude Read uses tool_input.file_path", () => {
  assert.equal(
    extractFilePath(JSON.stringify({
      hook_event_name: "PreToolUse",
      tool_name: "Read",
      tool_input: { file_path: DOC },
    })),
    DOC,
  );
});

test("codex Read uses tool_input.file_path", () => {
  assert.equal(
    extractFilePath(JSON.stringify({
      tool_name: "Read",
      tool_input: { file_path: DOC },
    })),
    DOC,
  );
});

test("grok read_file uses toolInput.target_file", () => {
  assert.equal(
    extractFilePath(JSON.stringify({
      hook_event_name: "PreToolUse",
      toolName: "read_file",
      toolInput: { target_file: DOC },
    })),
    DOC,
  );
});

test("grok docs envelope with toolInput.path still works", () => {
  assert.equal(
    extractFilePath(JSON.stringify({
      toolInput: { path: DOC },
    })),
    DOC,
  );
});

test("agy view_file uses toolCall.args.AbsolutePath", () => {
  assert.equal(
    extractFilePath(JSON.stringify({
      conversationId: "ec33ebf9-0cba-4100-8142-c61503f6c587",
      toolCall: {
        name: "view_file",
        args: { AbsolutePath: DOC, toolAction: "Viewing" },
      },
    })),
    DOC,
  );
});

test("agy camelCase absolutePath is accepted", () => {
  assert.equal(
    extractFilePath(JSON.stringify({
      toolCall: { name: "view_file", args: { absolutePath: DOC } },
    })),
    DOC,
  );
});

test("specific path keys win over a generic path field", () => {
  assert.equal(
    extractFilePath(JSON.stringify({
      tool_input: { path: "/wrong.txt", file_path: DOC },
    })),
    DOC,
  );
});

test("malformed JSON and missing path fail open as empty", () => {
  assert.equal(extractFilePath("not-json"), "");
  assert.equal(extractFilePath("{}"), "");
  assert.equal(extractFilePath(JSON.stringify({ tool_input: { file_path: 1 } })), "");
});

test("claude payload denies with hookSpecificOutput", () => {
  const result = runHook({
    hook_event_name: "PreToolUse",
    tool_name: "Read",
    tool_input: { file_path: DOC },
  });
  assert.equal(result.status, 0, result.stderr);
  const out = JSON.parse(result.stdout);
  assert.equal(out.hookSpecificOutput.permissionDecision, "deny");
  assert.equal(out.hookSpecificOutput.permissionDecisionReason, "<B>bridge</B>");
});

test("grok target_file payload denies with hookSpecificOutput", () => {
  const result = runHook({
    toolName: "read_file",
    toolInput: { target_file: DOC },
  });
  assert.equal(result.status, 0, result.stderr);
  const out = JSON.parse(result.stdout);
  assert.equal(out.hookSpecificOutput.permissionDecision, "deny");
  assert.equal(out.hookSpecificOutput.permissionDecisionReason, "<B>bridge</B>");
});

test("agy payload denies with top-level decision/reason", () => {
  const result = runHook({
    toolCall: { name: "view_file", args: { AbsolutePath: DOC } },
  });
  assert.equal(result.status, 0, result.stderr);
  const out = JSON.parse(result.stdout);
  assert.equal(out.decision, "deny");
  assert.equal(out.reason, "<B>bridge</B>");
  assert.equal(out.hookSpecificOutput, undefined);
});

test("non-compressible files produce no stdout", () => {
  const result = runHook({
    tool_input: { file_path: "/tmp/example.rs" },
  });
  assert.equal(result.status, 0, result.stderr);
  assert.equal(result.stdout, "");
});
