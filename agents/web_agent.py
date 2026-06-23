import datetime as _dt
import hashlib
import logging
import re
import uuid
from typing import Any

import requests

from agents.base_agent import BaseAgent
from tools.answer_extractor import AnswerExtractor
from tools.fact_verifier import FactVerifier
from tools.similarity_ranker import SimilarityRanker
from tools.web_page_reader import WebPageReader
from tools.web_search_tool import QueryRewriter, WebSearchTool

logger = logging.getLogger(__name__)


class _HashEmbeddingFunction:
    """Small deterministic embedding function for Chroma cache queries."""

    def __call__(self, input: list[str]) -> list[list[float]]:
        vectors: list[list[float]] = []
        for text in input:
            buckets = [0.0] * 64
            for token in re.findall(r"[a-z0-9]+", text.lower()):
                digest = hashlib.md5(token.encode("utf-8")).digest()
                index = digest[0] % len(buckets)
                buckets[index] += 1.0
            norm = sum(value * value for value in buckets) ** 0.5 or 1.0
            vectors.append([round(value / norm, 6) for value in buckets])
        return vectors


class WebSummaryCache:
    similarity_threshold = 0.5

    def __init__(
        self,
        persist_directory: str = "knowledge/web_cache_chroma",
        collection_name: str = "web_summary_cache",
    ):
        self._memory: list[dict[str, Any]] = []
        self._collection = None
        self.backend = "memory"
        self.persist_directory = persist_directory
        self.collection_name = collection_name

    def _ensure_chroma(self) -> None:
        if self._collection is not None:
            return
        try:
            import chromadb

            client = chromadb.PersistentClient(path=self.persist_directory)
            self._collection = client.get_or_create_collection(
                name=self.collection_name,
                embedding_function=_HashEmbeddingFunction(),
            )
            self.backend = "chromadb"
        except Exception:
            self._collection = None

    def store(self, query: str, summary: str, sources: list[dict]) -> dict:
        self._ensure_chroma()
        cache_id = str(uuid.uuid4())
        metadata = {
            "query": query,
            "created_at": _dt.datetime.utcnow().isoformat(timespec="seconds") + "Z",
            "source_count": len(sources),
        }
        source_text = "\n".join(
            f"- {source.get('title', 'Source')}: {source.get('url', '')}"
            for source in sources
        )
        document = f"Query: {query}\nSummary: {summary}\nSources:\n{source_text}"

        if self._collection is not None:
            self._collection.add(
                ids=[cache_id],
                documents=[document],
                metadatas=[metadata],
            )
        else:
            self._memory.append({
                "id": cache_id,
                "document": document,
                "metadata": metadata,
                "query": query,
                "summary": summary,
                "sources": sources,
            })

        return {"id": cache_id, "backend": self.backend, **metadata}

    def store_summary(self, query: str, result: dict, summary: str) -> str | None:
        if not summary:
            summary = result.get("snippet") or result.get("text", "")
        if not summary:
            return None

        cache_id = str(uuid.uuid4())
        metadata = {
            "query": query,
            "title": result.get("title", ""),
            "url": result.get("url", ""),
            "timestamp": _dt.datetime.utcnow().isoformat(timespec="seconds") + "Z",
        }

        self._ensure_chroma()
        if self._collection is not None:
            self._collection.add(
                ids=[cache_id],
                documents=[summary],
                metadatas=[metadata],
            )
        else:
            self._memory.append({
                "id": cache_id,
                "document": summary,
                "metadata": metadata,
                "query": query,
                "summary": summary,
                "sources": [result],
            })

        return cache_id

    def retrieve(self, query: str, top_k: int = 3) -> dict:
        self._ensure_chroma()
        if self._collection is not None:
            result = self._collection.query(query_texts=[query], n_results=top_k)
            documents = result.get("documents", [[]])[0]
            metadatas = result.get("metadatas", [[]])[0]
            ids = result.get("ids", [[]])[0]
            distances = result.get("distances", [[]])[0]
            if distances and min(distances) > self.similarity_threshold:
                return {
                    "query": query,
                    "backend": self.backend,
                    "documents": [],
                    "metadatas": [],
                    "distances": distances,
                    "results": [],
                    "cache_miss": True,
                    "reason": (
                        "No Chroma cache item met the similarity threshold "
                        f"(best_distance={min(distances):.3f}, "
                        f"threshold={self.similarity_threshold})."
                    ),
                }
            return {
                "query": query,
                "backend": self.backend,
                "documents": documents,
                "metadatas": metadatas,
                "distances": distances,
                "results": [
                    {
                        "id": ids[i],
                        "text": doc,
                        "metadata": metadatas[i],
                        "distance": distances[i] if i < len(distances) else None,
                    }
                    for i, doc in enumerate(documents)
                ],
            }

        query_terms = set(re.findall(r"[a-z0-9]+", query.lower()))
        ranked = sorted(
            self._memory,
            key=lambda item: len(
                query_terms
                & set(re.findall(r"[a-z0-9]+", item.get("document", "").lower()))
            ),
            reverse=True,
        )
        results = [
            {
                "id": item["id"],
                "text": item["document"],
                "metadata": item["metadata"],
            }
            for item in ranked[:top_k]
        ]
        return {
            "query": query,
            "backend": self.backend,
            "documents": [item["text"] for item in results],
            "metadatas": [item["metadata"] for item in results],
            "results": results,
        }


