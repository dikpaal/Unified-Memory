# Session Notes

## 2026-03-12 - Initial Planning Session

### Context
Fresh repository. User wants Chrome extension + self-hosted mem0 backend for syncing memories across ChatGPT, Claude.ai, and Gemini.

### Requirements Gathered
- **Platforms**: claude.ai, chatgpt.com, gemini.google.com
- **Memory Backend**: Self-hosted mem0 (local Qdrant + SQLite)
- **Sync Method**: Manual "Sync Memory" button (not auto-capture)
- **Load Method**: Clipboard approach (not auto-inject)
- **Memory Storage**: mem0 handles extraction using OpenAI API
- **Tech Stack**: Chrome-only, Manifest V3, plain JavaScript

### Key Decisions Made

1. **Clipboard over auto-inject**: Avoids fragility of injecting into React-controlled textboxes across platforms
2. **Manual sync over auto-capture**: Simpler implementation, user controls when to sync
3. **Plain JS over TypeScript**: Faster development for focused scope, can migrate later
4. **Self-hosted mem0**: User runs locally, no cloud costs, full privacy

### Architecture Defined

**Frontend**: Chrome extension (content scripts per platform, background worker, popup UI)
**Backend**: Flask + mem0 API
**Data Flow**:
- Sync: Scrape messages → POST /sync → mem0.add()
- Load: GET /load → mem0.search(filters) → clipboard copy

### Documents Created
- `/Users/dikpaal/Desktop/main/code/projects/Unified-Memory/PRD.md`: Full requirements, architecture, 5-phase plan
- `/Users/dikpaal/Desktop/main/code/projects/Unified-Memory/TODO.md`: Phase-by-phase task breakdown
- `/Users/dikpaal/Desktop/main/code/projects/Unified-Memory/SESSION_NOTES.md`: This file

### Configuration Finalized

All questions answered by user:
1. **Backend**: localhost:5000 (default Flask port)
2. **Memory Formatting**: mem0 handles extraction, backend formats as bulleted list by platform
3. **UI Design**: Minimalist, SF Mono Light font, max two colors, no icons
4. **Lookback Period**: 7 days (rolling window)
5. **OpenAI API Key**: User has key available

### mem0 Integration Details

Reviewed mem0 documentation:
- **Install**: `pip install mem0ai` (Python 3.10+)
- **Dependencies**: Qdrant (local at `/tmp/qdrant`), SQLite (`~/.mem0/history.db`)
- **API**: `Memory.add(messages, user_id)` for storing, `Memory.search(query, filters)` for retrieval
- **Output Format**: Returns JSON with memory text, timestamps, categories, relevance scores

Extension sends raw user messages → mem0 extracts semantic facts → backend formats for clipboard.

### Project State - END OF SESSION
- **Phase**: Phase 1 frontend COMPLETE
- **Completed**: Full Chrome extension (all 3 platforms)
- **Blockers**: Awaiting user's backend implementation
- **Git**: Uncommitted changes (extension code ready)

---

## 2026-03-12 - Phase 1 Implementation Session

### Work Completed

