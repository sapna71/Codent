import pytest

from types import SimpleNamespace

from app.processing.chunker import Chunk

from app.processing.embedder import (
    EMBEDDING_DIM,
    EmbeddingRateLimitError,
    embed_chunks,
    embed_query,
)


def make_client(calls):
    def embed_content(model, contents, config):
        calls.append((len(contents), config.task_type))

        vec = [3.0, 4.0] + [0.0] * (EMBEDDING_DIM - 2)

        return SimpleNamespace(
            embeddings=[
                SimpleNamespace(values=vec)
                for _ in contents
            ]
        )

    return SimpleNamespace(
        models=SimpleNamespace(
            embed_content=embed_content
        )
    )


def _chunk(i=0):
    return Chunk(
        "a.py",
        f"f{i}",
        "function",
        1,
        2,
        "def f(): pass",
    )


def test_embed_chunks_shape_and_normalization():
    calls = []

    result = embed_chunks(
        [_chunk(0), _chunk(1)],
        client=make_client(calls),
    )

    assert len(result) == 2
    assert len(result[0].embedding) == EMBEDDING_DIM

    # (3,4) normalized -> (0.6,0.8)
    assert abs(result[0].embedding[0] - 0.6) < 1e-6

    assert calls == [
        (2, "RETRIEVAL_DOCUMENT")
    ]


def test_embed_chunks_batches_requests():
    calls = []

    embed_chunks(
        [_chunk(i) for i in range(250)],
        client=make_client(calls),
    )

    assert [n for n, _ in calls] == [
        100,
        100,
        50,
    ]


def test_embed_query_uses_query_task_type():
    calls = []

    vec = embed_query(
        "where is login?",
        client=make_client(calls),
    )

    assert len(vec) == EMBEDDING_DIM

    assert calls == [
        (1, "RETRIEVAL_QUERY")
    ]


def test_embed_empty_list_makes_no_call():
    calls = []

    assert embed_chunks(
        [],
        client=make_client(calls),
    ) == []

    assert calls == []


def test_rate_limit_retries_then_succeeds(monkeypatch):
    monkeypatch.setattr(
        "app.processing.embedder.time.sleep",
        lambda s: None,
    )

    calls = {"n": 0}

    def flaky_embed_content(model, contents, config):
        calls["n"] += 1

        if calls["n"] < 3:
            raise Exception(
                "429 RESOURCE_EXHAUSTED "
                "{'retryDelay': '2s'}"
            )

        vec = [3.0, 4.0] + [0.0] * (EMBEDDING_DIM - 2)

        return SimpleNamespace(
            embeddings=[
                SimpleNamespace(values=vec)
                for _ in contents
            ]
        )

    client = SimpleNamespace(
        models=SimpleNamespace(
            embed_content=flaky_embed_content
        )
    )

    result = embed_chunks(
        [_chunk(0)],
        client=client,
    )

    assert len(result) == 1
    assert calls["n"] == 3


def test_rate_limit_exhausted_raises_clear_error(monkeypatch):
    monkeypatch.setattr(
        "app.processing.embedder.time.sleep",
        lambda s: None,
    )

    def always_fails(model, contents, config):
        raise Exception(
            "429 RESOURCE_EXHAUSTED"
        )

    client = SimpleNamespace(
        models=SimpleNamespace(
            embed_content=always_fails
        )
    )

    with pytest.raises(EmbeddingRateLimitError):
        embed_chunks(
            [_chunk(0)],
            client=client,
        )