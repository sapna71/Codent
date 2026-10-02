from collections import defaultdict

from app.processing.chunker import Chunk
from app.processing.file_filter import SourceFile

MAX_OVERVIEW_CHARS = 3000
MAX_FILES_PER_DIR = 15


def build_repo_overview(source_files: list[SourceFile]) -> str:
    """A directory-level summary of the repo: what's where, roughly how big.

    This gives the LLM structural context that similarity search alone can't
    provide, useful for broad questions like "explain this repository".
    """
    by_dir: dict[str, list[str]] = defaultdict(list)
    for f in source_files:
        parts = f.path.split("/")
        top_dir = parts[0] if len(parts) > 1 else "(root)"
        by_dir[top_dir].append(f.path)

    lines = [
        f"Repository contains {len(source_files)} source files "
        f"across {len(by_dir)} top-level directories.",
        "",
    ]
    for directory, paths in sorted(by_dir.items()):
        lines.append(f"{directory}/ ({len(paths)} files)")
        for p in sorted(paths)[:MAX_FILES_PER_DIR]:
            lines.append(f"  - {p}")
        if len(paths) > MAX_FILES_PER_DIR:
            lines.append(f"  ... and {len(paths) - MAX_FILES_PER_DIR} more")

    return "\n".join(lines)[:MAX_OVERVIEW_CHARS]


def overview_chunk(overview_text: str) -> Chunk:
    """Wrap the overview as a pseudo-chunk so it can flow through the same
    citation and prompt-building code paths as real code chunks."""
    return Chunk(file="<repository>", name="overview", kind="overview",
                 start_line=0, end_line=0, code=overview_text)