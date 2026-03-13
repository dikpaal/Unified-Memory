# Unified-Memory TODO

## Phase 1: Foundation (MVP) - Claude Only

### Backend Setup (COMPLETED)
- [x] Create Python virtual environment
- [x] Install dependencies (mem0ai, flask, flask-cors, python-dotenv)
- [x] Initialize mem0 with config (Qdrant, SQLite, OpenAI)
- [x] Create Flask app structure (localhost:5000)
- [x] Implement POST /sync endpoint (see BACKEND_CONTRACT.md)
- [x] Implement GET /load endpoint (7-day lookback)
- [x] Add CORS for localhost Chrome extension
- [ ] Test mem0 storage with sample data (needs user to run)

### Chrome Extension Scaffold (COMPLETED)
- [x] Create manifest.json (Manifest V3)
- [x] Define permissions (activeTab, clipboardWrite, storage)
- [x] Create popup HTML/CSS (minimalist, SF Mono Light, two colors max)
- [x] Create background service worker
- [x] Set up content script injection for claude.ai

### Claude.ai Scraping (COMPLETED)
- [x] Write content script selector logic with fallbacks
- [x] Extract message text from DOM
- [x] Send scraped data to background worker
- [x] Background worker → POST to backend /sync

### Popup UI - Sync Feature (COMPLETED)
- [x] "Sync Memory" + "Load Memories" buttons
- [x] Click handlers → message to content script / background
- [x] Display sync status (loading, success, error)
- [x] Show last sync timestamp, platform, memory count
- [x] Clipboard API integration for load feature

### Integration Testing (READY TO TEST)
- [x] Create placeholder extension icons (16x16, 48x48, 128x128 PNG)
- [ ] Load extension in Chrome (chrome://extensions/)
- [ ] Test on claude.ai with backend running
- [ ] Test end-to-end sync flow
- [ ] Verify mem0 storage (check SQLite/Qdrant)
- [ ] Test load memories flow + clipboard copy
- [ ] Test error cases (backend down, no messages)

---

## Phase 2: Multi-Platform Scraping

### ChatGPT Support (COMPLETED - NEEDS TESTING)
- [x] Create content script for chatgpt.com
- [x] Add to manifest host permissions
- [ ] Test scraping accuracy with real conversations
- [ ] Refine selectors if needed

### Gemini Support (COMPLETED - NEEDS TESTING)
- [x] Create content script for gemini.google.com
- [x] Add to manifest host permissions
- [ ] Test scraping accuracy with real conversations
- [ ] Refine selectors if needed

### Platform Detection (COMPLETED)
- [x] Popup detects current platform from URL
- [x] Content scripts pass platform identifier to backend
- [ ] Test sync on all three platforms

---

## Phase 3: Memory Loading

### Backend Load Endpoint (USER HANDLES)
- [ ] Implement GET /load?platform=X endpoint (see BACKEND_CONTRACT.md)
- [ ] Query mem0 for memories from other platforms (7-day lookback)
- [ ] Format mem0 results as prompt text (bulleted by platform)
- [ ] Return formatted string + memory count

### Frontend Load Feature (COMPLETED)
- [x] "Load Memories" button in popup
- [x] Click handler → GET /load with current platform
- [x] Use Clipboard API to copy formatted text
- [x] Show success notification with memory count
- [x] Handle no memories case

### Testing (NEEDS BACKEND)
- [ ] Test cross-platform memory loading
- [ ] Verify 7-day filtering works correctly
- [ ] Test clipboard copy on all platforms
- [ ] Test with no memories case

---

## Phase 4: Polish & Reliability

### Error Handling
- [ ] Backend error responses (500, connection refused)
- [ ] Frontend error display in popup
- [ ] Graceful degradation when scraping fails
- [ ] Retry logic for failed syncs

### UX Improvements
- [ ] Show memory count in popup
- [ ] Display last sync time per platform
- [ ] Loading spinners for sync/load actions
- [ ] Success/error toast notifications

### Scraping Reliability
- [ ] Add fallback selectors for each platform
- [ ] Test with different conversation lengths
- [ ] Handle edge cases (empty conversations, special characters)

### Settings
- [ ] Settings page for backend URL configuration
- [ ] Enable/disable per-platform toggle
- [ ] Clear all memories option

---

## Phase 5: Enhancements (Optional)

- [ ] Export memories to JSON
- [ ] Import memories from JSON
- [ ] Memory search UI in extension
- [ ] Configurable formatting templates
- [ ] Firefox extension port
- [ ] TypeScript migration

---

## Current Status

**Phase**: Phase 1 & 2 complete - ready to test
**Completed**:
- Chrome extension scaffold (Manifest V3)
- Popup UI (minimalist, SF Mono Light)
- Background service worker (API integration)
- Content scripts for all 3 platforms (Claude, ChatGPT, Gemini)
- Flask backend with mem0 integration
- Extension icons (16x16, 48x48, 128x128)

**Next Action (User)**:
1. Set up backend:
   - `cd backend && python3 -m venv venv && source venv/bin/activate`
   - `pip install -r requirements.txt`
   - `cp .env.example .env` (add OPENAI_API_KEY)
   - `python app.py`
2. Load extension in Chrome (chrome://extensions/ → Load unpacked)
3. Test sync/load flows on all platforms
