import logging
from typing import Any

logger = logging.getLogger(__name__)


class QdrantKnowledgeTool:
    """Optional vector database search for large general-knowledge corpora."""

    def __init__(
        self,
        collection: str = "general_knowledge",
        host: str = "localhost",
        port: int = 6333,
        model_name: str = "all-MiniLM-L6-v2",
    ):
        self.collection = collection
        self.host = host
        self.port = port
        self.model_name = model_name
        self._model: Any | None = None
        self._client: Any | None = None
        self._available: bool | None = None

    def available(self) -> bool:
        if self._available is not None:
            return self._available
        try:
            self._load()
            self._client.get_collection(self.collection)
            self._available = True
        except Exception as exc:
            logger.debug("Qdrant knowledge search unavailable: %s", exc)
            self._available = False
        return self._available

    def search(self, query: str, top_k: int = 5) -> list[dict]:
        if not query.strip() or not self.available():
            return []
        try:
            query_vector = self._model.encode(query).tolist()
            results = self._client.search(
                collection_name=self.collection,
                query_vector=query_vector,
                limit=top_k,
            )
        except Exception as exc:
            logger.warning("Qdrant knowledge search failed: %s", exc)
            return []

        docs = []
        for result in results:
            payload = result.payload or {}
            docs.append({
                "title": payload.get("title", ""),
                "url": payload.get("source", ""),
                "source": payload.get("source", "Qdrant"),
                "text": payload.get("text", ""),
                "similarity_score": float(result.score or 0.0),
            })
        return docs

    def build_context(self, docs: list[dict]) -> str:
        return "\n\n".join(
            f"Source: {d.get('title', '')}\nURL: {d.get('url', '')}\nText: {d.get('text', '')}\nSimilarity: {d.get('similarity_score', 0)}"
            for d in docs
        )

    def _load(self):
        if self._model is not None and self._client is not None:
            return
        from qdrant_client import QdrantClient
        from sentence_transformers import SentenceTransformer

        self._model = SentenceTransformer(self.model_name)
        self._client = QdrantClient(self.host, port=self.port)
