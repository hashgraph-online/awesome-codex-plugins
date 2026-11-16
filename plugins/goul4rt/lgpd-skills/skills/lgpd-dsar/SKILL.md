---
name: lgpd-dsar
description: Implement endpoints and operational workflows for data subject rights (DSAR) under LGPD Arts. 18, 19, and 20, distinguishing standard controller SLAs (immediate simplified / 15d complete) from ATPP SLAs under Resolução CD/ANPD nº 2/2022 Art. 14 (15d simplified / 30d complete). Covers legal representatives, ex-employees, informal channels, and proportional identity verification. Outputs `.lgpd/dsar/workflow.md` + endpoint specs.
---

# DSAR — Direitos dos Titulares (Arts. 18, 19 e 20 da LGPD)

Implementação técnica e operacional dos direitos do titular (Art. 18) e da revisão/explicação de decisões automatizadas (Art. 20), que figuram no topo do Mapa de Temas Prioritários da ANPD (Res. CD/ANPD nº 30/2025).

## Prazos legais exatos: Controlador Padrão vs. ATPP

Não aplique a mesma regra de resposta imediata indistintamente a todos os agentes e modalidades. Consulte [`assets/dsar-sla.ts`](assets/dsar-sla.ts):

| Direito / Modalidade | Controlador Padrão (Art. 19 LGPD) | ATPP elegível (Res. CD/ANPD nº 2/2022, Art. 14) |
|---|---|---|
| **Confirmação ou acesso em formato simplificado** (`Art. 18, I e II` c/c `Art. 19, I`) | **Imediato** | **Até 15 dias** (`Res. 2/2022, Art. 14, I`) |
| **Declaração clara e completa** indicando origem, critérios e finalidade (`Art. 19, II`) | **Até 15 dias corridos** da requisição | **Até 30 dias corridos** (prazo em dobro — `Res. 2/2022, Art. 14, caput`) |
| **Revogação de consentimento** (`Art. 8º, § 5º` e `Art. 18, IX`) | Procedimento gratuito e facilitado (efeito imediato na interrupção de novos tratamentos) | Procedimento gratuito e facilitado |
| **Correção, eliminação, bloqueio, anonimização, portabilidade** (`Art. 18, III a VI`) | **Sem demora injustificada** (boa prática operacional: meta ≤ 15 dias; comunicar imediatamente eventual impossibilidade de adoção imediata — `Art. 18, § 4º`) | Prazo operacional compatível com porte + comunicação fundamentada (`Art. 18, § 4º`) |

## Mapeamento técnico dos direitos

| Artigo | Direito | Rota de referência | Observação técnica |
|---|---|---|---|
| Art. 18, I | Confirmação da existência de tratamento | `GET /api/me` | Self-service imediato para logados |
| Art. 18, II | Acesso (simplificado vs. completo) | `GET /api/me` / `GET /api/me/export` | Bundle completo inclui categorias, origem, finalidades e destinatários |
| Art. 18, III | Correção de dados incompletos/inexatos | `PATCH /api/me/profile` | Enfileirar propagação em `OperatorPropagationOutbox` (`Art. 18, § 6º`) |
| Art. 18, IV | Anonimização, bloqueio ou eliminação de excessos | `POST /api/dsar/tickets` | Análise caso a caso + log de decisão |
| Art. 18, V | Portabilidade | `GET /api/me/export?format=portable` | Formato estruturado/interoperável (JSON/CSV), resguardado segredo comercial/industrial |
| Art. 18, VI | Eliminação de dados tratados com consentimento (e término do Art. 15/16) | `POST /api/me/erasure` | Checar retenções legais específicas (`planErasureDisposition`) + tombstone de backup + propagação `Art. 18, § 6º` |
| Art. 18, VII e VIII | Informação sobre compartilhamentos e não consentir | Política + UX de coleta + `GET /api/me` | Linguagem clara antes da coleta |
| Art. 18, IX | Revogação do consentimento | `POST /api/consent/revoke` | Cria evento `REVOKED` em `ConsentEvent` + propaga a operadores |
| Art. 20 | Revisão e critérios de decisão unicamente automatizada | `POST /api/dsar/automated-review` | Fornecer critérios e procedimentos claros, respeitados segredos comercial e industrial (§ 1º) |

