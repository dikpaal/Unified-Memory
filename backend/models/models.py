from pydantic import BaseModel, Field
from uuid import UUID, uuid4
from typing import Dict, List

class Memory(BaseModel):
    memory_id: UUID = Field(default_factory=uuid4)
    memory: str
    metadata: Dict | None

class Memories(BaseModel):
    memories: List[str]
 
class Summary(BaseModel):
    summary: str