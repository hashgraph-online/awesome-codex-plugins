---
name: lgpd-ripd
description: Produce a Relatório de Impacto à Proteção de Dados Pessoais (RIPD / DPIA) under LGPD Art. 38, applying the cumulative high-risk test of Resolução CD/ANPD nº 2/2022 Art. 4 (multifactorial large scale + specific criteria) or precautionary risk governance. Includes LINDDUN privacy threat modeling, inference risks, algorithmic bias, and AI/LLM exposure. Produces `.lgpd/RIPD/ripd-{slug}.md`.
---

# RIPD — Relatório de Impacto à Proteção de Dados Pessoais

Art. 38 da LGPD: documento do controlador que contém a descrição dos processos de tratamento de dados pessoais que podem gerar riscos às liberdades civis e aos direitos fundamentais, bem como medidas, salvaguardas e mecanismos de mitigação de risco.

## Status regulatório (atualizado até novembro de 2026)

- A regulamentação específica do RIPD integra a **Agenda Regulatória 2025–2026 da ANPD** (Res. CD/ANPD nº 31/2025).
- **Deliberação de setembro de 2026 (Voto nº 11/2025/DIR-MW)**: o Conselho Diretor da ANPD decidiu por unanimidade **não aprovar e arquivar** a minuta isolada do *Guia Orientativo sobre Tratamento de Dados Pessoais de Alto Risco* (que sugeria metodologia de pontuação em etapas e patamar preliminar de 2 milhões de titulares), determinando que os critérios de alto risco sejam consolidados de forma integrada dentro da futura norma de **RIPD**.
- Enquanto a resolução específica de RIPD não é publicada, utilize as balizas vigentes do **Art. 38 da LGPD**, do **Art. 4º da Resolução CD/ANPD nº 2/2022** e das perguntas orientativas publicadas pela ANPD.

## Quando elaborar um RIPD: obrigação normativa vs. boa prática preventiva

Separe sempre no relatório se o RIPD decorre de **enquadramento normativo de alto risco / requisição** ou de **boa prática preventiva de engenharia e governança**:

### 1. Enquadramento de Alto Risco (teste cumulativo — Res. CD/ANPD nº 2/2022, Art. 4º)

Para caracterizar alto risco segundo o parâmetro normativo vigente da ANPD, devem concorrer **pelo menos UM critério geral E pelo menos UM critério específico**:

- **Critérios gerais (ao menos 1)**:
  - **(I) Larga escala** — avaliada de forma **multifatorial no caso concreto** (Art. 4º, § 1º), considerando conjuntamente: número de titulares afetados, volume de dados, duração, permanência, frequência do tratamento e extensão geográfica (**não use corte numérico fixo inventado**); **OU**
  - **(II) Afetação significativa a interesses e direitos fundamentais** — tratamentos que possam impedir o exercício de direitos, o acesso a um serviço essencial, causar discriminação ilícita/abusiva ou dano material/moral relevante.

- **Critérios específicos (ao menos 1)**:
  - **(I)** Uso de tecnologias emergentes ou inovadoras (ex.: IA generativa/preditiva, reconhecimento facial);
  - **(II)** Vigilância ou controle de zonas acessíveis ao público;
  - **(III)** Decisões tomadas unicamente com base em tratamento automatizado de dados pessoais, inclusive definição de perfis (*profiling*);
  - **(IV)** Utilização de dados pessoais sensíveis ou de dados pessoais de crianças, de adolescentes ou de idosos.

### 2. Outras hipóteses legais de exigibilidade
- Requisição expressa da ANPD a qualquer tempo (**Art. 38, caput**, e **Art. 10, § 3º** em tratamentos baseados em legítimo interesse);
- Plataformas sujeitas ao **ECA Digital**: **avaliação de impacto à segurança e à saúde de crianças e adolescentes** com mapeamento de riscos (Lei nº 15.211/2025, Art. 16, parágrafo único) e **publicação de versão resumida** em linguagem clara (Decreto nº 12.880/2026, Art. 47, § 1º). Pode integrar o RIPD, mas cobre também riscos de design (uso compulsivo, contato com desconhecidos, recomendação), não só de dados pessoais. Ver `lgpd-eca-digital-minors`.

