#!/usr/bin/env bash
# forge installer for Linux and macOS
# Usage:
#   bash install.sh                  (from inside the cloned repo)
#   curl -fsSL <raw-url>/install.sh | bash   (auto-clones the repo)

set -e

REPO_URL="https://github.com/flawlessenergy/forge"
INSTALL_DIR="$HOME/.local/bin"
MIN_PYTHON_MINOR=10

# ── colours ──────────────────────────────────────────────────────────────────
RED='\033[0;31m'; GREEN='\033[0;32m'; YELLOW='\033[1;33m'
CYAN='\033[0;36m'; BOLD='\033[1m'; RESET='\033[0m'
ok()   { echo -e "${GREEN}✓${RESET} $*"; }
info() { echo -e "${CYAN}→${RESET} $*"; }
warn() { echo -e "${YELLOW}!${RESET} $*"; }
die()  { echo -e "${RED}✗ Error:${RESET} $*" >&2; exit 1; }

echo -e "\n${BOLD}forge installer${RESET}\n"

# ── find Python ──────────────────────────────────────────────────────────────
PYTHON=""
for cmd in python3 python; do
    if command -v "$cmd" &>/dev/null; then
        ver=$("$cmd" -c "import sys; print(sys.version_info.minor)" 2>/dev/null)
        maj=$("$cmd" -c "import sys; print(sys.version_info.major)" 2>/dev/null)
        if [[ "$maj" == "3" && "$ver" -ge "$MIN_PYTHON_MINOR" ]]; then
            PYTHON="$cmd"
            break
        fi
    fi
done

[[ -z "$PYTHON" ]] && die "Python 3.${MIN_PYTHON_MINOR}+ not found.\nInstall from: https://python.org/downloads"
ok "Python: $($PYTHON --version)"

# ── locate repo ──────────────────────────────────────────────────────────────
# If piped through curl, SCRIPT_DIR won't contain pyproject.toml — clone it.
SCRIPT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]:-$0}")" 2>/dev/null && pwd || echo "")"

if [[ ! -f "$SCRIPT_DIR/pyproject.toml" ]]; then
    info "Cloning forge from GitHub..."
    TMP_DIR="$(mktemp -d)"
    git clone --depth 1 "$REPO_URL" "$TMP_DIR/forge" \
        || die "Could not clone $REPO_URL\nCheck your internet connection."
    SCRIPT_DIR="$TMP_DIR/forge"
fi

# ── create venv ──────────────────────────────────────────────────────────────
VENV="$SCRIPT_DIR/.venv"
info "Creating virtual environment at $VENV ..."
"$PYTHON" -m venv "$VENV"
ok "Virtual environment ready"

# ── install ──────────────────────────────────────────────────────────────────
info "Installing forge..."
"$VENV/bin/pip" install --quiet --upgrade pip
"$VENV/bin/pip" install --quiet -e "$SCRIPT_DIR"
ok "forge installed"

# ── symlink ──────────────────────────────────────────────────────────────────
mkdir -p "$INSTALL_DIR"
ln -sf "$VENV/bin/forge" "$INSTALL_DIR/forge"
ok "Symlinked → $INSTALL_DIR/forge"

# ── PATH check ───────────────────────────────────────────────────────────────
echo ""
if [[ ":$PATH:" != *":$INSTALL_DIR:"* ]]; then
    warn "$INSTALL_DIR is not in your PATH."
    SHELL_RC=""
    case "$SHELL" in
        */zsh)  SHELL_RC="$HOME/.zshrc" ;;
        */bash) SHELL_RC="$HOME/.bashrc" ;;
    esac

    if [[ -n "$SHELL_RC" ]]; then
        echo "  Add this line to $SHELL_RC:"
        echo ""
        echo -e "    ${CYAN}export PATH=\"\$HOME/.local/bin:\$PATH\"${RESET}"
        echo ""
        read -r -p "  Add it automatically now? [y/N] " ans
        if [[ "$ans" =~ ^[Yy]$ ]]; then
            echo '' >> "$SHELL_RC"
            echo '# forge' >> "$SHELL_RC"
            echo 'export PATH="$HOME/.local/bin:$PATH"' >> "$SHELL_RC"
            ok "Added to $SHELL_RC — restart your terminal or run: source $SHELL_RC"
        fi
    else
        echo "  Add $INSTALL_DIR to your PATH manually."
    fi
else
    ok "PATH already includes $INSTALL_DIR"
fi

echo ""
echo -e "${BOLD}Done!${RESET} Run:  ${CYAN}forge --help${RESET}"
echo ""
echo "Quick start:"
echo "  cd your-project"
echo "  forge init --scaffold"
echo "  forge docs edit tasks"
echo "  forge chat"
echo ""
