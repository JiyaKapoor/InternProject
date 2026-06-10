"""
Simple RAG agent for answering user questions from the indexed documents.

Usage:
    python RAGAgent.py
"""

import asyncio
import logging
import os
from pathlib import Path

from dotenv import load_dotenv
from google import genai
from langchain_mistralai import ChatMistralAI

PROJECT_ROOT = Path(__file__).resolve().parents[1]
load_dotenv(PROJECT_ROOT / ".env")

from Embedder import embed_query
from Store import hybrid_search

logging.basicConfig(level=logging.INFO, format="%(asctime)s | %(levelname)s | %(message)s")
log = logging.getLogger(__name__)

GEMINI_API_KEY = os.getenv("GEMINI_API_KEY", "")
MISTRAL_API_KEY = os.getenv("MISTRAL_API_KEY", "")


def _build_prompt(question: str, chunks: list[dict]) -> str:
    if not chunks:
        return """
You are a helpful assistant.
Answer the user using only the provided context.
If the context does not contain the answer, say that you do not have enough information.

User question: {question}

Relevant context:
No relevant context was found.
""".format(question=question)

    context_text = "\n\n".join(
        f"[Source: {chunk.get('source_url', 'unknown')} | Product: {chunk.get('product', 'general')}]\n"
        f"{chunk.get('content', '').strip()}"
        for chunk in chunks
    )

    return """
You are a helpful support assistant.
Answer the user's question using only the supplied context from the indexed knowledge base.
If the answer is not in the context, say you do not have enough information.
Cite the source URLs when possible.

User question: {question}

Relevant context:
{context_text}
""".format(question=question, context_text=context_text)


async def answer_query(question: str, product_filter: str | None = None, top_k: int = 5) -> dict:
    """
    Retrieve the most relevant chunks from Supabase and generate an answer.
    Returns a dictionary with the answer and source metadata.
    """
    if not (MISTRAL_API_KEY or GEMINI_API_KEY):
        raise ValueError("Set MISTRAL_API_KEY or GEMINI_API_KEY in .env")

    log.info("🔎 Retrieving relevant context...")
    query_embedding = await embed_query(question)
    chunks = await hybrid_search(query_embedding, question, product_filter=product_filter, top_k=top_k)

    if not chunks:
        return {
            "answer": "I could not find relevant documentation for that question.",
            "sources": [],
            "chunk_count": 0,
        }

    prompt = _build_prompt(question, chunks)

    if MISTRAL_API_KEY:
        llm = ChatMistralAI(model_name="mistral-small-latest", api_key=MISTRAL_API_KEY)
        log.info("🧠 Generating answer with Mistral AI...")
        response = llm.invoke(prompt)
        answer_text = getattr(response, "content", "") or str(response)
    else:
        client = genai.Client(api_key=GEMINI_API_KEY)
        log.info("🧠 Generating answer with Gemini...")
        response = client.models.generate_content(
            model="gemini-2.0-flash",
            contents=prompt,
        )
        answer_text = getattr(response, "text", "") or str(response)

    return {
        "answer": answer_text.strip(),
        "sources": [
            {
                "source_url": chunk.get("source_url"),
                "product": chunk.get("product"),
                "doc_type": chunk.get("doc_type"),
                "score": chunk.get("rrf_score"),
            }
            for chunk in chunks
        ],
        "chunk_count": len(chunks),
    }


async def main() -> None:
    print("\nRAG Assistant ready. Type 'quit' to exit.\n")
    while True:
        question = input("Ask a question: ").strip()
        if not question or question.lower() in {"quit", "exit"}:
            print("Goodbye.")
            break

        result = await answer_query(question)
        print("\nAnswer:\n")
        print(result["answer"])
        print("\nSources:")
        for i, src in enumerate(result["sources"], start=1):
            print(f"  {i}. {src.get('source_url') or 'unknown'}")
        print("\n")


if __name__ == "__main__":
    asyncio.run(main())
