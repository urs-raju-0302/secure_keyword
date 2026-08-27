"""Deterministic searchable-encryption tokens via HMAC-SHA-256.

Leakage note: identical keywords produce identical tokens under the same
search-key version (search-pattern / equality leakage).
"""

from __future__ import annotations

import hmac
from hashlib import sha256


def generate_search_token(search_key: bytes, normalized_keyword: str) -> str:
    if not search_key:
        raise ValueError("search_key must not be empty")
    if not normalized_keyword:
        raise ValueError("normalized_keyword must not be empty")
    digest = hmac.new(search_key, normalized_keyword.encode("utf-8"), sha256).digest()
    return digest.hex()
