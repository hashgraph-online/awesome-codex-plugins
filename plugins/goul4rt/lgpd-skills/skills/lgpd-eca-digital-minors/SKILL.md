---
name: lgpd-eca-digital-minors
description: Assess and implement obligations under Lei nº 15.211/2025 (ECA Digital), Decreto nº 12.880/2026, and ANPD's Oct 2026 Guide for IT Providers for digital products directed to or likely accessed by children and adolescents. Use when user mentions 'ECA Digital', 'menores', 'crianças e adolescentes', 'verificação de idade', 'sinais de idade', 'acesso provável', 'controle parental', 'loot box', 'uso compulsivo', 'denúncia de conteúdo', or when the product may have users under 18 — including social networks, games, generative AI, app stores and e-commerce of age-restricted goods. Modulates controls by ecosystem role and risk.
---

# ECA Digital — Lei nº 15.211/2025 e Decreto nº 12.880/2026

A **Lei nº 15.211/2025** está em vigor desde **17 de março de 2026** (Art. 41-A, redação da Lei nº 15.352/2026). Foi regulamentada pelo **Decreto nº 12.880, de 18 de março de 2026**, que atribui à **ANPD** a regulamentação e a fiscalização (Decreto, Art. 1º, parágrafo único). Em **28 de outubro de 2026**, a ANPD publicou o **Guia Orientativo "Fornecedores de produtos ou serviços de tecnologia da informação: escopo e obrigações gerais do ECA Digital"** (versão 1.0).

> **Monitoramento regulatório (novembro/2026):** o Guia específico da ANPD sobre **mecanismos de aferição de idade** ainda está sendo consolidado após a tomada de subsídios. Até a versão final, **não trate a minuta como padrão técnico definitivo**. Pelo cronograma publicado na página da ANPD sobre o ECA Digital (confirme antes de emitir artefatos), o período de adaptação vai de agosto a novembro de 2026 e as **ações de fiscalização começam em janeiro de 2027**.

> **Guia ≠ norma:** o Guia orienta a interpretação da ANPD, mas não cria obrigações. Cite a obrigação pelo artigo da Lei ou do Decreto e use o Guia como critério interpretativo.

## 1. Escopo: direcionamento ou "acesso provável"

A Lei alcança produtos ou serviços de TI fornecidos a distância, por meio eletrônico e por requisição individual (Art. 2º, I) que sejam **direcionados** a crianças (< 12 anos) e adolescentes (12 a < 18 anos) **ou de acesso provável** por eles (Art. 1º).

### 1.1 Presunção legal (Guia ANPD out/2026)

O Guia lista **8 categorias** presumidas de acesso provável. Para elas, em regra, não é preciso fazer o teste do item 1.2. A presunção só pode ser afastada **de forma motivada**, demonstrando que falta algum dos critérios do Art. 1º, parágrafo único:

1. Redes sociais
2. Lojas de aplicações
3. Sistemas operacionais
4. Serviços com controle editorial
5. Jogos eletrônicos
6. Provedores de conteúdo adulto
7. **Sistemas de inteligência artificial generativa** (geração de conteúdo e interação a partir de instruções em linguagem natural)
8. **Plataformas de comércio eletrônico que intermedeiam compra e venda de produtos ou serviços proibidos para crianças e adolescentes**

> Mensageria privada usada para comunicação interpessoal e serviços de reuniões fechadas **não** se enquadram como rede social (Guia, seção "Rede social"). Avalie-os pelo teste do item 1.2, sem presunção.

### 1.2 Teste de acesso provável (Art. 1º, parágrafo único — critérios **cumulativos**)

Fora das categorias presumidas, o ECA Digital se aplica quando estão presentes **os três** critérios:

