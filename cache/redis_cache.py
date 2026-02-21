import os
import json
import gzip
import hashlib
from redis import Redis
from redisvl.index import SearchIndex
from redisvl.query import VectorQuery
from models.embeddings import bge_m3
from cachetools import TTLCache

# Global TTLs
SEMANTIC_CACHE_TTL = 7200  # 2 hours

# L1: In-memory, instant, zero bandwidth cost (100 items, 5 min TTL)
l1_cache = TTLCache(maxsize=100, ttl=300)

def compress_value(data: dict) -> bytes:
    json_str = json.dumps(data, separators=(',', ':'))
    return gzip.compress(json_str.encode(), compresslevel=6)

def decompress_value(data: bytes) -> dict:
    return json.loads(gzip.decompress(data).decode())

def make_cache_key(prefix: str, query: str) -> str:
    query_hash = hashlib.md5(query.encode()).hexdigest()[:16]
    return f"{prefix}:{query_hash}"

class RedisSemanticCache:
    def __init__(self):
        # Override to use Upstash specifically
        redis_url = os.getenv("UPSTASH_REDIS_REST_URL", os.getenv("REDIS_URL", "redis://localhost:6379/0"))
        # Using standard Redis client here, assuming URL has necessary auth or we build from REST format if strictly requested.
        # Often UPSTASH_REDIS_REST_URL is http, but the `redis` python package requires redis:// or rediss://.
        # We assume standard redis compatible connection string is provided in reality, or use standard `redis` init.
        # For this requirement, we'll initialize assuming REDIS_URL style if using `redis` library.
        # Note: If strictly REST, a different client is needed, but `redis` library usually works with upstash endpoints starting with rediss://
        redi_conn_url = os.getenv("UPSTASH_REDIS_TIO_URL", os.getenv("REDIS_URL", "redis://localhost:6379/0"))
        
        self.threshold = float(os.getenv("CACHE_THRESHOLD", "0.88"))
        self.redis = Redis.from_url(redi_conn_url)
        
        # Define the redisvl schema
        schema = {
            "index": {
                "name": "brd_semantic_cache",
                "prefix": "sem:"
            },
            "fields": [
                {"name": "query_embedding", "type": "vector", "attrs": {
                    "dims": 1024,
                    "distance_metric": "cosine",
                    "algorithm": "flat",
                    "datatype": "float32"
                }}
                # Note: 'payload' (compressed data) is not indexed, just stored alongside
            ]
        }
        
        try:
            self.index = SearchIndex.from_dict(schema)
            self.index.connect(self.redis)
            self.index.create(overwrite=False)
        except Exception as e:
            print(f"Redis Cache init error (ensure redis is running): {e}")

    def check(self, query: str, section_name: str, threshold: float = None):
        """Check L1 Cache first, then L2 Upstash, with compression support."""
        # 1. Check L1 Cache
        cache_key = make_cache_key("sem", query)
        if cache_key in l1_cache:
            print(f"[CACHE HIT] L1 Instant Hit: {cache_key}")
            return l1_cache[cache_key].get("answer")

        # 2. Check L2 Cache (Vector Search for semantic match)
        thresh = threshold or self.threshold
        query_vector = bge_m3.embed_dense([query])[0]
        
        v_query = VectorQuery(
            vector=query_vector.tolist(),
            vector_field_name="query_embedding",
            return_fields=["payload", "vector_distance"],
            num_results=1
        )
        
        results = self.index.query(v_query)
        if not results:
            return None
            
        doc = results[0]
        distance = float(doc.get("vector_distance", 1.0))
        similarity = 1.0 - distance
        
        if similarity >= thresh:
            print(f"[CACHE HIT] L2 Upstash Similarity: {similarity:.2f}")
            payload_bytes = doc.get("payload")
            if payload_bytes:
                # Decompress from Upstash
                data = decompress_value(payload_bytes)
                # Promote to L1
                l1_cache[cache_key] = data
                return data.get("answer")
            
        return None

    def store(self, query: str, section_name: str, answer: str, inference_time_ms: int = 4000):
        """Smart cache eviction: only store if high value."""
        # Only cache if query is substantive and result is not bloated
        if len(query) < 20: 
            return
            
        doc_content = {
            "query": query,
            "answer": answer,
            "section": section_name
        }
        
        value_size = len(json.dumps(doc_content).encode())
        
        # Don't cache bloated responses or ultra-fast generations
        if inference_time_ms > 3000 and value_size < 50000:
            query_vector = bge_m3.embed_dense([query])[0]
            compressed_payload = compress_value(doc_content)
            
            key = make_cache_key("sem", query)
            
            mapping = {
                "query_embedding": query_vector.tobytes(), # redisvl expects bytes/lists depending on setup
                "payload": compressed_payload
            }
            
            # Store with strict TTL to prevent free-tier bloat
            pipe = self.redis.pipeline()
            pipe.hset(key, mapping=mapping) # We use raw redis operation to set TTL easily
            pipe.expire(key, SEMANTIC_CACHE_TTL)
            pipe.execute()

redis_cache = RedisSemanticCache()
