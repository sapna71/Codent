from app.processing.chunker import chunk_generic_file, chunk_file


def test_chunk_generic_file():
    content = "\n".join(f"line {i}" for i in range(1, 251))  # 250 lines
    chunks = chunk_generic_file("readme.md", content)
    assert len(chunks) == 3  # 100 + 100 + 50
    assert chunks[0].start_line == 1
    assert chunks[0].end_line == 100
    assert chunks[2].start_line == 201
    assert chunks[2].end_line == 250


def test_chunk_file_dispatches_by_language():
    py_chunks = chunk_file("a.py", "python", "def f():\n    pass\n")
    assert py_chunks[0].kind == "function"

    js_chunks = chunk_file("a.js", "javascript", "let x = 1;\n")
    assert js_chunks[0].kind == "block"