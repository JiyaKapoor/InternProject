import re
from bs4 import BeautifulSoup


# Boilerplate phrases common in MS Docs — remove these
_BOILERPLATE_PATTERNS = [
    r"In this article.*?(?=\n\n)",
    r"Feedback\s*Was this page helpful.*",
    r"Submit and view feedback for.*",
    r"Additional resources.*",
    r"Theme\s+Light\s+Dark\s+High contrast.*",
]
def clean_text(raw: str, doc_type: str | None = None) -> str:
    if doc_type in ("open_incident", "resolved_incident"):
        return _clean_plain_text(raw)
    else:
        return _clean_markdown(raw)   # ← changed from _clean_html

def _clean_markdown(text: str) -> str:
    """Clean markdown — remove YAML frontmatter and normalize."""
    # Strip YAML frontmatter (--- ... ---)
    if text.startswith("---"):
        end = text.find("---", 3)
        if end != -1:
            text = text[end + 3:]

    # Remove HTML comments
    text = re.sub(r"<!--.*?-->", "", text, flags=re.DOTALL)
    # Remove image tags
    text = re.sub(r"!\[.*?\]\(.*?\)", "", text)
    # Clean up excessive blank lines
    text = re.sub(r"\n{3,}", "\n\n", text)

    return text.strip()

def _clean_plain_text(text: str) -> str:
    """Light cleanup for already-plain ServiceNow text."""
    return _normalize(text)


def _normalize(text: str) -> str:
    """Shared normalization: boilerplate removal, whitespace cleanup."""
    for pattern in _BOILERPLATE_PATTERNS:
        text = re.sub(pattern, "", text, flags=re.DOTALL | re.IGNORECASE)

    # Collapse excessive newlines
    text = re.sub(r"\n{3,}", "\n\n", text)
    # Collapse multiple spaces
    text = re.sub(r"[ \t]{2,}", " ", text)
    # Strip leading/trailing whitespace per line
    lines = [line.strip() for line in text.splitlines()]
    # Drop very short lines (likely nav artifacts)
    lines = [l for l in lines if len(l) > 3 or l == ""]

    return "\n".join(lines).strip()