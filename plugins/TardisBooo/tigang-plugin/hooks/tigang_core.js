/**
 * 提肛提醒共享核心(node,零依赖)
 * 供各 agent 适配器(Claude Code / Codex / dsh / pi / …)复用:
 *   detectActions  — 从 shell 命令串识别 git commit / git push
 *   shouldSkip     — 根据 git 输出判断是否为无效操作(nothing to commit 等)
 *   bumpStats      — 累计统计(~/.claude/tigang-reminder/stats.json)
 *   pending 系列   — "待提醒"状态文件(回合结束时渲染)
 *   buildMessage   — 提醒文案(自动适配系统语言,TIGANG_LANG 可覆盖)
 */
"use strict";

const fs = require("fs");
const os = require("os");
const path = require("path");

// 测试时可用 TIGANG_STATE_DIR 重定向状态目录
const STATE_DIR =
  process.env.TIGANG_STATE_DIR ||
  path.join(os.homedir(), ".claude", "tigang-reminder");
const STATS_FILE = path.join(STATE_DIR, "stats.json");
const PENDING_FILE = path.join(STATE_DIR, "pending.json");
const PENDING_TTL_MS = 30 * 60 * 1000; // 超过 30 分钟的待提醒视为过期

// 把命令按 &&、||、;、|、换行拆段,逐段匹配 "git [全局选项] commit|push"
// 支持:git commit / git push / git -C path commit / git --no-pager push /
//       cd x && git push origin main / FOO=1 git commit 等
const GIT_ACTION_RE =
  /^(?:[A-Za-z_]\w*=\S+\s+)*git\s+(?:(?:-{1,2}[A-Za-z][\w-]*)(?:[=\s]\S+)?\s+)*(commit|push)\b/;

// git 输出中出现这些内容说明没有产生新的 commit / push,不提醒
const SKIP_PATTERNS = [
  "nothing to commit",
  "nothing added to commit",
  "no changes added to commit",
  "working tree clean",
  "everything up-to-date",
  "failed to push",
  "! [rejected]",
  "fatal:",
];

function detectActions(command) {
  const res = { commit: false, push: false };
  // 先剥掉引号内的内容,避免把"字符串里提到的 git push"误判为真实命令
  // (真实命令不受影响:git commit -m "msg" 剥掉 "msg" 后仍以 git commit 开头)
  const stripped = String(command)
    .replace(/'(?:[^'\\]|\\.)*'/g, "''")
    .replace(/"(?:[^"\\]|\\.)*"/g, '""');
  for (const seg of stripped.split(/&&|\|\||;|\||\n/)) {
    const m = seg.trim().match(GIT_ACTION_RE);
    if (m) res[m[1]] = true;
  }
  return res;
}

function shouldSkip(responseText) {
  const text = String(responseText || "").toLowerCase();
  return SKIP_PATTERNS.some((p) => text.includes(p));
}

function localDate(d) {
  const p = (n) => String(n).padStart(2, "0");
  return d.getFullYear() + "-" + p(d.getMonth() + 1) + "-" + p(d.getDate());
}

function loadJson(file, fallback) {
  try {
    return JSON.parse(fs.readFileSync(file, "utf8"));
  } catch (_) {
    return fallback;
  }
}

function saveJson(file, obj) {
  try {
    fs.mkdirSync(path.dirname(file), { recursive: true });
    fs.writeFileSync(file, JSON.stringify(obj, null, 2));
  } catch (_) {
    /* 写不进去就算了 */
  }
}

function bumpStats(actions) {
  const stats = loadJson(STATS_FILE, {});
  const today = localDate(new Date());
  if (stats.today !== today) {
    stats.today = today;
    stats.todayCount = 0;
  }
  stats.total = (stats.total || 0) + 1;
  stats.todayCount = (stats.todayCount || 0) + 1;
  if (actions.commit) stats.commit = (stats.commit || 0) + 1;
  if (actions.push) stats.push = (stats.push || 0) + 1;
  stats.last = new Date().toISOString();
  saveJson(STATS_FILE, stats);
  return stats;
}

/* ── 提醒文案多语言:自动识别系统语言,TIGANG_LANG 可强制覆盖 ── */

// 语言标签 → 目录键:zh_CN.UTF-8 → zh,zh-TW/zh-Hant → zh-TW,en_US → en …
function pickLang(tag) {
  const t = String(tag || "")
    .toLowerCase()
    .split(".")[0]
    .replace("_", "-");
  if (t.startsWith("zh")) {
    return /tw|hk|hant/.test(t) ? "zh-TW" : "zh";
  }
  if (t.startsWith("en")) return "en";
  if (t.startsWith("ja")) return "ja";
  if (t.startsWith("ko")) return "ko";
  if (t.startsWith("es")) return "es";
  return null; // 未覆盖语言 → 由调用方回退英文
}

