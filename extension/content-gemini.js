// Content script for gemini.google.com - scrapes user messages

// Listen for sync requests from popup
chrome.runtime.onMessage.addListener((request, sender, sendResponse) => {
  if (request.action === 'sync') {
    scrapeAndSync(sendResponse);
    return true;
  }
});

// Scrape full conversation from Gemini interface
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

// Scrape full conversation (user + assistant messages) in chronological order
function scrapeFullConversation() {
  const messages = [];

  // Gemini has a structured conversation layout
  const conversationSelectors = [
    'chat-window',
    '[role="main"]',
    'main',
    '.conversation-container'
  ];

  let conversationContainer = null;
  for (const selector of conversationSelectors) {
    conversationContainer = document.querySelector(selector);
    if (conversationContainer) break;
  }

  if (!conversationContainer) {
    conversationContainer = document.body;
  }

  // Find message elements
  const allDivs = conversationContainer.querySelectorAll('div');

  const messageData = [];

  allDivs.forEach((el, index) => {
    const text = extractText(el);

    // Skip if empty or too short
    if (!text || text.length < 10) return;

    // Skip system messages
    if (isSystemMessage(text)) return;

    // Determine role based on selectors/classes
    let role = null;

    // User message indicators for Gemini
    const userIndicators = [
      'user-message',
      'user-query',
      'UserMessage',
      'query-text',
      'user-input'
    ];

    // Assistant message indicators for Gemini
    const assistantIndicators = [
      'model-response',
      'assistant-message',
      'gemini-response',
      'model-output',
      'response-text',
      'markdown-render'
    ];

    // Check classes and attributes
    const elClasses = el.className || '';
    const elDataAttrs = Array.from(el.attributes || []).map(a => a.name + '=' + a.value).join(' ');
    const combined = elClasses + ' ' + elDataAttrs;

    if (userIndicators.some(ind => combined.toLowerCase().includes(ind.toLowerCase()))) {
      role = 'user';
    } else if (assistantIndicators.some(ind => combined.toLowerCase().includes(ind.toLowerCase()))) {
      role = 'assistant';
    }

    // Additional heuristic: check parent structure
    if (!role) {
      const parent = el.parentElement;
      if (parent) {
        const parentClass = (parent.className || '').toLowerCase();
        const parentData = Array.from(parent.attributes || []).map(a => a.name + '=' + a.value).join(' ').toLowerCase();
        const parentCombined = parentClass + ' ' + parentData;

        if (userIndicators.some(ind => parentCombined.includes(ind.toLowerCase()))) {
          role = 'user';
        } else if (assistantIndicators.some(ind => parentCombined.includes(ind.toLowerCase()))) {
          role = 'assistant';
        }
      }
    }

    // Fallback: check for specific patterns in the DOM tree
    if (!role) {
      // User messages typically have simpler structure
      // Model responses have markdown/code blocks
      const hasCodeBlock = el.querySelector('pre, code');
      const hasMarkdown = el.querySelector('.markdown, [class*="markdown"]');

      if (hasCodeBlock || hasMarkdown) {
        role = 'assistant';
      }
    }

    // If we found a role, add to messages
    if (role && text.length > 10) {
      messageData.push({
        index: index,
        role: role,
        content: text
      });
    }
  });

  // Sort by DOM order to maintain chronological order
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
