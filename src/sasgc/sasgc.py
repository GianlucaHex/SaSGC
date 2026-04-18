#!/usr/bin/env python3
"""
git-commit-msg: Generate a useful git commit message from staged changes using Ollama.

Usage:
    poetry run python git_commit_msg.py [--model MODEL] [--lang LANG]

Setup:
    poetry install
    Ollama running locally (started automatically if not running)
"""

import re
import subprocess
import sys
import argparse
import time
import urllib.request
import urllib.error
import ollama

SYSTEM_PROMPT = """You are an expert software engineer writing git commit messages.
Given a git diff of staged changes, produce a clear and concise commit message following these rules:

1. First line: imperative mood summary, max 72 chars (e.g. "Add user auth via JWT")
2. Use a conventional commit prefix: fix:, feat:, refactor:, docs:, chore:, test:, style:
3. Leave a blank line after the summary
4. Then paragraphs or bullet points explaining *why* and *what* changed (not just restating the diff)
5. Group related changes together
6. Mention any breaking changes with "BREAKING CHANGE:" prefix
7. Do NOT include the diff itself, file paths, or line numbers in the message
8. Output ONLY the commit message, nothing else — no preamble, no markdown fences

---

Here are examples of good commit messages to guide your output:

Example 1 — a bug fix:
```
fix: handle NaN values in feature engineering

The preprocessing pipeline crashed when encountering NaN values
in the 'age' column. Added fillna() with median imputation before
scaling features.
```
This works because it identifies the problem (NaN crashes), explains where it happened
(preprocessing pipeline, age column), and describes the solution (median imputation).

Example 2 — a new feature:
```
feat: add model performance tracking to MLflow

Added automatic logging of model metrics, parameters, and artifacts
to MLflow after each training run. This replaces our manual CSV
logging and makes experiment comparison much easier.

Metrics tracked: accuracy, precision, recall, F1 score
Training time also logged for performance monitoring.
```
Good feature commits explain what you built, why it's useful, and any details
that help readers understand the scope.

Example 3 — a refactor:
```
refactor: split data_loader.py into separate modules

Moved dataset classes to datasets.py, transformation logic to
transforms.py, and utility functions to utils.py. The original
file was 800+ lines and hard to navigate.

No behavior changes - all tests still pass.
```
Refactor messages should make it clear that you didn't change functionality, just
structure. The "all tests still pass" line reassures reviewers.

Example 4 — a documentation update:
```
docs: add examples for custom loss functions

Previous documentation showed only built-in loss functions.
Added three examples: weighted cross-entropy, focal loss, and
custom regression loss with L1 regularization.

Each example includes code and explanation of when to use it.
```
Documentation commits should explain what you documented and why it was needed.
"""


def is_ollama_running() -> bool:
    try:
        urllib.request.urlopen("http://localhost:11434", timeout=2)
        return True
    except urllib.error.URLError:
        return False


def ensure_ollama_running():
    if is_ollama_running():
        return  # already up, nothing to do

    print("Ollama is not running. Starting 'ollama serve'...", file=sys.stderr)
    subprocess.Popen(
        ["ollama", "serve"],
        stdout=subprocess.DEVNULL,
        stderr=subprocess.DEVNULL,
    )

    # Wait up to 10 seconds for the server to become ready
    for i in range(10):
        time.sleep(1)
        if is_ollama_running():
            print("Ollama server started.\n", file=sys.stderr)
            return
        print(f"  waiting... ({i + 1}s)", file=sys.stderr)

    print("Error: Ollama did not start in time. Is it installed?", file=sys.stderr)
    print("Install it from https://ollama.com", file=sys.stderr)
    sys.exit(1)


def get_staged_diff() -> str:
    result = subprocess.run(
        ["git", "diff", "--staged"],
        capture_output=True,
        text=True,
    )
    if result.returncode != 0:
        print(f"Error running git diff: {result.stderr}", file=sys.stderr)
        sys.exit(1)
    return result.stdout.strip()


def get_repo_context() -> str:
    """Get extra context: current branch and recent commits."""
    branch = subprocess.run(
        ["git", "rev-parse", "--abbrev-ref", "HEAD"], capture_output=True, text=True
    ).stdout.strip()

    log = subprocess.run(
        ["git", "log", "--oneline", "-5"], capture_output=True, text=True
    ).stdout.strip()

    return f"Branch: {branch}\nRecent commits:\n{log}"


def generate_commit_message(
    diff: str, model: str, lang: str, use_reasoning: bool
) -> str:
    context = get_repo_context()

    lang_instruction = ""
    if lang and lang.lower() != "en":
        lang_instruction = f"\nWrite the commit message in {lang}."

    user_message = f"""Here is the git diff of the staged changes:

```diff
{diff}
```

Repository context:
{context}
{lang_instruction}
Generate the commit message now."""

    response = ollama.chat(
        model=model,
        messages=[
            {"role": "system", "content": SYSTEM_PROMPT},
            {"role": "user", "content": user_message},
        ],
        options={"temperature": 0.3},
        think=use_reasoning,
    )
    content = response["message"]["content"].strip()

    return re.sub(r"<think>.*?</think>", "", content, flags=re.DOTALL).strip()


def main():
    parser = argparse.ArgumentParser(
        description="Generate a git commit message from staged changes using Ollama."
    )
    parser.add_argument(
        "--model", default="qwen3.5:4b", help="Ollama model to use (default: llama3.2)"
    )
    parser.add_argument(
        "--lang", default="en", help="Language for the commit message (default: en)"
    )
    parser.add_argument(
        "--apply",
        action="store_true",
        help="Directly run 'git commit' with the generated message",
    )
    parser.add_argument(
        "--use-reasoning",
        action="store_true",
        help="Disable chain-of-thought reasoning (faster, for reasoning models)",
    )
    args = parser.parse_args()

    ensure_ollama_running()

    diff = get_staged_diff()
    if not diff:
        print("No staged changes found. Stage some files first with 'git add'.")
        sys.exit(0)

    print(f"Generating commit message with model '{args.model}'...\n", file=sys.stderr)

    message = generate_commit_message(diff, args.model, args.lang, args.use_reasoning)

    print("─" * 60)
    print(message)
    print("─" * 60)

    if args.apply:
        result = subprocess.run(["git", "commit", "-m", message])
        sys.exit(result.returncode)
    else:
        print("\nTo commit with this message, run:")
        print(f'  git commit -m "{message.splitlines()[0]}"')
        print("Or re-run with --apply to commit automatically.")


if __name__ == "__main__":
    main()
