#!/usr/bin/env node

const { spawn } = require("node:child_process");
const path = require("node:path");
const fs = require("node:fs");
const os = require("node:os");

const pluginRoot = path.resolve(__dirname, "..");
const helperScript = path.join(pluginRoot, "scripts", "antigravity.ps1");
const devToolsPortFile = path.join(process.env.APPDATA || "", "Antigravity", "DevToolsActivePort");

const tools = [
  {
    name: "quick",
    description: "Preferred first call. Compact setup, live UI, and model-limit summary in one low-token report.",
    inputSchema: { type: "object", properties: {}, additionalProperties: false },
  },
  {
    name: "setup",
    description: "Verify Antigravity 2.0 local setup readiness: install path, runtime, Node.js, DevTools, and model-limit API.",
    inputSchema: { type: "object", properties: {}, additionalProperties: false },
  },
  {
    name: "doctor",
    description: "Alias for setup. Diagnose whether the local Antigravity bridge is ready.",
    inputSchema: { type: "object", properties: {}, additionalProperties: false },
  },
  {
    name: "status",
    description: "Report whether Antigravity is installed/running and the current DevTools port.",
    inputSchema: { type: "object", properties: {}, additionalProperties: false },
  },
  {
    name: "open",
    description: "Open Antigravity 2.0 if it is installed and not already running.",
    inputSchema: { type: "object", properties: {}, additionalProperties: false },
  },
  {
    name: "repair-live",
    description: "Restart Antigravity and wait for an inspectable DevTools page when live UI control is not ready.",
    inputSchema: { type: "object", properties: {}, additionalProperties: false },
  },
  {
    name: "inspect",
    description: "Inspect local Antigravity integration details, bundled helpers, and known binaries.",
    inputSchema: { type: "object", properties: {}, additionalProperties: false },
  },
  {
    name: "live",
    description: "Report the live Chromium DevTools connection and page list for UI inspection.",
    inputSchema: { type: "object", properties: {}, additionalProperties: false },
  },
  {
    name: "devtools-health",
    description: "Low-token fallback for antigravity-devtools transport errors. Reports live pages and the recommended recovery step.",
    inputSchema: { type: "object", properties: {}, additionalProperties: false },
  },
  {
    name: "submission-guide",
    description: "Compact guidance for reliably submitting Antigravity chat prompts through DevTools without invalid key names.",
    inputSchema: { type: "object", properties: {}, additionalProperties: false },
  },
  {
    name: "prepare-offload",
    description: "Default first call for nontrivial work. Decide offload, check live/model readiness, generate the compact handoff, and give submit instructions.",
    inputSchema: {
      type: "object",
      properties: {
        goal: { type: "string", description: "Task goal for Antigravity." },
        workspace: { type: "string", description: "Local workspace path or Antigravity project name." },
        statusFile: { type: "string", description: "Small artifact Antigravity should write.", default: "notes/antigravity-status.md" },
        nextStep: { type: "string", description: "Specific next action.", default: "Inspect the relevant files and write a compact status checkpoint." },
        hasWorkspaceWork: { type: "boolean", description: "Whether the task needs files, diffs, logs, browser state, or project context.", default: true },
        estimatedCodexInputTokens: { type: "number", description: "Rough Codex tokens needed if handled directly.", default: 2000 },
      },
      required: ["goal"],
      additionalProperties: false,
    },
  },
  {
    name: "submit-offload",
    description: "Fast path: prepare and submit a compact handoff into the currently selected Antigravity chat via direct CDP, avoiding repeated snapshots.",
    inputSchema: {
      type: "object",
      properties: {
        goal: { type: "string", description: "Task goal for Antigravity." },
        workspace: { type: "string", description: "Local workspace path or Antigravity project name." },
        statusFile: { type: "string", description: "Small artifact Antigravity should write.", default: "notes/antigravity-status.md" },
        nextStep: { type: "string", description: "Specific next action.", default: "Inspect the relevant files and write a compact status checkpoint." },
        expectedProject: { type: "string", description: "Optional visible project text that must be present before submit." },
        expectedChat: { type: "string", description: "Optional visible chat/conversation text that must be present before submit." },
        submit: { type: "boolean", description: "Set true to fill and click Send.", default: false },
        fillOnly: { type: "boolean", description: "Set true to fill the composer without clicking Send. Use only when the user wants a manual review before submit.", default: false },
      },
      required: ["goal", "submit"],
      additionalProperties: false,
    },
  },
  {
    name: "limits-summary",
    description: "Preferred quota check. Compact model availability summary without dumping full per-model JSON.",
    inputSchema: { type: "object", properties: {}, additionalProperties: false },
  },
  {
    name: "limits",
    description: "Read full Antigravity model quota/limit state from the local language server. Use limits-summary first to save tokens.",
    inputSchema: { type: "object", properties: {}, additionalProperties: false },
  },
  {
    name: "models",
    description: "Alias for limits. Read Antigravity model quota/limit state.",
    inputSchema: { type: "object", properties: {}, additionalProperties: false },
  },
  {
    name: "privacy",
    description: "Scan this plugin repository for obvious sensitive data before publishing.",
    inputSchema: { type: "object", properties: {}, additionalProperties: false },
  },
  {
    name: "handoff-template",
    description: "Generate a compact Antigravity offload prompt without reading files or using DevTools UI tokens.",
    inputSchema: {
      type: "object",
      properties: {
        goal: { type: "string", description: "Task goal for Antigravity." },
        workspace: { type: "string", description: "Local workspace path or project name." },
        statusFile: { type: "string", description: "Small artifact Antigravity should write.", default: "notes/antigravity-status.md" },
        nextStep: { type: "string", description: "Specific next action.", default: "Inspect the relevant files and write a compact status checkpoint." },
      },
      required: ["goal"],
      additionalProperties: false,
    },
  },
  {
    name: "offload-advice",
    description: "Cheap decision gate for whether Codex should offload a task to Antigravity or answer/act directly.",
    inputSchema: {
      type: "object",
      properties: {
        goal: { type: "string", description: "User task or intended Antigravity handoff." },
        hasWorkspaceWork: { type: "boolean", description: "Whether the task needs local project files, diffs, logs, or long workspace inspection.", default: false },
        estimatedCodexInputTokens: { type: "number", description: "Rough Codex tokens needed if handled directly.", default: 0 },
      },
      required: ["goal"],
      additionalProperties: false,
    },
  },
];

