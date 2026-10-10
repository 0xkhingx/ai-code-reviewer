"""Secret redaction: scrub credentials from diffs BEFORE any LLM call.

Runs locally, no network. Never log or return the original secret.
"""
import re

_PATTERNS = [
    # AWS access key IDs, GitHub tokens, Slack tokens, generic JWT-ish blobs
    r"AKIA[0-9A-Z]{16}",
    r"gh[pousr]_[A-Za-z0-9_]{16,}",
    r"xox[bpars]-[A-Za-z0-9-]{10,}",
    r"eyJ[A-Za-z0-9_-]{10,}\.[A-Za-z0-9_-]{10,}\.[A-Za-z0-9_-]{10,}",
    # PEM blocks (private keys) — multiline
    r"-----BEGIN [A-Z ]*PRIVATE KEY-----[\s\S]*?-----END [A-Z ]*PRIVATE KEY-----",
    # Assignments like password = "value", api_key: 'value' (quoted values only)
    r"(?i)(password|passwd|secret|api[_-]?key|auth[_-]?token|access[_-]?token)\s*[:=]\s*[\"'][^\"']+[\"']",
]


def redact(text: str) -> tuple[str, int]:
    """Return (scrubbed_text, count_of_redactions)."""
    count = 0
    for pattern in _PATTERNS:
        text, n = re.subn(pattern, "[REDACTED]", text)
        count += n
    return text, count
