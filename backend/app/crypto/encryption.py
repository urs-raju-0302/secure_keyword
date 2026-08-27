"""AES-256-GCM authenticated encryption. Never reuse nonce with same key."""

from __future__ import annotations

from dataclasses import dataclass

from cryptography.exceptions import InvalidTag
from cryptography.hazmat.primitives.ciphers.aead import AESGCM

from app.crypto.random import random_nonce


@dataclass(frozen=True)
class EncryptedPayload:
    ciphertext: bytes
    nonce: bytes
    algorithm: str = "AES-256-GCM"


class EncryptionError(Exception):
    """Raised when encryption/decryption fails safely."""


def encrypt(plaintext: bytes, dek: bytes, associated_data: bytes | None = None) -> EncryptedPayload:
    if len(dek) != 32:
        raise EncryptionError("DEK must be 32 bytes for AES-256-GCM")
    nonce = random_nonce(12)
    aesgcm = AESGCM(dek)
    # AESGCM.encrypt appends the authentication tag to ciphertext
    ciphertext = aesgcm.encrypt(nonce, plaintext, associated_data)
    return EncryptedPayload(ciphertext=ciphertext, nonce=nonce)


def decrypt(
    ciphertext: bytes,
    dek: bytes,
    nonce: bytes,
    associated_data: bytes | None = None,
) -> bytes:
    if len(dek) != 32:
        raise EncryptionError("DEK must be 32 bytes for AES-256-GCM")
    aesgcm = AESGCM(dek)
    try:
        return aesgcm.decrypt(nonce, ciphertext, associated_data)
    except InvalidTag as exc:
        # Integrity/authenticity failure — do not return plaintext
        raise EncryptionError("Ciphertext authentication failed") from exc
