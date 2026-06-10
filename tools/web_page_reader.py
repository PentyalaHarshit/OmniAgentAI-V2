"""
tools/web_page_reader.py
========================
Page Content Extractor.

ReAct Stage: Action — fetch full page body from a URL and extract clean text.

Optionally enriches search-result snippets by downloading the actual page
and stripping boilerplate HTML (nav, header, footer, scripts).
"""

import re
import logging
import requests
from bs4 import BeautifulSoup

logger = logging.getLogger(__name__)

_HEADERS = {"User-Agent": "Mozilla/5.0 (compatible; OmniAgentAI/1.0)"}
_TIMEOUT = 10


class WebPageReader:
    """
    Fetches a URL and extracts clean body text.

    Usage
    -----
        reader = WebPageReader()
        text = reader.fetch("https://en.wikipedia.org/wiki/Chola_dynasty")
    """

    def __init__(self, timeout: int = _TIMEOUT, max_chars: int = 3000):
        self.timeout   = timeout
        self.max_chars = max_chars

    def fetch(self, url: str) -> str:
        """
        Downloads the page, strips boilerplate, returns clean text.
        Returns "" on any network / parse error.
        """
        if not url or not url.startswith("http"):
            return ""
        try:
            resp = requests.get(url, timeout=self.timeout, headers=_HEADERS)
            resp.raise_for_status()
            return self._extract(resp.text)
        except requests.RequestException as e:
            logger.debug("[PageReader] Request failed for %s: %s", url, e)
        except Exception as e:
            logger.debug("[PageReader] Parse error for %s: %s", url, e)
        return ""

    def _extract(self, html: str) -> str:
        """Strip boilerplate and return clean body text."""
        soup = BeautifulSoup(html, "html.parser")

        # Remove non-content elements
        for tag in soup(["script", "style", "nav", "header",
                          "footer", "aside", "form", "noscript"]):
            tag.decompose()

        text = soup.get_text(separator=" ", strip=True)
        text = re.sub(r"\s+", " ", text).strip()
        return text[: self.max_chars]

    def enrich_docs(self, docs: list[dict]) -> list[dict]:
        """
        For each doc that has a URL and a short snippet, fetch the full page
        and replace the snippet with richer content.

        Only enriches if snippet is shorter than 200 chars to avoid extra
        network calls when we already have good content.
        """
        enriched: list[dict] = []
        for doc in docs:
            url     = doc.get("url", "")
            snippet = doc.get("text", "")
            if url and len(snippet) < 200:
                page_text = self.fetch(url)
                if page_text:
                    doc = {**doc, "text": page_text, "source": "page_fetch"}
            enriched.append(doc)
        return enriched
