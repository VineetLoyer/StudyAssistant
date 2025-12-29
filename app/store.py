import faiss, numpy as np
from typing import List, Dict, Tuple
from .ingestion import Chunk
from .embeddings import embed_texts

class VectorStore:
    def __init__(self):
        self.index=None
        self.id2chunk: Dict[int, Chunk] = {}
        self.next_id=0
        self.dim = None

    def _ensure(self, d:int):
        if self.index is None:
            self.index = faiss.IndexFlatIP(d)
            self.dim = d

    def add_corpus(self, corpus_id: str, chunks: List[Chunk]):
        texts=[c.text for c in chunks]
        vecs=embed_texts(texts)
        self._ensure(vecs.shape[1])
        ids=np.arange(self.next_id, self.next_id+len(chunks))
        self.next_id += len(chunks)
        self.index.add(vecs)
        for i,c in zip(ids,chunks):
            self.id2chunk[int(i)] = c

    def search(self, query: str, corpus_id: str, k: int = 8) -> List[Tuple[int,float]]:
        if self.index is None: return []
        qv = embed_texts([query])
        D, I = self.index.search(qv, min(k*6, len(self.id2chunk)))  # overfetch
        hits=[]
        for idx, score in zip(I[0], D[0]):
            if idx == -1: continue
            ch = self.id2chunk.get(int(idx))
            if ch and ch.uid.startswith(corpus_id + ":"):
                hits.append((int(idx), float(score)))
            if len(hits) >= k: break
        return hits

    def get_chunks(self, ids: List[int]) -> List[Chunk]:
        return [self.id2chunk[i] for i in ids if i in self.id2chunk]
   
   
    def all_chunks_for_corpus(self, corpus_id: str, max_per_source: int = 5, max_total: int = 30):
        # gather chunks belonging to corpus_id, lightly balanced across source_ids
        items = [c for c in self.id2chunk.values() if c.uid.startswith(corpus_id + ":")]
        # group by source_id
        from collections import defaultdict
        buckets = defaultdict(list)
        for c in items:
            buckets[c.source_id].append(c)
        # take up to max_per_source from each, then cap total
        snippets = []
        for sid in sorted(buckets, key=lambda x: int(x)):
            for c in buckets[sid][:max_per_source]:
                snippets.append({"source_id": c.source_id, "text": c.text})
                if len(snippets) >= max_total:
                    return snippets
        return snippets[:max_total]