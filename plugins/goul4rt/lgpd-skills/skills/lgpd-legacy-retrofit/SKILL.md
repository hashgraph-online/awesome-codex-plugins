---
name: lgpd-legacy-retrofit
description: Run a code-level privacy discovery, gap analysis, and prioritized retrofit plan for an existing software project. Entry point for Pipeline B when user asks 'auditar projeto legado LGPD', 'gap analysis LGPD', 'sistema antigo LGPD', 'diagnóstico de privacidade no código', or invokes `lgpd-audit` on an existing repository. Produces `.lgpd/discovery.md` and `.lgpd/gaps.md`.
---

# Legacy Retrofit — Diagnóstico e Plano de Remediação

Skill de entrada para sistemas já em produção (`Pipeline B — L1`). Produz diagnóstico técnico objetivo do repositório e separa claramente **o que foi verificado no código** do que **depende de validação jurídica/organizacional externa**.

## Workflow

### Fase 1: Discovery reverso do repositório
Inspecione sistematicamente:
1. **Modelos de dados e migrations** (`prisma/schema.prisma`, SQL, ORM models)
2. **Rotas, controllers, Server Actions e jobs assíncronos**
3. **Dependências, SDKs mobile/web e variáveis de ambiente** (`package.json`, `app.json`, `Info.plist`, `AndroidManifest.xml`, `.env.example`)
4. **Cookies, trackers, pixels e logs de aplicação/APM** (verificar vazamento de PII em `console.log`, Sentry, Datadog)
5. **Fluxos de autenticação, consentimento e exclusão de conta existentes**
6. **Infraestrutura como código (IaC)** — regiões de nuvem, criptografia de volumes/buckets, retenção de backups
7. **Textos públicos versionados** — Política de Privacidade, Termos de Uso, contato do Encarregado

Registre os fatos observados (com links para arquivos e linhas) em `.lgpd/discovery.md`.

### Fase 2: Matriz de Gap Analysis

Classifique cada dimensão como `OK (no código)`, `PARCIAL`, `GAP` ou `VALIDAÇÃO EXTERNA NECESSÁRIA`:

| Dimensão | Status | Evidência observada | Tipo de pendência |
|---|---|---|---|
| Inventário de dados e cookies/SDKs | `{status}` | `{evidência}` | Técnica + Governança |
| Base legal por atividade (Arts. 7º/11 + Enunciado 1/2023) | `{status}` | `{evidência}` | Jurídica + Governança |
| Encarregado (Res. 18/2024) ou canal ATPP (Res. 2/2022, Art. 11) | `{status}` | `{evidência}` | Organizacional + Web |
| Canais e endpoints DSAR (SLA padrão vs. ATPP) | `{status}` | `{evidência}` | Técnica + Operacional |
| Ledger de consentimento orientado a eventos (se aplicável) | `{status}` | `{evidência}` | Técnica |
| Criptografia em trânsito + storage/volume + campos críticos | `{status}` | `{evidência}` | Técnica / Infra |
| Trilha de auditoria íntegra e sem PII em claro | `{status}` | `{evidência}` | Técnica |
| Regras de retenção, bloqueio, backups e propagação | `{status}` | `{evidência}` | Técnica + Jurídica |
| Terceiros classificados por papel + DPAs (Art. 39) | `{status}` | `{evidência}` | Contratual / Jurídica |
| Transferência internacional (Res. 32/2026 UE ou Res. 19/2024 SCCs) | `{status}` | `{evidência}` | Contratual + Infra |
| Runbook e registro de incidentes de 5 anos (Res. 15/2024) | `{status}` | `{evidência}` | Operacional + Governança |
| Controles do ECA Digital (Lei 15.211/2025 + Dec. 12.880/2026) | `{status}` | `{evidência}` | Técnica + Produto |

### Fase 3: Priorização por Risco × Esforço

1. **P0 — Exposição imediata / regulatória alta**: vazamento de PII em logs/rotas públicas, ausência de canal do Encarregado/ATPP, ausência de atendimento mínimo a titulares (DSAR), ausência de runbook de incidente (3 dias úteis), perfilamento ilegal de menores.
2. **P1 — Fundamentos e contratos**: mapa de dados, bases legais/LIAs, regularização de operadores e transferências internacionais, retenção/eliminação, consent ledger íntegro.
3. **P2 — Maturidade e defesa em profundidade**: criptografia em nível de coluna/crypto-shredding, hash chain com ancoragem externa, anonimização formal em analytics, automações avançadas.

### Fase 4: Gerar `.lgpd/gaps.md` e pausar em Checkpoint

Salve `.lgpd/gaps.md` separando **Ações de Engenharia (repositório)** de **Ações Jurídicas/Organizacionais (fora do repositório)** e apresente `⏸ CHECKPOINT` ao usuário antes de iniciar `L2` (`lgpd-data-mapping`).

## Status update

```markdown
## L1 — Legacy retrofit ✓
- Discovery técnico salvo em `.lgpd/discovery.md`
- Plano priorizado (P0/P1/P2) salvo em `.lgpd/gaps.md`
- ⏸ Aguardando confirmação para avançar ao `lgpd-data-mapping` (L2)
```
