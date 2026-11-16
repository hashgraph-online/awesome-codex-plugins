import { createHash } from "node:crypto";
import { isIP } from "node:net";

export type ConsentEventType = "GRANTED" | "REVOKED" | "SUPERSEDED" | "EXPIRED";

// Faixa etária do titular no momento do evento (LGPD Art. 14 + ECA Art. 2º). null = não aferida.
export type SubjectAgeBand = "CHILD" | "ADOLESCENT" | "ADULT";

export type ConsentChannel =
  | "WEB"
  | "MOBILE_RN"
  | "API"
  | "SIGNUP"
  | "SETTINGS_PAGE"
  | "EMAIL_OPTIN"
  | "COOKIE_BANNER";

export interface ConsentEventRecord {
  id: string;
  seq: bigint;
  subjectId: string;
  purpose: string;
  eventType: ConsentEventType;
  occurredAt: Date;
  expiresAt: Date | null;
  rootConsentId: string | null;
  policyVersionId: string;
  evidenceHash: string;
  ipAddress: string | null;
  userAgent: string | null;
  locale: string;
  channel: ConsentChannel;
  uiSnapshot: string | null;
  subjectAgeBand: SubjectAgeBand | null;
  parentalConsent: boolean | null;
  guardianId: string | null;
  propagatedTo: unknown;
}

export interface ConsentEventCreateData {
  subjectId: string;
  purpose: string;
  eventType: ConsentEventType;
  occurredAt: Date;
  expiresAt?: Date | null;
  rootConsentId?: string | null;
  policyVersionId: string;
  evidenceHash: string;
  ipAddress?: string | null;
  userAgent?: string | null;
  locale?: string;
  channel: ConsentChannel;
  uiSnapshot?: string | null;
  subjectAgeBand?: SubjectAgeBand | null;
  parentalConsent?: boolean | null;
  guardianId?: string | null;
  propagatedTo?: unknown;
}

export interface ConsentEventDelegate {
  create(args: { data: ConsentEventCreateData }): Promise<ConsentEventRecord>;
  findFirst(args: {
    where: { subjectId: string; purpose: string };
    orderBy: Array<{ occurredAt?: "asc" | "desc"; seq?: "asc" | "desc" }>;
  }): Promise<ConsentEventRecord | null>;
}

export interface ConsentLedgerDb {
  consentEvent: ConsentEventDelegate;
  $transaction<T>(fn: (tx: { consentEvent: ConsentEventDelegate }) => Promise<T>): Promise<T>;
}

export interface EvidenceContext {
  forwardedFor?: string | null;
  userAgent?: string | null;
  locale?: string;
  channel: ConsentChannel;
  uiSnapshot?: string | null;
}

export function extractValidIp(forwardedFor?: string | null): string | null {
  if (!forwardedFor) return null;
  const candidate = forwardedFor.split(",")[0]?.trim() ?? "";
  return isIP(candidate) !== 0 ? candidate : null;
}

export function computeConsentEvidenceHash(payload: {
  subjectId: string;
  purpose: string;
  eventType: ConsentEventType;
  policyVersionId: string;
  occurredAtIso: string;
  rootConsentId: string | null;
  ipAddress: string | null;
  userAgent: string | null;
  locale: string;
  channel: ConsentChannel;
  uiSnapshot: string | null;
}): string {
  const canonical = JSON.stringify({
    v: 1,
    subjectId: payload.subjectId,
    purpose: payload.purpose,
    eventType: payload.eventType,
    policyVersionId: payload.policyVersionId,
    occurredAtIso: payload.occurredAtIso,
    rootConsentId: payload.rootConsentId,
    ipAddress: payload.ipAddress,
    userAgent: payload.userAgent,
    locale: payload.locale,
    channel: payload.channel,
    uiSnapshot: payload.uiSnapshot,
  });
  return createHash("sha256").update(canonical, "utf8").digest("hex");
}

const LATEST_EVENT_ORDER: Array<{ occurredAt?: "asc" | "desc"; seq?: "asc" | "desc" }> = [
  { occurredAt: "desc" },
  { seq: "desc" },
];

export async function grantConsent(
  db: ConsentLedgerDb,
  input: {
    subjectId: string;
    purpose: string;
    policyVersionId: string;
    evidence: EvidenceContext;
    occurredAt?: Date;
    expiresAt?: Date | null;
    subjectAgeBand?: SubjectAgeBand | null;
    parentalConsent?: boolean | null;
    guardianId?: string | null;
    propagatedTo?: string[];
  },
): Promise<ConsentEventRecord> {
  // Art. 14, § 1º exige consentimento específico e em destaque de pai/mãe/responsável apenas para
  // CRIANÇAS (< 12). Adolescentes consentem por si (Enunciado CD/ANPD nº 1/2023), observado o melhor
  // interesse; a vinculação de conta do Art. 24 do ECA Digital é dever distinto (lgpd-eca-digital-minors).
  if (input.subjectAgeBand === "CHILD" && (input.parentalConsent !== true || !input.guardianId)) {
    throw new Error(
      "Consent-based processing for children requires specific parental/guardian consent with an identified guardian (LGPD Art. 14, § 1º).",
    );
  }

  const occurredAt = input.occurredAt ?? new Date();
  const ipAddress = extractValidIp(input.evidence.forwardedFor);
  const userAgent = input.evidence.userAgent ?? null;
  const locale = input.evidence.locale ?? "pt-BR";
  const uiSnapshot = input.evidence.uiSnapshot ?? null;

  const evidenceHash = computeConsentEvidenceHash({
    subjectId: input.subjectId,
    purpose: input.purpose,
    eventType: "GRANTED",
    policyVersionId: input.policyVersionId,
    occurredAtIso: occurredAt.toISOString(),
    rootConsentId: null,
    ipAddress,
    userAgent,
    locale,
    channel: input.evidence.channel,
    uiSnapshot,
  });

  return db.consentEvent.create({
    data: {
      subjectId: input.subjectId,
      purpose: input.purpose,
      eventType: "GRANTED",
      occurredAt,
      expiresAt: input.expiresAt ?? null,
      rootConsentId: null,
      policyVersionId: input.policyVersionId,
      evidenceHash,
      ipAddress,
      userAgent,
      locale,
      channel: input.evidence.channel,
      uiSnapshot,
      subjectAgeBand: input.subjectAgeBand ?? null,
      parentalConsent: input.parentalConsent ?? null,
      guardianId: input.guardianId ?? null,
      propagatedTo: input.propagatedTo ?? undefined,
    },
  });
}

