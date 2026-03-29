from bot.web_search import (
    WebPageExtract,
    _clean_html_to_text,
    _normalize_wiki_language,
    _reddit_json_url,
    _truncate_text,
    format_page_extracts,
)


def test_clean_html_to_text_removes_scripts_and_tags() -> None:
    html = """
    <html>
      <head><script>var a = 1;</script><title>Title</title></head>
      <body>
        <h1>Hello</h1>
        <p>World <b>bold</b></p>
        <ul><li>One</li><li>Two</li></ul>
      </body>
    </html>
    """
    text = _clean_html_to_text(html)
    assert "var a = 1" not in text
    assert "Hello" in text
    assert "World bold" in text
    assert "One" in text and "Two" in text


def test_truncate_text_adds_ellipsis_when_needed() -> None:
    value = "x" * 50
    out = _truncate_text(value, max_chars=10)
    assert out.endswith("…")
    assert len(out) == 10


def test_reddit_json_url_appends_json_suffix() -> None:
    assert _reddit_json_url("https://www.reddit.com/r/python/comments/abc123/post") == (
        "https://www.reddit.com/r/python/comments/abc123/post.json"
    )


def test_normalize_wiki_language_uses_known_aliases_and_default() -> None:
    assert _normalize_wiki_language("ru") == "ru"
    assert _normalize_wiki_language("unknown") == "en"


def test_format_page_extracts_renders_blocks() -> None:
    formatted = format_page_extracts(
        [
            WebPageExtract(source_index=1, title="Example", url="https://example.com", text="Body text."),
        ]
    )
    assert "Fetched page excerpts:" in formatted
    assert "[1] Example (https://example.com)" in formatted
    assert "Body text." in formatted
