import argparse

from qdrant_client import QdrantClient
from sentence_transformers import SentenceTransformer

COLLECTION = "general_knowledge"
MODEL_NAME = "all-MiniLM-L6-v2"


def search_knowledge(query: str, top_k: int = 5, collection: str = COLLECTION) -> list[dict]:
    model = SentenceTransformer(MODEL_NAME)
    client = QdrantClient("localhost", port=6333)
    query_vector = model.encode(query).tolist()

    results = client.search(
        collection_name=collection,
        query_vector=query_vector,
        limit=top_k,
    )

    return [
        {
            "score": result.score,
            "title": result.payload.get("title"),
            "source": result.payload.get("source"),
            "text": result.payload.get("text"),
        }
        for result in results
    ]


def main():
    parser = argparse.ArgumentParser(description="Search OmniAgent's Qdrant knowledge base.")
    parser.add_argument("query", nargs="?", default="Who was Saladin?")
    parser.add_argument("--top-k", type=int, default=5)
    parser.add_argument("--collection", default=COLLECTION)
    args = parser.parse_args()

    for result in search_knowledge(args.query, top_k=args.top_k, collection=args.collection):
        print("\nTITLE:", result["title"])
        print("SCORE:", result["score"])
        print("SOURCE:", result["source"])
        print("TEXT:", (result["text"] or "")[:300])


if __name__ == "__main__":
    main()
