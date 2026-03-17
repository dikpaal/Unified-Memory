from pydantic import BaseModel, Field
from uuid import UUID, uuid4
from typing import Dict, List
from enum import Enum

class Memory(BaseModel):
    memory_id: UUID = Field(default_factory=uuid4)
    memory: str
    metadata: Dict | None

class Memories(BaseModel):
    memories: List[str]
 
class Summary(BaseModel):
    summary: str

class RelationType(str, Enum):
    CONTRADICTS = "contradicts"
    SUPPORTS = "supports"
    PARTIAL = "partial"
    UNRELATED = "unrelated"

class MemoryRelation(BaseModel):
    candidate_id: str
    relation: RelationType
    confidence: float  # 0 → 1
    reasoning: str     # keep short (1 sentence max)

class ContradictionCheckOutput(BaseModel):
    results: List[MemoryRelation]