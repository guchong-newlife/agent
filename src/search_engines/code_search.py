from .base import SearchEngine, SearchResult
from .keyword_search import keyword_engine
from ..repo_manager.git_manager import git_manager


class CodeSearchEngine(SearchEngine):
    def search(self, query: str, top_k: int = 10, **kwargs) -> list[SearchResult]:
        results = []
        repo_name = kwargs.get("repo_name")

        grep_results = git_manager.grep_code(query, repo_name)
        for r in grep_results[:top_k]:
            results.append(SearchResult(
                source="code_repository",
                title=f"{r['repo']}/{r['file']}:{r['line']}",
                snippet=r["content"],
                score=0.95,
                metadata={"repo": r["repo"], "file": r["file"], "line": r["line"], "search_type": "grep"},
            ))

        remaining = top_k - len(results)
        if remaining > 0:
            kw_results = keyword_engine.search(query, top_k=remaining, source_type="code")
            results.extend(kw_results)

        return results


code_engine = CodeSearchEngine()
