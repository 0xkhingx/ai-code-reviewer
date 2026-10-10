import logging

import httpx

from core.config import load_settings
from core.github.auth import installation_token
from core.github.client import upsert_summary_comment
from core.github.diff import fetch_pr_files, summarize_files
from core.llm.review import resolve_config, review_diff

log = logging.getLogger("review_pr")


def run(payload: dict) -> None:
    """M5: LLM review when a key is configured, else deterministic summary."""
    s = load_settings()
    with httpx.Client(timeout=30) as client:
        token = installation_token(
            client, s.github_app_id, s.github_private_key, payload["installation_id"]
        )
        files = fetch_pr_files(
            client, token, payload["repo_full_name"], payload["pr_number"]
        )
        body = summarize_files(files, payload["head_sha"])
        patches = "\n".join(
            f"--- {f['filename']} ---\n{f['patch'] or '[no patch]'}"
            for f in files
            if f["patch"]
        )
        config = resolve_config(
            payload["installation_id"],
            env_provider=s.llm_provider,
            env_model=s.llm_model,
            env_api_key=s.llm_api_key,
        )
        if config is not None and patches:
            try:
                body = review_diff(
                    patches,
                    config,
                    installation_id=payload["installation_id"],
                    repo_full_name=payload["repo_full_name"],
                    max_input_chars=s.llm_max_input_chars,
                    max_output_tokens=s.llm_max_output_tokens,
                )
            except Exception as exc:  # noqa: BLE001 - LLM is best-effort; keep summary
                log.warning("llm review failed, using summary: %r", exc)
        upsert_summary_comment(
            client,
            token,
            payload["repo_full_name"],
            payload["pr_number"],
            body,
        )
