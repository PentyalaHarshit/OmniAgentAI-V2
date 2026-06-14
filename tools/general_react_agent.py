"""
tools/general_react_agent.py
=============================
GeneralReActAgent — full ReAct + Web RAG pipeline for open-domain questions.

Flow
----
  Thought     : understand what is being asked
  Action      : rewrite query into multiple targeted search variants
  Action      : search multiple web links (DuckDuckGo HTML)
  Observation : collect snippets, log each source pass/reject
  Action      : similarity rank (with answer-type boosting + off-topic penalty)
  Action      : if duration question AND top doc score low → fetch Wikipedia directly
  Action      : extract answer from ranked documents
  Action      : fact-verify across sources
  Final       : answer with source links
"""

import re
import json
import logging
import urllib.parse
import urllib.request

from tools.web_search_tool   import WebSearchTool, QueryRewriter
from tools.similarity_ranker import SimilarityRanker
from tools.fact_verifier     import FactVerifier
from tools.answer_extractor  import AnswerExtractor

logger = logging.getLogger(__name__)

_MIN_SCORE  = 0.10
_WIKI_UA    = "OmniAgentAI/1.0 (general-agent)"
_WIKI_TIMEOUT = 8


# ---------------------------------------------------------------------------
# Wikipedia direct fetch helpers
# ---------------------------------------------------------------------------

def _wiki_search_title(entity: str) -> str:
    """Return the best Wikipedia page title for an entity."""
    try:
        url = (
            "https://en.wikipedia.org/w/api.php?"
            + urllib.parse.urlencode({
                "action": "query", "list": "search",
                "srsearch": entity, "format": "json", "srlimit": 3,
            })
        )
        req  = urllib.request.Request(url, headers={"User-Agent": _WIKI_UA})
        with urllib.request.urlopen(req, timeout=_WIKI_TIMEOUT) as resp:
            data = json.loads(resp.read().decode("utf-8", errors="replace"))
        results = data.get("query", {}).get("search", [])
        # Prefer exact match on entity name
        entity_lo = entity.lower()
        for r in results:
            if entity_lo in r.get("title", "").lower():
                return r["title"]
        return results[0]["title"] if results else ""
    except Exception as e:
        logger.debug("_wiki_search_title error: %s", e)
        return ""


def _wiki_fetch_summary(title: str) -> tuple[str, str]:
    """Fetch Wikipedia page summary. Returns (extract_text, page_url)."""
    try:
        url = (
            "https://en.wikipedia.org/api/rest_v1/page/summary/"
            + urllib.parse.quote(title.replace(" ", "_"))
        )
        req  = urllib.request.Request(url, headers={"User-Agent": _WIKI_UA})
        with urllib.request.urlopen(req, timeout=_WIKI_TIMEOUT) as resp:
            data = json.loads(resp.read().decode("utf-8", errors="replace"))
        extract  = data.get("extract", "").strip()
        page_url = data.get("content_urls", {}).get("desktop", {}).get("page", "")
        return extract, page_url
    except Exception as e:
        logger.debug("_wiki_fetch_summary error for '%s': %s", title, e)
        return "", ""


def _extract_entity_for_duration(query: str) -> str:
    """
    Pull the main subject from a duration question.
    'How long did the Chola dynasty rule?' → 'Chola dynasty'
    'How long did the Roman Empire last?'  → 'Roman Empire'
    """
    q = query.strip().rstrip("?")
    # Remove "how long did/was/has the ... rule/last/exist/reign/stand"
    m = re.search(
        r"how long\s+(?:did|was|has|have|were|are)?\s*(?:the\s+)?(.+?)"
        r"\s+(?:rule|ruled|last|lasted|exist|existed|reign|reigned|stand|stood|survive|run)?$",
        q, re.I
    )
    if m:
        return m.group(1).strip()
    # Fallback: everything between "how long" and end
    m = re.search(r"how long\s+(?:did|was|has)?\s*(.+)", q, re.I)
    return m.group(1).strip() if m else ""


# ---------------------------------------------------------------------------
# GeneralReActAgent
# ---------------------------------------------------------------------------

