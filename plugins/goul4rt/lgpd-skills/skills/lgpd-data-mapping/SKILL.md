---
name: lgpd-data-mapping
description: Build and maintain a canonical data inventory (mapa de dados) of all personal data processing activities, databases, APIs, cookies, pixels, mobile/web SDKs, telemetry streams, and third-party legal roles. Run FIRST before `lgpd-legal-basis`, `lgpd-ropa`, `lgpd-ripd`, and `lgpd-retention-erasure`. Produces `.lgpd/data-map.md`.
---

# Data Mapping LGPD

Inventário canônico de **todas** as atividades de tratamento de dados pessoais no projeto. Deve ser executado **antes** de `lgpd-legal-basis` (mapa preliminar → atribuição de base legal por atividade → mapa consolidado) e serve de insumo direto para ROPA (Art. 37), RIPD (Art. 38), retenção e DSAR.

## Workflow de descoberta

### Em projetos Greenfield (`Pipeline A — F1`)
1. Liste cada funcionalidade/jornada planejada que coleta, armazena, consulta, compartilha ou descarta dados relacionados a pessoa natural identificada ou identificável (Art. 5º, I).
2. Gere o **mapa preliminar** em `.lgpd/data-map.md` com finalidades concretas, atributos, agentes externos e seus papéis jurídicos; em seguida acione `lgpd-legal-basis` (`F2`) para preencher e validar as bases legais.

### Em sistemas Legados ou Híbridos (`Pipeline B — L2`)
Faça engenharia reversa sistemática no repositório:
1. ** Persistência**: schemas Prisma/SQL/NoSQL, migrations, buckets de objetos (S3/GCS/R2), filas e caches (Redis).
2. **Superfície de API e jobs**: rotas REST/GraphQL/tRPC, Server Actions, webhooks, workers e rotinas cron.
3. **Cookies, pixels e trackers web**: leitura/escrita de cookies (`httpOnly`, sessão, atribuição, marketing), `localStorage`/`sessionStorage`, Google Tag Manager, Meta/TikTok/LinkedIn pixels, scripts de replay de sessão (Hotjar, PostHog, FullStory).
4. **SDKs, eventos de produto e telemetria**: chamadas `identify`/`track` (Segment, Mixpanel, Amplitude, Firebase Analytics), APMs e error trackers (Sentry, Datadog — verificar se capturam headers, body, IP ou e-mail em breadcrumbs/logs).
5. **Coletas mobile (React Native / iOS / Android)**: permissões em `app.json`, `Info.plist` e `AndroidManifest.xml`, push tokens (Expo/FCM/APNs), identificadores de dispositivo/publicidade (IDFA/GAID), geolocalização, câmera/galeria, contatos, área de transferência (*clipboard*) e armazenamento local (`AsyncStorage` vs. `SecureStore`/Keychain).

## O que registrar por atividade de tratamento

- **ID e Nome curto** (`A001 — Autenticação de usuários`)
- **Finalidade específica, explícita e informada** (Art. 6º, I)
- **Base legal** (preenchida/validada em conjunto com `lgpd-legal-basis`)
- **Categorias de titulares**: usuários finais, visitantes, candidatos, colaboradores, representantes. **Sinalizar vulnerabilidade**: envolve **crianças (< 12)**, **adolescentes (12–17)** ou **idosos (≥ 60)**?
- **Categorias de dados**:
  - **Comuns**: identificação, contato, CPF, credenciais, financeiros, logs/IP, cookies, identificadores de dispositivo, eventos comportamentais.
  - **Sensíveis (Art. 5º, II)**: origem racial/étnica, convicção religiosa, opinião política, filiação sindical/filosófica, saúde, vida sexual, dado genético ou biométrico.
- **Origem do dado**: fornecido pelo titular, observado (cookies/telemetria/SDK), inferido (scores/perfis) ou recebido de terceiro.
- **Ativos e repositórios**: tabelas, caches, buckets, ferramentas de observabilidade.
- **Agentes externos e Papel Jurídico efetivo**:
  - Classifique **cada terceiro** como **Operador** (Art. 39), **Controlador Independente** ou **Controlador Conjunto** (nunca presuma que todo terceiro é operador!).
- **Transferência internacional**: país/região efetiva de processamento/acesso e mecanismo aplicável (`Res. 32/2026 Adequação UE/EEE` | `Res. 19/2024 SCCs` | `N/A — 100% BR sem acesso externo`).
- **Prazo e critério de retenção** (alinhado ao `lgpd-retention-erasure`).
- **Triagem de Alto Risco (Res. CD/ANPD nº 2/2022, Art. 4º)**:
  - Avaliar cumulativamente **1 critério geral** (larga escala multifatorial — número, volume, duração, frequência e alcance geográfico — **ou** impacto significativo em direitos fundamentais) **+** **1 critério específico** (IA/tecnologia emergente, vigilância pública, decisão unicamente automatizada/profiling, ou dados sensíveis/crianças/adolescentes/idosos). Se positivo → marcar para `lgpd-ripd` (ou indicar RIPD preventivo por boa prática).

