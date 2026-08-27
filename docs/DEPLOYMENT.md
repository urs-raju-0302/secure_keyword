# Deployment

## Educational / local

```bash
cp .env.example .env   # set secrets
docker compose up --build
```

Services: postgres, minio, minio-init, backend (migrate+seed+uvicorn), frontend (nginx).

Health checks on postgres and backend. Backend runs as non-root (`appuser`).

## Environment variables

See `.env.example`: `DATABASE_URL`, `JWT_SECRET`, `MASTER_KEY`, MinIO settings, `CORS_ORIGINS`.

Generate with `python scripts/gen_dev_secrets.py`. Never commit `.env`.

## Production architecture notes (not claimed as implemented)

- TLS everywhere (reverse proxy / cloud LB)
- AWS KMS or Vault for master keys (not env-equivalent to HSM)
- Managed PostgreSQL, private object storage, IAM roles
- Secret manager, WAF/rate limiting, centralized monitoring
- Immutable audit sink, DR for keys, penetration test
- Stronger SSE if required

## Makefile

`make up` · `make down` · `make migrate` · `make seed` · `make test` · `make bench`
