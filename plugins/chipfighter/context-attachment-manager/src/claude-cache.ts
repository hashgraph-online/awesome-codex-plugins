// Purpose: v0.10 — keep Claude Code's prompt cache readable after the engine changed the history. Claude Code marks
// the end of each request for the cache: the last two messages (with two marks in the system prompt, the four
// allowed). A read lands only where an earlier request wrote a mark; Anthropic looks back from this request's marks
// for one, but in a long-task eval (docs/v0.10/plan.md) it missed marks 6 places back, while a mark put on the very
// place was read every time. When the engine changes a message (an earlier turn's images become placeholders),
// Claude Code's marks all sit after the change; 7–9 requests a run read only the system prompt and wrote the whole
// conversation again. So the engine places the message marks itself:
// - read: where the latest of the last few requests it sent had a mark before the first difference with that request
//   (what it covers is unchanged and was written then), when this request is more than one of them added to;
// - prepare: just before the first image still sent as an original that a later request will leave out (automatic
//   selection), so the request that does has an unchanged place to read; with feature lines written a turn late, the
//   images go out once more and are left out in the middle of the next turn, after every mark of the requests before;
// - Claude Code's last mark, so the request writes its own end, unless both of the others need the two places.
// Input: a request's messages, what was sent before (newest first), how many marks sit outside the messages, the
// first image a later request will leave out. Output: the messages with the marks placed, and what to remember once
// they are sent.

import { link } from "./claude-thinking.ts";

type Json = Record<string, any>;
export type Mark = { message: number; block: number };
// What a sent request leaves to read: its messages' prefix hashes (hashes[i] covers messages 0..i) and its marks.
export type SentPrefix = { hashes: string[]; marks: Mark[] };
const MAX_MARKS = 4;
// How many sent requests a session remembers: a turn's requests, and the turn before.
export const REMEMBERED = 4;
// Blocks that cannot carry a mark.
const UNMARKABLE = new Set(["thinking", "redacted_thinking"]);

const blocksOf = (message: Json): Json[] | null => (Array.isArray(message?.content) ? message.content : null);

function marksOf(messages: Json[]): Mark[] {
  const marks: Mark[] = [];
  messages.forEach((message, m) => blocksOf(message)?.forEach((block, b) => { if (block?.cache_control) marks.push({ message: m, block: b }); }));
  return marks;
}

function hashesOf(messages: Json[]): string[] {
  const hashes: string[] = [];
  let chain = "";
  for (const message of messages) hashes.push((chain = link(chain, message)));
  return hashes;
}

export const sentPrefixOf = (messages: Json[]): SentPrefix => ({ hashes: hashesOf(messages), marks: marksOf(messages) });

// Marks a request carries outside its messages: the top-level one (automatic caching), tools, system blocks.
export function marksOutside(body: Json): number {
  const count = (list: unknown) => (Array.isArray(list) ? list.filter((block: Json) => block?.cache_control).length : 0);
  return (body.cache_control ? 1 : 0) + count(body.tools) + count(body.system);
}

const later = (a: Mark, b: Mark) => a.message > b.message || (a.message === b.message && a.block > b.block);
const same = (a: Mark, b: Mark) => a.message === b.message && a.block === b.block;
const markable = (messages: Json[], mark: Mark) => {
  const blocks = blocksOf(messages[mark.message]);
  if (!blocks) return mark.block === 0 && typeof messages[mark.message]?.content === "string";
  return !!blocks[mark.block] && !UNMARKABLE.has(blocks[mark.block]?.type);
};

// The latest remembered mark before where this request first differs from that request; null when this request only
// adds to the newest one (Claude Code's own marks read its end).
function readAt(hashes: string[], previous: SentPrefix[]): Mark | null {
  let target: Mark | null = null;
  for (const [i, sent] of previous.entries()) {
    let kept = 0;
    while (kept < hashes.length && kept < sent.hashes.length && hashes[kept] === sent.hashes[kept]) kept++;
    if (i === 0 && kept >= sent.hashes.length) return null;
    for (const mark of sent.marks) if (mark.message < kept && (!target || later(mark, target))) target = mark;
  }
  return target;
}

// The last block a mark can go on before `at` (a top-level block of a message).
function blockBefore(messages: Json[], at: Mark): Mark | null {
  for (let m = at.message, b = at.block - 1; m >= 0; m--, b = Infinity) {
    const count = blocksOf(messages[m])?.length ?? (typeof messages[m]?.content === "string" ? 1 : 0);
    for (let k = Math.min(b, count - 1); k >= 0; k--) if (markable(messages, { message: m, block: k })) return { message: m, block: k };
    if (m < at.message - 2) return null;
  }
  return null;
}

export type Placed = { messages: Json[]; marks: { read: Mark | null; prepare: Mark | null; dropped: Mark[] } | null };

export function keepCacheRead(messages: Json[], previous: SentPrefix[], outside: number, volatile: Mark | null = null): Placed {
  const none = { messages, marks: null };
  const current = marksOf(messages);
  const end = current.at(-1);
  if (!end) return none;
  const readCandidate = previous.length ? readAt(hashesOf(messages), previous) : null;
  const read = readCandidate && markable(messages, readCandidate) ? readCandidate : null;
  const prepare = volatile ? blockBefore(messages, volatile) : null;
  const wanted: Mark[] = [];
  for (const mark of [read, prepare]) if (mark && !wanted.some((other) => same(other, mark))) wanted.push(mark);
  if (!wanted.length) return none;
  const slots = Math.max(0, MAX_MARKS - outside);
  // The read first, then the prepared place, then Claude Code's last mark while there is room.
  const chosen = [...wanted];
  if (!chosen.some((mark) => same(mark, end))) chosen.push(end);
  chosen.splice(slots);
  // Room left: Claude Code's other marks stay, latest first.
  for (const mark of [...current].reverse()) if (chosen.length < slots && !chosen.some((other) => same(other, mark))) chosen.push(mark);
  if (!chosen.length) return none;
  const keep = (mark: Mark) => chosen.some((other) => same(other, mark));
  if (current.length === chosen.length && current.every(keep)) return none;
  // A mark put earlier takes the TTL of Claude Code's next one: marks with a longer TTL must come first.
  const controlFor = (at: Mark) => { const next = current.find((mark) => !later(at, mark)) ?? end; return messages[next.message].content[next.block].cache_control; };
  const touched = new Set([...current, ...chosen].map((mark) => mark.message));
  const next = messages.map((message, m) => {
    if (!touched.has(m)) return message;
    const content = Array.isArray(message.content) ? message.content : [{ type: "text", text: message.content }];
    return {
      ...message,
      content: content.map((part: Json, b: number) => {
        const mark = { message: m, block: b };
        if (keep(mark)) return part.cache_control ? part : { ...part, cache_control: controlFor(mark) };
        if (!part.cache_control) return part;
        const { cache_control: _dropped, ...rest } = part;
        return rest;
      }),
    };
  });
  return { messages: next, marks: { read, prepare, dropped: current.filter((mark) => !keep(mark)) } };
}
