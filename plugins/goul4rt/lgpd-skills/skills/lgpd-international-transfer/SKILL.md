---
name: lgpd-international-transfer
description: Assess and structure international data transfers per LGPD Arts. 33-36, Resolução CD/ANPD nº 19/2024 (Brazilian Standard Contractual Clauses), and Resolução CD/ANPD nº 32/2026 (EU/EEA adequacy decision). Use when user asks 'transferência internacional', 'AWS US LGPD', 'AWS Frankfurt UE LGPD', 'decisão de adequação', 'cláusulas-padrão', 'SCCs Brasil', 'data residency', or onboarding vendors/sub-processors outside Brazil. Outputs per-vendor transfer assessments in `.lgpd/transfers/`.
---

# Transferência Internacional de Dados

Regida pelos **Arts. 33 a 36 da LGPD**, pela **Resolução CD/ANPD nº 19/2024** (Regulamento de Transferência Internacional + Cláusulas-Padrão Contratuais no Anexo II) e pelas **decisões de adequação publicadas pela ANPD** (como a **Resolução CD/ANPD nº 32/2026** para União Europeia e EEE).

> **Atenção ao conceito de transferência:** hospedar o banco primário em `sa-east-1` (São Paulo) **não elimina** transferência internacional se operadores, equipes de suporte global (`follow-the-sun`), CDNs com terminação/logs ou sub-operadores acessarem ou replicarem dados pessoais a partir do exterior.

## Passo 1 obrigatório: consultar Decisões de Adequação vigentes (Art. 33, I)

**Antes de exigir Cláusulas-Padrão Contratuais**, verifique se o país ou organismo internacional de destino já possui **decisão de adequação** reconhecida pela ANPD:

### Decisões de adequação vigentes (atualizado até nov/2026)

1. **União Europeia e Espaço Econômico Europeu (EEE) — Resolução CD/ANPD nº 32, de 26/01/2026**:
   - **Abrangência**: todos os **Estados-membros da União Europeia**, as **instituições, órgãos e agências da UE**, e os países da EFTA integrantes do EEE (**Islândia, Liechtenstein e Noruega**).
   - **Efeito prático**: a transferência ocorre diretamente com fundamento no **Art. 33, I da LGPD**, **dispensando Cláusulas-Padrão brasileiras (Res. 19/2024)** ou BCRs para essa rota.
   - **Exceções expressas (onde a Res. 32/2026 NÃO se aplica)**: transferências realizadas exclusivamente para fins de **segurança pública, defesa nacional, segurança do Estado ou atividades de investigação e repressão de infrações penais**.
   - **Deveres remanescentes**: a dispensa de SCCs **não dispensa** (a) base legal para o tratamento/compartilhamento (Arts. 7º/11), (b) contrato/DPA conforme Art. 39 quando o destinatário atuar como operador, nem (c) transparência ao titular na política de privacidade.

