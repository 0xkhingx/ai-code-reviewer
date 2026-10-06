import os
from dataclasses import dataclass
from pathlib import Path


@dataclass(frozen=True)
class Settings:
    database_url: str
    github_app_id: str
    github_webhook_secret: str
    github_private_key: str


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
    )
