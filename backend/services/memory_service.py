from datetime import datetime
from backend.db.kv_store import KVStore
from backend.generators.gemini_generator import Gemini
from backend.models.models import Memory

from collections import defaultdict


class MemoryService:

    def __init__(self):
        self.kv_store = KVStore()
        self.generator = Gemini()

    def sync_memories(self, messages, metadata):

        memories = self.generator.generate_memories(messages)
        updated_memories = self._update_memories_and_embeddings(memories=memories)
        print("UPDATED MEMORIES: ", updated_memories)
        
        for index in range(len(updated_memories)):
            embedding = self.generator.embed_text(updated_memories[index])
            memory = updated_memories[index]
            print(f'- {memory}: {embedding}\n')
            
            self.kv_store.add_memory(
                platform=metadata["platform"],
                memory=Memory(memory=memory, metadata=None),
                embedding=embedding
            )

        print(memories)
        
        return memories

    def get_all_memories(self):

        memories = []
        store = self.kv_store.get_all_memories()

        for _, mem_list in store.items():
            memories.extend(mem_list)

        return [{
            "text": m[0].memory,
            "created": m[1]
        } for m in memories]

    def load_cross_platform_memories(self, current_platform):

        platforms = {"chatgpt", "claude"}
        platforms.discard(current_platform)

        loaded_memories = []

        store = self.kv_store.get_all_memories()
        memories_from_current = store.get(current_platform, [])

        if not memories_from_current:
            timestamp = datetime.min
        else:
            timestamp = memories_from_current[-1][1]

        for platform in platforms:
            memories = self.kv_store.get_memories(
                platform=platform,
                timestamp=timestamp
            )
            loaded_memories.extend(memories)

        return loaded_memories
    

    def format_memories_for_load(self, memories):
        """
        Format memories as text for AI to update its memory
        """
        
        if not memories:
            return "No new memories from other platforms."

        text = "Update your memory with these facts from other platforms:\n\n"
        for memory in memories:
            text += f"- {memory.memory}\n"

        return text.strip()
    
    
    def _update_memories_and_embeddings(self, memories):
        
        # memory -> [similar memories from db based on similarity score]
        similar_memories = defaultdict(list)
        
        for memory in memories:
            similar_memories[memory].append(memory)
        
        for index in range(len(memories)):
            memory = memories[index]
            embedding = self.generator.embed_text(memory) 
            retrieved_memories = self.kv_store.perform_vector_search(embedding=embedding)
            similar_memories[memory].extend(retrieved_memories)
            
        updated_memories = []
        
        for memory in similar_memories:
            if not similar_memories[memory]:
                continue
            
            updated_mems = self.generator.update_memories(new_memory=memory, memories=similar_memories[memory])
            updated_memories.extend(updated_mems)
            
        return updated_memories