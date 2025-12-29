import os, numpy as np
from typing import List
from sentence_transformers import SentenceTransformer

_model = None
def get_model():
    global _model
    if _model is None:
        name = os.getenv("EMBEDDING_MODEL", "sentence-transformers/all-MiniLM-L6-v2")
        _model = SentenceTransformer(name)
    return _model

def embed_texts(texts: List[str]) -> np.ndarray:
    m = get_model()
    v = m.encode(texts, normalize_embeddings=True, convert_to_numpy=True)
    return v.astype("float32")
