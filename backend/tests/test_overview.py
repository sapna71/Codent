from app.processing.file_filter import SourceFile
from app.processing.overview import build_repo_overview, overview_chunk


def _sf(path):
    return SourceFile(path=path, language="python", content="x = 1")


def test_build_repo_overview_groups_by_top_dir():
    files = [_sf("app/main.py"), _sf("app/github.py"), _sf("tests/test_main.py")]
    overview = build_repo_overview(files)
    assert "3 source files" in overview
    assert "app/ (2 files)" in overview
    assert "tests/ (1 files)" in overview
    assert "app/main.py" in overview


def test_build_repo_overview_truncates_long_dirs():
    files = [_sf(f"app/file_{i}.py") for i in range(30)]
    overview = build_repo_overview(files)
    assert "... and 15 more" in overview


def test_overview_chunk_is_a_valid_chunk():
    c = overview_chunk("some overview text")
    assert c.kind == "overview"
    assert c.code == "some overview text"