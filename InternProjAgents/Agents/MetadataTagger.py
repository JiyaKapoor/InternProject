"""
Metadata Tagger
Enriches each chunk with structured metadata used for filtered retrieval.
Metadata lets the retrieval agent narrow search BEFORE semantic similarity —
e.g. "only search azure_monitor chunks" for an Azure alert ticket.
"""

import hashlib
import re
from datetime import datetime, timezone


# Error code patterns to extract from content
_ERROR_CODE_PATTERNS = [
    r"\b(0x[0-9A-Fa-f]{4,8})\b",       # hex codes: 0x80070005
    r"\b(AADSTS\d{5,6})\b",             # Entra/AAD errors
    r"\b(Error\s+\d{4,6})\b",           # generic Error 12345
    r"\b(\d{4,6})\b(?=.*error)",        # numeric codes near "error"
    r"\b(HTTP\s+[45]\d{2})\b",          # HTTP errors
]

# Keywords that map content to products (fallback when product is "general")
_PRODUCT_KEYWORDS = {
    "azure_monitor":   ["log analytics", "azure monitor", "alert rule", "kql", "workspace"],
    "microsoft_teams": ["teams", "meeting", "call quality", "direct routing"],
    "entra_id":        ["aad", "entra", "active directory", "sso", "oauth", "mfa"],
    "windows_server":  ["windows server", "event log", "iis", "active directory domain"],
    "microsoft_365":   ["exchange", "sharepoint", "outlook", "onedrive", "m365"],
    "azure_networking":["vnet", "nsg", "vpn gateway", "expressroute", "load balancer"],
}


def tag_metadata(chunk: dict) -> dict:
    """Enrich a chunk with derived metadata fields."""
    content_lower = chunk["content"].lower()

    # Infer product from content if not already set
    product = chunk.get("product", "general")
    if product == "general":
        product = _infer_product(content_lower)

    # Extract error codes found in content
    error_codes = _extract_error_codes(chunk["content"])

    # Severity hint from incident priority field or keywords
    severity = _infer_severity(content_lower)

    # Stable dedup hash (content-based, not URL-based)
    content_hash = hashlib.sha256(chunk["content"].encode()).hexdigest()

    return {
        **chunk,
        "product": product,
        "error_codes": error_codes,
        "severity": severity,
        "content_hash": content_hash,
        "indexed_at": datetime.now(timezone.utc).isoformat(),
    }


def _infer_product(content_lower: str) -> str:
    scores = {product: 0 for product in _PRODUCT_KEYWORDS}
    for product, keywords in _PRODUCT_KEYWORDS.items():
        for kw in keywords:
            if kw in content_lower:
                scores[product] += 1
    best = max(scores, key=scores.get)
    return best if scores[best] > 0 else "general"


def _extract_error_codes(content: str) -> list[str]:
    codes = []
    for pattern in _ERROR_CODE_PATTERNS:
        codes.extend(re.findall(pattern, content, re.IGNORECASE))
    return list(set(codes))[:5]   # cap at 5 per chunk


def _infer_severity(content_lower: str) -> str:
    if any(kw in content_lower for kw in ["critical", "sev 1", "p1", "priority: 1 - critical"]):
        return "critical"
    if any(kw in content_lower for kw in ["high", "sev 2", "p2", "priority: 2 - high"]):
        return "high"
    if any(kw in content_lower for kw in ["medium", "sev 3", "p3"]):
        return "medium"
    return "low"