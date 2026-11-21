---
name: lgpd-vendor-audit
description: Classify third-party privacy roles (operator, independent controller, joint controller) and conduct due diligence under LGPD Arts. 39 and 42. Use when user asks 'auditar fornecedor', 'vendor audit LGPD', 'operadores LGPD', 'devida diligência', or onboarding/reviewing external SDKs, APIs, cloud, payment, or analytics providers. Produces vendor role & tier assessments in `.lgpd/vendors/` and remediation items in `.lgpd/gaps.md`.
---

# Vendor Audit — Terceiros e Agentes de Tratamento

Avaliação técnica e contratual de todos os fornecedores, SDKs, nuvens e integrações externas que tocam dados do projeto.

## Premissas jurídicas corretas (Arts. 39 e 42 LGPD)

1. **Nem todo fornecedor é Operador**: antes de cobrar um DPA, classifique o **papel jurídico efetivo** na operação concreta (Guia Orientativo da ANPD sobre Agentes de Tratamento):
   - **Operador**: trata dados pessoais em nome do controlador e sob suas instruções (ex.: AWS RDS, Resend/SES, Sentry, Datadog).
   - **Controlador Independente (Singular)**: define finalidades e meios próprios (ex.: bancos liquidantes, bureaus antifraude independentes, adquirentes em obrigações regulatórias do BCB, redes sociais em login social para fins próprios da rede).
   - **Controlador Conjunto**: decide finalidades e elementos essenciais em conjunto com o controlador (ex.: produto co-branded com base compartilhada e governança comum).
   - **Sem acesso a dados pessoais**: bibliotecas puramente locais (ex.: `zod`, `prisma`, `better-auth` auto-hospedado sem telemetria externa) não são agentes externos de tratamento.
2. **Responsabilidade solidária condicional (Art. 42, § 1º, I)**:
   - O operador responde **solidariamente** pelos danos causados pelo tratamento **quando descumprir as obrigações da LGPD ou não seguir as instruções lícitas do controlador** (e os controladores diretamente envolvidos respondem nos termos do inciso II, observadas as excludentes do Art. 43). A diligência prévia na escolha e instrução documentada do fornecedor protege o controlador e os titulares.

## Workflow

### Passo 1: Inventário automatizado no repositório
Cruze evidências técnicas de integrações externas:
- Dependências e SDKs (`package.json`, `Podfile`, `app.json`, `requirements.txt`, `go.mod`)
- Variáveis de ambiente (`.env.example`, secrets configurados em CI/IaC)
- Clientes HTTP, webhooks de entrada/saída, CSP/`connect-src`, tags/pixels frontend
- Infraestrutura declarada (Terraform, Docker, regiões cloud, DNS/CDN)

### Passo 2: Classificação de papel e Tiering de risco

| Tier | Critério técnico | Exemplos típicos | Revisão recomendada |
|---|---|---|---|
| **Crítico** | Trata dados sensíveis (Art. 11), dados de menores ou grande volume de PII essencial | Banco gerenciado principal, IdP externo, provedor de antifraude/KYC, LLM processando PII | Semestral |
| **Alto** | Trata PII comum de forma contínua | Pagamentos, e-mail/SMS transacional, observabilidade/APM, suporte/CRM | Anual |
| **Médio** | Trata identificadores pseudonimizados ou metadados técnicos limitados | Analytics de produto pseudonimizada, push notifications | Anual |
| **Baixo** | Sem PII (ou tráfego estritamente técnico efêmero em borda) | Pacotes locais sem rede, CDN de assets estáticos públicos | Sob mudança arquitetural |

### Passo 3: Due diligence proporcional ao papel e ao Tier

Use [`assets/vendor-checklist.md`](assets/vendor-checklist.md). Distinga os instrumentos exigidos:
- **Se Operador com PII**: verificar DPA vigente (contrato assinado **ou** Data Processing Addendum público vinculante nos termos enterprise do provedor) + controles de segurança (Art. 46) + capacidade de exclusão/propagação (Art. 18, § 6º).
- **Se Controlador Independente / Conjunto**: verificar base legal do compartilhamento (`lgpd-legal-basis`), transparência na Política de Privacidade (Art. 9º, V) e cláusulas contratuais de delimitação de responsabilidades (não impor modelo de subordinação de operador onde não cabe).
- **Se houver Transferência Internacional**: consultar primeiro se há **Decisão de Adequação da ANPD** (ex.: UE/EEE pela **Res. CD/ANPD nº 32/2026**); caso contrário, verificar **Cláusulas-Padrão da Res. 19/2024 (Anexo II)** ou outra hipótese aplicável do Art. 33 (`lgpd-international-transfer`).

### Passo 4: Critérios de bloqueio vs. remediação com ressalvas

- **Bloqueio para produção com dados pessoais reais**:
  - Operador tratando dados pessoais sem vínculo contratual de confidencialidade/segurança/instruções (nem DPA assinado, nem adendo público vinculante equivalente);
  - Transferência internacional de dados pessoais para jurisdição sem decisão de adequação **e** sem mecanismo válido do Art. 33 da LGPD;
  - SDK/fornecedor que reutiliza dados de crianças/adolescentes para perfilamento publicitário (vedado pelos Arts. 22 e 26 do ECA Digital).
- **Ressalva gerenciada (plano de ação em `.lgpd/gaps.md`)**:
  - Provedor global com DPA padrão sólido (SOC 2 / ISO 27001), mas pendente de formalização específica do adendo brasileiro ou ajuste de região (ex.: migrar instância de `us` para `sa-east-1` ou `eu` coberta pela Res. 32/2026).

## Status update

```markdown
## F4a / L5a — Vendor audit ✓
- {N} integrações externas inventariadas
- Papéis: {O} operadores, {CI} controladores independentes, {CC} controladores conjuntos
- Tiers: {Crit} críticos, {Alto} altos, {Med} médios, {Baixo} baixos
- Fichas salvas em `.lgpd/vendors/` e pendências em `.lgpd/gaps.md`
```
