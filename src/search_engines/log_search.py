import json
from datetime import datetime, timedelta
from sqlalchemy import desc
from .base import SearchEngine, SearchResult
from .keyword_search import keyword_engine
from ..database.session import SessionLocal
from ..models.log_entry import LogEntry


class LogSearchEngine(SearchEngine):
    def search(self, query: str, top_k: int = 10, **kwargs) -> list[SearchResult]:
        results = []

        level_filter = kwargs.get("level")
        days_back = kwargs.get("days_back")

        db = SessionLocal()
        try:
            q = db.query(LogEntry)
            if level_filter:
                q = q.filter(LogEntry.level == level_filter.upper())
            if days_back:
                cutoff = datetime.now() - timedelta(days=int(days_back))
                q = q.filter(LogEntry.timestamp >= cutoff)

            if query:
                q = q.filter(LogEntry.message.contains(query))

            rows = q.order_by(desc(LogEntry.timestamp)).limit(top_k).all()

            for r in rows:
                extra = json.loads(r.extra_data) if r.extra_data else {}
                metadata = {
                    "id": r.id,
                    "level": r.level,
                    "module": r.module,
                    "function": r.function_name,
                    "timestamp": str(r.timestamp),
                    "request_id": r.request_id,
                }
                metadata.update(extra)
                results.append(SearchResult(
                    source="log_system",
                    title=f"[{r.level}] {r.module}.{r.function_name}",
                    snippet=r.message,
                    score=0.9,
                    metadata=metadata,
                ))
        finally:
            db.close()

        if len(results) < top_k:
            kw_results = keyword_engine.search(query, top_k=top_k - len(results), source_type="logs")
            results.extend(kw_results)

        return results


log_engine = LogSearchEngine()
