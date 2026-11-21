---
name: lgpd-consent-schema
description: Design an event-sourced, database-enforced append-only consent ledger satisfying LGPD Art. 8 (free, informed, unambiguous consent, burden of proof, easy revocation, policy version supersession), Art. 14, and Art. 18, IX. Use when user asks for "consent schema", "consent ledger", "schema de consentimento", "Prisma consentimento", or integrates consent capture/revocation with Better Auth, NextAuth, or Clerk. Outputs Prisma schema, PostgreSQL append-only triggers, and TypeScript helpers.
---

# Consent Ledger Orientado a Eventos (Prisma + PostgreSQL)

Implementação técnica de consentimento quando a base legal da atividade é o **consentimento** (`Art. 7º, I` ou `Art. 11, I`, e `Art. 14, § 1º` para crianças).

> **Quando usar:** apenas para finalidades efetivamente baseadas em consentimento (ex.: comunicações de marketing sem legítimo interesse aplicável, cookies/trackers não essenciais, opt-in biométrico facultativo). **Não crie registros de "consentimento" para atividades cuja base real é execução de contrato (`Art. 7º, V`) ou obrigação legal (`Art. 7º, II`).**

## Arquitetura: sequência de eventos imutáveis

Em vez de mutar uma linha ou misturar `grantedAt`/`revokedAt` no mesmo campo de ordenação, modele o consentimento como uma **sequência cronológica de eventos (`ConsentEvent`)**:

- `GRANTED` — consentimento concedido para `(subjectId, purpose, policyVersionId)` com hash de evidência;
- `REVOKED` — consentimento revogado pelo titular/responsável (`Art. 8º, § 5º`), referenciando o evento original via `rootConsentId`;
- `SUPERSEDED` — substituído quando uma mudança material de finalidade/política invalida o consentimento anterior (`Art. 8º, § 6º`);
- `EXPIRED` — expirado quando a concessão possuía TTL explícito (`expiresAt`).

Cada evento possui:
- `occurredAt: DateTime` + `seq: BigInt @default(autoincrement())` — **ordenação monotônica determinística** (`orderBy: [{ occurredAt: "desc" }, { seq: "desc" }]`), evitando que uma revogação no mesmo milissegundo de um grant mantenha o consentimento ativo por erro de ordenação;
- `rootConsentId` — linhagem direta até o `GRANTED` original;
- `policyVersionId` + `evidenceHash` + `channel` — preenchidos em **todos** os eventos (sem omissão de campos obrigatórios do Prisma).

## Artefatos de referência prontos e testados

- **Schema Prisma**: [`assets/consent-schema.prisma`](assets/consent-schema.prisma)
- **Trigger PostgreSQL append-only real**: [`assets/consent-append-only.sql`](assets/consent-append-only.sql) — bloqueia `UPDATE`, `DELETE` e `TRUNCATE` diretamente no banco (além de `REVOKE UPDATE, DELETE` na role da aplicação).
- **Módulo TypeScript tipado**: [`assets/consent-ledger.ts`](assets/consent-ledger.ts) (`grantConsent`, `revokeConsent`, `recordPolicySupersession`, `hasActiveConsent`).

## Proteção append-only efetiva no banco

Comentário em código não garante imutabilidade. Inclua na migration do Prisma o trigger de [`assets/consent-append-only.sql`](assets/consent-append-only.sql):

```sql
CREATE TRIGGER trg_consent_event_no_update_delete
BEFORE UPDATE OR DELETE ON "ConsentEvent"
FOR EACH ROW EXECUTE FUNCTION prevent_consent_event_mutation();
```

## Integração com Better Auth (sem coleta excessiva)

Não obrigue `dateOfBirth` para todos os usuários em aplicações B2B/adultas sem necessidade (Art. 6º, III — minimização). Em produtos sujeitos ao ECA Digital (`lgpd-eca-digital-minors`), prefira sinais de idade de SO/loja (Decreto nº 12.880/2026) ou faixa etária verificada:

