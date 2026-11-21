---
name: lgpd-anonymization
description: Apply anonymization (Art. 5, XI) and pseudonymization (Art. 13, §4) techniques to take data out of LGPD scope or reduce risk in analytics pipelines. Use when user asks 'anonimizar', 'pseudonimizar', 'k-anonymity', 'differential privacy', 'tokenização', 'analytics LGPD', or designing analytics/ML pipelines.
---

# Anonimização e Pseudonimização

## Diferença crítica

| | Anonimização (Art. 5º, XI) | Pseudonimização (Art. 13, § 4º) |
|---|---|---|
| Reversível? | Não, considerando meios técnicos razoáveis | Sim, com info adicional segregada |
| Status LGPD | Fora do escopo (Art. 12) | Continua sendo dado pessoal |
| Uso típico | Estatísticas públicas, datasets de pesquisa | Analytics interna, logs, redução de exposição |
| Risco residual | Baixíssimo (re-identificação) | Médio (depende da segurança da chave) |

## Técnicas

### Pseudonimização
- **Tokenização determinística**: substitui PII por token; mapping mantido em vault separado
- **Hashing com salt** (cuidado — sem salt aleatório, é reversível por força bruta para campos de baixa entropia como CPF)
- **Format-preserving encryption** quando o formato precisa ser mantido

### Anonimização
- **Generalização**: idade exata → faixa (25-34); CEP → cidade
- **Supressão**: remoção de campos identificadores
- **Perturbação**: adicionar ruído aleatório
- **k-anonymity (k ≥ 5)**: cada combinação de quasi-identificadores aparece em ≥ k registros
- **l-diversity, t-closeness**: refinamentos para resistir a ataques de inferência
- **Differential privacy (ε pequeno)**: garantia matemática contra re-identificação

## Pipeline típico de analytics

```
[Postgres prod] → ETL com pseudonimização (token PII) → [Analytics DW] → Generalização + k-anonymity → [Dashboards públicos]
```

## Anti-padrões

- ❌ "Removemos o nome" e mantemos CPF, e-mail, endereço — **não é anonimização**
- ❌ Hash de CPF sem salt único — facilmente reversível (~210 milhões de combinações)
- ❌ ID interno como "pseudônimo" se está exposto em URLs e logs — não é pseudonimização
- ❌ Agregação só por região quando dataset tem campos suficientes para inferência cruzada

## Implementação

Ver `assets/anonymization-recipes.md` para receitas concretas em SQL e Python.

## Re-identificação — teste obrigatório

Antes de declarar um dataset "anonimizado":
1. **Linkage attack**: tente combinar com dataset público
2. **Inference attack**: estime atributo sensível a partir dos outros
3. **Singling out**: existe registro único na base?

Se algum passa → dataset ainda é dado pessoal.

## Status update

```markdown
## F (legacy L6) — Anonimização ✓
- Pipelines de analytics revisados
- {N} datasets passados por pseudonimização
- {M} datasets passados por anonimização (k=5+)
- Vault de tokens isolado
- Próximo: lgpd-dsar (legacy) ou conforme pipeline
```

