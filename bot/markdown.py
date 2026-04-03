r"""
Utilities for Markdown formatting in Telegram messages with proper MarkdownV2 escaping.

MarkdownV2 Escaping Guide:
=======================

Telegram MarkdownV2 requires these characters to be escaped with backslash:
  _ * [ ] ( ) ~ ` > # + - = | { } . !

Example:
  Text:     "Hello_world! Check this: url(example.com)"
  Escaped:  "Hello\_world\! Check this\: url\(example\.com\)"

Special Case - Code Blocks:
  Code blocks with triple backticks (``` ```) do NOT need internal escaping.
  The content inside remains 100% unchanged.
  
  Example:
    Input markup:
    ```python
    def test():
        x = 5 * 2  # No escaping needed!
    ```
    
    Sends exactly as-is to Telegram. The *, (), : etc inside are NOT escaped.

This module provides intelligent escaping that:
  1. Escapes all special chars in regular text
  2. Preserves code blocks without escaping their content
  3. Supports common Markdown styles from LLM output (headings, lists, links, inline code, tables)
"""

from __future__ import annotations

import re
from typing import Literal

_FENCED_CODE_PATTERN = r"(```[\s\S]*?```)"
_MARKDOWN_TABLE_SEPARATOR_RE = re.compile(
    r"\s*\|?\s*:?-{3,}:?\s*(\|\s*:?-{3,}:?\s*)+\|?\s*"
)
_MARKDOWN_LINK_RE = re.compile(r"\[([^\]\n]+)\]\((https?://[^\s)]+)\)")
_INLINE_CODE_RE = re.compile(r"(?<!`)`([^`\n]+)`(?!`)")
_HORIZONTAL_RULE_RE = re.compile(r"^\s*([-*_])(?:\s*\1){2,}\s*$")


def escape_markdown_v2(text: str) -> str:
    r"""
    Escapes special characters for Telegram MarkdownV2.
    
    This function escapes ALL special MarkdownV2 characters:
    _ * [ ] ( ) ~ ` > # + - = | { } . !
    
    Use this for:
    - User inputs
    - Error messages  
    - Any text you don't want interpreted as Markdown
    
    Do NOT use this for:
    - Text inside code blocks (they auto-escape)
    - Pre-formatted text blocks
    
    Args:
        text: Raw text to escape
        
    Returns:
        Text with special characters escaped with backslash
        
    Examples:
        >>> escape_markdown_v2("Hello_world!")
        'Hello\\_world\\!'
        
        >>> escape_markdown_v2("Check (example.com)")
        'Check \\(example\\.com\\)'
    """
    # All special characters that need escaping in MarkdownV2
    special_chars = r"_*[]()~`>#+-=|{}.!"
    escaped: list[str] = []
    for char in text:
        if char in special_chars:
            escaped.append(f"\\{char}")
        else:
            escaped.append(char)
    return "".join(escaped)


def format_code_block(
    code: str, 
    language: str = "python",
    parse_mode: Literal["MarkdownV2", "Markdown"] = "MarkdownV2"
) -> str:
    """
    Formats code with triple backticks for code blocks.
    
    In MarkdownV2, characters inside code blocks don't need escaping.
    
    Args:
        code: The code content
        language: Programming language for syntax highlighting
        parse_mode: Markdown parse mode to use
        
    Returns:
        Formatted code block string
    """
    if parse_mode == "MarkdownV2":
        # In MarkdownV2, backticks and characters inside them don't need escaping
        return f"```{language}\n{code}\n```"
    else:
        # In basic Markdown, same format but may have different escaping rules
        return f"```{language}\n{code}\n```"


def format_inline_code(
    code: str,
    parse_mode: Literal["MarkdownV2", "Markdown"] = "MarkdownV2"
) -> str:
    """
    Formats inline code with single backticks.
    
    Args:
        code: The code content
        parse_mode: Markdown parse mode to use
        
    Returns:
        Formatted inline code string
    """
    if parse_mode == "MarkdownV2":
        return f"`{code}`"
    else:
        return f"`{code}`"


def format_bold(
    text: str,
    parse_mode: Literal["MarkdownV2", "Markdown"] = "MarkdownV2"
) -> str:
    """Formats text as bold."""
    if parse_mode == "MarkdownV2":
        # In MarkdownV2, need to escape the text inside
        escaped = escape_markdown_v2(text)
        return f"*{escaped}*"
    else:
        return f"*{text}*"


def format_italic(
    text: str,
    parse_mode: Literal["MarkdownV2", "Markdown"] = "MarkdownV2"
) -> str:
    """Formats text as italic."""
    if parse_mode == "MarkdownV2":
        escaped = escape_markdown_v2(text)
        return f"_{escaped}_"
    else:
        return f"_{text}_"


