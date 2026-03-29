from bot.handlers import (
    _apply_recency_ranking,
    _build_precise_search_query,
    _count_results_for_domains,
    _dedupe_search_results,
    _extract_profile_handle_candidate,
    _extract_search_decision_from_llm_output,
    _compact_search_query,
    _extract_query_from_llm_output,
    _filter_noisy_search_results,
    _is_generic_search_phrase,
    _language_aware_query_variants,
    _looks_like_context_dependent_followup,
    _looks_like_search_execution_confirmation,
    _next_topic_hint,
    _parse_search_intent,
    _preferred_domains_for_search,
    _prioritize_search_results,
    _query_is_broad,
    _resolve_search_query,
    _search_clarification_prompt,
    _search_answer_style_guardrail,
    _search_target_domain_from_intent,
    _should_auto_web_search,
    _should_try_llm_context_resolution,
    _trusted_domains_for_query,
)
from bot.web_search import WebSearchResult


def test_search_about_him_is_detected_as_followup() -> None:
    assert _looks_like_context_dependent_followup("search about him")


def test_u_sure_is_detected_as_followup() -> None:
    assert _looks_like_context_dependent_followup("u sure?")
    assert _looks_like_context_dependent_followup("ты уверен?")


def test_search_about_him_is_generic_search_phrase() -> None:
    assert _is_generic_search_phrase("search about him")
    assert not _is_generic_search_phrase("search about elon musk")


def test_next_topic_hint_keeps_previous_topic_for_pronoun_search() -> None:
    current_topic = "Elon Musk"
    assert _next_topic_hint("search about him", current_topic=current_topic) == current_topic


def test_next_topic_hint_keeps_previous_topic_for_short_challenge_followup() -> None:
    current_topic = "Horse painting analysis"
    assert _next_topic_hint("u sure?", current_topic=current_topic) == current_topic


def test_resolve_search_query_uses_topic_hint_for_pronoun_search() -> None:
    topic = "Elon Musk"
    query, resolved_topic = _resolve_search_query(
        "search about him",
        history=[{"role": "user", "content": "Who is Elon Musk?"}],
        topic_hint=topic,
        lang="en",
    )
    assert query == _compact_search_query(topic)
    assert resolved_topic == topic


def test_resolve_search_query_uses_recent_history_when_no_topic_hint() -> None:
    history = [
        {"role": "user", "content": "Who is Elon Musk?"},
        {"role": "assistant", "content": "Elon Musk is an entrepreneur."},
        {"role": "user", "content": "search about him"},
    ]
    query, resolved_topic = _resolve_search_query(
        "search about him",
        history=history,
        topic_hint=None,
        lang="en",
    )
    assert query == _compact_search_query("Who is Elon Musk?")
    assert resolved_topic == "Who is Elon Musk?"


def test_should_try_llm_context_resolution_is_language_agnostic_for_short_query() -> None:
    assert _should_try_llm_context_resolution("busca sobre él", "Elon Musk")
    assert _should_try_llm_context_resolution("ابحث عنه", "إيلون ماسك")
    assert _should_try_llm_context_resolution("onun hakkında ara", "Elon Musk")


def test_extract_query_from_llm_output_parses_json_shape() -> None:
    query, used_topic = _extract_query_from_llm_output(
        '{"query":"search latest price Elon Musk","use_topic":true}',
        fallback="search latest price",
    )
    assert query == "search latest price Elon Musk"
    assert used_topic is True


def test_search_execution_confirmation_detected() -> None:
    assert _looks_like_search_execution_confirmation("используй")
    assert _looks_like_search_execution_confirmation("go ahead")
    assert not _looks_like_search_execution_confirmation("write a poem")


def test_next_topic_hint_keeps_context_for_search_confirmation() -> None:
    assert _next_topic_hint("используй", current_topic="Qarabag FC") == "Qarabag FC"


def test_resolve_search_query_confirmation_uses_topic() -> None:
    query, resolved_topic = _resolve_search_query(
        "используй",
        history=[{"role": "user", "content": "последние матчи Карабаха"}],
        topic_hint="последние матчи Карабаха",
        lang="ru",
    )
    assert query == _compact_search_query("последние матчи Карабаха")
    assert resolved_topic == "последние матчи Карабаха"


def test_extract_search_decision_from_llm_output_parses_json_shape() -> None:
    search, confidence = _extract_search_decision_from_llm_output('{"search": true, "confidence": 0.91}')
    assert search is True
    assert confidence == 0.91


def test_auto_web_search_true_for_confirmation_with_topic() -> None:
    assert _should_auto_web_search("используй", wants_search=False, topic_hint="последние матчи Карабаха")


def test_search_answer_style_guardrail_mentions_selected_personality() -> None:
    guardrail = _search_answer_style_guardrail("comedian", include_clarify=True)
    assert "comedian" in guardrail
    assert "do not switch to a generic neutral assistant voice" in guardrail


def test_search_target_domain_from_intent_detects_github_gitlab() -> None:
    assert _search_target_domain_from_intent("search his github") == "github.com"
    assert _search_target_domain_from_intent("найди его гитхаб профиль") == "github.com"
    assert _search_target_domain_from_intent("search her gitlab profile") == "gitlab.com"
    assert _search_target_domain_from_intent("find his linkedin profile") == "linkedin.com"


def test_resolve_search_query_targets_github_domain_with_topic() -> None:
    query, resolved_topic = _resolve_search_query(
        "search his github",
        history=[{"role": "user", "content": "Tell me about thebitsamurai"}],
        topic_hint="thebitsamurai",
        lang="en",
    )
    assert query == "thebitsamurai site:github.com"
    assert resolved_topic is not None
    assert resolved_topic.startswith("search his github\n\nTopic (")
    assert resolved_topic.endswith("): thebitsamurai")


