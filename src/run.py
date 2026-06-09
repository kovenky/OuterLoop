# run.py
from src.loop import loop

spec = (
    "Implement `parse_log_line(line)` that parses a line of the form "
    "'YYYY-MM-DD HH:MM:SS LEVEL message' and returns a dict with keys "
    "`timestamp` (datetime), `level` (str, uppercase), and `message` (str). "
    "Raise ValueError on malformed input."
)

tests = """
from datetime import datetime

def test_basic():
    r = parse_log_line("2025-01-15 14:23:01 INFO server started")
    assert r["timestamp"] == datetime(2025, 1, 15, 14, 23, 1)
    assert r["level"] == "INFO"
    assert r["message"] == "server started"

def test_uppercase_level():
    r = parse_log_line("2025-01-15 14:23:01 warning slow query")
    assert r["level"] == "WARNING"

def test_malformed_raises():
    import pytest
    with pytest.raises(ValueError):
        parse_log_line("not a log line")
"""

result = loop(spec, tests)

print(f"status: {result['status']}, iterations: {result['iterations']}")

if result["status"] == "success":
    print(result["code"])
