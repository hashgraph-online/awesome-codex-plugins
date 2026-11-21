---
name: lgpd-encryption-keys
description: Configure encryption in transit, cloud storage/volume encryption at rest, application-level column encryption, blind indexing, and KMS key management as engineering controls aligned with LGPD Art. 46 and ANPD's Information Security Guide. Outputs tested AES-256-GCM + Prisma query extension handlers.
---

# Encryption & Key Management

Controles técnicos de criptografia e gestão de chaves voltados a atender o dever geral de segurança do **Art. 46 da LGPD** e as recomendações do *Guia Orientativo de Segurança da Informação para Agentes de Tratamento de Pequeno Porte* da ANPD.

> **Exigência legal vs. referência de engenharia:**
> O **Art. 46 da LGPD** exige medidas técnicas e administrativas aptas a proteger os dados pessoais, mas **não estipula em lei** versões específicas de protocolo (TLS 1.3), *certificate pinning*, intervalos fixos de rotação de chaves ou algoritmos nominais. Os parâmetros abaixo são **referências recomendadas de engenharia de segurança** (e reduzem drasticamente o impacto regulatório em incidentes — Art. 48 e Res. CD/ANPD nº 15/2024). Avalie sempre o risco operacional concreto (por exemplo, *certificate pinning* em apps mobile exige automação rigorosa de rotação e chaves de backup para não inutilizar o app dos usuários).

## As 3 camadas de criptografia (e o que cada uma realmente protege)

### 1. Em trânsito (rede)
- **TLS 1.2+ (preferencialmente TLS 1.3)** em toda comunicação externa (`HTTPS`) e conexões com banco/cache (`sslmode=verify-full` no PostgreSQL).
- **HSTS** (`Strict-Transport-Security`) em aplicações web.
- **Certificate pinning em mobile**: recomendado apenas em fluxos de altíssimo risco (ex.: financeiro/saúde) **desde que** acompanhado de estratégia de *pinning* da SPKI intermediária/backup e atualização remota segura.

### 2. Em repouso na infraestrutura (Storage / Volume Encryption ≠ TDE nativo do PostgreSQL)
- **Correção técnica importante**: o PostgreSQL comunitário **não possui TDE (*Transparent Data Encryption*) nativo embutido** por padrão (diferentemente de Oracle/SQL Server ou distribuições específicas como EDB / extensões `pg_tde`).
- O que provedores como **AWS RDS/Aurora**, **GCP Cloud SQL** e **Supabase/Neon** entregam por padrão é **criptografia de volumes de armazenamento, snapshots e WAL em nível de infraestrutura/bloco** (AES-256 gerenciado via KMS).
- **O que isso protege**: roubo físico de discos ou vazamento de snapshots brutos de infraestrutura.
- **O que isso NÃO protege**: vazamento via credencial de banco comprometida, SQL injection, dump lógico (`pg_dump`) ou acesso indevido de DBA — pois o banco devolve o dado em claro para qualquer sessão autenticada.

### 3. Em nível de aplicação / coluna (Envelope & Field-Level Encryption)
Para atributos de alta criticidade (dados sensíveis do Art. 11, tokens de integração, CPF de responsáveis legais, segredos financeiros), cifre **na aplicação antes de enviar ao banco**:
- **Algoritmo autenticado**: `AES-256-GCM` com IV aleatório de 96 bits (12 bytes) por escrita + AAD vinculando o contexto (`"Guardian.cpfCiphertext"`) para impedir transplante de ciphertext entre colunas.
- **Versionamento de chave (`enc:v1:...`, `enc:v2:...`)**: permite rotacionar chaves no KMS sem quebrar a leitura de registros antigos e re-cifrar gradualmente em background.
- **Busca por igualdade sem expor o dado (*Blind Index*)**: como o IV aleatório gera ciphertexts diferentes para o mesmo CPF, mantenha uma coluna auxiliar `cpfBlindIndex = HMAC-SHA256(blindKey, cpfNormalizado)` usando **uma chave KMS distinta da chave de cifragem**.

## Implementação de referência testada

Veja [`assets/field-encryption.ts`](assets/field-encryption.ts), que implementa:
- `encryptField` / `decryptField` com `Keyring` versionado e AAD;
- `computeBlindIndex` com HMAC-SHA256;
- `createPrismaModelEncryptionHandlers` cobrindo os caminhos de escrita (`create`, `createMany`, `createManyAndReturn`, `update`, `updateMany`, `upsert`) e leitura (`findUnique`, `findUniqueOrThrow`, `findFirst`, `findFirstOrThrow`, `findMany`).

```ts
import { PrismaClient } from "@prisma/client";
import { createPrismaModelEncryptionHandlers } from "@/lib/privacy/field-encryption";

const guardianEncryption = createPrismaModelEncryptionHandlers({
  keyring: {
    currentVersion: 2,
    keys: {
      1: Buffer.from(process.env.KMS_DATA_KEY_V1_B64!, "base64"),
      2: Buffer.from(process.env.KMS_DATA_KEY_V2_B64!, "base64"),
    },
  },
  blindKey: Buffer.from(process.env.KMS_BLIND_INDEX_KEY_B64!, "base64"),
  fields: [
    {
      field: "cpfCiphertext",
      aadContext: "Guardian.cpfCiphertext",
      blindIndexField: "cpfBlindIndex",
      normalizeForBlindIndex: (cpf) => cpf.replace(/\D/g, ""),
    },
  ],
});

export const db = new PrismaClient().$extends({
  query: {
    guardian: guardianEncryption,
  },
});
```

### Limites conhecidos de extensões Prisma (documente para o time!)
Nenhuma extensão de ORM é 100% mágica. `createPrismaModelEncryptionHandlers` **não intercepta automaticamente**:
1. Queries SQL cruas (`$queryRaw`, `$executeRaw`) — cifre/decifre explicitamente usando `encryptField`/`decryptField`;
2. Escritas aninhadas dentro de outro model (`user.create({ data: { guardian: { create: ... } } })`) se o handler estiver registrado apenas em `guardian` — prefira criar via serviço dedicado ou registrar validação na camada de domínio;
3. Filtros `contains` / `startsWith` / `ORDER BY` sobre colunas cifradas — use `cpfBlindIndex` apenas para igualdade exata.

## Gestão de chaves (KMS) e Crypto-shredding

- **Segregação**: chaves distintas para cifragem (`AES-256-GCM`) e para índices cegos (`HMAC-SHA256`), armazenadas em AWS KMS, GCP Cloud KMS, Azure Key Vault ou HashiCorp Vault com auditoria de uso ativa.
- **Senhas de usuários (Better Auth)**: hashing unidirecional lento (`Argon2id` ou `scrypt`/`bcrypt` com custo adequado) — senha **nunca** é cifrada de forma reversível.
- **Crypto-shredding seletivo**: quando backups imutáveis impedem expurgo físico imediato, cifrar os atributos elimináveis de cada titular com uma Data Encryption Key (DEK) individual envelopada pelo KMS permite inutilizar criptograficamente esses dados destruindo a DEK correspondente (ver `lgpd-retention-erasure`).

## Status update

```markdown
## F7 / L8a — Encryption & Key Management ✓
- TLS em trânsito (incluindo `sslmode=verify-full` no banco) verificado
- Criptografia de storage/volumes e snapshots confirmada no provedor cloud
- Cifragem de aplicação (`AES-256-GCM` versionado + blind index HMAC) implementada para campos críticos
- Chaves segregadas no KMS com trilha de auditoria ativa
```
