import argparse
import json
import sqlite3
import uuid
from pathlib import Path

from qdrant_client import QdrantClient
from qdrant_client.models import Distance, PointStruct, VectorParams
from sentence_transformers import SentenceTransformer
from tqdm import tqdm

COLLECTION = "general_knowledge"
CHUNK_SIZE = 800
CHUNK_OVERLAP = 120
MODEL_NAME = "all-MiniLM-L6-v2"


def chunk_text(text: str, chunk_size: int = CHUNK_SIZE, overlap: int = CHUNK_OVERLAP) -> list[str]:
    chunks = []
    start = 0
    step = max(1, chunk_size - overlap)
    while start < len(text):
        chunk = text[start:start + chunk_size].strip()
        if chunk:
            chunks.append(chunk)
        start += step
    return chunks


def load_jsonl(path: Path) -> list[dict]:
    documents = []
    with path.open("r", encoding="utf-8") as handle:
        for line in handle:
            line = line.strip()
            if line:
                documents.append(json.loads(line))
    return documents


def seed_documents() -> list[dict]:
    return [
        {
            "title": "Saladin",
            "source": "manual",
            "text": (
                "Saladin was the founder of the Ayyubid dynasty and the first Sultan of Egypt and Syria. "
                "He is famous for recapturing Jerusalem in 1187."
            ),
        },
        {
            "title": "Babur",
            "source": "manual",
            "text": (
                "Babur was the founder and first emperor of the Mughal Empire. "
                "He established the empire in 1526 after the First Battle of Panipat."
            ),
        },
    ]


def init_metadata_db(path: Path) -> sqlite3.Connection:
    conn = sqlite3.connect(path)
    conn.execute(
        """
        CREATE TABLE IF NOT EXISTS chunks (
            id TEXT PRIMARY KEY,
            title TEXT,
            source TEXT,
            text TEXT
        )
        """
    )
    return conn


def ingest_documents(
    documents: list[dict],
    collection: str = COLLECTION,
    metadata_path: Path = Path("knowledge_metadata.sqlite"),
    recreate: bool = True,
):
    model = SentenceTransformer(MODEL_NAME)
    client = QdrantClient("localhost", port=6333)
    metadata = init_metadata_db(metadata_path)

    if recreate:
        client.recreate_collection(
            collection_name=collection,
            vectors_config=VectorParams(size=384, distance=Distance.COSINE),
        )

    batch = []
    metadata_rows = []

    for doc in tqdm(documents, desc="Ingesting documents"):
        title = doc["title"]
        source = doc.get("source", "")
        chunks = chunk_text(doc["text"])
        embeddings = model.encode(chunks, batch_size=64, show_progress_bar=False)

        for chunk, emb in zip(chunks, embeddings):
            chunk_id = str(uuid.uuid4())
            payload = {"title": title, "source": source, "text": chunk}
            batch.append(PointStruct(id=chunk_id, vector=emb.tolist(), payload=payload))
            metadata_rows.append((chunk_id, title, source, chunk))

            if len(batch) >= 500:
                client.upsert(collection_name=collection, points=batch)
                metadata.executemany(
                    "INSERT OR REPLACE INTO chunks (id, title, source, text) VALUES (?, ?, ?, ?)",
                    metadata_rows,
                )
                metadata.commit()
                batch = []
                metadata_rows = []

    if batch:
        client.upsert(collection_name=collection, points=batch)
        metadata.executemany(
            "INSERT OR REPLACE INTO chunks (id, title, source, text) VALUES (?, ?, ?, ?)",
            metadata_rows,
        )
        metadata.commit()

    metadata.close()


def main():
    parser = argparse.ArgumentParser(description="Ingest general knowledge chunks into Qdrant.")
    parser.add_argument("--jsonl", type=Path, help="JSONL file with title/source/text fields.")
    parser.add_argument("--collection", default=COLLECTION)
    parser.add_argument("--metadata", type=Path, default=Path("knowledge_metadata.sqlite"))
    parser.add_argument("--append", action="store_true", help="Append to existing collection instead of recreating it.")
    args = parser.parse_args()

    documents = load_jsonl(args.jsonl) if args.jsonl else seed_documents()
    ingest_documents(
        documents,
        collection=args.collection,
        metadata_path=args.metadata,
        recreate=not args.append,
    )
    print("Ingestion completed.")


if __name__ == "__main__":
    main()
