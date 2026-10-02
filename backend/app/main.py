from dotenv import load_dotenv

load_dotenv()

from fastapi import FastAPI, HTTPException
from fastapi.middleware.cors import CORSMiddleware
from pydantic import BaseModel

from app.github import (
    GitHubError,
    build_blob_url,
    get_repo_files,
    parse_github_url,
)

from app.processing.chunker import Chunk, chunk_file

from app.processing.dependency import (
    build_dependency_graph,
    get_affected_files,
)

from app.processing.embedder import (
    embed_chunks,
    embed_query,
    EmbeddingRateLimitError,
)

from app.processing.file_filter import filter_source_files
from app.processing.overview import build_repo_overview, overview_chunk
from app.processing.rag import answer_question

from app.processing.vector_store import (
    build_index,
    get_repo_meta,
    get_repo_overview,
    get_dependency_graph,
    has_index,
    search_index,
)


app = FastAPI(title="Codent", version="0.1.0")


app.add_middleware(
    CORSMiddleware,
    allow_origins=[
        "http://localhost:3000",
        "https://codent-neon.vercel.app",
    ],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)


@app.get("/health")
def health() -> dict:
    return {"status": "ok"}


class IngestRequest(BaseModel):
    url: str


@app.post("/ingest")
def ingest(req: IngestRequest) -> dict:
    try:
        ref = parse_github_url(req.url)
        info, files = get_repo_files(ref)

    except ValueError as e:
        raise HTTPException(
            status_code=400,
            detail=str(e),
        )

    except GitHubError as e:
        raise HTTPException(
            status_code=502,
            detail=str(e),
        )

    source_files = filter_source_files(files)

    all_chunks = []

    for f in source_files:
        all_chunks.extend(
            chunk_file(
                f.path,
                f.language,
                f.content,
            )
        )

    # Build dependency graph from the repository source files
    dependency_graph = build_dependency_graph(source_files)

    repo_key = f"{ref.owner}/{ref.name}"

    overview = build_repo_overview(source_files)

    # Embed the chunks and build the FAISS index.
    # If Gemini embedding quota is exceeded, return
    # a readable HTTP 429 response instead of a 500 crash.
    try:
        build_index(
            repo_key,
            embed_chunks(all_chunks),
            info.owner,
            info.name,
            info.default_branch,
            overview,
            dependency_graph,
        )

    except EmbeddingRateLimitError as e:
        raise HTTPException(
            status_code=429,
            detail=str(e),
        )

    return {
        "owner": info.owner,
        "name": info.name,
        "default_branch": info.default_branch,
        "raw_file_count": len(files),
        "filtered_file_count": len(source_files),
        "chunk_count": len(all_chunks),
        "repo_key": repo_key,
    }


class QueryRequest(BaseModel):
    repo_key: str
    question: str
    top_k: int = 5


def _retrieve(req: QueryRequest) -> list[Chunk]:
    if not has_index(req.repo_key):
        raise HTTPException(
            status_code=404,
            detail=f"Repo '{req.repo_key}' not indexed. Call /ingest first.",
        )

    return search_index(
        req.repo_key,
        embed_query(req.question),
        top_k=req.top_k,
    )


def _cite(repo_key: str, c: Chunk, ref: int) -> dict:
    owner, name, branch = get_repo_meta(repo_key)

    github_url = (
        f"https://github.com/{owner}/{name}"
        if c.kind == "overview"
        else build_blob_url(
            owner,
            name,
            branch,
            c.file,
            c.start_line,
            c.end_line,
        )
    )

    return {
        "ref": ref,
        "file": c.file,
        "name": c.name,
        "kind": c.kind,
        "start_line": c.start_line,
        "end_line": c.end_line,
        "github_url": github_url,
    }


@app.post("/query")
def query(req: QueryRequest) -> dict:
    results = _retrieve(req)

    return {
        "question": req.question,
        "results": [
            {
                **_cite(req.repo_key, c, i),
                "code": c.code,
            }
            for i, c in enumerate(results, start=1)
        ],
    }


@app.post("/ask")
def ask(req: QueryRequest) -> dict:
    retrieved = _retrieve(req)

    overview = get_repo_overview(req.repo_key)

    full_chunks = (
        [overview_chunk(overview)] + retrieved
        if overview
        else retrieved
    )

    answer = answer_question(
        req.question,
        full_chunks,
    )

    return {
        "question": req.question,
        "answer": answer,
        "sources": [
            _cite(req.repo_key, c, i)
            for i, c in enumerate(full_chunks, start=1)
        ],
    }


class ImpactRequest(BaseModel):
    repo_key: str
    file_path: str
    max_depth: int = 2


@app.post("/impact")
def impact(req: ImpactRequest) -> dict:
    if not has_index(req.repo_key):
        raise HTTPException(
            status_code=404,
            detail=f"Repo '{req.repo_key}' not indexed. Call /ingest first.",
        )

    graph = get_dependency_graph(req.repo_key)

    affected = get_affected_files(
        graph,
        req.file_path,
        max_depth=req.max_depth,
    )

    return {
        "file": req.file_path,
        "affected_file_count": len(affected),
        "affected_files": affected,
    }