def format_link(
    text: str,
    url: str,
    parse_mode: Literal["MarkdownV2", "Markdown"] = "MarkdownV2"
) -> str:
    """Formats a hyperlink."""
    if parse_mode == "MarkdownV2":
        escaped_text = escape_markdown_v2(text)
        return f"[{escaped_text}]({url})"
    else:
        return f"[{text}]({url})"


def smart_escape_for_response(
    text: str,
    parse_mode: Literal["MarkdownV2", "Markdown"] = "MarkdownV2"
) -> str:
    """
    Intelligently escapes text while preserving code blocks.
    
    This function:
    1. Preserves code blocks (```code```) without escaping their content
    2. Escapes other special characters in regular text
    
    Args:
        text: Text that may contain code blocks
        parse_mode: Markdown parse mode to use
        
    Returns:
        Properly escaped text with preserved code blocks
    """
    if parse_mode != "MarkdownV2":
        return text
    
    # Split by code blocks while preserving them
    parts = re.split(_FENCED_CODE_PATTERN, text)
    
    result = []
    for i, part in enumerate(parts):
        # Odd indices are code blocks (matched by the pattern)
        if i % 2 == 1:
            # Code block - don't escape
            result.append(part)
        else:
            # Regular text - escape special characters
            result.append(escape_markdown_v2(part))
    
    return ''.join(result)


def _escape_markdown_v2_url(url: str) -> str:
    # Telegram MarkdownV2 requires escaping ")" and "\" inside link URLs.
    return url.replace("\\", "\\\\").replace(")", "\\)")


def _escape_inline_code(text: str) -> str:
    return text.replace("\\", "\\\\").replace("`", "\\`")


def _split_markdown_table_row(line: str) -> list[str]:
    stripped = line.strip()
    if stripped.startswith("|"):
        stripped = stripped[1:]
    if stripped.endswith("|"):
        stripped = stripped[:-1]
    cells = [cell.strip().replace(r"\|", "|") for cell in re.split(r"(?<!\\)\|", stripped)]
    return cells


def _is_markdown_table_candidate_row(line: str) -> bool:
    stripped = line.strip()
    if not stripped:
        return False
    return stripped.count("|") >= 2


def _clean_table_cell(cell: str, *, limit: int = 34) -> str:
    value = cell.strip()
    value = re.sub(r"\*\*(.+?)\*\*|__(.+?)__", lambda m: m.group(1) or m.group(2) or "", value)
    value = re.sub(r"(?<!\*)\*([^*\n]+)\*(?!\*)", r"\1", value)
    value = re.sub(r"(?<!\w)_([^_\n]+)_(?!\w)", r"\1", value)
    value = re.sub(r"`([^`\n]+)`", r"\1", value)
    value = re.sub(r"~~(.+?)~~", r"\1", value)
    value = re.sub(r"\s+", " ", value).strip()
    if len(value) <= limit:
        return value
    return value[: max(0, limit - 1)].rstrip() + "…"


def _render_box_table(rows: list[list[str]]) -> str:
    if not rows:
        return ""
    col_count = max(len(row) for row in rows)
    normalized_rows: list[list[str]] = []
    for row in rows:
        cleaned = [_clean_table_cell(cell) for cell in row]
        if len(cleaned) < col_count:
            cleaned.extend([""] * (col_count - len(cleaned)))
        normalized_rows.append(cleaned)

    widths: list[int] = []
    for col in range(col_count):
        max_len = max(len(normalized_rows[row][col]) for row in range(len(normalized_rows)))
        widths.append(max(3, min(34, max_len)))

    def border(left: str, middle: str, right: str) -> str:
        body = middle.join("─" * (width + 2) for width in widths)
        return f"{left}{body}{right}"

    def render_row(values: list[str]) -> str:
        cells = [f" {values[idx].ljust(widths[idx])} " for idx in range(col_count)]
        return f"│{'│'.join(cells)}│"

    output = [border("┌", "┬", "┐"), render_row(normalized_rows[0])]
    if len(normalized_rows) > 1:
        output.append(border("├", "┼", "┤"))
        for row in normalized_rows[1:]:
            output.append(render_row(row))
    output.append(border("└", "┴", "┘"))
    return "\n".join(output)


def _convert_markdown_tables_in_segment(segment: str) -> str:
    lines = segment.splitlines()
    if not lines:
        return segment
    had_trailing_newline = segment.endswith("\n")
    output: list[str] = []
    index = 0
    while index < len(lines):
        current = lines[index]
        next_line = lines[index + 1] if index + 1 < len(lines) else ""
        if _is_markdown_table_candidate_row(current) and _MARKDOWN_TABLE_SEPARATOR_RE.fullmatch(next_line or ""):
            rows: list[list[str]] = [_split_markdown_table_row(current)]
            index += 2
            while index < len(lines) and _is_markdown_table_candidate_row(lines[index]):
                rows.append(_split_markdown_table_row(lines[index]))
                index += 1
            table = _render_box_table(rows)
            if table:
                output.append(f"```text\n{table}\n```")
            else:
                output.append(current)
            continue
        output.append(current)
        index += 1

    result = "\n".join(output)
    if had_trailing_newline:
        result += "\n"
    return result


