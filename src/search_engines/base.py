from abc import ABC, abstractmethod
from dataclasses import dataclass, field


@dataclass
class SearchResult:
    source: str
    title: str
    snippet: str
    score: float = 0.0
    metadata: dict = field(default_factory=dict)

    def to_dict(self) -> dict:
        return {
            "source": self.source,
            "title": self.title,
            "snippet": self.snippet,
            "score": self.score,
            "metadata": self.metadata,
        }


class SearchEngine(ABC):
    @abstractmethod
    def search(self, query: str, top_k: int = 10, **kwargs) -> list[SearchResult]:
        ...
