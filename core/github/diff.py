import httpx

from core.github.auth import API, HEADERS

MAX_PAGES = 10


def fetch_pr_files(
    client: httpx.Client,
    token: str,
    repo_full_name: str,
    pr_number: int,
    per_page: int = 100,
    max_pages: int = MAX_PAGES,
) -> list[dict]:
    """Fetch per-file diff entries via the Files API (paginated).

    Returns list of {filename, additions, deletions, patch, status}.
    Uses page loop; stops early when a page is short (last page).
    """
    files: list[dict] = []
    headers = {**HEADERS, "Authorization": f"Bearer {token}"}
    for page in range(1, max_pages + 1):
        resp = client.get(
            f"{API}/repos/{repo_full_name}/pulls/{pr_number}/files",
            headers=headers,
            params={"per_page": per_page, "page": page},
        )
        resp.raise_for_status()
        batch = resp.json()
        for f in batch:
            files.append(
                {
                    "filename": f.get("filename", "?"),
                    "additions": int(f.get("additions", 0)),
                    "deletions": int(f.get("deletions", 0)),
                    "patch": f.get("patch"),
                    "status": f.get("status", ""),
                }
            )
        if len(batch) < per_page:
            break
    return files


def summarize_files(
    files: list[dict], head_sha: str, max_files: int = 20, max_chars: int = 6000
) -> str:
    """Build a deterministic markdown summary (no LLM). Truncates large PRs."""
    short = (head_sha or "")[:7]
    if not files:
        return f"Review bot saw commit `{short}`: no files changed."

    total_add = sum(f["additions"] for f in files)
    total_del = sum(f["deletions"] for f in files)
    lines = [
        f"Review bot saw commit `{short}`: {len(files)} file(s), +{total_add} -{total_del}."
    ]

    shown = files[:max_files]
    for f in shown:
        # Note: patch is None for binary/too-large files; counts still valid.
        tag = " (binary/large, no patch)" if f["patch"] is None else ""
        lines.append(f"- `{f['filename']}` +{f['additions']} -{f['deletions']}{tag}")

    omitted = len(files) - len(shown)
    if omitted > 0:
        lines.append(f"_...and {omitted} more file(s) omitted (showing first {max_files})._")

    body = "\n".join(lines)
    if len(body) > max_chars:
        body = body[:max_chars] + "\n_...truncated for length._"
    return body
