import { createHash, timingSafeEqual } from "node:crypto";
import { isIP } from "node:net";

export type ActorType = "USER" | "ADMIN" | "SYSTEM" | "OPERATOR";

export const AUDIT_GENESIS_HASH = "GENESIS";

export interface AuditLogRecord {
  id: string;
  seq: bigint;
  actorId: string | null;
  actorType: ActorType;
  action: string;
  resource: string;
  subjectId: string | null;
  legalBasis: string | null;
  purpose: string | null;
  ipAddress: string | null;
  userAgent: string | null;
  payloadHash: string;
  prevHash: string;
  selfHash: string;
  timestamp: Date;
}

export interface AuditLogCreateData {
  actorId: string | null;
  actorType: ActorType;
  action: string;
  resource: string;
  subjectId: string | null;
  legalBasis: string | null;
  purpose: string | null;
  ipAddress: string | null;
  userAgent: string | null;
  payloadHash: string;
  prevHash: string;
  selfHash: string;
  timestamp: Date;
}

export interface AuditLogTx {
  auditLogEntry: {
    findFirst(args: {
      orderBy: { seq: "desc" };
      select: { seq: true; selfHash: true };
    }): Promise<{ seq: bigint; selfHash: string } | null>;
    create(args: { data: AuditLogCreateData }): Promise<AuditLogRecord>;
  };
  $executeRawUnsafe?(query: string): Promise<unknown>;
}

export interface AuditLogDb {
  $transaction<T>(fn: (tx: AuditLogTx) => Promise<T>): Promise<T>;
}

export interface RequestLike {
  headers: {
    get(name: string): string | null;
  };
}

export interface LogAuditInput {
  actorId?: string | null;
  actorType: ActorType;
  action: string;
  resource: string;
  subjectId?: string | null;
  legalBasis?: string | null;
  purpose?: string | null;
  redactedMetadata?: Record<string, unknown>;
  req?: RequestLike;
  timestamp?: Date;
}

function canonicalJson(value: unknown): string {
  if (value === null || typeof value !== "object") {
    return JSON.stringify(value ?? null);
  }
  if (Array.isArray(value)) {
    return `[${value.map((v) => canonicalJson(v)).join(",")}]`;
  }
  const entries = Object.entries(value as Record<string, unknown>)
    .filter(([, v]) => v !== undefined)
    .sort(([a], [b]) => a.localeCompare(b));
  return `{${entries.map(([k, v]) => `${JSON.stringify(k)}:${canonicalJson(v)}`).join(",")}}`;
}

export function extractAuditClientIp(req?: RequestLike): string | null {
  const raw = req?.headers.get("x-forwarded-for");
  if (!raw) return null;
  const first = raw.split(",")[0]?.trim() ?? "";
  return isIP(first) !== 0 ? first : null;
}

export function computeAuditPayloadHash(redactedMetadata?: Record<string, unknown>): string {
  return createHash("sha256")
    .update(canonicalJson(redactedMetadata ?? {}), "utf8")
    .digest("hex");
}

export function computeAuditSelfHash(fields: {
  prevHash: string;
  timestampIso: string;
  actorType: ActorType;
  actorId: string | null;
  action: string;
  resource: string;
  subjectId: string | null;
  payloadHash: string;
}): string {
  const preimage = [
    fields.prevHash,
    fields.timestampIso,
    fields.actorType,
    fields.actorId ?? "",
    fields.action,
    fields.resource,
    fields.subjectId ?? "",
    fields.payloadHash,
  ].join("|");
  return createHash("sha256").update(preimage, "utf8").digest("hex");
}

/**
 * Grava um evento de auditoria encadeado de forma transacionalmente serializada:
 * 1. Não vaza `req` nem `redactedMetadata` para o objeto `data` do Prisma;
 * 2. Usa `pg_advisory_xact_lock` dentro da transação PostgreSQL para serializar escritas concorrentes
 *    sem quebrar nem bifurcar a hash chain;
 * 3. Ordena pelo `seq` monotônico (evitando ambiguidade de timestamps no mesmo milissegundo).
 */
