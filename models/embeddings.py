import os
from FlagEmbedding import BGEM3FlagModel
from dotenv import load_dotenv

load_dotenv()

EMBEDDING_MODEL = os.getenv("EMBEDDING_MODEL", "BAAI/bge-m3")

class BGEEmbedder:
    def __init__(self):
        # Load the BGE-M3 model into memory
        # bge-m3 supports dense, sparse, and colbert
        print(f"Loading BGE-M3 Embedding Model: {EMBEDDING_MODEL}...")
        self.model = BGEM3FlagModel(EMBEDDING_MODEL, use_fp16=True)

    def embed_dense(self, texts: list[str]):
        """Generate dense representations for FAISS / standard vector DBs."""
        # return_dense=True, return_sparse=False, return_colbert_vecs=False
        embeddings = self.model.encode(texts, return_dense=True)['dense_vecs']
        return embeddings

    def embed_sparse(self, texts: list[str]):
        """Generate lexical sparse representations."""
        sparse_vecs = self.model.encode(texts, return_dense=False, return_sparse=True)['lexical_weights']
        return sparse_vecs

bge_m3 = BGEEmbedder()
