# Project Types Reference

> Documentation patterns by project category.
> Templates adapt to project type for relevant content.

## Type Detection

```bash
#!/bin/bash
# Detect project type based on file patterns

detect_project_type() {
    local type="unknown"
    local confidence=0

    # CLI Tool (Go)
    if [[ -f go.mod ]] && [[ -d cmd ]]; then
        type="cli-go"
        confidence=90

    # CLI Tool (Python)
    elif [[ -f pyproject.toml ]] && grep -q "scripts" pyproject.toml 2>/dev/null; then
        type="cli-python"
        confidence=85

    # Kubernetes Operator
    elif [[ -f PROJECT ]] || [[ -d config/crd ]] || [[ -f Makefile ]] && grep -q "controller-gen" Makefile 2>/dev/null; then
        type="operator"
        confidence=95

    # Helm Chart
    elif [[ -f Chart.yaml ]]; then
        type="helm"
        confidence=100

    # Go Library
    elif [[ -f go.mod ]] && [[ ! -d cmd ]]; then
        type="library-go"
        confidence=80

    # Python Library
    elif [[ -f pyproject.toml ]] || [[ -f setup.py ]]; then
        type="library-python"
        confidence=75

    # Node.js
    elif [[ -f package.json ]]; then
        if grep -q '"bin"' package.json 2>/dev/null; then
            type="cli-node"
            confidence=85
        else
            type="library-node"
            confidence=75
        fi

    # Rust
    elif [[ -f Cargo.toml ]]; then
        if [[ -d src/bin ]] || grep -q '^\[\[bin\]\]' Cargo.toml 2>/dev/null; then
            type="cli-rust"
            confidence=85
        else
            type="library-rust"
            confidence=80
        fi

    # Documentation/Informational
    elif [[ -d docs ]] && [[ $(find . -maxdepth 1 -name "*.md" | wc -l) -gt 5 ]]; then
        type="docs"
        confidence=70
    fi

    echo "$type:$confidence"
}
```

---

## Type: cli-go

**Go CLI tools (like beads, gastown)**

### Detection Signals
- `go.mod` present
- `cmd/` directory with main packages
- Often has `internal/` for private packages

### Recommended Documentation

| File | Priority | Content Focus |
|------|----------|---------------|
| `README.md` | Required | Installation (brew, go install), quick start |
| `docs/CLI_REFERENCE.md` | High | All commands with flags |
| `docs/QUICKSTART.md` | High | First-run experience |
| `docs/CONFIG.md` | Medium | Config files, env vars |
| `docs/TROUBLESHOOTING.md` | Medium | Common errors, fixes |
| `examples/` | Medium | Usage examples |

### README Template Key Sections

```markdown
## Installation

```bash
# Homebrew (recommended)
brew install <name>

# Go install
go install <module>/cmd/<name>@latest

# From source
git clone <repo>
cd <repo>
go build -o <name> ./cmd/<name>
```

## Quick Start

```bash
<name> init
<name> <primary-command>
```

## Commands

| Command | Description |
|---------|-------------|
| `init` | Initialize configuration |
| `<cmd>` | Primary operation |
| `help` | Show help |
```

---

## Type: operator

**Kubernetes Operators (kubebuilder, operator-sdk)**

### Detection Signals
- `PROJECT` file (kubebuilder marker)
- `config/crd/` directory
- `Makefile` with controller-gen references
- `api/` or `apis/` directory with types

### Recommended Documentation

| File | Priority | Content Focus |
|------|----------|---------------|
| `README.md` | Required | What it manages, quick install |
| `docs/ARCHITECTURE.md` | High | Controllers, reconciliation |
| `docs/CONFIG.md` | High | CRD spec fields |
| `SECURITY.md` | High | RBAC, pod security |
| `docs/TROUBLESHOOTING.md` | Medium | Common issues |

### README Template Key Sections

```markdown
## Installation

```bash
kubectl apply -f https://github.com/<owner>/<repo>/releases/latest/download/install.yaml
```

Or with Helm:
```bash
helm install <name> <repo>/<chart>
```

## CRDs

| Kind | API Version | Description |
|------|-------------|-------------|
| `<Kind>` | `<group>/<version>` | Manages... |

## Quick Start

```yaml
apiVersion: <group>/<version>
kind: <Kind>
metadata:
  name: example
spec:
  # minimal spec
```

## RBAC Requirements

The operator requires the following permissions:
- `<resource>`: create, get, list, watch, update, delete
```

### SECURITY.md Focus

```markdown
## Security Considerations

- **Pod Security:** Runs with restricted security context
- **RBAC:** Minimal permissions following least-privilege
- **Secrets:** Never logged, stored encrypted at rest
- **Network:** Egress to API server only
```

---

## Type: helm

**Helm Charts**

