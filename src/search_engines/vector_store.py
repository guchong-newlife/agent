import os
import chromadb
from chromadb.config import Settings as ChromaSettings
from .base import SearchEngine, SearchResult
from ..config import settings
from ..embeddings.embedder import embedder as _embedder


class VectorSearchEngine(SearchEngine):
    def __init__(self):
        self.persist_dir = os.path.abspath(settings.chroma_persist_dir)
        os.makedirs(self.persist_dir, exist_ok=True)
        self._client = chromadb.PersistentClient(
            path=self.persist_dir,
            settings=ChromaSettings(anonymized_telemetry=False),
        )

    def get_or_create_collection(self, name: str):
        return self._client.get_or_create_collection(name=name)

    def list_collections(self) -> list[str]:
        return [c.name for c in self._client.list_collections()]

    def add_documents(self, collection_name: str, doc_ids: list[str], texts: list[str],
                      metadatas: list[dict] | None = None):
        if not texts:
            return
        embeddings = _embedder.embed(texts)
        collection = self.get_or_create_collection(collection_name)
        collection.add(
            ids=doc_ids,
            embeddings=embeddings,
            documents=texts,
            metadatas=metadatas or [{}] * len(texts),
        )

    def search(self, query: str, top_k: int = 10, collection_name: str | None = None, **kwargs) -> list[SearchResult]:
        query_embedding = _embedder.embed_query(query)
        results = []

        if collection_name:
            collections = [self.get_or_create_collection(collection_name)]
        else:
            collections = [self.get_or_create_collection(c) for c in self.list_collections()]

        for coll in collections:
            if coll.count() == 0:
                continue
            query_results = coll.query(query_embeddings=[query_embedding], n_results=min(top_k, coll.count()))
            if not query_results["ids"] or not query_results["ids"][0]:
                continue
            for i, doc_id in enumerate(query_results["ids"][0]):
                doc_text = query_results["documents"][0][i] if query_results["documents"] else ""
                distance = query_results["distances"][0][i] if query_results["distances"] else 0
                meta = query_results["metadatas"][0][i] if query_results["metadatas"] else {}
                results.append(SearchResult(
                    source=f"vector_store:{coll.name}",
                    title=meta.get("title", f"文档片段 {doc_id}"),
                    snippet=doc_text[:300] if doc_text else "",
                    score=1.0 - distance,
                    metadata={"collection": coll.name, "doc_id": doc_id, **meta},
                ))
        results.sort(key=lambda r: r.score, reverse=True)
        return results[:top_k]

    def clear_collection(self, name: str):
        try:
            self._client.delete_collection(name)
        except Exception:
            pass


vector_engine = VectorSearchEngine()
