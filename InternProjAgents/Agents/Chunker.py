"""
Section-Aware Chunker
Splits MS Docs at H2/H3 heading boundaries first, then applies token-based
splitting within sections. This preserves semantic coherence far better than
pure fixed-size chunking for technical documentation.
"""

import re
from langchain_text_splitters import RecursiveCharacterTextSplitter

# Chunk config
CHUNK_SIZE    = 700     # larger chunks for technical articles
CHUNK_OVERLAP = 100     # keep context around section boundaries


def chunk_documents(documents: list[dict]) -> list[dict]:
    """Chunk all documents, returning flat list of chunk dicts."""
    all_chunks = []
    for doc in documents:
        chunks = _chunk_single(doc)
        all_chunks.extend(chunks)
    return all_chunks


def _chunk_single(doc: dict) -> list[dict]:
    """
    Chunk strategy:
    - MS Docs: split at heading boundaries first, then by token size
      while preserving article title and section hierarchy.
    - Incidents: split by token size only (already short, structured text)
    """
    content  = doc["content"]
    doc_type = doc.get("doc_type", "ms_docs")

    if doc_type == "ms_docs":
        sections = _semantic_sections(doc, content)
    else:
        sections = [content]  # incidents are short — treat as one section

    splitter = RecursiveCharacterTextSplitter(
        chunk_size=CHUNK_SIZE * 4,      # convert tokens → chars (approx)
        chunk_overlap=CHUNK_OVERLAP * 4,
        separators=["\n\n", "\n", ". ", " ", ""],
    )

    chunks = []
    for section_idx, section in enumerate(sections):
        section = section.strip()
        if not section:
            continue

        sub_chunks = splitter.split_text(section)
        for chunk_idx, chunk_text in enumerate(sub_chunks):
            if len(chunk_text.strip()) < 50:   # skip near-empty chunks
                continue
            heading_path = _extract_heading_path(section)
            title = doc.get("title") or ""
            chunk_text = chunk_text.strip()

            if title:
                content_with_context = f"Title: {title}\nSection: {heading_path}\n\n{chunk_text}"
            else:
                content_with_context = f"Section: {heading_path}\n\n{chunk_text}"

            chunks.append({
                "content": content_with_context,
                "source_url": doc.get("url", ""),
                "doc_type": doc_type,
                "product": doc.get("product", "general"),
                "title": title,
                "source_path": doc.get("source_path", ""),
                "section_index": section_idx,
                "chunk_index": chunk_idx,
                "sys_id": doc.get("sys_id"),
                "ticket_number": doc.get("ticket_number"),
            })

    return chunks


def _semantic_sections(doc: dict, text: str) -> list[str]:
    """
    Build a small number of high-signal chunks for support articles:
    1) title + summary/cause context
    2) resolution steps
    3) more information (if present)
    This keeps the article coherent for semantic search.
    """
    title = (doc.get("title") or "").strip()
    description = (doc.get("description") or "").strip()
    lines = text.splitlines()

    # Find major heading blocks
    sections = []
    current_heading = None
    current_lines = []

    for line in lines:
        if re.match(r"^#{1,6}\s+.+", line):
            if current_heading and current_lines:
                sections.append((current_heading, "\n".join(current_lines).strip()))
            current_heading = line.strip()
            current_lines = []
        else:
            if current_heading:
                current_lines.append(line)

    if current_heading and current_lines:
        sections.append((current_heading, "\n".join(current_lines).strip()))

    summary_parts = []
    if title:
        summary_parts.append(f"Title: {title}")
    if description:
        summary_parts.append(f"Description: {description}")

    for heading, body in sections:
        h = heading.lstrip('#').strip().lower()
        if h.startswith("symptoms") or h.startswith("cause") or h.startswith("resolution") or h.startswith("more information"):
            summary_parts.append(f"\n## {heading.lstrip('#').strip()}\n{body}")

    # Build one summary chunk that keeps the title + description + problem context together.
    summary_text = "\n\n".join(summary_parts).strip()
    chunks = []
    if summary_text:
        chunks.append(summary_text)

    # Keep resolution and more-information sections as separate, larger chunks.
    for heading, body in sections:
        h = heading.lstrip('#').strip().lower()
        if h.startswith("resolution") or h.startswith("more information"):
            chunks.append(f"Title: {title}\n\n## {heading.lstrip('#').strip()}\n{body}".strip())

    return chunks or [text]


def _split_by_headings(text: str) -> list[str]:
    """
    Split MS Docs markdown into heading-aware sections while keeping the
    heading line with the section content.
    """
    lines = text.splitlines()
    sections = []
    current = []

    for line in lines:
        if re.match(r"^#{1,6}\s+.+", line):
            if current:
                sections.append("\n".join(current).strip())
            current = [line]
        else:
            if current:
                current.append(line)
            elif line.strip():
                current = [line]

    if current:
        sections.append("\n".join(current).strip())

    return [s for s in sections if s.strip()]


def _extract_heading_path(section: str) -> str:
    headings = [line.strip().lstrip('#').strip() for line in section.splitlines() if re.match(r"^#{1,6}\s+.+", line)]
    return " > ".join(headings) if headings else "Overview"