"""Usage caps: per-installation, per-repo, and global daily limits.

One heavy user must never burn the budget for everyone else, so every LLM
call passes three gates. Counters are in-memory (single worker process);
a multi-worker deploy must move these to Postgres — see ADR-006.
"""
import time

_counters: dict[tuple[str, str], list[float]] = {}


def _day() -> str:
    return time.strftime("%Y-%m-%d", time.gmtime())


def allow(scope: str, key: str, limit: int) -> bool:
    """Record one use and return True if within the daily limit."""
    now = time.time()
    bucket = _counters.setdefault((scope, key), [])
    cutoff = now - 86400
    while bucket and bucket[0] < cutoff:
        bucket.pop(0)
    if len(bucket) >= limit:
        return False
    bucket.append(now)
    return True


def check_caps(
    installation_id: int,
    repo_full_name: str,
    per_install_limit: int = 200,
    per_repo_limit: int = 100,
    global_limit: int = 1000,
) -> str | None:
    """Return None if allowed, else the name of the exhausted cap."""
    day = _day()
    if not allow("global", day, global_limit):
        return "global"
    if not allow("install", f"{installation_id}:{day}", per_install_limit):
        return "installation"
    if not allow("repo", f"{repo_full_name}:{day}", per_repo_limit):
        return "repo"
    return None
