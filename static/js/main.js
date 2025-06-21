let isTyping = false;

// Initialize
document.addEventListener("DOMContentLoaded", function () {
  const messageInput = document.getElementById("messageInput");
  messageInput.addEventListener("keypress", function (e) {
    if (e.key === "Enter" && !e.shiftKey) {
      e.preventDefault();
      sendMessage();
    }
  });

  // Load conversation count
  updateConversationCount();
});

async function sendMessage() {
  const messageInput = document.getElementById("messageInput");
  const message = messageInput.value.trim();

  if (!message || isTyping) return;

  // Add user message to chat
  addMessage(message, "user");
  messageInput.value = "";

  // Show typing indicator
  showTyping();

  try {
    const response = await fetch("/ask", {
      method: "POST",
      headers: {
        "Content-Type": "application/json",
      },
      body: JSON.stringify({ message: message }),
    });

    const data = await response.json();

    if (response.ok) {
      addMessage(data.response, "assistant");
      updateConversationCount(data.conversation_count);
      updateStatus("Response received");
    } else {
      throw new Error(data.error || "Failed to get response");
    }
  } catch (error) {
    console.error("Error:", error);
    addMessage(
      "Sorry, I encountered an error. Please try again.",
      "assistant",
      true
    );
    updateStatus("Error occurred", true);
  } finally {
    hideTyping();
  }
}

function addMessage(content, sender, isError = false) {
  const chatMessages = document.getElementById("chatMessages");
  const noMessages = chatMessages.querySelector(".no-messages");

  if (noMessages) {
    noMessages.remove();
  }

  const messageDiv = document.createElement("div");
  messageDiv.className = `message ${sender}`;

  const avatar =
    sender === "user"
      ? '<div class="message-avatar user-avatar">👤</div>'
      : '<div class="message-avatar assistant-avatar">🤖</div>';

  const messageContent = `
                <div class="message-content ${isError ? "error-message" : ""}">
                    ${content}
                </div>
            `;

  if (sender === "user") {
    messageDiv.innerHTML = messageContent + avatar;
  } else {
    messageDiv.innerHTML = avatar + messageContent;
  }

  chatMessages.appendChild(messageDiv);
  chatMessages.scrollTop = chatMessages.scrollHeight;
}

function showTyping() {
  isTyping = true;
  const typingIndicator = document.getElementById("typingIndicator");
  const sendBtn = document.getElementById("sendBtn");

  typingIndicator.style.display = "flex";
  sendBtn.disabled = true;
  sendBtn.textContent = "Sending...";

  updateStatus("Getting response...");
}

function hideTyping() {
  isTyping = false;
  const typingIndicator = document.getElementById("typingIndicator");
  const sendBtn = document.getElementById("sendBtn");

  typingIndicator.style.display = "none";
  sendBtn.disabled = false;
  sendBtn.textContent = "Send";
}

async function clearHistory() {
  if (!confirm("Are you sure you want to clear your conversation history?")) {
    return;
  }

  try {
    const response = await fetch("/clear_history", {
      method: "POST",
      headers: {
        "Content-Type": "application/json",
      },
    });

    const data = await response.json();

    if (response.ok) {
      // Clear chat messages
      const chatMessages = document.getElementById("chatMessages");
      chatMessages.innerHTML =
        '<div class="no-messages">Conversation cleared! How can I help you today?</div>';

      // Reset conversation count
      updateConversationCount(0);
      updateStatus("History cleared", false, true);
    } else {
      throw new Error(data.error || "Failed to clear history");
    }
  } catch (error) {
    console.error("Error clearing history:", error);
    updateStatus("Failed to clear history", true);
  }
}

async function showHistory() {
  try {
    const response = await fetch("/get_history");
    const data = await response.json();

    if (response.ok && data.history.length > 0) {
      let historyText = `Conversation History (${data.count} messages):\n\n`;
      data.history.forEach((conv, index) => {
        historyText += `${index + 1}. You: ${conv.user}\n`;
        historyText += `   Assistant: ${conv.assistant.substring(
          0,
          100
        )}...\n\n`;
      });
      alert(historyText);
    } else {
      alert("No conversation history found.");
    }
  } catch (error) {
    console.error("Error getting history:", error);
    alert("Failed to retrieve conversation history.");
  }
}

function updateConversationCount(count) {
  if (count !== undefined) {
    document.getElementById("conversationCount").textContent = count;
  }
}

function updateStatus(message, isError = false, isSuccess = false) {
  const statusText = document.getElementById("statusText");
  statusText.textContent = message;

  if (isError) {
    statusText.style.color = "#d63384";
  } else if (isSuccess) {
    statusText.style.color = "#198754";
  } else {
    statusText.style.color = "#666";
  }

  // Reset status after 3 seconds
  setTimeout(() => {
    statusText.textContent = "Ready to help";
    statusText.style.color = "#666";
  }, 3000);
}
