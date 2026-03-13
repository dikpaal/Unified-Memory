from flask import Flask, request, jsonify
from flask_cors import CORS
from mem0 import Memory
from datetime import datetime, timedelta, timezone
import os
from dotenv import load_dotenv
import logging
import traceback

load_dotenv()

# Setup logging
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

app = Flask(__name__)
CORS(app)

# Initialize mem0
logger.info("Initializing mem0...")
config = {
    "llm": {
        "provider": "openai",
        "config": {
            "model": "gpt-4o-mini",
            "api_key": os.getenv("OPENAI_API_KEY")
        }
    },
    "embedder": {
        "provider": "openai",
        "config": {
            "model": "text-embedding-3-small",
            "api_key": os.getenv("OPENAI_API_KEY")
        }
    }
}

try:
    m = Memory.from_config(config)
    logger.info("mem0 initialized successfully")
except Exception as e:
    logger.error(f"Failed to initialize mem0: {e}")
    m = None

@app.route('/health', methods=['GET'])
def health():
    return jsonify({'status': 'ok', 'mem0_ready': m is not None})

@app.route('/sync', methods=['POST'])
def sync():
    logger.info("Received sync request")
    try:
        if m is None:
            logger.error("mem0 not initialized")
            return jsonify({'success': False, 'error': 'Backend not initialized'}), 500

        data = request.json
        messages = data.get('messages', [])
        user_id = data.get('user_id')
        metadata = data.get('metadata', {})

        logger.info(f"Sync data: {user_id}, {len(messages)} messages")

        if not messages or not user_id:
            return jsonify({'success': False, 'error': 'Missing messages or user_id'}), 400

        # mem0.add() takes a single string (user message), not a list
        # Combine all user messages into one conversation context
        combined_text = "\n".join([msg['content'] for msg in messages if 'content' in msg])

        result = m.add(combined_text, user_id=user_id)
        logger.info(f"Sync successful: {len(messages)} messages stored")

        return jsonify({
            'success': True,
            'count': len(messages),
            'memories_stored': len(result) if isinstance(result, list) else 1
        })
    except Exception as e:
        logger.error(f"Sync error: {e}")
        logger.error(f"Full traceback:\n{traceback.format_exc()}")
        return jsonify({'success': False, 'error': str(e)}), 500

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

        user_id = f"{platform}_user"
        logger.info(f"Fetching memories for {user_id}")

        # Get all memories for this user
        results = m.get_all(user_id=user_id)

        # Handle response format
        memory_list = []
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
        logger.info(f"Load request for platform: {current_platform}")

        if not current_platform:
            return jsonify({'success': False, 'error': 'Missing platform parameter'}), 400

        # Get memories from other platforms
        seven_days_ago = datetime.now(timezone.utc) - timedelta(days=7)

        platforms = ['chatgpt', 'claude', 'gemini']
        if current_platform in platforms:
            platforms.remove(current_platform)

        all_memories = []

        for platform in platforms:
            user_id = f"{platform}_user"

            results = m.get_all(user_id=user_id)
            logger.info(f"Got memories for {platform}: {type(results)}, {results is not None}")

            # Handle both dict with 'results' key or list directly
            memory_list = []
            memory_list = results['results']
            
            logger.info(f"Processing {len(memory_list)} memories for {platform}")

            for r in memory_list:
                # Parse timestamp
                created_str = r.get('created_at', '')
                created = datetime.fromisoformat(created_str.replace('Z', '+00:00'))
                if created > seven_days_ago:
                    all_memories.append({
                        'platform': platform,
                        'memory': r.get('memory', ''),
                        'timestamp': created_str
                    })

        # Format memories
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
    logger.info(f"mem0 status: {'Ready' if m else 'Failed'}")
    logger.info("CORS: Enabled for all origins")
    logger.info("="*50)
    logger.info(f"Test with: curl http://localhost:{PORT}/health")
    logger.info("="*50)

    app.run(host='localhost', port=PORT, debug=True)
