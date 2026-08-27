"""Cryptographically secure random helpers. Prefer secrets over SystemRandom."""

from __future__ import annotations

import secrets


def random_bytes(n: int) -> bytes:
    """Return n cryptographically secure random bytes."""
    if n <= 0:
        raise ValueError("n must be positive")
    return secrets.token_bytes(n)


def random_dek() -> bytes:
    """Generate a 256-bit Data Encryption Key."""
    return random_bytes(32)


def random_nonce(n: int = 12) -> bytes:
    """Generate a unique nonce for AES-GCM (default 96-bit)."""
    return random_bytes(n)
