from bot.handlers import _normalize_text_for_image, _replace_latex_text_styles


def test_replace_latex_text_styles_handles_textbf_with_nested_parentheses() -> None:
    source = "Ответ: textbf((4n - 6m²)(4n + 6m²))"
    rendered = _replace_latex_text_styles(source)
    assert rendered == "Ответ: **(4n - 6m²)(4n + 6m²)**"


def test_normalize_text_for_image_preserves_bold_markers_from_textbf() -> None:
    source = "Ответ: textbf((4n - 6m²)(4n + 6m²))"
    normalized = _normalize_text_for_image(source)
    assert normalized == "Ответ: **(4n - 6m²)(4n + 6m²)**"