function sendMessage(message) {
  const body = Buffer.from(JSON.stringify(message), "utf8");
  process.stdout.write(`Content-Length: ${body.length}\r\n\r\n`);
  process.stdout.write(body);
}

function sendResult(id, result) {
  sendMessage({ jsonrpc: "2.0", id, result });
}

function sendError(id, code, message) {
  sendMessage({ jsonrpc: "2.0", id, error: { code, message } });
}

function runHelper(command) {
  return new Promise((resolve, reject) => {
    const child = spawn(
      "powershell.exe",
      ["-NoProfile", "-ExecutionPolicy", "Bypass", "-File", helperScript, command],
      { windowsHide: true }
    );

    let stdout = "";
    let stderr = "";
    child.stdout.on("data", (chunk) => {
      stdout += chunk.toString("utf8");
    });
    child.stderr.on("data", (chunk) => {
      stderr += chunk.toString("utf8");
    });
    child.on("error", reject);
    child.on("close", (code) => {
      if (code !== 0) {
        reject(new Error(stderr.trim() || `antigravity.ps1 ${command} exited with code ${code}`));
        return;
      }

      const text = stdout.trim();
      if (!text) {
        resolve("");
        return;
      }

      try {
        resolve(JSON.parse(text));
      } catch {
        resolve(text);
      }
    });
  });
}

