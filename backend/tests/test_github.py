import base64

import httpx
import pytest

from app.github import (
    RepoRef,
    TreeEntry,
    MAX_FETCHABLE_SIZE,
    GitHubError,
    get_file_content,
    get_repo_info,
    build_blob_url,
)


class FakeResponse:
    def __init__(self, status_code, data):
        self.status_code = status_code
        self._data = data

    def json(self):
        return self._data

    def raise_for_status(self):
        if self.status_code >= 400:
            raise httpx.HTTPStatusError(
                "HTTP error",
                request=None,
                response=None,
            )


def test_get_file_content(monkeypatch):
    encoded = base64.b64encode(
        b"print('hi')"
    ).decode()

    def fake_get(
        url,
        headers=None,
        timeout=None,
        **kwargs,
    ):
        return FakeResponse(
            200,
            {
                "encoding": "base64",
                "content": encoded,
            },
        )

    monkeypatch.setattr(
        "app.github.httpx.get",
        fake_get,
    )

    entry = TreeEntry(
        "app/x.py",
        "blob",
        "sha123",
        20,
    )

    result = get_file_content(
        RepoRef("o", "r"),
        entry,
    )

    assert result == "print('hi')"


def test_get_file_content_too_large():
    entry = TreeEntry(
        "big.bin",
        "blob",
        "sha",
        MAX_FETCHABLE_SIZE + 1,
    )

    result = get_file_content(
        RepoRef("o", "r"),
        entry,
    )

    assert result is None


def test_network_failure_becomes_github_error(monkeypatch):
    # Don't actually wait for retry delays.
    monkeypatch.setattr(
        "app.github.time.sleep",
        lambda s: None,
    )

    def boom(*args, **kwargs):
        raise httpx.RemoteProtocolError("dropped")

    monkeypatch.setattr(
        "app.github.httpx.get",
        boom,
    )

    with pytest.raises(GitHubError):
        get_repo_info(
            RepoRef("o", "r")
        )


def test_build_blob_url():
    url = build_blob_url(
        "pallets",
        "click",
        "main",
        "src/click/core.py",
        120,
        145,
    )

    assert url == (
        "https://github.com/pallets/click/blob/main/"
        "src/click/core.py#L120-L145"
    )