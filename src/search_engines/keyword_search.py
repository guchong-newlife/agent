import os
import jieba
from whoosh import index
from whoosh.fields import Schema, TEXT, ID, STORED
from whoosh.qparser import MultifieldParser
from whoosh.analysis import Tokenizer, Token
from .base import SearchEngine, SearchResult
from ..config import settings


class ChineseTokenizer(Tokenizer):
    def __call__(self, value, positions=False, chars=False, keeporiginal=False, removestops=True,
                 start_pos=0, start_char=0, mode="", **kwargs):
        words = list(jieba.cut(value, cut_all=False))
        pos = 0
        for w in words:
            w = w.strip()
            if w:
                t = Token(positions=positions, chars=chars, removestops=removestops,
                          mode=mode, **kwargs)
                t.text = w
                if positions:
                    t.pos = pos
                pos += 1
                yield t


class KeywordSearchEngine(SearchEngine):
    def __init__(self):
        self.index_dir = os.path.abspath(settings.whoosh_index_dir)
        self.schema = Schema(
            doc_id=ID(stored=True, unique=True),
            title=TEXT(stored=True, analyzer=ChineseTokenizer()),
            content=TEXT(stored=True, analyzer=ChineseTokenizer()),
            source_type=ID(stored=True),
            tags=TEXT(stored=True, analyzer=ChineseTokenizer()),
            metadata=STORED(),
        )
        self._ix: index.Index | None = None

    @property
    def ix(self) -> index.Index:
        if self._ix is None:
            os.makedirs(self.index_dir, exist_ok=True)
            if index.exists_in(self.index_dir):
                self._ix = index.open_dir(self.index_dir)
            else:
                self._ix = index.create_in(self.index_dir, self.schema)
        return self._ix

    def index_document(self, doc_id: str, title: str, content: str, source_type: str, tags: str = "", metadata: str = ""):
        writer = self.ix.writer()
        writer.update_document(
            doc_id=doc_id,
            title=title,
            content=content,
            source_type=source_type,
            tags=tags,
            metadata=metadata,
        )
        writer.commit()

    def index_batch(self, docs: list[dict]):
        writer = self.ix.writer()
        for doc in docs:
            writer.update_document(
                doc_id=doc["doc_id"],
                title=doc.get("title", ""),
                content=doc.get("content", ""),
                source_type=doc.get("source_type", ""),
                tags=doc.get("tags", ""),
                metadata=doc.get("metadata", ""),
            )
        writer.commit()

    def search(self, query: str, top_k: int = 10, **kwargs) -> list[SearchResult]:
        with self.ix.searcher() as searcher:
            parser = MultifieldParser(["title", "content", "tags"], self.ix.schema)
            q = parser.parse(query)
            hits = searcher.search(q, limit=top_k)
            results = []
            for hit in hits:
                results.append(SearchResult(
                    source=f"keyword_search:{hit.get('source_type', 'unknown')}",
                    title=hit.get("title", ""),
                    snippet=(hit.get("content", "") or "")[:300],
                    score=hit.score,
                    metadata={"doc_id": hit.get("doc_id", ""), "raw_metadata": hit.get("metadata", "")},
                ))
            return results

    def rebuild_index(self):
        if index.exists_in(self.index_dir):
            import shutil
            shutil.rmtree(self.index_dir)
        self._ix = index.create_in(self.index_dir, self.schema)


keyword_engine = KeywordSearchEngine()
