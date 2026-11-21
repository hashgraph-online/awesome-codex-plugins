# DSAR Endpoints — Next.js + Better Auth + Prisma

Exemplos alinhados aos módulos testados desta coleção:
- Ledger de eventos de consentimento: `skills/lgpd-consent-schema/assets/consent-ledger.ts`
- Auditoria serializada sem vazamento de `req`/payload: `skills/lgpd-audit-logging/assets/audit-log.ts`
- Cálculo de SLA (Padrão vs. ATPP) e disposição de eliminação: `skills/lgpd-dsar/assets/dsar-sla.ts`

## GET /api/me — Confirmação e Acesso Simplificado (Art. 18, I e II + Art. 19, I)

Para usuários autenticados, entrega resposta simplificada imediata (nota: em canais manuais/assíncronos, ATPPs dispõem de até **15 dias** para a declaração simplificada conforme **Res. CD/ANPD nº 2/2022, Art. 14, I**).

```ts
// app/api/me/route.ts
import { auth } from "@/lib/auth";
import { db } from "@/lib/db";
import { hasActiveConsent } from "@/lib/privacy/consent-ledger";
import { logAudit } from "@/lib/privacy/audit-log";

const CONSENT_PURPOSES = ["marketing_email", "analytics_cookies"] as const;

export async function GET(req: Request) {
  const session = await auth.api.getSession({ headers: req.headers });
  if (!session) return new Response("Unauthorized", { status: 401 });

  const userId = session.user.id;
  const user = await db.user.findUnique({
    where: { id: userId },
    select: { id: true, email: true, fullName: true, createdAt: true },
  });

  const activeConsents = await Promise.all(
    CONSENT_PURPOSES.map(async (purpose) => ({
      purpose,
      active: await hasActiveConsent(db, { subjectId: userId, purpose }),
    })),
  );

  await logAudit(db, {
    actorId: userId,
    actorType: "USER",
    action: "DSAR_SIMPLIFIED_ACCESS",
    resource: `User:${userId}`,
    subjectId: userId,
    legalBasis: "ART_18_I_II",
    purpose: "dsar_confirmation_simplified",
    redactedMetadata: { format: "simplified_json" },
    req,
  });

  return Response.json({
    confirmation: true,
    profile: user,
    consents: activeConsents,
    privacyContact: {
      nameOrChannel: process.env.PRIVACY_CONTACT_NAME ?? "Canal de Privacidade",
      email: process.env.PRIVACY_CONTACT_EMAIL,
    },
    completeExportEndpoint: "/api/me/export",
  });
}
```

## GET /api/me/export — Declaração Completa e Portabilidade (Art. 18, II e V + Art. 19, II)

Prazo máximo legal quando processado de forma assíncrona: **15 dias corridos** para controlador padrão (`Art. 19, II`) ou **30 dias corridos** para ATPP (`Res. 2/2022, Art. 14, caput`).

```ts
// app/api/me/export/route.ts
import { createHash } from "node:crypto";
import { auth } from "@/lib/auth";
import { db } from "@/lib/db";
import { logAudit } from "@/lib/privacy/audit-log";

export async function GET(req: Request) {
  const session = await auth.api.getSession({ headers: req.headers });
  if (!session) return new Response("Unauthorized", { status: 401 });

  const url = new URL(req.url);
  const format = url.searchParams.get("format") === "portable" ? "portable" : "complete";

  // Deve incluir dados cadastrais, eventos de consentimento, origem, critérios,
  // finalidades e categorias de destinatários (Art. 19, II), resguardado segredo comercial.
  const payload = await buildSubjectDataPackage(session.user.id, format);
  const serialized = JSON.stringify(payload, null, 2);
  const bundleSha256 = createHash("sha256").update(serialized, "utf8").digest("hex");

  await logAudit(db, {
    actorId: session.user.id,
    actorType: "USER",
    action: "DSAR_EXPORT_FULFILLED",
    resource: `User:${session.user.id}`,
    subjectId: session.user.id,
    legalBasis: format === "portable" ? "ART_18_V" : "ART_19_II",
    purpose: "dsar_complete_export",
    redactedMetadata: { format, bundleSha256 },
    req,
  });

  return new Response(serialized, {
    headers: {
      "Content-Type": "application/json; charset=utf-8",
      "Content-Disposition": `attachment; filename="lgpd-${format}-${Date.now()}.json"`,
    },
  });
}
```

## PATCH /api/me/profile — Correção + Propagação a Operadores (Art. 18, III e § 6º)

```ts
// app/api/me/profile/route.ts
import { auth } from "@/lib/auth";
import { db } from "@/lib/db";
import { logAudit } from "@/lib/privacy/audit-log";

const EDITABLE_FIELDS = new Set(["fullName", "phone", "addressLine1", "city"]);

export async function PATCH(req: Request) {
  const session = await auth.api.getSession({ headers: req.headers });
  if (!session) return new Response("Unauthorized", { status: 401 });

  const body = (await req.json()) as Record<string, unknown>;
  const updates = Object.fromEntries(
    Object.entries(body).filter(([k, v]) => EDITABLE_FIELDS.has(k) && typeof v === "string"),
  );

  await db.$transaction(async (tx) => {
    await tx.user.update({ where: { id: session.user.id }, data: updates });
    // Art. 18, § 6º — enfileira propagação imediata aos operadores relevantes
    await tx.operatorPropagationOutbox.createMany({
      data: ["customer_io", "stripe"].map((operatorSlug) => ({
        subjectId: session.user.id,
        operatorSlug,
        operation: "CORRECTION",
      })),
    });
  });

  await logAudit(db, {
    actorId: session.user.id,
    actorType: "USER",
    action: "DSAR_CORRECTION_FULFILLED",
    resource: `User:${session.user.id}`,
    subjectId: session.user.id,
    legalBasis: "ART_18_III",
    purpose: "dsar_rectification",
    redactedMetadata: { updatedFields: Object.keys(updates) },
    req,
  });

  return Response.json({ updatedFields: Object.keys(updates) });
}
```

