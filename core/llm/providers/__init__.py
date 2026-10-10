"""Provider dispatcher. Supported models and their providers."""
from core.llm.providers import anthropic as _anthropic
from core.llm.providers import openai as _openai

DEFAULT_MODEL = "gpt-6-luna"
SUPPORTED_MODELS = {
    "gpt-6-luna": "openai",
    "claude-haiku-5-5": "anthropic",
}


def complete(client, provider, api_key, model, system, user, max_output_tokens=1500):
    if provider == "openai":
        return _openai.complete(client, api_key, model, system, user, max_output_tokens)
    if provider == "anthropic":
        return _anthropic.complete(client, api_key, model, system, user, max_output_tokens)
    raise ValueError(f"unsupported provider: {provider}")
