# providers.py
"""LLM provider adapters.

Each adapter exposes the same method, ``complete(prompt) -> str``, so the rest
of the code never needs to know which provider or SDK is behind it.

Select a provider with the ``LLM_PROVIDER`` environment variable
(``openrouter`` | ``openai`` | ``anthropic``). Override the model with
``LLM_MODEL``. SDKs are imported lazily, so you only need the one you use.
"""
import os

MAX_TOKENS = 2048


class OpenAICompatibleProvider:
    """Chat-completions API shared by OpenAI, OpenRouter, and friends."""

    def __init__(self, api_key: str, model: str, base_url: str | None = None):
        from openai import OpenAI

        self.client = OpenAI(api_key=api_key, base_url=base_url)
        self.model = model

    def complete(self, prompt: str) -> str:
        response = self.client.chat.completions.create(
            model=self.model,
            max_tokens=MAX_TOKENS,
            messages=[{"role": "user", "content": prompt}],
        )
        return response.choices[0].message.content.strip()


class AnthropicProvider:
    """Anthropic's native messages API."""

    def __init__(self, api_key: str, model: str):
        import anthropic

        self.client = anthropic.Anthropic(api_key=api_key)
        self.model = model

    def complete(self, prompt: str) -> str:
        message = self.client.messages.create(
            model=self.model,
            max_tokens=MAX_TOKENS,
            messages=[{"role": "user", "content": prompt}],
        )
        return message.content[0].text.strip()


def get_provider():
    """Build the provider chosen by the LLM_PROVIDER environment variable."""
    name = os.environ.get("LLM_PROVIDER", "openrouter").lower()

    if name == "openrouter":
        return OpenAICompatibleProvider(
            api_key=os.environ["OPENROUTER_API_KEY"],
            base_url="https://openrouter.ai/api/v1",
            model=os.environ.get("LLM_MODEL", "anthropic/claude-sonnet-4.5"),
        )
    if name == "openai":
        return OpenAICompatibleProvider(
            api_key=os.environ["OPENAI_API_KEY"],
            model=os.environ.get("LLM_MODEL", "gpt-4o"),
        )
    if name == "anthropic":
        return AnthropicProvider(
            api_key=os.environ["ANTHROPIC_API_KEY"],
            model=os.environ.get("LLM_MODEL", "claude-sonnet-4-6"),
        )

    raise ValueError(
        f"Unknown LLM_PROVIDER: {name!r}. "
        "Use 'openrouter', 'openai', or 'anthropic'."
    )
