# helpers.py
"""Supporting functions: prompt building, the agent call, and test running."""
import subprocess
import tempfile
from pathlib import Path

from src.providers import get_provider

PROMPT_TEMPLATE = Path(__file__).with_name("prompt.txt").read_text()

agent = get_provider()


def format_history(history: list[dict]) -> str:
    """Render previous failed attempts as text to append to the prompt."""
    if not history:
        return ""
    attempts = []
    for i, attempt in enumerate(history, 1):
        attempts.append(
            f"Attempt {i}:\n```python\n{attempt['code']}\n```\n"
            f"Test output:\n{attempt['output']}"
        )
    return "\n\nPrevious attempts:\n" + "\n\n".join(attempts)


def build_prompt(spec: str, tests: str, history: list[dict]) -> str:
    """Fill the prompt template with the spec, tests, and prior attempts."""
    return (
        PROMPT_TEMPLATE
        .replace("{spec}", spec)
        .replace("{tests}", tests)
        .replace("{history}", format_history(history))
    )


def ask_agent(spec: str, tests: str, history: list[dict]) -> str:
    """Ask the agent for a function. Pass in any prior failures."""
    prompt = build_prompt(spec, tests, history)
    return agent.complete(prompt)


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
