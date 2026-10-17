---
name: mysql-query
description: Connect to MySQL and run read-only queries to inspect table data. Use when the user wants to query MySQL, show tables, view table contents, check schema, or run read-only SQL. Connection info must be provided by the user; do not read from environment or application config.
---

# MySQL 连接与查询

## 何时使用

- 用户要求查询 MySQL、查询数据库里一共有哪些表、查看某张表数据、统计条数、检查表结构
- **必须由用户提供**连接信息（host、port、user、password、database），不得从环境变量或 application.yml 读取

## 连接信息：必须由用户提供

- **禁止**从 `application.yml`、`application-*.yml`、环境变量、`.env` 等读取 MySQL 连接信息。
- 调用脚本或写代码时，**必须**使用用户本次提供的：host、port、user、password、database。
- 若用户未提供完整连接信息，应提示用户补全后再执行。

## 执行合同

### 适用前提

- 任务目标是只读查询、验数、查结构或排障取数，而不是写库或迁移。
- 用户已经在本次对话中提供了完整连接信息；若未提供完整信息，本 skill 只能停在待补充状态。

### 任务变量

- `host`、`port`、`user`、`password`、`database`：全部必须来自用户当次提供。
- `sql`：本次准备执行的只读 SQL。
- `<skill_dir>`：当前安装环境中的 `mysql-query` 技能目录，用于定位脚本。

### 变量来源

- 所有连接变量只能来自用户消息、当前任务单或上游 `/handoff` 中明确给出的数据库连接信息。
- 不允许从仓库配置、环境变量、历史默认值或示例命令中推断真实密码。
- `<skill_dir>` 为当前 skill 安装目录，由运行环境解析，不需要用户提供。
- 若 SQL 语义不明确，应先把查询目标写清楚再执行，避免误查大表。

### 执行入口

1. 先确认 SQL 是只读语句，并按需补 `LIMIT`。
2. 优先使用当前 skill 的脚本执行，除非用户明确要求别的方式。
3. 若连接信息不完整或只读边界不清晰，先停在 `待确认项`，不要私自补全。
4. 不把密码写入仓库、脚本文件或长期日志。

### 输出回落

- 查询结果应按当前任务目标回落到 `/team-execute`、`/team-review` 或 `/handoff` 的证据区，而不是只停留在终端输出。
- 若查询用于发布验证或数据核对，需在 `/team-release` 或 `/team-review` 中注明表、条件、时间点和结论。
- 用户提供的连接信息只在本次任务内使用，不进入文档存档。

## 执行查询

### 使用脚本（推荐）

使用 **python3**，依赖：`pip3 install pymysql`。路径示例：`<skill_dir>/scripts/query.py`，其中 `<skill_dir>` 为当前安装环境里的 `mysql-query` 技能目录。

**参数（均由用户提供）：**

- `--host`：MySQL 主机（必填）
- `--port`：端口（可选，默认 3306）
- `--user`：用户名（必填）
- `--password`：密码（必填）
- `--database`：数据库名（必填）
- `--sql`：SELECT 语句（必填，或通过 stdin 传入）

```bash
# 用户提供连接信息后，按下列方式调用
python3 <skill_dir>/scripts/query.py \
  --host 127.0.0.1 \
  --port 3306 \
  --user myuser \
  --password '用户提供的密码' \
  --database mydb \
  --sql "SELECT * FROM users LIMIT 10"

# 从标准输入传 SQL
echo "SELECT id, name FROM products LIMIT 5" | python3 <skill_dir>/scripts/query.py \
  --host 127.0.0.1 --port 3306 --user myuser --password 'xxx' --database mydb
```

脚本会：
- 只执行 read-only 类型的 SQL 语句（非 read-only 会报错退出）
- 将结果以表格形式打印到 stdout

### 内联代码时

若在项目内写一次性脚本，连接参数也必须来自**用户当次提供**的变量或输入，不要从 `application.yml` 或 `os.environ` 读取。

```python
import pymysql

# 使用用户提供的变量（例如从 API 入参、用户输入传入）
host = user_provided_host
port = user_provided_port
user = user_provided_user
password = user_provided_password
database = user_provided_database

conn = pymysql.connect(host=host, port=port, user=user, password=password, database=database, charset="utf8mb4")
# ...
```

## 安全与约定

- **默认只做只读**：未明确要求时不执行写操作或 DDL。
- **LIMIT**：对未知大表查询时建议加 `LIMIT`。
- **敏感信息**：不把用户提供的密码写进仓库或日志；仅在当次请求中使用。

## 常见场景

| 用户需求           | 做法 |
|--------------------|------|
| 看某张表前 N 条    | `SELECT * FROM table_name LIMIT 20` |
| 查表结构           | `DESCRIBE table_name` 或 `SHOW CREATE TABLE table_name` |
| 统计行数           | `SELECT COUNT(*) FROM table_name` |
| 按条件查           | 用 WHERE，必要时加 LIMIT |

---

## Overview

连接 MySQL 执行只读查询，支持查看表列表、表结构、表数据和聚合统计。连接信息（host/port/user/password/database）必须由用户在本次对话中提供，禁止从配置文件或环境变量读取。

本 skill **只执行只读 SQL**，不执行 INSERT / UPDATE / DELETE 等写操作。
