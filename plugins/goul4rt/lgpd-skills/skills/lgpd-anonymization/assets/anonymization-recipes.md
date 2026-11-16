# Receitas de Anonimização e Pseudonimização

Receitas concretas em **SQL (PostgreSQL)** e **Python**. Escolha pela coluna "Reversível?" da tabela do `SKILL.md`: pseudonimização (reversível, continua dado pessoal) vs anonimização (irreversível, sai do escopo — Art. 12).

> ⚠️ Regra de ouro: anonimização só vale **considerando os meios técnicos razoáveis disponíveis** (Art. 5º, XI). Sempre rode os testes de re-identificação no fim deste arquivo antes de declarar um dataset anonimizado.

---

## 1. Pseudonimização

### 1.1 Tokenização determinística com HMAC + vault separado (recomendado)

A chave fica em um segredo gerenciado (KMS/Secret Manager), **fora** do banco de analytics. O mapping reverso, se necessário, vive em um vault isolado com controle de acesso próprio.

```python
import hmac, hashlib, os

# Chave vem do KMS/Secret Manager — NUNCA hardcoded, NUNCA no mesmo banco do dado
PSEUDO_KEY = os.environ["PSEUDONYM_HMAC_KEY"].encode()  # >= 32 bytes aleatórios

def pseudonymize(value: str) -> str:
    """Token determinístico: mesmo input → mesmo token (permite joins no DW)."""
    return hmac.new(PSEUDO_KEY, value.strip().lower().encode(), hashlib.sha256).hexdigest()

# pseudonymize("123.456.789-00") -> "a3f9...e1" (estável, mas inquebrável sem a chave)
```

Vault reverso (apenas se houver necessidade legítima de re-identificar):

```sql
-- Banco/Schema SEPARADO, com RBAC próprio e auditoria de acesso (ver lgpd-audit-logging)
CREATE TABLE pii_vault (
    token       text PRIMARY KEY,          -- HMAC do valor
    ciphertext  bytea NOT NULL,            -- valor original cifrado (pgcrypto/KMS)
    created_at  timestamptz DEFAULT now()
);
-- O Analytics DW guarda só `token`. A re-identificação exige acesso ao vault.
```

### 1.2 Hashing com salt — feito do jeito certo

Hash simples de campo de baixa entropia (CPF, CEP, telefone) é **reversível por força bruta** (CPF ≈ 210 milhões de combinações → segundos em GPU). Use HMAC com chave secreta (seção 1.1) ou, no mínimo, salt único por registro **sem guardar o salt junto** do dado de analytics.

```sql
-- ❌ ERRADO: reversível por brute force / rainbow table
SELECT encode(digest(cpf, 'sha256'), 'hex') FROM users;

-- ✅ CERTO: HMAC com chave secreta (pgcrypto); chave via parâmetro, não no schema
SELECT encode(hmac(cpf, current_setting('app.pseudo_key'), 'sha256'), 'hex') FROM users;
```

### 1.3 Format-Preserving (quando o formato precisa ser mantido)

Quando sistemas a jusante validam o formato (ex.: precisa "parecer" um CPF). Use uma lib de FPE (FF3-1). Não improvise com substituição de dígitos — quebra a garantia.

```python
# pip install pyffx  (exemplo didático; em produção avalie FF3-1 auditado)
import pyffx
e = pyffx.Integer(os.environ["FPE_KEY"].encode(), length=11)
token = e.encrypt(12345678900)   # mantém 11 dígitos; reversível com a chave
```

---

## 2. Anonimização

### 2.1 Generalização

```sql
-- Idade exata -> faixa etária
SELECT
  CASE
    WHEN age BETWEEN 0  AND 17 THEN '0-17'
    WHEN age BETWEEN 18 AND 24 THEN '18-24'
    WHEN age BETWEEN 25 AND 34 THEN '25-34'
    WHEN age BETWEEN 35 AND 44 THEN '35-44'
    WHEN age BETWEEN 45 AND 59 THEN '45-59'
    ELSE '60+'
  END AS faixa_etaria,
  left(cep, 5) AS regiao_cep,        -- CEP completo -> prefixo (cidade/região)
  date_trunc('month', created_at) AS mes   -- timestamp -> mês
FROM users;
```

### 2.2 Supressão

```sql
-- Remove identificadores diretos; mantém só quasi-identificadores generalizados
SELECT faixa_etaria, regiao_cep, genero, plano
FROM users_generalizados;   -- nome, cpf, email, telefone NÃO entram
```

### 2.3 Perturbação (ruído aleatório)

