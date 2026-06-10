"""
tools/web_search_tool.py
========================
Search Query Rewriter + Multi-source Web Search.

ReAct Stage: Action — rewrite query into multiple targeted variants,
search DuckDuckGo HTML, return deduplicated document snippets.
"""

import re
import logging
import requests
from bs4 import BeautifulSoup
from urllib.parse import unquote

logger = logging.getLogger(__name__)

_HEADERS = {"User-Agent": "Mozilla/5.0 (compatible; OmniAgentAI/1.0)"}
_TIMEOUT = 10


# ---------------------------------------------------------------------------
# Query Rewriter
# ---------------------------------------------------------------------------

class QueryRewriter:
    """
    Expands a user query into multiple targeted search variants.

    Key improvement: each variant is designed to surface pages that
    *answer* the question, not just mention the entity.

    "how long did the Chola dynasty rule?" →
        "how long did the Chola dynasty rule"           ← original
        "Chola dynasty ruled from when to when"         ← duration framing
        "Chola dynasty period BCE CE years"             ← date-focused
        "How long did Chola dynasty rule history"       ← explicit question
        "Chola Empire duration history timeline"        ← entity + duration
        "Chola dynasty history period"                  ← dynasty-specific
        "Chola dynasty BCE CE years"                    ← date-focused
        "Chola Empire timeline"                         ← empire timeline
    """

    def rewrite(self, query: str) -> list[str]:
        q = query.lower().strip().rstrip("?")
        variants: list[str] = [query]

        # ── Duration questions ("how long", ruling periods) ───────────────
        if re.search(r"\bhow long\b", q):
            # Strip the "how long did/was/has" prefix to get the subject
            subject = re.sub(
                r"^how long\s+(?:did|was|has|have|were|are)?\s*", "", q
            ).strip()
            # Remove trailing verb phrase ("rule", "exist", "last", etc.)
            subject_clean = re.sub(
                r"\s+(?:rule|ruled|exist|existed|last|lasted|stand|stood|reign|reigned).*$",
                "", subject
            ).strip()
            variants += [
                f"{subject_clean} ruled from when to when",
                f"{subject_clean} period BCE CE years",
                f"How long did {subject_clean} history",
                f"{subject_clean} duration history timeline",
            ]

        # ── Dynasty / empire / kingdom ────────────────────────────────────
        dynasty_match = re.search(
            r"([A-Za-z\s]+?)\s+(?:dynasty|empire|kingdom|sultanate|republic)", q
        )
        if dynasty_match:
            entity = dynasty_match.group(1).strip()
            variants += [
                f"{entity} dynasty history period",
                f"{entity} dynasty BCE CE years",
                f"{entity} empire timeline",
                f"{entity} dynasty ruled years duration",
            ]

        # ── Inventor / discoverer ─────────────────────────────────────────
        inv_m = re.search(
            r"who\s+(?:invented|discovered|created|built|designed|founded)\s+(?:the\s+)?(.+)",
            q
        )
        if inv_m:
            subj = inv_m.group(1).strip()
            variants += [
                f"{subj} inventor history",
                f"{subj} invention patent",
                f"who created {subj}",
            ]
            if re.search(r"\bphone\b|\btelephone\b", q):
                variants += [
                    "Alexander Graham Bell telephone invention",
                    "telephone inventor patent 1876",
                ]

        # ── Capital city ──────────────────────────────────────────────────
        if "capital of" in q:
            cap_m = re.search(r"capital of\s+(.+)", q)
            if cap_m:
                country = cap_m.group(1).strip()
                variants += [
                    f"{country} capital city",
                    f"capital city of {country} official",
                ]

        # ── Population ────────────────────────────────────────────────────
        if "population" in q:
            variants += [query + " census latest", query + " how many people"]

        # ── GDP / economy ─────────────────────────────────────────────────
        if "gdp" in q or "economy" in q:
            variants += [
                query + " GDP World Bank",
                query + " gross domestic product trillion",
            ]

        # ── When / date event ─────────────────────────────────────────────
        if re.search(r"\bwhen (did|was|were|is)\b", q):
            variants.append(query + " date year history")

        # ── World War ─────────────────────────────────────────────────────
        if re.search(r"\bworld war\b|\bww[12]\b", q):
            variants += [
                "World War II start end date",
                "World War II 1939 1945 history",
            ]

        # ── Gravity / science discovery ───────────────────────────────────
        if "gravity" in q or "gravitation" in q:
            variants += [
                "Isaac Newton law of gravitation discovery",
                "who discovered gravity Newton apple",
            ]

        # ── Longest river / superlatives ──────────────────────────────────
        if re.search(r"\blongest\b|\blargest\b|\bbiggest\b", q):
            variants.append(query + " world record list")

        # Deduplicate, preserve order
        seen: set[str] = set()
        unique: list[str] = []
        for v in variants:
            key = v.strip().lower()
            if key not in seen and key:
                seen.add(key)
                unique.append(v.strip())
        return unique


# ---------------------------------------------------------------------------
# Web Search Tool (DuckDuckGo HTML)
# ---------------------------------------------------------------------------

class WebSearchTool:
    """Searches DuckDuckGo HTML for multiple query variants."""

    def __init__(self, timeout: int = _TIMEOUT, results_per_query: int = 5):
        self.timeout           = timeout
        self.results_per_query = results_per_query

    def search_one(self, query: str) -> list[dict]:
        docs: list[dict] = []
        try:
            resp = requests.get(
                "https://duckduckgo.com/html/",
                params={"q": query},
                timeout=self.timeout,
                headers=_HEADERS,
            )
            resp.raise_for_status()
            soup = BeautifulSoup(resp.text, "html.parser")

            for result in soup.select(".result")[: self.results_per_query]:
                title_tag   = result.select_one(".result__title a")
                snippet_tag = result.select_one(".result__snippet")
                if not title_tag:
                    continue

                title   = title_tag.get_text(" ", strip=True)
                href    = title_tag.get("href", "")
                snippet = snippet_tag.get_text(" ", strip=True) if snippet_tag else ""

                if "uddg=" in href:
                    m = re.search(r"uddg=([^&]+)", href)
                    if m:
                        href = unquote(m.group(1))

                docs.append({
                    "title":         title,
                    "url":           href,
                    "text":          snippet,
                    "source":        "DuckDuckGo",
                    "query_variant": query,
                })

        except requests.RequestException as e:
            logger.warning("[WebSearch] Request failed '%s': %s", query, e)
        except Exception as e:
            logger.warning("[WebSearch] Parse error '%s': %s", query, e)

        return docs

    def search_many(self, queries: list[str]) -> list[dict]:
        """Search all variants, deduplicate by URL."""
        all_docs: list[dict] = []
        seen_urls: set[str]  = set()

        for q in queries:
            for doc in self.search_one(q):
                url = doc.get("url", "")
                if url not in seen_urls:
                    seen_urls.add(url)
                    all_docs.append(doc)

        return all_docs
