---
name: lgpd-privacy-policy
description: Draft, version, and review a privacy policy compliant with LGPD Art. 9 (seven mandatory elements), Resolução CD/ANPD nº 18/2024 (DPO disclosure) or ATPP channel, international transfer transparency (Res. 19/2024 and Res. 32/2026), and ECA Digital when applicable. Run AFTER consolidating ROPA so the notice matches real data flows. CHECKPOINT skill — requires legal review before publication.
---

# Política / Aviso de Privacidade (Art. 9º LGPD)

Instrumento de transparência externa que materializa o livre acesso e a informação clara, adequada e ostensiva sobre o tratamento (Art. 6º, VI e Art. 9º da LGPD).

> **Ordem recomendada:** gere ou revise a Política **após** consolidar `data-map.md`, `legal-basis.md`, `encarregado.md`, `retention.md`, `transfers/` e `ROPA.md` — evitando publicar promessas genéricas descoladas do código real.

## Elementos obrigatórios (Art. 9º LGPD + normas da ANPD)

1. **Finalidade específica** de cada tratamento (Art. 9º, I) e respectiva hipótese legal
2. **Forma e duração** do tratamento, com prazos ou critérios objetivos de retenção (Art. 9º, II)
3. **Identificação do controlador** (razão social, CNPJ, endereço — Art. 9º, III)
4. **Informações de contato** do Encarregado — nome completo (PF) ou nome empresarial + responsável PF (PJ) conforme Res. 18/2024, Art. 9º — **ou**, para ATPP de baixo risco dispensado (Res. 2/2022, Art. 11), o **canal dedicado de comunicação com titulares**
5. **Uso compartilhado de dados** com terceiros, distinguindo finalidade e papel (operadores vs. controladores independentes/conjuntos — Art. 9º, V e VI)
6. **Direitos do titular** com menção expressa ao **Art. 18 da LGPD**, canais gratuitos de exercício e prazos de atendimento (padrão: formato simplificado imediato / declaração completa em até 15 dias; ATPP: simplificado em até 15 dias / completo em até 30 dias — Art. 19 c/c Res. 2/2022, Art. 14)
7. **Transferência internacional de dados** (Res. 19/2024, Art. 16): países/blocos de destino, finalidade e mecanismo aplicável — distinguindo **Decisões de Adequação da ANPD (ex.: UE/EEE pela Res. CD/ANPD nº 32/2026)** de **Cláusulas-Padrão Contratuais (Res. CD/ANPD nº 19/2024)**
8. **Cookies, SDKs e tecnologias de rastreamento** (alinhado ao Guia Orientativo de Cookies da ANPD: distinção entre estritamente necessários e não necessários + gestão granular de preferências)
9. **Crianças e adolescentes** (quando aplicável: linguagem simples e acessível nos termos do Art. 14, § 6º da LGPD + regras de supervisão/vinculação e vedação de perfilamento publicitário da Lei nº 15.211/2025 e Decreto nº 12.880/2026)

## Template de referência

Ver [`assets/privacy-policy-template.md`](assets/privacy-policy-template.md).

## Versionamento e re-coleta de consentimento

- Salve cada versão em `.lgpd/policies/privacy-policy-v{N}.md` e mantenha histórico acessível ao titular.
- **Mudança de finalidade ou nova finalidade incompatível com o consentimento original** (Art. 8º, § 6º e Art. 9º, § 2º): o titular deve ser informado em destaque e, quando o tratamento depender de consentimento, os registros anteriores passam ao estado `SUPERSEDED` até nova manifestação livre e específica (`lgpd-consent-schema`).

## ⏸ CHECKPOINT obrigatório

**Nunca publique diretamente em produção sem validação humana e revisão jurídica:**
1. Gere `.lgpd/policies/privacy-policy-v{N}-draft.md` cruzando 100% dos itens com `.lgpd/ROPA.md`.
2. Destaque eventuais divergências entre o código atual e a política existente.
3. Pause e aguarde aprovação formal antes de promover para `privacy-policy-v{N}.md`.

## Status update

```markdown
## F14 / L13 — Privacy policy ✓
- Minuta gerada em `.lgpd/policies/privacy-policy-v{N}-draft.md` alinhada ao ROPA
- ⏸ Aguardando revisão jurídica e aprovação do Encarregado antes da publicação
```