export async function revokeConsent(
  db: ConsentLedgerDb,
  input: {
    subjectId: string;
    purpose: string;
    evidence: EvidenceContext;
    occurredAt?: Date;
    propagatedTo?: string[];
  },
): Promise<{ revoked: boolean; event: ConsentEventRecord | null }> {
  return db.$transaction(async (tx) => {
    const latest = await tx.consentEvent.findFirst({
      where: { subjectId: input.subjectId, purpose: input.purpose },
      orderBy: LATEST_EVENT_ORDER,
    });

    if (!latest || latest.eventType !== "GRANTED") {
      return { revoked: false, event: null };
    }

    const occurredAt = input.occurredAt ?? new Date();
    const rootConsentId = latest.rootConsentId ?? latest.id;
    const ipAddress = extractValidIp(input.evidence.forwardedFor);
    const userAgent = input.evidence.userAgent ?? null;
    const locale = input.evidence.locale ?? latest.locale;
    const uiSnapshot = input.evidence.uiSnapshot ?? null;

    const evidenceHash = computeConsentEvidenceHash({
      subjectId: input.subjectId,
      purpose: input.purpose,
      eventType: "REVOKED",
      policyVersionId: latest.policyVersionId,
      occurredAtIso: occurredAt.toISOString(),
      rootConsentId,
      ipAddress,
      userAgent,
      locale,
      channel: input.evidence.channel,
      uiSnapshot,
    });

    const event = await tx.consentEvent.create({
      data: {
        subjectId: input.subjectId,
        purpose: input.purpose,
        eventType: "REVOKED",
        occurredAt,
        expiresAt: null,
        rootConsentId,
        policyVersionId: latest.policyVersionId,
        evidenceHash,
        ipAddress,
        userAgent,
        locale,
        channel: input.evidence.channel,
        uiSnapshot,
        subjectAgeBand: latest.subjectAgeBand,
        parentalConsent: latest.parentalConsent,
        guardianId: latest.guardianId,
        propagatedTo: input.propagatedTo ?? undefined,
      },
    });

    return { revoked: true, event };
  });
}

export async function recordPolicySupersession(
  db: ConsentLedgerDb,
  input: {
    subjectId: string;
    purpose: string;
    newPolicyVersionId: string;
    occurredAt?: Date;
  },
): Promise<ConsentEventRecord | null> {
  return db.$transaction(async (tx) => {
    const latest = await tx.consentEvent.findFirst({
      where: { subjectId: input.subjectId, purpose: input.purpose },
      orderBy: LATEST_EVENT_ORDER,
    });

    if (!latest || latest.eventType !== "GRANTED") {
      return null;
    }

    const occurredAt = input.occurredAt ?? new Date();
    const rootConsentId = latest.rootConsentId ?? latest.id;
    const evidenceHash = computeConsentEvidenceHash({
      subjectId: input.subjectId,
      purpose: input.purpose,
      eventType: "SUPERSEDED",
      policyVersionId: input.newPolicyVersionId,
      occurredAtIso: occurredAt.toISOString(),
      rootConsentId,
      ipAddress: null,
      userAgent: null,
      locale: latest.locale,
      channel: "API",
      uiSnapshot: null,
    });

    return tx.consentEvent.create({
      data: {
        subjectId: input.subjectId,
        purpose: input.purpose,
        eventType: "SUPERSEDED",
        occurredAt,
        expiresAt: null,
        rootConsentId,
        policyVersionId: input.newPolicyVersionId,
        evidenceHash,
        ipAddress: null,
        userAgent: null,
        locale: latest.locale,
        channel: "API",
        uiSnapshot: null,
        subjectAgeBand: latest.subjectAgeBand,
        parentalConsent: latest.parentalConsent,
        guardianId: latest.guardianId,
      },
    });
  });
}

export async function hasActiveConsent(
  db: Pick<ConsentLedgerDb, "consentEvent">,
  input: {
    subjectId: string;
    purpose: string;
    requiredPolicyVersionId?: string;
    now?: Date;
  },
): Promise<boolean> {
  const now = input.now ?? new Date();
  const latest = await db.consentEvent.findFirst({
    where: { subjectId: input.subjectId, purpose: input.purpose },
    orderBy: LATEST_EVENT_ORDER,
  });

  if (!latest || latest.eventType !== "GRANTED") {
    return false;
  }

  if (latest.expiresAt && latest.expiresAt.getTime() <= now.getTime()) {
    return false;
  }

  if (
    input.requiredPolicyVersionId &&
    latest.policyVersionId !== input.requiredPolicyVersionId
  ) {
    return false;
  }

  return true;
}
