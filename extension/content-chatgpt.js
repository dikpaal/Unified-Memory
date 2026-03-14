// Content script for chatgpt.com - scrapes user messages

// Listen for sync requests from popup
chrome.runtime.onMessage.addListener((request, sender, sendResponse) => {
  if (request.action === 'sync') {
    scrapeAndSync(sendResponse);
    return true;
  }
});

// Scrape full conversation from ChatGPT interface
async function scrapeAndSync(sendResponse) {
  try {
    const messages = scrapeFullConversation();
    console.log(messages)

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

// Scrape full conversation (user + assistant messages) in chronological order
function scrapeFullConversation() {
  const messages = [];

  // ChatGPT conversation is structured with data-message-author-role attributes
  // Find all message containers
  const conversationSelectors = [
    'main',
    '[role="main"]',
    '.flex.flex-col.items-center'
  ];

  let conversationContainer = null;
  for (const selector of conversationSelectors) {
    conversationContainer = document.querySelector(selector);
    if (conversationContainer) break;
  }

  if (!conversationContainer) {
    conversationContainer = document.body;
  }

  // Find all message elements
  // ChatGPT uses data-message-author-role="user" or "assistant"
  const allMessages = conversationContainer.querySelectorAll('[data-message-author-role]');

  if (allMessages.length > 0) {
    // Use the structured approach with data attributes
    allMessages.forEach((el, index) => {
      const role = el.getAttribute('data-message-author-role');

      if (role !== 'user' && role !== 'assistant') return;

      const text = extractText(el);

      if (text && text.length > 10 && !isSystemMessage(text)) {
        messages.push({
          index: index,
          role: role,
          content: text
        });
      }
    });
  } else {
    // Fallback: try finding by class patterns
    const userSelectors = [
      '.text-base.whitespace-pre-wrap',
      '[class*="user-message"]',
      '.group.w-full.text-token-text-primary'
    ];

    const assistantSelectors = [
      '[class*="assistant-message"]',
      '.markdown.prose',
      '.agent-turn'
    ];

    const allDivs = conversationContainer.querySelectorAll('div');

    allDivs.forEach((el, index) => {
      const text = extractText(el);
      if (!text || text.length < 10 || isSystemMessage(text)) return;

      let role = null;
      const elClasses = el.className || '';
      const parent = el.parentElement;
      const parentClasses = parent ? (parent.className || '') : '';

      // Check for user message
      if (userSelectors.some(sel => el.matches(sel)) ||
          elClasses.includes('user') ||
          parentClasses.includes('user')) {
        role = 'user';
      }
      // Check for assistant message
      else if (assistantSelectors.some(sel => el.matches(sel)) ||
               elClasses.includes('assistant') ||
               parentClasses.includes('assistant') ||
               elClasses.includes('markdown')) {
        role = 'assistant';
      }

      if (role) {
        messages.push({
          index: index,
          role: role,
          content: text
        });
      }
    });
  }

  // Sort by index to maintain chronological order
  messages.sort((a, b) => a.index - b.index);

  // Remove duplicates
  const seen = new Set();
  const uniqueMessages = [];

  for (const msg of messages) {
    if (!seen.has(msg.content)) {
      seen.add(msg.content);
      uniqueMessages.push({
        role: msg.role,
        content: msg.content
      });
    }
  }
  console.log(uniqueMessages)
  return uniqueMessages;
}

// Extract assistant messages from DOM (kept for backwards compatibility)
function scrapeAssistantMessages() {

    const messages = []

    const selectors = [
        '[class*="assistant-message"]',
        '[data-message-author-role="assistant"]',
    ]

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
