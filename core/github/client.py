import httpx

from core.github.auth import API, HEADERS

COMMENT_MARKER = "<!-- firstpass:pr-summary -->"


def post_issue_comment(
    client: httpx.Client, token: str, repo_full_name: str, pr_number: int, body: str
) -> None:
    """PRs are issues too, so a plain PR comment goes through the issues endpoint."""
    resp = client.post(
        f"{API}/repos/{repo_full_name}/issues/{pr_number}/comments",
        headers={**HEADERS, "Authorization": f"Bearer {token}"},
        json={"body": body},
    )
    resp.raise_for_status()


def list_issue_comments(
    client: httpx.Client, token: str, repo_full_name: str, pr_number: int
) -> list[dict]:
    """List comments on a PR (paginated). Returns [{id, body}]."""
    headers = {**HEADERS, "Authorization": f"Bearer {token}"}
    comments: list[dict] = []
    page = 1
    while True:
        resp = client.get(
            f"{API}/repos/{repo_full_name}/issues/{pr_number}/comments",
            headers=headers,
            params={"per_page": 100, "page": page},
        )
        resp.raise_for_status()
        batch = resp.json()
        comments.extend({"id": c["id"], "body": c.get("body", "")} for c in batch)
        if len(batch) < 100:
            break
        page += 1
    return comments


def upsert_summary_comment(
    client: httpx.Client, token: str, repo_full_name: str, pr_number: int, body: str
) -> str:
    """Create our summary comment, or update it if a previous run posted one.

    Retries re-run the same job, so without this each attempt spams a new
    comment. The marker lets us find our own comment and edit it in place.
    Returns "created" or "updated".
    """
    if COMMENT_MARKER not in body:
        body = f"{COMMENT_MARKER}\n{body}"
    headers = {**HEADERS, "Authorization": f"Bearer {token}"}
    for comment in list_issue_comments(client, token, repo_full_name, pr_number):
        if COMMENT_MARKER in comment["body"]:
            resp = client.patch(
                f"{API}/repos/{repo_full_name}/issues/comments/{comment['id']}",
                headers=headers,
                json={"body": body},
            )
            resp.raise_for_status()
            return "updated"
    post_issue_comment(client, token, repo_full_name, pr_number, body)
    return "created"
