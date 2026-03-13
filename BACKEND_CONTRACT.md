# Backend API Contract

Extension expects Flask backend at `http://localhost:5000` with following endpoints.

## POST /sync

Store user messages in mem0.

**Request**:
```json
{
  "messages": [
    {"role": "user", "content": "Hi, I'm Alex. I love basketball."},
    {"role": "user", "content": "I'm allergic to peanuts."}
  ],
  "user_id": "claude_user",
  "metadata": {
    "platform": "claude",
    "synced_at": "2026-03-12T14:30:00Z"
  }
}
```

**Response**:
```json
{
  "success": true,
  "count": 2,
  "memories_stored": 2
}
```

**Implementation Hint**:
```python
from mem0 import Memory

m = Memory()  # Initialize with OpenAI config

@app.route('/sync', methods=['POST'])
def sync():
    data = request.json
    result = m.add(data['messages'], user_id=data['user_id'])
    return jsonify({'success': True, 'count': len(data['messages'])})
```

## GET /load?platform={platform}

Retrieve memories from other platforms (7-day lookback).

**Request**: 
```
GET /load?platform=claude
```

**Response**:
```json
{
  "formatted_text": "Update your memory with these facts from other platforms:\n\nFrom ChatGPT (2026-03-12 14:00):\n- Name is Alex. Enjoys basketball and gaming.\n- User is allergic to peanuts.\n\nFrom Gemini (2026-03-12 13:30):\n- User prefers high-protein diet plan.",
  "memory_count": 2
}
```

**Implementation Hint**:
```python
from datetime import datetime, timedelta

@app.route('/load', methods=['GET'])
def load():
    current_platform = request.args.get('platform')
    
    # Query mem0 for other platforms (7-day lookback)
    seven_days_ago = datetime.now() - timedelta(days=7)
    
    # Search across chatgpt_user, claude_user, gemini_user
    # Exclude current_platform
    other_platforms = ['chatgpt', 'claude', 'gemini']
    other_platforms.remove(current_platform)
    
    all_memories = []
    for platform in other_platforms:
        user_id = f"{platform}_user"
        results = m.search("", user_id=user_id)
        
        # Filter by timestamp (7 days)
        for r in results:
            created = datetime.fromisoformat(r['created_at'])
            if created > seven_days_ago:
                all_memories.append({
                    'platform': platform,
                    'memory': r['memory'],
                    'timestamp': r['created_at']
                })
    
    # Format for clipboard
    formatted = format_memories(all_memories)
    
    return jsonify({
        'formatted_text': formatted,
        'memory_count': len(all_memories)
    })

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
        latest_time = items[0]['timestamp'][:16]  # YYYY-MM-DD HH:MM
        text += f"From {platform} ({latest_time}):\n"
        for item in items:
            text += f"- {item['memory']}\n"
        text += "\n"
    
    return text
```

## CORS Configuration

Must enable CORS for localhost Chrome extension:

```python
from flask_cors import CORS

app = Flask(__name__)
CORS(app)  # Enable for all origins (dev mode)
```

## mem0 Configuration

Initialize with OpenAI API key:

```python
from mem0 import Memory
import os

config = {
    "llm": {
        "provider": "openai",
        "config": {
            "model": "gpt-4.1-nano",
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
```

## Error Handling

Return appropriate errors:

```python
@app.errorhandler(500)
def internal_error(error):
    return jsonify({'success': False, 'error': str(error)}), 500

@app.errorhandler(400)
def bad_request(error):
    return jsonify({'success': False, 'error': 'Invalid request'}), 400
```

## Testing

Test with curl:

```bash
# Test sync
curl -X POST http://localhost:5000/sync \
  -H "Content-Type: application/json" \
  -d '{
    "messages": [{"role": "user", "content": "Test message"}],
    "user_id": "claude_user",
    "metadata": {"platform": "claude", "synced_at": "2026-03-12T14:30:00Z"}
  }'

# Test load
curl http://localhost:5000/load?platform=claude
```
