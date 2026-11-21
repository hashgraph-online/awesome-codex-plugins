# Template de DPA — Acordo de Tratamento de Dados Pessoais (Art. 39 LGPD)

> ⚠️ **Minuta de referência para engenharia e governança — não substitui revisão jurídica.** Este modelo organiza um **checklist contratual de boas práticas** em 12 cláusulas alinhadas aos Arts. 39, 42, 46 e 48 da LGPD (a LGPD não impõe um formulário legal fixo de 12 cláusulas, salvo para as Cláusulas-Padrão de transferência internacional da Res. CD/ANPD nº 19/2024 quando aplicáveis). Use apenas quando a contraparte atuar efetivamente como **Operador**.

---

**ACORDO DE TRATAMENTO DE DADOS PESSOAIS (DPA)**

Anexo ao Contrato Principal nº `{NUMERO_CONTRATO}`, celebrado entre:

- **CONTROLADOR**: `{RAZAO_SOCIAL_CONTROLADOR}`, CNPJ `{CNPJ}`, doravante "Controlador"; e
- **OPERADOR**: `{RAZAO_SOCIAL_OPERADOR}`, `{CNPJ_OU_REGISTRO_ESTRANGEIRO}`, doravante "Operador".

Regido pela Lei nº 13.709/2018 (LGPD) e pela regulamentação aplicável da Autoridade Nacional de Proteção de Dados (ANPD).

---

## Cláusula 1 — Qualificação das partes e papéis
O Controlador toma as decisões referentes ao tratamento de dados pessoais (finalidades e elementos essenciais). O Operador realiza o tratamento **em nome do Controlador e segundo suas instruções lícitas** (Art. 39 da LGPD), abstendo-se de tratar os dados para finalidades próprias.

## Cláusula 2 — Objeto, finalidade e escopo dos dados
O Operador tratará dados pessoais estritamente para executar os serviços descritos no Contrato Principal: `{DESCREVER FINALIDADE ESPECÍFICA}`.
- **Categorias de titulares**: `{ex.: usuários finais, colaboradores}`
- **Categorias de dados comuns**: `{ex.: nome, e-mail, IP, identificadores de sessão}`
- **Dados pessoais sensíveis (Art. 11) ou de menores (Art. 14)**: `{Não | Sim — especificar dados e salvaguardas reforçadas}`
- **Duração**: limitada à vigência do Contrato Principal, observada a Cláusula 9.

## Cláusula 3 — Instruções lícitas do Controlador (Art. 39)
O Operador tratará os dados pessoais exclusivamente conforme instruções documentadas e lícitas do Controlador. Caso obrigação legal ou regulatória aplicável exija tratamento diverso, o Operador notificará o Controlador previamente (salvo vedação legal) e informará prontamente caso entenda que determinada instrução viola a LGPD ou normas da ANPD.

## Cláusula 4 — Confidencialidade e controle de pessoal
O Operador assegura que todas as pessoas autorizadas a acessar os dados pessoais estejam vinculadas a dever legal ou contratual de confidencialidade e recebam acesso estritamente pelo princípio do menor privilégio (*need-to-know*).

## Cláusula 5 — Medidas técnicas e administrativas de segurança (Art. 46)
O Operador manterá controles técnicos e administrativos aptos a proteger os dados pessoais contra acessos não autorizados e situações acidentais ou ilícitas, detalhados no **Anexo I** (incluindo criptografia em trânsito e em armazenamento, controle de acesso autenticado, segregação lógica, registro de eventos e gestão de vulnerabilidades).

## Cláusula 6 — Subcontratação (Sub-operadores)
O Operador `{não contratará sub-operadores sem autorização prévia específica | poderá utilizar os sub-operadores listados no Anexo II, notificando alterações com antecedência mínima de X dias para eventual oposição justificada}`. O Operador imporá por contrato aos sub-operadores obrigações de proteção de dados equivalentes às deste Acordo, permanecendo responsável perante o Controlador pelos atos de seus subcontratados na execução contratual.

