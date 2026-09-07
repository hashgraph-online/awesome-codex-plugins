#!/bin/bash
# OSS Documentation Audit Script
# Usage: audit-oss-docs.sh [--json]
#
# Checks for presence of standard OSS documentation files
# and reports coverage across tiers.

set -e

JSON_OUTPUT=false
[[ "$1" == "--json" ]] && JSON_OUTPUT=true

# Colors (disabled for JSON output)
if [[ "$JSON_OUTPUT" == "false" ]]; then
    RED='\033[0;31m'
    GREEN='\033[0;32m'
    YELLOW='\033[0;33m'
    BLUE='\033[0;34m'
    NC='\033[0m' # No Color
else
    RED='' GREEN='' YELLOW='' BLUE='' NC=''
fi

# Project detection
PROJECT_NAME=$(basename "$(pwd)")
GIT_ORIGIN=$(git remote get-url origin 2>/dev/null || echo "")

# Detect project type
# Order matters: more specific types checked first
detect_type() {
    # Kubernetes Operator (kubebuilder/operator-sdk) - check BEFORE cli-go
    # because operators also have go.mod + cmd/
    if [[ -f PROJECT ]] || [[ -d config/crd ]] || [[ -d config/rbac ]]; then
        echo "operator"
    # Helm Chart
    elif [[ -f Chart.yaml ]]; then
        echo "helm"
    # Go CLI Tool
    elif [[ -f go.mod ]] && [[ -d cmd ]]; then
        echo "cli-go"
    # Python CLI Tool (has entry points)
    elif [[ -f pyproject.toml ]] && grep -q "\[project.scripts\]" pyproject.toml 2>/dev/null; then
        echo "cli-python"
    # Go Library (go.mod but no cmd/)
    elif [[ -f go.mod ]]; then
        echo "library-go"
    # Python Library
    elif [[ -f pyproject.toml ]] || [[ -f setup.py ]]; then
        echo "library-python"
    # Node.js
    elif [[ -f package.json ]]; then
        if grep -q '"bin"' package.json 2>/dev/null; then
            echo "cli-node"
        else
            echo "library-node"
        fi
    # Rust
    elif [[ -f Cargo.toml ]]; then
        if [[ -d src/bin ]] || grep -q '^\[\[bin\]\]' Cargo.toml 2>/dev/null; then
            echo "cli-rust"
        else
            echo "library-rust"
        fi
    else
        echo "unknown"
    fi
}

# Detect languages
detect_languages() {
    local langs=()
    [[ -f go.mod ]] && langs+=("go")
    [[ -f pyproject.toml ]] || [[ -f setup.py ]] && langs+=("python")
    [[ -f package.json ]] && langs+=("javascript")
    [[ -f Cargo.toml ]] && langs+=("rust")
    [[ -f Makefile ]] && langs+=("make")
    [[ -f Dockerfile ]] && langs+=("docker")
    [[ -f Chart.yaml ]] && langs+=("helm")
    echo "${langs[*]}"
}

PROJECT_TYPE=$(detect_type)
LANGUAGES=$(detect_languages)

# Tier 1: Required
check_tier1() {
    local score=0
    local total=4
    local results=()

    if [[ -f LICENSE ]]; then
        results+=("LICENSE:pass")
        ((score++))
    else
        results+=("LICENSE:fail")
    fi

    if [[ -f README.md ]]; then
        results+=("README.md:pass")
        ((score++))
    else
        results+=("README.md:fail")
    fi

    if [[ -f CONTRIBUTING.md ]]; then
        results+=("CONTRIBUTING.md:pass")
        ((score++))
    else
        results+=("CONTRIBUTING.md:fail")
    fi

    if [[ -f CODE_OF_CONDUCT.md ]]; then
        results+=("CODE_OF_CONDUCT.md:pass")
        ((score++))
    else
        results+=("CODE_OF_CONDUCT.md:fail")
    fi

    echo "$score:$total:${results[*]}"
}

# Tier 2: Standard
check_tier2() {
    local score=0
    local total=5
    local results=()

    if [[ -f SECURITY.md ]]; then
        results+=("SECURITY.md:pass")
        ((score++))
    else
        results+=("SECURITY.md:fail")
    fi

    if [[ -f CHANGELOG.md ]]; then
        results+=("CHANGELOG.md:pass")
        ((score++))
    else
        results+=("CHANGELOG.md:fail")
    fi

    if [[ -f AGENTS.md ]]; then
        results+=("AGENTS.md:pass")
        ((score++))
    else
        results+=("AGENTS.md:fail")
    fi

    if [[ -d .github/ISSUE_TEMPLATE ]]; then
        results+=("issue_templates:pass")
        ((score++))
    else
        results+=("issue_templates:fail")
    fi

    if [[ -f .github/PULL_REQUEST_TEMPLATE.md ]]; then
        results+=("pr_template:pass")
        ((score++))
    else
        results+=("pr_template:fail")
    fi

    echo "$score:$total:${results[*]}"
}

