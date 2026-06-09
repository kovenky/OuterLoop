# loop.py
"""The self-correcting loop: ask the agent, run the tests, retry on failure."""
from src.helpers import ask_agent, run_tests


def loop(spec: str, tests: str, max_iters: int = 5) -> dict:
    """Generate code until it passes the tests or max_iters is reached."""
    
    # Keep track of the history of code and outputs for debugging and analysis.
    history = []

    # Loop until we either succeed or reach the maximum iterations.
    for i in range(max_iters):

        code = ask_agent(spec, tests, history)
        passed, output = run_tests(code, tests)
        
        # If the tests passed, we can return the successful code and the number of iterations it took.
        if passed:
            return {
                "status": "success",
                "iterations": i + 1,
                "code": code,
            }
        
        # If the tests failed, we record the code and its output for future iterations to learn from.
        history.append({"code": code, "output": output})

    # If we exhaust all iterations without success, we return the history for analysis.
    return {
        "status": "failed",
        "iterations": max_iters,
        "history": history,
    }
