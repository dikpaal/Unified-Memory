import os
import logging
from flask import Flask, request, jsonify
from flask_cors import CORS
from datetime import datetime, timedelta, timezone
from dotenv import load_dotenv

from backend.summarize_conversation import GeminiGenerator
from models.models import Memory
from backend.db.kv_store import KVStore


class UnifiedMemoryService:
    
    def __init__(self):
        load_dotenv()
        logging.basicConfig(level=logging.INFO)
        
        self.logger = logging.getLogger(__name__)
        self.kv_store = KVStore()
        self.generator = GeminiGenerator()
        
        self.app = Flask(__name__)
        CORS(self.app)
        
        # register routes
        self.register_routes()

    def register_routes(self):

        self.app.add_url_rule(
            "/sync",
            view_func=self.sync,
            methods=["POST"]
        )

        self.app.add_url_rule(
            "/memories",
            view_func=self.get_memories,
            methods=["GET"]
        )

        self.app.add_url_rule(
            "/load",
            view_func=self.load,
            methods=["GET"]
        )

    # ----------- ROUTES -----------
    
    def sync(self):
        self.logger.info("Received sync request")

        data = request.json
        messages = data.get('messages', [])
        metadata = data.get('metadata', {})

        self.logger.info(f"Sync data: {len(messages)} messages")    
        
        memories = self.generator.generate_memory(messages)
        
        for memory_str in memories:        
            self.kv_store.add_memory(platform=metadata['platform'], memory=Memory(
                memory=memory_str,
                metadata=None
            ))
            
        self.logger.info(f"Sync successful: {len(memories)} memories stored")
        
        return jsonify({
            'success': True,
            'count': len(memories),
            'memories_stored': len(memories) if isinstance(memories, list) else 1
        })

    def get_memories(self):
        """Get all memories across all platforms"""

        self.logger.info("Received memories request")

        memories = []
        store = self.kv_store.get_all_memories()
        for _, mem_list in store.items():
            memories.extend(mem_list)
        
        # Format for display
        formatted_memories = [{
            'text': memory_tuple[0].memory,
            'created': memory_tuple[1]
        } for memory_tuple in memories]

        return jsonify({
            'success': True,
            'memories': formatted_memories
        })

    def load(self):
        self.logger.info("Received load request")

        current_platform = request.args.get('platform')

        platforms = {'chatgpt', 'claude'}
        if current_platform in platforms:
            platforms.remove(current_platform)

        for platform in platforms:
            
            # Get memories from other platforms after timestamp_to_fetch_from
            # timestamp_to_fetch_from is the latest timestamp from the current platform's memory sync
            loaded_memories = []
            
            store = self.kv_store.get_all_memories()
            memories_from_current_platform = store[current_platform]
            if not memories_from_current_platform:
                # we want all the memories so we set timestamp_to_fetch_from to the lowest possible value
                timestamp_to_fetch_from = datetime.min
            else:
                store = self.kv_store.get_all_memories()
                timestamp_to_fetch_from = store[current_platform][-1][1]
            
            memories = self.kv_store.get_memories(platform=platform, timestamp=timestamp_to_fetch_from)
            loaded_memories.extend(memories)

        formatted = self._format_memories(loaded_memories)
        print("LOADED MEMORIES: ", formatted)

        return jsonify({
            'formatted_text': formatted,
            'memory_count': len(loaded_memories)
        })

    def _format_memories(self, memories):
        if not memories:
            return "No new memories from other platforms."

        text = "Update your memory with these facts from other platforms:\n\n"

        for memory_tuple in memories:
            text += "- " + memory_tuple[0].memory + "\n"
        
        return text.strip()