from dataclasses import dataclass
from pathlib import PurePosixPath


LANGUAGES = {
    ".py": "python",
    ".js": "javascript",
    ".jsx": "javascript",
    ".ts": "typescript",
    ".tsx": "typescript",
    ".java": "java",
    ".go": "go",
    ".rs": "rust",
    ".rb": "ruby",
    ".php": "php",
    ".cs": "csharp",
    ".c": "c",
    ".h": "c",
    ".cpp": "cpp",
    ".kt": "kotlin",
    ".swift": "swift",
}


IGNORED_DIRS = {
    ".git",
    "node_modules",
    "venv",
    ".venv",
    "__pycache__",
    "dist",
    "build",
    ".next",
    "vendor",
    "target",
    "coverage",
    ".idea",
    ".vscode",
    "site-packages",
}


IGNORED_SUFFIXES = (
    ".min.js",
    ".d.ts",
    "_pb2.py",
    ".map",
)


MAX_FILE_BYTES = 200_000


@dataclass
class SourceFile:
    path: str
    language: str
    content: str


def filter_source_files(
    files: list[dict],
) -> list[SourceFile]:
    """Keep only useful, text-based source files and tag their language."""

    kept = []

    for f in files:
        path = f["path"].replace("\\", "/")
        content = f.get("content") or ""
        p = PurePosixPath(path)

        language = LANGUAGES.get(
            p.suffix.lower()
        )

        if language is None:
            continue

        if set(p.parts[:-1]) & IGNORED_DIRS:
            continue

        if path.endswith(IGNORED_SUFFIXES):
            continue

        if not content.strip() or "\x00" in content:
            continue

        if len(
            content.encode(
                "utf-8",
                errors="ignore",
            )
        ) > MAX_FILE_BYTES:
            continue

        kept.append(
            SourceFile(
                path=path,
                language=language,
                content=content,
            )
        )

    return kept


def is_candidate_path(path: str) -> bool:
    """
    Cheap path-only check, so we skip downloading
    files we'd discard anyway.
    """

    path = path.replace("\\", "/")
    p = PurePosixPath(path)

    if p.suffix.lower() not in LANGUAGES:
        return False

    if set(p.parts[:-1]) & IGNORED_DIRS:
        return False

    return not path.endswith(IGNORED_SUFFIXES)