class WebAgent(BaseAgent):
    name = "WebAgent"
    agent_type = "Web"
    base_tasks = [
        "Rewrite search query",
        "Search web snippets",
        "Rerank URLs",
        "Fetch selected pages",
        "Extract answer",
        "Cache compressed summary",
    ]

    def __init__(
        self,
        top_links: int = 10,
        fetch_links: int = 5,
        cache: WebSummaryCache | None = None,
    ):
        super().__init__()
        self.top_links = top_links
        self.fetch_links = fetch_links
        self.rewriter = QueryRewriter()
        self.searcher = WebSearchTool(results_per_query=5)
        self.ranker = SimilarityRanker()
        self.reader = WebPageReader(max_chars=6000)
        self.extractor = AnswerExtractor()
        self.verifier = FactVerifier()
        self.cache = cache or WebSummaryCache()

    def run(self, query: str, prefilled_fields: dict | None = None, session_id: str = "default"):
        query = query.strip()
        thoughts = self.tot.create_thoughts(self.agent_type, query, self.base_tasks)

        variants = self.rewriter.rewrite(query)
        thoughts.append(f"Web Search Agent: generated {len(variants)} query variant(s).")

        search_results = self.search_web(query, top_k=self.top_links, variants=variants)
        thoughts.append(f"Search Engine: returned {len(search_results)} unique URL/snippet result(s).")

        ranked_links = self.ranker.rank(query, self._docs_from_results(search_results))[: self.top_links]
        thoughts.append(f"Reranker: selected top {len(ranked_links)} link(s) before page fetch.")

        selected_docs = self.fetch_selected_pages(query, ranked_links[: self.fetch_links])
        fetched_count = sum(1 for doc in selected_docs if doc.get("page_fetched"))
        thoughts.append(f"Fetcher: fetched {fetched_count}/{len(selected_docs)} selected page(s).")

        if not selected_docs:
            answer = "I could not find useful web results for that query."
            return self.response(query, thoughts, answer, {
                "slot_filling": False,
                "source_stage": "web_agent",
                "search_results": [],
                "selected_sources": [],
                "verification": {
                    "verified": False,
                    "confidence": 0.0,
                    "reason": "No web search results were available.",
                    "corrected": answer,
                    "sources_used": 0,
                },
            })

        evidence = self.ranker.rank(query, selected_docs)[: self.fetch_links]
        context = self.build_context(evidence)
        answer = self.extractor.extract(query, context) or self.compress_context(context)
        verification = self.verifier.verify(query, answer, evidence)
        answer = verification.get("corrected") or answer

        stored_summaries = []
        for doc in evidence:
            summary = self.summarize_text(query, doc.get("text", "")) or doc.get("snippet", "")
            doc_id = self.store_summary(query, doc, summary)
            if doc_id:
                stored_summaries.append({
                    "doc_id": doc_id,
                    "title": doc.get("title", ""),
                    "url": doc.get("url", ""),
                    "summary": summary,
                })

        cache_record = self.cache.store(query, answer, self.public_sources(evidence))
        thoughts.append(f"Cache: stored compressed summary in {cache_record['backend']}.")
        cache_results = self.retrieve_cache(query)
        cache_answer = self.generate_answer(query, cache_results)

        return self.response(query, thoughts, answer, {
            "slot_filling": False,
            "source_stage": "web_agent",
            "pipeline": [
                "search_first",
                "rerank_links",
                "fetch_selected_pages_only",
                "extract_answer",
                "cache_summary",
            ],
            "search_results": ranked_links,
            "stored_summaries": stored_summaries,
            "retrieved_from_chroma": cache_results,
            "generated_cache_answer": cache_answer,
            "selected_sources": self.public_sources(evidence),
            "cache": cache_record,
            "verification": verification,
        })

    def retrieve_cache(self, query: str, top_k: int = 3) -> dict:
        return self.cache.retrieve(query, top_k=top_k)

    def search_web(self, query: str, top_k: int = 5, variants: list[str] | None = None) -> list[dict]:
        variants = variants or self.rewriter.rewrite(query)
        results = self.searcher.search_many(variants)
        ranked = self.ranker.rank(query, results)[:top_k] if results else []
        if ranked:
            return [self._result_from_doc(doc) for doc in ranked]

        wikipedia_results = self.search_wikipedia(query, top_k=top_k)
        if wikipedia_results:
            return wikipedia_results

        return self.local_fallback(query)

    def search_wikipedia(self, query: str, top_k: int = 5) -> list[dict]:
        try:
            response = requests.get(
                "https://en.wikipedia.org/w/api.php",
                params={
                    "action": "query",
                    "list": "search",
                    "srsearch": query,
                    "format": "json",
                    "srlimit": top_k,
                },
                headers={"User-Agent": "OmniAgentAI/1.0"},
                timeout=10,
            )
            response.raise_for_status()
            items = response.json().get("query", {}).get("search", [])
        except Exception as exc:
            logger.debug("Wikipedia fallback search failed for %s: %s", query, exc)
            return []

        results = []
        for item in items[:top_k]:
            title = item.get("title", "")
            snippet = re.sub(r"<[^>]+>", "", item.get("snippet", ""))
            results.append({
                "title": title,
                "url": "https://en.wikipedia.org/wiki/" + title.replace(" ", "_"),
                "snippet": snippet,
                "source": "Wikipedia",
            })
        return results

    @staticmethod
    def local_fallback(query: str) -> list[dict]:
        if "agentic ai" not in query.lower():
            return []
        return [
            {
                "title": "Agentic AI Overview",
                "url": "local://agentic-ai",
                "snippet": (
                    "Agentic AI refers to AI systems that can plan, reason, use tools, "
                    "take actions, observe results, and self-correct."
                ),
                "source": "local",
            },
            {
                "title": "ReAct Agent Pattern",
                "url": "local://react",
                "snippet": "ReAct combines reasoning, action, and observation in iterative loops.",
                "source": "local",
            },
            {
                "title": "Agentic RAG",
                "url": "local://agentic-rag",
                "snippet": (
                    "Agentic RAG uses retrieval as a tool controlled by an agent "
                    "rather than a fixed retrieval pipeline."
                ),
                "source": "local",
            },
        ]

    def fetch_page_text(self, url: str) -> str:
        if not url or url.startswith("local://"):
            return ""
        return self.reader.fetch(url)

    def fetch_selected_pages(self, query: str, docs: list[dict]) -> list[dict]:
        selected: list[dict] = []
        for doc in docs:
            url = doc.get("url", "")
            page_text = self.fetch_page_text(url)
            text = page_text or doc.get("text", "") or doc.get("snippet", "")
            if not text:
                continue
            selected.append({
                **doc,
                "snippet": doc.get("snippet") or doc.get("text", ""),
                "text": self.compress_context(text, max_sentences=8, max_chars=1800),
                "page_fetched": bool(page_text),
            })
        return selected

    def store_summary(self, query: str, result: dict, summary: str) -> str | None:
        return self.cache.store_summary(query, result, summary)

    def summarize_text(self, query: str, text: str) -> str:
        if not text:
            return ""

        keywords = re.findall(r"[a-z0-9]+", query.lower().replace("?", ""))
        sentences = [
            sentence.strip()
            for sentence in re.split(r"(?<=[.!?])\s+", re.sub(r"\s+", " ", text))
            if len(sentence.strip()) > 30
        ]
        scored = []
        for sentence in sentences:
            lower = sentence.lower()
            score = sum(1 for word in keywords if word in lower)
            if score > 0:
                scored.append((score, sentence))

        scored.sort(reverse=True, key=lambda item: item[0])
        if scored:
            return ". ".join(sentence.rstrip(".") for _, sentence in scored[:5]).strip() + "."
        return text[:800].strip()

    @staticmethod
    def generate_answer(query: str, cache_results: dict) -> str:
        docs = cache_results.get("documents") or [
            item.get("text", "")
            for item in cache_results.get("results", [])
        ]
        docs = [doc for doc in docs if doc]

        if not docs:
            return "I could not find reliable web information for this query."

        context = "\n\n".join(docs[:3])
        return (
            f"Answer for: {query}\n\n"
            f"{context}\n\n"
            "Summary:\n"
            "Based on the retrieved web/cache information, this answer is grounded "
            "in selected live search results and cached page summaries."
        )

    @staticmethod
    def build_context(docs: list[dict]) -> str:
        parts = []
        for index, doc in enumerate(docs, start=1):
            parts.append(
                f"[Source {index}: {doc.get('title', 'Source')}]\n"
                f"URL: {doc.get('url', '')}\n"
                f"{doc.get('text', '')}"
            )
        return "\n\n".join(parts)

    @staticmethod
    def compress_context(text: str, max_sentences: int = 4, max_chars: int = 1200) -> str:
        cleaned = re.sub(r"\s+", " ", text or "").strip()
        sentences = [
            sentence.strip()
            for sentence in re.split(r"(?<=[.!?])\s+", cleaned)
            if len(sentence.strip()) > 20
        ]
        summary = " ".join(sentences[:max_sentences]) if sentences else cleaned
        return summary[:max_chars].strip()

    @staticmethod
    def public_sources(docs: list[dict]) -> list[dict]:
        return [
            {
                "title": doc.get("title", ""),
                "url": doc.get("url", ""),
                "source": doc.get("source", "Web"),
                "similarity_score": doc.get("similarity_score", 0.0),
                "page_fetched": bool(doc.get("page_fetched")),
            }
            for doc in docs
        ]

    @staticmethod
    def _docs_from_results(results: list[dict]) -> list[dict]:
        return [
            {
                **result,
                "text": result.get("text") or result.get("snippet", ""),
                "source": result.get("source", "Web"),
            }
            for result in results
        ]

    @staticmethod
    def _result_from_doc(doc: dict) -> dict:
        return {
            "title": doc.get("title", ""),
            "url": doc.get("url", ""),
            "snippet": doc.get("snippet") or doc.get("text", ""),
            "source": doc.get("source", "Web"),
        }
