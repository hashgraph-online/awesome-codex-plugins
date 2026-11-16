# Referência Normativa LGPD — Encode rígido

Use este arquivo como fonte da verdade normativa desta coleção (revisado até **novembro de 2026**). Não invente prazos, percentuais, thresholds numéricos ou artigos, e separe sempre **obrigação legal expressa** de **boa prática de engenharia / gestão de risco**.

## Lei nº 13.709/2018 (LGPD)

| Artigo | Conteúdo crítico |
|---|---|
| Art. 5º | Definições (dado pessoal, sensível, anonimização, consentimento, controlador, operador, encarregado, tratamento) |
| Art. 6º | 10 princípios: finalidade, adequação, necessidade, livre acesso, qualidade, transparência, segurança, prevenção, não discriminação, responsabilização |
| Art. 7º | 10 bases legais para dados comuns (I consentimento, II obrigação legal/regulatória, III políticas públicas, IV pesquisa, V contrato/procedimentos pré-contratuais, VI exercício regular de direitos em processo, VII proteção da vida, VIII tutela da saúde, IX legítimo interesse, X proteção do crédito) |
| Art. 9º | Direito do titular ao acesso facilitado às informações sobre o tratamento — 7 elementos obrigatórios |
| Art. 10 | Legítimo interesse — requisitos + LIA + possibilidade de a ANPD solicitar RIPD (§ 3º) |
| Art. 11 | Bases legais para dados sensíveis (I consentimento específico e destacado OU II sete hipóteses sem consentimento) |
| Art. 14 | Crianças (< 12 anos) e adolescentes (12 a < 18 anos, ECA Art. 2º) — prevalência obrigatória do **melhor interesse**. Conforme **Enunciado CD/ANPD nº 1/2023**, admite qualquer base dos Arts. 7º ou 11; o consentimento específico e em destaque de ao menos um dos pais/responsáveis (§ 1º) aplica-se quando o **consentimento** for a base legal adotada para crianças (ressalvado o § 3º) |
| Arts. 15–16 | Término do tratamento e eliminação, ressalvadas as hipóteses legais de conservação (Art. 16, I a IV), com minimização e bloqueio para outras finalidades |
| Art. 18 | Direitos do titular (I a IX + §§ 1º a 8º, incluindo propagação imediata aos agentes com quem houve uso compartilhado no § 6º) |
| Art. 19, I e II | Confirmação e acesso: **(I)** formato simplificado = **imediato** (para ATPP: até **15 dias**, Res. 2/2022 Art. 14, I); **(II)** declaração clara e completa = até **15 dias corridos** da requisição (para ATPP: até **30 dias**, Res. 2/2022 Art. 14) |
| Art. 20 | Revisão de decisões tomadas unicamente com base em tratamento automatizado (sem exigência legal expressa de revisor humano após a Lei 13.853/2019, embora recomendável em decisões de alto impacto) |
| Arts. 33–36 | Transferência internacional — 9 hipóteses do Art. 33 (incluindo I decisão de adequação e II, b cláusulas-padrão) |
| Art. 37 | ROPA — obrigatório para controlador e operador |
| Art. 38 | RIPD — quando exigido pela ANPD ou em tratamentos de alto risco (avaliar distinção entre obrigação normativa e RIPD preventivo por boa prática) |
| Art. 39 | Operador — realiza o tratamento segundo as instruções lícitas fornecidas pelo controlador |
| Art. 41 | Encarregado — designação, divulgação pública da identidade/contato e atribuições |
| Art. 42, § 1º, I e II | **Responsabilidade condicional**: o operador responde **solidariamente** quando descumprir obrigações da LGPD **ou** não seguir instruções lícitas do controlador (equiparando-se a este); controladores diretamente envolvidos respondem solidariamente (II), observadas as excludentes do Art. 43 |
| Art. 46 | Medidas de segurança, técnicas e administrativas aptas a proteger os dados + privacy-by-design (§ 2º) |
| Art. 48 | Comunicação de incidente de segurança à ANPD e ao titular |
| Art. 52, II | **Multa simples de até 2% do faturamento no Brasil, limitada a R$ 50 milhões por infração** |

