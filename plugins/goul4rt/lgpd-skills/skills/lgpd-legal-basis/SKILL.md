---
name: lgpd-legal-basis
description: Choose and document the lawful basis (base legal) for each mapped personal data processing activity under LGPD Art. 7 (common data), Art. 11 (sensitive data), and Art. 14 + Enunciado CD/ANPD nº 1/2023 (children and adolescents). Use after `lgpd-data-mapping` or when designing a new feature, asking "qual base legal usar", "consentimento ou legítimo interesse", or "base legal para menores". Produces `.lgpd/legal-basis.md` and `.lgpd/lia/{slug}.md`.
---

# Base Legal LGPD

Defina e documente a base legal de **cada atividade de tratamento identificada no mapeamento (`lgpd-data-mapping`)**. Sem hipótese legal válida, o tratamento é ilícito (Arts. 7º e 11 da LGPD).

> **Pré-requisito de ordem:** execute primeiro o inventário preliminar em `lgpd-data-mapping` (ou identifique claramente a atividade da nova feature) — a base legal é atribuída **por finalidade/atividade concreta**, nunca para "o banco inteiro".

## Árvore de decisão

```text
1. Há dados pessoais de crianças (< 12 anos) ou adolescentes (12 a < 18 anos)? (Art. 14 LGPD + ECA Art. 2º)
   └── SIM → Avaliar e documentar obrigatoriamente a prevalência do MELHOR INTERESSE no caso concreto.
             Conforme o Enunciado CD/ANPD nº 1/2023, qualquer base dos Arts. 7º ou 11 pode ser
             aplicável (não apenas o consentimento), observadas as regras abaixo:
             • Se a base adequada para CRIANÇA (< 12) for o CONSENTIMENTO → exigir consentimento
               específico e em destaque de pelo menos um dos pais ou responsável legal (Art. 14, § 1º),
               ressalvada coleta única sem armazenamento para contatar pais/proteger a criança (§ 3º).
             • Se outra hipótese legal for a correta (ex.: obrigação legal, execução de contrato
               compatível com a capacidade civil/representação, tutela da saúde, prevenção à fraude)
               → documentar a base correspondente + demonstração do melhor interesse (sem forçar
               consentimento parental fictício onde a lei já impõe ou autoriza o tratamento).

2. O dado é sensível? (Art. 5º, II — origem racial/étnica, convicção religiosa, opinião política,
   filiação a sindicato ou organização religiosa/filosófica/política, saúde, vida sexual, dado genético ou biométrico)
   ├── SIM → Art. 11 (ATENÇÃO: execução de contrato e legítimo interesse NÃO existem no Art. 11!)
   │   ├── I — Consentimento específico e destacado, para finalidades específicas
   │   └── II — Sem consentimento, quando indispensável para:
   │       (a) obrigação legal ou regulatória pelo controlador
   │       (b) políticas públicas pela administração pública
   │       (c) estudos por órgão de pesquisa (anonimização sempre que possível)
   │       (d) exercício regular de direitos, inclusive em contrato e em processo judicial/adm./arbitral
   │       (e) proteção da vida ou da incolumidade física do titular ou de terceiro
   │       (f) tutela da saúde, exclusivamente, em procedimento por profissionais/serviços de saúde ou autoridade sanitária
   │       (g) garantia da prevenção à fraude e à segurança do titular, nos processos de identificação e autenticação de cadastro em sistemas eletrônicos (resguardados os direitos do Art. 9º e exceto se prevalecerem direitos e liberdades fundamentais do titular)
   │
   └── NÃO (dado pessoal comum) → Art. 7º:
       I    consentimento pelo titular (livre, informado, inequívoco, finalidade determinada)
       II   cumprimento de obrigação legal ou regulatória pelo controlador
       III  pela administração pública, para tratamento e uso compartilhado necessários a políticas públicas
       IV   realização de estudos por órgão de pesquisa (garantida, sempre que possível, a anonimização)
       V    execução de contrato ou de procedimentos preliminares relacionados a contrato do qual seja parte o titular, a pedido do titular
       VI   exercício regular de direitos em processo judicial, administrativo ou arbitral
       VII  proteção da vida ou da incolumidade física do titular ou de terceiro
       VIII tutela da saúde, exclusivamente, em procedimento realizado por profissionais/serviços de saúde ou autoridade sanitária
       IX   interesses legítimos do controlador ou de terceiro, exceto no caso de prevalecerem direitos e liberdades fundamentais do titular (Art. 10 — exige LIA)
       X    proteção do crédito
```

## Regras práticas e distinções críticas

