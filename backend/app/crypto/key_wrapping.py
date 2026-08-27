"""Authenticated DEK wrapping using AES-256-GCM under a versioned KEK."""

from __future__ import annotations

from dataclasses import dataclass

from cryptography.exceptions import InvalidTag
from cryptography.hazmat.primitives import hashes
from cryptography.hazmat.primitives.ciphers.aead import AESGCM
from cryptography.hazmat.primitives.kdf.hkdf import HKDF

from app.crypto.random import random_nonce


class KeyWrappingError(Exception):
    pass


@dataclass(frozen=True)
class WrappedKey:
    wrapped_dek: bytes
    wrap_nonce: bytes
    key_version: int
    algorithm: str = "AES-256-GCM-WRAP"


def derive_kek(master_key: bytes, version: int, purpose: str = "dek-wrap") -> bytes:
    """Derive a versioned KEK from master key material via HKDF-SHA256."""
    info = f"{purpose}:v{version}".encode("utf-8")
    return HKDF(
        algorithm=hashes.SHA256(),
        length=32,
        salt=b"secure-keyword-kek-v1",
        info=info,
    ).derive(master_key)


def wrap_dek(dek: bytes, master_key: bytes, key_version: int) -> WrappedKey:
    if len(dek) != 32:
        raise KeyWrappingError("DEK must be 32 bytes")
    kek = derive_kek(master_key, key_version)
    nonce = random_nonce(12)
    wrapped = AESGCM(kek).encrypt(nonce, dek, f"dek-wrap:v{key_version}".encode())
    return WrappedKey(wrapped_dek=wrapped, wrap_nonce=nonce, key_version=key_version)


def unwrap_dek(
    wrapped_dek: bytes,
    wrap_nonce: bytes,
    master_key: bytes,
    key_version: int,
) -> bytes:
    kek = derive_kek(master_key, key_version)
    try:
        dek = AESGCM(kek).decrypt(wrap_nonce, wrapped_dek, f"dek-wrap:v{key_version}".encode())
    except InvalidTag as exc:
        raise KeyWrappingError("Wrapped DEK authentication failed") from exc
    if len(dek) != 32:
        raise KeyWrappingError("Unwrapped DEK has invalid length")
    return dek


def wrap_search_key(search_key: bytes, master_key: bytes, key_version: int) -> WrappedKey:
    if len(search_key) != 32:
        raise KeyWrappingError("Search key must be 32 bytes")
    kek = derive_kek(master_key, key_version, purpose="search-key-wrap")
    nonce = random_nonce(12)
    wrapped = AESGCM(kek).encrypt(nonce, search_key, f"search-wrap:v{key_version}".encode())
    # Pack nonce || ciphertext for storage in a single column
    return WrappedKey(
        wrapped_dek=nonce + wrapped,
        wrap_nonce=nonce,
        key_version=key_version,
        algorithm="AES-256-GCM-SEARCH-WRAP",
    )


def unwrap_search_key(packed: bytes, master_key: bytes, key_version: int) -> bytes:
    if len(packed) < 13:
        raise KeyWrappingError("Invalid wrapped search key")
    nonce, wrapped = packed[:12], packed[12:]
    kek = derive_kek(master_key, key_version, purpose="search-key-wrap")
    try:
        key = AESGCM(kek).decrypt(nonce, wrapped, f"search-wrap:v{key_version}".encode())
    except InvalidTag as exc:
        raise KeyWrappingError("Wrapped search key authentication failed") from exc
    if len(key) != 32:
        raise KeyWrappingError("Unwrapped search key has invalid length")
    return key
