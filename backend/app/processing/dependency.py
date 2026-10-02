import ast
from dataclasses import dataclass, field

from app.processing.file_filter import SourceFile


@dataclass
class ImportEdge:
    importer: str   # file that contains the import statement
    imported: str   # file being imported
    line: int
    statement: str  # the actual source line, for evidence


@dataclass
class DependencyGraph:
    edges: list[ImportEdge] = field(default_factory=list)
    imports: dict[str, list[ImportEdge]] = field(default_factory=dict)       # file -> what it imports
    imported_by: dict[str, list[ImportEdge]] = field(default_factory=dict)   # file -> what imports it


def _module_name(path: str) -> str:
    """Convert a file path to its Python dotted module name."""
    if path.endswith("/__init__.py"):
        path = path[: -len("/__init__.py")]
    elif path.endswith(".py"):
        path = path[:-3]
    return path.replace("/", ".")


def _resolve_relative(current_path: str, level: int, module: str | None) -> str | None:
    """Best-effort resolution of `from . import x` / `from ..pkg import y` style imports."""
    dir_parts = current_path.split("/")[:-1]
    up = level - 1
    if up > 0:
        dir_parts = dir_parts[:-up] if up <= len(dir_parts) else []
    if module:
        dir_parts = dir_parts + module.split(".")
    return ".".join(dir_parts) if dir_parts else None


def build_dependency_graph(source_files: list[SourceFile]) -> DependencyGraph:
    """Parse import statements in every Python file and resolve them to repo files.

    Only Python is supported. Imports of external packages (not found in the
    repo) are silently ignored, since they can't be "affected" by a local change.
    """
    python_files = {f.path: f for f in source_files if f.language == "python"}
    module_map = {_module_name(p): p for p in python_files}

    graph = DependencyGraph()

    def add_edge(importer: str, imported: str, line: int, statement: str) -> None:
        edge = ImportEdge(importer=importer, imported=imported, line=line, statement=statement)
        graph.edges.append(edge)
        graph.imports.setdefault(importer, []).append(edge)
        graph.imported_by.setdefault(imported, []).append(edge)

    for path, source_file in python_files.items():
        try:
            tree = ast.parse(source_file.content)
        except SyntaxError:
            continue
        lines = source_file.content.splitlines()

        for node in ast.walk(tree):
            target_module: str | None = None

            if isinstance(node, ast.Import):
                for alias in node.names:
                    target_module = alias.name
                    target_path = module_map.get(target_module)
                    if target_path and target_path != path:
                        stmt = lines[node.lineno - 1].strip() if node.lineno - 1 < len(lines) else ""
                        add_edge(path, target_path, node.lineno, stmt)
                continue

            if isinstance(node, ast.ImportFrom):
                if node.level and node.level > 0:
                    target_module = _resolve_relative(path, node.level, node.module)
                else:
                    target_module = node.module
                target_path = module_map.get(target_module) if target_module else None
                if target_path and target_path != path:
                    stmt = lines[node.lineno - 1].strip() if node.lineno - 1 < len(lines) else ""
                    add_edge(path, target_path, node.lineno, stmt)

    return graph


def get_affected_files(graph: DependencyGraph, file_path: str, max_depth: int = 2) -> list[dict]:
    """BFS from file_path over 'imported_by' edges: who breaks if this file changes.

    Returns a list of {file, depth, evidence}, where evidence is the chain of
    import statements connecting file_path to that affected file.
    """
    visited = {file_path}
    frontier: list[tuple[str, list[ImportEdge]]] = [(file_path, [])]
    results: list[dict] = []
    depth = 0

    while frontier and depth < max_depth:
        depth += 1
        next_frontier = []
        for node, path_so_far in frontier:
            for edge in graph.imported_by.get(node, []):
                if edge.importer in visited:
                    continue
                visited.add(edge.importer)
                chain = path_so_far + [edge]
                results.append({
                    "file": edge.importer,
                    "depth": depth,
                    "evidence": [f"{e.importer} line {e.line}: {e.statement}" for e in chain],
                })
                next_frontier.append((edge.importer, chain))
        frontier = next_frontier

    return results