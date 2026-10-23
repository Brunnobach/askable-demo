from pathlib import Path


def test_hello_file_exists() -> None:
    hello_file = Path("/app/hello.txt")
    assert hello_file.exists(), "hello.txt does not exist at /app/hello.txt"


def test_hello_file_content() -> None:
    hello_file = Path("/app/hello.txt")
    content = hello_file.read_text()
    assert content == "Hello, Terminal Tasks!\n", (
        f"Expected 'Hello, Terminal Tasks!\\n', got {content!r}"
    )
