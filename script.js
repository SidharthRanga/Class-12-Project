document.addEventListener('DOMContentLoaded', () => {
    const chatWindow = document.getElementById('chat-window');
    const userInput = document.getElementById('user-input');
    const sendBtn = document.getElementById('send-btn');

    function appendMessage(text, sender) {
        const msgDiv = document.createElement('div');
        msgDiv.classList.add('message');
        msgDiv.classList.add(sender === 'user' ? 'user-message' : 'ai-message');

        // Format Markdown-like syntax
        let formattedText = text
            // 1. Bold: **text** or __text__ -> <strong>text</strong>
            .replace(/\*\*(.*?)\*\*/g, '<strong>$1</strong>')
            .replace(/__(.*?)__/g, '<strong>$1</strong>')
            // 2. Bullet Points: Lines starting with * or - -> • text
            .replace(/^[\*\-]\s(.*$)/gm, '• $1')
            // 3. Italic: *text* or _text_ -> <em>text</em>
            .replace(/\*(.*?)\*/g, '<em>$1</em>')
            .replace(/_(.*?)_/g, '<em>$1</em>')
            // 4. Headers: # Text -> <strong>Text</strong>
            .replace(/^# (.*$)/gm, '<strong>$1</strong>')
            .replace(/^## (.*$)/gm, '<strong>$1</strong>')
            .replace(/^### (.*$)/gm, '<strong>$1</strong>')
            // 5. Paragraphs and line breaks
            .replace(/\n\n/g, '</p><p>')
            .replace(/\n/g, '<br>');

        msgDiv.innerHTML = `<p>${formattedText}</p>`;

        chatWindow.appendChild(msgDiv);

        // Scroll to bottom
        chatWindow.scrollTop = chatWindow.scrollHeight;
    }

    async function handleSend() {
        const text = userInput.value.trim();
        if (text === '') return;

        // Append User Message
        appendMessage(text, 'user');
        userInput.value = '';

        // Show Loading State
        const loadingDiv = document.createElement('div');
        loadingDiv.classList.add('message', 'ai-message');
        loadingDiv.textContent = '...';
        loadingDiv.id = 'loading-msg';
        chatWindow.appendChild(loadingDiv);
        chatWindow.scrollTop = chatWindow.scrollHeight;

        try {
            const response = await fetch('/chat', {
                method: 'POST',
                headers: {
                    'Content-Type': 'application/json',
                },
                body: JSON.stringify({ message: text }),
            });

            const data = await response.json();

            // Remove loading indicator
            const loadingMsg = document.getElementById('loading-msg');
            if (loadingMsg) loadingMsg.remove();

            if (data.response) {
                appendMessage(data.response, 'ai');
            } else if (data.error) {
                appendMessage('Error: ' + data.error, 'ai');
            }
        } catch (error) {
            const loadingMsg = document.getElementById('loading-msg');
            if (loadingMsg) loadingMsg.remove();
            appendMessage('Sorry, something went wrong. Please try again.', 'ai');
            console.error(error);
        }
    }

    sendBtn.addEventListener('click', handleSend);

    userInput.addEventListener('keypress', (e) => {
        if (e.key === 'Enter') {
            handleSend();
        }
    });
});

async function clearCurrentSessionHistory() {
    if (confirm("Are you sure you want to clear the current session history?")) {
        try {
            const response = await fetch('/clear', { method: 'POST' });
            const result = await response.json();
            if (result.success) {
                alert("Chat history cleared!");
                location.reload();
            }
        } catch (error) {
            console.error("Error clearing history:", error);
            alert("Failed to clear history. Please try again.");
        }
    }
}

function toggleSettings() {
    const modal = document.getElementById('settings-modal');
    modal.style.display = (modal.style.display === 'none' || modal.style.display === '') ? 'flex' : 'none';

    if (modal.style.display === 'flex') {
        loadAccountInfo();
    }
}

function togglePasswordVisibility() {
    const passInput = document.getElementById('current-password');
    const btn = document.getElementById('toggle-pass-btn');
    if (passInput.type === 'password') {
        passInput.type = 'text';
        btn.textContent = 'Hide';
    } else {
        passInput.type = 'password';
        btn.textContent = 'Show';
    }
}

function toggleNewPasswordVisibility() {
    const passInput = document.getElementById('new-password');
    const btn = document.getElementById('toggle-new-pass-btn');
    if (passInput.type === 'password') {
        passInput.type = 'text';
        btn.textContent = 'Hide';
    } else {
        passInput.type = 'password';
        btn.textContent = 'Show';
    }
}

function toggleKeyVisibility() {
    const keyInput = document.getElementById('current-api-key');
    const btn = document.getElementById('toggle-key-btn');
    if (keyInput.type === 'password') {
        keyInput.type = 'text';
        btn.textContent = 'Hide';
    } else {
        keyInput.type = 'password';
        btn.textContent = 'Show';
    }
}

function toggleNewKeyVisibility() {
    const keyInput = document.getElementById('new-api-key');
    const btn = document.getElementById('toggle-new-key-btn');
    if (keyInput.type === 'password') {
        keyInput.type = 'text';
        btn.textContent = 'Hide';
    } else {
        keyInput.type = 'password';
        btn.textContent = 'Show';
    }
}

async function loadAccountInfo() {
    try {
        const response = await fetch('/get_account_info');
        const data = await response.json();
        if (data.success) {
            document.getElementById('current-password').value = data.password || '';
            document.getElementById('current-api-key').value = data.ollama_key || '';
            document.getElementById('new-password').value = '';
            document.getElementById('new-api-key').value = '';
        }
    } catch (error) {
        console.error("Error loading account info:", error);
    }
}

async function updatePassword() {
    const password = document.getElementById('new-password').value;
    if (!password) {
        alert("Please enter a new password.");
        return;
    }
    await performAccountUpdate({ password });
}

async function updateApiKey() {
    const apiKey = document.getElementById('new-api-key').value;
    if (!apiKey) {
        alert("Please enter a new API key.");
        return;
    }
    await performAccountUpdate({ ollama_key: apiKey });
}

async function performAccountUpdate(data) {
    try {
        const response = await fetch('/update_account', {
            method: 'POST',
            headers: {
                'Content-Type': 'application/json',
            },
            body: JSON.stringify(data),
        });

        const result = await response.json();
        if (result.success) {
            alert("Updated successfully!");
            document.getElementById('new-password').value = '';
            document.getElementById('new-api-key').value = '';
        } else {
            alert("Error: " + result.error);
        }
    } catch (error) {
        console.error("Error updating account:", error);
        alert("Failed to update account. Please try again.");
    }
}

async function logout() {
    try {
        const response = await fetch('/logout', { method: 'POST' });
        const result = await response.json();
        if (result.success) {
            alert("Logged out successfully!");
            window.location.href = '/';
        } else {
            alert("Logout failed. Please try again.");
        }
    } catch (error) {
        console.error("Error during logout:", error);
        alert("An error occurred during logout.");
    }
}
