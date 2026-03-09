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
  3. Allows you to use Markdown formatting like *bold*, _italic_, `code`
"""

from __future__ import annotations

import re
from typing import Literal


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
    special_chars = r'_*[]()~`>#+-=|{}.!'
    
    result = ""
    for char in text:
        if char in special_chars:
            result += '\\' + char  # Escape with backslash
        else:
            result += char
    return result


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
    pattern = r'(```[\s\S]*?```)'
    parts = re.split(pattern, text)
    
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


def _escape_segment_with_bold(segment: str) -> str:
    """
    Escape MarkdownV2 special chars in a text segment while preserving
    Markdown-style bold syntax: **text** -> *text*.
    Also converts list markers at line start: "* item" -> "◦ item".
    """
    placeholders: list[tuple[str, str]] = []

    def bullet_replacer(match: re.Match[str]) -> str:
        indent = match.group("indent")
        token = f"TGBULLETTOKEN{len(placeholders)}END"
        placeholders.append((token, f"{indent}◦ "))
        return token

    def bold_replacer(match: re.Match[str]) -> str:
        inner = match.group(1)
        token = f"TGBOLDTOKEN{len(placeholders)}END"
        placeholders.append((token, f"*{escape_markdown_v2(inner)}*"))
        return token

    # Convert leading-star bullet items before escaping.
    normalized = re.sub(r"(?m)^(?P<indent>[ \t]*)\*\s+", bullet_replacer, segment)
    normalized = re.sub(r"\*\*(.+?)\*\*", bold_replacer, normalized, flags=re.DOTALL)
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
    - Converts Markdown bold (**text**) to Telegram bold (*text*)
    - Escapes remaining MarkdownV2 special characters safely
    """
    if parse_mode != "MarkdownV2":
        return text

    pattern = r"(```[\s\S]*?```)"
    parts = re.split(pattern, text)

    result = []
    for i, part in enumerate(parts):
        if i % 2 == 1:
            result.append(part)
        else:
            result.append(_escape_segment_with_bold(part))

    return "".join(result)
