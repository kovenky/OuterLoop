import os

# helpers.py builds a provider at import time, which reads an API key from the
# environment. Tests don't make real calls, so a dummy key is enough to import.
os.environ.setdefault("OPENROUTER_API_KEY", "test-dummy-key")