## Resoluções, Enunciados e Deliberações da ANPD

### Res. CD/ANPD nº 2/2022 — Agentes de Tratamento de Pequeno Porte (ATPP)

- **Enquadramento**: microempresas, EPPs, startups (receita bruta até R$ 16 milhões/ano), pessoas jurídicas de direito privado sem fins lucrativos e pessoas naturais/entes despersonalizados que tratem dados com fins econômicos (desde que não pertençam a grupo econômico que exceda os limites e não realizem tratamento de alto risco para fins das dispensas aplicáveis).
- **Art. 4º — teste cumulativo de alto risco**: configura alto risco o tratamento que atenda **simultaneamente** a pelo menos **um critério geral** **E** pelo menos **um critério específico**:
  - **Critérios gerais**: (I) tratamento em larga escala; ou (II) tratamento que possa afetar significativamente interesses e direitos fundamentais dos titulares.
  - **Critérios específicos**: (I) uso de tecnologias emergentes ou inovadoras; (II) vigilância ou controle de zonas acessíveis ao público; (III) decisões tomadas unicamente com base em tratamento automatizado, inclusive definição de perfis; (IV) utilização de dados pessoais sensíveis ou de dados pessoais de crianças, de adolescentes e de idosos.
- **Art. 4º, § 1º — avaliação de larga escala**: **não existe número fixo de titulares na norma**. A larga escala é avaliada no caso concreto considerando fatores conjugados: número de titulares afetados, volume de dados envolvidos, duração, permanência, frequência do tratamento e extensão geográfica.
- **Art. 11 — dispensa de Encarregado**: ATPP que não realize tratamento de alto risco é dispensado de indicar Encarregado formal, **mas deve obrigatoriamente disponibilizar canal de comunicação** com o titular (Art. 11, § 1º).
- **Art. 14 — prazos diferenciados para ATPP**:
  - **Declaração simplificada (Art. 19, I LGPD)**: prazo de até **15 dias** (Art. 14, I) — **não** se exige resposta imediata como nos demais controladores.
  - **Prazos em dobro**: aplicam-se nos demais atendimentos a titulares (ex.: **30 dias** para declaração completa do Art. 19, II) e na comunicação de incidentes (**6 dias úteis**, salvo potencial comprometimento à integridade física ou moral dos titulares ou à segurança nacional/pública — Res. 15/2024).

### Enunciado CD/ANPD nº 1/2023 — Dados de Crianças e Adolescentes

- Publicado em 24/05/2023: *"O tratamento de dados pessoais de crianças e adolescentes poderá ser realizado com base nas hipóteses legais previstas no art. 7º ou no art. 11 da Lei Geral de Proteção de Dados Pessoais (LGPD), desde que observado e prevalecente o seu melhor interesse, a ser avaliado no caso concreto, nos termos do art. 14 da Lei."*
- Implicação técnica: **não implemente consentimento parental como requisito universal** para toda operação envolvendo menores; verifique primeiro qual é a base legal adequada da atividade e documente a avaliação do melhor interesse.

### Res. CD/ANPD nº 4/2023 — Dosimetria e Aplicação de Sanções

- Classificação das infrações: leves, médias e graves.
- Reincidência específica ou genérica considerada no janela de **5 anos**.
- Atenuantes relevantes para engenharia/governança: cessação espontânea da infração, boa-fé e implementação comprovada de política de boas práticas e governança ou medidas técnicas/administrativas prévias (Art. 50 / Art. 46).

### Res. CD/ANPD nº 15/2024 — Comunicação de Incidente de Segurança (RCIS)

