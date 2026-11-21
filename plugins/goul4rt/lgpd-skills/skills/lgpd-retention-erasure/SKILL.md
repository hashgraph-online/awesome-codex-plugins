---
name: lgpd-retention-erasure
description: Define data retention schedules, post-contract minimization, logical blocking, backup/replica erasure strategies, and operator propagation under LGPD Arts. 15, 16, and 18 (VI and § 6). Outputs precise Brazilian statutory retention references (document, legal basis, timeframe, dies a quo) and Prisma retention/outbox schemas.
---

# Retention & Erasure (Arts. 15, 16 e 18 da LGPD)

O **Art. 15 da LGPD** impõe o término do tratamento quando a finalidade foi alcançada, os dados deixaram de ser necessários, decorreu o período de tratamento, houve comunicação/revogação pelo titular (quando cabível) ou determinação da ANPD. O **Art. 16** determina a **eliminação** após o término, autorizando a conservação **apenas** para hipóteses taxativas (incisos I a IV).

## Contextualização correta: contrato NÃO autoriza retenção indefinida de tudo

Evite a simplificação equivocada de que "existindo contrato, retém-se toda a base do usuário por 5 ou 10 anos":
1. **Durante a vigência contratual (`Art. 7º, V`)**: mantêm-se apenas os dados necessários para executar o contrato ativo.
2. **Encerrado o contrato ou solicitada a exclusão (`Arts. 15 e 16`)**:
   - Dados sem obrigação legal nem necessidade probatória específica (ex.: preferências de UI, avatar, rascunhos, histórico comportamental de recomendação, dados baseados em consentimento revogado) devem ser **eliminados ou anonimizados imediatamente**.
   - Dados sujeitos a **dever legal/regulatório específico (`Art. 16, I`)** ou estritamente indispensáveis para **exercício regular de direitos em processo (`Art. 7º, VI`)** devem sofrer **minimização de atributos e bloqueio lógico** (`Art. 5º, XIII` — vedado qualquer uso comercial, de produto ou marketing), permanecendo segregados apenas até o termo final do respectivo prazo legal.

## Tabela de referência de prazos no Brasil (especifique sempre documento + marco inicial)

> **Atenção:** prazos legais incidem sobre **documentos/registros específicos** e possuem **marcos iniciais (*dies a quo*) próprios** — nunca aplique "5 anos" ou "10 anos" indiscriminadamente a todas as tabelas do sistema. Sempre valide o setor regulado do projeto com o jurídico.

| Documento / Registro específico | Obrigação / Finalidade | Fundamento normativo | Prazo | Marco inicial da contagem (*dies a quo*) |
|---|---|---|---|---|
| Documentos fiscais, NF-e e escrituração contábil-tributária | Fiscalização e constituição de crédito tributário | CTN, Art. 173, I e Art. 195, parágrafo único (c/c Art. 174 se lançado) | **5 anos** | **1º dia do exercício seguinte** àquele em que o lançamento poderia ter sido efetuado (ou constituição definitiva, no Art. 174) |
| Registros de acesso a aplicações de internet (IP, data/hora com fuso) | Dever legal de provedores de aplicação | Lei nº 12.965/2014 (Marco Civil), Art. 15 | **6 meses** | Data de cada acesso/evento (salvo ordem policial/MP/judicial de guarda estendida — § 2º) |
| Dados associados a relatórios de conteúdo de exploração, abuso sexual, sequestro ou aliciamento de menores | Dever legal de fornecedores sujeitos ao ECA Digital | Lei nº 15.211/2025, Art. 27, §§ 2º e 3º (remete ao Art. 15 do Marco Civil) | **6 meses**, prorrogável mediante requerimento da autoridade | Data do relatório de notificação à Polícia Federal |
| Registros de conexão à internet (exclusivo para provedores de conexão/ISP) | Dever legal de provedores de conexão | Lei nº 12.965/2014 (Marco Civil), Art. 13 | **1 ano** | Data do encerramento da conexão |
| Registros trabalhistas gerais de empregados | Prescrição trabalhista | CF, Art. 7º, XXIX e CLT, Art. 11 | **5 anos** (respeitado o biênio pós-rescisão) | Exigibilidade das parcelas, observado o limite de **2 anos após a extinção do contrato** *(nota: documentos previdenciários/eSocial, PPP/SST e FGTS possuem prazos específicos mais longos — validar com jurídico trabalhista)* |
| Cadastro e transações em instituições reguladas pelo Banco Central / COAF (PLD/FTP) | Prevenção à lavagem de dinheiro (restrito a entes sujeitos à lei/regulação financeira — **não vale para qualquer e-commerce comum**) | Lei nº 9.613/1998, Art. 10, § 2º e Circular BCB nº 3.978/2020, Art. 67 | **10 anos** | **1º dia do ano seguinte** ao término do relacionamento com o cliente ou à conclusão da operação |
| Evidências estritamente probatórias em relação de consumo (fato do produto/serviço) | Exercício regular de direitos em eventual ação reparatória (`Art. 7º, VI`) | CDC, Art. 27 *(nota: reparação civil geral no CC Art. 206, § 3º, V é de **3 anos**; vícios aparentes seguem Art. 26 CDC)* | **Até 5 anos** (conforme risco/tese aplicável) | Conhecimento do dano e autoria / encerramento da relação — **reter apenas o mínimo probatório bloqueado** |
| Registro interno de incidentes de segurança com dados pessoais | Fiscalização da ANPD (comunicados ou não) | Res. CD/ANPD nº 15/2024, Art. 10 | **Mínimo de 5 anos** | Data do registro interno do incidente *(não confundir com logs gerais de DSAR)* |

