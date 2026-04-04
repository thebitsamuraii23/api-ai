from bot.handlers import _extract_fraction_parts_from_line


def test_extract_fraction_parts_rejects_contextual_sentence_with_fraction() -> None:
    line = "**При a = 3.7, b = 2: (3.7 x 1.7)/(2 x 5.7) = 1.1**"
    assert _extract_fraction_parts_from_line(line) is None


def test_extract_fraction_parts_accepts_pure_standalone_fraction() -> None:
    line = "(3.7 x 1.7)/(2 x 5.7)"
    assert _extract_fraction_parts_from_line(line) == ("3.7 x 1.7", "2 x 5.7")
