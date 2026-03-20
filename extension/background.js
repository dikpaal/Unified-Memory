// Background service worker - handles API communication with backend

const BACKEND_URL = 'http://localhost:5001';  // Changed from 5000 (macOS uses 5000 for AirPlay)

// Listen for messages from popup and content scripts
chrome.runtime.onMessage.addListener((request, sender, sendResponse) => {
  if (request.action === 'syncToBackend') {
    handleSyncToBackend(request.data, sendResponse);
    return true; // Keep channel open for async response
  }

  if (request.action === 'loadMemories') {
    handleLoadMemories(request.platform, sendResponse);
    return true; // Keep channel open for async response
  }

  if (request.action === 'getMemories') {
    handleGetMemories(request.platform, sendResponse);
    return true; // Keep channel open for async response
  }

  if (request.action === 'summarizeChat') {
    handleSummarizeChat(request, sendResponse);
    return true; // Keep channel open for async response
  }
});

// Handle sync request - send scraped messages to backend
async function handleSyncToBackend(data, sendResponse) {
  try {
    const response = await fetch(`${BACKEND_URL}/sync`, {
      method: 'POST',
      headers: {
        'Content-Type': 'application/json',
      },
      body: JSON.stringify({
        messages: data.messages,
        user_id: `${data.platform}_user`,
        metadata: {
          platform: data.platform,
          synced_at: new Date().toISOString()
        }
      })
    });
    
    if (!response.ok) {
      throw new Error(`Backend returned ${response.status}`);
    }
    
    const result = await response.json();
    
    sendResponse({ 
      success: true, 
      count: data.messages.length,
      result 
    });
  } catch (error) {
    console.error('Sync error:', error);
    sendResponse({ 
      success: false, 
      error: `Backend error: ${error.message}` 
    });
  }
}

// Handle load memories request - fetch from backend
async function handleLoadMemories(platform, sendResponse) {
  try {
    const response = await fetch(`${BACKEND_URL}/load?platform=${platform}`, {
      method: 'GET',
      headers: {
        'Content-Type': 'application/json',
      }
    });

    if (!response.ok) {
      throw new Error(`Backend returned ${response.status}`);
    }

    const result = await response.json();

    sendResponse({
      success: true,
      formatted: result.formatted_text,
      count: result.memory_count
    });
  } catch (error) {
    console.error('Load error:', error);
    sendResponse({
      success: false,
      error: `Backend error: ${error.message}`
    });
  }
}

// Handle get memories request - fetch current platform's memories
async function handleGetMemories(platform, sendResponse) {
  try {
    const response = await fetch(`${BACKEND_URL}/memories?platform=${platform}`, {
      method: 'GET',
      headers: {
        'Content-Type': 'application/json',
      }
    });

    if (!response.ok) {
      throw new Error(`Backend returned ${response.status}`);
    }

    const result = await response.json();

    sendResponse({
      success: true,
      memories: result.memories
    });
  } catch (error) {
    console.error('Get memories error:', error);
    sendResponse({
      success: false,
      error: `Backend error: ${error.message}`
    });
  }
}

// Handle summarize chat request
async function handleSummarizeChat(request, sendResponse) {
  console.log('handleSummarizeChat called with:', request);
  console.log('Messages count:', request.messages?.length);

  try {
    const requestBody = {
      messages: request.messages,
      metadata: {
        platform: request.platform,
        timestamp: new Date().toISOString()
      }
    };

    console.log('Sending to backend:', BACKEND_URL + '/summarize_chat');
    console.log('Request body:', JSON.stringify(requestBody).substring(0, 500));

    const response = await fetch(`${BACKEND_URL}/summarize_chat`, {
      method: 'POST',
      headers: {
        'Content-Type': 'application/json',
      },
      body: JSON.stringify(requestBody)
    });

    console.log('Backend response status:', response.status);

    if (!response.ok) {
      const errorText = await response.text();
      console.error('Backend error response:', errorText);
      throw new Error(`Backend returned ${response.status}: ${errorText}`);
    }

    const result = await response.json();
    console.log('Backend result:', result);

    sendResponse({
      success: true,
      summary: result.summary
    });
  } catch (error) {
    console.error('Summarize error:', error);
    sendResponse({
      success: false,
      error: `Backend error: ${error.message}`
    });
  }
}
