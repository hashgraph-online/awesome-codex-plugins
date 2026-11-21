---
name: lgpd-incident-response
description: Execute the LGPD security incident response runbook (Art. 48 LGPD + Resolução CD/ANPD nº 15/2024). Trigger IMMEDIATELY in emergency mode when user reports "tivemos um incidente", "vazamento de dados", "data breach", "invadiram o banco", or "preciso comunicar a ANPD"; or run in preparatory mode during an audit pipeline. Encodes the 3-business-day deadline (6 for eligible ATPPs), the 12 mandatory ANPD items, the 7 data-subject items, and the 5-year incident log under Art. 10.
---

# Incident Response LGPD (Art. 48 + Res. CD/ANPD nº 15/2024)

Runbook operacional alinhado à **Resolução CD/ANPD nº 15/2024 (Regulamento de Comunicação de Incidente de Segurança — RCIS)** e ao **Art. 48 da LGPD**.

⚠️ **Dois modos de operação**:
1. **Modo Emergencial (prioridade absoluta)**: acionado imediatamente quando há incidente ativo ou suspeito — **não aguarde discovery geral do projeto**; registre o horário de conhecimento (`T+0`), oriente contenção + preservação forense e execute a triagem normativa.
2. **Modo Preparatório**: acionado dentro dos pipelines A/B/C para estruturar `.lgpd/incidents/runbook.md`, templates e exercício *tabletop*.

## Critério cumulativo de comunicação obrigatória (Res. 15/2024, Art. 5º)

Comunicar à ANPD **e** aos titulares quando o incidente puder acarretar **risco ou dano relevante aos titulares**, o que se caracteriza quando **concorrerem AMBOS os requisitos (A + B)**:

- **Requisito A**: potencial de afetar significativamente interesses e direitos fundamentais dos titulares (ex.: impedimento de exercício de direitos/serviços, discriminação, fraude financeira, roubo de identidade, dano moral/material ou perda de controle sobre dados); **E**
- **Requisito B — envolver pelo menos uma das 6 categorias**:
  - **I.** Dados pessoais sensíveis;
  - **II.** Dados de crianças, de adolescentes ou de idosos;
  - **III.** Dados financeiros;
  - **IV.** Dados de autenticação em sistemas (senhas, hashes fracos, tokens/chaves de sessão);
  - **V.** Dados protegidos por sigilo legal, judicial ou profissional;
  - **VI.** Dados em **larga escala** (avaliada de forma multifatorial no caso concreto — número de titulares, volume de dados, duração, frequência e extensão geográfica — sem corte numérico fixo).

> **Registro obrigatório mesmo se NÃO notificável (Art. 10 da Res. 15/2024):** o controlador deve manter registro interno de **todos** os incidentes de segurança com dados pessoais — inclusive os não comunicados à ANPD e aos titulares — pelo prazo mínimo de **5 anos**, contendo data de conhecimento, descrição, dados/titulares afetados, avaliação de risco e medidas adotadas (incluindo os motivos da ausência de comunicação, quando for o caso).

## Prazos regulatórios

| Obrigação | Prazo padrão | Regime ATPP (Res. 2/2022 c/c Res. 15/2024) |
|---|---|---|
| Comunicar à ANPD (Art. 6º) | **3 dias úteis** contados da ciência de que o incidente afetou dados pessoais | **6 dias úteis** (prazo em dobro), **SALVO** quando houver potencial comprometimento à integridade física ou moral dos titulares ou à segurança nacional/pública (hipóteses em que permanece **3 dias úteis**) |
| Comunicar aos titulares (Art. 9º) | **3 dias úteis** (mesmo marco inicial) | **6 dias úteis** (observada a mesma exceção acima) |
| Complementar comunicação preliminar (Art. 6º, § 4º) | Até **20 dias úteis** da comunicação inicial | Até **40 dias úteis** quando aplicável a dobra |
| Manter registro interno de incidentes (Art. 10) | **Mínimo de 5 anos** a contar do registro | **Mínimo de 5 anos** |

## Runbook Operacional — T+0 a Pós-Incidente

### Fase 1 — T+0h: Ciência e Abertura Imediata
- Registrar o **timestamp exato com fuso horário** do momento em que o controlador tomou conhecimento de que houve incidente afetando dados pessoais (marco inicial legal do prazo em dias úteis).
- Acionar imediatamente Encarregado, Segurança/Engenharia e Jurídico.

