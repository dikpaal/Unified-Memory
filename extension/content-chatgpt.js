// Content script for chatgpt.com - scrapes user messages

// Listen for sync requests from popup
chrome.runtime.onMessage.addListener((request, sender, sendResponse) => {
  if (request.action === 'sync') {
    scrapeAndSync(sendResponse);
    return true;
  }
});

// Scrape user messages from ChatGPT interface
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
        platform: 'chatgpt'
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
  
  // ChatGPT-specific selectors
  const selectors = [
    '[data-message-author-role="user"]',
    '.text-base.whitespace-pre-wrap',
    '[class*="user-message"]',
    '.group.w-full.text-token-text-primary'
  ];
  
  let messageElements = [];
  
  for (const selector of selectors) {
    messageElements = document.querySelectorAll(selector);
    if (messageElements.length > 0) break;
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
    /^(ChatGPT|Assistant):/i,
    /^New chat/i,
    /^Continue/i
  ];
  return systemPatterns.some(pattern => pattern.test(text));
}
