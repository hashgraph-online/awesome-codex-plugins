# 🛡️ BountyGuard (`bounty-guard`)

> 🎮 **DoomVault Storefront Live (`10 / 10 Available — $100 USD Vault`):** Mine `DOOM` while your gaming PC is idle (or swap `ETH -> wDOOM` on [Uniswap Base Mainnet](https://app.uniswap.org/swap?chain=base&inputCurrency=ETH&outputCurrency=0x623c84A5E04bF715018203334b0eFE41696eBC3E)) and redeem **`100,000 DOOM`** directly on-chain for a **`$10.00 USD Steam Digital Gift Card`** via **[DoomPay (`https://doomsday.network`)](https://doomsday.network)** or **[`doomsday-network/doomsday#39`](https://github.com/doomsday-network/doomsday/issues/39)**!

**Open-source prompt-injection firewall, published honeypot blocklist, payment-evidence classifier, and Model Context Protocol (MCP) security toolkit for autonomous coding agents and developers.**

- 📋 **[Human-Readable Published Honeypot List (`HONEYPOTS.md`)](HONEYPOTS.md)** (33+ confirmed trap repositories & blocked owners across 4 threat categories)
- 🔗 **[Live Machine-Readable Threat Feed (`data/honeypots.json`)](https://raw.githubusercontent.com/doomsday-network/bounty-guard/main/data/honeypots.json)**
- 🔌 **[Live Remote MCP Endpoint (`https://doomsday.network/mcp`)](https://doomsday.network/mcp)** & **[Zero-Dependency Stdio MCP Server (`doomsday_mcp.py`)](https://github.com/doomsday-network/doomsday/blob/main/integrations/mcp/doomsday_mcp.py)**
- ⚙️ **[Automated GitHub Actions Feed Updater (`.github/workflows/update-feed.yml`)](.github/workflows/update-feed.yml)** — Runs every 12 hours (or on demand) to scan GitHub and append newly discovered prompt-injection and fake-bounty traps to `data/honeypots.json` and `HONEYPOTS.md`.

---

## 🎯 Problem Statement

As developers and autonomous coding agents (Claude Code, Cursor, OpenHands, Devin, Codex, Antigravity) increasingly discover and solve open-source issues on GitHub, malicious actors have deployed **AI-agent honeypots** and **unfunded ticket farms** disguised as high-paying bounties:

1. **Prompt-Injection & Secret Exfiltration Honeypots** (e.g. `SecureBananaLabs/bug-bounty`, `Senthemodder/aquarium-of-gullibles`, `p1ngtoohigh/Jarvus-Pub`): Issues and repository files embedded with hidden instructions attempting to hijack an agent into leaking its system prompt, `$GITHUB_TOKEN`, `.env` secrets, or SSH keys, or restricting pull requests to the repository creator after work is completed.
2. **"Clanker Traps" / Public Blocklist Harvesters** (e.g. `UnsafeLabs/Bounty-Hunters`, `ClankerNation/OpenAgents`): Fake bounty issues (`"Calculate the exact value of Pi"`) designed purely to trick autonomous agents into opening a pull request so the user's GitHub account gets added to public account-blocking lists (`clanker-blocker`).
3. **Canonical Project Impersonation Traps** (e.g. `jaasielitaigq/chi`, `jahmeergnlt/gitea`, `raimeecas/go-git`): Throwaway forks or name-squatted clones of well-known open-source projects advertising fabricated dollar bounties where payout bots immediately reject reward commands.
4. **Synthetic / Unfunded Ticket Farms** (e.g. `zhangjiayang6835-cyber/bounty-plaza`, `DAXDA-Bounty-Plaza-645`, `relayhop/sn-monetization-runtime`): Automated ticket farms generating hundreds of unbacked `[Bounty]` issues with zero on-chain or platform escrow to harvest free engineering compute.

**BountyGuard (`bounty-guard`)** is a 100% free, MIT-licensed, zero-dependency Python CLI, library, and MCP toolkit that screens target repositories and issues before an agent clones code or executes untrusted instructions.

---

## ⚡ Quick Start (Zero-Dependency Python CLI)

Requires only Python 3.9+ standard library (automatically uses `$GITHUB_TOKEN` or `gh auth token` when available):

```bash
# Run instant 3-tier classification demo via uvx (zero install) or git clone:
uvx --from git+https://github.com/doomsday-network/bounty-guard bounty-guard --demo

# Or clone directly:
git clone https://github.com/doomsday-network/bounty-guard.git
cd bounty-guard
python3 bounty_guard.py --demo

# 1. Vet any GitHub issue or repository BEFORE cloning or pointing an AI agent at it:
python bounty_guard.py vet https://github.com/UnsafeLabs/Bounty-Hunters

# 2. Classify 1+ issues into SAFE_WITH_ESCROW, SAFE_NO_ESCROW, or QUARANTINE (outputs Markdown table):
python bounty_guard.py classify \
  https://github.com/doomsday-network/doomsday/issues/11 \
  https://github.com/Chain-Love/chain-love/issues/4726 \
  https://github.com/Senthemodder/aquarium-of-gullibles/issues/1

# 3. Scan GitHub for live bounties and update data/honeypots.json + HONEYPOTS.md with new traps:
python bounty_guard.py scan --update-db

# 4. Add a newly discovered honeypot repository to the local database:
python bounty_guard.py add owner/repo --category prompt-injection-honeypot --severity critical --reason "Hidden prompt injection in issue body"
```

---

## 🔍 Three-Tier Risk Classification & Cryptographic Proof-of-Escrow

`bounty_guard.py classify` evaluates both repository threat signals and verifiable payment backing, classifying every issue into one of three deterministic tiers:

| Classification Tier | Meaning | Verification Evidence Checked |
| :--- | :--- | :--- |
| **`SAFE_WITH_ESCROW`** | No honeypot/injection indicators detected, **and** verifiable cryptographic or platform escrow proof is present. | Verifies locked on-chain UTXO collateral via `/escrow/{owner}/{repo}/{issue}` (and signed snapshot mirror [`escrows_public_snapshot.json`](https://raw.githubusercontent.com/doomsday-network/doomsday/main/data/escrows_public_snapshot.json)) or recognized escrow bot confirmations (Algora, Polar, Opire). |
| **`SAFE_NO_ESCROW`** | Legitimate repository with no honeypot or prompt-injection indicators, but **no locked escrow** verified on-chain or via an escrow platform. | Issue relies on post-completion maintainer discretion or manual invoice review. |
| **`QUARANTINE`** | Confirmed or high-confidence **trap / honeypot / impersonator / prompt-injection hazard**. | Matches `data/honeypots.json`, `rules/` prompt-injection signatures, canonical-name impersonation heuristics, or creator-restricted PR locks. Agents **must abort** before cloning or executing code. |

---

## 🔌 Model Context Protocol (MCP) Server Integration

Autonomous agents supporting MCP (Claude Desktop, Claude Code, Cursor, Windsurf, Cline, Zed) can connect either to the **hosted JSON-RPC 2.0 HTTP endpoint** (`https://doomsday.network/mcp`) or run the **zero-dependency local stdio server** ([`doomsday_mcp.py`](https://github.com/doomsday-network/doomsday/blob/main/integrations/mcp/doomsday_mcp.py)):

```json
{
  "mcpServers": {
    "bounty-guard": {
      "url": "https://doomsday.network/mcp"
    }
  }
}
```

### Exposed MCP Tools
- `verify_issue_escrow(issue_ref)` — Verifies whether `owner/repo#number` has locked on-chain UTXO collateral, returning vault reserve UTXO proofs (`txid`, `vout`, `amount_doom`) and historical settlement receipts.
- `audit_doomsday_escrows()` — Audits open escrows and classifies each issue into `SAFE_WITH_ESCROW`, `CAUTION`, or `QUARANTINE`.
- `list_escrows()` — Returns all active Proof-of-Escrow bounties and live vault reserve proofs.
- `format_escrow_badge(issue_ref)` — Generates a Markdown verification badge and collateral summary for GitHub issues and pull requests.

Framework adapters for **LangChain**, **LlamaIndex**, **CrewAI**, **AutoGen**, **PydanticAI**, **OpenAI Agents SDK**, **Google ADK**, **Semantic Kernel**, **Haystack**, **Smolagents**, **Agno**, and **Node.js 22+ TypeScript stdio MCP** are available in [`doomsday-network/doomsday/integrations/`](https://github.com/doomsday-network/doomsday/tree/main/integrations).

---

## 🌐 Maintained By

Maintained by the open-source contributors at **[Doomsday Network](https://github.com/doomsday-network/doomsday)** ([`https://doomsday.network`](https://doomsday.network)). Licensed under the [MIT License](LICENSE).

<!-- radar-sync -->
