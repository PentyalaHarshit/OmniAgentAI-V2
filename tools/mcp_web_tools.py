"""
MCP-style Web Tools for GeneralAgent
=====================================
Implements a lightweight Model Context Protocol (MCP) tool-calling pattern.

Tools included:
  1. WikipediaSearchTool – Wikipedia REST API page summary
  2. DuckDuckGoTool      – DuckDuckGo Instant Answer API
  3. WikimediaSearchTool – Wikipedia full-text search (w/api.php)
"""

import re
import urllib.parse
import urllib.request
import json
import logging

from tools.general_query_tools import CountryInfoTool

logger = logging.getLogger(__name__)

TIMEOUT = 8
HEADERS = {"User-Agent": "OmniAgentAI/1.0 (general-agent; contact@omniagentai.local)"}

# Backwards-compatible alias
RestCountriesTool = CountryInfoTool


# ---------------------------------------------------------------------------
# Helpers
# ---------------------------------------------------------------------------

def _get(url: str) -> dict | None:
    try:
        req = urllib.request.Request(url, headers=HEADERS)
        with urllib.request.urlopen(req, timeout=TIMEOUT) as resp:
            return json.loads(resp.read().decode("utf-8", errors="replace"))
    except Exception as e:
        logger.warning("MCP HTTP error for %s: %s", url, e)
        return None


def _clean(text: str) -> str:
    text = re.sub(r"<[^>]+>", "", text)
    return re.sub(r"\s+", " ", text).strip()


# ---------------------------------------------------------------------------
# Tool 1 – Wikipedia page summary
# ---------------------------------------------------------------------------

class WikipediaSearchTool:
    name = "wikipedia_summary"
    description = "Fetches the summary of the most relevant Wikipedia article for a query."
    input_schema = {"query": "string"}

    def execute(self, query: str) -> str:
        search_url = (
            "https://en.wikipedia.org/w/api.php?"
            + urllib.parse.urlencode({
                "action": "query", "list": "search",
                "srsearch": query, "format": "json", "srlimit": 1,
            })
        )
        data = _get(search_url)
        if not data:
            return ""
        results = data.get("query", {}).get("search", [])
        if not results:
            return ""
        title = results[0]["title"]

        summary_url = (
            "https://en.wikipedia.org/api/rest_v1/page/summary/"
            + urllib.parse.quote(title.replace(" ", "_"))
        )
        sdata = _get(summary_url)
        if not sdata:
            return ""
        extract = sdata.get("extract", "").strip()
        page_url = sdata.get("content_urls", {}).get("desktop", {}).get("page", "")
        if not extract:
            return ""
        source = f"\n\n📖 *Source: [Wikipedia – {title}]({page_url})*" if page_url else ""
        return _clean(extract) + source


# ---------------------------------------------------------------------------
# Tool 2 – DuckDuckGo Instant Answer API
# ---------------------------------------------------------------------------

class DuckDuckGoTool:
    name = "duckduckgo_instant"
    description = "Queries DuckDuckGo Instant Answer API for factual one-line answers."
    input_schema = {"query": "string"}

    def execute(self, query: str) -> str:
        url = (
            "https://api.duckduckgo.com/?"
            + urllib.parse.urlencode({
                "q": query, "format": "json",
                "no_html": "1", "skip_disambig": "1",
            })
        )
        data = _get(url)
        if not data:
            return ""

        abstract = data.get("AbstractText", "").strip()
        if abstract:
            src = (
                f"\n\n🦆 *Source: [DuckDuckGo]({data.get('AbstractURL', '')})*"
                if data.get("AbstractURL") else ""
            )
            return _clean(abstract) + src

        answer = data.get("Answer", "").strip()
        if answer:
            return _clean(answer)

        definition = data.get("Definition", "").strip()
        if definition:
            src = (
                f"\n\n📚 *Source: [Definition]({data.get('DefinitionURL', '')})*"
                if data.get("DefinitionURL") else ""
            )
            return _clean(definition) + src

        return ""


# ---------------------------------------------------------------------------
# Tool 3 – Wikimedia full-text snippet search (fallback)
# ---------------------------------------------------------------------------

class WikimediaSearchTool:
    name = "wikimedia_search"
    description = "Returns snippets from Wikimedia full-text search."
    input_schema = {"query": "string"}

    def execute(self, query: str) -> str:
        url = (
            "https://en.wikipedia.org/w/api.php?"
            + urllib.parse.urlencode({
                "action": "query", "list": "search",
                "srsearch": query, "format": "json",
                "srlimit": 3, "srprop": "snippet|titlesnippet",
            })
        )
        data = _get(url)
        if not data:
            return ""
        results = data.get("query", {}).get("search", [])
        if not results:
            return ""
        lines = []
        for r in results[:3]:
            title   = r.get("title", "")
            snippet = _clean(r.get("snippet", ""))
            if title and snippet:
                wiki_url = (
                    "https://en.wikipedia.org/wiki/"
                    + urllib.parse.quote(title.replace(" ", "_"))
                )
                lines.append(f"**{title}**: {snippet}… [read more]({wiki_url})")
        return "\n\n".join(lines) if lines else ""


# ---------------------------------------------------------------------------
# MCPToolRunner – orchestrates DuckDuckGo → Wikipedia → Wikimedia
# ---------------------------------------------------------------------------

class MCPToolRunner:
    """
    Tries tools in priority order and returns the first non-empty result.
    Also exposes get_capital() for direct country lookups.
    """

    def __init__(self):
        self._country_tool = CountryInfoTool()
        self.tools = [
            DuckDuckGoTool(),
            WikipediaSearchTool(),
            WikimediaSearchTool(),
        ]

    def get_capital(self, country: str) -> str | None:
        """Convenience wrapper used by react_general_crew capital fast-path."""
        info = self._country_tool.get_country_info(country)
        return info["capital"] if info else None

    def run(self, query: str) -> dict:
        all_results = []
        best_answer = ""
        tool_used   = ""

        for tool in self.tools:
            try:
                result = tool.execute(query)
            except Exception as e:
                logger.warning("Tool %s raised: %s", tool.name, e)
                result = ""

            all_results.append({"tool": tool.name, "result": result})

            if result and not best_answer:
                best_answer = result
                tool_used   = tool.name

        return {
            "answer":      best_answer,
            "tool_used":   tool_used,
            "all_results": all_results,
        }
