import httpx

from core.github.auth import API, HEADERS


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
