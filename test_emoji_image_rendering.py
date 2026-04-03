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


def test_emoji_to_twemoji_codepoints_drops_variation_selector() -> None:
    assert _emoji_to_twemoji_codepoints("❤️") == "2764"
    assert _emoji_to_twemoji_codepoints("1️⃣") == "31-20e3"


def test_segments_for_image_text_marks_emoji_image_segments() -> None:
    segments = _segments_for_image_text(
        "Hello 👋 world",
        image_context=RESPONSE_IMAGE_EMOJI_SEGMENT_PREFIX,
    )
    assert any(seg.startswith(RESPONSE_IMAGE_EMOJI_SEGMENT_PREFIX) for seg in segments)


def test_extract_unique_emoji_clusters() -> None:
    text = "🍕 and 🍕 with 🍔"
    clusters = _extract_unique_emoji_clusters(text)
    assert "🍕" in clusters
    assert "🍔" in clusters
    assert len(clusters) == 2
