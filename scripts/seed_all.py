#!/usr/bin/env python3
"""Master seeder: initializes all data stores with coherent mock data."""
import sys
import os

sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from src.database.session import init_db, SessionLocal
from src.database.seed import seed_all as seed_sqlite
from src.search_engines.vector_store import vector_engine
from src.search_engines.keyword_search import keyword_engine
from src.embeddings.embedder import embedder as _embedder


def seed_chroma():
    print("\n--- Seeding ChromaDB Vector Store ---")
    vector_engine.clear_collection("documents")
    collection = vector_engine.get_or_create_collection("documents")

    from src.database.session import SessionLocal
    from src.models.document import Document
    db = SessionLocal()
    try:
        docs = db.query(Document).all()
        texts = []
        ids = []
        metadatas = []
        for doc in docs:
            content = doc.content or ""
            if content:
                texts.append(content)
                ids.append(f"doc_{doc.id}")
                metadatas.append({
                    "title": doc.title,
                    "doc_type": doc.doc_type,
                    "department": doc.department or "",
                    "tags": doc.tags or "",
                })

        if texts:
            print(f"Embedding {len(texts)} documents (this may take a while on first run)...")
            embeddings = _embedder.embed(texts)
            collection.add(ids=ids, embeddings=embeddings, documents=texts, metadatas=metadatas)
            print(f"Vector store: {collection.count()} documents indexed")
    finally:
        db.close()


def seed_whoosh():
    print("\n--- Seeding Whoosh Keyword Index ---")
    keyword_engine.rebuild_index()

    from src.database.session import SessionLocal
    from src.models.document import Document
    from src.models.log_entry import LogEntry
    db = SessionLocal()
    try:
        batch = []

        docs = db.query(Document).all()
        for doc in docs:
            batch.append({
                "doc_id": f"doc_{doc.id}",
                "title": doc.title,
                "content": doc.content or "",
                "source_type": f"document:{doc.doc_type}",
                "tags": doc.tags or "",
                "metadata": f"dept={doc.department},author={doc.author}",
            })

        logs = db.query(LogEntry).limit(200).all()
        for log in logs:
            batch.append({
                "doc_id": f"log_{log.id}",
                "title": f"[{log.level}] {log.module}",
                "content": log.message,
                "source_type": "logs",
                "tags": f"level={log.level},module={log.module}",
                "metadata": f"ts={log.timestamp}",
            })

        if batch:
            keyword_engine.index_batch(batch)
            print(f"Keyword index: {len(batch)} documents indexed")
    finally:
        db.close()


def main():
    print("=" * 60)
    print("Initializing database...")
    init_db()

    db = SessionLocal()
    try:
        seed_sqlite(db)
    finally:
        db.close()

    seed_chroma()
    seed_whoosh()

    print("\n" + "=" * 60)
    print("All seed data initialized successfully!")
    print("Run: python -m uvicorn src.main:app --reload")
    print("Open: http://localhost:8000")


if __name__ == "__main__":
    main()
