// TypeScript twin of agent_bridge's security core (examples/python/agent_bridge):
// numeric-id allowlist, approval binding, redaction, untrusted-text events.
// Node >= 22.18 (type stripping), no dependencies. Same callback_data layout as Python:
// "ap:<rid 8 hex>:<nonce 8>:<a|r|d>" - a Python process and this one can share a state file.
import { createHash, randomBytes, timingSafeEqual } from "node:crypto";

export type Rec = {
  rid: string; nonce: string; kind: "approval" | "ask"; status: "open" | "decided" | "expired";
  chat: number; messageId: number | null; approvers: number[]; expires: number;
  decision: string | null; by: number | null; choices: string[];
};
export type Outcome = "approved" | "rejected" | "details" | "answered" | "duplicate" | "already_decided"
  | "expired" | "forged" | "not_allowed" | "wrong_message";

const CB = /^(ap|aq):([0-9a-f]{8}):([A-Za-z0-9_-]{8}):([a-z0-9]{1,3})$/;
const CHOICE: Record<string, string> = { a: "approved", r: "rejected", d: "details" };

export function parseIds(raw: string | undefined): Set<number> {
  const out = new Set<number>();
  for (const part of (raw ?? "").split(/[,;]/).map((s) => s.trim()).filter(Boolean)) {
    if (!/^-?\d{1,20}$/.test(part)) throw new Error("allowlist entries must be numeric Telegram ids, not usernames");
    out.add(Number(part));
  }
  return out;
}

export function idPair(seed?: string, n = 1): [string, string] {
  if (seed === undefined) return [randomBytes(4).toString("hex"), "n" + randomBytes(4).toString("hex").slice(0, 7)];
  const h = createHash("sha256").update(`${seed}:${n}`).digest("hex");
  const nn = createHash("sha256").update(`nonce:${seed}:${n}`).digest("hex");
  return [h.slice(0, 8), "n" + nn.slice(0, 7)];
}

export class ApprovalBook {
  recs = new Map<string, Rec>();
  private clock: () => number;
  private seed?: string;
  private n = 0;
  constructor(clock: () => number, seed?: string) {
    this.clock = clock;
    this.seed = seed;
  }

  create(kind: Rec["kind"], chat: number, approvers: number[], ttl: number, choices: string[] = []): Rec {
    if (!approvers.length) throw new Error("an approval needs at least one approver id");
    const [rid, nonce] = idPair(this.seed, ++this.n);
    const rec: Rec = { rid, nonce, kind, status: "open", chat, messageId: null, approvers,
      expires: this.clock() + ttl, decision: null, by: null, choices };
    this.recs.set(rid, rec);
    return rec;
  }

  data(rec: Rec, choice: string): string {
    return `${rec.kind === "approval" ? "ap" : "aq"}:${rec.rid}:${rec.nonce}:${choice}`;
  }

  resolve(ev: { data: string; from: number; chat: number; messageId: number }): { outcome: Outcome; rec?: Rec } {
    const m = CB.exec(ev.data ?? "");
    if (!m) return { outcome: "forged" };
    const [, prefix, rid, nonce, choice] = m;
    const rec = this.recs.get(rid);
    if (!rec || !timingSafeEqual(Buffer.from(rec.nonce), Buffer.from(nonce)) ||
        (rec.kind === "approval" ? "ap" : "aq") !== prefix) return { outcome: "forged" };
    if (rec.chat !== ev.chat || rec.messageId !== ev.messageId) return { outcome: "wrong_message", rec };
    if (!rec.approvers.includes(ev.from)) return { outcome: "not_allowed", rec };
    let decision: string;
    if (rec.kind === "approval") {
      if (!(choice in CHOICE)) return { outcome: "forged", rec };
      decision = CHOICE[choice];
    } else {
      const i = Number(choice);
      if (!Number.isInteger(i) || i >= rec.choices.length) return { outcome: "forged", rec };
      decision = rec.choices[i];
    }
    if (decision === "details") return { outcome: "details", rec };
    if (rec.status !== "open") {
      return { outcome: rec.decision === decision && rec.by === ev.from ? "duplicate" : "already_decided", rec };
    }
    if (this.clock() >= rec.expires) {
      Object.assign(rec, { status: "expired", decision: "expired" });
      return { outcome: "expired", rec };
    }
    Object.assign(rec, { status: "decided", decision, by: ev.from });
    return { outcome: rec.kind === "approval" ? (decision as Outcome) : "answered", rec };
  }
}

const PATTERNS: RegExp[] = [
  /\b\d{6,12}:[A-Za-z0-9_-]{30,}\b/g, /\b(?:sk|pk|rk)-[A-Za-z0-9_-]{16,}\b/g, /\bgh[pousr]_[A-Za-z0-9]{20,}\b/g,
  /\bAKIA[0-9A-Z]{16}\b/g, /-----BEGIN [A-Z ]*PRIVATE KEY-----[\s\S]*?-----END [A-Z ]*PRIVATE KEY-----/g,
];

export function redact(text: string, secrets: string[] = []): string {
  let out = text;
  for (const s of secrets) if (s && s.length >= 6) out = out.split(s).join("[REDACTED]");
  for (const p of PATTERNS) out = out.replace(p, "[REDACTED]");
  return out.replace(/\b(password|passwd|secret|token|api[_-]?key)\b(\s*[:=]\s*)(['"]?)[^\s'"]{4,}\3/gi, "$1$2[REDACTED]");
}

// Incoming text is data. The agent receives it flagged, never as an instruction.
export function textEvent(msg: { from?: { id: number; is_bot?: boolean }; chat: { id: number; type: string };
  text?: string; forward_origin?: unknown }, operators: Set<number>) {
  const id = msg.from?.id;
  if (id === undefined || msg.from?.is_bot || !(msg.chat.type === "private" && msg.chat.id === id && operators.has(id))) {
    return { type: "rejected" as const, from: id ?? null };
  }
  return { type: "text" as const, from: id, text: msg.text ?? "", forwarded: msg.forward_origin !== undefined,
    contentIsUntrustedData: true as const };
}
