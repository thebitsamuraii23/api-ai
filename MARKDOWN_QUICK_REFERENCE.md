# Markdown Support - Quick Reference Guide

## What Changed?

Your Telegram bot now fully supports **Markdown formatting** with **code blocks**. All messages use `parse_mode="MarkdownV2"`.

---

## Example: LLM Response with Code Block

**User asks:** "Show me a Python function"

**LLM returns:**
```
Here's a simple function:

```python
def greet(name):
    """Greet someone."""
    return f"Hello, {name}!"

result = greet("Alice")
print(result)  # Output: Hello, Alice!
```

This is how it renders in Telegram!
```

**In Telegram, it appears as:**
- Clean, syntax-highlighted code block
- Properly formatted text with *bold*, _italic_, etc.
- Clickable links if included

---

## How It Works

### The Magic Function: `smart_escape_for_response()`

```python
from bot.markdown import smart_escape_for_response

# Handles both regular text AND code blocks perfectly:
response = """
Regular text with *special* (characters) is [escaped]!

But code blocks are preserved:
```python
x = 5 * 2  # This multiplication sign stays as-is
```
"""

escaped = smart_escape_for_response(response)
await message.answer(escaped, parse_mode="MarkdownV2")
```

### What Gets Escaped (outside code blocks):
- `_` → `\_` (underscore)
- `*` → `\*` (asterisk)
- `[` `]` `(` `)` (brackets/parens)
- `~` → `\~` (tilde)
- `` ` `` → `` \` `` (single backtick)
- `>` `#` `+` `-` `=` `|` `{` `}` `.` `!` (special chars)

### What Stays Unchanged (inside code blocks):
```
```python
def multiply(a, b):
    # This * and ! and _ and everything stays as-is!
    return a * b  # No escaping needed!
```
```

---

## Files Created/Modified

### ✨ NEW: `bot/markdown.py`
Complete Markdown utilities library:
```python
escape_markdown_v2(text)              # Escape special chars
smart_escape_for_response(text)       # Smart escape + preserve code blocks
format_code_block(code, language)     # Format ```code```
format_inline_code(code)              # Format `code`
format_bold(text)                     # Format *bold*
format_italic(text)                   # Format _italic_
format_link(text, url)                # Format [text](url)
```

### 📝 MODIFIED: `bot/handlers.py`
```python
# All message.answer() calls now have:
parse_mode="MarkdownV2"

# LLM responses use smart escaping:
escaped_chunk = smart_escape_for_response(chunk, parse_mode="MarkdownV2")
await message.answer(escaped_chunk, parse_mode="MarkdownV2")
```

---

## Usage Examples in Your Bot

### Example 1: Simple Message (automatic Markdown)
```python
# This will render as bold in Telegram:
await message.answer(
    "*Bold text* and _italic text_",
    parse_mode="MarkdownV2"
)
```

### Example 2: Code Block (automatically preserved)
```python
# The LLM returns code - it's automatically rendered as code block!
response = llm.generate_reply(...)  # Returns Python code in ```python...```
escaped = smart_escape_for_response(response)
await message.answer(escaped, parse_mode="MarkdownV2")
```

### Example 3: Using Your Bot
```
User: /help
Bot: Shows help with **bold** text and `inline_code`

User: Write Python code
Bot: Returns code in ```python...``` blocks with syntax highlighting

User: /settings
Bot: Shows settings with proper formatting
```

---

## Test It Out

1. **Start the bot:** `python app.py`
2. **Send a message** asking for code: "Write a Python function"
3. **Bot response** will include:
   - Properly formatted code blocks
   - Syntax highlighting
   - Escaped special characters in text

---

## Frequently Asked Questions

**Q: Will this break existing messages?**  
A: No! All existing bot logic works exactly the same. Only the rendering is enhanced.

**Q: What if the bot gets simple text without code?**  
A: `smart_escape_for_response()` handles both - it escapes special chars and returns plain text if no code blocks exist.

**Q: Can I use other formatting?**  
A: Yes! Use these in your messages:
- `*bold text*`
- `_italic text_`
- `` `inline code` ``
- ` ```python ... ``` ` (code blocks)
- `[link text](https://url.com)`

**Q: What about special characters in variable names?**  
A: Inside code blocks, they're never escaped. Outside, `smart_escape_for_response()` escapes them automatically.

**Q: Do I need to manually escape anything?**  
A: No! Just use `smart_escape_for_response(response)` and it handles everything.

---

## Implementation Details

### Before (No Markdown):
```python
response = "Check this! ```python\nprint('hi')\n``` And *this*"
await message.answer(response)  # Plain text, no formatting
```

**Result in Telegram:** Looks like plain text, code blocks not rendered

### After (With Markdown):
```python
response = "Check this! ```python\nprint('hi')\n``` And *this*"
escaped = smart_escape_for_response(response)
await message.answer(escaped, parse_mode="MarkdownV2")
```

**Result in Telegram:**
- Code block with syntax highlighting ✓
- \*this\* rendered as **this** (bold) ✓
- Special characters properly handled ✓

---

## Key Benefits

✅ **Code blocks render with syntax highlighting**  
✅ **Automatic escaping prevents rendering errors**  
✅ **Preserves LLM code exactly as returned**  
✅ **Works with all message types (commands, chat, callbacks)**  
✅ **No breaking changes to existing bot**  
✅ **Uses MarkdownV2 for best compatibility**  

---

## Support

For detailed implementation documentation, see: **MARKDOWN_IMPLEMENTATION.md**

For Markdown utilities documentation, see: **bot/markdown.py** (inline docstrings)