def test_preferred_domains_for_search_returns_strict_for_profile_intent() -> None:
    domains, strict = _preferred_domains_for_search("search his github profile", topic_hint="thebitsamurai")
    assert domains == ["github.com"]
    assert strict is True


def test_preferred_domains_for_search_returns_trusted_news_domains() -> None:
    domains, strict = _preferred_domains_for_search("latest news about Tesla", topic_hint=None)
    assert strict is False
    assert "reuters.com" in domains
    assert "apnews.com" in domains


def test_prioritize_search_results_prefers_target_domain_and_strict_filters() -> None:
    results = [
        WebSearchResult(title="Other", url="https://example.com/a", snippet=""),
        WebSearchResult(title="GH", url="https://github.com/thebitsamuraii23", snippet=""),
        WebSearchResult(title="Another", url="https://news.ycombinator.com/item?id=1", snippet=""),
    ]
    preferred = _prioritize_search_results(results, preferred_domains=["github.com"], strict=False)
    assert preferred[0].url.startswith("https://github.com/")

    strict = _prioritize_search_results(results, preferred_domains=["github.com"], strict=True)
    assert len(strict) == 1
    assert strict[0].url.startswith("https://github.com/")


def test_prioritize_search_results_returns_empty_for_strict_without_target_domain() -> None:
    results = [
        WebSearchResult(title="Other", url="https://example.com/a", snippet=""),
        WebSearchResult(title="Another", url="https://news.ycombinator.com/item?id=1", snippet=""),
    ]
    strict = _prioritize_search_results(results, preferred_domains=["github.com"], strict=True)
    assert strict == []


def test_dedupe_and_count_results_for_domains() -> None:
    results = [
        WebSearchResult(title="GH1", url="https://github.com/thebitsamuraii23/", snippet=""),
        WebSearchResult(title="GH1 dup", url="https://github.com/thebitsamuraii23", snippet=""),
        WebSearchResult(title="Other", url="https://example.com", snippet=""),
    ]
    deduped = _dedupe_search_results(results)
    assert len(deduped) == 2
    assert _count_results_for_domains(deduped, ["github.com"]) == 1


def test_filter_noisy_search_results_removes_github_search_and_youtube_for_strict() -> None:
    results = [
        WebSearchResult(title="GH search", url="https://github.com/search?q=thebitsamurai", snippet=""),
        WebSearchResult(title="YouTube guide", url="https://youtube.com/watch?v=1", snippet="how to search github users"),
        WebSearchResult(title="Profile", url="https://github.com/thebitsamuraii23", snippet=""),
    ]
    filtered = _filter_noisy_search_results(results, preferred_domains=["github.com"], strict=True)
    assert len(filtered) == 1
    assert filtered[0].url == "https://github.com/thebitsamuraii23"


def test_build_precise_search_query_adds_site_and_topic_for_strict() -> None:
    precise = _build_precise_search_query(
        "search his github",
        topic_hint="thebitsamurai",
        preferred_domains=["github.com"],
        strict=True,
    )
    assert precise == "search his github thebitsamurai site:github.com"


def test_trusted_domains_for_query_detects_sports_and_docs() -> None:
    sports_domains = _trusted_domains_for_query("latest score of Qarabag")
    docs_domains = _trusted_domains_for_query("python api docs")
    assert "espn.com" in sports_domains
    assert "sofascore.com" in sports_domains
    assert "docs.python.org" in docs_domains


def test_extract_profile_handle_candidate_from_topic_and_text() -> None:
    assert _extract_profile_handle_candidate("search his github", topic_hint="thebitsamurai") == "thebitsamurai"
    assert _extract_profile_handle_candidate("https://github.com/thebitsamuraii23") == "thebitsamuraii23"
    assert _extract_profile_handle_candidate("search his github", topic_hint="Tell me about thebitsamurai") == "thebitsamurai"


def test_parse_search_intent_profile_and_broad_detection() -> None:
    intent = _parse_search_intent("search his github", topic_hint="thebitsamurai", lang="en")
    assert intent["kind"] == "profile"
    assert intent["domain"] == "github.com"
    assert intent["profile_handle"] == "thebitsamurai"
    assert _query_is_broad("search his github", intent=intent, topic_hint="thebitsamurai") is False


def test_search_clarification_prompt_for_broad_news_query() -> None:
    intent = _parse_search_intent("news", topic_hint=None, lang="en")
    clarification = _search_clarification_prompt("news", lang="en", intent=intent, topic_hint=None)
    assert clarification is not None
    assert "clarify" in clarification.lower() or "specify" in clarification.lower()


def test_search_clarification_not_triggered_for_specific_entity() -> None:
    intent = _parse_search_intent("elon musk latest news", topic_hint=None, lang="en")
    clarification = _search_clarification_prompt("elon musk latest news", lang="en", intent=intent, topic_hint=None)
    assert clarification is None


def test_language_aware_query_variants_adds_english_bridge_for_non_latin_news() -> None:
    intent = _parse_search_intent("последние новости карабаха", topic_hint=None, lang="ru")
    variants = _language_aware_query_variants("последние новости карабаха", intent=intent, topic_hint=None)
    assert "последние новости карабаха" in variants
    assert any("latest news" in item.lower() for item in variants)


def test_apply_recency_ranking_prioritizes_recent_items_for_news() -> None:
    intent = {"kind": "news", "wants_latest": True}
    results = [
        WebSearchResult(title="Old", url="https://example.com/2020-01-01", snippet="2020-01-01 archive"),
        WebSearchResult(title="Today", url="https://example.com/today", snippet="published today"),
    ]
    ranked = _apply_recency_ranking(results, intent=intent)
    assert ranked[0].title == "Today"
