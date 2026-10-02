from app.processing.chunker import Chunk

from app.processing.embedder import (
    EMBEDDING_DIM,
    EmbeddedChunk,
)

from app.processing.vector_store import (
    build_index,
    get_repo_meta,
    get_repo_overview,
    get_dependency_graph,
    has_index,
    search_index,
)


def unit(i):
    v = [0.0] * EMBEDDING_DIM
    v[i] = 1.0
    return v


def test_build_and_search():
    embedded = [
        EmbeddedChunk(
            Chunk(
                "auth.py",
                "authenticate_user",
                "function",
                1,
                5,
                "...",
            ),
            unit(0),
        ),
        EmbeddedChunk(
            Chunk(
                "checkout.py",
                "process_order",
                "function",
                1,
                5,
                "...",
            ),
            unit(1),
        ),
    ]

    build_index(
        "test/repo",
        embedded,
        owner="pallets",
        name="click",
        branch="main",
    )

    assert has_index("test/repo")

    results = search_index(
        "test/repo",
        unit(0),
        top_k=1,
    )

    assert results[0].name == "authenticate_user"


def test_get_repo_meta():
    build_index(
        "test/meta",
        [
            EmbeddedChunk(
                Chunk(
                    "a.py",
                    "f",
                    "function",
                    1,
                    2,
                    "x",
                ),
                unit(0),
            )
        ],
        owner="o",
        name="r",
        branch="dev",
    )

    assert get_repo_meta("test/meta") == (
        "o",
        "r",
        "dev",
    )


def test_search_missing_repo_raises():
    try:
        search_index(
            "nonexistent/repo",
            [0.0] * EMBEDDING_DIM,
            top_k=1,
        )

        assert False, "should have raised"

    except KeyError:
        pass


def test_overview_round_trip():
    build_index(
        "test/overview",
        [
            EmbeddedChunk(
                Chunk(
                    "a.py",
                    "f",
                    "function",
                    1,
                    2,
                    "x",
                ),
                unit(0),
            )
        ],
        owner="o",
        name="r",
        branch="main",
        overview="Repo has 1 file.",
    )

    assert (
        get_repo_overview("test/overview")
        == "Repo has 1 file."
    )


def test_dependency_graph_round_trip():
    from app.processing.dependency import (
        DependencyGraph,
        ImportEdge,
    )

    graph = DependencyGraph()

    edge = ImportEdge(
        "app/main.py",
        "app/core.py",
        3,
        "from app.core import x",
    )

    graph.edges.append(edge)
    graph.imported_by["app/core.py"] = [edge]

    build_index(
        "test/depgraph",
        [
            EmbeddedChunk(
                Chunk(
                    "a.py",
                    "f",
                    "function",
                    1,
                    2,
                    "x",
                ),
                unit(0),
            )
        ],
        owner="o",
        name="r",
        branch="main",
        overview="",
        dependency_graph=graph,
    )

    stored = get_dependency_graph("test/depgraph")

    assert (
        stored.imported_by["app/core.py"][0].statement
        == "from app.core import x"
    )