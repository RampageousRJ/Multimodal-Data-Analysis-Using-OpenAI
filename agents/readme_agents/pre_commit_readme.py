"""
pre_commit_readme.py

Triggered from a git pre-commit hook. Analyses the staged diff, determines
which folders have functionally significant changes, and updates or creates
README.md files accordingly.
"""

import os
import subprocess
import sys
import time
from pathlib import Path
from dotenv import load_dotenv
from litellm import completion

sys.path.insert(0, str(Path(__file__).resolve().parent))
from generate_readme import (
    is_noisy,
    meaningful_files,
    read_sources,
    folder_tree,
    detect_type,
    TYPE_GUIDANCE,
    ROOT_GUIDANCE,
    call_llm,
    RATE_LIMIT_SLEEP,
    MODEL,
    surface_folders,
)

load_dotenv(Path(__file__).resolve().parent.parent / ".env")

EXCLUDED_FOLDERS = {
    ".git", ".github", "__pycache__", "node_modules", ".vscode",
    "venv", ".venv", "dist", "build", ".idea",
}


# ── Git helpers ───────────────────────────────────────────────────────────────

def _strip_noisy_hunks(diff: str) -> str:
    """Removes diff hunks belonging to noisy files."""
    blocks = diff.split("\ndiff --git ")
    clean = []
    for i, block in enumerate(blocks):
        full = block if i == 0 else "diff --git " + block
        try:
            filename = Path(full.splitlines()[0].split(" b/")[-1]).name
        except Exception:
            filename = ""
        if filename and is_noisy(filename):
            continue
        clean.append(full)
    return "\n".join(clean).strip()


def get_staged_diff_by_folder() -> dict[str, str]:
    """Returns { folder: diff } for folders with staged non-noisy changes."""
    try:
        names = subprocess.check_output(
            ["git", "diff", "--cached", "--name-only"],
            stderr=subprocess.DEVNULL,
        ).decode().strip().splitlines()
    except subprocess.CalledProcessError:
        return {}

    folder_files: dict[str, list[str]] = {}
    for f in names:
        if is_noisy(Path(f).name):
            print(f"  Ignoring noisy file: {f}")
            continue
        top = f.split("/")[0] if "/" in f else "."
        if top in EXCLUDED_FOLDERS:
            continue
        folder_files.setdefault(top, []).append(f)

    if not folder_files:
        return {}

    repo_root = subprocess.check_output(
        ["git", "rev-parse", "--show-toplevel"], stderr=subprocess.DEVNULL
    ).decode().strip()

    result = {}
    for folder, files in folder_files.items():
        try:
            raw_diff = subprocess.check_output(
                ["git", "diff", "--cached", "--", *files],
                cwd=repo_root, stderr=subprocess.DEVNULL,
            ).decode().strip()
        except subprocess.CalledProcessError:
            continue

        clean_diff = _strip_noisy_hunks(raw_diff)
        if clean_diff:
            result[folder] = clean_diff
        else:
            print(f"  Folder '{folder}' skipped — all staged changes are in noisy files.")

    return result


def stage_readme(folder: str) -> None:
    """Stages the README.md so it is included in the commit."""
    readme = os.path.join(folder, "README.md")
    if os.path.exists(readme):
        subprocess.run(["git", "add", readme], check=False)


# ── Prompt ────────────────────────────────────────────────────────────────────

def build_update_prompt(folder: str, diff: str, sources: str, existing: str, tree: str) -> str:
    files = meaningful_files(folder)
    is_root = folder == "."
    folder_type = detect_type(folder, files)
    type_guidance = ROOT_GUIDANCE if is_root else TYPE_GUIDANCE.get(folder_type, TYPE_GUIDANCE["generic"])
    has_readme = bool(existing.strip())
    mode = "UPDATE the existing README.md" if has_readme else "CREATE a README.md from scratch"
    current_section = existing if has_readme else "[No README exists — create from source code]"
    if len(diff) > 8000:
        diff = diff[:8000] + "\n...[diff truncated]"

    update_rules = """
CRITICAL PRESERVATION RULES (when updating an existing README):
- You MUST output the COMPLETE README from top to bottom.
- Copy every section, paragraph, diagram, and code block that is NOT affected by the diff EXACTLY as-is — character for character.
- ASCII diagrams, architecture diagrams, tables, and code blocks must be preserved verbatim unless the diff directly changes what they depict.
- Only modify the specific sections that describe what changed in the diff.
- If you are unsure whether a section is affected, preserve it unchanged.
- The output must be at least as long as the existing README unless content was explicitly deleted in the diff.
""" if has_readme else ""

    return f"""You are a Senior Software Engineer maintaining GitHub documentation.

Task: {mode} for `{folder}`.

[INTERNAL INSTRUCTIONS — do not reproduce any of the following in your output]

SIGNIFICANCE CHECK — read the diff and decide silently:
- SIGNIFICANT: new/removed function, class, endpoint, route, dependency, import, env var, config key, CLI flag, protocol, port, data model, feature, tool, agent capability, auth/security logic.
- NOT SIGNIFICANT: whitespace, comments, docstrings, log/print changes, renames with identical behaviour, refactors with unchanged inputs/outputs, .txt/.lock/.log file changes.
If ALL changes are not significant → respond with exactly: SKIP
If ANY change is significant → write the updated README below. Do not mention this evaluation in your output.

{"Repository root" if is_root else f"Folder type: {folder_type.upper()}"}
{type_guidance}
{update_rules}
OUTPUT RULES (follow silently — do not mention these in your response):
- Raw Markdown only. Your response IS the README. Nothing else.
- Do NOT output any preamble, commentary, step headers, or meta-text.
- Do NOT wrap output in triple backticks.
- Facts only — evidenced by the diff and source code below.
- When creating: cover only what is actually present in the source code.

[END INTERNAL INSTRUCTIONS]

STAGED DIFF:
```diff
{diff}
```

REFERENCE CONTEXT:
FOLDER: {folder}
FILES: {', '.join(files) or '(none)'}

TREE:
{tree}

SOURCE CODE:
{sources}

EXISTING README (reproduce in full — only patch what the diff requires):
{current_section}
""".strip()


