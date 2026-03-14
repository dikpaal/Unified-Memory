# Unified-Memory: Cross-Platform LLM Memory Sync

## Problem Statement

User leverages ChatGPT and Claude for different tasks, but each platform maintains isolated memory with no cross-awareness. Conversations happening on one platform remain unknown to the other.

## Solution

Chrome extension + local mem0 backend that:
1. Captures user messages from claude.ai and chatgpt.com
2. Stores memories locally with timestamps using mem0
3. Enables loading memories from other platforms into current conversation via clipboard

## Core Workflow

**Sync Memory (after conversation)**:
1. User clicks "Sync Memory" in extension popup
2. Extension scrapes all user messages from current page
3. Sends to local Python backend running mem0
4. Backend extracts semantic memories, stores with timestamp + platform metadata

**Load Memories (starting new conversation)**:
1. User clicks "Load Memories" in extension popup
2. Backend queries mem0 for memories from other platforms since last sync for current platform
3. Formats as: "Update your memory with: [formatted memory list]"
4. **Copies to clipboard automatically**
5. User pastes into textbox, clicks send

**Example**:
- Talk to Claude 11:00-12:00, sync (last sync: 12:00)
- Talk to ChatGPT 14:00-15:00 about diet, sync
- Open Claude, click "Load Memories"
- Paste formatted ChatGPT memories (12:00+) into Claude
- Send, continue diet conversation with Claude now aware

## Technical Architecture

### Frontend: Chrome Extension (Manifest V3)
- **Content Scripts**: One per platform (claude.ai, chatgpt.com)
  - DOM scraping logic for user messages
- **Background Service Worker**: Coordinates communication between content scripts and backend
- **Popup UI**:
  - Design: Minimalist, SF Mono Light font, max two colors
  - Buttons: "Sync Memory" and "Load Memories"
  - Status display: memory count, last sync time

### Backend: Python + mem0
- **Framework**: Flask (lightweight REST API)
- **Port**: localhost:5000 (default)
- **mem0 Setup**: Self-hosted, local Qdrant + SQLite
- **LLM**: OpenAI API (gpt-4.1-nano for extraction, text-embedding-3-small for embeddings)
- **Endpoints**:
  - `POST /sync`: Accepts messages array, platform, timestamp → stores in mem0
  - `GET /load?platform=X`: Returns formatted memories from other platforms (7-day lookback)

### Data Model

**mem0 Input** (what extension sends):
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

**mem0 Output** (what backend returns for /load):
```json
{
  "results": [
    {
      "id": "mem_123abc",
      "memory": "Name is Alex. Enjoys basketball and gaming.",
      "user_id": "chatgpt_user",
      "categories": ["personal_info"],
      "created_at": "2026-03-12T14:00:22Z",
      "score": 0.89
    }
  ]
}
```

**Memory Formatting for Clipboard**:
Backend formats mem0 results into prompt text:
```
Update your memory with these facts from other platforms:

From ChatGPT (2026-03-12 14:00):
- Name is Alex. Enjoys basketball and gaming.
- User is allergic to peanuts.
```

### Tech Stack Decision

**Industry Standard for Chrome Extensions**:

Both plain JS and TypeScript are widely used. Decision factors:

**Plain JavaScript (Recommended for this project)**:
- Faster initial development
- No build step → edit and reload
- Industry standard for small-medium extensions
- Examples: Grammarly, many popular extensions started here

**TypeScript**:
- Industry standard for large/complex extensions
- Type safety prevents bugs
- Better IDE support
- Requires webpack/vite build setup

**Choice: Plain JavaScript with Manifest V3**
- Rationale: Project scope is focused, scraping logic is straightforward, ship faster
- Migration path: Can add TypeScript later if codebase complexity grows
- Manifest V3: Required standard (V2 deprecated)

## Multi-Phase Plan

### Phase 1: Foundation (MVP)
**Goal**: Basic sync working for one platform (Claude)

**Frontend**:
- Chrome extension scaffold (Manifest V3)
- Content script for claude.ai with message scraping
- Popup with "Sync Memory" button
- Basic communication to local backend

**Backend**:
- Flask API with /sync endpoint
- mem0 initialization (Qdrant + SQLite)
- OpenAI API integration
- Store scraped messages with platform/timestamp metadata

**Deliverable**: Can click "Sync Memory" on Claude, see memories stored in mem0

### Phase 2: Multi-Platform Scraping
**Goal**: Sync working across both platforms

**Tasks**:
- Content script for chatgpt.com (different DOM selectors)
- Platform detection in background service worker
- Test sync on both platforms

**Deliverable**: "Sync Memory" works on Claude and ChatGPT

### Phase 3: Memory Loading
**Goal**: Load memories from other platforms via clipboard

**Backend**:
- `GET /load` endpoint with 7-day lookback filtering
- Track last sync per platform (SQLite table)
- Format mem0 results as prompt text for clipboard

**Frontend**:
- "Load Memories" button in popup
- Clipboard API integration
- Success notification with memory count

**Deliverable**: Click "Load Memories" on ChatGPT → copies Claude memories (7-day) to clipboard → paste into ChatGPT

### Phase 4: Polish & Reliability
**Goal**: Production-ready UX

**Tasks**:
- Error handling (backend down, scraping failed, no memories found)
- Popup UI improvements (show memory count, last sync time)
- Selector fallback chains (handle platform UI changes gracefully)
- Settings page (configure backend URL, enable/disable platforms)
- Loading states and user feedback

**Deliverable**: Robust, user-friendly extension

### Phase 5: Enhancements (Optional)
- Export/import memories (backup)
- Memory search within extension
- Configurable memory formatting templates
- Firefox support (different extension API)
- TypeScript migration

## Out of Scope
- Auto-inject (too fragile, maintenance burden)
- Real-time sync (manual trigger sufficient)
- Mobile browsers (desktop Chrome only)
- Custom LLM integration (mem0 handles via OpenAI)

## Dependencies & Prerequisites

**User Provides**:
- Self-hosted mem0 running locally (Python 3.10+)
- OpenAI API key (confirmed available)
- Backend running on localhost:5000

**Developer Provides**:
- Chrome extension (frontend)
- Python Flask backend integrating mem0

## Success Criteria

1. Can sync memories from both platforms (Claude, ChatGPT)
2. Memories stored with timestamps and platform metadata
3. Can load cross-platform memories via clipboard
4. Scraping resilient to minor UI changes (fallback selectors)
5. Clear user feedback on sync/load success/failure

## Risks & Mitigations

**Risk**: Platform UI changes break scraping
**Mitigation**: Multiple selector strategies per platform, easy to update content scripts

**Risk**: mem0 backend goes down
**Mitigation**: Extension shows clear error, queues failed syncs for retry (Phase 4)

**Risk**: Memory extraction quality varies
**Mitigation**: mem0 + OpenAI handle this, can tune prompts if needed

**Risk**: User forgets to sync
**Mitigation**: Add visual indicator in popup showing "X minutes since last sync" (Phase 4)

## Configuration Decisions

1. **Backend**: localhost:5000 (default Flask port)
2. **Memory Formatting**: Handled by mem0 extraction, backend formats as bulleted list by platform
3. **UI Design**: Minimalist, SF Mono Light font, max two colors, no icons
4. **Memory Lookback**: 7 days (7-day rolling window for loaded memories)
5. **OpenAI API Key**: User has key available
