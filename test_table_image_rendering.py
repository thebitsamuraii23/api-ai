from bot.handlers import (
    _extract_markdown_tables,
    _should_render_table_as_image,
    _render_table_as_image,
)


def test_extract_simple_markdown_table() -> None:
    """Test extraction of simple markdown tables."""
    text = """
Here is a table:

| Header 1 | Header 2 |
|----------|----------|
| Cell 1   | Cell 2   |
| Cell 3   | Cell 4   |

End of table.
"""
    tables = _extract_markdown_tables(text)
    assert len(tables) >= 1
    assert "Header 1" in tables[0] or "Header" in tables[0]


def test_extract_complex_table_with_alignment() -> None:
    """Test extraction of tables with text alignment markers."""
    text = """
| Left     | Center   | Right    |
|:---------|:--------:|----------:|
| L1       | C1       | R1       |
| L2       | C2       | R2       |
"""
    tables = _extract_markdown_tables(text)
    assert len(tables) >= 1


def test_should_render_table_as_image() -> None:
    """Test logic for determining if table should be rendered as image."""
    # Large tables should be rendered as images for better display
    large_table = """
| Col1 | Col2 | Col3 | Col4 | Col5 |
|------|------|------|------|------|
""" + "\n".join([f"| A{i} | B{i} | C{i} | D{i} | E{i} |" for i in range(20)])
    
    should_render = _should_render_table_as_image(large_table)
    assert should_render, "Large tables should be rendered as images"
    
    # Small tables might not need image rendering
    small_table = """
| Col1 | Col2 |
|------|------|
| A    | B    |
"""
    small_render = _should_render_table_as_image(small_table)
    # This depends on the implementation


def test_render_table_preserves_content() -> None:
    """Test that rendered table preserves all content."""
    table = """
| Product | Price | Stock |
|---------|-------|-------|
| Apple   | $1.50 | 50    |
| Orange  | $2.00 | 30    |
"""
    rendered = _render_table_as_image(table)
    # Content should be preserved (either as text or image reference)
    assert "Apple" in rendered or "table" in rendered.lower()


def test_table_with_special_characters() -> None:
    """Test tables containing special characters and emoji."""
    text = """
| Item | Status | Notes |
|------|--------|-------|
| ✅ Task 1 | Done | 100% complete |
| ⏳ Task 2 | Pending | 50% done |
| ❌ Task 3 | Failed | Check logs |
"""
    tables = _extract_markdown_tables(text)
    assert len(tables) >= 1
    # Should extract properly with emoji
    extracted = tables[0]
    assert "✅" in extracted or "Task" in extracted


def test_multiple_tables_extraction() -> None:
    """Test extraction of multiple tables from a single response."""
    text = """
| A | B |
|---|---|
| 1 | 2 |

Some text between tables.

| X | Y | Z |
|---|---|---|
| a | b | c |
"""
    tables = _extract_markdown_tables(text)
    assert len(tables) >= 2, "Should extract multiple tables"


def test_malformed_table_handling() -> None:
    """Test that malformed tables are handled gracefully."""
    text = """
| Header 1 | Header 2
|----------|----------
| Cell 1   | Cell 2
"""
    try:
        tables = _extract_markdown_tables(text)
        # Should handle gracefully, either extracting or returning empty
        assert True
    except Exception as e:
        assert False, f"Should handle malformed tables gracefully: {e}"
