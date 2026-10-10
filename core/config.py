import os
from dataclasses import dataclass
from pathlib import Path


@dataclass(frozen=True)
class Settings:
    database_url: str
    github_app_id: str
    github_webhook_secret: str
    github_private_key: str
    # BYOK LLM (all optional; empty = deterministic summary only, $0).
    llm_provider: str
    llm_model: str
    llm_api_key: str
    llm_max_input_chars: int
    llm_max_output_tokens: int


def load_settings() -> Settings:
    key = os.environ.get("GITHUB_PRIVATE_KEY", "")
    key_path = os.environ.get("GITHUB_PRIVATE_KEY_PATH")
    if not key and key_path and Path(key_path).exists():
        key = Path(key_path).read_text()
    return Settings(
        database_url=os.environ.get(
            "DATABASE_URL", "postgresql://reviewer:reviewer@localhost:5432/reviewer"
        ),
        github_app_id=os.environ.get("GITHUB_APP_ID", ""),
        github_webhook_secret=os.environ.get("GITHUB_WEBHOOK_SECRET", ""),
        github_private_key=key.replace("\\n", "\n"),
        llm_provider=os.environ.get("LLM_PROVIDER", ""),
        llm_model=os.environ.get("LLM_MODEL", "gpt-6-luna"),
        llm_api_key=os.environ.get("LLM_API_KEY", ""),
        llm_max_input_chars=int(os.environ.get("LLM_MAX_INPUT_CHARS", "60000")),
        llm_max_output_tokens=int(os.environ.get("LLM_MAX_OUTPUT_TOKENS", "1500")),
    )
