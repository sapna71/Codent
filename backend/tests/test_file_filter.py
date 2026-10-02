from app.processing.file_filter import (
    filter_source_files,
    is_candidate_path,
)


def test_filter():
    files = [
        {
            "path": "backend/auth/service.py",
            "content": "def login(): pass",
        },
        {
            "path": "node_modules/x/index.js",
            "content": "x = 1",
        },
        {
            "path": "package-lock.json",
            "content": "{}",
        },
        {
            "path": "static/app.min.js",
            "content": "x=1",
        },
        {
            "path": "logo.py",
            "content": "\x00\x01",
        },
        {
            "path": "empty.py",
            "content": "   ",
        },
    ]

    result = filter_source_files(files)

    assert [f.path for f in result] == [
        "backend/auth/service.py"
    ]

    assert result[0].language == "python"


def test_is_candidate_path():
    assert is_candidate_path("src/app/main.py")
    assert not is_candidate_path("README.md")
    assert not is_candidate_path(
        "node_modules/x/index.js"
    )
    assert not is_candidate_path(
        "dist/app.min.js"
    )