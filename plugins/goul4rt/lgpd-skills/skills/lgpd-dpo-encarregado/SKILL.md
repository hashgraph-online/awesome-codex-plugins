---
name: lgpd-dpo-encarregado
description: Designate and publish the Encarregado (DPO) per LGPD Art. 41 and Resolução CD/ANPD nº 18/2024, OR document the ATPP low-risk exemption with a mandatory communication channel under Resolução CD/ANPD nº 2/2022 Art. 11. Run before consolidating ROPA and Privacy Policy. Produces `.lgpd/encarregado.md`.
---

# Encarregado pelo Tratamento de Dados (Art. 41 LGPD + Res. 18/2024)

Define a governança do ponto focal de comunicação com titulares e com a ANPD **antes** da consolidação do ROPA (`lgpd-ropa`), do fluxo DSAR (`lgpd-dsar`) e da Política de Privacidade (`lgpd-privacy-policy`).

## Duas rotas válidas conforme o porte e o risco

### Rota A — Designação formal de Encarregado (regra geral — Art. 41 + Res. CD/ANPD nº 18/2024)
Obrigatória para todos os controladores fora do regime de ATPP e também para **ATPPs que realizem tratamento de alto risco** (teste cumulativo do Art. 4º da Res. 2/2022):
- **Natureza**: pessoa natural (interna ou externa) **ou** pessoa jurídica (**DPO as a Service** — caso PJ, deve constar o nome empresarial **e** o nome completo da pessoa natural responsável — Res. 18/2024, Art. 9º, § 1º).
- **Ato formal**: designado por documento escrito, datado e assinado, mantido à disposição da ANPD quando solicitado (Res. 18/2024, Art. 3º).
- **Substituto**: indicar formalmente substituto para ausências, impedimentos ou vacâncias (Res. 18/2024, Art. 5º).
- **Prevenção de conflito de interesse** (Res. 18/2024, Art. 2º, II e Arts. 17–19): o Encarregado não deve acumular função que determine autonomamente finalidades e meios de tratamento sem salvaguardas de independência (atenção a CEOs, CTOs, CISOs ou heads de produto/marketing acumulando o papel).
- **Responsabilidade**: a responsabilidade perante a ANPD pela conformidade do tratamento é do **agente de tratamento**, não do Encarregado (Res. 18/2024, Art. 15, § 2º).

### Rota B — Dispensa formal para ATPP de baixo risco (Res. CD/ANPD nº 2/2022, Art. 11)
O Agente de Tratamento de Pequeno Porte que **não** realize tratamento de alto risco:
- **Não é obrigado a indicar Encarregado formal**, **MAS tem obrigação legal expressa de disponibilizar um canal de comunicação** para atender o titular (Art. 11, § 1º da Res. 2/2022 — ex.: endereço de e-mail dedicado `privacidade@dominio.com.br` e/ou formulário público).
- Nota de governança: a indicação voluntária de Encarregado por ATPP é considerada **política de boas práticas** para fins de atenuante (Res. 2/2022, Art. 11, § 2º e Art. 52, § 1º, IX da LGPD), mas deve ser tratada como opção estratégica, não imposição legal.

## Divulgação pública obrigatória (Res. 18/2024, Art. 9º e Art. 13)

No sítio eletrônico (ou dentro do app, se não houver site), em local de **destaque e fácil acesso**, em **língua portuguesa**:
- **Se Rota A (Pessoa Natural)**: nome completo + canal(is) de contato (e-mail dedicado e/ou formulário).
- **Se Rota A (Pessoa Jurídica)**: nome empresarial / título do estabelecimento + nome completo da pessoa natural responsável + canal(is) de contato.
- **Se Rota B (ATPP dispensado)**: identificação clara do **canal de comunicação para assuntos de privacidade e direitos do titular** (Art. 11, § 1º da Res. 2/2022).

## Atribuições (Art. 41, § 2º LGPD + Res. 18/2024, Arts. 15–16)

1. Aceitar reclamações e comunicações dos titulares, prestar esclarecimentos e adotar providências.
2. Receber comunicações da ANPD e adotar providências.
3. Orientar funcionários e contratados a respeito das práticas de proteção de dados.
4. Prestar assistência e orientação estratégica ao controlador na elaboração de **ROPA**, **RIPD**, **regras de boas práticas**, **cláusulas contratuais/transferências internacionais** e **comunicação de incidentes de segurança**.

## Template — `.lgpd/encarregado.md`

```markdown
# Governança de Encarregado / Canal de Privacidade

**Regime adotado**: `{Rota A — Encarregado formal (Res. 18/2024) | Rota B — ATPP de baixo risco dispensado com canal obrigatório (Res. 2/2022, Art. 11)}`
**Data de formalização**: `{data}`

## Se Rota A — Encarregado Designado
- **Ato formal de designação**: `{referência ao documento assinado}`
- **Modalidade**: `{Pessoa Natural | Pessoa Jurídica}`
- **Nome / Razão Social**: `{preencher}`
- **Pessoa natural responsável (obrigatório se PJ)**: `{nome completo}`
- **Substituto formal (Res. 18/2024, Art. 5º)**: `{nome completo e contato}`
- **Avaliação de conflito de interesses**: `{realizada em YYYY-MM-DD — conclusão e mitigação}`

## Canal Público de Comunicação (obrigatório nas Rotas A e B)
- **E-mail dedicado**: `privacidade@{dominio}`
- **Portal / Formulário**: `https://{dominio}/privacidade#contato`
- **URL pública de divulgação**: `https://{dominio}/privacidade`
```

## Status update

```markdown
## F3 / L4 — Encarregado / Canal de Privacidade ✓
- Regime: {Encarregado formal Res. 18/2024 | Dispensa ATPP Art. 11 Res. 2/2022}
- Canal público configurado: {e-mail / URL}
- Próximo passo: auditoria de fornecedores, DPAs e transferências internacionais
```
