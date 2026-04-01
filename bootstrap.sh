#!/usr/bin/env bash
# bootstrap.sh — Set up a fresh STELAX fork for local development
# Usage: bash bootstrap.sh

set -euo pipefail

RED='\033[0;31m'
GREEN='\033[0;32m'
YELLOW='\033[1;33m'
BOLD='\033[1m'
RESET='\033[0m'

ok()   { echo -e "${GREEN}  ✓${RESET} $1"; }
warn() { echo -e "${YELLOW}  !${RESET} $1"; }
fail() { echo -e "${RED}  ✗${RESET} $1"; exit 1; }
step() { echo -e "\n${BOLD}$1${RESET}"; }

echo -e "${BOLD}"
echo "  ╔══════════════════════════════════════╗"
echo "  ║        STELAX Bootstrap Setup        ║"
echo "  ╚══════════════════════════════════════╝"
echo -e "${RESET}"

# ── 1. Prerequisites ──────────────────────────────────────────────────────────
step "1/5  Checking prerequisites"

if ! command -v python3 &>/dev/null; then
    fail "Python 3 not found. Install Python 3.12+ and retry."
fi

PY_VERSION=$(python3 -c "import sys; print(f'{sys.version_info.major}.{sys.version_info.minor}')")
PY_MAJOR=$(python3 -c "import sys; print(sys.version_info.major)")
PY_MINOR=$(python3 -c "import sys; print(sys.version_info.minor)")
if [ "$PY_MAJOR" -lt 3 ] || { [ "$PY_MAJOR" -eq 3 ] && [ "$PY_MINOR" -lt 12 ]; }; then
    fail "Python 3.12+ required (found $PY_VERSION). Please upgrade."
fi
ok "Python $PY_VERSION"

if ! command -v docker &>/dev/null; then
    warn "Docker not found — Veritas and NanoClaw services won't be available locally."
    DOCKER_AVAILABLE=false
else
    ok "Docker $(docker --version | awk '{print $3}' | tr -d ',')"
    DOCKER_AVAILABLE=true
fi

if ! command -v git &>/dev/null; then
    fail "Git not found. Install git and retry."
fi
ok "Git $(git --version | awk '{print $3}')"

# ── 2. Python package ─────────────────────────────────────────────────────────
step "2/5  Installing Python exporter package"

cd apps/exporter
pip install -e . --quiet && ok "stelax-exporter installed (editable)"
pip install pytest --quiet && ok "pytest installed"
cd ../..

# ── 3. Config files ───────────────────────────────────────────────────────────
step "3/5  Setting up config files"

copy_if_missing() {
    local src="$1" dst="$2"
    if [ -f "$dst" ]; then
        warn "$dst already exists — skipping (delete it to reset)"
    else
        cp "$src" "$dst"
        ok "Created $dst"
    fi
}

copy_if_missing configs/veritas/.env.example           configs/veritas/.env
copy_if_missing configs/veritas/integrations.example.json configs/veritas/integrations.json
copy_if_missing configs/nanoclaw/.env.example          configs/nanoclaw/.env
copy_if_missing configs/nanoclaw/mounts.example.json   configs/nanoclaw/mount_policy.json

# ── 4. Secrets reminder ───────────────────────────────────────────────────────
step "4/5  Secrets checklist"

echo "   Open these files and replace the placeholder values:"
echo ""
echo "   configs/veritas/.env"
echo "     VERITAS_API_KEY   — API key for your Veritas instance"
echo "     GITHUB_TOKEN      — GitHub PAT with Issues read access"
echo "     VERITAS_DB_URL    — Postgres connection string"
echo ""
echo "   configs/nanoclaw/.env"
echo "     NANOCLAW_TASK_QUEUE_URL — Redis connection string"
echo ""
echo "   GitHub repository secrets (Settings → Secrets → Actions):"
echo "     VERITAS_API_KEY   — same key as above"
echo "     MEMORY_REPO_PAT   — GitHub PAT scoped to your memory repo (write only)"
echo ""
warn "Never commit .env files — they are in .gitignore"

# ── 5. Smoke test ─────────────────────────────────────────────────────────────
step "5/5  Running smoke tests"

cd apps/exporter
if python -m pytest tests/ -q 2>&1; then
    ok "All tests passed"
else
    warn "Some tests failed — check output above"
fi
cd ../..

# ── Done ──────────────────────────────────────────────────────────────────────
echo ""
echo -e "${BOLD}  Bootstrap complete.${RESET}"
echo ""
echo "  Next steps:"
echo "    1. Fill in secrets in configs/veritas/.env and configs/nanoclaw/.env"
if [ "$DOCKER_AVAILABLE" = true ]; then
echo "    2. Start services:  cd configs/veritas && docker compose up -d"
echo "                        cd configs/nanoclaw && docker compose up -d"
else
echo "    2. Install Docker, then: cd configs/veritas && docker compose up -d"
fi
echo "    3. Add VERITAS_API_KEY and MEMORY_REPO_PAT to your GitHub repo secrets"
echo "    4. Open an Issue in your fork using one of the intake forms"
echo ""
echo "  Docs:  docs/architecture.md  |  docs/acceptance-tests.md"
echo ""
