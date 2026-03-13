# Unified-Memory
A brain that holds all memory from all the AI apps that you use

Chrome extension + mem0 backend for syncing memories across ChatGPT, Claude, and Gemini.

## Quick Start

### Backend Setup
```bash
cd backend
python3 -m venv venv
source venv/bin/activate
pip install -r requirements.txt
cp .env.example .env
# Add OPENAI_API_KEY to .env
python app.py
```

### Extension Setup
1. Open Chrome → `chrome://extensions/`
2. Enable "Developer mode"
3. Click "Load unpacked"
4. Select `/extension` folder
5. Visit claude.ai, chatgpt.com, or gemini.google.com
6. Click extension icon → "Sync Memory" or "Load Memories"

## How It Works
- **Sync Memory**: Scrapes your messages → stores in mem0
- **Load Memories**: Gets memories from other platforms → copies to clipboard → paste into chat

See [PRD.md](PRD.md) for full details.