# Tier 3: Enhanced (with recommendations)
check_tier3() {
    local score=0
    local total=6
    local results=()

    # QUICKSTART - recommended for all
    if [[ -f docs/QUICKSTART.md ]]; then
        results+=("docs/QUICKSTART.md:pass:recommended")
        ((score++))
    else
        results+=("docs/QUICKSTART.md:fail:recommended")
    fi

    # ARCHITECTURE - recommended for non-trivial projects
    if [[ -f docs/ARCHITECTURE.md ]]; then
        results+=("docs/ARCHITECTURE.md:pass:conditional")
        ((score++))
    else
        local rec="optional"
        # Recommend if large codebase
        [[ $(find . -name "*.go" -o -name "*.py" 2>/dev/null | wc -l) -gt 20 ]] && rec="recommended"
        results+=("docs/ARCHITECTURE.md:fail:$rec")
    fi

    # CLI_REFERENCE - recommended for CLI tools
    # CRD_REFERENCE - recommended for operators (check for either)
    if [[ -f docs/CLI_REFERENCE.md ]] || [[ -f docs/CRD_REFERENCE.md ]]; then
        local found_file="docs/CLI_REFERENCE.md"
        [[ -f docs/CRD_REFERENCE.md ]] && found_file="docs/CRD_REFERENCE.md"
        results+=("$found_file:pass:conditional")
        ((score++))
    else
        local rec="optional"
        local check_file="docs/CLI_REFERENCE.md"
        if [[ "$PROJECT_TYPE" == "operator" ]]; then
            check_file="docs/CRD_REFERENCE.md"
            rec="recommended"
        elif [[ "$PROJECT_TYPE" == "cli-go" ]] || [[ "$PROJECT_TYPE" == "cli-python" ]] || [[ "$PROJECT_TYPE" == "cli-node" ]] || [[ "$PROJECT_TYPE" == "cli-rust" ]]; then
            rec="recommended"
        fi
        results+=("$check_file:fail:$rec")
    fi

    # CONFIG - recommended if configurable or operator
    if [[ -f docs/CONFIG.md ]]; then
        results+=("docs/CONFIG.md:pass:conditional")
        ((score++))
    else
        local rec="optional"
        # Operators should document CRD spec fields
        [[ "$PROJECT_TYPE" == "operator" ]] && rec="recommended"
        [[ -f config.yaml ]] || [[ -d config ]] && rec="recommended"
        results+=("docs/CONFIG.md:fail:$rec")
    fi

    # TROUBLESHOOTING - recommended for production software
    if [[ -f docs/TROUBLESHOOTING.md ]]; then
        results+=("docs/TROUBLESHOOTING.md:pass:conditional")
        ((score++))
    else
        results+=("docs/TROUBLESHOOTING.md:fail:optional")
    fi

    # examples/ directory
    if [[ -d examples ]]; then
        results+=("examples/:pass:recommended")
        ((score++))
    else
        results+=("examples/:fail:optional")
    fi

    echo "$score:$total:${results[*]}"
}

# Parse tier results
parse_results() {
    local tier_data="$1"
    local score="${tier_data%%:*}"
    local rest="${tier_data#*:}"
    local total="${rest%%:*}"
    local items="${rest#*:}"
    echo "$score" "$total" "$items"
}

# Run checks
TIER1=$(check_tier1)
TIER2=$(check_tier2)
TIER3=$(check_tier3)

read -r T1_SCORE T1_TOTAL T1_ITEMS <<< "$(parse_results "$TIER1")"
read -r T2_SCORE T2_TOTAL T2_ITEMS <<< "$(parse_results "$TIER2")"
read -r T3_SCORE T3_TOTAL T3_ITEMS <<< "$(parse_results "$TIER3")"

TOTAL_SCORE=$((T1_SCORE + T2_SCORE + T3_SCORE))
TOTAL_POSSIBLE=$((T1_TOTAL + T2_TOTAL + T3_TOTAL))

