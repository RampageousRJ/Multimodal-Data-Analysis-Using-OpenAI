import os
import subprocess
import sys
import time
from pathlib import Path
from dotenv import load_dotenv
from litellm import completion

env_path = Path(__file__).resolve().parent.parent / ".env"

if not env_path.exists():
    print(f"WARNING: .env file not found at {env_path}")

load_dotenv(env_path)

MODEL = "groq/llama-3.3-70b-versatile"
RATE_LIMIT_SLEEP = 5
MAX_FILE_CHARS = 3000
MAX_TOTAL_CHARS = 12000

EXCLUDED_FOLDERS = {
    ".git", ".github", "__pycache__", "node_modules", ".vscode",
    "venv", ".venv", "dist", "build", ".idea", ".mypy_cache",
    ".pytest_cache", ".ruff_cache", "coverage", ".tox", "eggs", ".eggs", "htmlcov",
}
NOISY_EXTENSIONS = {
    ".pyc", ".pyo", ".pyd", ".so", ".dll", ".class", ".log", ".tmp",
    ".temp", ".swp", ".swo", ".png", ".jpg", ".jpeg", ".gif", ".ico",
    ".woff", ".woff2", ".ttf", ".eot", ".map",
}
NOISY_FILENAMES = {
    "hello.txt", "test.txt", "temp.txt", "dummy.txt", ".gitkeep", ".keep",
    ".gitignore", ".gitattributes", "thumbs.db", ".ds_store", "desktop.ini",
    ".env.example", ".env.sample",
}
LOW_SIGNAL_FILENAMES = {
    "__init__.py", "conftest.py", "setup.cfg", "pytest.ini",
    ".flake8", ".pylintrc", "mypy.ini", "tox.ini",
}
READABLE_EXTENSIONS = {
    ".py", ".js", ".ts", ".tsx", ".jsx", ".vue", ".svelte", ".html", ".css",
    ".scss", ".sass", ".less", ".json", ".yaml", ".yml", ".toml", ".ini",
    ".env", ".md", ".txt", ".sh", ".bash", ".go", ".rs", ".java", ".kt",
    ".rb", ".php", ".cs", ".sql", ".graphql", ".proto", ".tf", ".hcl",
}

# ── File helpers ──────────────────────────────────────────────────────────────

def is_noisy(filename: str) -> bool:
    return (
        filename.lower() in NOISY_FILENAMES
        or Path(filename).suffix.lower() in NOISY_EXTENSIONS
        or filename.endswith(".lock")
        or filename.endswith("-lock.json")
    )


def meaningful_files(folder: str) -> list[str]:
    try:
        files = [f for f in os.listdir(folder) if os.path.isfile(os.path.join(folder, f))]
    except PermissionError:
        return []
    clean = [f for f in files if not is_noisy(f)]
    return sorted(clean) if any(f not in LOW_SIGNAL_FILENAMES for f in clean) else []


def read_sources(folder: str, files: list[str]) -> str:
    sections, total = [], 0
    for f in files:
        if f in LOW_SIGNAL_FILENAMES:
            continue
        ext = Path(f).suffix.lower()
        if ext not in READABLE_EXTENSIONS and f.lower() not in {"dockerfile", "makefile", "procfile"}:
            continue
        try:
            raw = open(os.path.join(folder, f), encoding="utf-8", errors="replace").read(MAX_FILE_CHARS + 1)
        except (PermissionError, IsADirectoryError):
            continue
        content = raw[:MAX_FILE_CHARS] + ("\n... [truncated]" if len(raw) > MAX_FILE_CHARS else "")
        sections.append(f"### {f}\n```\n{content}\n```")
        total += len(content)
        if total >= MAX_TOTAL_CHARS:
            sections.append("*... remaining files truncated*")
            break
    return "\n\n".join(sections) or "(no readable source files)"


def folder_tree(folder: str, repo_path: str) -> str:
    lines = []
    for dirpath, dirnames, filenames in os.walk(folder):
        dirnames[:] = sorted(d for d in dirnames if d not in EXCLUDED_FOLDERS and not d.startswith("."))
        depth = len(Path(dirpath).relative_to(folder).parts)
        if depth > 2:
            dirnames[:] = []
            continue
        lines.append("  " * depth + os.path.relpath(dirpath, repo_path) + "/")
        lines += ["  " * depth + "  " + f for f in sorted(filenames) if not is_noisy(f)]
    return "\n".join(lines) or "(empty)"


def git_diff(folder: str, repo_path: str) -> str:
    for args in [["git", "diff", "--cached", "--", folder], ["git", "diff", "HEAD", "--", folder]]:
        try:
            out = subprocess.check_output(args, cwd=repo_path, stderr=subprocess.DEVNULL).decode().strip()
            if out:
                return out
        except subprocess.CalledProcessError:
            pass
    return ""