- **Art. 5º — incidente notificável (cumulativo)**: risco ou dano relevante aos titulares **E** pelo menos uma das categorias: (I) dados sensíveis; (II) dados de crianças, adolescentes ou idosos; (III) dados financeiros; (IV) dados de autenticação em sistemas; (V) dados protegidos por sigilo legal, judicial ou profissional; (VI) dados em larga escala.
- **Art. 6º** — **3 dias úteis** contados do conhecimento de que o incidente afetou dados pessoais para comunicar à ANPD (6 dias úteis para ATPP, salvo exceções de integridade física/moral ou segurança pública/nacional).
- **Art. 6º, § 2º** — 12 itens obrigatórios na comunicação à ANPD; complementação em até **20 dias úteis** se a comunicação inicial foi preliminar.
- **Art. 9º** — comunicação aos titulares em **3 dias úteis**, contendo 7 itens obrigatórios em linguagem simples.
- **Art. 10** — manutenção de registro interno de **todos os incidentes de segurança** (inclusive os não comunicados à ANPD) por **no mínimo 5 anos** (nota: este prazo refere-se a **incidentes de segurança**, não a logs gerais de requisições DSAR).

### Res. CD/ANPD nº 18/2024 — Regulamento do Encarregado

- Pode ser pessoa natural (integrante do quadro ou externa) **ou** pessoa jurídica.
- Divulgação obrigatória da identidade (nome completo se PF; nome empresarial + responsável PF se PJ) e informações de contato em local de destaque e fácil acesso no sítio eletrônico.
- Ausência de exigência de certificação ou inscrição profissional específica.
- O Encarregado não responde perante a ANPD pela conformidade do tratamento realizado pelo controlador (Art. 15, § 2º).
- Dever de prevenir **conflito de interesses** (especialmente acúmulo com chefia que determine finalidades/meios de sistemas críticos de TI/negócio sem segregação).

### Res. CD/ANPD nº 19/2024 — Regulamento de Transferência Internacional

- Regulamenta procedimentos de decisões de adequação, cláusulas específicas, normas corporativas globais (BCRs) e aprova as **Cláusulas-Padrão Contratuais brasileiras (Anexo II)**.
- As Cláusulas-Padrão do Anexo II devem ser adotadas integralmente e sem alteração de texto (prazo de adaptação contratual encerrado em agosto de 2025).

### Res. CD/ANPD nº 30/2025 e nº 31/2025 — Prioridades e Agenda Regulatória

- **Res. 30/2025 (Mapa de Temas Prioritários 2026–2027)**: fiscalização prioritária em (i) direitos dos titulares; (ii) dados de crianças e adolescentes no ambiente digital; (iii) tratamento pelo Poder Público; (iv) inteligência artificial e tecnologias emergentes (incluindo biometria e raspagem de dados).
- **Res. 31/2025 (Agenda Regulatória 2025–2026)**: inclui direitos dos titulares, RIPD, medidas de segurança, inteligência artificial, anonimização e dados biométricos.

### Res. CD/ANPD nº 32/2026 — Decisão de Adequação para União Europeia e EEE

- Publicada em **26 de janeiro de 2026**: primeira decisão de adequação da ANPD com fundamento no **Art. 33, I da LGPD**.
- Reconhece grau adequado de proteção de dados para transferências destinadas aos **Estados-membros da União Europeia**, às **instituições, órgãos e agências da UE** e aos países da EFTA integrantes do Espaço Econômico Europeu (**Islândia, Liechtenstein e Noruega**).
- **Efeito prático**: transferências cobertas por esta decisão **dispensam Cláusulas-Padrão Contratuais brasileiras (Res. 19/2024)** ou BCRs (mantida a necessidade de contrato/DPA do Art. 39 quando o destinatário atuar como operador, bem como transparência ao titular).
- **Exceções expressas**: a decisão **não se aplica** a transferências efetuadas exclusivamente para fins de segurança pública, defesa nacional, segurança do Estado ou investigação e repressão de infrações penais.

### Deliberação CD/ANPD (setembro de 2026) — Arquivamento da minuta de Guia de Alto Risco

