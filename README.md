# ClauseLedger

**Evidence-first contract search, built as a small API.**

I've found that a contract-search demo is far more useful when it shows *where* an answer came from, rather than generating confident text without evidence. ClauseLedger stores documents locally, keeps exact character offsets for every passage, ranks passages using word and character TF–IDF, and returns explicit source citations. It also highlights a few simple clause patterns as review signals.

## What's implemented
- `POST /documents`: content-hash idempotent ingestion; SQLite passage store
- `GET /search?q=...`: hybrid lexical retrieval with document, source and character offsets
- `GET /documents/{id}/signals`: explicit rule matches for termination, renewal, indemnity, liability and governing law
- `GET /audit`: local query history; `GET /health`: liveness check
- FastAPI type validation, unit/API tests, container recipe, CI

## Quick start
```bash
python -m venv .venv
source .venv/bin/activate
pip install -e '.[test]'
uvicorn clauseledger.api:app --reload
```
Then open `http://127.0.0.1:8000/docs`. A minimal ingestion request:
```bash
curl -X POST http://127.0.0.1:8000/documents -H 'Content-Type: application/json' \
  -d '{"source":"sample.txt","content":"This agreement has automatic renewal. The governing law is England."}'
curl 'http://127.0.0.1:8000/search?q=governing%20law'
pytest -q
```

## Design decisions
`document -> hashed deduplication -> offset-preserving chunking -> SQLite -> lexical reranking -> cited hits`. Two separately normalized TF–IDF signals make the scoring transparent. Rule-based clause flags deliberately do **not** pretend to be legal conclusions or LLM answers.

## Next steps / limits
The index is rebuilt for each query, which is appropriate for a small local demo but not for large collections. The API has no authentication, tenant isolation or encryption at rest; never expose it publicly or upload confidential agreements. In a production build I would add background ingestion, persistent ANN/sparse indexes, access control, redaction, evaluation sets and observability. This is a reference implementation, not legal advice.

## Retrieval evaluation
```bash
python -m clauseledger.evaluation
```
Runs a deliberately small source-retrieval benchmark against three invented contracts, reporting MRR@5. It is a functional regression check, **not** a representative legal-search benchmark or a claimed production accuracy figure.
