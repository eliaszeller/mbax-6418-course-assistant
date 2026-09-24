from __future__ import annotations

import math
import re
import hashlib
from collections import Counter

from .models import SourceChunk


STOPWORDS = {"a", "an", "and", "are", "as", "at", "be", "for", "from", "in", "is", "it", "of", "on", "or", "the", "to", "what"}


def tokenize(text: str) -> list[str]:
    return [token for token in re.findall(r"[a-z0-9]+", text.lower()) if token not in STOPWORDS]


class HybridRetriever:
    """Separate text/visual indexes with lexical and deterministic vector scores.

    The deterministic vector is a no-network baseline. Replace `_embed` with the
    documented class embedding calls once those schemas are supplied.
    """

    def __init__(self, chunks: list[SourceChunk], dimensions: int = 256):
        self.chunks = chunks
        self.dimensions = dimensions
        self.docs = [tokenize(c.text) for c in chunks]
        self.df = Counter(token for doc in self.docs for token in set(doc))
        self.avgdl = sum(map(len, self.docs)) / max(len(self.docs), 1)
        self.vectors = [self._embed(c.text) for c in chunks]

    def _embed(self, text: str) -> list[float]:
        vector = [0.0] * self.dimensions
        for token in tokenize(text):
            bucket = int.from_bytes(hashlib.blake2b(token.encode(), digest_size=8).digest(), "big") % self.dimensions
            vector[bucket] += 1.0
        norm = math.sqrt(sum(x * x for x in vector)) or 1.0
        return [x / norm for x in vector]

    def _bm25(self, query: list[str], index: int) -> float:
        doc = self.docs[index]
        tf = Counter(doc)
        score = 0.0
        for term in query:
            n = self.df.get(term, 0)
            idf = math.log(1 + (len(self.docs) - n + 0.5) / (n + 0.5))
            freq = tf.get(term, 0)
            denom = freq + 1.5 * (1 - 0.75 + 0.75 * len(doc) / max(self.avgdl, 1))
            score += idf * (freq * 2.5 / denom if denom else 0)
        return score

    def search(self, query: str, materials: list[str] | None = None, topic: str = "", limit: int = 8) -> list[SourceChunk]:
        expanded = f"{query} {topic}".strip()
        q_tokens = tokenize(expanded)
        q_vector = self._embed(expanded)
        scored = []
        for i, chunk in enumerate(self.chunks):
            if materials and chunk.material not in materials:
                continue
            semantic = sum(a * b for a, b in zip(q_vector, self.vectors[i]))
            lexical = self._bm25(q_tokens, i)
            kind_weight = 1.05 if chunk.kind == "visual" and any(w in q_tokens for w in ("chart", "diagram", "image", "figure")) else 1.0
            scored.append(((0.55 * lexical + 0.45 * semantic) * kind_weight, chunk))
        scored.sort(key=lambda item: item[0], reverse=True)
        return [chunk for _, chunk in scored[:limit]]