### Detection Signals
- `Chart.yaml` present
- `values.yaml` present
- `templates/` directory

### Recommended Documentation

| File | Priority | Content Focus |
|------|----------|---------------|
| `README.md` | Required | Installation, basic values |
| `docs/VALUES.md` | High | All values documented |
| `docs/UPGRADING.md` | Medium | Version migration |

### README Template Key Sections

```markdown
## Installation

```bash
helm repo add <repo> <url>
helm install <release> <repo>/<chart>
```

## Configuration

| Parameter | Description | Default |
|-----------|-------------|---------|
| `image.repository` | Image name | `<default>` |
| `image.tag` | Image tag | `latest` |
| `replicas` | Pod replicas | `1` |

See `values.yaml` for all options.

## Upgrading

```bash
helm upgrade <release> <repo>/<chart>
```
```

---

## Type: library-go

**Go Libraries**

### Detection Signals
- `go.mod` present
- No `cmd/` directory
- Public package exports

### Recommended Documentation

| File | Priority | Content Focus |
|------|----------|---------------|
| `README.md` | Required | Installation, basic usage |
| `docs/API.md` | High | Public API reference |
| `examples/` | High | Usage patterns |

### README Template Key Sections

```markdown
## Installation

```bash
go get <module>
```

## Usage

```go
import "<module>"

func main() {
    client := pkg.New()
    result, err := client.DoSomething()
}
```

## API

See [pkg.go.dev](https://pkg.go.dev/<module>) for complete API documentation.
```

---

## Type: library-python

**Python Libraries**

### Detection Signals
- `pyproject.toml` or `setup.py`
- `src/` or package directory
- No CLI entry points

### Recommended Documentation

| File | Priority | Content Focus |
|------|----------|---------------|
| `README.md` | Required | Installation, basic usage |
| `docs/API.md` | High | Public API reference |
| `examples/` | High | Usage notebooks/scripts |

### README Template Key Sections

```markdown
## Installation

```bash
pip install <package>
# or
uv pip install <package>
```

## Usage

```python
from <package> import Client

client = Client()
result = client.do_something()
```

## API Documentation

See your hosted API documentation URL for complete API reference.
```

---

## Type: cli-python

**Python CLI Tools**

### Detection Signals
- `pyproject.toml` with `[project.scripts]`
- Click, Typer, or argparse usage
- Entry point defined

### Recommended Documentation

Similar to cli-go but with Python installation methods:

```markdown
## Installation

```bash
# pip
pip install <package>

# pipx (recommended for CLI tools)
pipx install <package>

# uv
uv tool install <package>
```
```

---

## Type: docs

**Documentation-Only Repositories**

### Detection Signals
- Heavy markdown content
- `docs/` directory dominant
- Minimal code

### Recommended Documentation

| File | Priority | Content Focus |
|------|----------|---------------|
| `README.md` | Required | Navigation, purpose |
| `CONTRIBUTING.md` | High | How to contribute docs |
| `docs/index.md` | High | Main entry point |

---

## Language Detection

```bash
#!/bin/bash
# Detect languages in project

detect_languages() {
    local langs=()

    [[ -f go.mod ]] && langs+=("go")
    [[ -f pyproject.toml ]] || [[ -f setup.py ]] && langs+=("python")
    [[ -f package.json ]] && langs+=("javascript")
    [[ -f Cargo.toml ]] && langs+=("rust")
    [[ -f Makefile ]] && langs+=("make")
    [[ $(find . -name "*.sh" -maxdepth 2 | wc -l) -gt 0 ]] && langs+=("shell")
    [[ -f Dockerfile ]] && langs+=("docker")
    [[ -f Chart.yaml ]] && langs+=("helm")

    echo "${langs[*]}"
}
```

---

## Command Extraction

For CLI tools, extract commands for documentation:

### Go (cobra)

```bash
# Find cobra commands
grep -r "func.*Command\(\)" cmd/ --include="*.go" | \
    sed 's/.*func \(.*\)Command.*/\1/'
```

### Python (click/typer)

```bash
# Find click commands
grep -r "@click.command\|@app.command" --include="*.py" | \
    sed 's/.*def \([a-z_]*\).*/\1/'
```

---

## Test Command Detection

```bash
detect_test_command() {
    if [[ -f go.mod ]]; then
        echo "go test ./..."
    elif [[ -f pyproject.toml ]]; then
        if grep -q "pytest" pyproject.toml; then
            echo "pytest"
        else
            echo "python -m pytest"
        fi
    elif [[ -f package.json ]]; then
        echo "npm test"
    elif [[ -f Cargo.toml ]]; then
        echo "cargo test"
    elif [[ -f Makefile ]] && grep -q "^test:" Makefile; then
        echo "make test"
    else
        echo "<TEST_COMMAND>"
    fi
}
```
