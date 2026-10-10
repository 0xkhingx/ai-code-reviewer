import time

from core.github import auth as authmod
from core.github.client import COMMENT_MARKER, upsert_summary_comment


class FakeResp:
    def __init__(self, data):
        self._data = data

    def raise_for_status(self):
        return None

    def json(self):
        return self._data


class FakeClient:
    def __init__(self, get_pages=None, post_token="tok"):
        self.get_pages = get_pages or [[]]
        self.calls = []
        self.post_token = post_token

    def get(self, url, headers=None, params=None):
        self.calls.append(("GET", url, params))
        page = (params or {}).get("page", 1)
        return FakeResp(self.get_pages[page - 1])

    def post(self, url, headers=None, json=None):
        self.calls.append(("POST", url, json))
        if "access_tokens" in url:
            return FakeResp(
                {"token": self.post_token, "expires_at": "2099-01-01T00:00:00Z"}
            )
        return FakeResp({})

    def patch(self, url, headers=None, json=None):
        self.calls.append(("PATCH", url, json))
        return FakeResp({})


def test_upsert_creates_when_no_marker():
    client = FakeClient(get_pages=[[{"id": 1, "body": "human comment"}]])
    result = upsert_summary_comment(client, "t", "o/r", 7, "summary")
    assert result == "created"
    posts = [c for c in client.calls if c[0] == "POST"]
    assert len(posts) == 1
    assert COMMENT_MARKER in posts[0][2]["body"]


def test_upsert_updates_existing_marker_comment():
    mine = {"id": 42, "body": f"{COMMENT_MARKER}\nold summary"}
    client = FakeClient(get_pages=[[mine, {"id": 2, "body": "other"}]])
    result = upsert_summary_comment(client, "t", "o/r", 7, "new summary")
    assert result == "updated"
    patches = [c for c in client.calls if c[0] == "PATCH"]
    posts = [c for c in client.calls if c[0] == "POST" and "comments" in c[1]]
    assert len(patches) == 1
    assert "/issues/comments/42" in patches[0][1]
    assert "new summary" in patches[0][2]["body"]
    assert posts == []


def test_token_cache_avoids_second_post(monkeypatch):
    monkeypatch.setattr(authmod, "app_jwt", lambda *a: "fake-jwt")
    authmod._TOKEN_CACHE.clear()
    client = FakeClient(post_token="tok123")
    t1 = authmod.installation_token(client, "app", "key", 99)
    t2 = authmod.installation_token(client, "app", "key", 99)
    assert t1 == t2 == "tok123"
    token_posts = [c for c in client.calls if c[0] == "POST"]
    assert len(token_posts) == 1


def test_token_cache_refetches_when_expired(monkeypatch):
    monkeypatch.setattr(authmod, "app_jwt", lambda *a: "fake-jwt")
    authmod._TOKEN_CACHE.clear()
    authmod._TOKEN_CACHE[99] = ("old", time.time() - 10)
    client = FakeClient(post_token="fresh")
    assert authmod.installation_token(client, "app", "key", 99) == "fresh"
    assert len([c for c in client.calls if c[0] == "POST"]) == 1