function buildHandoffTemplate(args = {}) {
  const goal = String(args.goal || "<goal>").trim();
  const workspace = String(args.workspace || "<workspace/path>").trim();
  const statusFile = String(args.statusFile || "notes/antigravity-status.md").trim();
  const nextStep = String(args.nextStep || "Inspect the relevant files and write a compact status checkpoint.").trim();

  return [
    "Use this as a compact Antigravity offload handoff:",
    "",
    "```text",
    `Goal: ${goal}`,
    `Workspace: ${workspace}`,
    "Constraints: inspect files locally; do not paste full files, full logs, or full source; use search before reading whole files.",
    `Token rule: work token-efficiently; write progress to ${statusFile}; output max 10 bullets plus changed file list.`,
    `Next step: ${nextStep}`,
    "If blocked: ask one concise question; otherwise continue autonomously.",
    "```",
    "",
    "Codex follow-up rule: do not read the full Antigravity chat. Read only the status artifact, targeted diffs, or a compact visible UI status.",
  ].join("\n");
}

function getOffloadDecision(args = {}) {
  const goal = String(args.goal || "").trim();
  const hasWorkspaceWork = Boolean(args.hasWorkspaceWork);
  const estimatedCodexInputTokens = Number(args.estimatedCodexInputTokens || 0);
  const lowerGoal = goal.toLowerCase();
  const trivialPattern = /\b(2\s*\+\s*2|add\s+2\s*\+\s*2|what\s+is|time|date|summari[sz]e\s+this\s+short|one\s+line|yes\s+or\s+no)\b/;
  const workspacePattern = /\b(repo|workspace|project|files?|diff|logs?|tests?|build|lint|implement|refactor|debug|apply|continue\s+chat|job\s+search|browser|ui|analy[sz]e|review|plan|research|inspect|investigate|fix|patch|error|failure|trace|search|compare)\b/;

  const trivial = trivialPattern.test(lowerGoal) || (!hasWorkspaceWork && estimatedCodexInputTokens > 0 && estimatedCodexInputTokens < 400);
  const workspaceLikely = hasWorkspaceWork || workspacePattern.test(lowerGoal) || estimatedCodexInputTokens >= 800;
  const shouldOffload = workspaceLikely && !trivial;

  const decision = shouldOffload ? "offload-to-antigravity" : "codex-direct";
  const reason = shouldOffload
    ? "The task appears to benefit from Antigravity inspecting the local workspace or running longer reasoning while Codex reads back a compact artifact."
    : "The task is small enough that DevTools navigation, project context scanning, and Antigravity startup/agent overhead will likely cost more time and tokens than Codex answering directly.";

  return { decision, reason, shouldOffload };
}

function buildOffloadAdvice(args = {}) {
  const { decision, reason } = getOffloadDecision(args);
  return [
    `Decision: ${decision}`,
    `Reason: ${reason}`,
    "",
    "Rules:",
    "- Use Codex direct only for arithmetic, short factual answers, tiny commands, and small summaries.",
    "- Use Antigravity by default for nontrivial workspace tasks, UI/project continuation, job-search/application work, debugging, implementation, reviews, research, planning, and analysis that would make Codex read files or long output.",
    "- In existing project chats, assume Antigravity may scan attached folders. For small tests, use a blank/no-workspace chat when available or do not offload.",
    "- If Antigravity unexpectedly starts broad folder exploration for a small task, cancel and report that offload is not token-efficient.",
    "- When offloading, send a compact handoff and ask Antigravity to write a small status artifact; Codex should read only that artifact or a targeted diff.",
  ].join("\n");
}

function buildPrepareOffload(args = {}, quick = null) {
  const decision = getOffloadDecision(args);
  const handoff = buildHandoffTemplate(args).replace(/^Use this as a compact Antigravity offload handoff:\n\n/, "");
  const setup = quick?.Setup || {};
  const live = quick?.Live || {};
  const recommended = quick?.Limits?.RecommendedAvailable?.[0] || null;
  const readiness = [
    `Installed: ${setup.Installed === true}`,
    `Running: ${setup.Running === true}`,
    `LiveReady: ${setup.ReadyForLiveUiInspection === true}`,
    `PageCount: ${live.PageCount ?? "<unknown>"}`,
    `BestModel: ${recommended ? `${recommended.DisplayName || recommended.Id} (${recommended.RemainingPercent ?? "?"}% remaining)` : "<unknown>"}`,
  ].join("\n");

  const nextAction = decision.shouldOffload
    ? "Use antigravity-devtools only to select the project/chat/model, fill the handoff, and click the Send/arrow button. Then stop monitoring and read only the status artifact or targeted diff."
    : "Do not open or drive Antigravity for this task. Answer or act directly in Codex.";

  return [
    "FastAntigravityOffloadPlan:",
    `Decision: ${decision.decision}`,
    `Reason: ${decision.reason}`,
    "",
    "Readiness:",
    readiness,
    "",
    "NextAction:",
    nextAction,
    "",
    "SubmitRule:",
    "Fill/type the prompt without submitKey. Prefer clicking the visible Send/arrow button. If keyboard submit is required, use a separate simple Enter key call. Never use Control+Enter unless the active tool schema explicitly accepts it.",
    "",
    "CompactHandoff:",
    handoff,
  ].join("\n");
}

