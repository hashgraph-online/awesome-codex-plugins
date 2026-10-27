# Project Types Reference

> Documentation patterns by project category.
> Templates adapt to project type for relevant content.

## Type Detection

Use the type this skill's `scripts/audit-oss-docs.sh --json` reports for the
audited repository (see [OSS pack](oss-pack.md#audit-and-project-type)). The
detection signals under each type below help when it reports `unknown`; it has
no `docs` type, so a documentation-only repository reports `unknown`.

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

````markdown
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
````

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

````markdown
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
````

### SECURITY.md Focus

````markdown
## Security Considerations

- **Pod Security:** Runs with restricted security context
- **RBAC:** Minimal permissions following least-privilege
- **Secrets:** Never logged, stored encrypted at rest
- **Network:** Egress to API server only
````

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

````markdown
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
````

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

````markdown
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
````

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

````markdown
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
````

---

## Type: cli-python

**Python CLI Tools**

### Detection Signals
- `pyproject.toml` with `[project.scripts]`
- Click, Typer, or argparse usage
- Entry point defined

### Recommended Documentation

Similar to cli-go but with Python installation methods:

````markdown
## Installation

```bash
# pip
pip install <package>

# pipx (recommended for CLI tools)
pipx install <package>

# uv
uv tool install <package>
```
````

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
