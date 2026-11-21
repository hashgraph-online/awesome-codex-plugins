# Checklist de Due Diligence de Fornecedores e Agentes Externos

Use uma cópia desta ficha por fornecedor externo que receba ou acesse dados pessoais e salve em `.lgpd/vendors/{vendor-slug}.md`.

---

## 1. Identificação e Papel Jurídico

```markdown
# Fornecedor: {NOME}

- **Razão social / Registro**: {...}
- **Papel jurídico nesta atividade**: {Operador (Art. 39) | Controlador Independente | Controlador Conjunto}
- **Justificativa do papel**: {ex.: processa apenas sob nossas instruções vs. define finalidades regulatórias próprias}
- **País(es) / Região configurada**: {ex.: Brasil (sa-east-1) | Alemanha (UE — Res. 32/2026) | EUA (us-east-1)}
- **Acesso remoto de suporte/sub-operadores fora do Brasil?**: {Sim/Não — onde}
- **Dados compartilhados**: {categorias} | **Sensíveis (Art. 11)?** {Sim/Não} | **Menores?** {Sim/Não}
- **Tier de risco**: {Crítico | Alto | Médio | Baixo}
- **Owner interno**: {nome} | **Última revisão**: {data} | **Próxima revisão**: {data}
```

---

## 2. Governança Contratual e Base Legal (conforme o papel)

- [ ] Há base legal mapeada para o uso/compartilhamento (`.lgpd/legal-basis.md`) e menção adequada na Política de Privacidade (Art. 9º, V)
- [ ] **Se Operador**: há instrumento contratual vinculante (DPA bilateral assinado **ou** Data Processing Addendum online aderente) cobrindo instruções lícitas, confidencialidade, segurança, incidentes e exclusão (`lgpd-dpa`)
- [ ] **Se Controlador Independente ou Conjunto**: contrato delimita finalidades legítimas de cada parte, deveres de transparência e cooperação perante titulares (Art. 42, § 1º, II)
- [ ] Vedação contratual de uso dos dados para treinamento de modelos próprios ou perfilamento comercial não autorizado

## 3. Transferência Internacional (se houver armazenamento ou acesso fora do Brasil)

- [ ] Destino verificado frente às **Decisões de Adequação da ANPD**:
  - Se **UE / EEE (Islândia, Liechtenstein, Noruega)** para atividades comerciais comuns → amparado pelo **Art. 33, I + Res. CD/ANPD nº 32/2026** (dispensa SCCs BR)
  - Se país **sem** decisão de adequação (ex.: EUA) → **Cláusulas-Padrão da Res. CD/ANPD nº 19/2024 (Anexo II)** ou outra hipótese válida do Art. 33 formalizada (`.lgpd/transfers/{vendor}.md`)
- [ ] Sub-operadores subsequentes em terceiros países mapeados e cobertos por salvaguardas equivalentes

## 4. Segurança da Informação (Art. 46 LGPD)

- [ ] Criptografia em trânsito (TLS) e criptografia de armazenamento em repouso
- [ ] Mascaramento/redação de PII configurado no cliente/SDK antes do envio (minimização — Art. 6º, III)
- [ ] Controle de acesso (RBAC/IAM), MFA e logs de auditoria disponíveis
- [ ] Evidências independentes de segurança compatíveis com o Tier (SOC 2 Tipo II, ISO/IEC 27001, ISO/IEC 27701, PCI-DSS)

## 5. Direitos do Titular, Retenção e Incidentes

- [ ] Suporta exclusão/anonimização via API ou fluxo operacional dentro do SLA e propagação do **Art. 18, § 6º**
- [ ] Prazo de retenção (TTL de logs, eventos, backups) configurável e alinhado ao `.lgpd/retention.md`
- [ ] Compromisso de notificação tempestiva de incidentes de segurança (viabilizando o prazo da Res. 15/2024)

---

## 6. Parecer da Avaliação

```markdown
## Resultado — {fornecedor}
- **Veredito**: {APROVADO | APROVADO COM RESSALVAS (ver gaps.md) | BLOQUEADO PARA PRODUÇÃO}
- **Condicionantes / Ações pendentes**: {listar}
```

> **Nota jurídica (Art. 42, § 1º, I LGPD):** o operador responde solidariamente quando descumprir a LGPD ou deixar de seguir instruções lícitas do controlador. Formalizar o papel correto, instruções técnicas claras e mecanismos válidos do Art. 33 é essencial antes de enviar dados pessoais reais para produção.
