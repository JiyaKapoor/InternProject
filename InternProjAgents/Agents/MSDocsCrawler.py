import logging
import hashlib
import re
from pathlib import Path

log = logging.getLogger(__name__)

# Limit the crawl to the Outlook topics you asked for.
# The crawler will recurse into any internal subfolders under these paths.
PRODUCT_FOLDERS = {
    "outlook_connectivity":     "Outlook/classic-outlook-for-windows/connectivity",
    "outlook_authentication":   "Outlook/classic-outlook-for-windows/authentication",
}

MAX_FILES_PER_PRODUCT = 150   # cap so you don't over-index


class MsDocsCrawler:

    def __init__(self, repo_path: str = "./SupportArticles-docs"):
        self.repo_path = Path(repo_path)
        if not self.repo_path.exists():
            raise FileNotFoundError(
                f"Repo not found at {repo_path}. "
                f"Run: git clone --depth=1 https://github.com/MicrosoftDocs/SupportArticles-docs.git"
            )

    async def crawl_all(self) -> list[dict]:
        all_docs = []
        for product, folder in PRODUCT_FOLDERS.items():
            folder_path = self.repo_path / folder
            if not folder_path.exists():
                log.warning(f"  ⚠️  Folder not found: {folder_path}")
                continue

            docs = self._read_product_folder(product, folder_path)
            log.info(f"  ✅ {product}: {len(docs)} articles loaded")
            all_docs.extend(docs)

        log.info(f"  📚 Total: {len(all_docs)} articles loaded from repo")
        return all_docs

    def _read_product_folder(self, product: str, folder_path: Path) -> list[dict]:
        docs = []
        md_files = list(folder_path.rglob("*.md"))[:MAX_FILES_PER_PRODUCT]

        for md_file in md_files:
            try:
                content = md_file.read_text(encoding="utf-8", errors="ignore")

                # Skip tiny files — likely index/nav pages
                if len(content.strip()) < 300:
                    continue

                # Skip files with no resolution content
                if not self._has_resolution_content(content):
                    continue

                title = self._extract_title(content)
                description = self._extract_description(content)
                relative_path = md_file.relative_to(self.repo_path).as_posix()
                docs.append({
                    "url": f"https://learn.microsoft.com/en-us/troubleshoot/{relative_path}",
                    "content": content,
                    "product": product,
                    "doc_type": "ms_docs",
                    "title": title,
                    "description": description,
                    "source_path": str(md_file.relative_to(self.repo_path)),
                    "content_hash": hashlib.sha256(content.encode()).hexdigest(),
                })
            except Exception as e:
                log.warning(f"  ⚠️  Failed to read {md_file}: {e}")

        return docs

    def _extract_title(self, content: str) -> str:
        match = re.search(r"^title:\s*(.+)$", content, flags=re.MULTILINE)
        return match.group(1).strip() if match else ""

    def _extract_description(self, content: str) -> str:
        match = re.search(r"^description:\s*(.+)$", content, flags=re.MULTILINE)
        return match.group(1).strip() if match else ""

    def _has_resolution_content(self, content: str) -> bool:
        """Only keep articles that have actual resolution steps."""
        content_lower = content.lower()
        resolution_signals = [
            "## resolution", "## cause", "## symptoms", "## workaround",
            "## fix", "## solution", "to resolve", "to fix this issue",
            "follow these steps", "run the following"
        ]
        return any(signal in content_lower for signal in resolution_signals)