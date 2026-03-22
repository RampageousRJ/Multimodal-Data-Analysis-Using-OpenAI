# Overview
The `readme_agents` project is designed to automate the generation and update of README.md files within a repository. It uses a combination of natural language processing (NLP) and git hooks to analyze changes and create or update README files accordingly.

# Key Features
* Automatic generation of README.md files based on repository contents
* Analysis of staged diff to determine which folders have significant changes
* Updates or creates README.md files for folders with significant changes
* Excludes noisy files and folders from analysis
* Uses a pre-commit hook to trigger analysis and updates

# How It Works
The project consists of two main components: `generate_readme.py` and `pre_commit_readme.py`. The `generate_readme.py` script is responsible for generating README.md files based on repository contents, while the `pre_commit_readme.py` script is a pre-commit hook that analyzes the staged diff and triggers updates to README.md files as needed.

# Key Files
* `generate_readme.py`: generates README.md files based on repository contents
* `pre_commit_readme.py`: pre-commit hook that analyzes staged diff and triggers updates to README.md files

# Usage/API
To use the `readme_agents` project, simply install the pre-commit hook by running `git hooks --install` in your repository. The hook will automatically trigger on each commit, analyzing the staged diff and updating README.md files as needed.

# Configuration
The project uses a `.env` file to store configuration settings, including the model used for natural language processing and rate limiting settings. The following variables can be configured:
* `MODEL`: the model used for natural language processing (default: `groq/llama-3.3-70b-versatile`)
* `RATE_LIMIT_SLEEP`: the rate limit sleep time in seconds (default: `5`)