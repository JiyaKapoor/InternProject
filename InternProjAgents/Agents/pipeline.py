"""
AIOps Ingestion Pipeline - Main Orchestrator
Crawls MS Docs + polls ServiceNow → chunks → embeds → stores in pgvector
"""

import asyncio
import logging
import os
from pathlib import Path
from typing import Literal

from dotenv import load_dotenv
from langgraph.graph import StateGraph, END
from typing_extensions import TypedDict

PROJECT_ROOT = Path(__file__).resolve().parents[1]
load_dotenv(PROJECT_ROOT / ".env")

from .Cleaner import clean_text
from .Chunker import chunk_documents
from .Embedder import embed_chunks
from .MetadataTagger import tag_metadata
from .MSDocsCrawler import MsDocsCrawler
from .Store import upsert_chunks

logging.basicConfig(level=logging.INFO, format="%(asctime)s | %(levelname)s | %(message)s")
log = logging.getLogger(__name__)


# ── State shared across all LangGraph nodes ──────────────────────────────────

class PipelineState(TypedDict):
    source: Literal["ms_docs", "servicenow", "both"]
    raw_documents: list[dict]       # [{content, url, doc_type, product}]
    cleaned_documents: list[dict]
    chunks: list[dict]              # [{content, metadata}]
    tagged_chunks: list[dict]       # chunks + enriched metadata
    embedded_chunks: list[dict]     # chunks + embedding vectors
    stored_count: int
    errors: list[str]


# ── Node 1: Fetch raw documents ───────────────────────────────────────────────

async def fetch_node(state: PipelineState) -> PipelineState:
    log.info("📥 [fetch_node] Starting document fetch...")
    raw_docs = []
    errors = []

    if state["source"] in ("ms_docs", "both"):
        try:
            crawler = MsDocsCrawler(repo_path=r"C:\Users\Jiya123\Downloads\SupportArticles-docs")
            ms_docs = await crawler.crawl_all()
            log.info(f"   ✅ MS Docs: {len(ms_docs)} pages fetched")
            raw_docs.extend(ms_docs)
        except Exception as e:
            log.error(f"   ❌ MS Docs crawl failed: {e}")
            errors.append(f"ms_docs_crawl: {str(e)}")

    if state["source"] in ("servicenow", "both"):
        log.warning("   ⚠️  ServiceNow polling is not implemented in this checkout; skipping.")
        errors.append("servicenow_poll: not implemented in this workspace")

    return {**state, "raw_documents": raw_docs, "errors": errors}


# ── Node 2: Clean raw text ────────────────────────────────────────────────────

def clean_node(state: PipelineState) -> PipelineState:
    log.info("🧹 [clean_node] Cleaning documents...")
    cleaned = []
    for doc in state["raw_documents"]:
        try:
            doc["content"] = clean_text(doc["content"], doc.get("doc_type"))
            if len(doc["content"].strip()) > 100:   # skip near-empty pages
                cleaned.append(doc)
        except Exception as e:
            log.warning(f"   ⚠️  Skipped doc {doc.get('url','?')}: {e}")

    log.info(f"   ✅ {len(cleaned)} / {len(state['raw_documents'])} docs passed cleaning")
    return {**state, "cleaned_documents": cleaned}


# ── Node 3: Chunk documents ───────────────────────────────────────────────────

def chunk_node(state: PipelineState) -> PipelineState:
    log.info("✂️  [chunk_node] Chunking documents...")
    chunks = chunk_documents(state["cleaned_documents"])
    log.info(f"   ✅ {len(chunks)} chunks produced")
    return {**state, "chunks": chunks}


# ── Node 4: Tag metadata ──────────────────────────────────────────────────────

def tag_node(state: PipelineState) -> PipelineState:
    log.info("🏷️  [tag_node] Tagging metadata...")
    tagged = [tag_metadata(chunk) for chunk in state["chunks"]]
    log.info(f"   ✅ Metadata tagged for {len(tagged)} chunks")
    return {**state, "tagged_chunks": tagged}


# ── Node 5: Embed chunks ──────────────────────────────────────────────────────

async def embed_node(state: PipelineState) -> PipelineState:
    log.info("🔢 [embed_node] Generating embeddings...")
    embedded = await embed_chunks(state["tagged_chunks"])
    log.info(f"   ✅ {len(embedded)} chunks embedded")
    return {**state, "embedded_chunks": embedded}


# ── Node 6: Store in pgvector ─────────────────────────────────────────────────

async def store_node(state: PipelineState) -> PipelineState:
    log.info("💾 [store_node] Upserting into pgvector...")
    count = await upsert_chunks(state["embedded_chunks"])
    log.info(f"   ✅ {count} chunks stored (deduped by content_hash)")
    return {**state, "stored_count": count}


# ── Build LangGraph pipeline ──────────────────────────────────────────────────

def build_pipeline() -> StateGraph:
    graph = StateGraph(PipelineState)

    graph.add_node("fetch",  fetch_node)
    graph.add_node("clean",  clean_node)
    graph.add_node("chunk",  chunk_node)
    graph.add_node("tag",    tag_node)
    graph.add_node("embed",  embed_node)
    graph.add_node("store",  store_node)

    graph.set_entry_point("fetch")
    graph.add_edge("fetch", "clean")
    graph.add_edge("clean", "chunk")
    graph.add_edge("chunk", "tag")
    graph.add_edge("tag",   "embed")
    graph.add_edge("embed", "store")
    graph.add_edge("store", END)

    return graph.compile()


# ── Entry point ───────────────────────────────────────────────────────────────

async def run_pipeline(source: Literal["ms_docs", "servicenow", "both"] = "both"):
    pipeline = build_pipeline()

    initial_state: PipelineState = {
        "source": source,
        "raw_documents": [],
        "cleaned_documents": [],
        "chunks": [],
        "tagged_chunks": [],
        "embedded_chunks": [],
        "stored_count": 0,
        "errors": [],
    }

    log.info(f"🚀 Starting AIOps ingestion pipeline | source={source}")
    final_state = await pipeline.ainvoke(initial_state)

    log.info("=" * 60)
    log.info(f"✅ Pipeline complete | chunks stored: {final_state['stored_count']}")
    if final_state["errors"]:
        log.warning(f"⚠️  Errors encountered: {final_state['errors']}")
    return final_state


if __name__ == "__main__":
    # Run full pipeline: MS Docs + ServiceNow
    asyncio.run(run_pipeline(source="both"))

    # Or run individual sources:
    # asyncio.run(run_pipeline(source="ms_docs"))
    # asyncio.run(run_pipeline(source="servicenow"))