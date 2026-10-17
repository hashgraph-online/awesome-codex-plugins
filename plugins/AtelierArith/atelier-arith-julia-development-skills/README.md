# atelier-arith-julia-development-skills

Plugin containing Julia development skills for both **Claude Code** and **Codex**.

## Included Skills

- `installing-julia` — install the Julia runtime
- `generating-julia-package` — create Julia project environments and package layouts
- `creating-julia-app` — create Julia command-line apps with `@main` and `[apps]`
- `creating-julia-test-env` — add a Julia package test environment
- `running-julia-test` — run standard and faster local Julia test workflows

## Installation

### Claude Code

```sh
/plugin marketplace add atelierarith/atelier-arith-julia-development-skills
/plugin install aa-jl@atelier-arith-julia-development-skills
```

Session-only (no permanent install):

```sh
claude --plugin-dir /path/to/atelier-arith-julia-development-skills
# or
claude --plugin-url https://github.com/atelierarith/atelier-arith-julia-development-skills/archive/main.zip
```

### Codex

If your Codex client supports plugins, add this repository URL in the Codex
plugin settings. The manifest is at `.codex-plugin/plugin.json`.

For local development, add this repository as a local Codex plugin marketplace
entry. The Codex plugin name is `aa-jl`; it is intentionally short so namespaced
skill IDs such as `aa-jl:finding-latest-julia-version` stay under Codex's
64-character skill name limit.

```sh
git clone https://github.com/AtelierArith/atelier-arith-julia-development-skills.git ~/.codex/aa-jl
mkdir -p ~/.agents/plugins
python3 - <<'PY'
import json
from pathlib import Path

marketplace = Path.home() / ".agents" / "plugins" / "marketplace.json"
plugin_path = Path.home() / ".codex" / "aa-jl"
entry = {
    "name": "aa-jl",
    "source": {"source": "local", "path": str(plugin_path)},
    "policy": {"installation": "AVAILABLE", "authentication": "ON_INSTALL"},
    "category": "Developer Tools",
}

if marketplace.exists():
    data = json.loads(marketplace.read_text())
else:
    data = {
        "name": "local-codex-plugins",
        "interface": {"displayName": "Local Codex Plugins"},
        "plugins": [],
    }

data["plugins"] = [p for p in data.get("plugins", []) if p.get("name") != "aa-jl"]
data["plugins"].append(entry)
marketplace.write_text(json.dumps(data, indent=2) + "\n")
PY
```

Then install `aa-jl` from the local Codex plugin marketplace and restart Codex
so it reloads the skill list.

## Repository Structure

```
.
├── .claude-plugin/
│   ├── plugin.json       # Claude Code plugin manifest
│   └── marketplace.json  # Claude Code marketplace manifest (references this repo)
├── .codex-plugin/
│   └── plugin.json       # Codex plugin manifest
├── AGENTS.md
├── CLAUDE.md
├── LICENSE
├── README.md
├── plans/
└── skills/
    ├── creating-julia-app/
    │   └── SKILL.md
    ├── creating-julia-test-env/
    │   └── SKILL.md
    ├── generating-julia-package/
    │   └── SKILL.md
    ├── installing-julia/
    │   └── SKILL.md
    └── running-julia-test/
        └── SKILL.md
```

## Adding a New Skill

1. Create `skills/<skill-name>/SKILL.md` with YAML frontmatter:

   ```markdown
   ---
   name: <skill-name>
   description: Use when ...
   ---
   ```

2. Bump `version` in `.claude-plugin/plugin.json`, `.claude-plugin/marketplace.json`, and `.codex-plugin/plugin.json`.
