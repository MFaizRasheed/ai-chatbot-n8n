const app = document.getElementById("app");

let messages = [];
let isLoading = false;
let sidebarOpen = false;

let sessionId = localStorage.getItem("chat_session_id");

if (!sessionId) {
    sessionId = crypto.randomUUID();

    localStorage.setItem(
        "chat_session_id",
        sessionId
    );
}

function render() {
    app.innerHTML = `
        <div class="app-shell">

            ${renderMobileOverlay()}

            <aside class="sidebar ${sidebarOpen ? "open" : ""}">

                <div class="sidebar-header">

                    <div class="brand">

                        <div class="brand-icon">
                            AI
                        </div>

                        <div class="brand-text">
                            <h1>AI Assistant</h1>
                            <span>Smart Automation</span>
                        </div>

                    </div>

                    <button
                        id="close-sidebar"
                        class="icon-button mobile-only"
                        aria-label="Close menu"
                    >
                        ×
                    </button>

                </div>

                <button
                    id="new-chat"
                    class="new-chat"
                >
                    <span class="new-chat-icon">+</span>
                    <span>New Chat</span>
                </button>

                <div class="sidebar-section">

                    <div class="section-header">
                        <span>Chats</span>
                    </div>

                    ${
                        messages.length > 0
                            ? `
                                <button
                                    class="conversation-item active"
                                >
                                    <span class="conversation-icon">
                                        ◌
                                    </span>

                                    <span class="conversation-title">
                                        Current conversation
                                    </span>
                                </button>
                            `
                            : `
                                <div class="empty-history">
                                    No conversations yet
                                </div>
                            `
                    }

                </div>

                <div class="sidebar-bottom">

                    <button
                        id="clear-chat"
                        class="sidebar-action"
                    >
                        <span>⌫</span>
                        Clear conversation
                    </button>

                    <div class="sidebar-footer">
                        AI Assistant
                        <span>v1.0</span>
                    </div>

                </div>

            </aside>

            <main class="chat-container">

                <header class="chat-header">

                    <button
                        id="menu-button"
                        class="icon-button mobile-only"
                        aria-label="Open menu"
                    >
                        ☰
                    </button>

                    <div class="header-info">

                        <div class="header-title">
                            AI Assistant
                        </div>

                        <div class="header-status">

                            <span class="status-dot"></span>

                            <span>
                                Online
                            </span>

                        </div>

                    </div>

                </header>

                <section
                    id="messages"
                    class="messages"
                >
                    ${
                        messages.length === 0 && !isLoading
                            ? renderWelcome()
                            : renderMessages()
                    }

                    ${
                        isLoading
                            ? renderTypingIndicator()
                            : ""
                    }
                </section>

                <div class="input-area">

                    <form
                        id="chat-form"
                        class="chat-form"
                    >

                        <textarea
                            id="message-input"
                            placeholder="Message AI Assistant..."
                            rows="1"
                            maxlength="2000"
                        ></textarea>

                        <button
                            id="send-button"
                            type="submit"
                            class="send-button"
                            ${isLoading ? "disabled" : ""}
                            aria-label="Send message"
                        >
                            ${
                                isLoading
                                    ? `<span class="send-spinner"></span>`
                                    : "➤"
                            }
                        </button>

                    </form>

                    <div class="input-footer">

                        <span>
                            AI can make mistakes. Verify important information.
                        </span>

                        <span class="desktop-hint">
                            Enter to send · Shift + Enter for new line
                        </span>

                    </div>

                </div>

            </main>

        </div>
    `;

    attachEvents();

    scrollMessages();

    if (!isLoading) {
        focusInput();
    }
}

function renderMobileOverlay() {
    if (!sidebarOpen) {
        return "";
    }

    return `
        <div
            id="sidebar-overlay"
            class="sidebar-overlay"
        ></div>
    `;
}

function renderWelcome() {
    return `
        <div class="welcome">

            <div class="welcome-icon">
                <span>AI</span>
            </div>

            <h2>
                How can I help you?
            </h2>

            <p>
                Start a conversation with your AI assistant.
                Ask questions, get information, or explore
                what the assistant can do.
            </p>

            <div class="suggestions">

                <button
                    class="suggestion-card"
                    data-suggestion="Hello"
                >
                    <span class="suggestion-icon">✦</span>

                    <span>
                        <strong>Say hello</strong>
                        <small>Start a conversation</small>
                    </span>
                </button>

                <button
                    class="suggestion-card"
                    data-suggestion="What can you do?"
                >
                    <span class="suggestion-icon">?</span>

                    <span>
                        <strong>What can you do?</strong>
                        <small>Learn about the assistant</small>
                    </span>
                </button>

                <button
                    class="suggestion-card"
                    data-suggestion="Tell me about yourself"
                >
                    <span class="suggestion-icon">◈</span>

                    <span>
                        <strong>About yourself</strong>
                        <small>Learn more about the AI</small>
                    </span>
                </button>

            </div>

        </div>
    `;
}

