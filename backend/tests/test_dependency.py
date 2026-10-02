from app.processing.file_filter import SourceFile
from app.processing.dependency import build_dependency_graph, get_affected_files


def _sf(path, content):
    return SourceFile(path=path, language="python", content=content)


def test_absolute_import_detected():
    files = [
        _sf("app/chunker.py", "def chunk(): pass"),
        _sf("app/main.py", "from app.chunker import chunk\n\nchunk()"),
    ]
    graph = build_dependency_graph(files)
    assert len(graph.edges) == 1
    edge = graph.edges[0]
    assert edge.importer == "app/main.py"
    assert edge.imported == "app/chunker.py"
    assert "from app.chunker import chunk" in edge.statement


def test_relative_import_detected():
    files = [
        _sf("app/processing/chunker.py", "def chunk(): pass"),
        _sf("app/processing/embedder.py", "from .chunker import chunk\n"),
    ]
    graph = build_dependency_graph(files)
    assert any(e.imported == "app/processing/chunker.py" for e in graph.edges)


def test_external_import_ignored():
    files = [_sf("app/main.py", "import os\nimport numpy as np\n")]
    graph = build_dependency_graph(files)
    assert graph.edges == []


def test_affected_files_multi_hop():
    files = [
        _sf("app/core.py", "def core(): pass"),
        _sf("app/service.py", "from app.core import core\n"),
        _sf("app/api.py", "from app.service import core\n"),  # re-exported in practice; fine for this test
    ]
    graph = build_dependency_graph(files)
    affected = get_affected_files(graph, "app/core.py", max_depth=2)
    names_by_depth = {a["file"]: a["depth"] for a in affected}
    assert names_by_depth["app/service.py"] == 1
    assert names_by_depth["app/api.py"] == 2
    api_result = next(a for a in affected if a["file"] == "app/api.py")
    assert len(api_result["evidence"]) == 2  # full chain back to core.py


def test_affected_files_no_dependents():
    files = [_sf("app/lonely.py", "x = 1")]
    graph = build_dependency_graph(files)
    assert get_affected_files(graph, "app/lonely.py") == []