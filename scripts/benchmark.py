#!/usr/bin/env python3
"""Educational performance micro-benchmark for crypto + index operations."""

from __future__ import annotations

import json
import statistics
import sys
import time
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
BACKEND = ROOT / "backend"
sys.path.insert(0, str(BACKEND))

from app.crypto.encryption import decrypt, encrypt  # noqa: E402
from app.crypto.hmac_search import generate_search_token  # noqa: E402
from app.crypto.random import random_dek  # noqa: E402
from app.services.keyword_service import extract_keywords, normalize_keyword  # noqa: E402


def timed(fn, repeats: int = 5) -> dict:
    samples = []
    for _ in range(repeats):
        start = time.perf_counter()
        fn()
        samples.append(time.perf_counter() - start)
    return {
        "mean_s": statistics.mean(samples),
        "stdev_s": statistics.pstdev(samples) if len(samples) > 1 else 0.0,
        "repeats": repeats,
    }


def run_for_size(n_docs: int) -> dict:
    dek = random_dek()
    search_key = random_dek()
    docs = [f"document {i} cloud security encryption keyword search".encode() for i in range(n_docs)]

    def encrypt_all():
        for d in docs:
            encrypt(d, dek)

    enc = timed(encrypt_all, repeats=3)

    def extract_all():
        for d in docs:
            extract_keywords(d)

    extract = timed(extract_all, repeats=3)

    tokens_per_doc = []
    start = time.perf_counter()
    index: dict[str, list[int]] = {}
    for i, d in enumerate(docs):
        kws = extract_keywords(d)
        toks = [generate_search_token(search_key, kw) for kw in kws]
        tokens_per_doc.append(len(toks))
        for t in toks:
            index.setdefault(t, []).append(i)
    index_s = time.perf_counter() - start

    needle = generate_search_token(search_key, normalize_keyword("security"))

    def search_once():
        return index.get(needle, [])

    search = timed(search_once, repeats=20)
    sample = encrypt(docs[0], dek)

    def decrypt_one():
        decrypt(sample.ciphertext, dek, sample.nonce)

    dec = timed(decrypt_one, repeats=20)

    return {
        "documents": n_docs,
        "encrypt_all": enc,
        "keyword_extract_all": extract,
        "index_build_s": index_s,
        "avg_tokens_per_doc": statistics.mean(tokens_per_doc) if tokens_per_doc else 0,
        "search_lookup": search,
        "decrypt_one": dec,
        "index_entries": sum(len(v) for v in index.values()),
    }


def main() -> None:
    results = []
    for n in [100, 1000, 10000]:
        print(f"Benchmarking n={n} ...")
        results.append(run_for_size(n))
    out = ROOT / "docs" / "PERFORMANCE_RAW.json"
    out.write_text(json.dumps(results, indent=2), encoding="utf-8")
    print(json.dumps(results, indent=2))
    print(f"Wrote {out}")


if __name__ == "__main__":
    main()
