"""Thin service wrapper around crypto.encryption for DI clarity."""

from __future__ import annotations

from app.crypto.encryption import EncryptedPayload, EncryptionError, decrypt, encrypt


class EncryptionService:
    def encrypt(self, data: bytes, dek: bytes, associated_data: bytes | None = None) -> EncryptedPayload:
        return encrypt(data, dek, associated_data)

    def decrypt(
        self,
        ciphertext: bytes,
        dek: bytes,
        nonce: bytes,
        associated_data: bytes | None = None,
    ) -> bytes:
        return decrypt(ciphertext, dek, nonce, associated_data)


__all__ = ["EncryptionService", "EncryptionError", "EncryptedPayload"]
