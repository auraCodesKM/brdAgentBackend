from pydantic import BaseModel
from typing import List, Optional

class UserExtract(BaseModel):
    id: str
    email: str

class GenerateRequest(BaseModel):
    query: str
    # Array of document IDs to specifically search over, or empty for all
    source_ids: Optional[List[str]] = None
    
class GenerateResponse(BaseModel):
    text: str
    citations: List[dict]
