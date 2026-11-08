#!/usr/bin/env node
// frugal nudge: a tiny, local, zero-dependency hook.
//
// UserPromptSubmit: if the prompt looks like it involves spending money, add one line of context
//   that reminds the agent to run the frugal skill. Prints plain text (Claude Code and Codex both
//   add a UserPromptSubmit hook's stdout to the context).
// PostToolUse: if a browser tool just opened a pricing, plans, cart, checkout or billing page, add
//   the same reminder as JSON additionalContext (Claude Code).
//
// It never blocks, never calls a model, never sends anything anywhere, and stays quiet when unsure.
// Turn it off with FRUGAL_HOOK=off, or by saying "skip frugal" / "just buy it" in the prompt.

import { mkdirSync, readFileSync, writeFileSync } from "node:fs";
import { tmpdir } from "node:os";
import { join } from "node:path";
import { pathToFileURL } from "node:url";

// Phrases that almost always mean money is about to be spent, or the user wants to spend less.
// Tuned for precision: a missed nudge costs nothing (the skill still triggers on its description),
// a wrong one costs the agent one line to ignore.
const SPEND_PATTERNS = [
  /\b(i|we)('d| would| want to| need to| wanna| will|'ll| should| plan to| am going to| are going to)?\s+(like to\s+)?(buy|purchase|order|subscribe to|upgrade|renew|book|rent|pay for)\b/i,
  /\b(buy|purchase)\b(?!\s*(button|flow|page|endpoint|api|event|component|modal|form|link|cta|handler|webhook)s?\b)/i,
  /\b(coupon|promo ?codes?|vouchers?|discount codes?|cashback|cash back|referral codes?)\b/i,
  /\b(too expensive|overpriced|cheaper (option|alternative|plan|way|version|one|provider|host)|cheapest|save money|lower (our|my|the) bill|cut (our|my|the) (bill|costs?|spend(ing)?))\b/i,
  /\badd(ed)? to (the |my )?cart\b/i,
  /\b(book|booking|reserve)\b.{0,40}\b(flights?|hotels?|airbnb|tickets?|rooms?|car rental|rental car|train)\b/i,
  /\b(flights?|airfares?|hotels?|airbnbs?|car rentals?)\b.{0,60}\b(jan|feb|mar|apr|may|jun|jul|aug|sep|sept|oct|nov|dec|january|february|march|april|june|july|august|september|october|november|december|economy|business class|round[- ]trip|one[- ]way|nights?|weekend|next week)\b/i,
  /\bwhere (should|can|do|to) (i |we )?(buy|get|order|purchase)\b/i,
  /\bsign(ing)? (me |us )?up (for|to)\b(?!.{0,15}\b(form|page|flow|button|screen|endpoint)s?\b)/i,
  /\b(video|youtube|tutorial|course|guide|influencer)\b.{0,80}\b(says to (use|buy|start|get|sign up)|told (me|us) to (use|buy|get|sign up)|recommends? (buying|subscribing|signing up))\b/i,
  /\b(best price|best deal|lowest price|good deal|price drop)\b/i,
  /\b(free trial|paid plan|annual plan|monthly plan|yearly plan)\b/i,
  /\bupgrade\b.{0,30}\b(pro|plus|premium|team|business|enterprise|max|paid)\b/i,
  /\b(renew|renewal)\b.{0,30}\b(subscription|plan|license|licence|domain|membership|contract|insurance|lease)\b/i,
  /\bsubscri(be|bing|ption)\b.{0,30}\b(plan|pro|plus|premium|monthly|yearly|annual|membership)\b/i,
  /\b(how much|what)\b.{0,15}\b(does|do|would|will|is)\b.{0,40}\b(cost|charge|price)\b/i,
  /[$€£₪]\s?\d[\d,.]*\s*(\/|per|a)\s*(mo|month|yr|year|seat|user)\b/i,
  /\b\d[\d,.]*\s?(usd|eur|gbp|ils|nis|dollars|euros|pounds|shekels?)\b/i,
  /(לקנות|לרכוש|להזמין|מנוי|קופון|הנחה|הנחות|זול יותר|הכי זול|יקר מדי|טיסה|טיסות|מלון|לשלם על)/,
];

