// =====================================================
// SHARED CHATBOT LOGIC (STREAMING AGENT)
// =====================================================

document.addEventListener("DOMContentLoaded", () => {
    const toggleBtn = document.getElementById("chatbotToggle");
    const chatbotWindow = document.getElementById("chatbotWindow");
    const closeBtn = document.getElementById("chatbotClose");
    const sendBtn = document.getElementById("sendMessage");
    const chatInput = document.getElementById("chatInput");
    const chatMessages = document.getElementById("chatMessages");

    if (!toggleBtn || !chatbotWindow || !closeBtn || !sendBtn || !chatInput || !chatMessages) {
        console.warn("Chatbot elements missing from the page.");
        return;
    }

    // Open / Close
    toggleBtn.onclick = () => chatbotWindow.classList.remove("hidden");
    closeBtn.onclick = () => chatbotWindow.classList.add("hidden");

    // Send chat message
    sendBtn.onclick = async () => {
        const question = chatInput.value.trim();
        if (!question) return;

        chatMessages.innerHTML += `<div class="msg user">${question}</div>`;
        chatInput.value = "";
        chatMessages.scrollTop = chatMessages.scrollHeight;

        // STREAMING MODE
        const botMsgDiv = document.createElement("div");
        botMsgDiv.className = "msg bot";
        botMsgDiv.innerHTML = `<div class="status-msg" style="color: #666; font-style: italic; font-size: 0.85em; margin-bottom: 5px;">Connecting...</div><p class="content"></p>`;
        chatMessages.appendChild(botMsgDiv);
        chatMessages.scrollTop = chatMessages.scrollHeight;

        const statusEl = botMsgDiv.querySelector(".status-msg");
        const contentEl = botMsgDiv.querySelector(".content");

        try {
            const response = await authFetch("/chat/stream", {
                method: "POST",
                headers: { "Content-Type": "application/json" },
                body: JSON.stringify({ question })
            });

            if (!response.ok) throw new Error("Connection failed");

            const reader = response.body.getReader();
            const decoder = new TextDecoder();
            let buffer = "";

            while (true) {
                const { value, done } = await reader.read();
                if (done) break;

                buffer += decoder.decode(value, { stream: true });
                const lines = buffer.split("\n\n");
                buffer = lines.pop();

                for (const line of lines) {
                    if (line.startsWith("data: ")) {
                        try {
                            const data = JSON.parse(line.substring(6));
                            if (data.type === "status") {
                                statusEl.innerText = data.content;
                            } else if (data.type === "token") {
                                statusEl.style.display = "none";
                                contentEl.innerText += data.content;
                            } else if (data.type === "done") {
                                statusEl.style.display = "none";
                            }
                        } catch (e) {
                            console.error("Error parsing stream chunk", e);
                        }
                    }
                }
                chatMessages.scrollTop = chatMessages.scrollHeight;
            }
        } catch (err) {
            console.error("Streaming error:", err);
            statusEl.innerText = "⚠️ Connection error.";
        }
    };

    chatInput.addEventListener("keypress", (e) => {
        if (e.key === "Enter") sendBtn.click();
    });
});
