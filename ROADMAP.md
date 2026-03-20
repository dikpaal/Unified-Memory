# Unified Memory Roadmap

## v1.0 - Web Platform Polish (Current Focus)

**Goal:** Production-ready Chrome extension for ChatGPT and Claude web platforms

**Core Deliverables:**
- Caching layer for Gemini API calls (3-5s → <100ms on cache hits)
- Docker image for one-command backend setup
- Polished documentation with screenshots and examples
- Settings UI for backend URL configuration
- Improved error handling and user feedback

**Status:** In Progress

---

## v1.1 - MCP Server Integration

**Goal:** Expand platform support to Claude Desktop, Claude Code, and other MCP clients

**Deliverables:**
- Build MCP server (separate from extension)
- Test with Claude Desktop first (easiest to verify)
- Document MCP setup separately

**Benefits:**
- Same backend, multiple frontends (web extension + MCP)
- Claude Desktop/Code can query memories automatically
- ChatGPT web ↔ Claude Desktop memory sync
- Future-proof for new MCP-compatible tools

**Status:** Planned

---

## v1.2 - Advanced Features

**Goal:** Enhanced user experience and flexibility

**Planned Features:**
- Memory management UI (delete, edit, search)
- Export/import memories (JSON backup/restore)
- Configurable memory retention periods
- Chrome Web Store listing
- First-run setup wizard
- Advanced settings (cache TTL, API model selection)

**Status:** Backlog

---

## v2.0 - Multi-Platform Expansion

**Goal:** Support additional AI platforms

**Potential Targets:**
- Gemini web interface
- Perplexity
- Microsoft Copilot
- Firefox extension support

**Status:** Research Phase

---

## Future Considerations

- Mobile support (iOS/Android extensions)
- Team/shared memory spaces (multi-user)
- End-to-end encryption for synced memories
- Self-hosted web UI for memory browsing
- Plugin system for custom memory extractors
