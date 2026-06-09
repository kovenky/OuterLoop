# helpers.py
"""Supporting functions: prompt building, the agent call, and test running."""
import re
import subprocess
import tempfile
import time
from pathlib import Path

from src.observability import log_event
from src.providers import get_provider

PROMPT_TEMPLATE = Path(__file__).with_name("prompt.txt").read_text()

agent = get_provider()


def strip_code_fences(text: str) -> str:
    """Remove a surrounding ```lang ... ``` markdown fence if the model added one.

    Models routinely wrap code in fences despite being told not to. If we don't
    strip them, the fence ends up in the file we run and pytest fails with a
    SyntaxError before the code is ever executed.
    """
    text = text.strip()
    match = re.match(r"^```[\w]*\n(.*)\n```$", text, re.DOTALL)
    return match.group(1).strip() if match else text


def format_history(history: list[dict]) -> str:
    """Render previous failed attempts as text to append to the prompt."""
    if not history:
        return ""
    attempts = []
    for i, attempt in enumerate(history, 1):
        attempts.append(
            f"Attempt {i}:\n```python\n{attempt['code']}\n```\n"
            f"Test output:\n{attempt['output']}"
        )  # code is fence-stripped before storage, so this wraps it exactly once
    return "\n\nPrevious attempts:\n" + "\n\n".join(attempts)


def build_prompt(spec: str, tests: str, history: list[dict]) -> str:
    """Fill the prompt template with the spec, tests, and prior attempts."""
    return (
        PROMPT_TEMPLATE
        .replace("{spec}", spec)
        .replace("{tests}", tests)
        .replace("{history}", format_history(history))
    )


def ask_agent(
    spec: str,
    tests: str,
    history: list[dict],
    run_id: str | None = None,
    iteration: int | None = None,
) -> str:
    """Ask the agent for a function. Pass in any prior failures.

    Each call is logged as an ``llm_call`` event with latency and the full
    prompt/response, so runs can be inspected after the fact.
    """
    prompt = build_prompt(spec, tests, history)
    start = time.perf_counter()
    base = {
        "run_id": run_id,
        "iteration": iteration,
        "provider": type(agent).__name__,
        "model": agent.model,
        "prompt_chars": len(prompt),
        "prompt": prompt,
    }
    try:
        raw = agent.complete(prompt)
    except Exception as e:
        log_event(
            "llm_call",
            ok=False,
            latency_ms=round((time.perf_counter() - start) * 1000, 1),
            error=repr(e),
            **base,
        )
        raise
    response = strip_code_fences(raw)
    log_event(
        "llm_call",
        ok=True,
        latency_ms=round((time.perf_counter() - start) * 1000, 1),
        response_chars=len(response),
        response=response,
        # keep the raw model output so we can see when a fence was stripped
        fence_stripped=(response != raw),
        raw_response=raw,
        **base,
    )
    return response


def run_tests(code: str, tests: str) -> tuple[bool, str]:
    """Write code + tests to a temp file, run pytest, return (passed, output)."""
    with tempfile.NamedTemporaryFile(
        mode="w", suffix=".py", delete=False
    ) as f:
        f.write(code + "\n\n" + tests)
        path = f.name
    try:
        result = subprocess.run(
            ["python", "-m", "pytest", path, "-q", "--tb=short"],
            capture_output=True,
            text=True,
            timeout=30,
        )
        return result.returncode == 0, result.stdout + result.stderr
    finally:
        Path(path).unlink()