function getDevToolsPort() {
  if (!devToolsPortFile || !fs.existsSync(devToolsPortFile)) {
    throw new Error(`DevToolsActivePort not found at ${devToolsPortFile}`);
  }
  const firstLine = fs.readFileSync(devToolsPortFile, "utf8").split(/\r?\n/)[0]?.trim();
  if (!firstLine) {
    throw new Error("DevToolsActivePort exists but does not contain a port.");
  }
  return firstLine;
}

async function getAntigravityPage() {
  const port = getDevToolsPort();
  const pages = await fetch(`http://127.0.0.1:${port}/json/list`).then((response) => response.json());
  const page = pages.find((entry) => entry.type === "page" && entry.webSocketDebuggerUrl)
    || pages.find((entry) => entry.webSocketDebuggerUrl);
  if (!page) {
    throw new Error(`No inspectable Antigravity page found on DevTools port ${port}.`);
  }
  return { port, page };
}

function createCdpClient(webSocketDebuggerUrl) {
  return new Promise((resolve, reject) => {
    const ws = new WebSocket(webSocketDebuggerUrl);
    let nextId = 1;
    const pending = new Map();
    const timeout = setTimeout(() => reject(new Error("Timed out connecting to Antigravity DevTools WebSocket.")), 5000);

    ws.addEventListener("open", () => {
      clearTimeout(timeout);
      resolve({
        send(method, params = {}) {
          const id = nextId++;
          ws.send(JSON.stringify({ id, method, params }));
          return new Promise((sendResolve, sendReject) => {
            const timer = setTimeout(() => {
              pending.delete(id);
              sendReject(new Error(`CDP command timed out: ${method}`));
            }, 10000);
            pending.set(id, { resolve: sendResolve, reject: sendReject, timer });
          });
        },
        close() {
          try {
            ws.close();
          } catch {
            // Ignore close races.
          }
        },
      });
    });

    ws.addEventListener("message", (event) => {
      let message;
      try {
        message = JSON.parse(String(event.data));
      } catch {
        return;
      }
      if (!message.id || !pending.has(message.id)) {
        return;
      }
      const entry = pending.get(message.id);
      pending.delete(message.id);
      clearTimeout(entry.timer);
      if (message.error) {
        entry.reject(new Error(message.error.message || JSON.stringify(message.error)));
      } else {
        entry.resolve(message.result);
      }
    });

    ws.addEventListener("error", () => {
      clearTimeout(timeout);
      reject(new Error("Failed to connect to Antigravity DevTools WebSocket."));
    });
  });
}

function jsString(value) {
  return JSON.stringify(String(value ?? ""));
}