## Template — `.lgpd/data-map.md`

```markdown
# Mapa de Dados Pessoais — {projeto}

**Versão**: v{N} | **Status**: {Preliminar | Consolidado} | **Data**: {data}
**Responsável técnico / Encarregado**: {nome ou canal ATPP}

## 1. Atividades de Tratamento

### A001 — {nome}

| Campo | Valor |
|---|---|
| Slug | `a001-{slug}` |
| Finalidade (Art. 6º, I) | {finalidade específica} |
| Base legal | {pendente F2 | Art. 7º, V — Execução de contrato ([detalhes](./legal-basis.md))} |
| Categorias de titulares | {ex.: usuários adultos; adolescentes 14–17 (acesso provável)} |
| Dados comuns | {ex.: nome, e-mail, hash de senha, IP de acesso} |
| Dados sensíveis (Art. 5º, II) | {Não | Sim: especificar} |
| Origem / Coleta | {formulário de cadastro + cookie httpOnly de sessão + SDK Sentry} |
| Sistemas internos | `users` e `sessions` (PostgreSQL), Redis |
| Terceiros e Papel Jurídico | AWS RDS (`sa-east-1` — **Operador**); Sentry (`us` — **Operador**); Stripe (**Operador** no checkout / **Controlador Independente** em PLD/antifraude regulatório) |
| Transferência internacional | Sim — Sentry (EUA → SCCs Res. 19/2024); ou UE (Res. 32/2026 Adequação) |
| Retenção | Conta ativa; logs de acesso a aplicação por 6 meses (Marco Civil, Art. 15) |
| Controles de segurança | TLS 1.3, criptografia de storage em repouso, RBAC, scrubbing de PII em logs |
| Alto risco (Res. 2/2022 Art. 4º)? | {Não (ausência de critério geral/específico cumulativos) | Sim → RIPD obrigatório | RIPD preventivo recomendado} |
| Owner | {@time-responsavel} |

## 2. Inventário de Cookies, SDKs e Telemetria

| Nome / Identificador | Tipo | Finalidade | Papel do Terceiro | Estritamente necessário? | Bloqueado antes do consentimento? |
|---|---|---|---|---|---|
| `better-auth.session_token` | Cookie `httpOnly` | Sessão autenticada | Próprio | Sim | N/A (execução contratual) |
| `@sentry/nextjs` | SDK Web/Server | Rastreamento de erros | Operador | Não (legítimo interesse c/ scrubbing) | PII redigida (`sendDefaultPii: false`) |
| `_fbp` / Pixel | Tracker terceiros | Atribuição de marketing | Controlador Conjunto / Operador | Não (exige consentimento; proibido p/ < 18 no ECA Digital) | Sim |
```

## Anotações no Prisma Schema (opcional para Greenfield/CI)

```prisma
/// @lgpd:activity=a001
/// @lgpd:purpose="autenticação e gestão de conta"
/// @lgpd:legal_basis="art_7_v"
/// @lgpd:retention="active_account_plus_mci_6m_logs"
/// @lgpd:sensitive=false
model User {
  id    String  @id @default(cuid())
  email String  @unique /// @lgpd:pii=direct
  cpf   String? /// @lgpd:pii=high @lgpd:encrypted=true
}
```

Script auxiliar para extração automática: [`assets/extract-prisma-annotations.sh`](assets/extract-prisma-annotations.sh).

## Checklist de qualidade

- [ ] Todas as tabelas/coleções com dados pessoais estão vinculadas a pelo menos uma atividade
- [ ] Cookies, pixels, SDKs mobile/web e fluxos de observabilidade/logs foram inventariados
- [ ] Cada fornecedor externo possui classificação explícita de papel (`Operador`, `Controlador Independente` ou `Controlador Conjunto`)
- [ ] Atividades com crianças/adolescentes sinalizam avaliação do melhor interesse (Enunciado 1/2023) e ECA Digital
- [ ] Avaliação de alto risco aplicou o teste cumulativo da Res. 2/2022, Art. 4º (sem atalhos numéricos fixos)

## Status update

```markdown
## F1 / L2 — Data mapping ✓
- {N} atividades de tratamento e {K} cookies/SDKs inventariados
- {S} envolvem dados sensíveis | {M} envolvem menores
- {R} sinalizadas para RIPD ({obrigatório vs. preventivo})
- Próximo passo: `lgpd-legal-basis`
```
