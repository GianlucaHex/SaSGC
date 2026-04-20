# SaSGC

Simple and Stupid Git Commit — a CLI tool that reads your staged changes
and generates a conventional commit message using a local LLM via Ollama.
No cloud, no API keys, everything runs on your machine.

---

## Requirements

- Python 3.10 or newer
- [Poetry](https://python-poetry.org/docs/#installation)
- [Ollama](https://ollama.com/download)

---

## Installation

### 1. Install Ollama

Follow the instructions at https://ollama.com/download for your OS.

Pull a recommended model (3b is the best balance for CPU-only machines):
```bash
ollama pull qwen2.5-coder:3b
```

### 2. Clone the repository

```bash
git clone https://github.com/youruser/sasgc.git
cd sasgc
```

### 3. Install Python dependencies

```bash
poetry install
```

This creates an isolated virtualenv and installs the `ollama` Python library.
The `sasgc` command becomes available inside the Poetry environment.

---

## Usage

Stage your changes as usual, then run:

```bash
git add .
poetry run sasgc
```

Ollama will be started automatically if it is not already running.

### Options

| Flag | Default | Description |
|---|---|---|
| `--model MODEL` | `qwen2.5-coder:3b` | Ollama model to use |
| `--lang LANG` | `en` | Language for the commit message |
| `--apply` | off | Run `git commit` automatically with the generated message |
| `--no-think` | off | Strip chain-of-thought blocks (useful for reasoning models) |

### Examples

```bash
# Generate and print the message, then decide manually
poetry run sasgc

# Use a different model
poetry run sasgc --model mistral:7b

# Generate and commit in one step
poetry run sasgc --apply

# Write the commit message in Italian
poetry run sasgc --lang italian

# Use a reasoning model without waiting for the thinking block
poetry run sasgc --model qwen3.5:27b --no-think
```

---

## Performance notes

SaSGC runs entirely on local hardware. Speed depends on your machine.

If you have no dedicated GPU (CPU-only), prefer 3b models over 7b.
You can cap generation length and set thread count for faster results:

```bash
OLLAMA_NUM_THREADS=8 poetry run sasgc --model qwen2.5-coder:3b
```