| Critério | Pergunta de engenharia/produto |
|---|---|
| **I. Probabilidade de uso e atratividade** | Há gamificação, recompensas, rankings, personagens, influenciadores, notificações ou personalização atraentes para menores? Há sinais reais de menores na base (analytics, suporte, denúncias)? |
| **II. Facilidade de acesso e uso** | O cadastro é aberto (sem convite, SSO corporativo ou contratação B2B)? Está em loja pública? É gratuito? |
| **III. Risco relevante** à privacidade, à segurança ou ao desenvolvimento biopsicossocial | Há interação social aberta, contato com desconhecidos, compartilhamento amplo, compras, geolocalização ou recomendação algorítmica? |

- **Autodeclaração não vincula a ANPD** (Decreto, Art. 19, § 2º, e Guia). Escrever nos Termos de Uso "exclusivo para maiores de 18" **não afasta o ECA Digital**. Mecanismos de aferição de idade, sozinhos, também não excluem a incidência da Lei.
- **Software B2B fechado** (ex.: ERP com provisionamento via SSO empresarial, sem cadastro público): em geral falha nos critérios I e II. Documente a não aplicabilidade **critério por critério** em `.lgpd/eca-digital.md`.

### 1.3 Tratamento diferenciado (Art. 39)

As obrigações dos Arts. 6º, 17, 18, 19, 20, 27, 28, 29, 31, 32 e 40 são **moduladas** conforme as características e funcionalidades do produto, o grau de interferência do fornecedor sobre o conteúdo, o número de usuários e o porte. A modulação muda a forma e a extensão das medidas, **não** a responsabilidade.

- **Não há dispensa equivalente à de ATPP** da LGPD. Ser pequeno modula as medidas, mas não tira o produto do escopo.
- **Art. 39, § 1º:** serviços com controle editorial e provedores de conteúdo protegido por direitos autorais (ex.: música, obras literárias licenciadas) podem ser dispensados de parte das obrigações, desde que ofereçam contas infantis com conteúdo adequado e supervisão parental com bloqueio.

## 2. Papel no ecossistema

| Papel | Obrigações típicas |
|---|---|
| **A. Loja de aplicações / Sistema operacional** | Aferir idade (Lei, Art. 12; Decreto, Art. 25, § 2º, II, preferencialmente com credenciais verificáveis). Fornecer **gratuitamente** sinal de idade por API, **sem data de nascimento exata, identidade civil ou dados de perfilamento** (Decreto, Art. 25, caput e § 1º). Pedir autorização dos responsáveis para download, vedada a presunção de autorização (Lei, Art. 12, § 2º; Decreto, Art. 25, § 3º). Permitir contestar a classificação etária (Decreto, Art. 25, § 2º, III). Combater múltiplas contas (§ 2º, IV) |
| **B. Fornecedor de aplicação ou funcionalidade** (SaaS consumer, app, jogo, edtech, IA generativa, e-commerce) | **Receber** os sinais de idade (Lei, Art. 14; Decreto, Art. 26) **e manter mecanismos próprios** de bloqueio, independentemente das medidas de lojas e sistemas operacionais (Lei, Art. 14, parágrafo único). Receber o sinal **não exime** da efetividade das medidas (Decreto, Art. 26, § 3º). Serviços acessados por navegador devem aferir a idade por conta própria, podendo usar sinais de terceiros (Decreto, Art. 26, § 2º). Se o sinal divergir da aferição própria, aplicar a alternativa **mais protetiva** (Decreto, Art. 25, § 4º) |
| **C. Administrador de comunidade ou canal em plataforma de terceiro** (servidor Discord, canal) | Limitado pelas APIs da plataforma: configurar flags etárias nativas (NSFW/18+), moderar ativamente, manter canal de denúncia e não fazer coleta externa nem publicidade segmentada a menores |

> **Responsabilidade solidária da cadeia (Lei, Art. 15):** cumprir o capítulo de aferição de idade não exime os demais agentes da cadeia digital. O papel B não pode delegar a conformidade ao papel A.

## 3. Obrigações materiais

