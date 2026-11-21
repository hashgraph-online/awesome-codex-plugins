---
name: lgpd-audit-logging
description: Design and implement tamper-evident, transactionally serialized audit logging as a recommended engineering control for LGPD accountability (Art. 6, X) and security (Art. 46). Outputs Prisma schema, concurrency-safe hash-chain writer, DB write-protection triggers, and external WORM/SIEM anchoring verification.
---

# Audit Logging — Trilha de Auditoria Tamper-Evident

Controle de engenharia voltado a sustentar **responsabilização e prestação de contas (`Art. 6º, X`)** e **segurança da informação (`Art. 46`)**.

> **Distinção normativa importante:**
> 1. **A LGPD não exige expressamente o uso de *hash chain*.** A lei exige medidas técnicas e administrativas aptas a proteger os dados (`Art. 46`) e demonstração de eficácia (`Art. 6º, X`). O encadeamento criptográfico (*hash chain*) é classificado aqui como **controle técnico recomendado** para detecção de adulteração (*tamper-evidence*), não como imposição literal do texto legal.
> 2. **Prazo de retenção:** o prazo legal mínimo de **5 anos** do **Art. 10 da Resolução CD/ANPD nº 15/2024** refere-se especificamente ao **registro de incidentes de segurança com dados pessoais**. Para logs operacionais de auditoria (acessos administrativos, exportações, DSAR, consentimento), defina retenção proporcional aos prazos prescricionais e de fiscalização aplicáveis (ex.: 6 meses mínimos do Art. 15 do Marco Civil para logs de acesso a aplicações; 3 a 5 anos para trilhas probatórias de DSAR/consentimento sob Art. 6º, X e Res. 4/2023).

## Por que uma *hash chain* sozinha NÃO é imutável

Uma cadeia de hashes armazenada apenas na mesma tabela PostgreSQL detecta edições pontuais ingênuas, mas **sofre duas falhas clássicas se mal implementada**:
1. **Condição de corrida (*race condition*)**: duas requisições paralelas que leem o último hash fora de uma transação serializada gravam o **mesmo `prevHash`**, bifurcando e quebrando a cadeia em produção.
2. **Reescrita privilegiada**: um invasor ou administrador malicioso com permissão de `UPDATE`/`DELETE` no banco pode alterar um registro antigo e **recalcular todos os hashes subsequentes** em segundos.

Para que a trilha seja confiável de verdade, combine **quatro camadas**:
1. **Serialização transacional + sequência monotônica (`seq BigInt`)**: use `pg_advisory_xact_lock` dentro de `db.$transaction(...)` e ordene por `seq` (nunca apenas por `timestamp`, que pode empatar no mesmo milissegundo).
2. **Restrição de privilégios e triggers no PostgreSQL**: a role da aplicação deve ter apenas `SELECT, INSERT` (`REVOKE UPDATE, DELETE, TRUNCATE`) + trigger bloqueando mutações.
3. **Mapeamento explícito de colunas**: nunca faça spread (`...entry`) repassando objetos `Request` ou payloads brutos para o Prisma, e extraia apenas o primeiro IP válido de `x-forwarded-for` para não quebrar colunas `@db.Inet`.
4. **Ancoragem externa periódica (WORM / SIEM)**: publique periodicamente (ex.: a cada hora/dia) o par `(seq, selfHash)` mais recente em destino externo imutável (S3 Object Lock em modo Compliance, CloudWatch Logs / GCP Cloud Logging em conta segregada) e valide-o em `verifyAuditChain()`.

## Artefatos de referência prontos e testados

- **Schema Prisma**: [`assets/audit-log.prisma`](assets/audit-log.prisma)
- **Implementação TypeScript serializada + verificador**: [`assets/audit-log.ts`](assets/audit-log.ts)

## Uso recomendado em rotas críticas

```ts
import { logAudit, verifyAuditChain } from "@/lib/privacy/audit-log";

await logAudit(prisma, {
  actorId: session.user.id,
  actorType: "USER",
  action: "DSAR_EXPORT_COMPLETED",
  resource: `User:${session.user.id}`,
  subjectId: session.user.id,
  legalBasis: "ART_18_II",
  purpose: "subject_data_export",
  // NUNCA passe PII em claro — apenas metadados redigidos ou hashes
  redactedMetadata: { format: "json", bundleSha256: bundleHash },
  req,
});
```

## Eventos prioritários para registrar (sem PII em claro)

- Autenticação administrativa, elevação de privilégio e mudanças de RBAC
- Leitura/exportação administrativa de dados pessoais ou sensíveis de terceiros
- Operações do ledger de consentimento (`GRANTED`, `REVOKED`, `SUPERSEDED`)
- Ciclo completo de DSAR (recebimento, verificação proporcional de identidade, atendimento, eventual recusa fundamentada)
- Execução de jobs de retenção, anonimização e *crypto-shredding*

## Proteção de banco + Ancoragem externa

1. Aplique na tabela `"AuditLogEntry"` a mesma trigger de bloqueio de `UPDATE`, `DELETE` e `TRUNCATE` (ver `lgpd-consent-schema/assets/consent-append-only.sql`) e revogue permissões destrutivas da role de aplicação.
2. Agende job diário que:
   - Executa `verifyAuditChain(entries, lastExternalAnchor)`;
   - Grava o novo `(seq, selfHash)` em bucket S3 Object Lock (WORM) ou SIEM segregado;
   - Dispara alerta imediato para Segurança e Encarregado em caso de divergência.

## Status update

```markdown
## F8 / L8b — Audit logging ✓
- Modelo `AuditLogEntry` com `seq` monotônico validado
- `logAudit()` serializado com `pg_advisory_xact_lock` e sanitização de IP
- Trigger append-only + revogação de `UPDATE/DELETE` configurados
- Verificação periódica `verifyAuditChain()` + âncora externa configuradas
```
