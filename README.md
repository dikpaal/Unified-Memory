# Unified Memory

> Seamlessly continue conversations across ChatGPT and Claude without losing context

Chrome extension + local backend that syncs memories between AI platforms. Your data stays on your machine.

## Features

- **Sync Memory** - Capture conversation context from ChatGPT or Claude
- **Load Memories** - Access memories from other platforms (copied to clipboard)
- **Summarize Chat** - Generate concise summaries of conversations instantly
- **Local-First** - All data stored locally, complete privacy
- **Cross-Platform** - Works on claude.ai and chatgpt.com

## Quick Start

### 1. Backend Setup (Docker)

```bash
docker run -d \
  -e GEMINI_API_KEY=your_api_key_here \
  -p 5001:5001 \
  -v unified-memory-data:/app/data \
  --name unified-memory \
  unified-memory:latest
```

> **Note:** Docker image coming soon. For now, see [manual setup](#manual-setup).

### 2. Extension Setup

1. Open Chrome → `chrome://extensions/`
2. Enable "Developer mode"
3. Click "Load unpacked"
4. Select the `/extension` folder from this repo
5. Visit claude.ai or chatgpt.com
6. Click extension icon to start using

## How It Works

1. **Sync Memory** - Scrapes your conversation → extracts semantic memories → stores locally
2. **Load Memories** - Queries memories from other platforms → copies formatted text to clipboard → paste into new chat
3. **Summarize Chat** - Generates concise summary of current conversation → copies to clipboard

**Example Flow:**
- Talk to Claude about project planning → Sync Memory
- Switch to ChatGPT → Load Memories → Paste
- ChatGPT now has context from Claude conversation
- Continue conversation seamlessly across platforms

## Manual Setup

<details>
<summary>Click to expand manual setup instructions</summary>

### Backend
```bash
cd backend
python3 -m venv venv
source venv/bin/activate
pip install -r requirements.txt
cp .env.example .env
# Add your GEMINI_API_KEY to .env
python app.py
```

Backend runs on `localhost:5001`

### Extension
Same as Quick Start steps 1-6 above

</details>

## Requirements

- **Chrome Browser** (Manifest V3 extension)
- **Gemini API Key** (free tier works - get one at [ai.google.dev](https://ai.google.dev))
- **Docker** (recommended) or Python 3.10+

## Architecture

- **Frontend:** Chrome extension (content scripts for DOM scraping, background worker for API calls)
- **Backend:** Python/Flask REST API with SQLite storage
- **LLM:** Google Gemini (free tier) for memory extraction and summarization

## Privacy

- All data stored locally on your machine
- No cloud sync, no external servers
- Memories never leave your localhost
- Open source - audit the code yourself

## Roadmap

See [ROADMAP.md](ROADMAP.md) for planned features including MCP server support for Claude Desktop/Code integration.

## Contributing

Issues and PRs welcome. See open issues for areas needing help.

## License

MIT
