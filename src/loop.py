# loop.py
"""The self-correcting loop: ask the agent, run the tests, retry on failure."""
from src.helpers import ask_agent, run_tests
from src.observability import log_event, new_run_id


def loop(spec: str, tests: str, max_iters: int = 5) -> dict:
    """Generate code until it passes the tests or max_iters is reached."""

    # A run_id ties every log record from this call together.
    run_id = new_run_id()
    log_event("run_start", run_id=run_id, max_iters=max_iters, spec=spec)

    # Keep track of the history of code and outputs for debugging and analysis.
    history = []

    # Loop until we either succeed or reach the maximum iterations.
    for i in range(max_iters):

        code = ask_agent(spec, tests, history, run_id=run_id, iteration=i + 1)
        passed, output = run_tests(code, tests)

        # Record what this iteration produced.
        log_event(
            "iteration",
            run_id=run_id,
            iteration=i + 1,
            passed=passed,
            code=code,
            output=output,
        )

        # If the tests passed, we can return the successful code and the number of iterations it took.
        if passed:
            log_event("run_end", run_id=run_id, status="success", iterations=i + 1)
            return {
                "status": "success",
                "iterations": i + 1,
                "code": code,
            }

        # If the tests failed, we record the code and its output for future iterations to learn from.
        history.append({"code": code, "output": output})

    # If we exhaust all iterations without success, we return the history for analysis.
    log_event("run_end", run_id=run_id, status="failed", iterations=max_iters)
    return {
        "status": "failed",
        "iterations": max_iters,
        "history": history,
    }