### 3. RIPD Preventivo (*boa prática recomendada*)
- Quando houver **apenas um critério específico isolado** (ex.: coleta pontual de biometria de um grupo restrito sem larga escala e sem impacto significativo sobre acesso a direitos), o teste cumulativo da Res. 2/2022 **não se completa automaticamente**. Ainda assim, **recomenda-se elaborar RIPD simplificado/preventivo como boa prática de *privacy-by-design* (Art. 46, § 2º e Art. 50)** — registrando expressamente no cabeçalho do documento tratar-se de **avaliação preventiva de risco**, e não de obrigação legal automática.

## Estrutura técnica do RIPD (com Threat Modeling e IA)

1. **Identificação e natureza do relatório**: controlador, Encarregado, versão, e classificação explícita (`Alto risco cumulativo` | `Requisição/Legítimo interesse` | `Preventivo — boa prática`).
2. **Contexto, finalidade e necessidade (Art. 6º, I a III)**: justificativa, volume multifatorial e alternativas menos intrusivas descartadas.
3. **Fluxo completo dos dados e papéis dos agentes**: coleta → armazenamento → inferência/uso → compartilhamento (operadores vs. controladores independentes/conjuntos) → retenção/eliminação.
4. **Base legal e direitos dos titulares**: enquadramento nos Arts. 7º/11 (+ melhor interesse se menores, Enunciado 1/2023) e atendimento aos direitos dos Arts. 18 e 20.
5. **Modelagem de ameaças de privacidade (LINDDUN) e riscos de IA**:
   - **L**inking / **I**dentifying (re-identificação por cruzamento e quasi-identificadores);
   - **N**on-repudiation / **D**etecting (inferência de atributos sensíveis a partir de metadados/uso);
   - **D**ata disclosure (vazamento em banco, logs, SDKs, caches ou prompts);
   - **U**nawareness / **N**on-compliance (assimetria informacional, dark patterns, desvio de finalidade);
   - **Riscos específicos de IA e decisões automatizadas**: discriminação algorítmica e viés (Art. 6º, IX), retenção ou treinamento indevido em provedores externos de LLM, vazamento entre tenants em RAG/embeddings, alucinação sobre dados pessoais (violação do princípio da qualidade — Art. 6º, V) e ausência de explicabilidade/revisão (Art. 20).
6. **Matriz Probabilidade × Impacto (ISO/IEC 29134 / ISO 31000)**, controles mitigatórios e **risco residual**.
7. **Parecer do Encarregado e aprovação da liderança** (`⏸ CHECKPOINT` obrigatório).

## Workflow

1. Verifique as atividades sinalizadas em `.lgpd/data-map.md` aplicando o teste cumulativo (1 geral + 1 específico) e separe as obrigatórias das preventivas.
2. Gere `.lgpd/RIPD/ripd-{slug}.md` a partir de [`assets/ripd-template.md`](assets/ripd-template.md).
3. Execute a modelagem de riscos técnicos (incluindo LINDDUN e IA se houver modelos/automação).
4. **⏸ CHECKPOINT**: pause obrigatoriamente para revisão humana, jurídica e parecer do Encarregado antes de aprovar a versão final.

## Status update

```markdown
## F13 / L12 — RIPD ✓
- {N} RIPDs elaborados ({A} alto risco cumulativo, {B} preventivos por boa prática)
- Riscos mapeados: {total} ({mitigados} mitigados, {residuais} residuais documentados)
- ⏸ Aprovação do Encarregado: {pendente | aprovada em YYYY-MM-DD}
```