def surface_folders(root: str, depth: int = 1) -> list[str]:
    """
    Returns root plus all subdirectories up to `depth` levels deep.
    depth=0 → root only, depth=1 → root + direct children, etc.
    """
    base = Path(root).resolve()
    folders = [str(base)]
    for dirpath, dirnames, _ in os.walk(base):
        dirnames[:] = sorted(d for d in dirnames if d not in EXCLUDED_FOLDERS and not d.startswith("."))
        current_depth = len(Path(dirpath).relative_to(base).parts)
        if current_depth >= depth:
            dirnames[:] = []
            continue
        folders += [str(Path(dirpath) / d) for d in dirnames]
    return folders


# ── Prompt building ───────────────────────────────────────────────────────────

FOLDER_TYPE_MAP = {
    "ui":      {"ui", "frontend", "client", "web", "app", "pages", "components", "views", "src"},
    "api":     {"api", "server", "backend", "routes", "endpoints", "rest", "graphql"},
    "agents":  {"agents", "agent", "bots", "assistant", "assistants"},
    "config":  {"config", "configs", "settings", "configuration"},
    "tests":   {"tests", "test", "spec", "specs", "__tests__"},
    "utils":   {"utils", "util", "helpers", "lib", "shared", "common", "core"},
    "scripts": {"scripts", "bin", "tools", "cli"},
}

TYPE_GUIDANCE = {
    "ui":      "Focus on: Overview, Key Components & Features (name actual files), How It Works (user flow, libraries used), Component Structure (annotated tree), Env Vars if any. OMIT: Installation, License, Contributing.",
    "api":     "Focus on: Overview, Endpoints/Routes (table: method/path/params/response), Key Features (auth/middleware/validation), How It Works (request lifecycle), Data Models, Env Vars, Error Handling. OMIT: Installation, License, Contributing.",
    "agents":  "Focus on: Overview, How It Works (decision loop + ASCII flow diagram), Agent Tools (each tool with description), Dynamic Configuration (how to customize), Key Files (annotated tree), Example Interaction. OMIT: Installation, License, Contributing.",
    "config":  "Focus on: Overview, Full Configuration Reference (table: key/type/default/description), How to Customize. OMIT: Installation, License, Contributing, Features.",
    "tests":   "Focus on: Overview (unit/integration/e2e), Test Structure (what each suite covers), How to Run. OMIT: License, Contributing, Installation.",
    "utils":   "Focus on: Overview, Function/Class Reference (signatures + one-liners), Usage Examples (code snippets), File Structure. OMIT: Installation, License, Contributing.",
    "scripts": "Focus on: Overview, Script Reference (each script: purpose + invocation), Usage Examples (real commands), Dependencies. OMIT: License, Contributing.",
    "generic": "Include only sections with real content: Overview, Key Features, How It Works (if non-trivial), Key Files (annotated), Usage/API, Configuration. Omit anything that doesn't apply.",
}

ROOT_GUIDANCE = """Include ALL applicable sections:
1. Title & Badges (shields.io where inferable)
2. Overview (3-5 sentences, specific to actual tech/domain)
3. Key Features (5-8 concrete capabilities)
4. Architecture / How It Works (ASCII diagram if helpful)
5. Project Structure (annotated file tree)
6. Prerequisites (exact versions, tools, accounts)
7. Installation & Setup (step-by-step with ```bash blocks, include venv)
   If a sync_hooks.sh or similar setup script exists, include it as a step here.)
8. Configuration (table of all env vars)
9. Usage (runnable examples)
10. Contributing
11. License"""


def detect_type(folder_rel: str, files: list[str]) -> str:
    name = Path(folder_rel).name.lower()
    for ftype, names in FOLDER_TYPE_MAP.items():
        if name in names:
            return ftype
    files_lower = {f.lower() for f in files}
    exts = {Path(f).suffix.lower() for f in files}
    if files_lower & {"index.html", "app.jsx", "app.tsx", "app.vue", "main.tsx"} or exts & {".tsx", ".jsx", ".vue", ".svelte"}:
        return "ui"
    if files_lower & {"main.py", "app.py", "server.py", "wsgi.py", "asgi.py"}:
        return "api"
    if files_lower & {"agent.py", "agent.ts", "bot.py"}:
        return "agents"
    return "generic"


