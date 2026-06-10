"""
Embedder
Prefers Mistral AI embeddings for the RAG pipeline and falls back to Gemini only if needed.
"""

import asyncio
import logging
import os

from google import genai
from langchain_mistralai import MistralAIEmbeddings

log = logging.getLogger(__name__)

GEMINI_API_KEY   = os.getenv("GEMINI_API_KEY", "")
MISTRAL_API_KEY  = os.getenv("MISTRAL_API_KEY", "")
EMBEDDING_MODEL  = "mistral-embed"
EMBEDDING_DIM    = 768
BATCH_SIZE       = 20
BATCH_DELAY_SEC  = 1.0


_client = None


def _init_mistral_embeddings():
    if not MISTRAL_API_KEY:
        raise ValueError("MISTRAL_API_KEY is not set in .env")
    return MistralAIEmbeddings(model=EMBEDDING_MODEL, api_key=MISTRAL_API_KEY)


def _init_gemini():
    global _client
    if not GEMINI_API_KEY:
        raise ValueError("GEMINI_API_KEY not set. Get a free key at aistudio.google.com")
    if _client is None:
        _client = genai.Client(api_key=GEMINI_API_KEY)
    return _client


def _get_embedder():
    if MISTRAL_API_KEY:
        return _init_mistral_embeddings()
    return _init_gemini()


async def embed_chunks(chunks: list[dict]) -> list[dict]:
    """
    Embed all chunks using the configured provider.
    Prefers Mistral AI embeddings; falls back to Gemini if needed.
    """
    _get_embedder()
    embedded = []

    # Process in batches
    for i in range(0, len(chunks), BATCH_SIZE):
        batch = chunks[i : i + BATCH_SIZE]
        log.info(f"   Embedding batch {i // BATCH_SIZE + 1} / {-(-len(chunks) // BATCH_SIZE)} ({len(batch)} chunks)")

        try:
            batch_embedded = await _embed_batch(batch)
            embedded.extend(batch_embedded)
        except Exception as e:
            log.error(f"   ❌ Batch {i // BATCH_SIZE + 1} failed: {e}")
            # Skip failed batch — don't crash entire pipeline
            continue

        # Respect rate limits
        if i + BATCH_SIZE < len(chunks):
            await asyncio.sleep(BATCH_DELAY_SEC)

    log.info(f"   ✅ Embedded {len(embedded)} / {len(chunks)} chunks")
    return embedded


async def _embed_batch(chunks: list[dict]) -> list[dict]:
    """Embed a single batch of chunks."""
    # Run in thread pool since Gemini SDK is synchronous
    loop = asyncio.get_event_loop()
    texts = [chunk["content"] for chunk in chunks]

    def _sync_embed():
        if MISTRAL_API_KEY:
            embedder = _init_mistral_embeddings()
            embeddings = embedder.embed_documents(texts)
            return [vector[:EMBEDDING_DIM] for vector in embeddings]

        client = _init_gemini()
        result = client.models.embed_content(
            model="gemini-embedding-001",
            contents=texts,
            config={
                "task_type": "RETRIEVAL_DOCUMENT",
                "output_dimensionality": 768,
            },
        )
        return [item.values for item in result.embeddings]

    embeddings = await loop.run_in_executor(None, _sync_embed)

    return [
        {**chunk, "embedding": embedding}
        for chunk, embedding in zip(chunks, embeddings)
    ]


async def embed_query(query_text: str) -> list[float]:
    """
    Embed a single query string for retrieval.
    Uses the configured provider; prefers Mistral AI.
    """
    _get_embedder()
    loop = asyncio.get_event_loop()

    def _sync_embed():
        if MISTRAL_API_KEY:
            embedder = _init_mistral_embeddings()
            vector = embedder.embed_query(query_text)
            return vector[:EMBEDDING_DIM]

        client = _init_gemini()
        result = client.models.embed_content(
            model="gemini-embedding-001",
            contents=[query_text],
            config={
                "task_type": "RETRIEVAL_QUERY",
                "output_dimensionality": 768,
            },
        )
        return result.embeddings[0].values

    return await loop.run_in_executor(None, _sync_embed)