### 3.1 Aferição de idade (Arts. 9º a 15)
- **Art. 9º, § 1º:** verificação de idade confiável **a cada acesso**, **vedada a autodeclaração**, para impedir o acesso a **conteúdos, produtos ou serviços impróprios, inadequados ou proibidos para menores de 18 anos**. O § 2º inclui material pornográfico e outros conteúdos vedados pela legislação. O § 3º obriga provedores de pornografia a **impedir a criação de contas** por menores.
- **Não generalize:** isso **não** significa exigir documento ou biometria a cada login em qualquer funcionalidade (Art. 6º, III, LGPD — necessidade). Aplique a verificação reforçada só nas rotas de risco etário. Nas demais, use sinais de idade e defaults protetivos (Art. 10: experiência adequada à idade, respeitando a autonomia progressiva).
- **Vedação de desvio de finalidade (Art. 13; Art. 24, § 3º):** dados coletados para aferir idade só servem para isso. Nunca use para perfilamento, marketing ou enriquecimento. Guarde o **resultado** (faixa, origem, método) e descarte o documento ou a biometria brutos (modelo `AgeAssurance` em `lgpd-consent-schema`).
- A ANPD certifica soluções de aferição e credencia entidades (Lei, Art. 11; Decreto, Art. 30).

### 3.2 Design protetivo (Arts. 6º a 8º e 18, § 2º)
- **Privacidade por padrão (Art. 7º):** o grau mais elevado de proteção vem configurado. Contas de menores começam privadas, sem indexação pública e sem geolocalização aberta. Configurações menos protetivas exigem informação clara (§ 1º).
- **Gerenciamento de riscos e avaliação de conteúdo por faixa etária (Art. 8º, I a V)**, com prevenção desde a concepção dos riscos listados no Art. 6º (exploração sexual, violência, automutilação, apostas, publicidade predatória etc.).
- **Prevenção de uso compulsivo (Art. 8º; Decreto, Art. 9º):** proibido ocultar pontos naturais de parada. Revise autoplay, feed infinito, streaks e notificações de reengajamento em contas de menores.
- **Interfaces manipulativas são vedadas (Art. 18, § 2º; Decreto, Art. 10):** sem dark patterns, sem dificultar cancelamento ou desativação de controles, sem urgência artificial.

### 3.3 Supervisão parental e vinculação de conta (Arts. 16 a 19 e 24)
- **Ferramentas de supervisão (Arts. 17 e 18):** controle de tempo de uso, restrição de compras, restrição de contato com desconhecidos, identificação de adultos que contatam a criança, gestão de privacidade e acesso a métricas de uso. Aviso claro quando a supervisão estiver ativa. Parâmetros mínimos serão definidos pela ANPD.
- **Informação sobre riscos (Art. 16):** acessível a pais e menores **sem exigir compra** do produto.
- **Vinculação a responsável (Art. 24, caput):** contas de menores **de até 16 anos** devem ser vinculadas à conta ou ao usuário de um responsável legal.
  - **Escopo controvertido:** o caput fala em "provedores de produtos ou serviços direcionados [...] ou de acesso provável", mas o artigo está no Capítulo IX ("Das Redes Sociais"), e o Guia o apresenta como obrigação específica de redes sociais. **Redes sociais: obrigatório.** Demais serviços com contas e interação: aplique (leitura mais protetiva, Art. 3º) **ou** documente a justificativa em `.lgpd/eca-digital.md`.
  - **Faixa:** "até 16 anos". Adote 16 **inclusive** (leitura mais protetiva; `classifyMinorAgeRules` em `lgpd-dsar`).
  - **§ 4º:** diante de indícios fundados de conta de menor fora das regras, suspenda o acesso e ofereça procedimento de recurso.
  - **§ 5º:** sem responsável vinculado, é **vedado reduzir o nível de proteção padrão**.
