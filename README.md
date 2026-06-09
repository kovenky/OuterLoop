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

Every LLM call and every iteration is appended to a JSON Lines log so a run can
be inspected after the fact (see [Observability](#observability)).

The code lives in the `src/` package:

| File                   | Responsibility                                                      |
| ---------------------- | ------------------------------------------------------------------- |
| `src/prompt.txt`       | The prompt template (data, not code)                                |
| `src/providers.py`     | LLM provider adapters (OpenRouter, OpenAI, Anthropic)               |
| `src/helpers.py`       | Prompt building, the agent call (`ask_agent`), `run_tests`, fence stripping |
| `src/loop.py`          | The orchestration loop                                              |
| `src/observability.py` | JSONL event logging (`log_event`, `new_run_id`)                     |
| `src/run.py`           | An example: generate a `parse_log_line` function from a spec + tests |

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

`uv sync` installs the project, which registers an `outerloop` console command.
With your API key set, run any of these from the **project root**:

```bash
make run          # convenience wrapper
uv run outerloop  # without activating the venv
outerloop         # with the venv activated
```

The [Makefile](Makefile) also provides `make install` (= `uv sync`),
`make test` (= `uv run pytest`), and `make clean`.

> Running as a module (`python -m src.run`) still works, but `python src/run.py`
> does not — the example uses absolute imports (`from src.loop import loop`), so
> `src` must be importable as a package, which only happens from the repo root.

You should see output like:

```
status: success, iterations: 1
def parse_log_line(line):
    ...
```

If the model needs more than one try, `iterations` will be higher; if it never
passes within `max_iters` (default 5), `status` will be `failed`.

## Using it on your own task

Import `loop` and pass your own spec and tests (run from the project root):

```python
from src.loop import loop

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

## Observability

Each run appends structured records — one JSON object per line — to
`src/loop-logs.jsonl` (git-ignored). All records from a single `loop()` call
share a `run_id` so you can correlate the LLM calls with the iterations they
produced. Tail it live with `tail -f src/loop-logs.jsonl`.

| `event`     | Key fields                                                              |
| ----------- | ---------------------------------------------------------------------- |
| `run_start` | `run_id`, `max_iters`, `spec`                                          |
| `llm_call`  | `iteration`, `provider`, `model`, `latency_ms`, `prompt`, `response`, `fence_stripped`, `raw_response`, `ok` |
| `iteration` | `iteration`, `passed`, `code`, `output`                               |
| `run_end`   | `status`, `iterations`                                                |

> **Note:** records include the full prompt and response (no truncation), so the
> log captures whatever you send the model. It's append-only and grows with every
> run; delete it freely. Override the path with `LOOP_LOG_PATH`.

`raw_response` and `fence_stripped` exist because models often wrap code in
markdown fences despite being told not to. `ask_agent` strips a surrounding
fence before the code is run (otherwise pytest sees ```` ```python ```` and dies
with a `SyntaxError`); `fence_stripped` flags when that happened.

## Configuration

All via environment variables (no code edits needed):

| Variable        | Purpose                          | Default                          |
| --------------- | -------------------------------- | -------------------------------- |
| `LLM_PROVIDER`  | `openrouter` / `openai` / `anthropic` | `openrouter`                |
| `LLM_MODEL`     | Model id for the chosen provider | per-provider (see below)         |
| `LOOP_LOG_PATH` | Where the JSONL log is written   | `src/loop-logs.jsonl`            |

Default models: `anthropic/claude-sonnet-4.5` (openrouter), `gpt-4o` (openai),
`claude-sonnet-4-6` (anthropic). Override with `LLM_MODEL`, e.g.:

```bash
export LLM_PROVIDER="openai"
export LLM_MODEL="gpt-4o-mini"
```

- **Max iterations** — pass `max_iters` to `loop(...)` (default `5`).
- **Adding a provider** — add an adapter class with a `complete(prompt) -> str`
  method in `providers.py` and a branch in `get_provider()`. Nothing else changes.
