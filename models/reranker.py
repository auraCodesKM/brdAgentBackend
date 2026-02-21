import os
from FlagEmbedding import FlagReranker
from dotenv import load_dotenv

load_dotenv()

RERANKER_MODEL = os.getenv("RERANKER_MODEL", "BAAI/bge-reranker-large")

class CrossEncoderReranker:
    def __init__(self):
        print(f"Loading Cross-Encoder Reranker: {RERANKER_MODEL}...")
        self.model = FlagReranker(RERANKER_MODEL, use_fp16=True)

    def rerank_and_score(self, query: str, context_chunks: list[str]):
        """
        Scores the relevance between 0.0 and 1.0 using the BGE cross-encoder.
        Used extensively in CRAG to discard context < 0.6.
        """
        pairs = [[query, chunk] for chunk in context_chunks]
        # model.compute_score returns logits, so we apply a sigmoid if raw logits desired, or just use relative scaling.
        # Note: raw scores can be negative, so we normalize for CRAG (0 to 1 mapping approximation)
        scores = self.model.compute_score(pairs)
        
        # If single item, convert to list for zip
        if isinstance(scores, float):
            scores = [scores]

        # Simple logistic sigmoid normalization to get 0.0 - 1.0 confidence pseudo-probability
        import math
        def sigmoid(x):
            return 1 / (1 + math.exp(-x))
            
        normalized_scores = [sigmoid(s) for s in scores]
        
        results = [{"chunk": c, "score": s} for c, s in zip(context_chunks, normalized_scores)]
        # Sort descending by score
        results.sort(key=lambda x: x["score"], reverse=True)
        return results

bge_reranker = CrossEncoderReranker()
