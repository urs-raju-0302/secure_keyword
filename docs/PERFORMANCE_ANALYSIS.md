# Performance Analysis

Raw data: [PERFORMANCE_RAW.json](PERFORMANCE_RAW.json) from `python scripts/benchmark.py`.

## Measured (in-process micro-benchmark)

| Docs | Encrypt all (mean) | Extract all | Index build | Search lookup | Decrypt one |
|------|--------------------|-------------|-------------|---------------|-------------|
| 100 | ~0.8 ms | ~0.4 ms | ~2 ms | ~negligible | ~µs |
| 1,000 | ~3.7 ms | ~3.5 ms | ~21 ms | ~negligible | ~µs |
| 10,000 | ~34 ms | ~35 ms | ~196 ms | ~negligible | ~µs |

Exact numbers vary by host; see JSON.

## Trade-offs

- **Deterministic tokens** make lookup O(1)/indexed and simple — at the cost of equality leakage.
- **Per-document DEK + GCM** adds encrypt/wrap cost on upload; downloads pay unwrap+decrypt once.
- **Search-key rotation** requires decrypting all docs to reindex — expensive; schedule offline.
- **Index size** scales with tokens × documents; cap tokens per document (500) to limit abuse.
- DB/network latency dominates real deployments vs pure crypto micro-benchmarks.

## Scaling notes

Millions of documents: partition index, consider inverted-index sharding, async reindex workers, and stronger SSE only if threat model demands it.