## Cláusula 7 — Cooperação em direitos dos titulares (Art. 18)
O Operador auxiliará tecnicamente o Controlador no atendimento tempestivo às requisições de titulares (confirmação, acesso, correção, anonimização, bloqueio, eliminação e propagação prevista no Art. 18, § 6º), encaminhando ao Controlador em até `{ex.: 2 dias úteis}` qualquer solicitação recebida diretamente do titular, sem respondê-la em mérito próprio salvo instrução expressa.

## Cláusula 8 — Incidentes de segurança (Art. 48 + Res. CD/ANPD nº 15/2024)
O Operador comunicará ao Controlador qualquer incidente de segurança confirmado ou razoavelmente suspeito que afete dados pessoais tratados sob este Acordo **sem demora injustificada e preferencialmente em até `{ex.: 24 horas}`** da ciência, fornecendo os elementos técnicos disponíveis para viabilizar a avaliação e eventual comunicação à ANPD e aos titulares no prazo regulatório (3 dias úteis pela Res. CD/ANPD nº 15/2024).

## Cláusula 9 — Término do tratamento, devolução e eliminação (Arts. 15 e 16)
Encerrado o Contrato Principal ou mediante solicitação do Controlador, o Operador devolverá ou eliminará de forma segura os dados pessoais em até `{ex.: 30 dias}` (incluindo expiração programada ou supressão controlada em backups), emitindo declaração formal de cumprimento, ressalvadas hipóteses estritas de conservação impostas por lei ou regulação aplicável ao Operador (Art. 16, I).

## Cláusula 10 — Demonstração de conformidade e auditoria
O Operador disponibilizará relatórios e certificações independentes atualizados (ex.: SOC 2 Tipo II, ISO/IEC 27001, ISO/IEC 27701) para demonstrar conformidade e, quando justificadamente necessário, permitirá auditoria documental ou técnica mediante aviso prévio de `{ex.: 15 dias}`, resguardados o sigilo comercial e a segurança de outros clientes.

## Cláusula 11 — Responsabilidade (Arts. 42 a 45 da LGPD)
A responsabilidade perante os titulares rege-se pelos Arts. 42 a 45 da LGPD — respondendo o Operador solidariamente quando descumprir as obrigações da legislação de proteção de dados ou quando não tiver seguido as instruções lícitas do Controlador (Art. 42, § 1º, I), assegurado o direito de regresso nos termos da lei e do Contrato Principal `{ajustar limites indenizatórios inter partes com o jurídico}`.

## Cláusula 12 — Transferência internacional de dados (Arts. 33–36)
Caso haja armazenamento, processamento ou acesso remoto fora do território brasileiro:
- **(a)** Se destinado exclusivamente a país ou bloco coberto por **Decisão de Adequação da ANPD** (ex.: União Europeia / EEE nos termos e limites da **Resolução CD/ANPD nº 32/2026**), a transferência fundamenta-se no **Art. 33, I da LGPD**;
- **(b)** Nos demais destinos sem decisão de adequação, as partes celebram integralmente e sem alterações as **Cláusulas-Padrão Contratuais aprovadas pela Resolução CD/ANPD nº 19/2024 (Anexo II)**, que passam a integrar o **Anexo III** deste Acordo.

---

## Anexo I — Medidas técnicas e administrativas de segurança
`{Descrever controles de criptografia, IAM/MFA, isolamento de tenants, logging, retenção de backups e testes de segurança.}`

## Anexo II — Sub-operadores autorizados
| Sub-operador | Escopo do serviço | País / Região | Mecanismo internacional (se fora do BR) |
|---|---|---|---|
| `{nome}` | `{ex.: infraestrutura cloud}` | `{ex.: Alemanha (UE) / EUA}` | `{Res. 32/2026 Adequação | Res. 19/2024 SCCs}` |

## Anexo III — Mecanismo de Transferência Internacional
`{Indicar N/A (tratamento 100% no Brasil sem acesso externo), Decisão de Adequação aplicável (Res. 32/2026) ou anexar texto integral preenchido do Anexo II da Res. CD/ANPD nº 19/2024.}`

---

**Assinaturas**

Controlador: ______________________  Data: ___/___/______
Operador:    ______________________  Data: ___/___/______
