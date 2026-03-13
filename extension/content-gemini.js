// Content script for gemini.google.com - scrapes user messages

// Listen for sync requests from popup
chrome.runtime.onMessage.addListener((request, sender, sendResponse) => {
  if (request.action === 'sync') {
    scrapeAndSync(sendResponse);
    return true;
  }
});

// Scrape user messages from Gemini interface
async function scrapeAndSync(sendResponse) {
  try {
    const messages = scrapeUserMessages();
    
    if (messages.length === 0) {
      sendResponse({ 
        success: false, 
        error: 'No messages found. Start a conversation first.' 
      });
      return;
    }
    
    const response = await chrome.runtime.sendMessage({
      action: 'syncToBackend',
      data: {
        messages: messages,
        platform: 'gemini'
      }
    });
    
    sendResponse(response);
  } catch (error) {
    console.error('Scrape error:', error);
    sendResponse({ 
      success: false, 
      error: error.message 
    });
  }
}

// Extract user messages from DOM
function scrapeUserMessages() {
  const messages = [];
  
  // Gemini-specific selectors
  const selectors = [
    '.user-message',
    '[data-test-id="user-message"]',
    '[class*="UserMessage"]',
    'message-content.user-query'
  ];
  
  let messageElements = [];
  
  for (const selector of selectors) {
    messageElements = document.querySelectorAll(selector);
    if (messageElements.length > 0) break;
  }
  
  // Fallback for Gemini's structure
  if (messageElements.length === 0) {
    const allMessages = document.querySelectorAll('[class*="message"], [class*="query"]');
    messageElements = Array.from(allMessages).filter(el => {
      return !el.querySelector('[class*="model-response"]') && 
             !el.querySelector('[class*="assistant"]');
    });
  }
  
  messageElements.forEach(el => {
    const text = extractText(el);
    if (text && text.length > 0 && !isSystemMessage(text)) {
      messages.push({
        role: 'user',
        content: text
      });
    }
  });
  
  // Remove duplicates
  const uniqueMessages = Array.from(
    new Map(messages.map(m => [m.content, m])).values()
  );
  
  return uniqueMessages;
}

// Extract clean text from element
function extractText(element) {
  const clone = element.cloneNode(true);
  clone.querySelectorAll('button, svg, .copy-button').forEach(el => el.remove());
  return clone.textContent?.trim() || '';
}

// Check if text looks like a system message
function isSystemMessage(text) {
  const systemPatterns = [
    /^(Gemini|Bard):/i,
    /^New chat/i,
    /^Continue/i
  ];
  return systemPatterns.some(pattern => pattern.test(text));
}