**Chrome Extension Built** (`/extension` directory):
- `manifest.json`: Manifest V3 config with permissions for all 3 platforms
- `popup.html/css/js`: Minimalist UI (SF Mono Light, dark theme with #1a1a1a bg, #e0e0e0 text)
- `background.js`: Service worker handling API calls to localhost:5000
- `content-claude.js`: Claude.ai scraper with multiple selector fallbacks
- `content-chatgpt.js`: ChatGPT scraper
- `content-gemini.js`: Gemini scraper

**Features Implemented**:
1. **Sync Memory**: Scrapes user messages → POST to /sync → stores in mem0
2. **Load Memories**: GET from /load → copies formatted text to clipboard
3. **UI Status**: Shows platform, last sync time, memory count
4. **Error Handling**: Displays backend errors, handles no messages case

**Documentation Created**:
- `BACKEND_CONTRACT.md`: Full API spec with Python examples
- `extension/README.md`: Installation, usage, troubleshooting, architecture

**Scraping Strategy**:
- Multiple selector fallbacks per platform
- Deduplication of scraped messages
- System message filtering
- Clean text extraction (removes buttons, SVGs)

### Backend Handoff

User needs to implement Flask backend with:
1. **POST /sync**: Accept messages array, call `mem0.add()`, return success
2. **GET /load?platform=X**: Query mem0 (7-day, other platforms only), format as text, return
3. **CORS enabled** for localhost extension
4. **Port**: localhost:5000

Full specification in `BACKEND_CONTRACT.md` with code examples.

### Next Steps for User

1. Build Flask backend per BACKEND_CONTRACT.md
2. Create placeholder icons (`extension/icons/icon16.png`, icon48.png, icon128.png)
3. Load extension: Chrome → chrome://extensions/ → Load unpacked → select `/extension`
4. Test on claude.ai, chatgpt.com, gemini.google.com

### Testing Plan

Once backend running:
1. Visit claude.ai, have conversation
2. Click extension → "Sync Memory"
3. Verify mem0 storage (check ~/.mem0/history.db or Qdrant)
4. Visit chatgpt.com, have different conversation
5. Sync on ChatGPT
6. Return to claude.ai → "Load Memories" → paste → verify ChatGPT memories appear
7. Test error cases (backend down, empty conversation)

### Known Limitations

- Scraping selectors may break if platforms update UI (fallbacks help but not foolproof)
- Icons needed (manifest references but files don't exist yet)
- No settings UI yet (backend URL hardcoded to localhost:5000)

### Notes for Next Session
- Phase 1 frontend 100% complete
- Phase 2 frontend also mostly done (all 3 content scripts exist)
- Backend is blocking factor for testing
- Once backend works, move to Phase 4 (polish/reliability)

---

## 2026-03-12 - Backend Implementation Session

### Work Completed

**Backend Built** (`/backend` directory):
- `app.py`: Flask API with mem0 integration
  - POST /sync: Accepts messages, stores in mem0
  - GET /load: Returns formatted memories (7-day, cross-platform)
  - CORS enabled for localhost extension
- `requirements.txt`: Dependencies (flask, flask-cors, mem0ai, python-dotenv)
- `.env.example`: OpenAI API key template
- `README.md`: Setup and testing instructions
- `.gitignore`: Python-specific ignores

**Extension Icons**:
- Created SVG brain icon (minimalist design)
- Generated PNG icons at 16x16, 48x48, 128x128
- Used ImageMagick for conversion

**Documentation Updates**:
- Updated main README.md with Quick Start section
- Updated TODO.md status (backend complete, ready to test)
- Updated .gitignore files

### Implementation Details

**Backend Architecture**:
- mem0 configured with OpenAI (gpt-4o-mini for LLM, text-embedding-3-small for embeddings)
- Platform-specific user IDs (claude_user, chatgpt_user, gemini_user)
- 7-day lookback filter for cross-platform memory retrieval
- Formatted output grouped by platform with timestamps

**Error Handling**:
- Try/catch on all endpoints
- Graceful platform failure (continues if one platform errors)
- Timestamp parsing fallback

### Ready for Testing

All Phase 1 & 2 components complete:
1. Chrome extension (frontend)
2. Flask backend (API)
3. Icons (all sizes)
4. Documentation (setup guides)

**User Next Steps**:
1. Install backend dependencies (`pip install -r requirements.txt`)
2. Configure .env with OPENAI_API_KEY
3. Run backend (`python app.py`)
4. Load extension in Chrome
5. Test on claude.ai, chatgpt.com, gemini.google.com

### Known Considerations

- Backend uses gpt-4o-mini instead of gpt-4.1-nano (model availability)
- Icons are minimal placeholders (can improve in Phase 4)
- Selectors may need adjustment based on actual platform UI testing
