from app.crypto.encryption import EncryptionError, decrypt, encrypt
from app.crypto.hmac_search import generate_search_token
from app.crypto.key_wrapping import unwrap_dek, wrap_dek
from app.crypto.random import random_dek
from app.services.keyword_service import extract_keywords, normalize_keyword


def test_normalize_keyword():
    assert normalize_keyword("  Cloud-Security  ") == "cloud-security"
    assert normalize_keyword("Hello, World!") == "hello world"
    assert normalize_keyword("AES_GCM") == "aes gcm" or normalize_keyword("AES_GCM") == "aesgcm"


def test_hmac_token_not_plaintext():
    key = random_dek()
    token = generate_search_token(key, "security")
    assert token != "security"
    assert len(token) == 64
    assert generate_search_token(key, "security") == token
    assert generate_search_token(key, "privacy") != token


def test_encrypt_decrypt_roundtrip():
    dek = random_dek()
    pt = b"sensitive cloud document"
    enc = encrypt(pt, dek)
    assert enc.ciphertext != pt
    assert decrypt(enc.ciphertext, dek, enc.nonce) == pt


def test_distinct_nonces():
    dek = random_dek()
    a = encrypt(b"same", dek)
    b = encrypt(b"same", dek)
    assert a.nonce != b.nonce
    assert a.ciphertext != b.ciphertext


def test_tampered_ciphertext_fails():
    dek = random_dek()
    enc = encrypt(b"important", dek)
    tampered = bytearray(enc.ciphertext)
    tampered[0] ^= 0x01
    try:
        decrypt(bytes(tampered), dek, enc.nonce)
        assert False, "should have failed"
    except EncryptionError:
        pass


def test_wrong_dek_fails():
    dek = random_dek()
    enc = encrypt(b"data", dek)
    try:
        decrypt(enc.ciphertext, random_dek(), enc.nonce)
        assert False
    except EncryptionError:
        pass


def test_wrap_unwrap_dek():
    master = random_dek()
    dek = random_dek()
    wrapped = wrap_dek(dek, master, 1)
    assert unwrap_dek(wrapped.wrapped_dek, wrapped.wrap_nonce, master, 1) == dek


def test_extract_keywords():
    kws = extract_keywords(b"Cloud Security Encryption search")
    assert "cloud" in kws
    assert "security" in kws
