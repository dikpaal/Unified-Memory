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
        existing_similar_memories = defaultdict(list)
        # memory -> [UUIDs of similar memories to delete]
        memory_uuids_to_delete = defaultdict(list)

        for index in range(len(memories)):
            memory = memories[index]
            embedding = self.generator.embed_text(memory)
            retrieved_memories = self.kv_store.perform_vector_search(embedding=embedding)

            # Track UUIDs and memory text separately
            for uuid, mem_text, score in retrieved_memories:
                existing_similar_memories[memory].append(mem_text)
                memory_uuids_to_delete[memory].append(uuid)

        # Group new memories that share overlapping UUIDs
        groups = self._group_memories_by_overlap(memories, memory_uuids_to_delete)

        updated_memories = []

        for group in groups:
            # Collect all unique existing memories for this group
            all_existing_mems = []
            all_uuids_to_delete = set()

            for memory in group:
                all_existing_mems.extend(existing_similar_memories[memory])
                all_uuids_to_delete.update(memory_uuids_to_delete[memory])

            # Deduplicate existing memories
            unique_existing_mems = list(set(all_existing_mems))

            # If no similar memories in group, just add all new ones
            if not unique_existing_mems:
                updated_memories.extend(group)
                continue

            # Pass to LLM: all new memories in group + their shared existing memories
            updated_mems = self.generator.update_memories(new_memories=group, memories=unique_existing_mems)
            updated_memories.extend(updated_mems)

            # Delete all old similar memories once per group
            for uuid in all_uuids_to_delete:
                self.kv_store.delete_memory(uuid)

        return updated_memories

    def _group_memories_by_overlap(self, memories, memory_uuids_to_delete):
        """
        Group memories that share overlapping UUIDs using union-find
        """
        # Map memory index to group id
        parent = {i: i for i in range(len(memories))}

        def find(x):
            if parent[x] != x:
                parent[x] = find(parent[x])
            return parent[x]

        def union(x, y):
            px, py = find(x), find(y)
            if px != py:
                parent[px] = py

        # Build UUID -> memory indices map
        uuid_to_indices = defaultdict(list)
        for i, memory in enumerate(memories):
            for uuid in memory_uuids_to_delete[memory]:
                uuid_to_indices[uuid].append(i)

        # Union memories that share UUIDs
        for indices in uuid_to_indices.values():
            for i in range(1, len(indices)):
                union(indices[0], indices[i])

        # Build groups
        groups_map = defaultdict(list)
        for i, memory in enumerate(memories):
            groups_map[find(i)].append(memory)

        return list(groups_map.values())