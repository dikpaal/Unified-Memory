from datetime import datetime, timezone
from typing import List
from collections import defaultdict


from models.models import Memory

class KVStore:

    def __init__(self):        
        """
        key: platform
        value: (Memory, timestamp)
        """
        
        self.kv_store = defaultdict(list)
        
    def add_memory(self, platform: str, memory: Memory):
        """
        Add memory for `platform` with current timestamp
        """
        
        if platform not in {'chatgpt', 'claude'}:
            raise ValueError("Invalid platform")
        
        self.kv_store[platform].append((memory, datetime.now(timezone.utc)))
        
    def get_memories(self, platform: str, timestamp: datetime) -> List[Memory]:
        """
        Returns the memories for a platform after `timestamp`
        """
            
        if platform not in {'chatgpt', 'claude'}:
            raise ValueError("Invalid platform")
        
        memories = self.kv_store[platform]
        
        l, r = 0, len(memories) - 1
        
        while l < r:
            mid = (l + r) // 2
            
            if memories[mid][1] < timestamp:
                # move right
                l = mid + 1
            else:
                # move left
                r = mid
                
        return memories[l:]
    
    def get_all_memories(self):
        return self.kv_store