- **Produtos de monitoramento infantil (Art. 19):** garanta a inviolabilidade dos dados captados e informe a criança, em linguagem apropriada, de que está sendo monitorada.
- **Coordenação com a LGPD:** a vinculação do Art. 24 **não** se confunde com a base legal da LGPD (Art. 14 + **Enunciado CD/ANPD nº 1/2023** — ver `lgpd-legal-basis`). O consentimento parental do Art. 14, § 1º vale só para **crianças** e só quando a base legal for o consentimento.

### 3.4 Jogos eletrônicos (Arts. 20 e 21)
- **Loot boxes (Art. 20; Decreto, Art. 23):** vedadas em jogos direcionados a menores ou de acesso provável. O fornecedor deve verificar a idade e impedir o acesso de menores à funcionalidade. Alternativas do Decreto (Art. 23, § 1º): **versão sem loot box** ou funcionalidade **bloqueada por padrão** (neste caso, a verificação de idade é dispensada).
- **Interação entre usuários (Art. 21):** cumpra as salvaguardas do Art. 16 da Lei nº 14.852/2024, com interação **limitada por padrão** para garantir o consentimento dos pais (parágrafo único).

### 3.5 Publicidade e monetização (Arts. 22, 23 e 26)
- **Perfilamento para publicidade é vedado (Arts. 22 e 26):** é proibido criar perfis comportamentais de menores para direcionar publicidade comercial, inclusive com dados agregados ou grupais, análise emocional e RA/RV. Bloqueie pixels e SDKs de ad-tech em sessões e contas sinalizadas como `< 18` ou com idade não aferida em produto de acesso provável.
- **Monetização e impulsionamento (Art. 23; Decreto, Art. 34):** vedados para conteúdo que retrate menores de forma erotizada ou sexualmente sugestiva. Conteúdo monetizado ou impulsionado que explore a imagem ou a rotina de criança ou adolescente exige **autorização judicial** apresentada pelo usuário, sob pena de retirada.

### 3.6 Violações graves, denúncia e retirada (Arts. 27 a 30 e 32–33)
- **Remoção e comunicação (Art. 27):** remova e comunique conteúdos de aparente exploração, abuso sexual, sequestro e aliciamento. Os relatórios vão à **Polícia Federal**, pelo **Centro Nacional de Triagem de Notificações** (Decreto, Arts. 36 e 37).
  - **Retenção (Art. 27, §§ 2º e 3º):** guarde os dados associados pelo prazo do **Art. 15 do Marco Civil** (Lei nº 12.965/2014), prazo que pode ser estendido mediante requerimento. Configure isso em `lgpd-retention-erasure` como hipótese de conservação (Art. 16, I, LGPD).
- **Canal de notificação público e de fácil acesso (Arts. 28 e 29, § 3º):** retire o conteúdo violador assim que comunicado pela vítima, por representantes, pelo Ministério Público ou por entidades, **independentemente de ordem judicial** (Art. 29). A notificação identifica o conteúdo e o notificante; denúncia anônima é vedada (§ 2º).
- **Contestação (Art. 30):** o autor do conteúdo retirado tem direito a notificação, motivo, indicação de análise humana ou automatizada, recurso e prazos.
- **Uso abusivo de denúncias (Arts. 32 e 33):** detecte denúncias usadas para censura ou perseguição, com sanções graduais, recurso e registros detalhados.

### 3.7 Avaliação de impacto, transparência e representação
- **Avaliação de impacto à segurança e à saúde de crianças e adolescentes (Art. 16, parágrafo único; Decreto, Art. 47):** mapeie riscos e elabore relatório quando o tratamento for além do necessário. **Publique uma versão resumida** em linguagem clara (Decreto, Art. 47, § 1º). Integre ao RIPD (`lgpd-ripd`).
- **Relatórios semestrais em português (Art. 31):** obrigatórios para provedores com **mais de 1.000.000 de usuários crianças ou adolescentes registrados no Brasil**, qualquer que seja o papel no ecossistema.
- **Representante legal no País (Art. 40):** fornecedores estrangeiros devem mantê-lo, com poderes para receber citações e notificações.
- **Hardware (Art. 38):** equipamentos com acesso à internet levam adesivo de alerta em português na embalagem. Normalmente N/A para software.