# Output
if [[ "$JSON_OUTPUT" == "true" ]]; then
    # JSON output
    cat <<EOF
{
  "project": "$PROJECT_NAME",
  "type": "$PROJECT_TYPE",
  "languages": "$(echo $LANGUAGES | tr ' ' ',')",
  "tier1": {
    "score": $T1_SCORE,
    "total": $T1_TOTAL,
    "items": [$(echo "$T1_ITEMS" | tr ' ' '\n' | sed 's/\(.*\):\(.*\)/{"file":"\1","status":"\2"}/' | tr '\n' ',' | sed 's/,$//' )]
  },
  "tier2": {
    "score": $T2_SCORE,
    "total": $T2_TOTAL,
    "items": [$(echo "$T2_ITEMS" | tr ' ' '\n' | sed 's/\(.*\):\(.*\)/{"file":"\1","status":"\2"}/' | tr '\n' ',' | sed 's/,$//' )]
  },
  "tier3": {
    "score": $T3_SCORE,
    "total": $T3_TOTAL,
    "items": [$(echo "$T3_ITEMS" | tr ' ' '\n' | sed 's/\([^:]*\):\([^:]*\):\(.*\)/{"file":"\1","status":"\2","recommendation":"\3"}/' | tr '\n' ',' | sed 's/,$//' )]
  },
  "total_score": $TOTAL_SCORE,
  "total_possible": $TOTAL_POSSIBLE
}
EOF
else
    # Human-readable output
    echo -e "${BLUE}═══════════════════════════════════════════════════════════${NC}"
    echo -e "${BLUE}  OSS Documentation Audit: ${PROJECT_NAME}${NC}"
    echo -e "${BLUE}═══════════════════════════════════════════════════════════${NC}"
    echo ""
    echo -e "Project Type: ${YELLOW}$PROJECT_TYPE${NC}"
    echo -e "Languages: ${YELLOW}$LANGUAGES${NC}"
    echo ""

    # Tier 1
    echo -e "${BLUE}── Tier 1: Required ──${NC}"
    for item in $T1_ITEMS; do
        file="${item%%:*}"
        status="${item##*:}"
        if [[ "$status" == "pass" ]]; then
            echo -e "  ${GREEN}✓${NC} $file"
        else
            echo -e "  ${RED}✗${NC} $file"
        fi
    done
    echo -e "  Score: ${T1_SCORE}/${T1_TOTAL}"
    echo ""

    # Tier 2
    echo -e "${BLUE}── Tier 2: Standard ──${NC}"
    for item in $T2_ITEMS; do
        file="${item%%:*}"
        status="${item##*:}"
        if [[ "$status" == "pass" ]]; then
            echo -e "  ${GREEN}✓${NC} $file"
        else
            echo -e "  ${RED}✗${NC} $file"
        fi
    done
    echo -e "  Score: ${T2_SCORE}/${T2_TOTAL}"
    echo ""

    # Tier 3
    echo -e "${BLUE}── Tier 3: Enhanced ──${NC}"
    for item in $T3_ITEMS; do
        IFS=':' read -r file status rec <<< "$item"
        if [[ "$status" == "pass" ]]; then
            echo -e "  ${GREEN}✓${NC} $file"
        elif [[ "$rec" == "recommended" ]]; then
            echo -e "  ${YELLOW}✗${NC} $file (recommended)"
        else
            echo -e "  ${NC}○${NC} $file (optional)"
        fi
    done
    echo -e "  Score: ${T3_SCORE}/${T3_TOTAL}"
    echo ""

    # Summary
    echo -e "${BLUE}═══════════════════════════════════════════════════════════${NC}"
    if [[ $T1_SCORE -lt $T1_TOTAL ]]; then
        echo -e "${RED}  Status: INCOMPLETE - Missing required files${NC}"
    elif [[ $T2_SCORE -lt 3 ]]; then
        echo -e "${YELLOW}  Status: BASIC - Consider adding standard files${NC}"
    elif [[ $T3_SCORE -lt 3 ]]; then
        echo -e "${GREEN}  Status: STANDARD - Ready for public${NC}"
    else
        echo -e "${GREEN}  Status: COMPREHENSIVE - Well documented${NC}"
    fi
    echo -e "  Total Score: ${TOTAL_SCORE}/${TOTAL_POSSIBLE}"
    echo -e "${BLUE}═══════════════════════════════════════════════════════════${NC}"

    # Scaffold hint
    if [[ $TOTAL_SCORE -lt $TOTAL_POSSIBLE ]]; then
        echo ""
        echo "To scaffold missing files:"
        echo "  /oss-docs scaffold"
    fi
fi
