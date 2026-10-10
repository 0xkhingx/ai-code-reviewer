"""BYOK review orchestration: resolve key -> caps -> redact -> prompt -> model.

BYOK (bring your own key) means the repo owner plugs in their own provider
key, so firstpass holds no billing risk. No key configured -> raise
RuntimeError and the caller falls back to the deterministic summary.
Costs the operator $0 at any scale.
"""
import httpx

from core.llm import caps
from core.llm import prompt as promptlib
from core.llm.providers import DEFAULT_MODEL, SUPPORTED_MODELS, complete
from core.review.redact import redact


def resolve_config(
    installation_id: int,
    env_provider: str = "",
    env_model: str = "",
    env_api_key: str = "",
    per_install_keys: dict | None = None,
) -> dict | None:
    """Resolve LLM config for an installation. None = no key, use fallback."""
    per_install_keys = per_install_keys or {}
    if installation_id in per_install_keys:
        entry = per_install_keys[installation_id]
        return {
            "provider": entry["provider"],
            "model": entry.get("model", DEFAULT_MODEL),
            "api_key": entry["api_key"],
        }
    if env_api_key and env_provider:
        return {
            "provider": env_provider,
            "model": env_model or DEFAULT_MODEL,
            "api_key": env_api_key,
        }
    return None


def review_diff(
    diff: str,
    config: dict | None,
    installation_id: int = 0,
    repo_full_name: str = "",
    max_input_chars: int = 60000,
    max_output_tokens: int = 1500,
) -> str:
    """Run an LLM review. Returns markdown. Raises RuntimeError to fall back."""
    if config is None:
        raise RuntimeError("no LLM key configured; use deterministic summary")
    provider, model = config["provider"], config["model"]
    if model not in SUPPORTED_MODELS or SUPPORTED_MODELS[model] != provider:
        raise RuntimeError(f"unsupported model for provider: {model}")
    exhausted = caps.check_caps(installation_id, repo_full_name)
    if exhausted:
        raise RuntimeError(f"LLM cap exhausted: {exhausted}; use deterministic summary")
    scrubbed, _ = redact(diff)
    messages = promptlib.build_messages(scrubbed, max_chars=max_input_chars)
    with httpx.Client(timeout=60) as client:
        raw = complete(
            client, provider, config["api_key"], model,
            messages[0]["content"], messages[1]["content"], max_output_tokens,
        )
    findings = promptlib.parse_findings(raw)
    if not findings:
        return "firstpass LLM review: no issues found."
    lines = ["firstpass LLM review:"]
    for f in findings:
        loc = f"{f['file']}:{f['line']}" if f["line"] is not None else f["file"]
        lines.append(f"- [{f['severity']}] `{loc}` — {f['note']}")
    return "\n".join(lines)