class GeneralReActAgent:

    TOP_K = 6

    def __init__(self):
        self.rewriter  = QueryRewriter()
        self.searcher  = WebSearchTool(results_per_query=5)
        self.ranker    = SimilarityRanker()
        self.extractor = AnswerExtractor()
        self.verifier  = FactVerifier()

    # ── Public API ───────────────────────────────────────────────────────

    def run(self, query: str) -> dict:
        thoughts: list[str] = []

        q_type = self._classify(query)
        thoughts.append(f"Thought: Need {q_type} information for: \"{query}\"")

        # ── Action: rewrite → multiple search queries ─────────────────────
        search_queries = self.rewriter.rewrite(query)
        thoughts.append(
            "Action: Generate search queries →\n"
            + "\n".join(f"  • {q}" for q in search_queries[:6])
        )

        # ── Action: search multiple web links ─────────────────────────────
        thoughts.append(f"Action: Search {len(search_queries)} query variants across DuckDuckGo.")
        docs = self.searcher.search_many(search_queries)
        thoughts.append(
            f"Observation: {len(docs)} documents retrieved "
            f"({len(set(d.get('url','') for d in docs))} unique URLs)."
        )

        # ── Action: similarity rank ────────────────────────────────────────
        ranked = self.ranker.rank(query, docs) if docs else []
        top    = ranked[: self.TOP_K]

        rank_lines = []
        for i, d in enumerate(top):
            sc = d.get("similarity_score", 0.0)
            rank_lines.append(
                f"  Rank {i+1}: \"{d.get('title','?')[:65]}\" | "
                f"Score: {sc} {'✓' if sc >= _MIN_SCORE else '✗'}"
            )
        if rank_lines:
            thoughts.append("Action: Similarity rank search-result snippets.\n" + "\n".join(rank_lines))

        chunk_candidates = ranked or docs
        page_limit = min(len(chunk_candidates), self.searcher.max_pages_to_fetch)
        thoughts.append(
            f"Action: Open top {page_limit} result links, extract readable text, "
            "and split pages into chunks."
        )
        chunks = self.searcher.enrich_with_page_chunks(chunk_candidates)
        fetched_pages = {
            c.get("url", "")
            for c in chunks
            if c.get("url") and c.get("page_chars", 0) > 0
        }
        snippet_fallbacks = sum(1 for c in chunks if c.get("page_chars", 0) == 0)
        thoughts.append(
            f"Observation: Built {len(chunks)} chunks from {len(fetched_pages)} fetched pages "
            f"and {snippet_fallbacks} snippet fallbacks."
        )

        chunk_ranked = self.ranker.rank(query, chunks) if chunks else []
        chunk_top = chunk_ranked[: self.TOP_K]
        chunk_rank_lines = []
        for i, d in enumerate(chunk_top):
            sc = d.get("similarity_score", 0.0)
            chunk_rank_lines.append(
                f"  Chunk {i+1}: \"{d.get('title','?')[:60]}\" "
                f"#{d.get('chunk_index', 1)} | Score: {sc} "
                f"{'âœ“' if sc >= _MIN_SCORE else 'âœ—'}"
            )
        if chunk_rank_lines:
            thoughts.append("Action: Similarity rank extracted chunks.\n" + "\n".join(chunk_rank_lines))

        usable = [d for d in chunk_top if d.get("similarity_score", 0) >= _MIN_SCORE]
        if not usable:
            usable = [d for d in top if d.get("similarity_score", 0) >= _MIN_SCORE]

        # ── Action: Wikipedia direct fetch for duration / history ─────────
        # If DuckDuckGo gave us weak results, go straight to Wikipedia.
        need_wiki_fallback = (
            q_type in ("duration/ruling period", "inventor/discoverer", "date/event")
            and (
                not usable
                or not any(d.get("text", "").strip() for d in usable[:2])
                or (usable and usable[0].get("similarity_score", 0) < 0.60)
            )
        )

        if need_wiki_fallback:
            entity = _extract_entity_for_duration(query) or query
            thoughts.append(
                f"Observation: DuckDuckGo results insufficient. "
                f"Action: Fetch Wikipedia directly for '{entity}'."
            )
            wiki_title = _wiki_search_title(entity)
            thoughts.append(f"Action: Wikipedia search → best title = '{wiki_title}'")

            if wiki_title:
                wiki_text, wiki_url = _wiki_fetch_summary(wiki_title)
                if wiki_text:
                    wiki_doc = {
                        "title":            wiki_title,
                        "url":              wiki_url,
                        "text":             wiki_text,
                        "source":           "Wikipedia",
                        "query_variant":    query,
                        "similarity_score": 1.50,   # trusted source, high score
                    }
                    thoughts.append(
                        f"Observation: Wikipedia '{wiki_title}' fetched "
                        f"({len(wiki_text)} chars). ✓"
                    )
                    # Prepend to usable so it ranks first
                    usable = [wiki_doc] + [d for d in usable if d.get("title") != wiki_title]
                else:
                    thoughts.append(f"Observation: Wikipedia '{wiki_title}' returned no content.")

        if not usable:
            thoughts.append("Observation: No usable documents found. Cannot answer.")
            return self._empty(thoughts)

        best = usable[0]
        thoughts.append(
            f"Observation: Top source = \"{best.get('title','?')[:70]}\" "
            f"(score {best.get('similarity_score', 0.0)}) ✓"
        )

        # ── Action: extract answer ─────────────────────────────────────────
        thoughts.append("Action: Pass top relevant chunks through the answer generator.")
        context = self._build_context(usable[:4])
        answer  = self.extractor.extract(query, context)

        if not answer:
            # Fallback: first 2 sentences of best doc
            text  = best.get("text", "")
            sents = [s.strip() for s in re.split(r"(?<=[.!?])\s+", text) if len(s.strip()) > 15]
            answer = " ".join(sents[:2]) if sents else text[:300]

        thoughts.append(f"Observation: Extracted → \"{answer[:200]}\"")

        # ── Action: fact verify ────────────────────────────────────────────
        thoughts.append("Action: Verify answer across multiple sources.")
        verified = self.verifier.verify(query, answer, usable)
        thoughts.append(
            f"Observation: verified={verified['verified']}, "
            f"confidence={verified['confidence']}, {verified['reason']}"
        )

        final = verified["corrected"]

        src_lines = self._format_sources(usable[:3])
        if src_lines:
            final += "\n\n" + src_lines

        thoughts.append(f"Final: {final[:300]}")

        return {
            "answer":    final,
            "sources":   usable[:3],
            "verified":  verified,
            "thoughts":  thoughts,
            "tool_used": "general_react_webrag",
        }

    # ── Helpers ──────────────────────────────────────────────────────────

    def _classify(self, query: str) -> str:
        q = query.lower()
        if re.search(r"\bhow long\b|\bduration\b|\bfor how long\b", q):
            return "duration/ruling period"
        if re.search(r"\bwho (invented|discovered|created|built|founded)\b", q):
            return "inventor/discoverer"
        if re.search(r"\bwhen (did|was|were|is)\b", q):
            return "date/event"
        if re.search(r"\bwhere (is|was|are)\b", q):
            return "location"
        if re.search(r"\bwhat is\b", q):
            return "definition/fact"
        if re.search(r"\b(longest|largest|biggest|tallest)\b", q):
            return "superlative/record"
        return "general factual"

    def _build_context(self, docs: list[dict]) -> str:
        parts: list[str] = []
        for i, doc in enumerate(docs, 1):
            text = doc.get("text", "").strip()
            if text:
                parts.append(f"[Source {i}: {doc.get('title', 'Unknown')}]\n{text}")
        return "\n\n".join(parts)

    def _format_sources(self, docs: list[dict]) -> str:
        lines: list[str] = []
        for doc in docs:
            title = doc.get("title", "Source")
            url   = doc.get("url", "")
            score = doc.get("similarity_score", 0.0)
            if url:
                lines.append(f"🔗 [{title}]({url}) *(relevance: {score})*")
            else:
                lines.append(f"📄 {title} *(relevance: {score})*")
        return "\n".join(lines) if lines else ""

    def run_safe(self, query: str) -> dict:
        """
        Safe wrapper around run() — catches all exceptions and returns an
        empty result dict so callers do not need their own try/except.
        """
        try:
            return self.run(query)
        except Exception as exc:
            logger.warning("[GeneralReActAgent] run_safe error for '%s': %s", query, exc)
            return self._empty([f"Error in GeneralReActAgent: {exc}"])

    def _empty(self, thoughts: list[str]) -> dict:
        return {
            "answer":    "",
            "sources":   [],
            "verified":  {
                "verified": False, "confidence": 0.0,
                "reason":   "No usable documents found.",
                "corrected": "", "sources_used": 0,
            },
            "thoughts":  thoughts,
            "tool_used": "general_react_webrag",
        }
