from datetime import datetime
from datetime import datetime
from backend.db.kv_store import KVStore
from backend.llms.gemini import GeminiGenerator
from models.models import Memory


class MemoryService:

    def __init__(self):
        self.kv_store = KVStore()
        self.generator = GeminiGenerator()

    def sync_memories(self, messages, metadata):

        memories = self.generator.generate_memory(messages)

        for memory_str in memories:
            self.kv_store.add_memory(
                platform=metadata["platform"],
                memory=Memory(memory=memory_str, metadata=None),
            )

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