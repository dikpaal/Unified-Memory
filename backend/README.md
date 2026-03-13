# Backend Setup

Flask API for mem0 memory storage.

## Install

```bash
cd backend
python3 -m venv venv
source venv/bin/activate
pip install -r requirements.txt
```

## Config

```bash
cp .env.example .env
# Add your OpenAI API key to .env
```

## Run

```bash
python app.py
```

Backend runs at http://localhost:5001

## Test

```bash
# Test sync
curl -X POST http://localhost:5001/sync \
  -H "Content-Type: application/json" \
  -d '{
    "messages": [{"role": "user", "content": "Test message"}],
    "user_id": "claude_user",
    "metadata": {"platform": "claude", "synced_at": "2026-03-12T14:30:00Z"}
  }'

# Test load
curl http://localhost:5001/load?platform=claude
```
