# MarkdownV2 Escaping - Developer Quick Reference

## TL;DR - Use These Functions

### For Regular Text
```python
from bot.markdown import escape_markdown_v2

text = "Hello_world! Check (example.com)"
safe = escape_markdown_v2(text)
await message.answer(safe, parse_mode="MarkdownV2")
```

### For LLM Responses (Mixed Text + Code)
```python
from bot.markdown import smart_escape_for_response

response = await llm.generate_reply(...)  # May have code + special chars
escaped = smart_escape_for_response(response)
await message.answer(escaped, parse_mode="MarkdownV2")
```

### For Formatted Text
```python
from bot.markdown import format_bold, format_italic, format_code_block

msg = format_bold("Important: " + username)
await message.answer(msg, parse_mode="MarkdownV2")
```

---

## Function Reference

| Function | Use Case | Input | Output |
|----------|----------|-------|--------|
| `escape_markdown_v2(text)` | Escape all special chars | `"hello_world"` | `"hello\_world"` |
| `smart_escape_for_response(text)` | Mixed text + code | Code in ` ``` ` preserved | Text escaped, code not |
| `format_bold(text)` | Make text **bold** | Any text | `*escaped_text*` |
| `format_italic(text)` | Make text _italic_ | Any text | `_escaped_text_` |
| `format_code_block(code)` | Show code block | Python code | ` ```python code``` ` |
| `format_inline_code(code)` | Inline `code` | Any code | ` `code` ` |
| `format_link(text, url)` | Make clickable link | Text + URL | `[text](url)` |

---

## Always Needed

```python
# ALWAYS add this to every message.answer() call
parse_mode="MarkdownV2"
```

---

## The 18 Special Characters to Know

```
_ * [ ] ( ) ~ ` > # + - = | { } . !
```

These get escaped with a backslash when using `escape_markdown_v2()`.

---

## Common Patterns

### Pattern 1: User Input with Special Chars
```python
user_input = "john_doe@example.com"
safe = escape_markdown_v2(user_input)
await msg.answer(f"User: {safe}", parse_mode="MarkdownV2")
```

### Pattern 2: LLM Code Response
```python
response = await llm.generate(...)  # Returns code in ```
escaped = smart_escape_for_response(response)
await msg.answer(escaped, parse_mode="MarkdownV2")
```

### Pattern 3: Error Message
```python
try:
    # Something
except Exception as e:
    safe_error = escape_markdown_v2(str(e))
    await msg.answer(safe_error, parse_mode="MarkdownV2")
```

### Pattern 4: URL with Special Chars
```python
url = "https://example.com/path(v2)"
safe_url = escape_markdown_v2(url)
await msg.answer(f"Click: {safe_url}", parse_mode="MarkdownV2")
```

---

## DO's and DON'Ts

### ✅ DO's
- ✅ Use `escape_markdown_v2()` for text with special chars
- ✅ Use `smart_escape_for_response()` for mixed content
- ✅ Always include `parse_mode="MarkdownV2"`
- ✅ Escape user inputs and error messages
- ✅ Let code blocks in smart_escape work as-is

### ❌ DON'Ts
- ❌ Don't forget `parse_mode="MarkdownV2"` parameter
- ❌ Don't escape code blocks twice
- ❌ Don't use `escape_markdown_v2()` on already-escaped text
- ❌ Don't escape content inside ` ``` ` blocks manually
- ❌ Don't mix parse_mode values in the same message

---

## Testing Your Changes

```bash
# Run the test suite
python test_markdown_escaping.py

# Expected output
# ======================================================================
# ✅ All tests passed!
```

---

## Files to Know

| File | Purpose |
|------|---------|
| `bot/markdown.py` | The escaping functions (this is what you import) |
| `test_markdown_escaping.py` | Tests to verify everything works |
| `MARKDOWNV2_ESCAPING_GUIDE.md` | Full detailed guide |
| `BEFORE_AFTER_COMPARISON.md` | All code changes |

---

## Import Template

```python
# Use this import in your handler files
from bot.markdown import (
    escape_markdown_v2,       # Escape all special chars
    smart_escape_for_response, # Escape but preserve code blocks
    format_bold,              # Make **bold**
    format_italic,            # Make _italic_
    format_code_block,        # Make code block
    format_inline_code,       # Make inline code
    format_link,              # Make clickable link
)
```

---

## Next Steps

1. ✅ Your bot already has all this integrated
2. ✅ All handlers use `parse_mode="MarkdownV2"`
3. ✅ LLM responses use `smart_escape_for_response()`
4. ✅ Run `python test_markdown_escaping.py` to verify

**You're done!** The bot is ready to use. 🚀

---

## Troubleshooting

### Problem: Text with underscores shows as italic
**Solution:** Make sure you have `parse_mode="MarkdownV2"` and the text is escaped
```python
text = escape_markdown_v2("hello_world")
await msg.answer(text, parse_mode="MarkdownV2")
```

### Problem: Code block is broken with escaped characters inside
**Solution:** Use `smart_escape_for_response()` instead of `escape_markdown_v2()`
```python
response = "```python\nx = 5 * 2\n```"
escaped = smart_escape_for_response(response)  # Correct!
```

### Problem: Special characters not escaping
**Solution:** Check that you're using escape function and parse_mode
```python
safe = escape_markdown_v2(text)  # ← Escape the text
await msg.answer(safe, parse_mode="MarkdownV2")  # ← Add parse_mode
```

---

## Key Reference

**Always remember:**
```python
# The template for safe messages
from bot.markdown import escape_markdown_v2, smart_escape_for_response

# For regular text:
safe_text = escape_markdown_v2(your_text)
await message.answer(safe_text, parse_mode="MarkdownV2")

# For mixed code + text:
safe_text = smart_escape_for_response(your_text)
await message.answer(safe_text, parse_mode="MarkdownV2")
```

That's it! Everything else is just variations on this pattern. ✅
