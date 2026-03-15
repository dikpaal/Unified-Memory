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
    """Get all memories for current platform"""
    logger.info("Received memories request")
    try:
        if m is None:
            return jsonify({'success': False, 'error': 'Backend not initialized'}), 500

        platform = request.args.get('platform')
        if not platform:
            return jsonify({'success': False, 'error': 'Missing platform'}), 400

        logger.info(f"Fetching memories for {USER_ID}")

        # Get all memories for this user
        results = m.get_all(user_id=USER_ID)
        memory_list = results['results']

        logger.info(f"Found {len(memory_list)} memories")

        # Format for display
        memories = [{
            'text': mem.get('memory', ''),
            'created': mem.get('created_at', '')[:16] if mem.get('created_at') else ''
        } for mem in memory_list]

        return jsonify({
            'success': True,
            'memories': memories
        })
    except Exception as e:
        logger.error(f"Memories error: {e}")
        return jsonify({'success': True, 'memories': []}), 200

@app.route('/load', methods=['GET'])
def load():
    logger.info("Received load request")
    try:
        if m is None:
            logger.error("mem0 not initialized")
            return jsonify({'success': False, 'error': 'Backend not initialized'}), 500

        current_platform = request.args.get('platform')
        # Get memories from other platforms
        seven_days_ago = datetime.now(timezone.utc) - timedelta(days=7)

        platforms = {'chatgpt', 'claude'}
        if current_platform in platforms:
            platforms.remove(current_platform)

        all_memories = []

        for platform in platforms:

            results = m.get_all(user_id=USER_ID)
            logger.info(f"Got memories for {platform}: {type(results)}, {results is not None}")
            memory_list = results['results']
            
            for memory in memory_list:
                # Parse timestamp
                created_str = memory.get('created_at', '')
                created = datetime.fromisoformat(created_str.replace('Z', '+00:00'))
                if memory['metadata']['platform'] == platform and created > seven_days_ago:
                    all_memories.append({
                        'platform': platform,
                        'memory': memory.get('memory', ''),
                        'timestamp': created_str
                    })
                    
        # Format memories
        print("ALL MEMORIES: ", all_memories)
        formatted = format_memories(all_memories)
        logger.info(f"Load successful: {len(all_memories)} memories found")

        return jsonify({
            'formatted_text': formatted,
            'memory_count': len(all_memories)
        })
    except Exception as e:
        logger.error(f"Load error: {e}")
        return jsonify({'success': False, 'error': str(e)}), 500

def format_memories(memories):
    if not memories:
        return "No new memories from other platforms."

    text = "Update your memory with these facts from other platforms:\n\n"

    # Group by platform
    by_platform = {}
    for m in memories:
        platform = m['platform'].title()
        print("PLATFORM: ", platform)
        if platform not in by_platform:
            by_platform[platform] = []

        by_platform[platform].append(m)

    for platform, items in by_platform.items():
        # Get latest timestamp
        latest_time = items[0]['timestamp'][:16] if items[0]['timestamp'] else ''
        text += f"From {platform} ({latest_time}):\n"
        for item in items:
            memory_text = item['memory'].strip()
            if memory_text:
                text += f"- {memory_text}\n"
        text += "\n"

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
