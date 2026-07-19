let aiChatSending = false;

function scrollAiChatToBottom() {
  const transcript = document.querySelector("#ai-chat-messages");
  if (transcript) {
    transcript.scrollTop = transcript.scrollHeight;
  }
}

function resizeAiChatInput(event) {
  const input = event && event.currentTarget
    ? event.currentTarget
    : document.querySelector("#ai-chat-input");
  if (!input) {
    return;
  }
  input.style.height = "auto";
  input.style.height = Math.min(input.scrollHeight, 160) + "px";
}

function appendOptimisticUserMessage(text) {
  const transcript = document.querySelector("#ai-chat-messages");
  const empty = transcript.querySelector(".ai-chat-empty");
  if (empty) {
    empty.remove();
  }

  const bubble = document.createElement("div");
  bubble.className = "ai-chat-bubble ai-chat-bubble-user";
  const body = document.createElement("div");
  body.className = "ai-chat-bubble-body";
  body.textContent = text;
  bubble.appendChild(body);
  transcript.appendChild(bubble);
}

function appendAiChatLoading() {
  const transcript = document.querySelector("#ai-chat-messages");
  const existing = document.querySelector("#ai-chat-loading");
  if (existing) {
    existing.remove();
  }

  const bubble = document.createElement("div");
  bubble.className = "ai-chat-bubble ai-chat-bubble-assistant ai-chat-loading";
  bubble.id = "ai-chat-loading";
  const body = document.createElement("div");
  body.className = "ai-chat-bubble-body ai-chat-typing";
  body.setAttribute("aria-label", "Assistant is typing");
  for (let i = 0; i < 3; i++) {
    const dot = document.createElement("span");
    dot.className = "ai-chat-typing-dot";
    body.appendChild(dot);
  }
  bubble.appendChild(body);
  transcript.appendChild(bubble);
}

function setAiChatSending(isSending) {
  aiChatSending = isSending;
  const sendButton = document.querySelector("#ai-chat-send");
  const input = document.querySelector("#ai-chat-input");
  if (sendButton) {
    sendButton.disabled = isSending;
  }
  if (input) {
    input.readOnly = isSending;
  }
}

function sendAiChatMessage(event) {
  if (aiChatSending) {
    return;
  }

  const trigger = event.currentTarget;
  const form = trigger.closest("form") || document.querySelector("#ai-chat-form");
  const input = form.querySelector('[name="message"]');
  const text = input.value.trim();
  if (!text) {
    return;
  }

  appendOptimisticUserMessage(text);
  appendAiChatLoading();
  scrollAiChatToBottom();

  // FormData skips disabled fields — collect the request before locking the UI.
  const pending = sendWsRequest("ai/send_message", trigger);
  setAiChatSending(true);
  input.value = "";
  resizeAiChatInput({ currentTarget: input });

  pending.then((response) => {
    setAiChatSending(false);
    if (response.json_content?.target && response.json_content?.html) {
      document.querySelector(response.json_content.target).innerHTML =
        response.json_content.html;
    }
    scrollAiChatToBottom();
    input.focus();
  });
}

function aiChatInputKeydown(event) {
  if (event.key !== "Enter" || event.shiftKey) {
    return;
  }
  event.preventDefault();
  const form = event.currentTarget.closest("form");
  const sendButton = form.querySelector("#ai-chat-send");
  sendAiChatMessage({ currentTarget: sendButton });
}