def _convert_markdown_tables_to_fenced_code(text: str) -> str:
    parts = re.split(_FENCED_CODE_PATTERN, text)
    normalized: list[str] = []
    for index, part in enumerate(parts):
        if index % 2 == 1:
            normalized.append(part)
        else:
            normalized.append(_convert_markdown_tables_in_segment(part))
    return "".join(normalized)


def _normalize_markdown_lines(segment: str) -> str:
    lines = segment.splitlines()
    had_trailing_newline = segment.endswith("\n")
    normalized: list[str] = []
    for raw_line in lines:
        line = raw_line
        heading_match = re.match(r"^\s{0,3}#{1,6}\s+(.*)$", line)
        if heading_match:
            title = heading_match.group(1).strip()
            line = f"**{title}**" if title else ""
        else:
            quote_match = re.match(r"^\s*>\s?(.*)$", line)
            if quote_match:
                quote_text = quote_match.group(1).strip()
                line = f"❝ {quote_text}" if quote_text else "❝"
            if _HORIZONTAL_RULE_RE.fullmatch(line.strip() or ""):
                line = "────────────"
            line = re.sub(r"^(?P<indent>[ \t]*)[*+-]\s+", r"\g<indent>◦ ", line)
        normalized.append(line)
    result = "\n".join(normalized)
    if had_trailing_newline:
        result += "\n"
    return result


def _escape_segment_with_markdown(segment: str) -> str:
    """
    Escape MarkdownV2 special chars while preserving common markdown styles.
    Supported inline styles in plain-text segments:
    - bold: **text**, __text__
    - italic: *text*, _text_
    - strikethrough: ~~text~~
    - inline code: `code`
    - links: [label](https://...)
    """
    normalized = _normalize_markdown_lines(segment)
    placeholders: list[tuple[str, str]] = []

    def add_placeholder(rendered: str) -> str:
        token = f"TGMDTOKEN{len(placeholders)}END"
        placeholders.append((token, rendered))
        return token

    def bold_replacer(match: re.Match[str]) -> str:
        inner = (match.group(1) or match.group(2) or "").strip()
        if not inner:
            return ""
        return add_placeholder(f"*{escape_markdown_v2(inner)}*")

    def italic_replacer(match: re.Match[str]) -> str:
        inner = (match.group(1) or match.group(2) or "").strip()
        if not inner:
            return ""
        return add_placeholder(f"_{escape_markdown_v2(inner)}_")

    def strike_replacer(match: re.Match[str]) -> str:
        inner = (match.group(1) or "").strip()
        if not inner:
            return ""
        return add_placeholder(f"~{escape_markdown_v2(inner)}~")

    def code_replacer(match: re.Match[str]) -> str:
        inner = match.group(1)
        return add_placeholder(f"`{_escape_inline_code(inner)}`")

    def link_replacer(match: re.Match[str]) -> str:
        label = match.group(1)
        url = match.group(2)
        return add_placeholder(f"[{escape_markdown_v2(label)}]({_escape_markdown_v2_url(url)})")

    normalized = _MARKDOWN_LINK_RE.sub(link_replacer, normalized)
    normalized = _INLINE_CODE_RE.sub(code_replacer, normalized)
    normalized = re.sub(r"\*\*(.+?)\*\*|__(.+?)__", bold_replacer, normalized)
    normalized = re.sub(r"~~(.+?)~~", strike_replacer, normalized)
    normalized = re.sub(r"(?<!\*)\*([^*\n][^*\n]*?)\*(?!\*)|(?<!\w)_([^_\n]+)_(?!\w)", italic_replacer, normalized)
    escaped = escape_markdown_v2(normalized)
    for token, rendered in placeholders:
        escaped = escaped.replace(token, rendered)
    return escaped


def render_llm_markdown_v2(
    text: str,
    parse_mode: Literal["MarkdownV2", "Markdown"] = "MarkdownV2"
) -> str:
    """
    Renders LLM response text for Telegram MarkdownV2.

    Behavior:
    - Preserves fenced code blocks (```...```) unchanged
    - Converts markdown tables to readable box tables inside fenced code blocks
    - Preserves common markdown inline styles where safe in Telegram MarkdownV2
    - Escapes remaining MarkdownV2 special characters safely
    """
    if parse_mode != "MarkdownV2":
        return text

    normalized_text = _convert_markdown_tables_to_fenced_code(text)
    parts = re.split(_FENCED_CODE_PATTERN, normalized_text)

    result = []
    for i, part in enumerate(parts):
        if i % 2 == 1:
            result.append(part)
        else:
            result.append(_escape_segment_with_markdown(part))

    return "".join(result)
