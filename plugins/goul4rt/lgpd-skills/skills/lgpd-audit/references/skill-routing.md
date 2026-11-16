# Roteamento de Skills Filhas

| Skill | Quando invocar | Outputs em `.lgpd/` |
|---|---|---|
| `lgpd-data-mapping` | Inventariar fluxos de dados, cookies/SDKs e papéis jurídicos dos agentes | `data-map.md` |
| `lgpd-legal-basis` | Definir base legal de cada atividade mapeada + LIA / melhor interesse | `legal-basis.md`, `lia/{slug}.md` |
| `lgpd-dpo-encarregado` | Designar/publicar Encarregado (Res. 18/2024) ou canal obrigatório ATPP (Res. 2/2022, Art. 11) | `encarregado.md` |
| `lgpd-ropa` | Consolidar Registro de Operações (Art. 37) | `ROPA.md` |
| `lgpd-ripd` | Relatório de Impacto (Art. 38) — alto risco (Res. 2/2022 Art. 4º) ou preventivo | `RIPD/ripd-{slug}.md` |
| `lgpd-consent-schema` | Modelar ledger de eventos de consentimento append-only no Prisma | `consent/schema.prisma`, `consent/spec.md` |
| `lgpd-dsar` | Implementar canais e endpoints de direitos do titular (Art. 18 + SLA padrão/ATPP) | `dsar/workflow.md`, `dsar/endpoints.md` |
| `lgpd-audit-logging` | Trilha de auditoria encadeada com serialização e proteção de escrita | `security/audit-logging.md` |
| `lgpd-encryption-keys` | Criptografia em trânsito, storage/volume, nível de coluna e KMS | `security/encryption.md` |
| `lgpd-anonymization` | Anonimização (Art. 12) e pseudonimização (Art. 13, § 4º) em analytics | `security/anonymization.md` |
| `lgpd-retention-erasure` | Regras de retenção legal, bloqueio, réplicas/backups e propagação | `retention.md` |
| `lgpd-incident-response` | Resposta emergencial ou runbook preparatório (Res. 15/2024 — 3d/6d úteis) | `incidents/runbook.md`, `incidents/log.md` |
| `lgpd-privacy-policy` | Política de privacidade conforme Art. 9º alinhada ao ROPA | `policies/privacy-policy-v{N}.md` |
| `lgpd-vendor-audit` | Classificar papel jurídico de terceiros e conduzir due diligence | `vendors/audit-{date}.md`, `vendors/{vendor}.md` |
| `lgpd-dpa` | Checklist contratual de boas práticas para operadores (Art. 39 e Art. 42) | `vendors/dpa-template.md`, `vendors/{vendor}.md` |
| `lgpd-international-transfer` | Decisões de adequação (Res. 32/2026 UE/EEE) e Cláusulas-Padrão (Res. 19/2024) | `transfers/{vendor}.md` |
| `lgpd-eca-digital-minors` | Proteção de crianças e adolescentes (Lei 15.211/2025 + Decreto 12.880/2026) | `eca-digital.md` |
| `lgpd-legacy-retrofit` | Discovery reverso e plano priorizado de remediação em código legado | `discovery.md`, `gaps.md` |

## Ordem de prioridade (se o tempo for limitado e não houver incidente ativo)

1. `lgpd-incident-response` (imediato se houver incidente ativo; preparatório logo após o básico)
2. `lgpd-data-mapping` — é impossível atribuir base legal, ROPA ou retenção sem saber quais atividades existem
3. `lgpd-legal-basis` — toda atividade mapeada precisa de hipótese legal válida nos Arts. 7º ou 11
4. `lgpd-dpo-encarregado` — define o ponto focal (ou canal obrigatório de ATPP) exigido na política, DSAR e ROPA
5. `lgpd-dsar` — atendimento aos direitos dos titulares é eixo prioritário de fiscalização da ANPD
6. `lgpd-privacy-policy` — transparência externa refletindo os fluxos reais já mapeados
7. Demais controles técnicos e contratuais conforme risco

## Dependências entre skills

- `lgpd-legal-basis` requer o inventário preliminar de atividades de `lgpd-data-mapping`
- `lgpd-ropa` requer `lgpd-data-mapping` + `lgpd-legal-basis` + `lgpd-dpo-encarregado` (ou registro de dispensa ATPP com canal de comunicação)
- `lgpd-ripd` requer `lgpd-data-mapping` + `lgpd-legal-basis` (e idealmente `lgpd-ropa`)
- `lgpd-dpa` e `lgpd-international-transfer` requerem o inventário e classificação de papéis de `lgpd-vendor-audit` / `lgpd-data-mapping`
- `lgpd-privacy-policy` deve consolidar as saídas de `lgpd-data-mapping`, `lgpd-legal-basis`, `lgpd-dpo-encarregado`, `lgpd-retention-erasure` e `lgpd-international-transfer`
- `lgpd-eca-digital-minors` impacta `lgpd-legal-basis`, `lgpd-consent-schema`, `lgpd-retention-erasure` (Art. 27, § 2º — retenção pelo Art. 15 do Marco Civil), `lgpd-ripd` (avaliação de impacto do Art. 16, parágrafo único / Decreto, Art. 47) e `lgpd-privacy-policy` quando há acesso provável ou direcionamento a menores. A **aplicabilidade** é triada já no mapeamento (F1/L2); os controles rodam antes do consent ledger