function renderMessages() {
    return `
        <div class="message-list">

            ${messages.map((message) => {

                const time = formatTime(
                    message.timestamp
                );

                return `
                    <article
                        class="message ${message.role}"
                    >

                        <div class="message-avatar">

                            ${
                                message.role === "user"
                                    ? "U"
                                    : "AI"
                            }

                        </div>

                        <div class="message-body">

                            <div class="message-meta">

                                <strong>
                                    ${
                                        message.role === "user"
                                            ? "You"
                                            : "AI Assistant"
                                    }
                                </strong>

                                <span>
                                    ${time}
                                </span>

                            </div>

                            <div class="message-text">
                                ${formatMessage(message.content)}
                            </div>

                        </div>

                    </article>
                `;

            }).join("")}

        </div>
    `;
}

function renderTypingIndicator() {
    return `
        <div class="typing-message">

            <div class="message-avatar">
                AI
            </div>

            <div class="typing-content">

                <div class="message-meta">
                    <strong>AI Assistant</strong>
                </div>

                <div class="typing-indicator">

                    <span></span>
                    <span></span>
                    <span></span>

                </div>

            </div>

        </div>
    `;
}

function attachEvents() {

    const form =
        document.getElementById("chat-form");

    const input =
        document.getElementById("message-input");

    const newChat =
        document.getElementById("new-chat");

    const clearChat =
        document.getElementById("clear-chat");

    const menuButton =
        document.getElementById("menu-button");

    const closeSidebar =
        document.getElementById("close-sidebar");

    const overlay =
        document.getElementById("sidebar-overlay");

    if (form) {
        form.addEventListener(
            "submit",
            async (event) => {

                event.preventDefault();

                if (isLoading) {
                    return;
                }

                const content =
                    input.value.trim();

                if (!content) {
                    return;
                }

                await sendMessage(content);
            }
        );
    }

    if (input) {

        input.addEventListener(
            "keydown",
            (event) => {

                if (
                    event.key === "Enter" &&
                    !event.shiftKey
                ) {
                    event.preventDefault();

                    form.requestSubmit();
                }

            }
        );

        input.addEventListener(
            "input",
            () => {

                input.style.height =
                    "auto";

                input.style.height =
                    `${Math.min(
                        input.scrollHeight,
                        180
                    )}px`;
            }
        );
    }

    if (newChat) {

        newChat.addEventListener(
            "click",
            () => {

                startNewChat();

                sidebarOpen = false;

                render();
            }
        );
    }

    if (clearChat) {

        clearChat.addEventListener(
            "click",
            () => {

                messages = [];

                render();
            }
        );
    }

    if (menuButton) {

        menuButton.addEventListener(
            "click",
            () => {

                sidebarOpen = true;

                render();
            }
        );
    }

    if (closeSidebar) {

        closeSidebar.addEventListener(
            "click",
            () => {

                sidebarOpen = false;

                render();
            }
        );
    }

    if (overlay) {

        overlay.addEventListener(
            "click",
            () => {

                sidebarOpen = false;

                render();
            }
        );
    }

    document
        .querySelectorAll("[data-suggestion]")
        .forEach((button) => {

            button.addEventListener(
                "click",
                () => {

                    const text =
                        button.dataset.suggestion;

                    if (text) {
                        sendMessage(text);
                    }

                }
            );

        });
}

async function sendMessage(content) {

    messages.push({
        role: "user",
        content,
        timestamp: Date.now()
    });

    isLoading = true;

    render();

    try {

        const response =
            await fetch(
                "/api/chat",
                {
                    method: "POST",

                    headers: {
                        "Content-Type":
                            "application/json"
                    },

                    body: JSON.stringify({
                        message: content,
                        session_id: sessionId
                    })
                }
            );

        const data =
            await response.json();

        if (!response.ok) {

            throw new Error(
                data.detail ||
                data.error ||
                "Unable to get a response."
            );
        }

        const reply =
            data.response ||
            data.reply;

        if (!reply) {

            throw new Error(
                "The AI service returned an empty response."
            );
        }

        messages.push({
            role: "assistant",
            content: String(reply),
            timestamp: Date.now()
        });

    } catch (error) {

        messages.push({
            role: "assistant",
            content:
                error.message ||
                "Something went wrong. Please try again.",
            timestamp: Date.now(),
            error: true
        });

    } finally {

        isLoading = false;

        render();
    }
}

function startNewChat() {

    messages = [];

    sessionId =
        crypto.randomUUID();

    localStorage.setItem(
        "chat_session_id",
        sessionId
    );
}

function formatMessage(value) {

    if (!value) {
        return "";
    }

    return escapeHtml(String(value))
        .replace(
            /\n/g,
            "<br>"
        );
}

function escapeHtml(value) {

    const div =
        document.createElement("div");

    div.textContent = value;

    return div.innerHTML;
}

function formatTime(timestamp) {

    if (!timestamp) {
        return "";
    }

    return new Date(timestamp)
        .toLocaleTimeString(
            [],
            {
                hour: "2-digit",
                minute: "2-digit"
            }
        );
}

function scrollMessages() {

    const container =
        document.getElementById("messages");

    if (!container) {
        return;
    }

    requestAnimationFrame(() => {

        container.scrollTop =
            container.scrollHeight;

    });
}

function focusInput() {

    const input =
        document.getElementById(
            "message-input"
        );

    if (input && window.innerWidth > 560) {
        input.focus();
    }
}

render();