## 4. Sanções (Art. 35)
- Advertência com prazo de até 30 dias para correção; **multa de até 10% do faturamento do grupo econômico no Brasil** (ou, sem faturamento, de R$ 10 a R$ 1.000 por usuário cadastrado), limitada a **R$ 50 milhões por infração**; suspensão temporária; proibição de atividades.
- **Art. 35, § 5º:** advertência e multa são aplicadas pela ANPD; **suspensão e proibição, pelo Poder Judiciário**. Filial de empresa estrangeira responde solidariamente pela multa (§ 2º).

## Workflow de engenharia

1. **Classificar aplicabilidade:** categoria presumida (1.1)? Se não, aplicar o teste cumulativo (1.2) e registrar critério por critério. Definir o papel (A, B ou C) e a modulação (1.3).
2. **Mapear funcionalidades por risco etário:** separar as funcionalidades gerais das impróprias ou proibidas para < 18 (Art. 9º, § 1º) e das de risco (chat aberto, compras, loot box, geolocalização, recomendação).
3. **Aferição de idade:** consumir os sinais de SO e loja (Decreto, Art. 26), manter mecanismo próprio (Art. 14, parágrafo único), aplicar verificação reforçada só nas rotas do Art. 9º, § 1º e registrar o resultado em `AgeAssurance`, sem documento bruto.
4. **Defaults protetivos e anti-compulsão:** privacidade máxima por padrão, sem autoplay ou feed infinito para menores, sem dark patterns. **Busque no código:** autoplay, infinite scroll, streaks, push de reengajamento e fluxos de cancelamento.
5. **Supervisão parental e vinculação até 16 anos:** `Guardian`/`MinorLink` em `lgpd-consent-schema`, com suspensão e recurso (Art. 24, § 4º) e bloqueio de redução de proteção sem responsável (§ 5º).
6. **Bloquear ad-tech e perfilamento** para contas `< 18` (Arts. 22 e 26). **Busque no código:** pixels, SDKs de atribuição e segmentação de anúncios.
7. **Monetização e jogos:** sem loot box (ou versão sem ou bloqueio por padrão), interação limitada por padrão, sem monetização de conteúdo com menores sem autorização judicial.
8. **Canal de denúncia e retirada:** endpoint público de notificação, fila de moderação, fluxo de contestação (Art. 30), comunicação à Polícia Federal (Art. 27) e retenção pelo Art. 15 do Marco Civil.
9. **Avaliação de impacto e transparência:** relatório com resumo público (Decreto, Art. 47), relatório semestral se > 1M menores (Art. 31) e representante legal se fornecedor estrangeiro (Art. 40).
10. **Documentar** em `.lgpd/eca-digital.md`.

## Template `.lgpd/eca-digital.md`

