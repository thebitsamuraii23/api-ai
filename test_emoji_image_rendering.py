from bot.handlers import (
    RESPONSE_IMAGE_EMOJI_SEGMENT_PREFIX,
    _emoji_cluster_spans,
    _emoji_to_twemoji_codepoints,
    _extract_unique_emoji_clusters,
    _segments_for_image_text,
)


def test_emoji_cluster_spans_detects_simple_and_zwj_clusters() -> None:
    text = "A 🙂 B 👨‍👩‍👧‍👦 C"
    spans = _emoji_cluster_spans(text)
    clusters = [text[start:end] for start, end in spans]
    assert clusters == ["🙂", "👨‍👩‍👧‍👦"]


def test_emoji_cluster_spans_detects_keycap_cluster() -> None:
    text = "Press 1️⃣ now"
    spans = _emoji_cluster_spans(text)
    clusters = [text[start:end] for start, end in spans]
    assert "1️⃣" in clusters


def test_emoji_cluster_spans_detects_country_flag_clusters() -> None:
    text = "Flags 🇺🇸 and 🇩🇪"
    spans = _emoji_cluster_spans(text)
    clusters = [text[start:end] for start, end in spans]
    assert clusters == ["🇺🇸", "🇩🇪"]


def test_emoji_to_twemoji_codepoints_drops_variation_selector() -> None:
    assert _emoji_to_twemoji_codepoints("❤️") == "2764"
    assert _emoji_to_twemoji_codepoints("1️⃣") == "31-20e3"


def test_emoji_to_twemoji_codepoints_supports_country_flags() -> None:
    assert _emoji_to_twemoji_codepoints("🇺🇸") == "1f1fa-1f1f8"


def test_segments_for_image_text_marks_emoji_image_segments() -> None:
    segments = _segments_for_image_text(
        "Hello 🙂 world",
        "body",
        fonts={"body": object(), "emoji": object()},
        emoji_image_keys={"🙂"},
    )
    assert ("Hello ", "body") in segments
    assert ("🙂", f"{RESPONSE_IMAGE_EMOJI_SEGMENT_PREFIX}body") in segments
    assert (" world", "body") in segments


def test_extract_unique_emoji_clusters_returns_unique_ordered() -> None:
    clusters = _extract_unique_emoji_clusters("🙂🙂 🔥🙂")
    assert clusters == ["🙂", "🔥"]
