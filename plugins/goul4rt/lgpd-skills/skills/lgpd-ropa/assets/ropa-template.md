# Registro de Operações de Tratamento de Dados Pessoais (ROPA — Art. 37 LGPD)

**Agente de Tratamento**: `{razão social}` | **CNPJ**: `{nº}` | **Enquadramento**: `{Padrão | ATPP — Res. CD/ANPD nº 2/2022}`
**Encarregado / Canal (Res. 18/2024 ou Res. 2/2022 Art. 11)**: `{nome + contato OU "ATPP baixo risco dispensado de indicação formal — canal: privacidade@..."}`
**Versão**: `v{N}` | **Data**: `{data}` | **Próxima revisão**: `{data + 6 meses}`

## Histórico de versões
- `v1.0` (`{data}`): consolidação inicial

---

## I. Operações realizadas como Controlador

### A001 — `{nome da operação}`

| Campo | Descrição |
|---|---|
| **Finalidade específica (Art. 6º, I)** | `{finalidade determinada, explícita e informada}` |
| **Hipótese legal (Arts. 7º / 11)** | `{Art. 7º/11, inciso X — ver .lgpd/legal-basis.md}` |
| **LIA vinculado (se Art. 7º, IX)** | `{N/A | .lgpd/lia/a001.md}` |
| **Categorias de titulares** | `{usuários, colaboradores, candidatos — sinalizar crianças, adolescentes ou idosos}` |
| **Dados pessoais comuns** | `{nome, e-mail, CPF, IP, identificadores de cookie/SDK}` |
| **Dados pessoais sensíveis (Art. 5º, II)** | `{nenhum | listar}` |
| **Origem dos dados** | `{titular | coleta automática (cookie/SDK) | inferido | terceiro}` |
| **Compartilhamento interno** | `{áreas/empresas do grupo}` |
| **Agentes externos e Papel Jurídico** | `{Fornecedor A (Operador); Fornecedor B (Controlador Independente)}` |
| **Transferência internacional** | `{Não | Sim — UE/EEE (Art. 33, I — Res. 32/2026) | EUA (Art. 33, II, b — Res. 19/2024)}` |
| **Período de armazenamento e marco inicial** | `{prazo + fundamento específico + marco inicial — ver .lgpd/retention.md}` |
| **Medidas de segurança (Art. 46)** | `{TLS 1.3, criptografia de volume/storage em repouso, criptografia de coluna, RBAC, MFA, logs}` |
| **Decisão unicamente automatizada (Art. 20)?** | `{Não | Sim — mecanismo de explicação/revisão}` |
| **Enquadramento de Alto Risco / RIPD** | `{Não | Sim (teste cumulativo Res. 2/2022 Art. 4º) | RIPD preventivo — .lgpd/RIPD/...}` |
| **Observações** | `{ex.: avaliação do melhor interesse p/ menores conforme Enunciado 1/2023}` |

---

## II. Operações realizadas como Operador (em nome de clientes B2B)

### O001 — `{nome do serviço prestado}`

| Campo | Descrição |
|---|---|
| **Categorias de Controladores atendidos** | `{ex.: clientes corporativos do plano SaaS}` |
| **Instrumento contratual padrão (Art. 39)** | `{DPA padrão anexo aos Termos B2B — .lgpd/vendors/customer-dpa.md}` |
| **Operações executadas sob instrução** | `{hospedagem, processamento transacional, envio de notificações}` |
| **Categorias de dados processados** | `{conforme escopo contratado pelo controlador}` |
| **Sub-operadores autorizados** | `{listar provedores de nuvem/infra + país + salvaguarda Art. 33}` |
| **Medidas de segurança aplicadas** | `{isolamento lógico por tenant, TLS, criptografia de storage, logs}` |
| **Devolução / eliminação no encerramento** | `{exportação em até X dias + expurgo definitivo após Y dias}` |

---

## III. Resumo Executivo

- **Operações como Controlador**: `{N}` | **Como Operador**: `{M}`
- **Operações em Legítimo Interesse (com LIA)**: `{L}`
- **Operações com menores (Art. 14 / ECA Digital)**: `{K}`
- **Operações com RIPD (alto risco ou preventivo)**: `{R}`
- **Transferências internacionais**: `{T}` (`{A}` por adequação Res. 32/2026; `{B}` por SCCs Res. 19/2024)