async function submitOffloadToCurrentChat(args = {}) {
  const { decision } = getOffloadDecision({ ...args, hasWorkspaceWork: true, estimatedCodexInputTokens: 2000 });
  if (decision !== "offload-to-antigravity") {
    return `SubmitOffload: skipped\nDecision: ${decision}\nReason: task does not need Antigravity.`;
  }

  const handoff = buildHandoffTemplate(args).replace(/^Use this as a compact Antigravity offload handoff:\n\n/, "");
  const expectedProject = String(args.expectedProject || "").trim();
  const expectedChat = String(args.expectedChat || "").trim();
  const submit = Boolean(args.submit);
  const fillOnly = Boolean(args.fillOnly);
  const { port, page } = await getAntigravityPage();
  const client = await createCdpClient(page.webSocketDebuggerUrl);

  const expression = `
(() => {
  const prompt = ${jsString(handoff)};
  const expectedProject = ${jsString(expectedProject)};
  const expectedChat = ${jsString(expectedChat)};
  const shouldSubmit = ${submit ? "true" : "false"};
  const shouldFillOnly = ${fillOnly ? "true" : "false"};
  const visibleText = document.body ? document.body.innerText || "" : "";
  const missing = [];
  if (expectedProject && !visibleText.includes(expectedProject)) missing.push("expectedProject");
  if (expectedChat && !visibleText.includes(expectedChat)) missing.push("expectedChat");
  if (missing.length) {
    return { ok: false, stage: "verify", missing, submitted: false };
  }

  if (!shouldSubmit && !shouldFillOnly) {
    return { ok: true, stage: "verified", submitted: false, promptLength: prompt.length };
  }

  const isVisible = (el) => {
    if (!el) return false;
    const rect = el.getBoundingClientRect();
    const style = getComputedStyle(el);
    return rect.width > 0 && rect.height > 0 && style.visibility !== "hidden" && style.display !== "none";
  };

  const candidates = Array.from(document.querySelectorAll('textarea,input,[contenteditable="true"],[role="textbox"],[role="combobox"]'))
    .filter((el) => isVisible(el) && !el.disabled && !el.readOnly)
    .sort((a, b) => b.getBoundingClientRect().bottom - a.getBoundingClientRect().bottom);
  const composer = candidates[0];
  if (!composer) {
    return { ok: false, stage: "composer", submitted: false, message: "No visible composer found." };
  }

  composer.focus();
  if (composer.matches('textarea,input')) {
    const setter = Object.getOwnPropertyDescriptor(Object.getPrototypeOf(composer), "value")?.set;
    if (setter) setter.call(composer, prompt);
    else composer.value = prompt;
    composer.dispatchEvent(new InputEvent("input", { bubbles: true, inputType: "insertText", data: prompt }));
    composer.dispatchEvent(new Event("change", { bubbles: true }));
  } else {
    document.execCommand("selectAll", false, null);
    const inserted = document.execCommand("insertText", false, prompt);
    if (!inserted) composer.textContent = prompt;
    composer.dispatchEvent(new InputEvent("input", { bubbles: true, inputType: "insertText", data: prompt }));
  }

  if (!shouldSubmit) {
    return { ok: true, stage: "filled", submitted: false, promptLength: prompt.length };
  }

  const composerRect = composer.getBoundingClientRect();
  const buttons = Array.from(document.querySelectorAll('button,[role="button"]'))
    .filter((el) => isVisible(el) && !el.disabled && el.getAttribute("aria-disabled") !== "true");
  const labeled = buttons.find((el) => /send|submit/i.test([el.ariaLabel, el.title, el.textContent].filter(Boolean).join(" ")));
  const nearby = buttons
    .filter((el) => {
      const rect = el.getBoundingClientRect();
      return rect.top >= composerRect.top - 80 && rect.bottom <= composerRect.bottom + 120 && rect.left > composerRect.left;
    })
    .sort((a, b) => b.getBoundingClientRect().right - a.getBoundingClientRect().right)[0];
  const sendButton = labeled || nearby;
  return {
    ok: true,
    stage: "filled-ready-for-enter",
    submitted: false,
    promptLength: prompt.length,
    hasSendButton: Boolean(sendButton)
  };
})()
`;

  try {
    const result = await client.send("Runtime.evaluate", {
      expression,
      awaitPromise: true,
      returnByValue: true,
    });
    let value = result?.result?.value || {};
    if (submit && value.ok === true && value.stage === "filled-ready-for-enter") {
      await client.send("Input.dispatchKeyEvent", {
        type: "rawKeyDown",
        key: "Enter",
        code: "Enter",
        windowsVirtualKeyCode: 13,
        nativeVirtualKeyCode: 13,
        unmodifiedText: "\r",
        text: "\r",
      });
      await client.send("Input.dispatchKeyEvent", {
        type: "keyUp",
        key: "Enter",
        code: "Enter",
        windowsVirtualKeyCode: 13,
        nativeVirtualKeyCode: 13,
      });
      await new Promise((resolve) => setTimeout(resolve, 500));
      const afterEnter = await client.send("Runtime.evaluate", {
        expression: `
(() => {
  const visibleText = document.body ? document.body.innerText || "" : "";
  const busy = /working|worked for|stop|cancel|running|thinking/i.test(visibleText);
  const composer = Array.from(document.querySelectorAll('textarea,input,[contenteditable="true"],[role="textbox"],[role="combobox"]'))
    .filter((el) => {
      const rect = el.getBoundingClientRect();
      const style = getComputedStyle(el);
      return rect.width > 0 && rect.height > 0 && style.visibility !== "hidden" && style.display !== "none";
    })
    .sort((a, b) => b.getBoundingClientRect().bottom - a.getBoundingClientRect().bottom)[0];
  const composerText = composer ? (composer.value || composer.innerText || composer.textContent || "") : "";
  return { busy, composerStillHasPrompt: composerText.includes(${jsString(handoff.slice(0, 80))}) };
})()
`,
        awaitPromise: true,
        returnByValue: true,
      });
      const afterValue = afterEnter?.result?.value || {};
      value = {
        ...value,
        stage: afterValue.composerStillHasPrompt ? "enter-dispatched-unconfirmed" : "enter-submitted",
        submitted: !afterValue.composerStillHasPrompt || afterValue.busy === true,
        enterDispatched: true,
        busy: afterValue.busy === true,
      };
    }
    return [
      "SubmitOffloadResult:",
      `DevToolsPort: ${port}`,
      `PageTitle: ${page.title || "<unknown>"}`,
      `Ok: ${value.ok === true}`,
      `Stage: ${value.stage || "<unknown>"}`,
      `Submitted: ${value.submitted === true}`,
      value.missing?.length ? `Missing: ${value.missing.join(", ")}` : null,
      value.message ? `Message: ${value.message}` : null,
      "Next: If Submitted is true, stop monitoring every UI step and read only the requested status artifact or targeted diff.",
    ].filter(Boolean).join("\n");
  } finally {
    client.close();
  }
}

