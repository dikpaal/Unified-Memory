from flask import Flask, request, jsonify
from flask_cors import CORS
from mem0 import Memory
from datetime import datetime, timedelta
import os
from dotenv import load_dotenv

load_dotenv()

app = Flask(__name__)
CORS(app)

# Initialize mem0
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

m = Memory.from_config(config)

@app.route('/sync', methods=['POST'])
def sync():
    try:
        data = request.json
        messages = data.get('messages', [])
        user_id = data.get('user_id')
        metadata = data.get('metadata', {})

        if not messages or not user_id:
            return jsonify({'success': False, 'error': 'Missing messages or user_id'}), 400

        # Add messages to mem0
        result = m.add(messages, user_id=user_id, metadata=metadata)

        return jsonify({
            'success': True,
            'count': len(messages),
            'memories_stored': len(result) if isinstance(result, list) else 1
        })
    except Exception as e:
        return jsonify({'success': False, 'error': str(e)}), 500

@app.route('/load', methods=['GET'])
def load():
    try:
        current_platform = request.args.get('platform')

        if not current_platform:
            return jsonify({'success': False, 'error': 'Missing platform parameter'}), 400

        # Get memories from other platforms
        seven_days_ago = datetime.now() - timedelta(days=7)

        platforms = ['chatgpt', 'claude', 'gemini']
        if current_platform in platforms:
            platforms.remove(current_platform)

        all_memories = []

        for platform in platforms:
            user_id = f"{platform}_user"
            try:
                # Search with empty query to get all memories
                results = m.search("", user_id=user_id)

                if results and 'results' in results:
                    for r in results['results']:
                        # Parse timestamp
                        created_str = r.get('created_at', '')
                        try:
                            created = datetime.fromisoformat(created_str.replace('Z', '+00:00'))
                            if created > seven_days_ago:
                                all_memories.append({
                                    'platform': platform,
                                    'memory': r.get('memory', ''),
                                    'timestamp': created_str
                                })
                        except:
                            # If timestamp parsing fails, include anyway
                            all_memories.append({
                                'platform': platform,
                                'memory': r.get('memory', ''),
                                'timestamp': created_str
                            })
            except Exception as e:
                # Continue if one platform fails
                print(f"Error loading from {platform}: {e}")
                continue

        # Format memories
        formatted = format_memories(all_memories)

        return jsonify({
            'formatted_text': formatted,
            'memory_count': len(all_memories)
        })
    except Exception as e:
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
    print("Starting Unified Memory backend on http://localhost:5000")
    print("Make sure OPENAI_API_KEY is set in .env file")
    app.run(host='localhost', port=5000, debug=True)
