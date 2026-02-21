import os
import json
from redis import Redis
from redis.commands.search.field import TextField
from redis.commands.search.index_definition import IndexDefinition, IndexType
from redis.commands.search.query import Query
from dotenv import load_dotenv

load_dotenv()

BM25_INDEX_TTL = 86400  # 24 hours

class RedisBM25Index:
    def __init__(self):
        redis_url = os.getenv("UPSTASH_REDIS_TIO_URL", os.getenv("REDIS_URL", "redis://localhost:6379/0"))
        self.redis = Redis.from_url(redis_url)
        self.index_name = "brd_bm25_index"
        
        try:
            # We ONLY index the specific text fields needed for BM25 term frequency counting
            # We explicitly do NOT store the full document to save Upstash free-tier limits
            schema = (TextField("content", weight=1.0),)
            self.redis.ft(self.index_name).create_index(
                schema,
                definition=IndexDefinition(prefix=["doc:bm25:"], index_type=IndexType.HASH)
            )
        except Exception:
            pass

    def add_documents(self, chunks: list[str]):
        """
        Index raw text chunks into Redis for sparse retrieval.
        Using pipelining and strict 24hr TTLs.
        """
        pipe = self.redis.pipeline()
        for idx, chunk in enumerate(chunks):
            # Minimizing key size
            import hashlib
            doc_hash = hashlib.md5(chunk.encode()).hexdigest()[:16]
            doc_id = f"doc:bm25:{doc_hash}"
            
            # The prompt requested saving bandwidth by NOT storing full text if possible,
            # but RediSearch *needs* the text to be in a field mapped by schema to search it.
            # To optimize, we just store what's absolutely necessary.
            pipe.hset(doc_id, mapping={"content": chunk})
            pipe.expire(doc_id, BM25_INDEX_TTL)
            
        try:
            pipe.execute()
        except Exception as e:
            print(f"Redis pipeline execution failed: {e}")

    async def search(self, query_str: str, top_k: int = 10):
        """
        Perform a BM25 sparse search using RediSearch.
        """
        clean_query = query_str.replace(":", " ").replace("-", " ")
        q = Query(clean_query).paging(0, top_k).with_scores()
        
        try:
            results = self.redis.ft(self.index_name).search(q)
            formatted = []
            for doc in results.docs:
                formatted.append({
                    "chunk": doc.content,
                    "score": doc.score,
                    "source": "bm25_redis"
                })
            return formatted
        except Exception as e:
            print(f"BM25 Search Error: {e}")
            return []

redis_bm25 = RedisBM25Index()
