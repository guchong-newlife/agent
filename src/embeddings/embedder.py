import hashlib
import numpy as np
from ..config import settings


class Embedder:
    def __init__(self):
        self._dimension = settings.embedding_dimension

    @property
    def dimension(self) -> int:
        return self._dimension

    def embed(self, texts: list[str]) -> list[list[float]]:
        return [self.embed_query(t) for t in texts]

    def embed_query(self, text: str) -> list[float]:
        h = hashlib.sha256(text.encode("utf-8")).digest()
        seed = int.from_bytes(h[:4], "big")  # 32-bit seed for numpy
        rng = np.random.RandomState(seed)
        vec = rng.randn(self._dimension).astype(np.float32)
        norm = np.linalg.norm(vec)
        if norm > 0:
            vec = vec / norm
        return vec.tolist()


embedder = Embedder()
