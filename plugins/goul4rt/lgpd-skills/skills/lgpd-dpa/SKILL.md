---
name: lgpd-dpa
description: Structure and review Data Processing Agreements (DPA) with operators under LGPD Arts. 39, 42, 46, and 48, distinguishing operators from independent or joint controllers. Use when user mentions 'DPA', 'contrato com operador', 'cláusulas LGPD', 'data processing agreement', or onboarding a third-party service (cloud, analytics, payment, email, observability). Outputs DPA best-practice checklist + per-vendor sheets in `.lgpd/vendors/`.
---

# DPA — Acordo de Tratamento de Dados com Operadores (Art. 39 LGPD)

Instrumento contratual que formaliza as instruções lícitas do controlador ao **operador** (Art. 39 da LGPD), aloca deveres operacionais (segurança, auxílio em DSAR, notificação de incidentes) e reduz assimetrias de responsabilidade.

## Distinções jurídicas essenciais antes de exigir um DPA

1. **Verifique primeiro o papel jurídico do terceiro** (conforme Guia Orientativo da ANPD sobre Agentes de Tratamento):
   - **Operador**: trata dados em nome do controlador e conforme suas instruções (ex.: hospedagem cloud IaaS, disparo transacional de e-mail, observabilidade) → **aplica-se DPA (Art. 39)**.
   - **Controlador Independente (Singular)**: decide autonomamente finalidades e elementos essenciais do próprio tratamento (ex.: bancos/adquirentes em prevenção regulatória própria, operadoras de telecom, órgãos públicos) → **não cabe DPA de operador**, mas sim cláusulas de compartilhamento entre controladores + base legal própria + transparência ao titular (Art. 9º, V).
   - **Controlador Conjunto**: toma decisões comuns ou convergentes sobre finalidades e meios com outro controlador → **acordo de controladoria conjunta** definindo responsabilidades de transparência e atendimento a titulares (Art. 42, § 1º, II).
2. **Responsabilidade solidária não é irrestrita (Art. 42, § 1º, I)**:
   - O operador responde **solidariamente** pelos danos causados pelo tratamento **quando descumprir as obrigações da legislação de proteção de dados ou quando não tiver seguido as instruções lícitas do controlador** (hipótese em que se equipara ao controlador, respeitadas as excludentes do Art. 43). Documentar instruções claras em contrato é, portanto, proteção crítica para ambas as partes.
3. **Natureza das 12 cláusulas abaixo**:
   - A LGPD **não traz uma lista legal taxativa de 12 cláusulas** para DPAs (diferentemente do Art. 28 do GDPR). Os **12 itens abaixo constituem um checklist contratual de boas práticas** consolidado a partir dos Arts. 39, 42, 46 e 48 da LGPD, da Res. CD/ANPD nº 15/2024 e das orientações da ANPD.

## Checklist de boas práticas para DPA (12 cláusulas recomendadas)

1. **Qualificação das partes e papéis** (Controlador vs. Operador)
2. **Objeto, finalidade, categorias de dados e titulares**
3. **Vinculação às instruções lícitas documentadas do Controlador** (Art. 39)
4. **Dever de confidencialidade** da equipe e prestadores autorizados
5. **Medidas técnicas e administrativas de segurança** (Art. 46)
6. **Regime de sub-operadores** (autorização prévia geral ou específica, dever de equivalência contratual)
7. **Cooperação técnica para direitos dos titulares — DSAR** (Art. 18, incluindo propagação do § 6º)
8. **Comunicação célere de incidentes de segurança ao Controlador** (viabilizando o prazo de 3 dias úteis da Res. 15/2024)
9. **Devolução ou eliminação dos dados ao término do contrato** (Arts. 15 e 16)
10. **Demonstração de conformidade e auditoria** (relatórios SOC 2 / ISO 27001 / ISO 27701 ou inspeção acordada)
11. **Alocação de responsabilidade e regresso** (observados os Arts. 42 a 45 da LGPD)
12. **Transferência internacional de dados** (quando aplicável: verificar **Decisão de Adequação — Res. 32/2026 UE/EEE** ou anexar **Cláusulas-Padrão da Res. 19/2024 Anexo II**)

## Template de referência

Ver [`assets/dpa-template.md`](assets/dpa-template.md) (sempre submeter a revisão jurídica antes de assinatura).

## Padrões de mercado em provedores de tecnologia

Em provedores globais de nuvem/SaaS, o DPA costuma ser aderido via **Data Processing Addendum público incorporado aos Termos Enterprise** (sem negociação individual para planos padrão). Avalie a substância jurídica:

| Provedor | Papel usual | DPA / Adendo público | Transferência internacional | Ação recomendada |
|---|---|---|---|---|
| AWS / GCP / Azure | Operador | Sim (DPA online com anexo LGPD) | Depende da região (`sa-east-1` BR vs. `eu-*` Res. 32/2026 vs. `us-*` Res. 19/2024) + suporte global | Verificar região configurada e cobertura das SCCs BR (Res. 19/2024) quando fora de BR/UE |
| Stripe / Pagar.me | Misto (Operador + Controlador Independente antifraude/BACEN) | Sim | EUA / Global (Stripe) ou BR | Distinguir fluxos de operador vs. controlador independente e checar mecanismo Art. 33 |
| Datadog / Sentry | Operador | Sim (DPA online) | Região EU (`datadoghq.eu` → Res. 32/2026) ou US (`datadoghq.com` → SCCs Res. 19/2024) | Configurar scrubbing de PII no SDK + formalizar DPA e mecanismo Art. 33 adequado à região |

## Workflow

1. Receba a lista classificada de terceiros de `lgpd-vendor-audit`.
2. Para cada terceiro classificado como **Operador** (com acesso a dados pessoais):
   - Verifique se há DPA vigente (assinado ou adendo público vinculante) cobrindo os pontos essenciais do checklist;
   - Se envolver transferência internacional fora de jurisdição adequada (Res. 32/2026), vincule o Anexo II da Res. 19/2024 (`lgpd-international-transfer`).
3. Para terceiros classificados como **Controladores Independentes ou Conjuntos**, encaminhe para revisão jurídica de cláusulas de compartilhamento/corresponsabilidade.
4. Registre a ficha consolidada em `.lgpd/vendors/{vendor}.md`.

## Status update

```markdown
## F4b / L5b — Contratos e DPAs ✓
- {N} operadores com dados pessoais avaliados
- {M} com DPA vigente (bilateral ou adendo público aderente)
- {K} controladores independentes/conjuntos encaminhados para cláusula de compartilhamento
- {X} pendências contratuais abertas em `.lgpd/gaps.md`
```
