// Popup UI controller
const syncBtn = document.getElementById('sync-btn');
const loadBtn = document.getElementById('load-btn');
const viewBtn = document.getElementById('view-btn');
const summarizeBtn = document.getElementById('summarize-btn');
const statusEl = document.getElementById('status');
const statusText = document.getElementById('status-text');
const platformEl = document.getElementById('platform');
const lastSyncEl = document.getElementById('last-sync');
const memoryCountEl = document.getElementById('memory-count');
const memoriesPanel = document.getElementById('memories-panel');
const memoriesList = document.getElementById('memories-list');
const closeMemoriesBtn = document.getElementById('close-memories');

// Platform detection
const platformMap = {
  'claude.ai': 'claude',
  'chatgpt.com': 'chatgpt'
};

const platformDisplayNames = {
  'claude': 'Claude',
  'chatgpt': 'ChatGPT'
};

// Initialize popup
async function init() {
  const [tab] = await chrome.tabs.query({ active: true, currentWindow: true });
  const url = new URL(tab.url);
  const hostname = url.hostname;
  
  // Detect platform
  const platformKey = Object.keys(platformMap).find(key => hostname.includes(key));
  if (platformKey) {
    const platform = platformMap[platformKey];
    platformEl.textContent = platformDisplayNames[platform];
    platformEl.dataset.platform = platform;  // Store normalized name
  } else {
    platformEl.textContent = 'Unknown';
    syncBtn.disabled = true;
    loadBtn.disabled = true;
    summarizeBtn.disabled = true;
    setStatus('Navigate to Claude or ChatGPT', 'error');
    return;
  }
  
  // Load stored data
  loadStoredData(platform);
}

// Load stored sync data
async function loadStoredData(platform) {
  const result = await chrome.storage.local.get(['lastSync', 'memoryCount']);
  
  if (result.lastSync && result.lastSync[platform]) {
    const syncTime = new Date(result.lastSync[platform]);
    lastSyncEl.textContent = formatTime(syncTime);
  }
  
  if (result.memoryCount && result.memoryCount[platform]) {
    memoryCountEl.textContent = result.memoryCount[platform];
  }
}

// Format timestamp
function formatTime(date) {
  const now = new Date();
  const diff = now - date;
  const minutes = Math.floor(diff / 60000);
  const hours = Math.floor(diff / 3600000);
  const days = Math.floor(diff / 86400000);
  
  if (minutes < 1) return 'Just now';
  if (minutes < 60) return `${minutes}m ago`;
  if (hours < 24) return `${hours}h ago`;
  return `${days}d ago`;
}

// Set status message
function setStatus(message, type = 'default') {
  statusText.textContent = message;
  statusEl.className = `status ${type}`;
}

// Sync memory handler
syncBtn.addEventListener('click', async () => {
  syncBtn.disabled = true;
  loadBtn.disabled = true;
  setStatus('Syncing...', 'loading');

  try {
    const platform = platformEl.dataset.platform;  // Get normalized platform name
    const [tab] = await chrome.tabs.query({ active: true, currentWindow: true });

    // Send message to content script to scrape
    const response = await chrome.tabs.sendMessage(tab.id, { action: 'sync' });

    if (response && response.success) {
      setStatus(`Synced ${response.count} messages`, 'success');

      // Update stored data
      const lastSync = await chrome.storage.local.get('lastSync') || {};
      lastSync.lastSync = lastSync.lastSync || {};
      lastSync.lastSync[platform] = new Date().toISOString();
      await chrome.storage.local.set(lastSync);

      const memoryCount = await chrome.storage.local.get('memoryCount') || {};
      memoryCount.memoryCount = memoryCount.memoryCount || {};
      memoryCount.memoryCount[platform] = response.count;
      await chrome.storage.local.set(memoryCount);

      // Reload display
      loadStoredData(platform);
    } else {
      setStatus(response?.error || 'Sync failed', 'error');
    }
  } catch (error) {
    setStatus(`Error: ${error.message}`, 'error');
  } finally {
    syncBtn.disabled = false;
    loadBtn.disabled = false;
  }
});