function buildDevToolsHealthAdvice(result) {
  const pageCount = Number(result?.PageCount || 0);
  const running = Boolean(result?.Running);
  const port = result?.DevToolsPort || "<unknown>";
  const status = running && pageCount > 0 ? "ready" : "not-ready";
  const next = status === "ready"
    ? "If antigravity-devtools still says Transport closed, do not retry the same MCP transport. Restart Codex so the DevTools MCP server is re-created, or use handoff-template/manual paste for this turn."
    : "Run antigravity-local.repair-live once. If it restarts Antigravity, restart Codex before calling antigravity-devtools again.";

  return [
    `DevToolsHealth: ${status}`,
    `Running: ${running}`,
    `DevToolsPort: ${port}`,
    `PageCount: ${pageCount}`,
    `Next: ${next}`,
    "",
    "Rule: antigravity-local can report health even when antigravity-devtools/list_pages fails with Transport closed. A closed transport means the DevTools MCP child process died; it is not fixed by repeatedly calling list_pages in the same session.",
  ].join("\n");
}

function buildSubmissionGuide() {
  return [
    "AntigravitySubmissionGuide:",
    "1. Verify the target project, conversation, model, and idle composer first.",
    "2. Fill or type the prompt into the composer only. Do not include submitKey in the fill/type call.",
    "3. Prefer clicking the visible Send/arrow button after the composer contains the prompt.",
    "4. If a keyboard submit is required, use a separate key tool call with a simple accepted key such as Enter. Do not use Control+Enter, Ctrl+Enter, or chord strings unless the active tool schema explicitly lists that exact value.",
    "5. After submitting, verify Antigravity accepted the message by checking for a working/streaming state or a new visible user message.",
    "6. If the key or click fails once, stop retrying the same submit method. Report the blocker or use handoff-template for manual paste.",
    "",
    "Reason: some Codex DevTools tools reject chord strings like Control+Enter with Unknown key, even after the prompt was typed correctly.",
  ].join("\n");
}

