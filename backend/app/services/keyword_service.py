"""Keyword extraction and normalization for searchable encryption."""

from __future__ import annotations

import re
import unicodedata
from typing import Iterable


_WORD_RE = re.compile(r"[a-z0-9]+(?:-[a-z0-9]+)*")


def normalize_keyword(keyword: str) -> str:
    """Deterministic normalization policy:

    1. Strip leading/trailing whitespace
    2. Unicode NFKC normalization
    3. Lowercase
    4. Collapse internal whitespace to single spaces
    5. Drop punctuation except hyphens inside tokens
    6. Join remaining tokens with spaces (single-token searches typically one word)
    """
    if keyword is None:
        raise ValueError("keyword is required")
    text = unicodedata.normalize("NFKC", keyword).strip().lower()
    text = re.sub(r"\s+", " ", text)
    tokens = _WORD_RE.findall(text)
    return " ".join(tokens)


def extract_keywords(document_bytes: bytes, content_type: str = "text/plain") -> set[str]:
    """Extract searchable keywords from document bytes.

    Educational extraction: decode as UTF-8 text when possible and tokenize.
    Binary/PDF content without text layer yields empty set (documented limitation).
    """
    try:
        text = document_bytes.decode("utf-8")
    except UnicodeDecodeError:
        # Attempt latin-1 fallback for educational demos; still may fail for binary
        try:
            text = document_bytes.decode("latin-1")
        except Exception:
            return set()

    normalized = normalize_keyword(text)
    if not normalized:
        return set()
    # Also index individual tokens for multi-word documents
    tokens = set(normalized.split(" "))
    tokens.discard("")
    # Cap index size for a single document to avoid abuse
    return set(list(tokens)[:500])


def normalize_keywords(keywords: Iterable[str]) -> set[str]:
    out: set[str] = set()
    for kw in keywords:
        n = normalize_keyword(kw)
        if n:
            out.add(n)
    return out
