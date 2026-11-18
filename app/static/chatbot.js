document.addEventListener("DOMContentLoaded", () => {
  const toggle = document.getElementById("kbChatToggle");
  const panel = document.getElementById("kbChatPanel");
  const close = document.getElementById("kbChatClose");
  const form = document.getElementById("kbChatForm");
  const input = document.getElementById("kbChatInput");
  const messages = document.getElementById("kbChatMessages");
  if (!toggle || !panel || !form) return;

  function showPanel(open) {
    panel.hidden = !open;
    toggle.setAttribute("aria-expanded", String(open));
    if (open) input.focus();
  }
  function addMessage(text, kind) {
    const item = document.createElement("p");
    item.className = kind === "user" ? "kb-user-message" : "kb-bot-message";
    item.textContent = text;
    messages.appendChild(item);
    messages.scrollTop = messages.scrollHeight;
    return item;
  }
  toggle.addEventListener("click", () => showPanel(panel.hidden));
  close.addEventListener("click", () => showPanel(false));
  form.addEventListener("submit", async (event) => {
    event.preventDefault();
    const question = input.value.trim();
    if (!question) return;
    addMessage(question, "user");
    input.value = "";
    const waiting = addMessage("Thinking...", "bot");
    const send = form.querySelector("button");
    send.disabled = true;
    try {
      const response = await fetch("/chatbot/reply", {
        method: "POST",
        headers: { "Content-Type": "application/json" },
        body: JSON.stringify({ message: question })
      });
      const data = await response.json();
      waiting.textContent = data.reply || "Sorry, I could not answer that.";
    } catch (error) {
      waiting.textContent = "I could not connect. Please check that KoraBiz is running and try again.";
    } finally {
      send.disabled = false;
      messages.scrollTop = messages.scrollHeight;
    }
  });
});