- Pelo **Voto nº 11/2025/DIR-MW** (setembro de 2026), o Conselho Diretor decidiu por unanimidade **não aprovar e determinar o arquivamento** da minuta do *Guia Orientativo sobre Tratamento de Dados Pessoais de Alto Risco* (que propunha metodologia de pontuação e o patamar preliminar de 2 milhões de titulares para larga escala).
- O tema foi devolvido à Superintendência de Regulação (SRE) para tratamento integrado dentro da futura regulamentação do **RIPD**. Portanto, **não aplique o número de 2 milhões de titulares como regra ou threshold automático**.

## Lei nº 15.211/2025 e Decreto nº 12.880/2026 — ECA Digital

- **Vigência**: Lei em vigor desde **17 de março de 2026** (Art. 41-A, redação da Lei nº 15.352/2026). Regulamentada pelo **Decreto nº 12.880, de 18 de março de 2026**, cujo Art. 1º, parágrafo único, atribui à **ANPD** a regulamentação e a fiscalização. A competência já havia sido atribuída pelo Decreto nº 12.622/2025. O Decreto nº 12.881/2026 trata da estrutura da Agência.
- **Cronograma ANPD** (página oficial do ECA Digital; confirmar antes de emitir artefatos): adaptação e monitoramento de agosto a novembro de 2026; **fiscalização a partir de janeiro de 2027**. O Guia de *Mecanismos de Aferição de Idade* segue em consolidação: não trate a minuta como norma definitiva.
- **Escopo (Art. 1º)**: produtos ou serviços de TI direcionados a crianças e adolescentes **ou de acesso provável**. O **acesso provável** exige três critérios **cumulativos** (Art. 1º, parágrafo único): (I) probabilidade suficiente de uso e atratividade; (II) facilidade considerável de acesso e uso; (III) risco relevante à privacidade, à segurança ou ao desenvolvimento biopsicossocial.
- **Guia ANPD "Fornecedores de produtos ou serviços de TI: escopo e obrigações gerais do ECA Digital" (v1.0, 28/10/2026)**: presume acesso provável em **8 categorias**: redes sociais, lojas de aplicações, sistemas operacionais, serviços com controle editorial, jogos eletrônicos, provedores de conteúdo adulto, **sistemas de IA generativa** e **e-commerce que intermedeia produtos ou serviços proibidos para menores**. A presunção só se afasta de forma motivada. A autoavaliação do fornecedor **não vincula a ANPD** (Decreto, Art. 19, § 2º). Mensageria privada interpessoal **não** é rede social. O Guia é orientativo e não cria obrigações.
- **Tratamento diferenciado (Art. 39)**: os Arts. 6º, 17, 18, 19, 20, 27, 28, 29, 31, 32 e 40 são modulados por funcionalidades, grau de interferência no conteúdo, número de usuários e porte. **Não há dispensa equivalente à de ATPP.** O § 1º prevê dispensa parcial para controle editorial e conteúdo licenciado com contas infantis e supervisão parental.
- **Art. 7º** — privacidade no grau mais elevado por padrão. **Art. 8º** — gerenciamento de riscos, avaliação de conteúdo por faixa etária e prevenção de uso compulsivo (Decreto, Art. 9º: vedado ocultar pontos naturais de parada). **Art. 18, § 2º** e **Decreto, Art. 10** — vedação de interfaces e práticas manipulativas.
- **Art. 9º, § 1º — verificação de idade**: mecanismos confiáveis a cada acesso, vedada a autodeclaração, para impedir o acesso a **conteúdos, produtos ou serviços impróprios, inadequados ou proibidos para menores de 18 anos**. **Não** equivale a impor verificação documental ou biométrica a cada acesso em qualquer funcionalidade. O § 3º veda a criação de contas por menores em provedores de pornografia.
- **Sinais de idade**:
  - **Lei, Art. 12, III**: lojas e sistemas operacionais fornecem sinal de idade por API.
  - **Decreto, Art. 25**: o sinal é **gratuito** e restrito ao estritamente necessário, **sem data de nascimento exata, identidade civil ou dados de perfilamento** (§ 1º). Aferição por método confiável, preferencialmente credenciais verificáveis (§ 2º, II). Se houver divergência, aplica-se a alternativa mais protetiva (§ 4º).
  - **Lei, Art. 14, parágrafo único**: a aplicação deve manter **mecanismos próprios**, independentemente das lojas e dos sistemas operacionais.
  - **Decreto, Art. 26, § 3º**: receber o sinal não exime da efetividade das medidas.
  - **Lei, Art. 15**: responsabilidade solidária da cadeia.
