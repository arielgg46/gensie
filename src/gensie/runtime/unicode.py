from __future__ import annotations

import re
import unicodedata
from typing import Any


_LITERAL_UNICODE_ESCAPE_RE = re.compile(r"\\u([0-9a-fA-F]{4})")


def normalize_model_output_strings(value: Any) -> Any:
    if isinstance(value, str):
        return unicodedata.normalize("NFC", _decode_literal_unicode_escapes(value))
    if isinstance(value, list):
        return [normalize_model_output_strings(item) for item in value]
    if isinstance(value, dict):
        return {
            key: normalize_model_output_strings(item)
            for key, item in value.items()
        }
    return value


def _decode_literal_unicode_escapes(value: str) -> str:
    def replace(match: re.Match[str]) -> str:
        codepoint = int(match.group(1), 16)
        if codepoint < 0x20 or 0xD800 <= codepoint <= 0xDFFF:
            return match.group(0)
        return chr(codepoint)

    return _LITERAL_UNICODE_ESCAPE_RE.sub(replace, value)
