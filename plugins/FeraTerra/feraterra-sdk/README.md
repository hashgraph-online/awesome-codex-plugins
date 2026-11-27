<!-- mcp-name: io.github.FeraTerra/feraterra-sdk -->
# Arena Exchange — Official Headless Client SDK & MCP Gateway (`v4.9.4`)

[![FeraTerra/feraterra-sdk MCP server](https://glama.ai/mcp/servers/FeraTerra/feraterra-sdk/badges/score.svg)](https://glama.ai/mcp/servers/FeraTerra/feraterra-sdk)

Zero-dependency client connectors, `agentskills.io` / Claude / Cursor / Codex trading skill, Rust `#![no_std]` `feraterra-wire` crate, CMake C++23 HFT targets, LangChain/PydanticAI agent toolkits, and 24-tool MCP gateway for trading on **Arena Exchange** (`https://feraterra.app`) — a 100% headless computational venue with **0 bps maker fees** (maker rebates on segmented venues), cross-margined Spot/Perps/FormulaPerps/BoundedClaims/SpreadBooks, stateless `POST /order/preview` margin dry-runs, `$0`-capital atomic flash arbitrage & liquidation bounties, live Gladiator Leaderboard (`GET /leaderboard`), and non-custodial L2 `Clearinghouse` Merkle-escape solvency.

- **Apex Network Directory:** `https://feraterra.app`
- **Zero-Install Remote Streamable HTTP MCP:** `https://mcp.feraterra.app/mcp`
- **Public Base Sepolia Testnet HTTPS:** `https://testnet.feraterra.app`
- **Public Base Sepolia Testnet WebSocket:** `wss://testnet.feraterra.app/ws`
- **AI Discovery & OpenAPI 3.1:** `https://testnet.feraterra.app/llms.txt` | `https://testnet.feraterra.app/openapi.json`
- **Gladiator Leaderboard:** `https://testnet.feraterra.app/leaderboard`

## Bundle Contents (29 Files)

| Path | Purpose |
| :--- | :--- |
| `sdk/python/arena_sdk.py` | Pure Python 3 stdlib client (`ArenaHttpClient`, `ArenaWsClient`, `ArenaBinaryClient`, `ArenaItchClient`, `ArenaCcxtAdapter`, `EthWalletSigner`, `EvmJsonRpcClient`, `testnet()` presets, `get_leaderboard()` & Merkle/Ledger verifiers) |
| `sdk/python/feraterra_sdk.py` | Canonical `import feraterra_sdk` namespace plus LangChain (`create_langchain_tools()`) and PydanticAI (`create_pydantic_ai_toolset()`) agent toolkits |
| `sdk/python/arena_mcp_server.py` | Packaged MCP gateway module exposing `feraterra-mcp`, `feraterra-sdk`, `arena-mcp`, and `arena-sdk` CLI entry points |
| `include/arena_wire.hpp` | Canonical 64-byte `ArenaWireFrame` & `ArenaITCH` C++23 wire layout (`static_assert(sizeof == 64)`) |
| `include/arena_hft_client.hpp` | Header-only C++23 HFT TCP/UDP/ITCH client (`namespace arena::sdk`, `PUBLIC_TESTNET_HTTPS_URL`) |
| `CMakeLists.txt` | Root CMake 3.20+ header-only C++23 `INTERFACE` targets (`feraterra::wire`, `feraterra::hft_client`) |
| `crates/feraterra-wire/Cargo.toml` | Zero-dependency `#![no_std]` Rust 1.75+ crate manifest (`feraterra-wire` `v4.9.4`) |
| `crates/feraterra-wire/src/lib.rs` | Canonical 64-byte big-endian `ArenaWire` & `ArenaITCH` `#![no_std]` Rust HFT codec with dual SipHash-2-4 MACs |
| `skills/feraterra-trading/SKILL.md` | Portable `agentskills.io` trading skill for Claude Code, Cursor, Codex, and Antigravity (`npx skills add FeraTerra/feraterra-sdk`) |
| `.claude-plugin/plugin.json` | Claude Code plugin manifest (`feraterra` `v4.9.4`, `./skills/`) |
| `.cursor-plugin/plugin.json` | Cursor plugin manifest (`feraterra` `v4.9.4`, `./skills/`) |
| `glama.json` | Glama MCP directory ownership & schema manifest |
| `scripts/arena_mcp_server.py` | MCP JSON-RPC 2.0 `stdio` & Streamable HTTP (`POST /mcp`, `GET /mcp/health`) gateway script |
| `abi/Clearinghouse.abi.json` | L2 `Clearinghouse` ABI (`depositTraderMargin`, `claimWithdrawalVoucher`, `claimMerkleEmergencyEscape`, `depositPolicyConfig`) |
| `examples/quickstart_ccxt_and_preview.py` | Client-side AI discovery (`GET /llms.txt`, `GET /openapi.json`), EIP-191 wallet login, CCXT `camelCase` & `POST /order/preview` dry-run |
| `examples/algo_two_sided_quoter.py` | Client-side Market-Maker Protection (`MMP`) + inventory-skewed atomic two-sided quote replacement starter |
| `examples/ai_agent_zero_capital_scanner.py` | Client-side zero-capital atomic flash-arbitrage (`POST /flash_arb`) & auto-liquidation bounty scanner |
| `pyproject.toml` | Zero-dependency PEP 621 package manifest (`pip install feraterra-sdk` + optional `langchain` & `pydantic-ai` extras) |
| `uv.lock` | Deterministic `uv` lockfile (`version = 1`, `requires-python = ">=3.10"`, virtual `feraterra-sdk` `4.9.4`) |
| `server.json` | Official MCP Registry manifest (`io.github.FeraTerra/feraterra-sdk`) with `runtimeHint: "uvx"`, `ARENA_NETWORK=testnet` default & Remote Streamable HTTP MCP |
| `Dockerfile` | Minimal non-root `python:3.12-slim` container image (`ENTRYPOINT ["feraterra-mcp"]`) for Docker MCP Catalog & self-hosted deployments |
| `SECURITY.md` | Responsible vulnerability disclosure policy & client guardrail notes |
| `.github/dependabot.yml` | Weekly Dependabot security updates for SHA-pinned GitHub Actions |
| `.github/workflows/ci.yml` | SHA-pinned GitHub Actions CI workflow (Python `3.12` SDK/MCP self-tests, Rust `cargo test`, `g++ -std=c++23`, and CMake `feraterra::hft_client` smoke gate) |
| `.github/workflows/publish-pypi.yml` | SHA-pinned OIDC Trusted Publisher GitHub Actions workflow (`pypa/gh-action-pypi-publish`) |
| `.github/workflows/publish-crates.yml` | SHA-pinned `crates.io` OIDC Trusted Publisher / token release workflow (`feraterra-wire`) |
| `.gitignore` | Clean repository ignore rules for Python bytecode, CMake/Cargo artifacts (`target/`, `Cargo.lock`), venvs, and local key files |
| `README.md` | Public trader, quant & AI-agent quickstart guide |
| `LICENSE` | MIT license for public client connectors |

## Quickstart

### 1. Install Python SDK, Agent Skill & Machine-Readable AI Discovery

```bash
pip install feraterra-sdk

# Optional LangChain / PydanticAI agent framework extras:
pip install "feraterra-sdk[langchain,pydantic-ai]"

# Install the portable coding-agent skill (Claude Code, Cursor, Codex, Antigravity):
npx skills add FeraTerra/feraterra-sdk

# Launch the MCP gateway directly (via pip or uvx):
feraterra-mcp --testnet
# or:
uvx feraterra-sdk --testnet
```

For single-click MCP clients and the Official MCP Registry (`io.github.FeraTerra/feraterra-sdk`), a zero-dependency MCP Bundle (`feraterra-sdk.mcpb`) is also attached to every GitHub Release (`https://github.com/FeraTerra/feraterra-sdk/releases/download/v4.9.4/feraterra-sdk.mcpb`), or connect with **zero install** to the hosted Remote Streamable HTTP MCP endpoint at `https://mcp.feraterra.app/mcp`.

Point any LLM, autonomous agent, or HTTP client at `https://feraterra.app` (Apex Network Directory) or `https://testnet.feraterra.app` (or local `http://127.0.0.1:8088`):

- `GET /llms.txt` — Concise machine-readable protocol specification, fixed-point scales (`1 tick = $0.01`, `1 lot = 1e-4` base, `1 micro = $1e-6`), EIP-191 auth flow, and zero-capital endpoints.
- `GET /openapi.json` — Full OpenAPI `3.1.0` JSON schema for automatic tool/client generation.
- `GET /leaderboard` — Live Gladiator Leaderboard ranking active wallets (masked `0x1234...abcd`) by equity, PnL, maker BBO streak, volume, or ROI.
- `GET /faucet/status` — Base Sepolia (`chain_id=84532`) `Clearinghouse` contract address, collateral token address, and faucet limits.

### 2. One-Line Public Testnet Onboarding, Agent Toolkits (`import feraterra_sdk`) & CCXT Adapter

```python
import feraterra_sdk
from feraterra_sdk import (
    ArenaCcxtAdapter,
    ArenaHttpClient,
    EthWalletSigner,
    create_langchain_tools,
    create_pydantic_ai_toolset,
)

client = ArenaHttpClient.testnet()  # https://testnet.feraterra.app

# 1) Generate a local secp256k1 wallet & authenticate via EIP-191 (no browser or KYC)
signer = EthWalletSigner()
login = client.login_with_wallet(signer)
account_id = int(login["account_id"])

# 2) Optional: build LangChain StructuredTools or PydanticAI FunctionToolset (with [langchain,pydantic-ai] extras)
# lc_tools = create_langchain_tools(client, account_id=account_id)
# pai_toolset = create_pydantic_ai_toolset(client, account_id=account_id)

# 3) Drop-in CCXT camelCase adapter + stateless pre-trade margin/fill simulation (zero WAL mutation)
exchange = ArenaCcxtAdapter(client, account_id=account_id)
markets = exchange.loadMarkets()
print("BTC Perp   :", markets["BTC/USD:USD"]["symbol"])
print("Preview    :", exchange.previewOrder("BTC/USD:USD", "limit", "buy", "0.0100", "50000.00", {"postOnly": True}))
print("Leaderboard:", exchange.fetchLeaderboard(limit=5, sort="equity")[:3])
```

### 3. Autonomous AI Agent MCP Server (Remote Streamable HTTP & Local `stdio`)

**Zero-Install Hosted Remote Streamable HTTP MCP (`https://mcp.feraterra.app/mcp`):**

```json
{
  "mcpServers": {
    "feraterra-remote": {
      "type": "streamable-http",
      "url": "https://mcp.feraterra.app/mcp"
    }
  }
}
```

**Local Claude Desktop / Cursor / Windsurf (`mcpServers` JSON via `uvx` or `feraterra-mcp`):**

```json
{
  "mcpServers": {
    "arena-exchange": {
      "command": "uvx",
      "args": [
        "feraterra-sdk",
        "--testnet",
        "--max-order-notional-usd",
        "5000"
      ]
    }
  }
}
```

Inside the agent session, call `arena_onboard_and_deposit` (`generate_ephemeral=true`) to provision a wallet, mint testnet collateral + gas, and deposit margin in a single tool call, `arena_get_leaderboard` to check live Gladiator standings, or self-host Streamable HTTP mode for private remote agents:

```bash
feraterra-mcp --testnet --http-listen-port 8765 --http-bearer-token "$MCP_SECRET"
```

### 4. C++23 Header-Only 64-Byte HFT Wire & ArenaITCH Client

Integrate via 4-line CMake `FetchContent` (`feraterra::wire` and `feraterra::hft_client` automatically propagate `include/`, `cxx_std_23`, and Windows `ws2_32` + `bcrypt` system libraries):

```cmake
include(FetchContent)
FetchContent_Declare(feraterra GIT_REPOSITORY https://github.com/FeraTerra/feraterra-sdk.git GIT_TAG v4.9.4)
FetchContent_MakeAvailable(feraterra)
target_link_libraries(your_hft_bot PRIVATE feraterra::hft_client)
```

Or compile directly against `-Iinclude` with `-std=c++23` (when connected to direct/colocated TCP `19100`, UDP `19101`, and `ArenaITCH` L3 `19102` ports; `https://testnet.feraterra.app` exposes HTTPS REST + `wss://testnet.feraterra.app/ws` WebSockets):

```cpp
#include "arena_hft_client.hpp"
static_assert(sizeof(arena::wire::ArenaWireFrame) == 64);
```

### 5. Rust `#![no_std]` 64-Byte HFT Wire & ArenaITCH Crate (`crates/feraterra-wire`)

Add the zero-dependency `#![no_std]` Rust 1.75+ codec directly from GitHub:

```bash
cargo add feraterra-wire --git https://github.com/FeraTerra/feraterra-sdk
```

```rust
use feraterra_wire::{
    pack_wire_frame, unpack_and_verify_wire_frame, ArenaFlags, ArenaHeader, BaseOp, OrderSide,
    StpMode, TimeInForce, DEFAULT_DEV_KEY_HI64, DEFAULT_DEV_KEY_LO64,
    ORDER_AUX_FLAG_POST_ONLY_SLIDE,
};

let hdr = ArenaHeader {
    op: BaseOp::NewOrder,
    flags: ArenaFlags::new(TimeInForce::PostOnly, StpMode::CancelResting),
    market_id: 1,
    account_id: 1001,
    side: OrderSide::Bid,
    seq_lo: 1,
    price_ticks: 5_000_000,
    qty_lots: 10_000,
};
let frame = pack_wire_frame(&hdr, 42, ORDER_AUX_FLAG_POST_ONLY_SLIDE, 1, DEFAULT_DEV_KEY_LO64, DEFAULT_DEV_KEY_HI64);
let verified = unpack_and_verify_wire_frame(&frame, 1, DEFAULT_DEV_KEY_LO64, DEFAULT_DEV_KEY_HI64).unwrap();
assert_eq!(verified.header, hdr);
```

### 6. Starter Bots & Self-Tests (`examples/`)

```bash
# Offline deterministic self-tests:
python -B sdk/python/arena_sdk.py --self-test
PYTHONPATH=sdk/python python -B sdk/python/feraterra_sdk.py --self-test
python -B scripts/arena_mcp_server.py --self-test
python -B examples/quickstart_ccxt_and_preview.py --self-test
cargo test --manifest-path crates/feraterra-wire/Cargo.toml

# Live dry-run & execution against the public Base Sepolia testnet:
python examples/quickstart_ccxt_and_preview.py --testnet
python examples/quickstart_ccxt_and_preview.py --testnet --execute
python examples/algo_two_sided_quoter.py --testnet
python examples/algo_two_sided_quoter.py --testnet --live
python examples/ai_agent_zero_capital_scanner.py --testnet
python examples/ai_agent_zero_capital_scanner.py --testnet --live
```
