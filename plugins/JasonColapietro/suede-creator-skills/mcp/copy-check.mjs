// Deterministic copy checks for the Suede AI Skills MCP.
//
// The rules come from the pack's own copy skills: the house bans and kill list
// in skills/suede-deslop, the pre-ship checklist in skills/suede-copy, and the
// sales-copy rule that bans hedging. Each finding carries a severity that
// follows suede-deslop's signal strength: "act on one sighting" rules are
// medium or high, "weak alone" rules are low and only add up when several share
// the passage.

import { letterGrade } from "./page-audit.mjs";

const HOUSE_BANS = [
  [/—/g, "Em dash", "Use a period, comma, colon or parentheses."],
  [/\bmoreover\b/gi, '"moreover"', 'Cut it, or use "also" if the link is needed.'],
  [/\bdelv(e|es|ed|ing)( into)?\b/gi, '"delve"', "Use cover, examine or get into."],
  [/\bgame[- ]?changer\b/gi, '"game-changer"', "Name the change and its size."],
  [/\b(unlock|unleash)(es|ed|ing|s)?\b/gi, '"unlock/unleash"', "Say what was blocked and what now works."],
  [/\belevat(e|es|ed|ing)\b/gi, '"elevate"', "Say what changes, before and after."],
  [/\bseamless(ly)?\b/gi, '"seamless"', "Name the step count or the handoff that disappeared."],
  [/\btapestry\b/gi, '"tapestry"', "Cut the metaphor and name the parts."],
  [/\bit'?s important to note\b/gi, '"it\'s important to note"', "Cut it and state the point."],
  [/\b(the|today'?s|digital|competitive|business|ever-changing|evolving) landscape\b|\blandscape of\b/gi, 'Abstract "landscape"', "Name the market, field or thing."]
];

const HEDGES = [
  /\b(may|might|could) (help|improve|increase|boost|be able)\b/gi,
  /\bcan help\b/gi,
  /\bhelps? (you|businesses|teams|brands)\b/gi,
  /\b(aims?|tries|try|strives?) to\b/gi,
  /\bresults (may )?vary\b/gi,
  /\bhopefully\b/gi,
  /\bwe (think|believe|feel)\b/gi,
  /\b(honest|important) (limits|caveats)\b/gi,
  /\bnot (the first choice|a fit|for everyone)\b/gi,
  /\b(just|simply|basically|merely)\b/gi,
  /\b(potentially|possibly|perhaps)\b/gi
];

const VAGUE = [
  /\bworld[- ]class\b/gi, /\bbest[- ]in[- ]class\b/gi, /\bcutting[- ]edge\b/gi, /\bstate[- ]of[- ]the[- ]art\b/gi,
  /\brevolutionary\b/gi, /\binnovative\b/gi, /\bnext[- ]level\b/gi, /\bleverag(e|es|ed|ing)\b/gi, /\bempower(s|ed|ing)?\b/gi,
  /\bsynerg(y|ies|istic)\b/gi, /\bholistic\b/gi, /\bend[- ]to[- ]end solutions?\b/gi, /\b(innovative|tailored|custom|complete) solutions?\b/gi,
  /\bgrow your business\b/gi, /\btake (it|your \w+) to the next level\b/gi, /\bin today'?s (fast[- ]paced|digital) world\b/gi
];

const OPENERS = [
  /^here'?s (the thing|what|this|that|why)\b/i, /^let'?s (be honest|face it)\b/i, /^the (truth|reality) is\b/i,
  /^it turns out\b/i, /^let me be clear\b/i, /^it'?s worth noting\b/i, /^at the end of the day\b/i,
  /^when it comes to\b/i, /^picture this\b/i, /^imagine this\b/i, /^at its core\b/i
];

const CTA_START = /^(get|start|book|try|buy|shop|order|download|install|join|sign up|subscribe|schedule|call|contact|request|claim|see|run|grade|audit|apply|register|create|launch|hire|talk to|email|reply|grab|reserve|watch|read|explore)\b/i;
const CTA_INLINE = /\b(get|start|book|try|download|install|join|sign up|subscribe|schedule|call|contact|request|claim|run|grade|audit)\s+(your|my|a|an|the|now|today|free|it)\b/i;

const PASSIVE = /\b(am|is|are|was|were|be|been|being)\s+(\w+ly\s+)?(\w+ed|built|made|done|given|known|shown|seen|written|taken|sent|found|run|held|kept|left|paid|put|set|told|won)\b/gi;

function sentencesOf(text) {
  return text
    .replace(/\s+/g, " ")
    .split(/(?<=[.!?])\s+(?=[A-Z0-9"'(])|\n+/)
    .map((s) => s.trim())
    .filter((s) => /[a-z0-9]/i.test(s));
}

function syllables(word) {
  const clean = word.toLowerCase().replace(/[^a-z]/g, "");
  if (!clean) return 0;
  if (clean.length <= 3) return 1;
  const groups = clean.replace(/(?:[^laeiouy]es|ed|[^laeiouy]e)$/, "").replace(/^y/, "").match(/[aeiouy]{1,2}/g);
  return Math.max(1, groups ? groups.length : 1);
}

function excerpt(text, index, length) {
  const start = Math.max(0, index - 30);
  const end = Math.min(text.length, index + length + 30);
  return `${start > 0 ? "..." : ""}${text.slice(start, end).replace(/\s+/g, " ").trim()}${end < text.length ? "..." : ""}`;
}

function collect(text, pattern, limit = 5) {
  const hits = [];
  pattern.lastIndex = 0;
  let match;
  while ((match = pattern.exec(text)) && hits.length < limit) {
    hits.push({ match: match[0], index: match.index });
    if (match[0].length === 0) pattern.lastIndex += 1;
  }
  return hits;
}

const PENALTY = { high: 8, medium: 4, low: 2 };

export function checkCopy(input, { primaryAction, houseStyle = true } = {}) {
  // Curly apostrophes and quotes are the same length as straight ones, so
  // normalizing them keeps every match index valid for the excerpts.
  const text = String(input || "").replace(/[\u2018\u2019]/g, "'").replace(/[\u201c\u201d]/g, '"');
  const findings = [];
  const add = (rule, severity, hits, suggestion) => {
    if (!hits.length) return;
    findings.push({
      rule,
      severity,
      count: hits.length,
      examples: hits.slice(0, 3).map((hit) => (typeof hit === "string" ? hit : excerpt(text, hit.index, hit.match.length))),
      suggestion
    });
  };

  if (houseStyle) {
    for (const [pattern, label, fix] of HOUSE_BANS) add(`House ban: ${label}`, "high", collect(text, pattern), fix);
    const exclaims = collect(text, /[a-z0-9)]!+/gi);
    add("Promotional exclamation point", "medium", exclaims, "Use a period. Let the claim carry the energy.");
  }
  const hedges = HEDGES.flatMap((pattern) => collect(text, pattern));
  add("Hedge or softener", hedges.length >= 3 ? "high" : "medium", hedges, "State the outcome directly: \"cuts your reply time to 2 minutes\", not \"can help you reply faster\".");
  add("Vague or buzzword claim", "medium", VAGUE.flatMap((pattern) => collect(text, pattern)), "Replace it with the specific result, number or mechanism. If a competitor could say the same line, it is not specific enough.");

  const sentences = sentencesOf(text);
  const opener = sentences.filter((s) => OPENERS.some((pattern) => pattern.test(s)));
  add("Throat-clearing opener", "medium", opener.map((s) => s.slice(0, 80)), "Cut the opener and start with the point.");
  const whStart = sentences.filter((s) => /^(what|when|where|which|who|why|how)\b/i.test(s) && !/\?\s*$/.test(s));
  add("Sentence opens with a Wh- word", "low", whStart.map((s) => s.slice(0, 80)), "Restructure so the sentence starts with the subject or the result.");
  const contrast = collect(text, /\bnot (just |only )?[^.,;!?]{1,40}[,;] (it'?s|but|it is)\b/gi);
  add('"Not X, it\'s Y" contrast', "medium", contrast, "State Y directly.");
  const passive = collect(text, PASSIVE, 10);
  if (passive.length >= 2) add("Passive voice", "low", passive, "Name who does the action: \"we ship it in a day\", not \"it is shipped in a day\".");

  const wordList = text.match(/[A-Za-z0-9'][A-Za-z0-9'-]*/g) || [];
  const wordCount = wordList.length;
  const sentenceCount = Math.max(1, sentences.length);
  const avgSentence = wordCount / sentenceCount;
  const longSentences = sentences.filter((s) => (s.match(/\S+/g) || []).length > 30);
  add("Sentence over 30 words", "low", longSentences.map((s) => `${s.slice(0, 80)}...`), "Split it. One idea per sentence.");
  const syllableCount = wordList.reduce((sum, word) => sum + syllables(word), 0);
  const readingGrade = wordCount ? Math.max(0, Math.round((0.39 * avgSentence + 11.8 * (syllableCount / wordCount) - 15.59) * 10) / 10) : 0;
  if (wordCount >= 40 && readingGrade > 10) {
    findings.push({ rule: "Reading level", severity: "low", count: 1, examples: [`grade ${readingGrade}`], suggestion: "Aim for grade 8 or lower on sales copy: shorter sentences, plainer words." });
  }

  const hasCta = sentences.some((s) => CTA_START.test(s)) || CTA_INLINE.test(text);
  if (wordCount >= 12 && !hasCta) {
    findings.push({ rule: "No call to action", severity: "high", count: 1, examples: [], suggestion: "End with one next step that names the payoff, such as \"Get your free audit\"." });
  }
  if (primaryAction) {
    const wanted = (primaryAction.toLowerCase().match(/[a-z0-9]+/g) || []).filter((w) => w.length > 2);
    const have = new Set(text.toLowerCase().match(/[a-z0-9]+/g) || []);
    const present = wanted.length && wanted.filter((w) => have.has(w)).length >= Math.ceil(wanted.length / 2);
    if (!present) findings.push({ rule: "Primary action missing", severity: "high", count: 1, examples: [primaryAction], suggestion: `Say "${primaryAction}" in the copy and on the button.` });
  }
  const numbers = (text.match(/\d/g) || []).length;
  if (wordCount >= 60 && numbers === 0) {
    findings.push({ rule: "No specific number", severity: "low", count: 1, examples: [], suggestion: "Add one concrete figure the copy can back: a time, a count, a price or a result." });
  }
  const you = (text.match(/\b(you|your|yours)\b/gi) || []).length;
  const we = (text.match(/\b(we|our|us|ours)\b/gi) || []).length;
  if (wordCount >= 30 && we > you) {
    findings.push({ rule: "Writer-focused", severity: "medium", count: 1, examples: [`we/our ${we} vs you/your ${you}`], suggestion: "Turn \"we do X\" into \"you get Y\". Lead with the reader's result." });
  }

  const penalty = findings.reduce((sum, finding) => {
    const per = PENALTY[finding.severity];
    // Repeats of one weak signal count less than a spread of distinct problems.
    return sum + per + Math.min(finding.count - 1, 3) * (per / 2);
  }, 0);
  // Four problems in one short line is worse than four across a page, so short
  // copy weighs each finding more, up to double under 20 words.
  const density = wordCount && wordCount < 40 ? Math.min(2, 40 / Math.max(wordCount, 20)) : 1;
  const score = Math.max(0, Math.round(100 - penalty * density));
  const order = { high: 0, medium: 1, low: 2 };
  findings.sort((a, b) => order[a.severity] - order[b.severity] || b.count - a.count);
  return {
    score,
    grade: letterGrade(score),
    metrics: {
      words: wordCount,
      sentences: sentences.length,
      avgSentenceWords: Math.round(avgSentence * 10) / 10,
      readingGrade,
      youCount: you,
      weCount: we,
      numbers,
      hasCallToAction: hasCta
    },
    findings
  };
}

export function copyReportMarkdown(result) {
  const lines = [
    `# Suede Copy Check: ${result.grade} (${result.score}/100)`,
    "",
    `${result.metrics.words} words, ${result.metrics.sentences} sentences, ${result.metrics.avgSentenceWords} words per sentence, reading grade ${result.metrics.readingGrade}.`,
    ""
  ];
  if (!result.findings.length) {
    lines.push("No house bans, hedges, buzzwords or missing calls to action found.");
  } else {
    lines.push("## Findings");
    for (const finding of result.findings) {
      lines.push(`- **${finding.severity.toUpperCase()} ${finding.rule}**${finding.count > 1 ? ` (x${finding.count})` : ""}: ${finding.suggestion}`);
      for (const example of finding.examples) lines.push(`  - "${example}"`);
    }
  }
  lines.push("", "For a full rewrite, run $suede-copy. To strip AI tells line by line, run $suede-deslop.");
  return lines.join("\n");
}