# ── Core logic ────────────────────────────────────────────────────────────────

def _llm_raw(prompt: str, label: str) -> str | None:
    """Calls LLM and returns raw string including SKIP so callers can log context-aware reasons."""
    for attempt in range(3):
        try:
            out = completion(model=MODEL, messages=[{"role": "user", "content": prompt}], max_tokens=4096)
            return out.choices[0].message.content.strip()
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


def build_subfolder_summaries(repo_root: str) -> str:
    """
    Reads existing READMEs (or source files) from all surface subfolders.
    Used to give the root README full project context during hook runs.
    """
    summaries = []
    for folder_path in surface_folders(repo_root, depth=1):
        if Path(folder_path).resolve() == Path(repo_root).resolve():
            continue
        label = os.path.relpath(folder_path, repo_root)
        files = meaningful_files(folder_path)
        if not files:
            continue
        readme_path = os.path.join(folder_path, "README.md")
        if os.path.exists(readme_path):
            summary = open(readme_path, encoding="utf-8").read()[:1500]
        else:
            summary = read_sources(folder_path, files)[:800]
        summaries.append(f"### {label}/\nFiles: {', '.join(files)}\n\n{summary}")
    return "\n\n".join(summaries)


def process_staged_folder(folder: str, diff: str, repo_root: str) -> bool:
    """
    Processes one folder: reads context, calls LLM, writes README if needed.
    For root (.), injects subfolder summaries so the LLM has full project context.
    Returns True if a README was written.
    """
    is_root = folder == "."
    abs_folder = repo_root if is_root else os.path.join(repo_root, folder)
    readme_path = os.path.join(abs_folder, "README.md")

    files = meaningful_files(abs_folder)
    sources = read_sources(abs_folder, files)
    tree = folder_tree(abs_folder, repo_root)
    existing = open(readme_path, encoding="utf-8").read() if os.path.exists(readme_path) else ""

    # Root README gets full subfolder context injected so LLM knows the whole project
    if is_root:
        subfolder_summaries = build_subfolder_summaries(repo_root)
        if subfolder_summaries:
            sources += "\n\n---\nSUBFOLDER SUMMARIES:\n" + subfolder_summaries

    action = "Updating" if existing else "Creating"
    print(f"  {action} README for '{folder}'...")

    prompt = build_update_prompt(folder, diff, sources, existing, tree)
    raw = _llm_raw(prompt, folder)

    if raw is None:
        return False

    if raw[:10].upper().startswith("SKIP"):
        print(f"  Skipped '{folder}' — LLM found no significant functional changes in this diff.")
        return False

    open(readme_path, "w", encoding="utf-8").write(raw)
    stage_readme(abs_folder)
    print(f"  {'Updated' if existing else 'Created'} and staged: {folder}/README.md")
    return True


def main():
    if not os.getenv("GROQ_API_KEY"):
        print("ERROR: GROQ_API_KEY not set.")
        sys.exit(1)

    try:
        repo_root = subprocess.check_output(
            ["git", "rev-parse", "--show-toplevel"], stderr=subprocess.DEVNULL
        ).decode().strip()
    except subprocess.CalledProcessError:
        print("ERROR: Not inside a git repository.")
        sys.exit(1)

    print("Scanning staged diff for README-worthy changes...\n")
    staged = get_staged_diff_by_folder()

    if not staged:
        print("No staged changes found after filtering noisy files. Nothing to do.")
        sys.exit(0)

    # Always process root (.) last so it has the most up-to-date subfolder context
    subfolders = [(f, d) for f, d in staged.items() if f != "."]
    root_entry = [(f, d) for f, d in staged.items() if f == "."]
    ordered = subfolders + root_entry

    print(f"Order: {', '.join(f for f, _ in ordered)}\n")

    written = 0
    for i, (folder, diff) in enumerate(ordered):
        result = process_staged_folder(folder, diff, repo_root)
        if result:
            written += 1
        if i < len(ordered) - 1:
            time.sleep(RATE_LIMIT_SLEEP)

    skipped = len(ordered) - written
    print(f"\nDone. {written} README(s) updated, {skipped} folder(s) skipped (no significant changes).")


if __name__ == "__main__":
    main()