- **Art. 13** — dados de aferição de idade só podem ser usados para essa finalidade.
- **Art. 16, parágrafo único + Decreto, Art. 47** — avaliação de impacto à segurança e à saúde de crianças e adolescentes, com **versão resumida publicada**.
- **Art. 20 + Decreto, Art. 23** — vedação de *loot boxes* em jogos direcionados ou de acesso provável. O Decreto exige verificar idade e impedir o acesso de menores, ou oferecer **versão sem loot box**, ou manter a funcionalidade **bloqueada por padrão** (o que dispensa a verificação). **Art. 21** — interação entre usuários em jogos limitada por padrão.
- **Arts. 22 e 26** — vedação de perfilamento de menores para direcionamento de publicidade comercial (inclusive análise emocional e RA/RV). **Art. 23 + Decreto, Art. 34** — vedada a monetização ou impulsionamento de conteúdo erotizado com menores; conteúdo monetizado que explore a imagem ou a rotina de menores exige autorização judicial.
- **Art. 24** — contas de usuários **de até 16 anos** vinculadas à conta de um responsável legal. O caput menciona provedores direcionados ou de acesso provável, mas o artigo está no Capítulo IX ("Das Redes Sociais") e o Guia o trata como obrigação de redes sociais: **escopo controvertido**, registre a leitura adotada. O § 4º prevê suspensão com recurso; o § 5º veda reduzir a proteção padrão sem responsável vinculado.
- **Art. 27 + Decreto, Arts. 36–37** — remoção e comunicação de conteúdo de exploração, abuso sexual, sequestro e aliciamento, com relatórios à **Polícia Federal** (Centro Nacional de Triagem de Notificações). Retenção dos dados pelo prazo do **Art. 15 do Marco Civil**, prorrogável (§§ 2º e 3º).
- **Arts. 28 a 30** — mecanismo público de notificação, retirada sem ordem judicial quando comunicada pela vítima, representantes, MP ou entidades (vedada a denúncia anônima), e direito de contestação do autor. **Arts. 32–33** — combate ao uso abusivo de denúncias.
- **Art. 31** — relatórios semestrais em português para provedores com **mais de 1 milhão de usuários crianças ou adolescentes registrados no Brasil**.
- **Art. 35** — advertência; multa de até **10% do faturamento do grupo econômico no Brasil** ou de R$ 10 a R$ 1.000 por usuário cadastrado, limitada a R$ 50 milhões por infração; suspensão; proibição. Advertência e multa são aplicadas pela ANPD; **suspensão e proibição, pelo Judiciário** (§ 5º).
- **Art. 40** — fornecedor estrangeiro deve manter representante legal no País.

## Lei nº 15.352/2026

Transformou a ANPD em agência reguladora de natureza especial (autarquia em regime especial), fortalecendo autonomia administrativa, poder normativo e estrutura de fiscalização.

## Matriz de decisão normativa (sem atalhos inventados)

