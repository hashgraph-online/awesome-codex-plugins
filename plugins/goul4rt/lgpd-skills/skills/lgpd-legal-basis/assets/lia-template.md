# Legitimate Interest Assessment (LIA) — Template

Obrigatório como evidência de responsabilização (Art. 6º, X + Art. 10, § 3º LGPD) sempre que a base legal avaliada for o **legítimo interesse (Art. 7º, IX)**. Lembre-se: legítimo interesse **não se aplica a dados pessoais sensíveis (Art. 11)**.

## Identificação

- **Atividade (ref. `data-map.md`)**: {A00X — nome}
- **Controlador**: {razão social}
- **Data**: {data} | **Versão**: {vN} | **Próxima revisão**: {data}

## 1. Teste de Finalidade (Legitimidade do Interesse)

- **Qual é o interesse concreto perseguido pelo controlador ou terceiro?** (Art. 10, caput e incisos I/II)
- **A situação é concreta e atual (não meramente especulativa ou futura)?**
- **A finalidade é lícita e compatível com o ordenamento brasileiro (incluindo LGPD, CDC e ECA Digital)?**

## 2. Teste de Necessidade (Minimização — Art. 10, § 1º)

- **Os dados pessoais selecionados são estritamente necessários para a finalidade pretendida?** (Art. 10, § 1º)
- **Existe alternativa menos intrusiva (ex.: dados agregados/anonimizados) que atinja o mesmo resultado?**
- **Quais campos foram descartados por minimização?**

## 3. Teste de Balanceamento e Legítima Expectativa (Art. 10, II)

| Dimensão | Análise concreta |
|---|---|
| Relação prévia com o titular | {usuário ativo / ex-cliente / visitante sem vínculo} |
| Legítima expectativa do titular (Art. 10, II) | {alta / média / baixa — explicar contexto no momento da coleta} |
| Impacto potencial sobre direitos e liberdades | {baixo / moderado / elevado — riscos financeiros, morais, discriminatórios} |
| Vulnerabilidade dos titulares | {adultos comuns / idosos / adolescentes / crianças — se menores, aplicar teste reforçado do melhor interesse conforme Art. 14 e Enunciado CD/ANPD nº 1/2023} |
| Origem do dado | {fornecido pelo titular / observado no uso / inferido / obtido de terceiro} |
| Salvaguardas e opt-out | {transparência prévia, oposição facilitada em 1 clique, pseudonimização} |

**Conclusão fundamentada do balanceamento**: {demonstrar por que direitos e liberdades fundamentais do titular não prevalecem, ou concluir pela inviabilidade do legítimo interesse}.

## 4. Salvaguardas obrigatórias (Art. 10, § 2º)

- [ ] Transparência clara na Política de Privacidade e no momento/contexto relevante
- [ ] Mecanismo gratuito e facilitado de oposição (*opt-out*) e respeito imediato à escolha
- [ ] Minimização estrita de atributos e prazo de retenção curto/definido
- [ ] Pseudonimização ou agregação sempre que tecnicamente viável
- [ ] Proibição absoluta de uso para perfilamento publicitário de menores (ECA Digital, Arts. 22 e 26)

## 5. Avaliação de Alto Risco e necessidade de RIPD (Art. 10, § 3º + Res. 2/2022, Art. 4º)

A ANPD pode solicitar RIPD quando o tratamento tiver como fundamento o legítimo interesse (Art. 10, § 3º). Além disso, verifique o **teste cumulativo da Res. CD/ANPD nº 2/2022, Art. 4º**:
- **Critério geral presente?** Larga escala (avaliada de forma multifatorial: número de titulares, volume, duração, frequência e alcance geográfico — sem corte numérico fixo) **OU** potencial de afetar significativamente interesses e direitos fundamentais?
- **Critério específico presente?** Tecnologias emergentes/IA, vigilância de áreas públicas, decisões automatizadas/profiling, ou dados de crianças, adolescentes ou idosos?

- **Resultado**: {Não configura alto risco cumulativo | Configura alto risco → elaborar RIPD obrigatório | Elaborar RIPD preventivo por boa prática}

## 6. Parecer e Aprovação

- [ ] **Aprovado** o uso do Art. 7º, IX com as salvaguardas da seção 4
- [ ] **Reprovado** — alterar arquitetura ou migrar para outra hipótese legal ({especificar})

**Revisado por (Encarregado / Jurídico)**: {nome} — **Data**: {data}