1. **Legítimo interesse (Art. 7º, IX) e execução de contrato (Art. 7º, V — regra geral) não se aplicam a dados sensíveis** (Art. 11 possui rol próprio; para contratos envolvendo dados sensíveis, verifique se incide estritamente o Art. 11, II, `d` ou `g`, ou Art. 11, I).
2. **Não use consentimento quando o titular não pode recusar nem revogar**: se o dado é obrigatório por lei fiscal/regulatória (`Art. 7º, II`) ou indispensável para entregar o serviço contratado (`Art. 7º, V`), pedir "consentimento" gera nulidade por falta de liberdade e quebra o fluxo quando o usuário tenta revogar (Art. 8º, § 5º).
3. **Crianças vs. Adolescentes (Art. 14 + Enunciado CD/ANPD nº 1/2023 + ECA Digital)**:
   - **Criança**: menor de 12 anos incompletos; **Adolescente**: entre 12 e 18 anos incompletos (ECA, Art. 2º).
   - O **Enunciado CD/ANPD nº 1/2023** pacificou que o tratamento de dados de crianças e adolescentes pode apoiar-se em **qualquer hipótese dos Arts. 7º ou 11**, condicionado à avaliação concreta e prevalência do **melhor interesse**.
   - Quando usar **legítimo interesse (Art. 7º, IX)** envolvendo crianças ou adolescentes, o teste de balanceamento no LIA exige escrutínio reforçado sobre vulnerabilidade e impacto.
   - Não confunda a **base legal da LGPD** com o dever de **vinculação de conta a responsável legal até 16 anos** previsto no **Art. 24 da Lei nº 15.211/2025 (ECA Digital)** — uma plataforma pode tratar dados de autenticação de um adolescente de 15 anos por execução de contrato (observada a assistência civil aplicável) e, simultaneamente, precisar vincular a conta ao responsável por força do Art. 24 do ECA Digital (ver `lgpd-eca-digital-minors`).
4. **Biometria de autenticação vs. conveniência**: para usar o **Art. 11, II, `g`** (prevenção à fraude e segurança em identificação/autenticação eletrônica sem consentimento), avalie proporcionalidade, necessidade real frente a alternativas menos intrusivas e vedação de desvio para marketing/ponto trabalhista (que não é "cadastro em sistema eletrônico" antifraude).

## Workflow

1. Leia as atividades inventariadas em `.lgpd/data-map.md`.
2. Para cada atividade, defina a hipótese legal exata (Art. 7º ou Art. 11 + inciso/alínea).
3. Se a atividade envolver **crianças ou adolescentes**, preencha o bloco obrigatório de avaliação do **melhor interesse** (Art. 14 + Enunciado 1/2023).
4. Se a base for **legítimo interesse (Art. 7º, IX)**, elabore um LIA em `.lgpd/lia/{slug}.md` a partir de [`assets/lia-template.md`](assets/lia-template.md).
5. Se a finalidade mudar posteriormente, reavalie a base legal e informe o titular (Art. 9º, § 2º).
6. Salve em `.lgpd/legal-basis.md` e sincronize a coluna de base legal em `.lgpd/data-map.md`.

## Template — `.lgpd/legal-basis.md`

```markdown
# Bases Legais por Atividade de Tratamento

**Última atualização**: {data}

## Atividade {ID} — {nome curto}

- **Finalidade específica (Art. 6º, I)**: {descrição objetiva}
- **Dados tratados**: {lista}
- **Contém dados sensíveis (Art. 5º, II)?**: {Não | Sim — especificar}
- **Envolve crianças (< 12) ou adolescentes (12–17)?**: {Não | Crianças | Adolescentes | Ambos}
- **Base legal**: {Art. 7º, inciso X | Art. 11, inciso X, alínea Y} — {nome da hipótese}
- **Justificativa de adequação**: {por que esta base é a correta e proporcional}
- **Avaliação do Melhor Interesse (obrigatória se houver menores — Art. 14 + Enunciado 1/2023)**:
  - {Como o tratamento protege ou beneficia o menor, minimização aplicada e por que não há prejuízo ao seu desenvolvimento/direitos; se consentimento para < 12, indicar fluxo do Art. 14, § 1º}
- **LIA (se Art. 7º, IX)**: `.lgpd/lia/{slug}.md`
- **Direito de oposição / revogação**: {Consentimento: revogação facilitada Art. 8º, § 5º | Sem consentimento: oposição em caso de desconformidade Art. 18, § 2º}
- **Última revisão**: {data}
```

## Cláusulas-armadilha (rejeite na revisão)

- Checkbox pré-marcado para consentimento → **vício de vontade** (não é inequívoco/livre).
- Pacote único "aceito todos os tratamentos" para finalidades distintas → viola **Art. 8º, § 4º** e **Art. 9º, § 2º**.
- Exigir consentimento parental universal para obrigação legal sanitária/educacional de menor → erro conceitual frente ao **Enunciado CD/ANPD nº 1/2023**.
- Invocar legítimo interesse para tratar dado biométrico ou de saúde → **vedado** (Art. 10 não alcança Art. 11).

## Status update

```markdown
## F2 / L3 — Legal basis ✓
- {N} atividades do data-map avaliadas e vinculadas a base legal
- {A} em execução de contrato / obrigação legal
- {B} em consentimento (encaminhadas ao `lgpd-consent-schema`)
- {C} em legítimo interesse (LIAs gerados em `.lgpd/lia/`)
- {D} com avaliação explícita de melhor interesse (Art. 14 + Enunciado 1/2023)
```
