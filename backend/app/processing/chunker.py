import ast
from dataclasses import dataclass


MAX_CHUNK_LINES = 100


@dataclass
class Chunk:
    file: str
    name: str          # function/class name, or "<module>" for top-level code
    kind: str          # "function", "class", "module", or "block"
    start_line: int
    end_line: int
    code: str


def chunk_python_file(
    path: str,
    content: str,
) -> list[Chunk]:
    """
    Split a Python file into function/class-level chunks
    with line numbers.
    """

    try:
        tree = ast.parse(content)
    except SyntaxError:
        # Unparsable Python file.
        # Skip it instead of crashing the whole ingestion.
        return []

    lines = content.splitlines()

    chunks: list[Chunk] = []
    covered_lines: set[int] = set()

    for node in ast.walk(tree):

        if isinstance(
            node,
            (
                ast.FunctionDef,
                ast.AsyncFunctionDef,
                ast.ClassDef,
            ),
        ):
            start = node.lineno
            end = getattr(
                node,
                "end_lineno",
                node.lineno,
            )

            if isinstance(node, ast.ClassDef):
                kind = "class"
            else:
                kind = "function"

            code = "\n".join(
                lines[start - 1:end]
            )

            chunks.append(
                Chunk(
                    file=path,
                    name=node.name,
                    kind=kind,
                    start_line=start,
                    end_line=end,
                    code=code,
                )
            )

            covered_lines.update(
                range(start, end + 1)
            )

    # Anything not inside a function/class:
    # imports, constants, top-level statements, etc.
    leftover_lines = [
        i
        for i in range(1, len(lines) + 1)
        if i not in covered_lines
    ]

    if leftover_lines:
        start = leftover_lines[0]
        end = leftover_lines[-1]

        code = "\n".join(
            lines[i - 1]
            for i in leftover_lines
        )

        if code.strip():
            chunks.append(
                Chunk(
                    file=path,
                    name="<module>",
                    kind="module",
                    start_line=start,
                    end_line=end,
                    code=code,
                )
            )

    return chunks


def chunk_generic_file(
    path: str,
    content: str,
) -> list[Chunk]:
    """
    Fallback for non-Python files.

    Splits the file into fixed-size blocks of
    MAX_CHUNK_LINES lines.
    """

    lines = content.splitlines()

    if not lines:
        return []

    chunks: list[Chunk] = []

    for i in range(
        0,
        len(lines),
        MAX_CHUNK_LINES,
    ):
        block = lines[
            i:i + MAX_CHUNK_LINES
        ]

        start = i + 1
        end = i + len(block)

        chunks.append(
            Chunk(
                file=path,
                name=f"lines_{start}-{end}",
                kind="block",
                start_line=start,
                end_line=end,
                code="\n".join(block),
            )
        )

    return chunks


def chunk_file(
    path: str,
    language: str,
    content: str,
) -> list[Chunk]:
    """
    Entry point for chunking a file.

    Uses AST-based chunking for Python.
    Uses fixed-size line blocks for other languages.
    """

    if language == "python":
        return chunk_python_file(
            path,
            content,
        )

    return chunk_generic_file(
        path,
        content,
    )