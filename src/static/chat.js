/**
 * Chat Module — AI Chat interface powered by Ollama (Qwen 2.5)
 * 
 * Handles:
 * - Chat state management (history, loading)
 * - SSE streaming from /api/chat endpoint
 * - Message rendering with Markdown support
 * - Suggested prompts, keyboard shortcuts
 * - Auto-growing textarea
 */

// ──────────────────────────────────
// Chat State
// ──────────────────────────────────
const chatHistory = [];
let isChatLoading = false;
let chatInitialized = false;

const API_CHAT = "/api/chat";

// ──────────────────────────────────
// Initialization
// ──────────────────────────────────

/**
 * Initialize chat event listeners.
 * Called once after chat.html is loaded into the DOM.
 */
function initChat() {
  if (chatInitialized) return;
  chatInitialized = true;

  // Send button
  const sendBtn = document.getElementById("chat-send-btn");
  if (sendBtn) {
    sendBtn.addEventListener("click", () => sendChatMessage());
  }

  // Keyboard shortcuts on textarea
  const chatInput = document.getElementById("chat-input");
  if (chatInput) {
    chatInput.addEventListener("keydown", (e) => {
      if (e.key === "Enter" && !e.shiftKey) {
        e.preventDefault();
        sendChatMessage();
      }
    });

    // Auto-grow textarea
    chatInput.addEventListener("input", () => {
      chatInput.style.height = "auto";
      chatInput.style.height = Math.min(chatInput.scrollHeight, 120) + "px";
    });
  }

  // Clear chat button
  const clearBtn = document.getElementById("chat-clear-btn");
  if (clearBtn) {
    clearBtn.addEventListener("click", clearChat);
  }

  // Suggested prompt chips
  const chips = document.querySelectorAll(".chat-suggestion-chip");
  chips.forEach((chip) => {
    chip.addEventListener("click", () => {
      const prompt = chip.getAttribute("data-prompt");
      if (prompt && !isChatLoading) {
        const chatInput = document.getElementById("chat-input");
        if (chatInput) chatInput.value = prompt;
        sendChatMessage();
      }
    });
  });
}

// ──────────────────────────────────
// Send Message
// ──────────────────────────────────

async function sendChatMessage() {
  const chatInput = document.getElementById("chat-input");
  if (!chatInput) return;

  const message = chatInput.value.trim();
  if (!message || isChatLoading) return;

  isChatLoading = true;
  updateSendButton(true);

  // Hide welcome state
  const welcome = document.getElementById("chat-welcome");
  if (welcome) welcome.style.display = "none";

  // Add user message to UI
  appendMessage("user", message);
  chatHistory.push({ role: "user", content: message });

  // Clear input
  chatInput.value = "";
  chatInput.style.height = "auto";

  // Show typing indicator
  const typingEl = showTypingIndicator();

  // Create AI message placeholder
  const aiMessageEl = createAIMessageElement();
  const bubbleEl = aiMessageEl.querySelector(".chat-msg-bubble");

  try {
    const response = await fetch(API_CHAT, {
      method: "POST",
      headers: { "Content-Type": "application/json" },
      body: JSON.stringify({
        message: message,
        history: chatHistory.slice(0, -1) // Exclude current message (already sent in body)
      }),
    });

    // Remove typing indicator
    if (typingEl) typingEl.remove();

    if (!response.ok) {
      const errData = await response.json().catch(() => ({}));
      throw new Error(errData.error || `HTTP ${response.status}`);
    }

    // Append AI message element to chat
    const chatMessages = document.getElementById("chat-messages");
    chatMessages.appendChild(aiMessageEl);

    // Stream SSE response
    let fullResponse = "";
    const reader = response.body.getReader();
    const decoder = new TextDecoder();
    let buffer = "";

    while (true) {
      const { done, value } = await reader.read();
      if (done) break;

      buffer += decoder.decode(value, { stream: true });

      // Process complete SSE events from buffer
      const events = buffer.split("\n\n");
      buffer = events.pop(); // Keep incomplete event in buffer

      for (const event of events) {
        const dataLine = event.trim();
        if (!dataLine.startsWith("data: ")) continue;

        const jsonStr = dataLine.slice(6); // Remove "data: "
        try {
          const data = JSON.parse(jsonStr);

          if (data.error) {
            bubbleEl.innerHTML = `<span class="chat-msg-error">${escapeHtml(data.error)}</span>`;
            bubbleEl.classList.add("chat-msg-error");
            break;
          }

          if (data.token) {
            fullResponse += data.token;
            // Render markdown in real-time
            renderMarkdown(bubbleEl, fullResponse);
            scrollToBottom();
          }

          if (data.done) {
            // Final render
            renderMarkdown(bubbleEl, fullResponse);
          }
        } catch (parseErr) {
          console.warn("SSE parse error:", parseErr);
        }
      }
    }

    // Save AI response to history
    if (fullResponse) {
      chatHistory.push({ role: "assistant", content: fullResponse });
    }

    // Add timestamp
    addTimestamp(aiMessageEl);

  } catch (error) {
    // Remove typing indicator if still present
    if (typingEl && typingEl.parentNode) typingEl.remove();

    // Show error message
    const chatMessages = document.getElementById("chat-messages");
    bubbleEl.innerHTML = escapeHtml(
      `⚠️ Lỗi: ${error.message || "Không thể kết nối đến AI. Hãy chắc chắn Ollama đang chạy."}`
    );
    bubbleEl.classList.add("chat-msg-error");
    chatMessages.appendChild(aiMessageEl);
  }

  isChatLoading = false;
  updateSendButton(false);
  scrollToBottom();
}

