import os
import re
import base64
import time
from dataclasses import dataclass
from urllib.parse import urlparse

import httpx

from app.processing.file_filter import is_candidate_path


GITHUB_API = "https://api.github.com"

OWNER_RE = re.compile(
    r"^[A-Za-z0-9](?:[A-Za-z0-9-]{0,38})$"
)

REPO_RE = re.compile(
    r"^[A-Za-z0-9._-]{1,100}$"
)

MAX_FETCHABLE_SIZE = 200_000
MAX_FILES = int(os.environ.get("MAX_FILES", "300"))


# ============================================================
# 1. Repository URL
# ============================================================

@dataclass(frozen=True)
class RepoRef:
    owner: str
    name: str


def parse_github_url(url: str) -> RepoRef:
    parsed = urlparse(url.strip())

    if (
        parsed.scheme not in ("http", "https")
        or parsed.netloc.lower() not in (
            "github.com",
            "www.github.com",
        )
    ):
        raise ValueError("Not a github.com URL")

    parts = [
        p
        for p in parsed.path.split("/")
        if p
    ]

    if len(parts) < 2:
        raise ValueError(
            "URL must look like https://github.com/owner/repo"
        )

    owner, name = parts[0], parts[1]

    if name.endswith(".git"):
        name = name[:-4]

    if (
        not OWNER_RE.match(owner)
        or not REPO_RE.match(name)
        or name in (".", "..")
    ):
        raise ValueError(
            "Invalid owner or repository name"
        )

    return RepoRef(
        owner=owner,
        name=name,
    )


# ============================================================
# 2. Repository information
# ============================================================

@dataclass(frozen=True)
class RepoInfo:
    owner: str
    name: str
    default_branch: str
    description: str | None


# ============================================================
# 3. File tree entry
# ============================================================

@dataclass(frozen=True)
class TreeEntry:
    path: str
    type: str
    sha: str
    size: int | None


# ============================================================
# 4. Custom GitHub error
# ============================================================

class GitHubError(Exception):
    pass


# ============================================================
# 5. GitHub request headers
# ============================================================

def _headers() -> dict:
    headers = {
        "Accept": "application/vnd.github+json"
    }

    token = os.environ.get("GITHUB_TOKEN")

    if token:
        headers["Authorization"] = f"Bearer {token}"

    return headers


def _get(
    url: str,
    retries: int = 3,
    **kwargs,
) -> httpx.Response:
    """
    Send a GET request to GitHub with retries.

    Network failures are converted into GitHubError.
    """

    for attempt in range(retries):
        try:
            return httpx.get(
                url,
                headers=_headers(),
                **kwargs,
            )

        except httpx.TransportError as e:
            if attempt == retries - 1:
                raise GitHubError(
                    f"Network error talking to GitHub: {e}"
                ) from e

            time.sleep(2 ** attempt)


# ============================================================
# 6. Get repository information
# ============================================================

def get_repo_info(ref: RepoRef) -> RepoInfo:
    url = (
        f"{GITHUB_API}/repos/"
        f"{ref.owner}/{ref.name}"
    )

    resp = _get(
        url,
        timeout=10,
    )

    if resp.status_code == 404:
        raise GitHubError(
            f"Repository {ref.owner}/{ref.name} not found"
        )

    if resp.status_code == 403:
        raise GitHubError(
            "GitHub API rate limit exceeded or access forbidden"
        )

    resp.raise_for_status()

    data = resp.json()

    return RepoInfo(
        owner=ref.owner,
        name=ref.name,
        default_branch=data["default_branch"],
        description=data.get("description"),
    )


# ============================================================
# 7. Get repository file tree
# ============================================================

def get_file_tree(
    ref: RepoRef,
    branch: str,
) -> list[TreeEntry]:

    url = (
        f"{GITHUB_API}/repos/"
        f"{ref.owner}/{ref.name}/git/trees/{branch}"
    )

    resp = _get(
        url,
        params={"recursive": "1"},
        timeout=15,
    )

    if resp.status_code == 404:
        raise GitHubError(
            f"Branch '{branch}' not found"
        )

    if resp.status_code == 403:
        raise GitHubError(
            "GitHub API rate limit exceeded or access forbidden"
        )

    resp.raise_for_status()

    data = resp.json()

    return [
        TreeEntry(
            path=entry["path"],
            type=entry["type"],
            sha=entry["sha"],
            size=entry.get("size"),
        )
        for entry in data["tree"]
        if entry["type"] == "blob"
    ]


# ============================================================
# 8. Get one file's actual content
# ============================================================

def get_file_content(
    ref: RepoRef,
    entry: TreeEntry,
) -> str | None:
    """
    Fetch and decode one file's content.

    Returns:
        str  -> if the file is valid UTF-8 text
        None -> if the file is too large, binary, or unavailable
    """

    # Skip huge files before making the API request.
    if (
        entry.size is not None
        and entry.size > MAX_FETCHABLE_SIZE
    ):
        return None

    url = (
        f"{GITHUB_API}/repos/"
        f"{ref.owner}/{ref.name}/git/blobs/{entry.sha}"
    )

    resp = _get(
        url,
        timeout=15,
    )

    if resp.status_code == 404:
        return None

    resp.raise_for_status()

    data = resp.json()

    # GitHub should return blob content encoded as base64.
    if data.get("encoding") != "base64":
        return None

    raw = base64.b64decode(
        data["content"]
    )

    try:
        return raw.decode("utf-8")

    except UnicodeDecodeError:
        # Probably a binary file.
        return None


# ============================================================
# 9. Build GitHub source permalink
# ============================================================

def build_blob_url(
    owner: str,
    name: str,
    branch: str,
    path: str,
    start_line: int,
    end_line: int,
) -> str:
    """
    Build a GitHub permalink to the exact lines
    a chunk came from.
    """

    return (
        f"https://github.com/"
        f"{owner}/{name}/blob/{branch}/{path}"
        f"#L{start_line}-L{end_line}"
    )


# ============================================================
# 10. Get candidate source files only
# ============================================================

def get_repo_files(
    ref: RepoRef,
) -> tuple[RepoInfo, list[dict]]:
    """
    Full repository fetching pipeline:

    1. Get repository information
    2. Get repository file tree
    3. Keep only candidate source files
    4. Limit the number of files
    5. Fetch each candidate file's content
    6. Skip huge/binary/unavailable files

    Returns:
        (
            RepoInfo,
            [
                {
                    "path": "...",
                    "content": "..."
                }
            ]
        )
    """

    # Step 1:
    # Get repository information.
    info = get_repo_info(ref)

    # Step 2:
    # Get all files from the repository.
    # Then keep only files that look like source files.
    entries = [
        entry
        for entry in get_file_tree(
            ref,
            info.default_branch,
        )
        if is_candidate_path(entry.path)
    ][:MAX_FILES]

    # Step 3:
    # Fetch actual content for each candidate file.
    files = []

    for entry in entries:
        content = get_file_content(
            ref,
            entry,
        )

        # None means:
        # - too large
        # - binary
        # - unavailable
        if content is not None:
            files.append(
                {
                    "path": entry.path,
                    "content": content,
                }
            )

    return info, files