def build_prompt(label: str, files: list[str], tree: str, diff: str,
                 sources: str, existing: str, is_root: bool) -> str:
    mode = "UPDATE the existing README.md" if existing.strip() else "CREATE a README.md from scratch"
    guidance = ROOT_GUIDANCE if is_root else TYPE_GUIDANCE[detect_type(label, files)]
    return f"""You are a Senior Software Engineer writing a GitHub README.
Task: {mode} for `{label}`.

{guidance}

RULES: Output ONLY raw Markdown. No preamble. No wrapping backticks. Use actual names from the code — no placeholders. Omit sections with nothing real to say. If folder has no substance respond with exactly: SKIP

---
FOLDER: {label}
FILES: {', '.join(files) or '(none)'}

TREE:
{tree}

SOURCE CODE:
{sources}

EXISTING README:
{existing.strip() or '[No existing README]'}

GIT DIFF:
{diff[:8000] + '...[truncated]' if len(diff) > 8000 else diff or '(none — infer from source code)'}""".strip()


# ── LLM call ──────────────────────────────────────────────────────────────────

def call_llm(prompt: str, label: str) -> str | None:
    for attempt in range(3):
        try:
            out = completion(model=MODEL, messages=[{"role": "user", "content": prompt}], max_tokens=4096)
            result = out.choices[0].message.content.strip()
            if result[:10].upper().startswith("SKIP"):
                print(f"  Skipped '{label}' — no meaningful content.")
                return None
            return result
        except Exception as e:
            if "rate limit" in str(e).lower() or "429" in str(e):
                wait = 10 * (2 ** attempt)
                print(f"  Rate limited. Retrying '{label}' in {wait}s...")
                time.sleep(wait)
            else:
                print(f"  ERROR '{label}': {e}")
                return None
    print(f"  FAILED '{label}' after 3 retries.")
    return None


# ── Processing ────────────────────────────────────────────────────────────────

def process_folder(folder: str, repo_path: str, is_root: bool = False, extra_sources: str = "") -> dict | None:
    files = meaningful_files(folder)
    tree = folder_tree(folder, repo_path)
    if not files and tree.strip() == "(empty)":
        return None

    label = "." if is_root else os.path.relpath(folder, repo_path)
    sources = read_sources(folder, files) + (f"\n\n---\n{extra_sources}" if extra_sources else "")
    existing = open(os.path.join(folder, "README.md"), encoding="utf-8").read() if os.path.exists(os.path.join(folder, "README.md")) else ""

    print(f"  Analyzing '{label}'...")
    output = call_llm(build_prompt(label, files, tree, git_diff(folder, repo_path), sources, existing, is_root), label)
    if output is None:
        return None

    open(os.path.join(folder, "README.md"), "w", encoding="utf-8").write(output)
    print(f"  {'Updated' if existing else 'Created'}: {os.path.relpath(os.path.join(folder, 'README.md'), repo_path)}")
    return {"label": label, "files": files, "readme": output}


def main():
    if not os.getenv("GROQ_API_KEY"):
        print("ERROR: GROQ_API_KEY not set.")
        sys.exit(1)

    import argparse
    parser = argparse.ArgumentParser(description="Generate README files for a repo.")
    parser.add_argument("--root_dir", nargs="?", default=".", help="Root directory to start from (default: current dir)")
    parser.add_argument("--depth", type=int, default=1, help="Subfolder depth to traverse (default: 1)")
    args = parser.parse_args()

    repo_path = str(Path(args.root_dir).resolve())
    depth = args.depth

    if not os.path.isdir(repo_path):
        print(f"ERROR: '{repo_path}' is not a valid directory.")
        sys.exit(1)
    if not os.path.isdir(os.path.join(repo_path, ".git")):
        print(f"WARNING: '{repo_path}' does not appear to be a git repo.")

    print(f"Root: {repo_path} | Depth: {depth} | Sleep: {RATE_LIMIT_SLEEP}s between calls\n")

    all_folders = surface_folders(repo_path, depth)
    subfolders = [f for f in all_folders if Path(f).resolve() != Path(repo_path).resolve()]
    print(f"Order: {', '.join(os.path.relpath(f, repo_path) for f in subfolders)} → . (root last)\n")

    # Step 1: subfolders first
    contexts = []
    for i, folder in enumerate(subfolders):
        ctx = process_folder(folder, repo_path)
        if ctx:
            contexts.append(ctx)
        if i < len(subfolders) - 1:
            time.sleep(RATE_LIMIT_SLEEP)

    # Step 2: root last with combined subfolder context
    if subfolders:
        print(f"\n  Sleeping {RATE_LIMIT_SLEEP}s before root...\n")
        time.sleep(RATE_LIMIT_SLEEP)

    combined = "\n\n".join(
        f"### {c['label']}/\nFiles: {', '.join(c['files'])}\n\n{c['readme'][:1200]}{'...' if len(c['readme']) > 1200 else ''}"
        for c in contexts
    )
    process_folder(repo_path, repo_path, is_root=True, extra_sources=f"SUBFOLDER SUMMARIES:\n{combined}" if combined else "")

    print("\nDone.")


if __name__ == "__main__":
    main()