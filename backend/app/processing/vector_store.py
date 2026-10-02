from dataclasses import dataclass

import faiss
import numpy as np

from app.processing.chunker import Chunk
from app.processing.dependency import DependencyGraph
from app.processing.embedder import EMBEDDING_DIM, EmbeddedChunk


@dataclass
class RepoIndex:
    index: faiss.IndexFlatIP
    chunks: list[Chunk]
    owner: str
    name: str
    branch: str
    overview: str
    dependency_graph: DependencyGraph


_STORE: dict[str, RepoIndex] = {}


def build_index(
    repo_key: str,
    embedded_chunks: list[EmbeddedChunk],
    owner: str,
    name: str,
    branch: str,
    overview: str = "",
    dependency_graph: DependencyGraph | None = None,
) -> None:
    """Build a FAISS index for a repo and keep its
    metadata and dependency graph in memory.
    """

    if not embedded_chunks:
        _STORE.pop(repo_key, None)
        return

    vectors = np.array(
        [e.embedding for e in embedded_chunks],
        dtype="float32",
    )

    index = faiss.IndexFlatIP(EMBEDDING_DIM)
    index.add(vectors)

    chunks = [
        e.chunk
        for e in embedded_chunks
    ]

    _STORE[repo_key] = RepoIndex(
        index=index,
        chunks=chunks,
        owner=owner,
        name=name,
        branch=branch,
        overview=overview,
        dependency_graph=(
            dependency_graph
            if dependency_graph is not None
            else DependencyGraph()
        ),
    )


def has_index(repo_key: str) -> bool:
    return repo_key in _STORE


def get_repo_meta(
    repo_key: str,
) -> tuple[str, str, str]:
    """Return (owner, name, branch) for a previously built index."""

    repo_index = _STORE.get(repo_key)

    if repo_index is None:
        raise KeyError(
            f"No index found for '{repo_key}'. Ingest it first."
        )

    return (
        repo_index.owner,
        repo_index.name,
        repo_index.branch,
    )


def get_repo_overview(repo_key: str) -> str:
    """Return the repository overview."""

    repo_index = _STORE.get(repo_key)

    if repo_index is None:
        raise KeyError(
            f"No index found for '{repo_key}'. Ingest it first."
        )

    return repo_index.overview


def get_dependency_graph(
    repo_key: str,
) -> DependencyGraph:
    """Return the dependency graph for a repository."""

    repo_index = _STORE.get(repo_key)

    if repo_index is None:
        raise KeyError(
            f"No index found for '{repo_key}'. Ingest it first."
        )

    return repo_index.dependency_graph


def search_index(
    repo_key: str,
    query_vector: list[float],
    top_k: int = 5,
) -> list[Chunk]:
    repo_index = _STORE.get(repo_key)

    if repo_index is None:
        raise KeyError(
            f"No index found for '{repo_key}'. Ingest it first."
        )

    query = np.array(
        [query_vector],
        dtype="float32",
    )

    top_k = min(
        top_k,
        len(repo_index.chunks),
    )

    scores, indices = repo_index.index.search(
        query,
        top_k,
    )

    return [
        repo_index.chunks[i]
        for i in indices[0]
        if i != -1
    ]