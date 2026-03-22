#!/usr/bin/env sh
# sync_hooks.sh — installs the pre-commit README hook. Run once after cloning.
# The user must run sh sync_hooks.sh from Git Bash for Windows based system, not CMD or PowerShell. No issues for Mac or Linux distributions.

set -e

REPO_ROOT="$(git rev-parse --show-toplevel 2>/dev/null)" || { echo "ERROR: Not a git repo."; exit 1; }
HOOK_FILE="$REPO_ROOT/.git/hooks/pre-commit"
PYTHON_RECORD="$REPO_ROOT/.git/hooks/.readme_python"
SCRIPT_PATH="$REPO_ROOT/agents/readme_agents/pre_commit_readme.py"

# Verify the agent script exists
[ ! -f "$SCRIPT_PATH" ] && { echo "ERROR: pre_commit_readme.py not found at: $SCRIPT_PATH"; exit 1; }

# ── Find a venv anywhere in the repo (up to 3 levels deep) ───────────────────

echo "Searching for a virtual environment..."
PYTHON_BIN=""

# Use while+read to handle spaces in repo paths safely
PYTHON_BIN=""
TMPFILE="$(mktemp)"
find "$REPO_ROOT" -maxdepth 4 -name "pyvenv.cfg" -not -path "*/.git/*" 2>/dev/null > "$TMPFILE"

while IFS= read -r cfg; do
    venv_dir="$(dirname "$cfg")"
    for candidate in "$venv_dir/bin/python3" "$venv_dir/bin/python" "$venv_dir/Scripts/python.exe" "$venv_dir/Scripts/python"; do
        if [ -x "$candidate" ]; then
            ok="$("$candidate" -c 'import sys; print(sys.version_info >= (3,8))' 2>/dev/null || echo False)"
            if [ "$ok" = "True" ]; then
                PYTHON_BIN="$candidate"
                echo "  Found: $venv_dir"
                break 2
            fi
        fi
    done
done < "$TMPFILE"
rm -f "$TMPFILE"

[ -z "$PYTHON_BIN" ] && {
    echo "ERROR: No virtual environment found in this repo (searched up to 4 levels deep)."
    echo "  Create one with: python3 -m venv .venv && source .venv/bin/activate"
    echo "  Then re-run sync_hooks.sh."
    exit 1
}

echo "  Python: $("$PYTHON_BIN" --version 2>&1)"

# ── Save Python path ──────────────────────────────────────────────────────────

echo "$PYTHON_BIN" > "$PYTHON_RECORD"

# ── Write the pre-commit hook ─────────────────────────────────────────────────

cat > "$HOOK_FILE" << 'HOOK'
#!/usr/bin/env sh
REPO_ROOT="$(git rev-parse --show-toplevel)"
PYTHON_RECORD="$REPO_ROOT/.git/hooks/.readme_python"
SCRIPT="$REPO_ROOT/agents/readme_agents/pre_commit_readme.py"

[ ! -f "$PYTHON_RECORD" ] && { echo "WARNING: .readme_python missing. Re-run sync_hooks.sh. Committing anyway."; exit 0; }
[ ! -f "$SCRIPT" ]        && { echo "WARNING: pre_commit_readme.py not found. Committing anyway."; exit 0; }

PYTHON_BIN="$(cat "$PYTHON_RECORD")"
[ ! -x "$PYTHON_BIN" ] && { echo "WARNING: Python gone: $PYTHON_BIN. Re-run sync_hooks.sh. Committing anyway."; exit 0; }

if ! "$PYTHON_BIN" -c "import litellm, dotenv" 2>/dev/null; then
    "$PYTHON_BIN" -m pip install --quiet litellm python-dotenv 2>/dev/null || {
        echo "WARNING: Dependency install failed. Committing anyway — README sync skipped."
        exit 0
    }
fi

"$PYTHON_BIN" "$SCRIPT" || { echo "WARNING: README sync failed. Committing anyway."; exit 0; }
HOOK

chmod +x "$HOOK_FILE"

echo ""
echo "Hook installed."
echo "  Python: $PYTHON_BIN"
echo "  Script: $SCRIPT_PATH"
echo "To uninstall: rm $HOOK_FILE $PYTHON_RECORD"