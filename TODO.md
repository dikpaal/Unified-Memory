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

### Integration Testing (IN PROGRESS)
- [x] Create placeholder extension icons (16x16, 48x48, 128x128 PNG)
- [x] Load extension in Chrome (chrome://extensions/)
- [x] Fix port conflict (5000 → 5001)
- [x] Fix platform name normalization
- [x] Fix mem0 empty search issue
- [x] Test load memories flow (works with no memories)
- [ ] Test sync flow with real conversations
- [ ] Test cross-platform memory loading
- [ ] Verify mem0 storage (check SQLite/Qdrant)
- [ ] Test both platforms (claude, chatgpt)

---

## Phase 2: Multi-Platform Scraping

### ChatGPT Support (COMPLETED - NEEDS TESTING)
- [x] Create content script for chatgpt.com
- [x] Add to manifest host permissions
- [ ] Test scraping accuracy with real conversations
- [ ] Refine selectors if needed

### Platform Detection (COMPLETED)
- [x] Popup detects current platform from URL
- [x] Content scripts pass platform identifier to backend
- [ ] Test sync on both platforms

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

**Phase**: Phase 1 & 2 complete - debugging done, production testing next

**Completed**:
- Chrome extension scaffold (Manifest V3)
- Popup UI (minimalist, SF Mono Light)
- Background service worker (API integration)
- Content scripts for both platforms (Claude, ChatGPT)
- Flask backend with mem0 integration (port 5001)
- Extension icons (16x16, 48x48, 128x128)
- Logging and health check endpoint
- Platform name normalization
- mem0 search fixes

**Tested & Working**:
- Backend starts on localhost:5001
- Extension → Backend communication
- Load Memories (returns empty when no memories)
- Platform detection
- Error handling

**Next Testing**:
1. Sync Memory on both platforms with real conversations
2. Verify mem0 storage works
3. Test cross-platform memory loading
4. Edge cases (network errors, malformed data)

**To Run**:
```bash
# Backend
cd backend && source venv/bin/activate && python app.py

# Extension
chrome://extensions/ → reload Unified Memory
```
