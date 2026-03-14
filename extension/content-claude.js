// Content script for claude.ai - scrapes user messages

// Listen for sync requests from popup
chrome.runtime.onMessage.addListener((request, sender, sendResponse) => {
  if (request.action === 'sync') {
    scrapeAndSync(sendResponse);
    return true; // Keep channel open for async response
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

  // Find all message containers in conversation
  // Claude wraps each message (user or assistant) in its own container
  const conversationSelectors = [
    '.grid.grid-cols-1',  // Main conversation container
    '[role="presentation"]',
    'div[class*="conversation"]'
  ];

  let conversationContainer = null;
  for (const selector of conversationSelectors) {
    conversationContainer = document.querySelector(selector);
    if (conversationContainer) break;
  }

  if (!conversationContainer) {
    // Fallback: get document body
    conversationContainer = document.body;
  }

  // Find all message elements (both user and assistant)
  const allMessageElements = conversationContainer.querySelectorAll('div');

  // Process each element to determine if it's a message and its role
  const messageData = [];

  allMessageElements.forEach((el, index) => {
    const text = extractText(el);

    // Skip if empty or too short
    if (!text || text.length < 3) return;

    // Skip system messages
    if (isSystemMessage(text)) return;

    // Determine role based on selectors/classes
    let role = null;

    // Check for user message indicators
    const userIndicators = [
      'font-user-message',
      'UserMessage',
      'user-message',
      'data-test-render-count'
    ];

    const assistantIndicators = [
      'font-claude-message',
      'AssistantMessage',
      'assistant-message',
      'model-response'
    ];

    // Check classes and attributes
    const elClasses = el.className || '';
    const elDataAttrs = Array.from(el.attributes || []).map(a => a.name).join(' ');
    const combined = elClasses + ' ' + elDataAttrs;

    if (userIndicators.some(ind => combined.includes(ind))) {
      role = 'user';
    } else if (assistantIndicators.some(ind => combined.includes(ind))) {
      role = 'assistant';
    }

    // Additional heuristic: check parent/child structure
    if (!role) {
      // User messages often have specific parent structures
      const parent = el.parentElement;
      if (parent) {
        const parentClass = parent.className || '';
        if (parentClass.includes('user') || parentClass.includes('User')) {
          role = 'user';
        } else if (parentClass.includes('claude') || parentClass.includes('assistant') || parentClass.includes('Assistant')) {
          role = 'assistant';
        }
      }
    }

    // If we found a role, add to messages
    if (role && text.length > 10) {  // Min 10 chars to avoid UI fragments
      messageData.push({
        index: index,  // Preserve DOM order
        role: role,
        content: text
      });
    }
  });

  // Sort by DOM order (index) to maintain chronological order
  messageData.sort((a, b) => a.index - b.index);

  // Remove duplicates based on content
  const seen = new Set();
  const uniqueMessages = [];

  for (const msg of messageData) {
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
