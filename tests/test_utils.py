"""Tests for utility helpers."""

import pytest

from aria.utils import format_code_block


@pytest.mark.parametrize(
    ("code", "language", "expected"),
    [
        ("", "python", "```python\n\n```"),
        ("print('hello')", "javascript", "```javascript\nprint('hello')\n```"),
        ("line one\nline two\n", "text", "```text\nline one\nline two\n\n```"),
    ],
)
def test_format_code_block_preserves_content_boundaries(code, language, expected):
    """Format empty, custom-language, and trailing-newline code verbatim."""
    assert format_code_block(code, language) == expected


@pytest.mark.parametrize(
    ("code", "language", "expected"),
    [
        (None, "python", "```python\nNone\n```"),
        ("value", None, "```None\nvalue\n```"),
    ],
)
def test_format_code_block_interpolates_non_string_arguments(code, language, expected):
    """Document the helper's f-string coercion for unvalidated arguments."""
    assert format_code_block(code, language) == expected
