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
            console.error('Error:', error);
        }
    }

    sendBtn.addEventListener('click', handleSend);

    userInput.addEventListener('keypress', (e) => {
        if (e.key === 'Enter') {
            handleSend();
        }
    });
});
