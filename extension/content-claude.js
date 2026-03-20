// Content script for claude.ai - scrapes user messages

// Listen for sync requests from popup
chrome.runtime.onMessage.addListener((request, sender, sendResponse) => {
  if (request.action === 'sync') {
    scrapeAndSync(sendResponse);
    return true; // Keep channel open for async response
  }

  if (request.action === 'extractMessages') {
    const messages = scrapeFullConversation();
    sendResponse({ messages });
    return true;
  }
});

// Scrape full conversation from Claude interface
async function scrapeAndSync(sendResponse) {
  try {
    const messages = scrapeFullConversation();

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

// Scrape full conversation (user + assistant messages) in chronological order
function scrapeFullConversation() {
  const messages = [];

  // Find all user messages using data-testid attribute
  const userMessages = document.querySelectorAll('[data-testid="user-message"]');

  // Find all assistant messages using data-is-streaming attribute
  const assistantMessages = document.querySelectorAll('[data-is-streaming="false"]');

  // Collect all messages with their DOM position
  const allMessages = [];

  userMessages.forEach(el => {
    const text = extractText(el);
    if (text && text.length > 10) {
      allMessages.push({
        element: el,
        role: 'user',
        content: text,
        position: getElementPosition(el)
      });
    }
  });

  assistantMessages.forEach(el => {
    // Assistant messages are in a parent div, get the content from .standard-markdown or .progressive-markdown
    const contentDiv = el.querySelector('.standard-markdown, .progressive-markdown');
    if (contentDiv) {
      const text = extractText(contentDiv);
      if (text && text.length > 10 && !isSystemMessage(text)) {
        allMessages.push({
          element: el,
          role: 'assistant',
          content: text,
          position: getElementPosition(el)
        });
      }
    }
  });

  // Sort by DOM position to maintain chronological order
  allMessages.sort((a, b) => a.position - b.position);

  // Remove duplicates based on content
  const seen = new Set();
  const uniqueMessages = [];

  for (const msg of allMessages) {
    if (!seen.has(msg.content)) {
      seen.add(msg.content);
      uniqueMessages.push({
        role: msg.role,
        content: msg.content
      });
    }
  }

  return uniqueMessages;
}

// Helper function to get DOM position of an element
function getElementPosition(element) {
  let position = 0;
  let el = element;

  while (el) {
    if (el.previousSibling) {
      position++;
      el = el.previousSibling;
    } else {
      el = el.parentElement;
      if (el) position += 1000; // Weight parent traversal higher
    }
  }

  return position;
}

// Extract user messages from DOM (kept for backwards compatibility)
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
