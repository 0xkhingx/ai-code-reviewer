from core.github import diff as diffmod


class FakeResp:
    def __init__(self, data):
        self._data = data

    def raise_for_status(self):
        return None

    def json(self):
        return self._data


class FakeClient:
    def __init__(self, pages):
        self.pages = pages
        self.calls = []

    def get(self, url, headers=None, params=None):
        self.calls.append({"url": url, "params": params})
        page = params.get("page", 1)
        return FakeResp(self.pages[page - 1])


def test_summarize_empty():
    body = diffmod.summarize_files([], "abc1234567")
    assert "abc1234" in body
    assert "no files changed" in body


def test_summarize_totals_and_binary_tag():
    files = [
        {"filename": "a.py", "additions": 10, "deletions": 2, "patch": "@@ x", "status": "modified"},
        {"filename": "img.png", "additions": 0, "deletions": 0, "patch": None, "status": "added"},
    ]
    body = diffmod.summarize_files(files, "deadbee123")
    assert "2 file(s), +10 -2" in body
    assert "`a.py` +10 -2" in body
    assert "binary/large" in body


def test_summarize_truncates_file_list():
    files = [
        {"filename": f"f{i}.py", "additions": 1, "deletions": 0, "patch": "x", "status": "added"}
        for i in range(25)
    ]
    body = diffmod.summarize_files(files, "sha1234", max_files=20)
    assert "5 more file(s) omitted" in body
    assert "`f0.py`" in body
    assert "`f24.py`" not in body


def test_summarize_truncates_chars():
    files = [
        {"filename": "big.py", "additions": 1, "deletions": 1, "patch": "x", "status": "modified"}
    ]
    body = diffmod.summarize_files(files, "sha1234", max_chars=40)
    assert "truncated for length" in body


def test_fetch_merges_pages_and_stops_on_short_page():
    page1 = [
        {"filename": "a.py", "additions": 3, "deletions": 1, "patch": "p1", "status": "modified"},
        {"filename": "b.py", "additions": 0, "deletions": 0, "patch": None, "status": "added"},
    ]
    client = FakeClient(pages=[page1, []])
    files = diffmod.fetch_pr_files(client, "tok", "o/r", 7, per_page=2, max_pages=5)
    # page1 full (len==per_page) so page2 fetched; page2 empty -> stop
    assert len(files) == 2
    assert files[0]["filename"] == "a.py"
    assert files[1]["patch"] is None
    assert len(client.calls) == 2
    assert "/repos/o/r/pulls/7/files" in client.calls[0]["url"]
