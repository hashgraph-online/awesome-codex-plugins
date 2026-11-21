#!/usr/bin/env node
/**
 * 提肛提醒 — Claude Code 插件入口(node,零依赖)
 *
 * 两个入口:
 *   PostToolUse (matcher: Bash) → tigang_hook.js detect   [默认模式]
 *     检测 git commit / git push,累计统计,把"待提醒"写入 pending.json。
 *     不产生任何 stdout → 完全不进入模型上下文,零 token 消耗。
 *
 *   Stop → tigang_hook.js remind
 *     若存在新鲜的 pending,输出 systemMessage —— 由终端渲染在 AI 回答的
 *     末尾(显示层追加,不经过模型,零 token),然后清除 pending。
 *
 * 设计原则:任何异常都静默退出(exit 0),绝不阻塞 git / 会话。
 */
"use strict";

const core = require("./tigang_core");

/* PostToolUse:检测 commit/push → 统计 + 记录待提醒,零 stdout */
function detectMode(raw) {
  let event;
  try {
    event = JSON.parse(raw);
  } catch (_) {
    return;
  }
  const command = (event.tool_input && event.tool_input.command) || "";
  const resp = event.tool_response || {};
  const exitCode = resp.exit_code ?? resp.exitCode;
  if (resp.isError || (typeof exitCode === "number" && exitCode !== 0)) return;
  if (typeof resp === "string" && /^error:/im.test(resp)) return;
  core.detect(command, typeof resp === "string" ? resp : JSON.stringify(resp));
  // 故意不输出任何内容:不进模型上下文,零 token
}

/* Stop:回答结束时把提醒显示层追加到 AI 回答末尾 */
function remindMode() {
  const message = core.takePendingMessage();
  if (message) {
    process.stdout.write(JSON.stringify({ systemMessage: message }));
  }
}

let raw = "";
process.stdin.setEncoding("utf8");
process.stdin.on("data", (c) => (raw += c));
process.stdin.on("end", () => {
  try {
    if (process.argv[2] === "remind") remindMode();
    else detectMode(raw);
  } catch (_) {
    /* 静默失败 */
  }
  process.exit(0);
});
