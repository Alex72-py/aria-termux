#!/bin/bash
# ══════════════════════════════════════════════════════════════════
#  ARIA v4 — Install Script
#  Termux / proot-distro Ubuntu
#
#  What this does:
#  1. Installs Python deps
#  2. Installs the `aria` command
#  3. Cleans ALL previous ARIA hook versions from .bashrc/.zshrc
#  4. Installs a single clean hook (aria_hook_v4)
#  5. Updates ~/.aria/config.json with max_tokens fix
# ══════════════════════════════════════════════════════════════════

set -e

G="\e[32m"; Y="\e[33m"; R="\e[31m"; C="\e[36m"; B="\e[1m"; X="\e[0m"
ok()   { echo -e "  ${G}✓${X}  $1"; }
warn() { echo -e "  ${Y}⚠${X}  $1"; }
fail() { echo -e "  ${R}✗${X}  $1"; }

echo ""
echo -e "${C}${B}"
echo "  ╔══════════════════════════════════════════════════════╗"
echo "  ║  ARIA — Autonomous Repair & Intelligence Agent       ║"
echo "  ║  v4 Install Script                                   ║"
echo "  ╚══════════════════════════════════════════════════════╝"
echo -e "${X}"

# Guard: run from project root
if [ ! -f "setup.py" ] && [ ! -f "run_aria.py" ]; then
    fail "Run this from the aria-project directory."
    exit 1
fi

# ── 1. Python ────────────────────────────────────────────────────
if ! command -v python3 &>/dev/null && ! command -v python &>/dev/null; then
    echo "Installing Python..."
    pkg install python -y
fi
ok "Python found"

# ── 2. Pip deps ──────────────────────────────────────────────────
echo ""
echo -e "${B}Installing dependencies...${X}"

try_pip() { "$1" install -r requirements.txt --prefer-binary "$2" -q 2>/dev/null; }

if try_pip pip3 "--break-system-packages"; then
    ok "Dependencies installed (pip3)"
elif try_pip pip3 "--user"; then
    ok "Dependencies installed (pip3 --user)"
elif try_pip pip ""; then
    ok "Dependencies installed (pip)"
else
    fail "pip install failed. Try: pip install -r requirements.txt --prefer-binary"
    exit 1
fi

# ── 3. Install ARIA package ───────────────────────────────────────
echo ""
echo -e "${B}Installing ARIA...${X}"

if pip3 install -e . --break-system-packages -q 2>/dev/null; then
    ok "ARIA installed (editable)"
elif pip install -e . -q 2>/dev/null; then
    ok "ARIA installed"
else
    warn "pip install -e . failed. Trying manual bin install."
    BIN_DIR="$HOME/.local/bin"
    mkdir -p "$BIN_DIR"
    cat > "$BIN_DIR/aria" << 'PYEOF'
#!/usr/bin/env python3
import sys
from pathlib import Path
sys.path.insert(0, str(Path(__file__).resolve().parent.parent / "aria-project"))
from aria.main import main
main()
PYEOF
    chmod +x "$BIN_DIR/aria"
    ok "Manual bin installed to $BIN_DIR/aria"
fi

# ── 4. PATH ───────────────────────────────────────────────────────
SHELL_RC="$HOME/.bashrc"
echo "$SHELL" | grep -q zsh 2>/dev/null && SHELL_RC="$HOME/.zshrc"

if ! grep -q '\.local/bin' "$SHELL_RC" 2>/dev/null; then
    echo 'export PATH="$HOME/.local/bin:$PATH"' >> "$SHELL_RC"
    ok "PATH updated in $SHELL_RC"
else
    ok "PATH already configured"
fi

# ── 5. CLEAN all old ARIA hooks ───────────────────────────────────
echo ""
echo -e "${B}Cleaning old ARIA hooks from shell config...${X}"

clean_hooks() {
    local rc="$1"
    [ -f "$rc" ] || return

    local before
    before=$(wc -l < "$rc")

    # Remove all known ARIA hook blocks and markers
    # Uses Python for reliable multi-line removal
    python3 - "$rc" << 'PYEOF'
import sys, re
path = sys.argv[1]
text = open(path).read()

# Patterns that mark ARIA hook blocks from ALL past versions
markers = [
    # Block patterns (remove from marker to next empty-line-after-fi or closing brace)
    r'\n# ARIA.*?hook.*?\n(?:.*?\n)*?(?=\n[^\s#]|\Z)',
    r'\n# termux.copilot.*?\n(?:.*?\n)*?(?=\n[^\s#]|\Z)',
    # Specific function patterns
    r'\n_?aria_hook_v\d+\(\).*?(?=\naria_hook|\nPROMPT_COMMAND|[^\s].*=.*PROMPT|\Z)',
    r'\naria_hook_v\d+\b.*\n',
    r'\n_aria_zsh_hook_v\d+.*\n',
    # PROMPT_COMMAND lines referencing aria
    r'\nif \[\[.*PROMPT_COMMAND.*aria.*\]\].*\n(?:.*?\n){0,3}fi\n?',
    r'\nPROMPT_COMMAND="?_?aria[^"\n]*"?\n',
    r'\nif \[\[ "\$PROMPT_COMMAND".*aria.*\n',
    # add-zsh-hook lines
    r'\nadd-zsh-hook precmd _?aria.*\n',
    # Comment-only remnants
    r'\n# ARIA[^\n]*\n',
    r'\n# termux-copilot[^\n]*\n',
    r'\n# aria[^\n]*\n',
]

original = text
for pattern in markers:
    text = re.sub(pattern, '\n', text, flags=re.IGNORECASE | re.DOTALL)

# Collapse 3+ consecutive blank lines to 2
text = re.sub(r'\n{3,}', '\n\n', text)

if text != original:
    open(path, 'w').write(text)
    print(f"  Cleaned: {path}")
PYEOF

    local after
    after=$(wc -l < "$rc")
    local removed=$(( before - after ))
    [ "$removed" -gt 0 ] && ok "Removed $removed stale lines from $rc" || ok "No old hooks in $rc"
}

