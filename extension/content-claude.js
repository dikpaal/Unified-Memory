// Content script for claude.ai - scrapes user messages

// Listen for sync requests from popup
chrome.runtime.onMessage.addListener((request, sender, sendResponse) => {
  if (request.action === 'sync') {
    scrapeAndSync(sendResponse);
    return true; // Keep channel open for async response
  }
});

// Scrape user messages from Claude interface
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
    
    // Send to background worker for backend sync
    const response = await chrome.runtime.sendMessage({
      action: 'syncToBackend',
      data: {
        messages: messages,
        platform: 'claude'
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
  
  // Strategy 1: Try common selectors for user messages
  // Claude uses specific data attributes and classes for messages
  const selectors = [
    '[data-is-streaming="false"] [data-test-render-count]',
    '.font-user-message',
    '[class*="UserMessage"]',
    '[data-testid="user-message"]'
  ];
  
  let messageElements = [];
  
  // Try each selector
  for (const selector of selectors) {
    messageElements = document.querySelectorAll(selector);
    if (messageElements.length > 0) break;
  }
  
  // Fallback: Look for conversational pattern
  if (messageElements.length === 0) {
    // Try finding divs with specific text patterns that look like user messages
    const allDivs = document.querySelectorAll('div[class*="message"], div[class*="Message"]');
    messageElements = Array.from(allDivs).filter(div => {
      // Filter for divs that likely contain user messages
      const text = div.textContent?.trim();
      return text && text.length > 0 && !isSystemMessage(text);
    });
  }
  
  // Extract text from elements
  messageElements.forEach(el => {
    const text = extractText(el);
    if (text && text.length > 0) {
      messages.push({
        role: 'user',
        content: text
      });
    }
  });
  
  // Remove duplicates (sometimes multiple selectors match same content)
  const uniqueMessages = Array.from(
    new Map(messages.map(m => [m.content, m])).values()
  );
  
  return uniqueMessages;
}

// Extract clean text from element
function extractText(element) {
  // Clone to avoid modifying original
  const clone = element.cloneNode(true);
  
  // Remove code blocks, buttons, and UI elements
  clone.querySelectorAll('button, svg, .copy-button').forEach(el => el.remove());
  
  return clone.textContent?.trim() || '';
}

// Check if text looks like a system message
function isSystemMessage(text) {
  const systemPatterns = [
    /^(Claude|Assistant):/i,
    /^New conversation/i,
    /^Continue/i,
    /^Regenerate/i
  ];
  
  return systemPatterns.some(pattern => pattern.test(text));
}