```markdown
# Avaliação ECA Digital — Lei nº 15.211/2025 e Decreto nº 12.880/2026

- **Data da avaliação**: {data} | **Próxima revisão**: {data + 6 meses} (reavaliar ao sair o Guia de Aferição de Idade)
- **Categoria presumida (Guia ANPD out/2026)**: {Nenhuma | Rede social | Loja | SO | Controle editorial | Jogo | Conteúdo adulto | IA generativa | E-commerce de produtos proibidos a menores}

## Teste de acesso provável (Art. 1º, parágrafo único — cumulativo)
| Critério | Presente? | Evidência |
|---|---|---|
| I. Probabilidade de uso e atratividade | {Sim/Não} | {gamificação, sinais reais de menores, público-alvo} |
| II. Facilidade de acesso e uso | {Sim/Não} | {cadastro aberto, loja pública, gratuidade, SSO corporativo} |
| III. Risco relevante | {Sim/Não} | {interação aberta, contato com desconhecidos, compras, recomendação} |

- **Aplicabilidade**: {Não aplicável (algum critério ausente — justificar) | Aplicável — direcionado | Aplicável — acesso provável | Aplicável — presunção legal}
- **Papel no ecossistema**: {A. Loja/SO | B. Fornecedor de aplicação | C. Administrador de comunidade}
- **Modulação (Art. 39)**: {porte, nº de usuários, grau de interferência no conteúdo; dispensa do § 1º, se houver}

## Mapeamento de risco etário por funcionalidade
| Funcionalidade | Imprópria/proibida < 18 (Art. 9º, § 1º)? | Mecanismo etário |
|---|---|---|
| {ex.: Feed educacional} | Não | Sinal de idade + defaults de privacidade máxima |
| {ex.: Loja de itens 18+} | Sim | Verificação confiável a cada acesso (vedada autodeclaração) |

## Controles
- [ ] Sinais de idade consumidos + mecanismo próprio (Lei, Art. 14; Decreto, Art. 26): {detalhe}
- [ ] Resultado da aferição sem documento bruto e sem outra finalidade (Art. 13): {detalhe}
- [ ] Privacidade máxima por padrão (Art. 7º): {detalhe}
- [ ] Anti-uso compulsivo (Art. 8º; Decreto, Art. 9º): {autoplay/feed infinito/streaks revisados}
- [ ] Sem dark patterns (Art. 18, § 2º; Decreto, Art. 10): {detalhe}
- [ ] Supervisão parental (Arts. 17–18): {detalhe}
- [ ] Vinculação a responsável até 16 anos (Art. 24) + suspensão/recurso (§ 4º) + § 5º: {implementado | N/A justificado — leitura de escopo adotada}
- [ ] Sem perfilamento publicitário para < 18 (Arts. 22 e 26): {SDKs/pixels bloqueados}
- [ ] Loot boxes (Art. 20; Decreto, Art. 23): {ausentes | versão sem | bloqueadas por padrão | N/A}
- [ ] Interação em jogos limitada por padrão (Art. 21): {detalhe | N/A}
- [ ] Monetização de conteúdo com menores (Art. 23; Decreto, Art. 34): {detalhe | N/A}
- [ ] Canal público de denúncia + retirada + contestação (Arts. 28–30): {endpoint/fluxo}
- [ ] Comunicação à Polícia Federal + retenção pelo Art. 15 do Marco Civil (Art. 27; Decreto, Arts. 36–37): {detalhe}
- [ ] Avaliação de impacto + resumo público (Art. 16, parágrafo único; Decreto, Art. 47): {link}
- [ ] Relatório semestral (Art. 31 — > 1M menores no BR): {Sim | N/A}
- [ ] Representante legal no País (Art. 40): {Sim | N/A — fornecedor nacional}

## Monitoramento normativo pendente
- Guia final da ANPD sobre aferição de idade e parâmetros mínimos de supervisão parental.
- Atualização dos regulamentos de fiscalização e dosimetria da ANPD para o ECA Digital; fiscalização prevista a partir de jan/2027.
```

## Status update

```markdown
## F5 / L7a — ECA Digital ✓ (ou N/A documentado)
- Aplicabilidade, categoria e papel: {resumo}
- Controles ativos: {lista}
- Pendências técnicas/jurídicas: {lista}
```

## Fontes oficiais
- Lei nº 15.211/2025: https://www.planalto.gov.br/ccivil_03/_ato2023-2026/2025/lei/l15211.htm
- Decreto nº 12.880/2026: https://www.planalto.gov.br/ccivil_03/_ato2023-2026/2026/decreto/d12880.htm
- Guia ANPD (out/2026): https://www.gov.br/anpd/pt-br/centrais-de-conteudo/materiais-educativos-e-publicacoes/guia-fornecedores-de-produtos-ou-servicos-de-tecnologia-da-informacao.pdf
- Página ECA Digital da ANPD (cronograma e guias): https://www.gov.br/anpd/pt-br/assuntos/eca-digital
