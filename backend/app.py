import os
import logging
from flask import Flask, request, jsonify
from flask_cors import CORS
from datetime import datetime, timedelta, timezone
from dotenv import load_dotenv

from backend.summarize_conversation import GeminiGenerator
from models.models import Memory
from backend.db.kv_store import KVStore

load_dotenv()

# Setup logging
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

app = Flask(__name__)
CORS(app)

kv_store = KVStore()
generator = GeminiGenerator()

@app.route('/sync', methods=['POST'])
def sync():
    logger.info("Received sync request")

    data = request.json
    messages = data.get('messages', [])
    metadata = data.get('metadata', {})

    logger.info(f"Sync data: {len(messages)} messages")    
    
    memories = generator.generate_memory(messages)
    
    for memory_str in memories:        
        kv_store.add_memory(platform=metadata['platform'], memory=Memory(
            memory=memory_str,
            metadata=None
        ))
        
    print(kv_store.kv_store)
        
    logger.info(f"Sync successful: {len(memories)} memories stored")
    
    return jsonify({
        'success': True,
        'count': len(memories),
        'memories_stored': len(memories) if isinstance(memories, list) else 1
    })

@app.route('/memories', methods=['GET'])
def get_memories():
    """Get all memories across all platforms"""

    logger.info("Received memories request")

    memories = []
    store = kv_store.get_all_memories()
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

@app.route('/load', methods=['GET'])
def load():
    logger.info("Received load request")

    current_platform = request.args.get('platform')

    platforms = {'chatgpt', 'claude'}
    if current_platform in platforms:
        platforms.remove(current_platform)

    for platform in platforms:
        
        # Get memories from other platforms after timestamp_to_fetch_from
        # timestamp_to_fetch_from is the latest timestamp from the current platform's memory sync
        loaded_memories = []
        
        store = kv_store.get_all_memories()
        memories_from_current_platform = store[current_platform]
        if not memories_from_current_platform:
            # we want all the memories so we set timestamp_to_fetch_from to the lowest possible value
            timestamp_to_fetch_from = datetime.min
        else:
            store = kv_store.get_all_memories()
            timestamp_to_fetch_from = store[current_platform][-1][1]
        
        memories = kv_store.get_memories(platform=platform, timestamp=timestamp_to_fetch_from)
        loaded_memories.extend(memories)

    formatted = format_memories(loaded_memories)
    print("LOADED MEMORIES: ", formatted)

    return jsonify({
        'formatted_text': formatted,
        'memory_count': len(loaded_memories)
    })

def format_memories(memories):
    if not memories:
        return "No new memories from other platforms."

    text = "Update your memory with these facts from other platforms:\n\n"

    for memory_tuple in memories:
        text += "- " + memory_tuple[0].memory + "\n"
    
    return text.strip()

@app.errorhandler(500)
def internal_error(error):
    return jsonify({'success': False, 'error': str(error)}), 500

@app.errorhandler(400)
def bad_request(error):
    return jsonify({'success': False, 'error': 'Invalid request'}), 400

if __name__ == '__main__':
    api_key = os.getenv("OPENAI_API_KEY")
    if not api_key:
        logger.error("OPENAI_API_KEY not set in .env file!")
        logger.error("Create .env file with: OPENAI_API_KEY=your_key_here")
        exit(1)

    PORT = 5001  # Changed from 5000 (macOS uses 5000 for AirPlay)

    logger.info("="*50)
    logger.info("Starting Unified Memory backend")
    logger.info(f"Backend URL: http://localhost:{PORT}")
    logger.info("CORS: Enabled for all origins")

    app.run(host='localhost', port=PORT, debug=True)
