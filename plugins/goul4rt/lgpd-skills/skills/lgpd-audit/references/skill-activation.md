# Ativação de sub-skills por agente

O maestro `lgpd-audit` delega o trabalho **nomeando** sub-skills (ex.: `lgpd-legal-basis`,
`lgpd-data-mapping`). O mecanismo de ativação muda conforme o agente que está rodando.
As skills em si são idênticas — só a forma de ativá-las difere.

| Agente | Como ativar uma sub-skill pelo nome | Dispara sozinha pela descrição? |
|---|---|---|
| Claude Code | Ferramenta `Skill` (ou ativação automática) | Sim |
| Codex (CLI/App) | Progressive disclosure — o modelo carrega o SKILL.md ao decidir usar | Sim |
| Gemini CLI | Ferramenta nativa `activate_skill` | Sim |
| Cursor | Ativação automática pela descrição | Sim |
| OpenCode | Ferramenta nativa `skill`, ex.: `skill({ name: "lgpd-data-mapping" })` | **Não** — chamar explicitamente |

## Implicação prática

- Em **Claude Code, Codex, Gemini e Cursor**, o fluxo descrito nos pipelines (F0 → F1 → …)
  funciona como está: ao chegar numa etapa, ative a sub-skill correspondente pelo nome.
- Em **OpenCode**, o gatilho inicial do `lgpd-audit` exige que o usuário peça
  explicitamente (ex.: "use a skill lgpd-audit"). Uma vez ativo, o maestro invoca cada
  sub-skill chamando a ferramenta `skill` com o nome correspondente, na ordem do pipeline.

Operações de arquivo (ler código, escrever em `.lgpd/`) usam as ferramentas nativas de
cada agente — nenhum mapeamento adicional é necessário.
