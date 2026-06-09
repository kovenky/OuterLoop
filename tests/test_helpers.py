"""Tests for src/helpers.py — currently the fence-stripping safeguard.

Models routinely wrap code in markdown fences despite being told not to. If the
fence reaches the file we run, pytest fails with a SyntaxError before the code
is ever executed (the bug these tests guard against).
"""
from src.helpers import strip_code_fences


def test_strips_python_fence():
    assert strip_code_fences("```python\nx = 1\n```") == "x = 1"


def test_strips_bare_fence():
    assert strip_code_fences("```\nx = 1\n```") == "x = 1"


def test_no_fence_is_unchanged():
    code = "def f():\n    return 1"
    assert strip_code_fences(code) == code


def test_surrounding_whitespace_is_ignored():
    assert strip_code_fences("\n  ```python\nx = 1\n```  \n") == "x = 1"


def test_multiline_body_preserved_and_no_fence_leaks():
    # The exact shape seen in the failing run's logs.
    src = (
        "```python\n"
        "from datetime import datetime\n"
        "\n"
        "def parse_log_line(line):\n"
        "    return line\n"
        "```"
    )
    out = strip_code_fences(src)
    assert "```" not in out
    assert out.startswith("from datetime import datetime")
    assert out.endswith("return line")