// ──────────────────────────────────
// UI Helpers
// ──────────────────────────────────

function appendMessage(role, content) {
  const chatMessages = document.getElementById("chat-messages");
  if (!chatMessages) return;

  const isUser = role === "user";
  const msgDiv = document.createElement("div");
  msgDiv.className = `chat-message chat-message--${isUser ? "user" : "ai"}`;

  const time = new Date().toLocaleTimeString("vi-VN", {
    hour: "2-digit",
    minute: "2-digit",
  });

  msgDiv.innerHTML = `
    <div class="chat-msg-avatar">${isUser ? "👤" : "🤖"}</div>
    <div>
      <div class="chat-msg-bubble">${escapeHtml(content)}</div>
      <span class="chat-msg-timestamp">${time}</span>
    </div>
  `;

  chatMessages.appendChild(msgDiv);
  scrollToBottom();
}

function createAIMessageElement() {
  const msgDiv = document.createElement("div");
  msgDiv.className = "chat-message chat-message--ai";
  msgDiv.innerHTML = `
    <div class="chat-msg-avatar">🤖</div>
    <div>
      <div class="chat-msg-bubble"></div>
    </div>
  `;
  return msgDiv;
}

function addTimestamp(messageEl) {
  const time = new Date().toLocaleTimeString("vi-VN", {
    hour: "2-digit",
    minute: "2-digit",
  });
  const container = messageEl.querySelector(".chat-msg-bubble").parentNode;
  const existing = container.querySelector(".chat-msg-timestamp");
  if (!existing) {
    const ts = document.createElement("span");
    ts.className = "chat-msg-timestamp";
    ts.textContent = time;
    container.appendChild(ts);
  }
}

function showTypingIndicator() {
  const chatMessages = document.getElementById("chat-messages");
  if (!chatMessages) return null;

  const typingDiv = document.createElement("div");
  typingDiv.className = "chat-typing";
  typingDiv.id = "chat-typing-indicator";
  typingDiv.innerHTML = `
    <div class="chat-msg-avatar" style="background: linear-gradient(135deg, rgba(6, 182, 212, 0.15), rgba(16, 185, 129, 0.15)); border: 1px solid rgba(6, 182, 212, 0.15);">🤖</div>
    <div class="chat-typing-dots">
      <span></span><span></span><span></span>
    </div>
  `;

  chatMessages.appendChild(typingDiv);
  scrollToBottom();
  return typingDiv;
}

function clearChat() {
  chatHistory.length = 0;
  const chatMessages = document.getElementById("chat-messages");
  if (chatMessages) {
    chatMessages.innerHTML = "";
    // Restore welcome
    const welcome = document.getElementById("chat-welcome");
    if (welcome) {
      welcome.style.display = "flex";
      chatMessages.appendChild(welcome);
    } else {
      // Rebuild welcome if it was removed
      chatMessages.innerHTML = `
        <div class="chat-welcome" id="chat-welcome">
          <div class="chat-welcome-icon">🧠</div>
          <h3>Xin chào! Tôi là InsightAgent AI</h3>
          <p>Tôi có thể phân tích dữ liệu đánh giá khách hàng của bạn. Hỏi tôi bất kỳ điều gì về reviews, chi nhánh, sentiment, hoặc xu hướng.</p>
        </div>
      `;
    }
  }
}

function updateSendButton(loading) {
  const sendBtn = document.getElementById("chat-send-btn");
  if (sendBtn) {
    sendBtn.disabled = loading;
  }
}

function scrollToBottom() {
  const chatMessages = document.getElementById("chat-messages");
  if (chatMessages) {
    chatMessages.scrollTop = chatMessages.scrollHeight;
  }
}

function renderMarkdown(element, text) {
  // Use marked.js if available, otherwise fallback to basic rendering
  if (typeof marked !== "undefined") {
    element.innerHTML = marked.parse(text);
  } else {
    element.innerHTML = basicMarkdown(text);
  }
}

function basicMarkdown(text) {
  // Minimal fallback markdown renderer
  return text
    .replace(/&/g, "&amp;")
    .replace(/</g, "&lt;")
    .replace(/>/g, "&gt;")
    .replace(/\*\*(.*?)\*\*/g, "<strong>$1</strong>")
    .replace(/\*(.*?)\*/g, "<em>$1</em>")
    .replace(/`(.*?)`/g, '<code>$1</code>')
    .replace(/\n/g, "<br>");
}

function escapeHtml(text) {
  const div = document.createElement("div");
  div.textContent = text;
  return div.innerHTML;
}
