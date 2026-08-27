# Testing

```bash
cd backend && python -m pytest -q
```

## Levels

| Level | Coverage |
|-------|----------|
| Unit | normalize, HMAC, encrypt/decrypt, tamper, wrap, JWT |
| Integration | register → login → upload → search → download |
| Security | wrong password, bad JWT, IDOR, admin gate, SQLi payload, path traversal, oversized/empty, tampered ciphertext, rotation |
| Performance | `scripts/benchmark.py` → `PERFORMANCE_RAW.json` |

## Required crypto assertions (implemented)

- encrypt ≠ plaintext; roundtrip; distinct nonces; tamper fails; wrong DEK fails; token ≠ keyword; same keyword+key → same token

## Note

Tests use SQLite + local storage with `ENVIRONMENT=test` (rate limit disabled). Docker uses PostgreSQL + MinIO.
