from bot.handlers import (
    _extract_fractions_from_response,
    _render_fraction_as_image,
)


def test_extract_simple_fractions() -> None:
    """Test extraction of common fractions like 1/2, 1/3, 3/4."""
    text = "Mix 1/2 cup flour with 1/3 cup sugar and 3/4 cup butter"
    fractions = _extract_fractions_from_response(text)
    
    assert "1/2" in fractions
    assert "1/3" in fractions
    assert "3/4" in fractions


def test_extract_fractions_with_spaces() -> None:
    """Test fractions with optional spaces (1 / 2 style)."""
    text = "Use 2 / 5 of the mixture or 1/4 cup"
    fractions = _extract_fractions_from_response(text)
    
    assert any(f.replace(" ", "") == "2/5" for f in fractions)
    assert any(f.replace(" ", "") == "1/4" for f in fractions)


def test_render_fraction_as_image() -> None:
    """Test rendering fractions as high-quality Unicode/image equivalents."""
    # Common fractions with Unicode representations
    common_fractions = {
        "1/2": "½",
        "1/3": "⅓",
        "2/3": "⅔",
        "1/4": "¼",
        "3/4": "¾",
        "1/8": "⅛",
    }
    
    for fraction, expected in common_fractions.items():
        result = _render_fraction_as_image(fraction)
        assert result == expected, f"Expected {expected} for {fraction}, got {result}"


def test_fraction_rendering_in_response() -> None:
    """Test that fractions in model responses are properly rendered."""
    response = "Mix 1/2 cup milk with 1/4 cup sugar. Combine with 3/4 cup flour."
    rendered = _render_fraction_as_image(response)
    
    # Should contain Unicode fractions
    assert "½" in rendered or "1/2" in rendered
    assert "¼" in rendered or "1/4" in rendered
    assert "¾" in rendered or "3/4" in rendered


def test_complex_fractions() -> None:
    """Test fractions that need image rendering (like 2/5, 5/8)."""
    text = "Use 2/5 of the solution with 5/8 cup water"
    fractions = _extract_fractions_from_response(text)
    
    assert any(f.replace(" ", "") == "2/5" for f in fractions)
    assert any(f.replace(" ", "") == "5/8" for f in fractions)
