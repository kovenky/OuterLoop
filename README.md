# OuterLoop

A tiny self-correcting code-generation loop. You give it a **spec** and a set of
**tests**; it asks an LLM (via [OpenRouter](https://openrouter.ai)) to write a
function, runs the tests, and — if they fail — feeds the failures back to the
model and tries again, up to `max_iters` times.

## How it works

```
spec + tests ──▶ ask_agent ──▶ run_tests ──┬─ pass ─▶ return code
                    ▲                        │
                    └──── failures fed back ─┘ (retry)
```

| File           | Responsibility                                                      |
| -------------- | ------------------------------------------------------------------- |
| `prompt.txt`   | The prompt template (data, not code)                                |
| `providers.py` | LLM provider adapters (OpenRouter, OpenAI, Anthropic)               |
| `helpers.py`   | Prompt building, the agent call (`ask_agent`), and `run_tests`      |
| `loop.py`      | The orchestration loop                                              |
| `run.py`       | An example: generate a `parse_log_line` function from a spec + tests |

## Requirements

- Python 3.10+
- [`uv`](https://docs.astral.sh/uv/) for environment and package management
- An [OpenRouter API key](https://openrouter.ai/keys)

## Setup

### 1. Install `uv` (if you don't have it)

```bash
curl -LsSf https://astral.sh/uv/install.sh | sh
```

### 2. Create the environment and install dependencies

```bash
uv sync                          # creates .venv and installs from pyproject.toml
source .venv/bin/activate        # Windows: .venv\Scripts\activate
```

> Prefer to manage things manually? `uv venv && uv pip install openai pytest`
> does the same thing.

### 3. Choose a provider and set its API key

The provider is selected with the `LLM_PROVIDER` environment variable
(default: `openrouter`). Each provider reads its own key:

```bash
# OpenRouter (default)
export LLM_PROVIDER="openrouter"
export OPENROUTER_API_KEY="sk-or-..."

# OpenAI
export LLM_PROVIDER="openai"
export OPENAI_API_KEY="sk-..."

# Anthropic (needs the extra: uv pip install -e '.[anthropic]')
export LLM_PROVIDER="anthropic"
export ANTHROPIC_API_KEY="sk-ant-..."
```

> The key is read from the environment at import time, so a missing key fails
> loudly and early rather than at the first API call.

## Running the exercise

With the venv activated and the key set:

```bash
python run.py
```

You should see output like:

```
status: success, iterations: 1
def parse_log_line(line):
    ...
```

If the model needs more than one try, `iterations` will be higher; if it never
passes within `max_iters` (default 5), `status` will be `failed`.

## Using it on your own task

Import `loop` and pass your own spec and tests:

```python
from loop import loop

spec = "Implement `add(a, b)` that returns the sum of two numbers."

tests = """
def test_add():
    assert add(2, 3) == 5
"""

result = loop(spec, tests, max_iters=5)
print(result["status"], result["iterations"])
if result["status"] == "success":
    print(result["code"])
```

## Configuration

All via environment variables (no code edits needed):

| Variable        | Purpose                          | Default                          |
| --------------- | -------------------------------- | -------------------------------- |
| `LLM_PROVIDER`  | `openrouter` / `openai` / `anthropic` | `openrouter`                |
| `LLM_MODEL`     | Model id for the chosen provider | per-provider (see below)         |

Default models: `anthropic/claude-sonnet-4.5` (openrouter), `gpt-4o` (openai),
`claude-sonnet-4-6` (anthropic). Override with `LLM_MODEL`, e.g.:

```bash
export LLM_PROVIDER="openai"
export LLM_MODEL="gpt-4o-mini"
```

- **Max iterations** — pass `max_iters` to `loop(...)` (default `5`).
- **Adding a provider** — add an adapter class with a `complete(prompt) -> str`
  method in `providers.py` and a branch in `get_provider()`. Nothing else changes.