## Engenharia de Eliminação: Primário, Réplicas, Backups e Operadores

Schemas de referência validados: [`assets/retention.prisma`](assets/retention.prisma).

### 1. Banco primário, réplicas de leitura, caches e índices de busca
- **Primário + Réplicas**: a deleção/anonimização no primário propaga-se por replicação streaming às réplicas em milissegundos/segundos.
- **Caches e buscadores (`Redis`, `Elasticsearch`, `Algolia`, CDNs privadas)**: invalide explicitamente chaves de sessão/perfil e índices secundários no mesmo workflow de eliminação.

### 2. Backups imutáveis (PITR / Snapshots criptografados)
Reescrever snapshots históricos imutáveis é tecnicamente inviável e perigoso para integridade de *disaster recovery*. Duas abordagens aceitas de engenharia de privacidade:
- **Abordagem A — Tombstone de Supressão Pós-Restore (`ErasureSuppressionTombstone`)**:
  - Os snapshots têm TTL curto/definido (ex.: 14 a 35 dias) e criptografia de storage;
  - Em banco/storage segregado, grava-se apenas `HMAC-SHA256(suppressionKey, subjectId)` (zero PII);
  - O playbook de *restore* de backup **obrigatoriamente executa o job de reconciliação** contra a tabela `ErasureSuppressionTombstone` **antes** de reabrir tráfego da aplicação, impedindo "ressurreição" de titulares já eliminados!
- **Abordagem B — Crypto-shredding por titular**:
  - Atributos elimináveis cifrados com DEK individual do titular envelopada no KMS;
  - Eliminar = destruir a DEK do titular, tornando qualquer cópia em backups históricos permanentemente indecifrável.

### 3. Propagação obrigatória a operadores e terceiros (`Art. 18, § 6º LGPD`)
O **Art. 18, § 6º** determina que o controlador informe **de maneira imediata** os agentes de tratamento com os quais tenha realizado uso compartilhado de dados para que repitam idêntico procedimento (salvo impossibilidade comprovada ou esforço desproporcional):
- Grave um evento na tabela `OperatorPropagationOutbox` dentro da mesma transação da exclusão/correção/revogação;
- Um worker assíncrono chama as APIs de deleção/supressão dos operadores (ex.: `Mixpanel Engage Delete`, `Customer.io Suppress`, `Stripe/Zendesk` conforme papel), com retentativas exponenciais e registro de `confirmedAt` para auditoria.

## Status update

```markdown
## F9 / L6a — Retention & Erasure ✓
- Matriz de retenção com documento, base legal, prazo e marco inicial documentada em `.lgpd/retention.md`
- Schemas `RetentionRule`, `ErasureSuppressionTombstone` e `OperatorPropagationOutbox` validados
- Reconciliação pós-restore de backup e propagação do Art. 18, § 6º configuradas
```