*(Sempre confira https://www.gov.br/anpd/pt-br para eventuais novas decisões de adequação publicadas após novembro de 2026 — ex.: Reino Unido, Suíça, Argentina, Canadá ou outros países não estão cobertos pela Res. 32/2026).*

## Hipóteses do Art. 33 (visão completa)

```text
Destino fora do Brasil?
├── 1. Há Decisão de Adequação da ANPD cobrindo o destino e a finalidade? (Art. 33, I)
│      └── SIM (ex.: UE / Islândia / Liechtenstein / Noruega — Res. 32/2026)
│          → Transferência autorizada pelo Art. 33, I (sem SCCs BR; manter DPA Art. 39 se operador)
│
└── 2. NÃO há decisão de adequação (ex.: EUA, Reino Unido, Singapura)
       ├── Garantias contratuais de regime (Art. 33, II — regra geral recomendada pela Res. 19/2024):
       │   ├── (b) Cláusulas-Padrão Contratuais brasileiras (Res. 19/2024 Anexo II) ← caminho padrão
       │   ├── (c) Normas Corporativas Globais (BCRs) aprovadas pela ANPD (grupos econômicos)
       │   └── (a) Cláusulas contratuais específicas aprovadas pela ANPD (casos excepcionais)
       └── Hipóteses específicas / restritivas (avaliar com jurídico caso a caso):
           ├── III. Cooperação jurídica internacional entre órgãos públicos
           ├── IV. Proteção da vida ou incolumidade física
           ├── V. Autorização específica da ANPD
           ├── VI. Compromisso em acordo de cooperação internacional
           ├── VII. Execução de política pública / atribuição legal
           ├── VIII. Consentimento específico e em destaque do titular (com informação prévia sobre o risco)
           └── IX. Cumprimento de obrigação legal/regulatória, execução de contrato a pedido do titular ou exercício regular de direitos (Arts. 7º, II, V e VI)
```

## Cláusulas-Padrão Contratuais brasileiras (Res. 19/2024, Anexo II)

Quando o destino **não** é coberto por decisão de adequação e a rota escolhida é o **Art. 33, II, b**:
- Devem ser adotadas **integralmente e sem alteração de texto**, preenchendo apenas as seções editáveis (identificação das partes, papéis Controlador/Operador, descrição da transferência, dados, medidas de segurança e transferências posteriores).
- Podem ser firmadas em contrato autônomo ou como anexo/adendo a um DPA ou contrato principal (prazo de transição encerrado em agosto de 2025).
- Exigem transparência ao titular (informações em português sobre país de destino, finalidade, papel dos agentes e direitos exigíveis — Res. 19/2024, Art. 16).

## Workflow

1. Cruzar `.lgpd/data-map.md` e `.lgpd/vendors/` para listar todos os fluxos com armazenamento, processamento ou acesso remoto fora do Brasil (incluindo sub-operadores).
2. Verificar o **país/bloco de destino** e o **papel jurídico** do destinatário (Operador, Controlador Independente ou Controlador Conjunto).
3. Aplicar a árvore de decisão:
   - **UE / EEE (exceto segurança pública/defesa/penal)** → enquadrar no **Art. 33, I + Res. CD/ANPD nº 32/2026**.
   - **EUA e demais jurisdições sem decisão de adequação** → adotar **Cláusulas-Padrão da Res. 19/2024 (Anexo II)** (ou BCRs / cláusulas equivalentes reconhecidas pela ANPD nos termos da Res. 19/2024).
4. Documentar cada fluxo em `.lgpd/transfers/{vendor}.md`.
5. Refletir países/regiões e mecanismos adotados em `.lgpd/ROPA.md` e na política de privacidade (`lgpd-privacy-policy`).

## Template — `.lgpd/transfers/{vendor}.md`

```markdown
# Avaliação de Transferência Internacional — {Vendor}

- **Destinatário**: {razão social}
- **Papel jurídico na operação**: {Operador | Controlador Independente | Controlador Conjunto}
- **País / Região de tratamento**: {ex.: Irlanda (eu-west-1 — UE) | EUA (us-east-1)}
- **Acesso remoto de suporte em outros países?**: {Não | Sim — listar países de sub-operadores}
- **Finalidade específica**: {descrição}
- **Categorias de dados transferidos**: {lista}
- **Enquadramento no Art. 33 da LGPD**:
  - {Opção A: Art. 33, I — Decisão de Adequação (Res. CD/ANPD nº 32/2026 — UE/EEE)}
  - {Opção B: Art. 33, II, "b" — Cláusulas-Padrão Contratuais (Res. CD/ANPD nº 19/2024, Anexo II)}
- **Instrumento contratual associado**: {DPA Art. 39 + link | Adendo Anexo II Res. 19/2024 assinado em YYYY-MM-DD}
- **Transferências posteriores (sub-operadores)**: {ex.: atenção se operador na UE usa sub-operador nos EUA — exigir salvaguarda válida para a transferência posterior}
- **Medidas técnicas suplementares**: {criptografia em trânsito e em repouso, pseudonimização, BYOK/KMS}
- **Transparência na Política de Privacidade**: {confirmado na versão vX.Y}
- **Próxima revisão**: {data}
```

## Status update

```markdown
## F4c / L5c — Transferências internacionais ✓
- {N} fluxos internacionais mapeados
- {A} amparados por Decisão de Adequação (Res. 32/2026 — UE/EEE)
- {B} amparados por Cláusulas-Padrão brasileiras (Res. 19/2024 Anexo II)
- {X} pendentes de regularização contratual: {lista}
```
