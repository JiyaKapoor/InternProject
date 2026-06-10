"""
pgvector Store
Upserts embedded chunks into Supabase pgvector with content_hash deduplication.
Also exposes hybrid_search() used by the retrieval agent.
"""

import json
import logging
import math
import os

from supabase import create_client, Client

log = logging.getLogger(__name__)

SUPABASE_URL = os.getenv("SUPABASE_URL", "")
SUPABASE_KEY = os.getenv("SUPABASE_KEY", "")   # use service_role key for writes
TABLE_NAME   = "documents"
MATCH_COUNT  = 10
BATCH_SIZE   = 25   # upsert in batches, not one-by-one


def _get_client() -> Client:
    if not SUPABASE_URL or not SUPABASE_KEY:
        raise ValueError("SUPABASE_URL and SUPABASE_KEY must be set in .env")
    return create_client(SUPABASE_URL, SUPABASE_KEY)


async def upsert_chunks(chunks: list[dict]) -> int:
    """
    Batch-upsert chunks into pgvector.
    Dedup is handled by ON CONFLICT (content_hash) DO NOTHING in Postgres —
    no select-then-insert round trip, which was causing the Storage 404 bug.
    Returns count of newly inserted chunks.
    """
    client = _get_client()
    inserted = 0

    for i in range(0, len(chunks), BATCH_SIZE):
        batch = chunks[i : i + BATCH_SIZE]
        rows = [
            {
                "content":       chunk["content"],
                "embedding":     chunk["embedding"],
                "source_url":    chunk.get("source_url", ""),
                "doc_type":      chunk.get("doc_type", "ms_docs"),
                "product":       chunk.get("product", "general"),
                "error_codes":   chunk.get("error_codes", []),
                "severity":      chunk.get("severity", "low"),
                "chunk_index":   chunk.get("chunk_index", 0),
                "content_hash":  chunk["content_hash"],
                "indexed_at":    chunk.get("indexed_at"),
                "ticket_number": chunk.get("ticket_number"),
            }
            for chunk in batch
        ]
        try:
            result = (
                client.table(TABLE_NAME)
                .upsert(rows, on_conflict="content_hash", ignore_duplicates=True)
                .execute()
            )
            batch_inserted = len(result.data) if result.data else 0
            inserted += batch_inserted
            log.info(f"   Batch {i // BATCH_SIZE + 1}: {batch_inserted} new rows inserted")
        except Exception as e:
            log.warning(f"  ⚠️  Batch {i // BATCH_SIZE + 1} failed: {e}")

    return inserted
async def hybrid_search(
    query_embedding: list[float],
    query_text: str,
    product_filter: str | None = None,
    top_k: int = MATCH_COUNT,
) -> list[dict]:
    """
    Hybrid search: full cosine similarity scan + BM25 re-ranking via RRF.
    No RPC dependency — fetches all chunks directly from Supabase.
    """
    client = _get_client()

    def _to_vector(value) -> list[float]:
        if isinstance(value, list):
            return [float(x) for x in value]
        if isinstance(value, str):
            try:
                parsed = json.loads(value)
                if isinstance(parsed, list):
                    return [float(x) for x in parsed]
            except Exception:
                pass
            return [float(x.strip()) for x in value.strip("[]").split(",") if x.strip()]
        return []

    def _cosine_similarity(a: list[float], b: list[float]) -> float:
        dot = sum(x * y for x, y in zip(a, b))
        norm_a = math.sqrt(sum(x * x for x in a))
        norm_b = math.sqrt(sum(y * y for y in b))
        if norm_a == 0 or norm_b == 0:
            return 0.0
        return dot / (norm_a * norm_b)

    # Step 1: Fetch all chunks — filter by product first to reduce payload
    try:
        query = client.table(TABLE_NAME).select(
            "id, content, source_url, product, doc_type, error_codes, severity, ticket_number, embedding"
        )
        if product_filter:
            query = query.eq("product", product_filter)

        rows = query.execute().data or []
        log.info(f"  📦 Fetched {len(rows)} chunks for cosine search")
    except Exception as e:
        log.error(f"  ❌ Failed to fetch chunks: {e}")
        return []

    if not rows:
        return []

    # Step 2: Score all chunks by cosine similarity
    scored = []
    for row in rows:
        emb = _to_vector(row.get("embedding"))
        if not emb:
            continue
        score = _cosine_similarity(query_embedding, emb)
        if score > 0:
            scored.append({**row, "vector_score": score})

    # Sort by cosine score, keep top 3x for BM25 re-ranking
    candidates = sorted(scored, key=lambda x: x["vector_score"], reverse=True)[: top_k * 3]

    if not candidates:
        return []

    # Step 3: BM25 re-ranking over cosine candidates
    from rank_bm25 import BM25Okapi
    corpus = [r["content"].lower().split() for r in candidates]
    bm25 = BM25Okapi(corpus)
    query_tokens = query_text.lower().split()
    bm25_scores = bm25.get_scores(query_tokens)

    # Step 4: RRF fusion
    sorted_bm25_indices = sorted(
        range(len(bm25_scores)), key=lambda x: bm25_scores[x], reverse=True
    )
    bm25_rank_map = {idx: rank + 1 for rank, idx in enumerate(sorted_bm25_indices)}

    for i, result in enumerate(candidates):
        vector_rank = i + 1
        bm25_rank = bm25_rank_map.get(i, len(candidates))
        result["rrf_score"] = (1 / (60 + vector_rank)) + (1 / (60 + bm25_rank))

    reranked = sorted(candidates, key=lambda x: x["rrf_score"], reverse=True)
    return reranked[:top_k]