export async function logAudit(db: AuditLogDb, input: LogAuditInput): Promise<AuditLogRecord> {
  const payloadHash = computeAuditPayloadHash(input.redactedMetadata);
  const ipAddress = extractAuditClientIp(input.req);
  const userAgent = input.req?.headers.get("user-agent") ?? null;
  const actorId = input.actorId ?? null;
  const subjectId = input.subjectId ?? null;
  const legalBasis = input.legalBasis ?? null;
  const purpose = input.purpose ?? null;

  return db.$transaction(async (tx) => {
    if (typeof tx.$executeRawUnsafe === "function") {
      await tx.$executeRawUnsafe(
        "SELECT pg_advisory_xact_lock(hashtext('lgpd_audit_log_chain'))",
      );
    }

    const last = await tx.auditLogEntry.findFirst({
      orderBy: { seq: "desc" },
      select: { seq: true, selfHash: true },
    });

    const prevHash = last?.selfHash ?? AUDIT_GENESIS_HASH;
    const timestamp = input.timestamp ?? new Date();
    const selfHash = computeAuditSelfHash({
      prevHash,
      timestampIso: timestamp.toISOString(),
      actorType: input.actorType,
      actorId,
      action: input.action,
      resource: input.resource,
      subjectId,
      payloadHash,
    });

    return tx.auditLogEntry.create({
      data: {
        actorId,
        actorType: input.actorType,
        action: input.action,
        resource: input.resource,
        subjectId,
        legalBasis,
        purpose,
        ipAddress,
        userAgent,
        payloadHash,
        prevHash,
        selfHash,
        timestamp,
      },
    });
  });
}

export interface AuditChainAnchor {
  seq: bigint;
  selfHash: string;
}

export interface AuditVerificationResult {
  valid: boolean;
  checkedCount: number;
  failedAtSeq?: bigint;
  reason?: string;
}

function hashesEqual(a: string, b: string): boolean {
  const bufA = Buffer.from(a, "utf8");
  const bufB = Buffer.from(b, "utf8");
  if (bufA.length !== bufB.length) return false;
  return timingSafeEqual(bufA, bufB);
}

/**
 * Verifica integridade completa da cadeia ordenada por `seq ASC`, detectando:
 * - Edição de qualquer coluna de um registro;
 * - Remoção de registros intermediários ou do início (lacuna em `seq`);
 * - Reescrita completa da tabela por atacante com acesso privilegiado ao banco,
 *   quando confrontada com uma âncora externa imutável (`expectedAnchor` salvo em WORM/SIEM).
 */
export function verifyAuditChain(
  entries: ReadonlyArray<AuditLogRecord>,
  expectedAnchor?: AuditChainAnchor,
): AuditVerificationResult {
  const sorted = [...entries].sort((a, b) => (a.seq < b.seq ? -1 : a.seq > b.seq ? 1 : 0));

  let expectedPrevHash = AUDIT_GENESIS_HASH;
  let expectedSeq = 1n;

  for (const entry of sorted) {
    if (entry.seq !== expectedSeq) {
      return {
        valid: false,
        checkedCount: Number(expectedSeq - 1n),
        failedAtSeq: entry.seq,
        reason: `Sequence gap detected: expected seq=${expectedSeq.toString()}, got seq=${entry.seq.toString()}`,
      };
    }

    if (!hashesEqual(entry.prevHash, expectedPrevHash)) {
      return {
        valid: false,
        checkedCount: Number(expectedSeq - 1n),
        failedAtSeq: entry.seq,
        reason: `Broken prevHash link at seq=${entry.seq.toString()}`,
      };
    }

    const recomputed = computeAuditSelfHash({
      prevHash: entry.prevHash,
      timestampIso: entry.timestamp.toISOString(),
      actorType: entry.actorType,
      actorId: entry.actorId,
      action: entry.action,
      resource: entry.resource,
      subjectId: entry.subjectId,
      payloadHash: entry.payloadHash,
    });

    if (!hashesEqual(entry.selfHash, recomputed)) {
      return {
        valid: false,
        checkedCount: Number(expectedSeq - 1n),
        failedAtSeq: entry.seq,
        reason: `Tampered payload or metadata at seq=${entry.seq.toString()}`,
      };
    }

    expectedPrevHash = entry.selfHash;
    expectedSeq += 1n;
  }

  if (expectedAnchor) {
    const anchoredEntry = sorted.find((e) => e.seq === expectedAnchor.seq);
    if (!anchoredEntry || !hashesEqual(anchoredEntry.selfHash, expectedAnchor.selfHash)) {
      return {
        valid: false,
        checkedCount: sorted.length,
        failedAtSeq: expectedAnchor.seq,
        reason: `External WORM/SIEM anchor mismatch at seq=${expectedAnchor.seq.toString()}`,
      };
    }
  }

  return { valid: true, checkedCount: sorted.length };
}
