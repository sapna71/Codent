import os
import re
import time
from dataclasses import dataclass

import numpy as np
from google import genai
from google.genai import types

from app.processing.chunker import Chunk

EMBEDDING_MODEL = os.environ.get("EMBEDDING_MODEL", "gemini-embedding-001")
EMBEDDING_DIM = 768
BATCH_SIZE = 100
MAX_CHARS = 6000
MAX_RETRIES = 6
BASE_DELAY = 5  # seconds, fallback if the API doesn't tell us how long to wait


class EmbeddingRateLimitError(Exception):
    """Raised when the embedding API's quota is still exhausted after retrying."""


@dataclass
class EmbeddedChunk:
    chunk: Chunk
    embedding: list[float]


def _build_text(chunk: Chunk) -> str:
    return f"File: {chunk.file}\n{chunk.kind}: {chunk.name}\n\n{chunk.code}"[:MAX_CHARS]


def _retry_delay_seconds(error: Exception) -> float | None:
    """Pull Google's suggested wait time (e.g. 'retryDelay': '31s') out of the error."""
    match = re.search(r"retryDelay['\"]?:\s*['\"]?([\d.]+)s", str(error))
    return float(match.group(1)) if match else None


def _embed(texts: list[str], task_type: str, client=None) -> list[list[float]]:
    if not texts:
        return []

    client = client or genai.Client()
    config = types.EmbedContentConfig(task_type=task_type, output_dimensionality=EMBEDDING_DIM)

    vectors: list[list[float]] = []
    for i in range(0, len(texts), BATCH_SIZE):
        batch = texts[i:i + BATCH_SIZE]
        for attempt in range(MAX_RETRIES):
            try:
                resp = client.models.embed_content(model=EMBEDDING_MODEL, contents=batch, config=config)
                break
            except Exception as e:
                if attempt == MAX_RETRIES - 1:
                    raise EmbeddingRateLimitError(
                        "The embedding API's rate limit is still exceeded after retrying. "
                        "Wait about a minute and try again, or index a smaller repo "
                        "(lower MAX_FILES in .env)."
                    ) from e
                delay = _retry_delay_seconds(e) or BASE_DELAY * (2 ** attempt)
                time.sleep(delay + 1)  # +1s buffer past what Google asked for
        vectors.extend(e.values for e in resp.embeddings)
        if i + BATCH_SIZE < len(texts):
            time.sleep(1)  # small gap between batches, spreads out requests proactively

    arr = np.array(vectors, dtype="float32")
    arr /= np.linalg.norm(arr, axis=1, keepdims=True)
    return arr.tolist()


def embed_chunks(chunks: list[Chunk], client=None) -> list[EmbeddedChunk]:
    vectors = _embed([_build_text(c) for c in chunks], "RETRIEVAL_DOCUMENT", client)
    return [EmbeddedChunk(chunk=c, embedding=v) for c, v in zip(chunks, vectors)]


def embed_query(question: str, client=None) -> list[float]:
    return _embed([question], "RETRIEVAL_QUERY", client)[0]