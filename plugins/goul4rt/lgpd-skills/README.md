# lgpd-skills — LGPD Privacy Engineering Toolkit

> **AI-assisted privacy auditing, implementation and governance for software projects.**
> Toolkit modular e orquestrado de **Agent Skills** — compatível com **Claude Code, Codex, Gemini CLI, Cursor e OpenCode** — para diagnóstico técnico de código, implementação de controles de engenharia de privacidade e governança de artefatos sob a **Lei nº 13.709/2018 (LGPD)**, normas da **ANPD (até nov/2026)** e **Lei nº 15.211/2025 + Decreto nº 12.880/2026 (ECA Digital)**.

[![License: MIT](https://img.shields.io/badge/License-MIT-yellow.svg)](./LICENSE)
[![CI](https://github.com/goul4rt/lgpd-skills/actions/workflows/ci.yml/badge.svg)](./.github/workflows/ci.yml)
[![PRs Welcome](https://img.shields.io/badge/PRs-welcome-brightgreen.svg)](./CONTRIBUTING.md)
[![LGPD](https://img.shields.io/badge/LGPD-Lei%2013.709%2F2018-blue)](https://www.planalto.gov.br/ccivil_03/_ato2015-2018/2018/lei/l13709.htm)
[![ECA Digital](https://img.shields.io/badge/ECA%20Digital-Lei%2015.211%2F2025-blue)](https://www.planalto.gov.br/ccivil_03/_ato2023-2026/2025/lei/l15211.htm)

---

> **EN — Quick overview:** **LGPD Privacy Engineering Toolkit** — an Agent Skills bundle (works in Claude Code, Codex, Gemini CLI, Cursor, and OpenCode) for AI-assisted privacy auditing, technical control implementation, and living governance in software repositories. One orchestrator skill (`lgpd-audit`) coordinates 18 specialized sub-skills covering data mapping, legal basis (including Enunciado ANPD 1/2023), DPO/ATPP channels, ROPA, RIPD (with LINDDUN & AI threat modeling), event-sourced consent ledger, DSAR endpoints (standard vs. ATPP SLAs), emergency incident response (Res. 15/2024), field encryption, retention/erasure, vendor DPAs, international transfers (Res. 32/2026 EU/EEA adequacy & Res. 19/2024 SCCs), and ECA Digital (Lei 15.211/2025 + Decreto 12.880/2026). Includes automated normative/schema/code regression tests. MIT licensed.

---

## 📑 Índice

- [O que é (e o que não é)](#-o-que-é-e-o-que-não-é)
- [Quando usar](#-quando-usar)
- [Instalação](#-instalação)
- [Como usar](#-como-usar)
- [As 19 skills](#-as-19-skills)
- [Living artifacts em `.lgpd/`](#-living-artifacts-em-lgpd)
- [Cobertura normativa (revisão nov/2026)](#-cobertura-normativa-revisão-nov2026)
- [Qualidade e testes automatizados](#-qualidade-e-testes-automatizados)
- [Disclaimer jurídico](#%EF%B8%8F-disclaimer-jurídico)
- [Contribuindo](#-contribuindo)
- [Licença](#-licença)

---

## 🎯 O que é (e o que não é)

O `lgpd-skills` é um **Toolkit de Engenharia de Privacidade** composto por **19 Agent Skills coordenadas**:
- **1 maestro** (`lgpd-audit`) que detecta emergências de segurança sem burocracia, gerencia dependências entre etapas, mantém estado em `.lgpd/` e pausa em checkpoints obrigatórios;
- **18 sub-skills especializadas**, executáveis isoladamente ou em pipeline.

### Escopo real: código vs. conformidade organizacional

Nenhuma ferramenta que analisa apenas um repositório de código pode "certificar" ou garantir que uma organização está em conformidade jurídica plena. Este toolkit adota fronteiras transparentes:

| O que o toolkit FAZ no repositório | O que EXIGE validação humana, jurídica e operacional externa |
|---|---|
| Inspeciona schemas, rotas, SDKs, cookies, permissões mobile e IaC para mapear fluxos reais de dados | Comprovar contratos/DPAs efetivamente assinados fora do Git e práticas reais de fornecedores |
| Implementa código executável e testado (ledger de eventos de consentimento, rotas DSAR, criptografia de campos, *hash chain* serializada) | Auditar processos humanos internos, treinamento de equipes, atendimento informal e cultura operacional |
| Estrutura rascunhos técnicos vivos em `.lgpd/` (ROPA, RIPD, LIA, runbook de incidente, minuta de política) | Validar escolhas de base legal, balanceamento de legítimo interesse, retenção setorial e textos públicos com o Encarregado e o jurídico |
| Sinaliza configurações de risco e diferencia exigência legal expressa de boa prática de engenharia | Verificar IAM, segredos, backups e redes diretamente no ambiente de produção em nuvem |

---

## 🧭 Quando usar

| Cenário | Pipeline | Comportamento inicial |
|---|---|---|
| **Incidente de segurança ativo ou suspeito** | **Pipeline D (Fast-Path)** | Aciona contenção, preservação de evidências e registro `T+0` **imediatamente**, sem aguardar discovery geral (3 dias úteis — Res. 15/2024) |
| **Projeto greenfield** (*privacy-by-design*) | **Pipeline A** | Mapa preliminar → base legal → Encarregado/canal ATPP → fornecedores/transferências → controles técnicos → ROPA/RIPD/Política |
| **Sistema legado em produção** | **Pipeline B** | Discovery reverso do código → matriz de gaps priorizada (P0/P1/P2) → retrofit incremental |
| **Codebase híbrida** (legado + features novas) | **Pipeline C** | Diagnóstico do legado até fornecedores + controles completos nas novas features |

---

## 📦 Instalação

Segue o padrão aberto **Agent Skills** ([agentskills.io](https://agentskills.io)) com suporte nativo a 5 agentes:

### Claude Code
```text
/plugin marketplace add goul4rt/lgpd-skills
/plugin install lgpd-skills@lgpd-skills
```

### Codex (CLI / App)
```bash
codex plugin marketplace add goul4rt/lgpd-skills
codex plugin add lgpd-skills@lgpd-skills
```

### Gemini CLI
```bash
gemini extensions install https://github.com/goul4rt/lgpd-skills
```

### Cursor
Rode `/add-plugin` no editor e informe `https://github.com/goul4rt/lgpd-skills`.

### OpenCode
Adicione ao `opencode.json` (detalhes em [`.opencode/INSTALL.md`](./.opencode/INSTALL.md)):
```json
{
  "plugin": ["lgpd-skills@git+https://github.com/goul4rt/lgpd-skills.git"]
}
```
> **Nota OpenCode:** ative explicitamente via ferramenta `skill` (ex.: *"use a skill lgpd-audit"*).

### Instalação manual
```bash
git clone https://github.com/goul4rt/lgpd-skills.git /tmp/lgpd-skills
cp -r /tmp/lgpd-skills/skills/lgpd-* ~/.claude/skills/
rm -rf /tmp/lgpd-skills
```

---

## 🚀 Como usar

### Diagnóstico e governança estruturada
```text
Você: faça um diagnóstico de privacidade e LGPD deste projeto

Agente: [ativa lgpd-audit]
  → Pergunta cenário (A Greenfield / B Legacy / C Híbrido) e enquadramento ATPP (Res. 2/2022)
  → [L1] lgpd-legacy-retrofit: inspeciona schemas, rotas, SDKs, cookies e produz .lgpd/discovery.md + .lgpd/gaps.md
  → ⏸ CHECKPOINT — aguarda validação antes de avançar
  → [L2] lgpd-data-mapping → [L3] lgpd-legal-basis → [L4] lgpd-dpo-encarregado → ... → ROPA / RIPD / Política
```

### Incidente ativo (acionamento imediato)
```text
Você: descobrimos um endpoint expondo CPFs e e-mails de clientes agora

Agente: [ativa lgpd-audit → Fast-Path Pipeline D → lgpd-incident-response emergencial]
  → Registra T+0, guia contenção e preservação forense imediata, avalia Art. 5º da Res. 15/2024
```

---

## 🗂️ As 19 skills

```text
lgpd-audit (maestro — triagem imediata de incidente + pipelines A/B/C/D)
│
├── lgpd-data-mapping           Inventário de fluxos, schemas, cookies, SDKs, telemetria e papéis jurídicos
├── lgpd-legal-basis            Base legal por atividade (Arts. 7º/11), LIA e Enunciado ANPD 1/2023 (menores)
├── lgpd-dpo-encarregado        Designação Res. 18/2024 OU dispensa ATPP baixo risco + canal (Res. 2/2022 Art. 11)
├── lgpd-ropa                   Registro de Operações (Art. 37) — modelo completo ou simplificado ATPP
├── lgpd-ripd                   Relatório de Impacto (Art. 38) — teste cumulativo, LINDDUN e riscos de IA
├── lgpd-consent-schema         Ledger Prisma orientado a eventos (GRANTED/REVOKED/SUPERSEDED/EXPIRED) + triggers SQL
├── lgpd-dsar                   Direitos do titular (Arts. 18-20) — SLAs padrão vs. ATPP, representantes e canais
├── lgpd-privacy-policy         Política Art. 9º consolidada a partir do ROPA + CHECKPOINT jurídico
├── lgpd-incident-response      Res. 15/2024 — contenção T+0, 3d/6d úteis, 12 itens ANPD + registro de 5 anos
├── lgpd-vendor-audit           Classificação Operador vs. Controlador Independente/Conjunto + tiering de risco
├── lgpd-dpa                    Checklist contratual de 12 boas práticas (Art. 39 e Art. 42, § 1º, I)
├── lgpd-international-transfer Adequação UE/EEE (Res. 32/2026) + Cláusulas-Padrão BR (Res. 19/2024 Anexo II)
├── lgpd-audit-logging          Hash chain serializada (advisory lock + seq), triggers e âncora externa WORM
├── lgpd-encryption-keys        TLS, storage encryption vs. TDE, AES-256-GCM versionado, blind index HMAC e KMS
├── lgpd-anonymization          Pseudonimização com vault segregado, k-anonymity, l-diversity e testes de ataque
├── lgpd-retention-erasure      Prazos legais com documento/marco inicial, tombstones de backup e outbox Art. 18 § 6º
├── lgpd-eca-digital-minors     Lei 15.211/2025 + Dec. 12.880/2026 + Guia ANPD TI out/2026 (modulado por papel/risco)
└── lgpd-legacy-retrofit        Discovery reverso de código + matriz priorizada (técnico vs. organizacional)
```

---

## 📂 Living artifacts em `.lgpd/`

Todos os artefatos produzidos ficam versionados no repositório do projeto auditado:

```text
.lgpd/
├── STATUS.md              ← progresso, enquadramento ATPP/padrão e fronteiras da análise
├── discovery.md           ← evidências técnicas levantadas no código
├── data-map.md            ← atividades, cookies/SDKs e papel jurídico de cada terceiro
├── legal-basis.md         ← bases legais + avaliação do melhor interesse (menores)
├── lia/                   ← Legitimate Interest Assessments (Art. 7º, IX + Art. 10)
├── encarregado.md         ← designação Res. 18/2024 ou canal obrigatório ATPP
├── ROPA.md                ← registro consolidado (Art. 37)
├── RIPD/                  ← relatórios de impacto (alto risco cumulativo ou preventivos)
├── consent/               ← schema e especificação do ledger de eventos
├── dsar/                  ← workflow operacional + rotas
├── security/              ← criptografia, chaves, anonimização e trilha de auditoria
├── retention.md           ← prazos legais, marcos iniciais, backups e propagação
├── incidents/             ← runbook + registro interno obrigatório de 5 anos (Res. 15/2024 Art. 10)
├── policies/              ← minutas e versões históricas da política de privacidade
├── vendors/               ← fichas de due diligence e DPAs
├── transfers/             ← avaliações de transferência internacional (Res. 32/2026 e Res. 19/2024)
├── eca-digital.md         ← aderência modulada à Lei 15.211/2025 e Dec. 12.880/2026
└── gaps.md                ← plano de remediação separando código e governança externa
```

---

## 📚 Cobertura normativa (revisão nov/2026)

Referência consolidada em [`skills/lgpd-audit/references/normative-reference.md`](./skills/lgpd-audit/references/normative-reference.md):

- **Lei nº 13.709/2018 (LGPD)**, incluindo **Lei nº 15.352/2026** (ANPD como agência reguladora autônoma)
- **Resolução CD/ANPD nº 2/2022** — Agentes de Tratamento de Pequeno Porte (teste cumulativo multifatorial de alto risco no Art. 4º, dispensa de Encarregado com canal obrigatório no Art. 11, declaração simplificada em 15 dias e prazos em dobro no Art. 14)
- **Enunciado CD/ANPD nº 1/2023** — Aplicabilidade das bases dos Arts. 7º e 11 a crianças e adolescentes sob prevalência do melhor interesse
- **Resolução CD/ANPD nº 4/2023** — Dosimetria e aplicação de sanções administrativas
- **Resolução CD/ANPD nº 15/2024** — Comunicação de Incidentes de Segurança (3 dias úteis; registro interno por 5 anos no Art. 10)
- **Resolução CD/ANPD nº 18/2024** — Regulamento do Encarregado pelo Tratamento de Dados Pessoais
- **Resolução CD/ANPD nº 19/2024** — Transferência Internacional e Cláusulas-Padrão Contratuais brasileiras
- **Resoluções CD/ANPD nº 30 e 31/2025** — Mapa de Temas Prioritários (2026–2027) e Agenda Regulatória (2025–2026)
- **Resolução CD/ANPD nº 32/2026 (26/01/2026)** — Decisão de Adequação reconhecendo União Europeia e EEE (Islândia, Liechtenstein e Noruega)
- **Deliberação CD/ANPD de setembro/2026 (Voto nº 11/2025/DIR-MW)** — Arquivamento da minuta isolada do Guia de Alto Risco para consolidação futura na regulamentação de RIPD
- **Lei nº 15.211/2025 (ECA Digital)**, **Decreto nº 12.880/2026** e **Guia Orientativo da ANPD para Fornecedores de Produtos ou Serviços de TI (28/10/2026)**

---

## 🧪 Qualidade e testes automatizados

O repositório conta com validação estática, checagem de tipos, validação de schemas Prisma, regressão normativa e testes de cenários executados via GitHub Actions:

```bash
npm install
npm run check   # frontmatters + links/assets + manifests + regressão normativa + tsc + prisma validate + testes unitários
```

Cobertura automatizada:
- Frontmatters YAML, limite de tamanho de `description` e integridade de links/assets das 19 skills;
- Consistência de versões e carregamento dos manifests nos 5 agentes suportados;
- Validação real de schemas Prisma (`prisma validate`) e extrator `extract-prisma-annotations.sh`;
- Compilação estrita TypeScript (`tsc --noEmit --strict`) das implementações de referência;
- Testes de cenários: linhagem e ordenação do *consent ledger*, concorrência paralela e detecção de adulteração na *hash chain*, rotação de chaves e *blind index* na criptografia Prisma, cálculo de SLAs DSAR (padrão vs. ATPP) e regras etárias de menores.

---

## ⚠️ Disclaimer jurídico

**Este projeto é uma ferramenta de engenharia de privacidade e não constitui aconselhamento ou certificação jurídica.** Decisões sobre enquadramento de bases legais, comunicação de incidentes à ANPD, celebração de contratos/DPAs, avaliação de risco residual e publicação de políticas exigem validação pelo **Encarregado (DPO)** e por **advogado(a) especializado(a) em proteção de dados**.

---

## 🤝 Contribuindo

Veja [CONTRIBUTING.md](./CONTRIBUTING.md) para diretrizes de precisão normativa, padrões de código executável e processo de atualização regulatória.

## 📄 Licença

[MIT](./LICENSE) — construído por [goul4rt](https://github.com/goul4rt).
