import { readFile, writeFile } from "node:fs/promises";
import { pathToFileURL } from "node:url";
const VALID_PLACEHOLDER_PATTERN = /^⟦SIS:[A-Za-z0-9_-]+:[a-z-]+:\d+⟧$/u;
const FRONTMATTER_PATTERN = /^(?:\uFEFF)?---[^\r\n]*\r?\n(?:[\s\S]*?\r?\n)?---[ \t]*(?=\r?\n|$)/;
const NUMBER_PATTERN = /[+-]?(?:[$€£¥₩][ \t\u00A0\u202F]?)?(?:(?:\d{1,3}(?:,\d{3})+(?:\.\d+)?|\d{1,3}(?:\.\d{3})+(?:,\d+)?|\d{1,3}(?:[\u00A0\u202F]\d{3})+(?:[.,]\d+)?|\d+[.,]\d+|\d+|\.\d+)(?:%|[A-Za-z]+)?)/gu;
const SPACED_UNIT_PATTERN = /^([ \t\u00A0\u202F]+)(?:GiB|GHz|KiB|MHz|MiB|TiB|bytes?|cm|GB|hrs?|kHz|kg|km|kW|lbs?|mA|MB|mg|min|mm|ms|mV|oz|TB|yd|€|£|¥|₩|°C|°F|ft|Hz|in|mi|[ABghmsVW])(?![\p{L}\p{N}_])/iu;
const YEAR_PATTERN = String.raw`(?:1[5-9]\d{2}|20\d{2}|21\d{2})[a-z]?`;
const AUTHOR_PATTERN = String.raw`[A-Z][\p{L}'’-]*(?:\s+et al\.)?`;
const AUTHOR_LIST_PATTERN = String.raw`${AUTHOR_PATTERN}(?:,\s*(?:&\s+)?${AUTHOR_PATTERN})*(?:\s+(?:&|and)\s+${AUTHOR_PATTERN})?`;
const AUTHOR_YEAR_CITATION_PATTERN = new RegExp(String.raw`(?:\b${AUTHOR_LIST_PATTERN}\s*\(${YEAR_PATTERN}\)|\(${AUTHOR_LIST_PATTERN}\s*,\s*${YEAR_PATTERN}(?:;\s*${AUTHOR_LIST_PATTERN}\s*,\s*${YEAR_PATTERN})*\)|\[${AUTHOR_LIST_PATTERN}\s*,\s*${YEAR_PATTERN}\])`, "gu");
const MARKDOWN_AUTOLINK_PATTERN = /<(?:[A-Za-z][A-Za-z0-9+.-]{1,31}:[^\s<>]*|[A-Za-z0-9.!#$%&'*+\/=\?^_`{|}~-]+@(?:[A-Za-z0-9](?:[A-Za-z0-9-]{0,61}[A-Za-z0-9])?\.)+[A-Za-z0-9](?:[A-Za-z0-9-]{0,61}[A-Za-z0-9])?)>/g;
const PATH_ATOM = String.raw`[^\u0000-\u0020<>:"/\\|?*]*[^\u0000-\u0020<>:"/\\|?*.,;!?]`;
const PATH_SEGMENT = String.raw`${PATH_ATOM}(?:[ \t]+${PATH_ATOM})*`;
const PATH_LEAF = String.raw`(?:${PATH_SEGMENT}\.[\p{L}\p{N}_-]+(?::${PATH_ATOM})?|${PATH_SEGMENT})`;
const PATH_PATTERN = new RegExp(String.raw`(?<![\p{L}\p{N}_@%+=:.,-])(?:(?:[A-Za-z]:[\\/]|[A-Za-z]:(?![\\/])|\\\\\?(?:[\\/]UNC[\\/]|[\\/][A-Za-z]:[\\/]|[\\/])|\\\\\.[\\/](?:[A-Za-z]:[\\/])?|\\\\)(?:${PATH_SEGMENT}[\\/])*${PATH_LEAF}|(?:(?:~|\.{1,2})[\\/]|[\\/])(?:${PATH_SEGMENT}[\\/])*${PATH_LEAF}|${PATH_ATOM}(?:[\\/]${PATH_SEGMENT})*[\\/]${PATH_LEAF}|(?:\.[\p{L}\p{N}_-]+|[\p{L}\p{N}_-][\p{L}\p{N}_.-]*\.[\p{L}\p{N}_-]+)(?![\p{L}\p{N}_-]))[\\/]?`, "gu");
function addRegexCandidates(candidates, text, type, expression) { for (const match of text.matchAll(expression)) candidates.push({ type, value: match[0], start: match.index, end: match.index + match[0].length }); }
function addValueCandidates(candidates, text, protectedValues) {
  for (const value of protectedValues) {
    if (typeof value !== "string" || value.length === 0) continue; for (let start = text.indexOf(value); start !== -1; start = text.indexOf(value, start + 1)) candidates.push({ type: "user-frozen", value, start, end: start + value.length });
  }
}
function addNumberCandidates(candidates, text) {
  for (const match of text.matchAll(NUMBER_PATTERN)) {
    if (text[match.index - 1] === "." && !match[0].startsWith(".")) continue;
    let value = match[0];
    let end = match.index + value.length;
    if (!/[A-Za-z%]$/u.test(value)) {
      const unit = SPACED_UNIT_PATTERN.exec(text.slice(end));
      if (unit) { value += unit[0]; end += unit[0].length; }
    }
    candidates.push({ type: "number", value, start: match.index, end });
  }
}
function addFrontmatterCandidate(candidates, text) {
  const match = FRONTMATTER_PATTERN.exec(text);
  if (match) candidates.push({ type: "frontmatter", value: match[0], start: 0, end: match[0].length });
}
function textLines(text) {
  const lines = [];
  let start = 0;
  while (start < text.length) {
    const newline = text.indexOf("\n", start);
    const end = newline === -1 ? text.length : newline + 1;
    const contentEnd = newline === -1 ? end : text[newline - 1] === "\r" ? newline - 1 : newline;
    lines.push({ text: text.slice(start, contentEnd), start, end, contentEnd });
    start = end;
  }
  return lines;
}
function fencedCodeBlocks(text) {
  const lines = textLines(text);
  const blocks = [];
  for (let index = 0; index < lines.length; index += 1) {
    const opening = /^(?: {0,3})(`{3,}|~{3,})([^\r\n]*)$/u.exec(lines[index].text);
    if (!opening) continue;
    let closed = false;
    for (let closingIndex = index + 1; closingIndex < lines.length; closingIndex += 1) {
      const closing = /^(?: {0,3})(`{3,}|~{3,})[ \t]*$/u.exec(lines[closingIndex].text);
      if (!closing || closing[1][0] !== opening[1][0] || closing[1].length < opening[1].length) continue;
      const info = opening[2].trim();
      blocks.push({
        start: lines[index].start,
        end: lines[closingIndex].contentEnd,
        value: text.slice(lines[index].start, lines[closingIndex].contentEnd),
        language: info.split(/[ \t]+/u)[0] || ""
      });
      index = closingIndex;
      closed = true;
      break;
    }
    if (!closed) {
      const info = opening[2].trim();
      blocks.push({
        start: lines[index].start,
        end: text.length,
        value: text.slice(lines[index].start),
        language: info.split(/[ \t]+/u)[0] || ""
      });
      break;
    }
  }
  return blocks;
}
function addInlineCodeCandidates(candidates, text) {
  const runs = [];
  for (let start = text.indexOf("`"); start !== -1;) {
    let end = start + 1; while (text[end] === "`") end += 1;
    runs.push({ start, end, size: end - start }); start = text.indexOf("`", end);
  }
  const nextSame = Array(runs.length).fill(-1), nextBySize = new Map();
  for (let index = runs.length - 1; index >= 0; index -= 1) { nextSame[index] = nextBySize.get(runs[index].size) ?? -1; nextBySize.set(runs[index].size, index); }
  for (let index = 0; index < runs.length;) {
    const closingIndex = nextSame[index];
    if (closingIndex === -1) { index += 1; continue; }
    const start = runs[index].start, end = runs[closingIndex].end;
    candidates.push({ type: "inline-code", value: text.slice(start, end), start, end }); index = closingIndex + 1;
  }
}
function closingTitleIndex(text, cursor) {
  while (text[cursor] === " " || text[cursor] === "\t") cursor += 1;
  if (text[cursor] === ")") return cursor;
  const opener = text[cursor];
  const closer = opener === "(" ? ")" : opener;
  if (opener !== "\"" && opener !== "'" && opener !== "(") return -1;
  for (cursor += 1; cursor < text.length && text[cursor] !== "\n" && text[cursor] !== "\r"; cursor += 1) {
    if (text[cursor] === "\\") cursor += 1;
    else if (text[cursor] === closer) {
      cursor += 1;
      while (text[cursor] === " " || text[cursor] === "\t") cursor += 1;
      return text[cursor] === ")" ? cursor : -1;
    }
  }
  return -1;
}
function closingLinkIndex(text, opening) {
  let cursor = opening + 1;
  if (text[cursor] === "<") {
    for (cursor += 1; cursor < text.length && text[cursor] !== "\n" && text[cursor] !== "\r"; cursor += 1) {
      if (text[cursor] === "\\") cursor += 1;
      else if (text[cursor] === ">") return closingTitleIndex(text, cursor + 1);
    }
    return -1;
  }
  let depth = 0;
  for (; cursor < text.length && text[cursor] !== "\n" && text[cursor] !== "\r"; cursor += 1) {
    if (text[cursor] === "\\") cursor += 1;
    else if ((text[cursor] === " " || text[cursor] === "\t") && depth === 0) return closingTitleIndex(text, cursor);
    else if (text[cursor] === "(") depth += 1;
    else if (text[cursor] === ")" && depth === 0) return cursor;
    else if (text[cursor] === ")") depth -= 1;
  }
  return -1;
}
function addMarkdownLinkCandidates(candidates, text) {
  const referenceLabels = new Set(textLines(text).flatMap((line) => {
    const match = /^(?: {0,3})\[([^\]\r\n]+)\]:[^\r\n]*$/u.exec(line.text);
    return match ? [match[1].trim().replace(/[ \t]+/gu, " ").toLowerCase()] : [];
  }));
  for (let start = text.indexOf("["); start !== -1; start = text.indexOf("[", start + 1)) {
    const image = text[start - 1] === "!";
    const candidateStart = image ? start - 1 : start;
    let labelDepth = 0;
    for (let cursor = start + 1; cursor < text.length && text[cursor] !== "\n" && text[cursor] !== "\r"; cursor += 1) {
      if (text[cursor] === "\\") cursor += 1;
      else if (text[cursor] === "[") labelDepth += 1;
      else if (text[cursor] === "]" && labelDepth > 0) labelDepth -= 1;
      else if (text[cursor] === "]") {
        const type = image ? "markdown-image" : "markdown-url";
        if (text[cursor + 1] === "(") {
          const closing = closingLinkIndex(text, cursor + 1);
          if (closing !== -1) candidates.push({ type, value: text.slice(candidateStart, closing + 1), start: candidateStart, end: closing + 1 });
        } else if (text[cursor + 1] === "[") {
          const closing = text.indexOf("]", cursor + 2);
          if (closing !== -1 && !/[\r\n]/u.test(text.slice(cursor + 2, closing))) candidates.push({ type: "markdown-reference", value: text.slice(candidateStart, closing + 1), start: candidateStart, end: closing + 1 });
        } else if (referenceLabels.has(text.slice(start + 1, cursor).trim().replace(/[ \t]+/gu, " ").toLowerCase())) candidates.push({ type: image ? "markdown-shortcut-image" : "markdown-shortcut-reference", value: text.slice(candidateStart, cursor + 1), start: candidateStart, end: cursor + 1 });
        break;
      }
    }
  }
  for (const line of textLines(text)) if (/^(?: {0,3})\[[^\]\r\n]+\]:[^\r\n]*$/u.test(line.text)) candidates.push({ type: "markdown-reference-definition", value: line.text, start: line.start, end: line.contentEnd });
}
function addBlockquoteCandidates(candidates, text) {
  const lines = textLines(text);
  for (let index = 0; index < lines.length; index += 1) {
    if (!/^(?: {0,3})>[ \t]?/u.test(lines[index].text)) continue;
    let last = index;
    while (last + 1 < lines.length && (/^(?: {0,3})>[ \t]?/u.test(lines[last + 1].text) || (lines[last + 1].text && !/^(?: {0,3})(?:#{1,6}[ \t]|(?:[-+*]|\d+[.)])[ \t]|`{3,}|~{3,}|\[[^\]]+\]:|(?:(?:\*[ \t]*){3,}|(?:-[ \t]*){3,}|(?:_[ \t]*){3,})[ \t]*$)/u.test(lines[last + 1].text)))) last += 1;
    candidates.push({ type: "blockquote", value: text.slice(lines[index].start, lines[last].contentEnd), start: lines[index].start, end: lines[last].contentEnd });
    index = last;
  }
}
function tableCells(line) {
  const trimmed = line.trim();
  if (!trimmed.includes("|")) return null;
  const withoutLeadingPipe = trimmed.startsWith("|") ? trimmed.slice(1) : trimmed;
  const content = withoutLeadingPipe.endsWith("|") ? withoutLeadingPipe.slice(0, -1) : withoutLeadingPipe;
  return content.split("|").map((cell) => cell.trim());
}
function isOuterPipeRow(line) {
  return /^\|.*\|[ \t]*$/u.test(line);
}
function isTableDivider(cells) {
  return cells?.length > 0 && cells.every((cell) => /^:?-{3,}:?$/u.test(cell));
}
function tableBlocks(text) {
  const lines = textLines(text);
  const blocks = [];
  for (let index = 0; index < lines.length; index += 1) {
    if (!isOuterPipeRow(lines[index].text)) continue;
    let last = index;
    while (last + 1 < lines.length && isOuterPipeRow(lines[last + 1].text)) last += 1;
    const rowColumns = lines.slice(index, last + 1).map((line) => tableCells(line.text).length);
    blocks.push({ start: lines[index].start, end: lines[last].contentEnd, value: text.slice(lines[index].start, lines[last].contentEnd), rows: rowColumns.length, rowColumns });
    index = last;
  }
  for (let index = 0; index + 1 < lines.length; index += 1) {
    if (isOuterPipeRow(lines[index].text)) continue;
    const header = tableCells(lines[index].text);
    const divider = tableCells(lines[index + 1].text);
    if (!header || !divider || header.length !== divider.length || !isTableDivider(divider)) continue;
    let last = index + 1;
    while (last + 1 < lines.length && tableCells(lines[last + 1].text)) last += 1;
    const rowColumns = lines.slice(index, last + 1).map((line) => tableCells(line.text).length);
    blocks.push({ start: lines[index].start, end: lines[last].contentEnd, value: text.slice(lines[index].start, lines[last].contentEnd), rows: rowColumns.length, rowColumns });
    index = last;
  }
  return blocks;
}
function collectCandidates(text, protectedValues) {
  const candidates = [];
  addFrontmatterCandidate(candidates, text);
  for (const block of fencedCodeBlocks(text)) candidates.push({ type: "fenced-code", value: block.value, start: block.start, end: block.end });
  addInlineCodeCandidates(candidates, text);
  for (const table of tableBlocks(text)) candidates.push({ type: "table", value: table.value, start: table.start, end: table.end });
  addMarkdownLinkCandidates(candidates, text);
  addRegexCandidates(candidates, text, "markdown-autolink", MARKDOWN_AUTOLINK_PATTERN);
  addBlockquoteCandidates(candidates, text);
  addRegexCandidates(candidates, text, "bare-url", /\b(?:https?|ftp):\/\/[^\s<>()\[\]{}"']+[^\s<>()\[\]{}"'.,;:!?]/g);
  addRegexCandidates(candidates, text, "path", PATH_PATTERN);
  addRegexCandidates(candidates, text, "formula", /(?<![\p{L}\p{N}_])(?:[\p{L}_][\p{L}\p{N}_.-]*|[+-]?(?:\d+(?:\.\d+)?|\.\d+))[ \t]*(?:={1,3}|!==?|<=?|>=?|≈|≠|≤|≥)[ \t]*(?:[\p{L}_][\p{L}\p{N}_.-]*|[+-]?(?:\d+(?:\.\d+)?|\.\d+))(?![\p{L}\p{N}_])/gu);
  addRegexCandidates(candidates, text, "identifier", /(?<![\p{L}\p{N}_])(?:[A-Za-z][A-Za-z0-9]*_[A-Za-z0-9_]+|[a-z]+[A-Z][A-Za-z0-9]*|[A-Z]{2,}[a-z][A-Za-z0-9]*|[A-Z][a-z0-9]+(?:[A-Z][A-Za-z0-9]*)+)(?![\p{L}\p{N}_])/gu);
  addRegexCandidates(candidates, text, "citation", /\[(?:[A-Z][\w.-]*|\d+)(?:\s+[\w.-]+)*\]/g);
  addRegexCandidates(candidates, text, "author-year-citation", AUTHOR_YEAR_CITATION_PATTERN);
  addRegexCandidates(candidates, text, "quotation", /"(?:[^"\\\r\n]|\\.)*"|(?<![\p{L}\p{N}])'(?:[^'\\\r\n]|\\.)*'(?![\p{L}\p{N}])|“[^”\r\n]*”|‘[^’\r\n]*’|„[^“\r\n]*“|«[^»\r\n]*»|「[^」\r\n]*」|『[^』\r\n]*』/gu);
  addNumberCandidates(candidates, text);
  addValueCandidates(candidates, text, protectedValues);
  const autolinks = candidates.filter((candidate) => candidate.type === "markdown-autolink");
  return candidates.filter((candidate) => candidate.type !== "formula" || !autolinks.some((link) => candidate.start < link.end && candidate.end > link.start));
}
function acceptNonOverlapping(accepted, candidate) {
  const previous = accepted.at(-1);
  if (!previous || candidate.start >= previous.end) accepted.push(candidate);
  return accepted;
}
export function extractProtectedSpans(text, options = {}) {
  const protectedValues = Array.isArray(options.protectedValues) ? options.protectedValues : [];
  return collectCandidates(text, protectedValues)
    .sort((left, right) => left.start - right.start || right.end - left.end)
    .reduce(acceptNonOverlapping, []);
}
function countValues(spans, keyForSpan = (span) => `${span.type}\u0000${span.value}`) {
  const counts = new Map();
  for (const span of spans) {
    const key = keyForSpan(span);
    const entry = counts.get(key) ?? { value: span.value, count: 0 };
    entry.count += 1;
    counts.set(key, entry);
  }
  return counts;
}
function compareCounts(sourceSpans, finalSpans, keyForSpan) {
  const sourceCounts = countValues(sourceSpans, keyForSpan);
  const finalCounts = countValues(finalSpans, keyForSpan);
  const missing = [];
  const added = [];

  for (const [key, source] of sourceCounts) {
    const final = finalCounts.get(key);
    for (let index = final?.count ?? 0; index < source.count; index += 1) missing.push(source.value);
  }
  for (const [key, final] of finalCounts) {
    const source = sourceCounts.get(key);
    for (let index = source?.count ?? 0; index < final.count; index += 1) added.push(final.value);
  }

  return { ok: missing.length === 0 && added.length === 0, missing, added };
}

function valuesMissingEntirely(sourceSpans, finalSpans) {
  const finalCounts = countValues(finalSpans);
  const values = [];
  const seen = new Set();
  for (const span of sourceSpans) {
    const key = `${span.type}\u0000${span.value}`;
    if (!finalCounts.has(key) && !seen.has(key)) {
      seen.add(key);
      values.push(span.value);
    }
  }
  return { ok: values.length === 0, values };
}

function sourceValuesAppearInOrder(sourceSpans, finalText, allowOverlap = false) {
  let searchFrom = 0;
  const positions = [];
  for (const span of sourceSpans) {
    const start = finalText.indexOf(span.value, searchFrom);
    if (start === -1) return { ok: false, positions };
    positions.push(start);
    searchFrom = start + (allowOverlap ? 0 : span.value.length);
  }
  return { ok: true, positions };
}

function compareProtectedSpans(sourceSpans, finalSpans, finalText, options = {}) {
  const missing = valuesMissingEntirely(sourceSpans, finalSpans);
  const count = compareCounts(sourceSpans, finalSpans);
  const order = sourceValuesAppearInOrder(sourceSpans, finalText, options.allowOverlap);
  const problems = [];
  if (!missing.ok) problems.push({ check: "protected.missing", values: missing.values });
  if (!count.ok) problems.push({ check: "protected.count", missing: count.missing, added: count.added });
  if (!order.ok) problems.push({ check: "protected.order" });
  return { ok: problems.length === 0, missing, count, order, problems };
}

function userFrozenSpans(text, protectedValues) {
  const spans = [];
  addValueCandidates(spans, text, protectedValues);
  return spans.sort((left, right) => left.start - right.start || right.end - left.end);
}

function mergeProtectedChecks(syntax, userFrozen) {
  const userProblems = userFrozen.problems.map((problem) => ({
    ...problem,
    check: problem.check.replace("protected.", "protected.user-frozen.")
  }));
  return {
    ok: syntax.ok && userFrozen.ok,
    missing: { ok: syntax.missing.ok && userFrozen.missing.ok, values: [...syntax.missing.values, ...userFrozen.missing.values] },
    count: { ok: syntax.count.ok && userFrozen.count.ok, missing: [...syntax.count.missing, ...userFrozen.count.missing], added: [...syntax.count.added, ...userFrozen.count.added] },
    order: { ok: syntax.order.ok && userFrozen.order.ok, positions: syntax.order.positions, userFrozenPositions: userFrozen.order.positions },
    userFrozen,
    problems: [...syntax.problems, ...userProblems]
  };
}

function compareNumberMultisets(sourceSpans, finalSpans) {
  const sourceNumbers = sourceSpans.filter((span) => span.type === "number");
  const finalNumbers = finalSpans.filter((span) => span.type === "number");
  const count = compareCounts(sourceNumbers, finalNumbers, (span) => span.value);
  const problems = [];
  if (count.missing.length > 0) problems.push({ check: "numbers.missing", values: count.missing });
  if (count.added.length > 0) problems.push({ check: "numbers.added", values: count.added });
  return { ok: count.ok, missing: count.missing, added: count.added, problems };
}

function compareSignatures(source, final) {
  return { ok: JSON.stringify(source) === JSON.stringify(final), source, final };
}

function frontmatterBlocks(text) { const match = FRONTMATTER_PATTERN.exec(text); return match ? [match[0]] : []; }

function headingSignatures(text) {
  const headings = [];
  const lines = textLines(text);
  for (const line of lines) {
    const match = /^(#{1,6})[ \t]+(.+?)[ \t]*$/u.exec(line.text);
    if (match) headings.push({ start: line.start, level: match[1].length, text: match[2].replace(/[ \t]+#+$/, "") });
  }
  for (let index = 1; index < lines.length; index += 1) {
    const underline = /^[ \t]*(=+|-+)[ \t]*$/u.exec(lines[index].text);
    const text = lines[index - 1].text.trim();
    if (underline && text) headings.push({ start: lines[index - 1].start, level: underline[1][0] === "=" ? 1 : 2, text });
  }
  return headings.sort((left, right) => left.start - right.start).map(({ level, text }) => ({ level, text }));
}

function fenceSignatures(text) {
  return fencedCodeBlocks(text).map(({ language, value }) => ({ language, value }));
}

function tableSignatures(text) { return tableBlocks(text).map(({ rows, rowColumns }) => ({ rows, rowColumns })); }
function listSignatures(text) { return textLines(text).flatMap((line) => { const match = /^([ \t]*)([-+*]|\d{1,9}[.)])[ \t]+(?:\[([ xX])\][ \t]+)?/u.exec(line.text); return match ? [{ indent: match[1].length, kind: /^\d/u.test(match[2]) ? "ordered" : "unordered", task: match[3]?.toLowerCase() ?? null }] : []; }); }
function structureCheck(sourceText, finalText) {
  const frontmatter = compareSignatures(frontmatterBlocks(sourceText), frontmatterBlocks(finalText));
  const headings = compareSignatures(headingSignatures(sourceText), headingSignatures(finalText));
  const fences = compareSignatures(fenceSignatures(sourceText), fenceSignatures(finalText));
  const tables = compareSignatures(tableSignatures(sourceText), tableSignatures(finalText)); const lists = compareSignatures(listSignatures(sourceText), listSignatures(finalText));
  const checks = { frontmatter, headings, fences, tables, lists };
  const problems = Object.entries(checks)
    .filter(([, check]) => !check.ok)
    .map(([name, check]) => ({ check: `structure.${name}`, source: check.source, final: check.final }));
  return { ok: problems.length === 0, ...checks, problems };
}

function placeholderResidues(text) {
  const residues = [];
  for (let start = text.indexOf("⟦SIS"); start !== -1; start = text.indexOf("⟦SIS", start + 1)) {
    const closing = text.indexOf("⟧", start + 4);
    const newline = text.indexOf("\n", start + 4);
    const end = closing !== -1 && (newline === -1 || closing < newline) ? closing + 1 : newline === -1 ? text.length : newline;
    residues.push(text.slice(start, end));
  }
  return residues;
}

function placeholderCheck(sourceText, finalText) {
  const sourceCollisions = placeholderResidues(sourceText);
  const unresolved = placeholderResidues(finalText);
  const malformed = unresolved.filter((value) => !VALID_PLACEHOLDER_PATTERN.test(value));
  const problems = [];
  if (sourceCollisions.length > 0) problems.push({ check: "placeholders.collision", values: sourceCollisions, message: "Source contains placeholder-shaped text; choose a different run tag." });
  if (unresolved.length > 0) problems.push({ check: "placeholders.unresolved", values: unresolved });
  return { ok: problems.length === 0, sourceCollisions, unresolved, malformed, problems };
}

function lengthMetrics(sourceText, finalText) {
  const sourceCharacters = sourceText.length, finalCharacters = finalText.length;
  const lengthDeltaRate = sourceCharacters === 0 ? null : (finalCharacters - sourceCharacters) / sourceCharacters;
  return { sourceCharacters, finalCharacters, lengthDeltaRate, shrinkageRate: lengthDeltaRate === null ? null : Math.max(0, -lengthDeltaRate) };
}

function lengthWarnings(metrics) {
  const warnings = [];
  if (metrics.shrinkageRate !== null && metrics.shrinkageRate > 0.35) {
    warnings.push({ check: "metrics.shrinkage", value: metrics.shrinkageRate, threshold: 0.35 });
  }
  if (metrics.lengthDeltaRate !== null && metrics.lengthDeltaRate > 0.5) {
    warnings.push({ check: "metrics.expansion", value: metrics.lengthDeltaRate, threshold: 0.5 });
  }
  return warnings;
}

export function auditTexts(sourceText, finalText, options = {}) {
  const sourceSpans = extractProtectedSpans(sourceText);
  const finalSpans = extractProtectedSpans(finalText);
  const syntaxCheck = compareProtectedSpans(sourceSpans, finalSpans, finalText);
  const protectedValues = Array.isArray(options.protectedValues) ? options.protectedValues : [];
  const userFrozen = compareProtectedSpans(
    userFrozenSpans(sourceText, protectedValues),
    userFrozenSpans(finalText, protectedValues),
    finalText,
    { allowOverlap: true }
  );
  const protectedCheck = mergeProtectedChecks(syntaxCheck, userFrozen);
  const numbers = compareNumberMultisets(sourceSpans, finalSpans);
  const structure = structureCheck(sourceText, finalText);
  const placeholders = placeholderCheck(sourceText, finalText);
  const metrics = lengthMetrics(sourceText, finalText);
  const problems = [...protectedCheck.problems, ...numbers.problems, ...structure.problems, ...placeholders.problems];
  return {
    schemaVersion: 1,
    ok: problems.length === 0,
    checks: { protected: protectedCheck, numbers, structure, placeholders },
    metrics,
    problems,
    warnings: lengthWarnings(metrics)
  };
}

class CliArgumentError extends Error {
  constructor(message) {
    super(message);
    this.check = "cli.arguments";
  }
}

class CliReadableError extends Error {
  constructor(check, message) {
    super(message);
    this.check = check;
  }
}

function usageError() {
  return new CliArgumentError("Usage: --source <path> --final <path> --report <path> [--protected <json-path>]");
}

function parseArguments(argv) {
  const values = {};
  const flags = new Set(["--source", "--final", "--report", "--protected"]);
  for (let index = 0; index < argv.length; index += 2) {
    const flag = argv[index];
    const value = argv[index + 1];
    if (!flags.has(flag) || !value || value.startsWith("--") || values[flag] !== undefined) throw usageError();
    values[flag] = value;
  }
  if (!values["--source"] || !values["--final"] || !values["--report"]) throw usageError();
  return values;
}

function recoverReportPath(argv) {
  const index = argv.indexOf("--report");
  const value = argv[index + 1];
  return index === -1 || !value || value.startsWith("--") ? undefined : value;
}

async function readCliInput(path, check) {
  try {
    return await readFile(path, "utf8");
  } catch (error) {
    throw new CliReadableError(check, `${check} failed: ${error.message}`);
  }
}

async function readProtectedValues(path) {
  const text = await readCliInput(path, "cli.protected.read");
  let manifest;
  try {
    manifest = JSON.parse(text);
  } catch (error) {
    throw new CliReadableError("cli.protected-manifest", `cli.protected-manifest failed: ${error.message}`);
  }
  if (!manifest || typeof manifest !== "object" || Array.isArray(manifest) || Object.keys(manifest).length !== 1 || !Object.hasOwn(manifest, "values") || !Array.isArray(manifest.values) || !manifest.values.every((value) => typeof value === "string")) {
    throw new CliReadableError("cli.protected-manifest", "cli.protected-manifest failed: expected { values: [\"exact text\"] }");
  }
  return manifest.values;
}

function emptyStructureCheck() { const empty = { ok: true, source: [], final: [] }; return { ok: true, frontmatter: empty, headings: empty, fences: empty, tables: empty, lists: empty, problems: [] }; }

function cliFailureReport(error) {
  return {
    schemaVersion: 1,
    ok: false,
    checks: {
      protected: { ok: true, missing: { ok: true, values: [] }, count: { ok: true, missing: [], added: [] }, order: { ok: true, positions: [] }, problems: [] },
      numbers: { ok: true, missing: [], added: [], problems: [] },
      structure: emptyStructureCheck(),
      placeholders: { ok: true, sourceCollisions: [], unresolved: [], malformed: [], problems: [] }
    },
    metrics: { sourceCharacters: null, finalCharacters: null, lengthDeltaRate: null, shrinkageRate: null },
    problems: [{ check: error.check, message: error.message }],
    warnings: []
  };
}

export async function runCli(argv = process.argv.slice(2)) {
  const recoveredReportPath = recoverReportPath(argv);
  let args;
  try {
    args = parseArguments(argv);
  } catch (error) {
    if (error instanceof CliArgumentError && recoveredReportPath) {
      await writeFile(recoveredReportPath, `${JSON.stringify(cliFailureReport(error), null, 2)}\n`);
    }
    throw error;
  }
  let report;
  try {
    const protectedValues = args["--protected"] ? await readProtectedValues(args["--protected"]) : [];
    const sourceText = await readCliInput(args["--source"], "cli.source.read");
    const finalText = await readCliInput(args["--final"], "cli.final.read");
    report = auditTexts(sourceText, finalText, { protectedValues });
  } catch (error) {
    if (!(error instanceof CliReadableError)) throw error;
    report = cliFailureReport(error);
  }
  await writeFile(args["--report"], `${JSON.stringify(report, null, 2)}\n`);
  return report;
}

if (process.argv[1] && import.meta.url === pathToFileURL(process.argv[1]).href) {
  runCli().then((report) => {
    process.exitCode = report.ok ? 0 : 1;
  }).catch((error) => {
    console.error(error.message);
    process.exitCode = error instanceof CliArgumentError ? 2 : 1;
  });
}
