---
name: lgpd-ropa
description: Generate and maintain the Registro de Operações de Tratamento de Dados Pessoais (ROPA) required by LGPD Art. 37, supporting both standard controllers/operators and the simplified ANPD model for ATPP (Resolução CD/ANPD nº 2/2022 Art. 9). Consolidates data mapping, legal bases, DPO/ATPP channel, vendors, transfers, security, and retention into `.lgpd/ROPA.md`.
---

# ROPA — Registro de Operações de Tratamento (Art. 37 LGPD)

Art. 37 da LGPD: *"O controlador e o operador devem manter registro das operações de tratamento de dados pessoais que realizarem, especialmente quando baseado no legítimo interesse."*

## Pré-requisitos (ordem de pipeline corrigida)

Execute **depois** de ter concluído:
1. `.lgpd/data-map.md` (`lgpd-data-mapping`)
2. `.lgpd/legal-basis.md` (`lgpd-legal-basis`)
3. `.lgpd/encarregado.md` (`lgpd-dpo-encarregado` — contendo Encarregado formal **ou** registro de dispensa ATPP de baixo risco com canal obrigatório do Art. 11, § 1º da Res. 2/2022)
4. `.lgpd/vendors/`, `.lgpd/transfers/` e `.lgpd/retention.md` (quando aplicáveis)

## Modelos: Simplificado ATPP vs. Completo

- **ATPP (Res. CD/ANPD nº 2/2022, Art. 9º)**: pode elaborar e manter o registro de forma **simplificada**, seguindo o modelo orientativo publicado pela ANPD em junho de 2023 (8 blocos essenciais: contato, categorias de titulares, categorias de dados, compartilhamento, medidas de segurança, período de armazenamento, processo/finalidade/base legal e observações).
- **Controladores/Operadores fora do regime simplificado (ou ATPP de alto risco)**: expandir com transferência internacional (adequação Res. 32/2026 ou SCCs Res. 19/2024), papel jurídico de cada terceiro, decisões automatizadas e vínculo com LIA/RIPD.

## Template — `.lgpd/ROPA.md`

Ver [`assets/ropa-template.md`](assets/ropa-template.md).

## Workflow

1. Consolide todas as atividades de `.lgpd/data-map.md` e `.lgpd/legal-basis.md`.
2. Separe claramente **Seção I — Atividades em que atuamos como Controlador** e **Seção II — Atividades em que atuamos como Operador** (ex.: plataformas B2B SaaS processando dados de clientes corporativos).
3. Destaque expressamente todas as operações fundamentadas em **legítimo interesse (Art. 7º, IX)** com referência ao respectivo LIA.
4. Preencha os dados do Encarregado **ou**, no caso de ATPP de baixo risco dispensado (Res. 2/2022, Art. 11), registre expressamente a condição de ATPP e o **canal oficial de comunicação com titulares**.
5. Salve em `.lgpd/ROPA.md`.
6. **⏸ CHECKPOINT obrigatório**: pause para validação do Encarregado / responsável jurídico antes de marcar como versão publicada.

## Governança contínua

- Mantenha o ROPA versionado no Git: qualquer nova feature com dados pessoais, mudança de finalidade, novo operador ou nova transferência internacional exige atualização do ROPA.
- A ANPD pode requisitar o ROPA em atividades de monitoramento/fiscalização (Art. 37 c/c Res. 4/2023).

## Status update

```markdown
## F12 / L11 — ROPA ✓
- ROPA v{N} gerado em `.lgpd/ROPA.md` ({Simplificado ATPP | Completo})
- {C} atividades como Controlador | {O} atividades como Operador
- ⏸ Aguardando revisão do Encarregado/jurídico
- Próximo passo: `lgpd-ripd` (se aplicável) ou `lgpd-privacy-policy`
```