```ts
// auth.ts
export const auth = betterAuth({
  database: prismaAdapter(db, { provider: "postgresql" }),
  user: {
    additionalFields: {
      ageBandVerified: { type: "string", required: false }, // ex.: "18+" | "17" | "12-16" | "<12" (Art. 24 ECA Digital: até 16 anos inclusive)
    },
  },
});
// Capture consentimentos opcionais em UX dedicada e desacoplada (/api/consent/grant),
// nunca embutidos como aceitação forçada nos Termos de Uso (Art. 8º, § 4º e Art. 9º, § 2º).
```

## Concessão, Revogação e Consulta de Estado Atual

Use os helpers de [`assets/consent-ledger.ts`](assets/consent-ledger.ts):

```ts
import { grantConsent, revokeConsent, hasActiveConsent } from "@/lib/privacy/consent-ledger";

// 1. Conceder consentimento específico
await grantConsent(prisma, {
  subjectId: session.user.id,
  purpose: "marketing_email",
  policyVersionId: currentPolicy.id,
  evidence: {
    forwardedFor: req.headers.get("x-forwarded-for"),
    userAgent: req.headers.get("user-agent"),
    locale: "pt-BR",
    channel: "SETTINGS_PAGE",
    uiSnapshot: "sha256:banner_v3_2_ptbr",
  },
});

// 2. Revogar (Art. 8º, § 5º) — preenche todos os campos obrigatórios + rootConsentId
const result = await revokeConsent(prisma, {
  subjectId: session.user.id,
  purpose: "marketing_email",
  evidence: {
    forwardedFor: req.headers.get("x-forwarded-for"),
    userAgent: req.headers.get("user-agent"),
    channel: "SETTINGS_PAGE",
  },
  propagatedTo: ["customer_io"],
});

if (result.revoked) {
  await propagateRevocationToOperators(session.user.id, "marketing_email");
}

// 3. Consultar estado vigente antes de executar a finalidade
const allowed = await hasActiveConsent(prisma, {
  subjectId: session.user.id,
  purpose: "marketing_email",
  requiredPolicyVersionId: currentPolicy.requiresReconsent ? currentPolicy.id : undefined,
});
```

## Crianças e adolescentes (`subjectAgeBand`)

- `subjectAgeBand: "CHILD"` (< 12): `grantConsent` exige `parentalConsent: true` **e** `guardianId` identificado (`Art. 14, § 1º`).
- `subjectAgeBand: "ADOLESCENT"` (12 a < 18): o adolescente consente por si (**Enunciado CD/ANPD nº 1/2023**), com o melhor interesse prevalecendo. Não force consentimento parental aqui.
- A vinculação da conta ao responsável (até 16 anos, `Art. 24` da Lei nº 15.211/2025) é outro dever, que não depende da base legal. Use `Guardian`/`MinorLink` e veja `lgpd-eca-digital-minors`.
- Guarde o **resultado** da aferição de idade em `AgeAssurance` (faixa, origem, método), nunca documento ou biometria bruta (`Art. 13` da Lei nº 15.211/2025).

## Requisitos de UX (Art. 8º e Art. 9º)

- **Zero checkboxes pré-marcados** — manifestação deve ser livre e inequívoca.
- **Granularidade por finalidade** — uma escolha independente para cada finalidade distinta.
- **Assimetria zero na revogação** — revogar deve ser gratuito e tão simples quanto conceder (`Art. 8º, § 5º`).
- **Mudança material de finalidade (`Art. 8º, § 6º`)** — emitir nova `PolicyVersion` com `requiresReconsent = true` e registrar `SUPERSEDED` até nova coleta.

## Status update

```markdown
## F6 / L7b — Consent ledger ✓
- Modelo `ConsentEvent` + `PolicyVersion` validado em `prisma/schema.prisma`
- Trigger PostgreSQL append-only aplicada em migration
- Helpers `grantConsent`, `revokeConsent` e `hasActiveConsent` testados
- Propagação de revogação configurada para operadores: {lista}
```