const OPT_OUT = /\b(skip frugal|no frugal|without frugal|just buy( it)?|don'?t (look for|search for) (deals|discounts))\b/i;

// URL paths that mean a pricing or payment page is open.
const MONEY_PAGE = /\/(checkout|cart|basket|bag|billing|pricing|plans?|upgrade|subscribe|subscription|payment|pay|purchase|buy|order|booking)(\/|\?|#|$|[-_.])/i;

const NAV_TOOL = /(navigate|navigate_page|new_page|open_url|preview_start|browser_batch|tabs_create)/i;

const QUIET_MINUTES = 20;

function readStdin() {
  try {
    return readFileSync(0, "utf8");
  } catch {
    return "";
  }
}

function statePath(sessionId) {
  const dir = join(tmpdir(), "frugal-hook");
  mkdirSync(dir, { recursive: true });
  return join(dir, `${String(sessionId || "default").replace(/[^\w.-]/g, "_")}.json`);
}

function loadState(sessionId) {
  try {
    return JSON.parse(readFileSync(statePath(sessionId), "utf8"));
  } catch {
    return {};
  }
}

function saveState(sessionId, state) {
  try {
    writeFileSync(statePath(sessionId), JSON.stringify(state));
  } catch {
    // State is a nicety; never fail the hook over it.
  }
}

export function spendMatch(prompt) {
  const text = String(prompt || "");
  if (!text.trim() || OPT_OUT.test(text)) return null;
  // Long pasted code or logs are rarely a purchase request.
  const codeFences = (text.match(/```/g) || []).length;
  if (codeFences >= 2 && text.length > 1500) return null;
  for (const pattern of SPEND_PATTERNS) {
    const m = text.match(pattern);
    if (m) return m[0].trim();
  }
  return null;
}

export function collectUrls(value, out = []) {
  if (typeof value === "string") {
    if (/^https?:\/\//i.test(value)) out.push(value);
  } else if (Array.isArray(value)) {
    for (const v of value) collectUrls(v, out);
  } else if (value && typeof value === "object") {
    for (const v of Object.values(value)) collectUrls(v, out);
  }
  return out;
}

export function moneyPage(toolName, toolInput) {
  if (!NAV_TOOL.test(String(toolName || ""))) return null;
  for (const raw of collectUrls(toolInput)) {
    let url;
    try {
      url = new URL(raw);
    } catch {
      continue;
    }
    if (["localhost", "127.0.0.1", "[::1]"].includes(url.hostname)) continue;
    if (MONEY_PAGE.test(url.pathname + url.search)) return { host: url.hostname, path: url.pathname };
  }
  return null;
}

export function promptNudge(match) {
  return (
    `frugal: this request may involve spending money (matched "${match}"). ` +
    `If it does, run the frugal skill before money is committed, sized to the amount ` +
    `(skip it if the user said to just buy, or the spend is tiny). If it does not, ignore this line.`
  );
}

export function pageNudge(page) {
  return (
    `frugal: a pricing or payment page is open (${page.host}${page.path}). ` +
    `Before anything is bought or upgraded, run the frugal skill once for this purchase: ` +
    `cheaper plan, programs, verified codes, alternatives. Never pay without the user's explicit yes.`
  );
}

function main() {
  if (String(process.env.FRUGAL_HOOK || "").toLowerCase() === "off") return;
  let payload = {};
  try {
    payload = JSON.parse(readStdin() || "{}");
  } catch {
    return;
  }
  const event = payload.hook_event_name || (payload.prompt !== undefined ? "UserPromptSubmit" : "");
  const sessionId = payload.session_id;
  const state = loadState(sessionId);
  const now = Date.now();

  if (event === "UserPromptSubmit") {
    const match = spendMatch(payload.prompt);
    if (!match) return;
    if (state.lastPrompt && now - state.lastPrompt < QUIET_MINUTES * 60_000) return;
    state.lastPrompt = now;
    saveState(sessionId, state);
    process.stdout.write(promptNudge(match) + "\n");
    return;
  }

  if (event === "PostToolUse") {
    const page = moneyPage(payload.tool_name, payload.tool_input);
    if (!page) return;
    state.hosts = state.hosts || {};
    if (state.hosts[page.host]) return;
    state.hosts[page.host] = now;
    saveState(sessionId, state);
    process.stdout.write(
      JSON.stringify({
        hookSpecificOutput: { hookEventName: "PostToolUse", additionalContext: pageNudge(page) },
      }) + "\n",
    );
  }
}

if (process.argv[1] && import.meta.url === pathToFileURL(process.argv[1]).href) {
  try {
    main();
  } catch {
    // A nudge hook must never break the agent.
  }
  process.exit(0);
}