async function handleRequest(message) {
  const { id, method, params } = message;

  if (method === "initialize") {
    sendResult(id, {
      protocolVersion: params?.protocolVersion || "2024-11-05",
      capabilities: { tools: {} },
      serverInfo: { name: "antigravity-local", version: "0.1.0" },
    });
    return;
  }

  if (method === "notifications/initialized") {
    return;
  }

  if (method === "tools/list") {
    sendResult(id, { tools });
    return;
  }

  if (method === "tools/call") {
    const name = params?.name;
    const tool = tools.find((entry) => entry.name === name);
    if (!tool) {
      sendError(id, -32602, `Unknown tool: ${name}`);
      return;
    }

    try {
      if (name === "handoff-template") {
        const text = buildHandoffTemplate(params?.arguments || {});
        sendResult(id, { content: [{ type: "text", text }] });
        return;
      }

      if (name === "offload-advice") {
        const text = buildOffloadAdvice(params?.arguments || {});
        sendResult(id, { content: [{ type: "text", text }] });
        return;
      }

      if (name === "devtools-health") {
        const result = await runHelper("live");
        const text = `${buildDevToolsHealthAdvice(result)}\n\nRaw live report:\n${JSON.stringify(result, null, 2)}`;
        sendResult(id, { content: [{ type: "text", text }] });
        return;
      }

      if (name === "submission-guide") {
        sendResult(id, { content: [{ type: "text", text: buildSubmissionGuide() }] });
        return;
      }

      if (name === "prepare-offload") {
        const quick = await runHelper("quick");
        const text = buildPrepareOffload(params?.arguments || {}, quick);
        sendResult(id, { content: [{ type: "text", text }] });
        return;
      }

      if (name === "submit-offload") {
        const text = await submitOffloadToCurrentChat(params?.arguments || {});
        sendResult(id, { content: [{ type: "text", text }] });
        return;
      }

      const command = name === "models" ? "limits" : name;
      const result = await runHelper(command);
      sendResult(id, {
        content: [
          {
            type: "text",
            text: typeof result === "string" ? result : JSON.stringify(result, null, 2),
          },
        ],
      });
    } catch (error) {
      sendError(id, -32000, error?.message || String(error));
    }
    return;
  }

  if (id !== undefined) {
    sendError(id, -32601, `Method not found: ${method}`);
  }
}

if (process.argv[2] === "submit-offload-cli") {
  let args = {};
  try {
    if (process.argv[3] === "--json-file") {
      args = JSON.parse(fs.readFileSync(process.argv[4], "utf8"));
    } else {
      args = process.argv[3] ? JSON.parse(process.argv[3]) : {};
    }
  } catch (error) {
    console.error(`Invalid submit-offload JSON: ${error?.message || String(error)}`);
    process.exit(2);
  }

  submitOffloadToCurrentChat(args)
    .then((text) => {
      console.log(text);
      process.exit(0);
    })
    .catch((error) => {
      console.error(error?.message || String(error));
      process.exit(1);
    });
  return;
}

let buffer = Buffer.alloc(0);

process.stdin.on("data", (chunk) => {
  buffer = Buffer.concat([buffer, chunk]);

  while (true) {
    const headerEnd = buffer.indexOf("\r\n\r\n");
    if (headerEnd === -1) {
      return;
    }

    const headers = buffer.slice(0, headerEnd).toString("utf8");
    const match = headers.match(/Content-Length:\s*(\d+)/i);
    if (!match) {
      buffer = buffer.slice(headerEnd + 4);
      continue;
    }

    const contentLength = Number.parseInt(match[1], 10);
    const messageStart = headerEnd + 4;
    const messageEnd = messageStart + contentLength;
    if (buffer.length < messageEnd) {
      return;
    }

    const payload = buffer.slice(messageStart, messageEnd).toString("utf8");
    buffer = buffer.slice(messageEnd);

    try {
      const message = JSON.parse(payload);
      handleRequest(message).catch((error) => {
        if (message.id !== undefined) {
          sendError(message.id, -32000, error?.message || String(error));
        }
      });
    } catch (error) {
      sendError(null, -32700, error?.message || "Parse error");
    }
  }
});