### Fase 2 — T+0h a T+4h: Contenção e Preservação Forense
- [ ] Isolar credenciais, rotas, instâncias ou buckets comprometidos (revogar chaves/sessões, bloquear IPs/tokens).
- [ ] **Preservar evidências antes de sobrescrever/reiniciar**: snapshots de disco/memória, logs de aplicação, WAF/CDN, CloudTrail e trilha de banco.
- [ ] Caso o incidente tenha ocorrido em **Operador**, exigir relatório técnico imediato conforme cláusula contratual.

### Fase 3 — T+4h a T+24h: Escopo e Triagem do Art. 5º (`⏸ DECISÃO HUMANA/JURÍDICA`)
- [ ] Levantar categorias exatas de dados afetados (estavam efetivamente criptografados com chave intacta e inacessível ao atacante? Documentar — isso pesa diretamente na avaliação de risco relevante).
- [ ] Estimar total de titulares afetados, **discriminando crianças, adolescentes e idosos**.
- [ ] Aplicar o teste cumulativo do **Art. 5º da Res. 15/2024** e submeter a decisão formal ao **Encarregado + Jurídico**.

### Fase 4 — Até 3 dias úteis (ou 6 dias úteis para ATPP elegível): Comunicações (`⏸ CHECKPOINT`)
- **À ANPD (12 itens obrigatórios — Art. 6º, § 2º Res. 15/2024)**: usar [`assets/notification-anpd.md`](assets/notification-anpd.md) e submeter via sistema oficial de peticionamento eletrônico da ANPD (SEI / Portal ANPD).
- **Aos titulares (7 itens obrigatórios — Art. 9º Res. 15/2024)**: usar [`assets/notification-subject.md`](assets/notification-subject.md), em linguagem simples e direta, de forma individualizada (ou divulgação pública ampla por no mínimo **3 meses** quando inviável individualizar).

### Fase 5 — Pós-Incidente e Registro de 5 anos
- [ ] Concluir investigação de causa raiz, complementar comunicação preliminar (se cabível, em até 20 dias úteis) e registrar em `.lgpd/incidents/log.md`.

## Exemplo de registro permanente — `.lgpd/incidents/log.md`

```markdown
# Registro Interno de Incidentes de Segurança (Art. 10 — Res. CD/ANPD nº 15/2024)

## INC-2026-001
- **Data/hora do incidente**: 2026-08-14T02:10:00-03:00
- **Data/hora do conhecimento da afetação a dados pessoais**: 2026-08-14T09:20:00-03:00
- **Descrição e causa principal**: exposição temporária de endpoint `/api/orders` sem verificação de ownership (IDOR)
- **Dados e titulares afetados**: nome, e-mail, endereço e histórico de pedidos de ~85.000 titulares adultos
- **Avaliação Art. 5º Res. 15/2024**: Risco relevante (fraude/engenharia social) + Larga escala multifatorial (volume elevado de atributos cadastrais/consumo e alcance nacional) → **Notificável**
- **Comunicação à ANPD**: realizada em 2026-08-18 (dentro de 3 dias úteis) — Protocolo SEI `{...}`
- **Comunicação aos titulares**: enviada individualmente por e-mail em 2026-08-18
- **Medidas técnicas adotadas**: correção de autorização em linha, revogação de sessões, testes automatizados de regressão de RBAC
- **Retenção mínima deste registro**: até 2031-08-18 (5 anos — Art. 10 Res. 15/2024)
```

## Exercício Tabletop (modo preparatório — mínimo anual)

Simule cronometrando o fluxo entre engenharia, Encarregado e jurídico para cenários como: (1) IDOR/endpoint exposto, (2) vazamento de credenciais/tokens de operador cloud, (3) exfiltração via ransomware, (4) envio acidental de PII sensível a logs/LLM externo.

## Status update

```markdown
## F11 / L10 / Pipeline D — Incident response ✓
- Modo executado: {Preparatório | Emergencial}
- Artefatos em `.lgpd/incidents/` atualizados
- Registro de 5 anos inicializado/atualizado em `.lgpd/incidents/log.md`
```