## POST /api/me/erasure — Eliminação, Bloqueio Seletivo, Tombstone de Backup e Propagação (Arts. 15, 16 e 18, VI e § 6º)

```ts
// app/api/me/erasure/route.ts
import { createHmac } from "node:crypto";
import { auth } from "@/lib/auth";
import { db } from "@/lib/db";
import { planErasureDisposition } from "@/lib/privacy/dsar-sla";
import { logAudit } from "@/lib/privacy/audit-log";

export async function POST(req: Request) {
  const session = await auth.api.getSession({ headers: req.headers });
  if (!session) return new Response("Unauthorized", { status: 401 });

  const userId = session.user.id;
  const { confirmation } = (await req.json()) as { confirmation?: string };
  if (confirmation !== "EXCLUIR MINHA CONTA") {
    return new Response("Confirmation mismatch", { status: 400 });
  }

  // Consulta apenas obrigações legais específicas vigentes (ex.: NF-e emitida sob CTN Art. 173, I)
  const obligations = await findSpecificStatutoryRetentions(userId);
  const disposition = planErasureDisposition(obligations);

  const subjectHmac = createHmac("sha256", Buffer.from(process.env.BACKUP_SUPPRESSION_KEY_B64!, "base64"))
    .update(userId, "utf8")
    .digest("hex");

  await db.$transaction(async (tx) => {
    if (disposition.mode === "BLOCK_AND_MINIMIZE") {
      await tx.user.update({
        where: { id: userId },
        data: {
          email: `blocked-${userId}@erased.invalid`,
          phone: null,
          avatarUrl: null,
          marketingOptIn: false,
          blockedAt: new Date(),
          retentionUntil: disposition.retainUntil,
        },
      });
    } else {
      await tx.user.delete({ where: { id: userId } });
    }

    // Evita ressurreição caso um snapshot de backup anterior precise ser restaurado
    await tx.erasureSuppressionTombstone.upsert({
      where: { subjectHmac },
      create: {
        subjectHmac,
        scope:
          disposition.mode === "HARD_DELETE"
            ? "FULL_ERASURE"
            : "PARTIAL_NON_STATUTORY_FIELDS",
      },
      update: { erasedAt: new Date() },
    });

    // Art. 18, § 6º — propaga imediatamente aos operadores externos
    await tx.operatorPropagationOutbox.createMany({
      data: ["mixpanel", "customer_io", "sentry"].map((operatorSlug) => ({
        subjectId: userId,
        operatorSlug,
        operation: "ERASURE",
      })),
    });
  });

  await auth.api.revokeAllSessions({ headers: req.headers });

  await logAudit(db, {
    actorId: userId,
    actorType: "USER",
    action: "DSAR_ERASURE_PROCESSED",
    resource: `User:${userId}`,
    subjectId: userId,
    legalBasis: "ART_18_VI_ART_16",
    purpose: "dsar_erasure",
    redactedMetadata: {
      mode: disposition.mode,
      statutoryBases: disposition.mode === "BLOCK_AND_MINIMIZE" ? disposition.statutoryBases : [],
    },
    req,
  });

  return Response.json({
    mode: disposition.mode,
    retainedUntil: disposition.retainUntil?.toISOString() ?? null,
    statutoryBases: disposition.mode === "BLOCK_AND_MINIMIZE" ? disposition.statutoryBases : [],
  });
}
```

## POST /api/consent/revoke — Revogação Orientada a Eventos (Art. 8º, § 5º e Art. 18, IX)

Usa o mesmo modelo `ConsentEvent` de `lgpd-consent-schema` (preenchendo `rootConsentId`, `policyVersionId`, `occurredAt`, `channel` e `evidenceHash` sem gambiarras semânticas):

```ts
// app/api/consent/revoke/route.ts
import { auth } from "@/lib/auth";
import { db } from "@/lib/db";
import { revokeConsent } from "@/lib/privacy/consent-ledger";
import { logAudit } from "@/lib/privacy/audit-log";

export async function POST(req: Request) {
  const session = await auth.api.getSession({ headers: req.headers });
  if (!session) return new Response("Unauthorized", { status: 401 });

  const { purpose } = (await req.json()) as { purpose?: string };
  if (!purpose) return new Response("Missing purpose", { status: 400 });

  const result = await revokeConsent(db, {
    subjectId: session.user.id,
    purpose,
    evidence: {
      forwardedFor: req.headers.get("x-forwarded-for"),
      userAgent: req.headers.get("user-agent"),
      channel: "API",
    },
    propagatedTo: ["mixpanel", "customer_io"],
  });

  if (result.revoked) {
    await db.operatorPropagationOutbox.createMany({
      data: ["mixpanel", "customer_io"].map((operatorSlug) => ({
        subjectId: session.user.id,
        operatorSlug,
        operation: "CONSENT_REVOCATION",
      })),
    });
  }

  await logAudit(db, {
    actorId: session.user.id,
    actorType: "USER",
    action: "CONSENT_REVOKED",
    resource: `Consent:${session.user.id}:${purpose}`,
    subjectId: session.user.id,
    legalBasis: "ART_8_5_ART_18_IX",
    purpose,
    redactedMetadata: { revoked: result.revoked, rootConsentId: result.event?.rootConsentId ?? null },
    req,
  });

  return Response.json({ revoked: result.revoked, purpose });
}
```