| Situação concreta | Consequência normativa |
|---|---|
| Receita > R$ 4,8M/ano (EPP) e fora de startup ≤ R$ 16M/ano (ou com tratamento de alto risco) | Fora das dispensas de ATPP — Encarregado formal obrigatório, DSAR simplificado imediato e completo em 15 dias, incidente notificável em 3 dias úteis |
| ATPP de baixo risco (Res. 2/2022) | Dispensado de Encarregado formal **desde que mantenha canal de comunicação** (Art. 11); DSAR simplificado em até **15 dias** e completo em até **30 dias** (Art. 14) |
| Critério geral (larga escala multifatorial OU impacto significativo) **+** critério específico (IA/emergente, vigilância, decisão automatizada/profiling, ou dados sensíveis/menores/idosos) | **Alto risco** no teste cumulativo da Res. 2/2022, Art. 4º → afasta dispensas de ATPP e indica elaboração de RIPD |
| Apenas dado sensível, biometria ou decisão automatizada **sem** critério geral | Não preenche sozinho o teste cumulativo da Res. 2/2022, mas **RIPD preventivo** é recomendado como boa prática de gestão de risco (identificar expressamente como boa prática) |
| Transferência internacional para UE ou EEE (Islândia, Liechtenstein, Noruega) em atividade comercial comum | Coberta pela **Decisão de Adequação da Res. CD/ANPD nº 32/2026** (Art. 33, I) — **não exige** Cláusulas-Padrão brasileiras (mantido DPA Art. 39 se operador) |
| Transferência internacional para país **sem** decisão de adequação (ex.: EUA) | Exige mecanismo válido do Art. 33 — tipicamente **Cláusulas-Padrão da Res. 19/2024 Anexo II** (Art. 33, II, b), BCRs ou outra hipótese aplicável |
| Tratamento de dados de crianças (< 12) ou adolescentes (12–17) | Avaliar **melhor interesse** + base legal nos Arts. 7º ou 11 (**Enunciado 1/2023**); exigir consentimento parental destacado (Art. 14, § 1º) quando a base for o consentimento para crianças |
| Produto/serviço direcionado a menores ou de **acesso provável** | Avaliar obrigações do **ECA Digital** moduladas pelo papel/controle (Decreto 12.880/2026 + Guia ANPD out/2026); verificação a cada acesso (Art. 9º, § 1º) obrigatória para conteúdos/serviços impróprios ou proibidos para < 18 |
| Produto em categoria presumida pelo Guia ANPD (rede social, loja, SO, controle editorial, jogo, conteúdo adulto, IA generativa, e-commerce de itens proibidos a menores) | ECA Digital aplica-se por presunção; afastá-la exige motivação demonstrando que falta algum critério do Art. 1º, parágrafo único |
| Produto fora das categorias presumidas | Teste cumulativo do Art. 1º, parágrafo único (atratividade **e** facilidade de acesso **e** risco relevante); ausência de qualquer critério → N/A documentado |
| App que recebe sinal de idade do SO ou da loja | Obrigatório manter mecanismo próprio (Lei, Art. 14, parágrafo único); o sinal não transfere a responsabilidade (Decreto, Art. 26, § 3º); divergência → alternativa mais protetiva (Decreto, Art. 25, § 4º) |

## Fontes oficiais (verificar antes de emissão final de artefatos)

- Lei nº 13.709/2018 (LGPD): https://www.planalto.gov.br/ccivil_03/_ato2015-2018/2018/lei/l13709.htm
- Lei nº 15.211/2025 (ECA Digital): https://www.planalto.gov.br/ccivil_03/_ato2023-2026/2025/lei/l15211.htm
- Decreto nº 12.880/2026: https://www.planalto.gov.br/ccivil_03/_ato2023-2026/2026/decreto/d12880.htm
- Guia ANPD ECA Digital — Fornecedores de TI (out/2026): https://www.gov.br/anpd/pt-br/centrais-de-conteudo/materiais-educativos-e-publicacoes/guia-fornecedores-de-produtos-ou-servicos-de-tecnologia-da-informacao.pdf
- Página ECA Digital da ANPD: https://www.gov.br/anpd/pt-br/assuntos/eca-digital
- Portal oficial da ANPD (Resoluções, Enunciados e Guias Orientativos): https://www.gov.br/anpd/pt-br