```python
import numpy as np
# Ruído gaussiano em métricas numéricas não-sensíveis a precisão exata
df["valor_compra"] = df["valor_compra"] + np.random.normal(0, scale=5.0, size=len(df))
```

### 2.4 k-anonymity (k ≥ 5) — verificação

Cada combinação de quasi-identificadores (QIs) deve aparecer em **≥ k** registros. Esta query lista as combinações que **violam** k=5:

```sql
-- Encontra "classes de equivalência" pequenas demais (re-identificáveis)
SELECT faixa_etaria, regiao_cep, genero, count(*) AS n
FROM users_generalizados
GROUP BY faixa_etaria, regiao_cep, genero
HAVING count(*) < 5;        -- qualquer linha aqui = risco de singling out
```

Se houver violações: generalize mais (faixas maiores, CEP→cidade) ou suprima as linhas das classes raras.

```python
# Versão Python equivalente
QIS = ["faixa_etaria", "regiao_cep", "genero"]
viol = df.groupby(QIS).size().reset_index(name="n").query("n < 5")
assert viol.empty, f"k-anonymity violada em {len(viol)} classes"
```

### 2.5 l-diversity (resistência a inferência)

k-anonymity não basta se todos numa classe têm o **mesmo** valor sensível. Exija ≥ l valores sensíveis distintos por classe:

```sql
SELECT faixa_etaria, regiao_cep, genero,
       count(DISTINCT diagnostico) AS valores_sensiveis_distintos
FROM dataset
GROUP BY faixa_etaria, regiao_cep, genero
HAVING count(DISTINCT diagnostico) < 3;   -- l = 3; linhas aqui = risco de inferência
```

### 2.6 Differential Privacy (ε pequeno) — contagens com ruído de Laplace

Para estatísticas agregadas publicadas, adicione ruído calibrado à sensibilidade:

```python
import numpy as np

def dp_count(true_count: int, epsilon: float = 0.5, sensitivity: float = 1.0) -> int:
    """Contagem com privacidade diferencial (mecanismo de Laplace)."""
    noise = np.random.laplace(loc=0.0, scale=sensitivity / epsilon)
    return max(0, round(true_count + noise))

# ε menor = mais privacidade, menos utilidade. Documente o ε usado no .lgpd/.
```

### 2.7 Date shifting consistente por titular

Preserva intervalos entre eventos do mesmo titular, mas embaralha datas absolutas:

```python
import hmac, hashlib, os, datetime as dt
def shift_days(subject_id: str) -> int:
    h = hmac.new(os.environ["DATESHIFT_KEY"].encode(), subject_id.encode(), hashlib.sha256).digest()
    return int.from_bytes(h[:2], "big") % 365 - 182   # offset estável em [-182, +182]
# nova_data = data_original + timedelta(days=shift_days(subject_id))
```

---

## 3. Pipeline de referência

```
[Postgres prod]
   └─(ETL com pseudonimização §1.1: PII -> token)→ [Analytics DW]
        └─(generalização §2.1 + supressão §2.2 + k-anonymity §2.4)→ [Views/Dashboards]
```

Token vault (§1.1) isolado, com RBAC e log de acesso próprio (ver `lgpd-audit-logging`).

---

## 4. Testes de re-identificação (OBRIGATÓRIO antes de declarar "anonimizado")

```sql
-- (a) SINGLING OUT: existe registro único pelos QIs? (= k-anonymity < 2)
SELECT faixa_etaria, regiao_cep, genero, count(*) n
FROM dataset GROUP BY 1,2,3 HAVING count(*) = 1;

-- (b) LINKAGE: junte com um dataset público/auxiliar pelas mesmas QIs e veja se casa 1:1
SELECT d.* FROM dataset d
JOIN dataset_publico p USING (faixa_etaria, regiao_cep, genero)
GROUP BY d.* HAVING count(p.*) = 1;
```

```python
# (c) INFERENCE: tente prever o atributo sensível a partir dos QIs.
#     Se um modelo simples acerta muito acima do baseline, há vazamento por inferência.
from sklearn.tree import DecisionTreeClassifier
from sklearn.model_selection import cross_val_score
score = cross_val_score(DecisionTreeClassifier(max_depth=4), X_qis, y_sensivel, cv=5).mean()
# score >> taxa da classe majoritária  => ainda é dado pessoal; generalize mais.
```

**Se qualquer teste passar (consegue isolar/ligar/inferir), o dataset ainda é dado pessoal — volte para a generalização/supressão.** Registre o resultado dos 3 testes no artefato `.lgpd/`.