clean_hooks "$HOME/.bashrc"
clean_hooks "$HOME/.zshrc"

# ── 6. Install single clean hook ─────────────────────────────────
echo ""
echo -e "${B}Installing shell hook (failure capture)...${X}"

MARKER="aria_hook_v4"

BASH_HOOK='
# ARIA v4 — shell hook
# Captures every failed command to ~/.aria/last_fail.json
# Run /fix in ARIA to diagnose automatically.
_aria_hook_v4() {
    local _code=$?
    local _cmd
    _cmd=$(HISTTIMEFORMAT="" history 1 2>/dev/null | sed "s/^ *[0-9]* *//")
    if [ "$_code" -ne 0 ] && [ -n "$_cmd" ] && [[ "$_cmd" != aria* ]]; then
        mkdir -p "$HOME/.aria" 2>/dev/null
        printf "{\"cmd\":\"%s\",\"code\":%d,\"cwd\":\"%s\",\"ts\":\"%s\"}\n" \
            "$(echo "$_cmd" | sed "s/\"/\\\\\"/g")" \
            "$_code" \
            "$(pwd 2>/dev/null || echo "?")" \
            "$(date +%Y-%m-%dT%H:%M:%S 2>/dev/null || echo "?")" \
            > "$HOME/.aria/last_fail.json" 2>/dev/null || true
    fi
}
if [[ "$PROMPT_COMMAND" != *_aria_hook_v4* ]]; then
    PROMPT_COMMAND="_aria_hook_v4${PROMPT_COMMAND:+;$PROMPT_COMMAND}"
fi
'

ZSH_HOOK='
# ARIA v4 — zsh hook
_aria_zsh_hook_v4() {
    local _code=$?
    local _cmd
    _cmd=$(fc -ln -1 2>/dev/null | sed "s/^ *//")
    if [ "$_code" -ne 0 ] && [ -n "$_cmd" ] && [[ "$_cmd" != aria* ]]; then
        mkdir -p "$HOME/.aria" 2>/dev/null
        printf "{\"cmd\":\"%s\",\"code\":%d,\"cwd\":\"%s\"}\n" \
            "${_cmd//\"/\\\"}" "$_code" "${PWD:-?}" \
            > "$HOME/.aria/last_fail.json" 2>/dev/null || true
    fi
}
autoload -Uz add-zsh-hook 2>/dev/null
add-zsh-hook precmd _aria_zsh_hook_v4 2>/dev/null
'

install_hook() {
    local rc="$1" hook="$2"
    if ! grep -q "$MARKER" "$rc" 2>/dev/null; then
        echo "$hook" >> "$rc"
        ok "Hook installed in $rc"
    else
        ok "Hook already present in $rc"
    fi
}

install_hook "$HOME/.bashrc" "$BASH_HOOK"
[ -f "$HOME/.zshrc" ] && install_hook "$HOME/.zshrc" "$ZSH_HOOK"

# ── 7. Config: fix max_tokens and ensure hook dir ─────────────────
echo ""
echo -e "${B}Configuring...${X}"

mkdir -p "$HOME/.aria"

CFG="$HOME/.aria/config.json"
if [ -f "$CFG" ]; then
    # Patch max_tokens if it's still at the truncating 2048
    python3 - "$CFG" << 'PYEOF'
import json, sys
path = sys.argv[1]
try:
    cfg = json.loads(open(path).read())
    changed = False
    if cfg.get("max_tokens", 0) < 4096:
        cfg["max_tokens"] = 8192
        changed = True
    if changed:
        open(path, "w").write(json.dumps(cfg, indent=2))
        print("  Raised max_tokens to 8192 (was causing truncation)")
except Exception as e:
    print(f"  Config update skipped: {e}")
PYEOF
    ok "Config verified"
else
    cat > "$CFG" << 'EOF'
{
  "api_key": "",
  "model": "gemma-4-26b-a4b-it",
  "temperature": 0.7,
  "max_tokens": 8192,
  "watch_mode": false,
  "guardian_mode": true
}
EOF
    ok "Default config created at $CFG"
fi

# Init empty hook file
[ ! -f "$HOME/.aria/last_fail.json" ] && echo "{}" > "$HOME/.aria/last_fail.json"

# ── Done ──────────────────────────────────────────────────────────
echo ""
echo -e "${G}${B}  ══════════════════════════════════════════════════${X}"
echo -e "${G}${B}  ✓  ARIA v4 installed!${X}"
echo -e "${G}${B}  ══════════════════════════════════════════════════${X}"
echo ""
echo -e "  ${B}Next steps:${X}"
echo ""
echo -e "  ${C}1.${X} Reload shell:  ${B}source $SHELL_RC${X}"
echo -e "  ${C}2.${X} Launch ARIA:   ${B}aria${X}  or  ${B}python3 run_aria.py${X}"
echo ""
echo -e "  ${B}Watch mode:${X}"
echo -e "  Type /watch in ARIA, then work normally in this or another terminal."
echo -e "  When a command fails, type /fix in ARIA — it reads the failure automatically."
echo ""
echo -e "  ${B}Logs:${X} ~/.aria/aria.log  (no longer pollutes terminal)"
echo ""