let sysLang = null; // 系统语言只探测一次(TIGANG_LANG 每次都查,便于测试)

function detectLang() {
  const forced = pickLang(process.env.TIGANG_LANG || "");
  if (forced) return forced;
  if (!sysLang) {
    sysLang =
      // Unix 惯例:LC_ALL > LC_MESSAGES > LANG(形如 zh_CN.UTF-8)
      pickLang(process.env.LC_ALL || process.env.LC_MESSAGES || process.env.LANG || "") ||
      // Windows / macOS:ICU 报告的系统 locale(形如 zh-CN)
      pickLang(
        typeof Intl !== "undefined"
          ? Intl.DateTimeFormat().resolvedOptions().locale
          : ""
      ) ||
      "en"; // 探测不出就用英文(开源场景的通用回退)
  }
  return sysLang;
}

const MESSAGES = {
  zh: (e, v, t, d) =>
    `${e} [提肛提醒] 检测到一次 git ${v}!现在做一组提肛:收紧 3 秒 → 放松 3 秒,重复 10 次,自然呼吸不要憋气。(今日第 ${t} 次 / 累计第 ${d} 次)`,
  "zh-TW": (e, v, t, d) =>
    `${e} [提肛提醒] 偵測到一次 git ${v}!現在做一組提肛(凱格爾運動):收緊 3 秒 → 放鬆 3 秒,重複 10 次,自然呼吸不要憋氣。(今日第 ${t} 次 / 累計第 ${d} 次)`,
  en: (e, v, t, d) =>
    `${e} [Kegel break] Detected a git ${v}! Time for one set: squeeze 3s → release 3s, 10 reps — keep breathing naturally. (today ${t} · total ${d})`,
  ja: (e, v, t, d) =>
    `${e} [骨盤底トレーニング] git ${v} を検出しました!一組やりましょう:3秒締めて→3秒緩めて、10回。自然に呼吸してください。(今日 ${t} 回 / 累計 ${d} 回)`,
  ko: (e, v, t, d) =>
    `${e} [케겔 타임] git ${v} 감지! 한 세트 해보세요: 3초 조이고 → 3초 풀고, 10회. 숨은 자연스럽게. (오늘 ${t}회 · 누적 ${d}회)`,
  es: (e, v, t, d) =>
    `${e} [Pausa de Kegel] Detectado un git ${v}! Haz una serie: aprieta 3s → suelta 3s, 10 repeticiones, respirando con naturalidad. (hoy ${t} · total ${d})`,
};

function buildMessage(verbs, stats) {
  const verb =
    verbs.commit && verbs.push ? "commit + push" : verbs.commit ? "commit" : "push";
  const emoji = verbs.push ? "🚀" : "💪";
  const render = MESSAGES[detectLang()] || MESSAGES.en;
  return render(emoji, verb, stats.todayCount || 0, stats.total || 0);
}

/* ── pending:检测到 commit/push 后暂存,回合结束时渲染 ── */

function savePending(actions) {
  const pending = loadJson(PENDING_FILE, null);
  const fresh =
    pending && Date.now() - new Date(pending.at).getTime() < PENDING_TTL_MS
      ? pending
      : { commit: false, push: false };
  fresh.commit = fresh.commit || actions.commit;
  fresh.push = fresh.push || actions.push;
  fresh.at = Date.now();
  saveJson(PENDING_FILE, fresh);
}

/** 取走待提醒:有且新鲜时返回提醒文案,否则返回 null(总是清理文件) */
function takePendingMessage() {
  const pending = loadJson(PENDING_FILE, null);
  try {
    fs.unlinkSync(PENDING_FILE);
  } catch (_) {
    /* 无文件也正常 */
  }
  if (!pending || !(pending.commit || pending.push)) return null;
  if (Date.now() - new Date(pending.at).getTime() > PENDING_TTL_MS) return null;
  const stats = loadJson(STATS_FILE, {});
  return buildMessage(pending, stats);
}

/**
 * 通用"检测"入口:各适配器把 (命令串, git输出) 喂进来。
 * 返回 true 表示检测到了有效 commit/push(已计数并暂存待提醒)。
 */
function detect(command, responseText) {
  const actions = detectActions(command);
  if (!actions.commit && !actions.push) return false;
  if (shouldSkip(responseText)) return false;
  bumpStats(actions);
  savePending(actions);
  return true;
}

module.exports = {
  STATE_DIR,
  STATS_FILE,
  PENDING_FILE,
  PENDING_TTL_MS,
  detectActions,
  shouldSkip,
  bumpStats,
  buildMessage,
  savePending,
  takePendingMessage,
  detect,
  pickLang,
  detectLang,
};