## Casos operacionais obrigatórios (além do usuário logado padrão)

### 1. Verificação proporcional de identidade (Art. 6º, III — necessidade)
- **Titular autenticado na sessão** (+ re-autenticação/2FA para exportação sensível ou exclusão): suficiente.
- **Titular sem acesso à conta**: valide pelos canais já vinculados ao cadastro (código em e-mail/telefone ou atributos cadastrais já existentes). **Nunca exija selfie/RG como barreira padrão** se você sequer possuía documento/biometria do titular antes — coletar mais PII para atender um pedido de privacidade viola a minimização (`Art. 6º, III`).

### 2. Representantes legais (pais, tutores, curadores e procuradores — `Art. 18, § 3º`)
- Direitos de crianças, adolescentes ou pessoas incapazes (ou pedidos via procurador constituído) podem ser exercidos por **representante legalmente constituído** (`Art. 18, § 3º`).
- Exija comprovação **proporcional** da qualidade de representante (ex.: vínculo já validado em `Guardian`/`MinorLink`, certidão/termo de guarda ou procuração específica com poderes expressos para proteção de dados — evite aceitar pedidos de terceiros por procurações genéricas de balcão/despachantes sem verificação do titular).

### 3. Solicitações de ex-funcionários, candidatos e prestadores
- Não descarte nem recuse integralmente dizendo "tudo fica retido por 5 anos pela CLT":
  - Entregue o acesso aos dados pessoais do próprio titular (resguardando e **tarjando dados pessoais de terceiros** — ex.: nomes/avaliações subjetivas de colegas protegidas por direitos de terceiros ou segredo empresarial);
  - Em pedidos de eliminação, aplique bloqueio seletivo apenas aos documentos trabalhistas/previdenciários/fiscais sujeitos a guarda legal (`Art. 16, I`), eliminando currículos antigos não contratados ou dados acessórios sem base de conservação.

### 4. Solicitações recebidas por canais informais (WhatsApp, redes sociais, suporte geral, loja)
- O titular não é obrigado a conhecer jargões ("DSAR", "Art. 18"). Se o cliente pedir "apaga meu cadastro" no WhatsApp de atendimento ou no chat de suporte:
  - Treine/automatize o suporte para **reconhecer e protocolar imediatamente** (a data de recebimento já corre!) ou direcionar em 1 clique ao fluxo autenticado sem criar obstáculos artificiais (`Art. 18, § 3º` — sem custos).

## Trilha de auditoria e retenção correta dos logs DSAR

Registre em `AuditLogEntry` (`lgpd-audit-logging`) apenas metadados sem PII desnecessária: `DSAR_RECEIVED`, `DSAR_IDENTITY_VERIFIED`, `DSAR_FULFILLED` (com hash do pacote entregue) e `DSAR_PARTIAL_OR_DENIED` (com fundamento legal do `Art. 16` ou `Art. 18, § 4º`).

> **Correção normativa sobre retenção de logs DSAR:** **não cite o Art. 10 da Resolução CD/ANPD nº 15/2024** como fundamento obrigatório de 5 anos para logs DSAR — aquele artigo trata exclusivamente de **incidentes de segurança**. A guarda das evidências de atendimento DSAR (tipicamente **3 a 5 anos**, em ambiente restrito e minimizado) fundamenta-se na **prestação de contas e exercício regular de direitos (`Art. 6º, X` e `Art. 7º, VI`)**, alinhada aos prazos prescricionais e à janela quinquenal de aferição de reincidência/dosimetria da **Res. CD/ANPD nº 4/2023**.

## Implementação de referência

- Cálculo de SLA e disposição de retenção: [`assets/dsar-sla.ts`](assets/dsar-sla.ts)
- Rotas Next.js + Better Auth + React Native: [`assets/endpoints.md`](assets/endpoints.md)

## Status update

```markdown
## F10 / L9 — DSAR ✓
- Regime de SLA configurado: {Padrão (imediato / 15d) | ATPP Res. 2/2022 Art. 14 (15d simplif. / 30d completo)}
- Endpoints ativos: `/api/me`, `/api/me/export`, `/api/me/profile`, `/api/me/erasure`, `/api/consent/revoke`
- Fluxo operacional documentado para representantes legais, ex-colaboradores e canais informais em `.lgpd/dsar/workflow.md`
```