// Load memories handler
loadBtn.addEventListener('click', async () => {
  syncBtn.disabled = true;
  loadBtn.disabled = true;
  setStatus('Loading memories...', 'loading');

  try {
    const platform = platformEl.dataset.platform;  // Get normalized platform name

    // Request memories from background worker
    const response = await chrome.runtime.sendMessage({
      action: 'loadMemories',
      platform
    });

    if (response && response.success) {
      // Copy to clipboard
      await navigator.clipboard.writeText(response.formatted);
      setStatus(`Copied ${response.count} memories`, 'success');
    } else {
      setStatus(response?.error || 'Load failed', 'error');
    }
  } catch (error) {
    setStatus(`Error: ${error.message}`, 'error');
  } finally {
    syncBtn.disabled = false;
    loadBtn.disabled = false;
  }
});

// View memories handler
viewBtn.addEventListener('click', async () => {
  try {
    const platform = platformEl.dataset.platform;

    // Fetch memories from backend
    const response = await chrome.runtime.sendMessage({
      action: 'getMemories',
      platform
    });

    if (response && response.success) {
      displayMemories(response.memories);
    } else {
      memoriesList.innerHTML = '<div class="empty-state">Failed to load memories</div>';
      memoriesPanel.classList.remove('hidden');
    }
  } catch (error) {
    console.error('View memories error:', error);
    memoriesList.innerHTML = '<div class="empty-state">Error loading memories</div>';
    memoriesPanel.classList.remove('hidden');
  }
});

// Summarize chat handler
summarizeBtn.addEventListener('click', async () => {
  syncBtn.disabled = true;
  loadBtn.disabled = true;
  summarizeBtn.disabled = true;
  viewBtn.disabled = true;
  setStatus('Extracting messages...', 'loading');

  try {
    const platform = platformEl.dataset.platform;
    const [tab] = await chrome.tabs.query({ active: true, currentWindow: true });

    // Extract messages from content script
    const extractResponse = await chrome.tabs.sendMessage(tab.id, { action: 'extractMessages' });
    console.log('Extract response:', extractResponse);

    if (!extractResponse || !extractResponse.messages || extractResponse.messages.length === 0) {
      setStatus('No messages found', 'error');
      return;
    }

    console.log('Messages extracted:', extractResponse.messages.length);
    setStatus('Generating summary...', 'loading');

    // Request summary from background worker
    const response = await chrome.runtime.sendMessage({
      action: 'summarizeChat',
      messages: extractResponse.messages,
      platform
    });

    console.log('Summarize response:', response);

    if (response && response.success) {
      await navigator.clipboard.writeText(response.summary);
      setStatus('Summary copied to clipboard', 'success');
    } else {
      console.error('Summarize failed:', response);
      setStatus(response?.error || 'Summarization failed', 'error');
    }
  } catch (error) {
    setStatus(`Error: ${error.message}`, 'error');
  } finally {
    syncBtn.disabled = false;
    loadBtn.disabled = false;
    summarizeBtn.disabled = false;
    viewBtn.disabled = false;
  }
});

// Close memories panel
closeMemoriesBtn.addEventListener('click', () => {
  memoriesPanel.classList.add('hidden');
});

// Display memories in panel
function displayMemories(memories) {
  if (!memories || memories.length === 0) {
    memoriesList.innerHTML = '<div class="empty-state">No memories stored yet</div>';
  } else {
    memoriesList.innerHTML = memories.map(m => `
      <div class="memory-item">
        <div class="memory-text">${escapeHtml(m.text)}</div>
        ${m.created ? `<div class="memory-time">${m.created}</div>` : ''}
      </div>
    `).join('');
  }
  memoriesPanel.classList.remove('hidden');
}

// Escape HTML to prevent XSS
function escapeHtml(text) {
  const div = document.createElement('div');
  div.textContent = text;
  return div.innerHTML;
}

// Initialize on load
init();
