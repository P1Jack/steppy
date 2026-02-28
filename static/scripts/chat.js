function scrollToBottom() {
    const chatMessages = document.getElementById('chat-messages');
    chatMessages.scrollTop = chatMessages.scrollHeight;
}

async function sendMessage() {
    const input = document.getElementById('message-input');
    const message = input.value.trim();

    if (!message) return;

    addMessageToChat('user', message);
    input.value = '';
    updateMessageCount();

    document.getElementById('typing-indicator').style.display = 'block';
    scrollToBottom();

    try {
        const response = await fetch('/send_message', {
            method: 'POST',
            headers: {
                'Content-Type': 'application/json',
            },
            body: JSON.stringify({ message: message })
        });

        const data = await response.json();

        if (response.ok) {
            addMessageToChat('assistant', data.response);
            updateChatHistory(data.history || []);
        } else {
            addMessageToChat('assistant', `Ошибка: ${data.error || 'Неизвестная ошибка'}`);
        }
    } catch (error) {
        addMessageToChat('assistant', `Ошибка соединения: ${error.message}`);
    } finally {
        document.getElementById('typing-indicator').style.display = 'none';
        scrollToBottom();
    }
}

function addMessageToChat(role, content) {
    const chatMessages = document.getElementById('chat-messages');
    const now = new Date();
    const timeString = now.getHours().toString().padStart(2, '0') + ':' +
                      now.getMinutes().toString().padStart(2, '0') + ':' +
                      now.getSeconds().toString().padStart(2, '0');

    const messageDiv = document.createElement('div');
    messageDiv.className = `message ${role === 'user' ? 'user-message' : 'assistant-message'}`;

    const icon = role === 'user' ? 'fa-user' : 'fa-robot';
    const sender = role === 'user' ? 'Вы' : 'Steppy';

    messageDiv.innerHTML = `
        <div class="message-content">
            <strong><i class="fas ${icon} me-2"></i>${sender}:</strong><br>
            ${content.replace(/\n/g, '<br>')}
        </div>
        <div class="message-time text-end">
            ${timeString}
        </div>
    `;

    chatMessages.appendChild(messageDiv);
}

function updateChatHistory(history) {
    updateMessageCount();
}

function updateMessageCount() {
    const messages = document.querySelectorAll('#chat-messages .message');
    document.getElementById('message-count').textContent = messages.length;
}

async function exportChat() {
    const response = await fetch('/export_chat');
    const data = await response.json();

    const blob = new Blob([JSON.stringify(data, null, 2)], { type: 'application/json' });
    const url = URL.createObjectURL(blob);
    const a = document.createElement('a');
    a.href = url;
    a.download = `gigachat-${data.session_id}-${new Date().toISOString().split('T')[0]}.json`;
    document.body.appendChild(a);
    a.click();
    document.body.removeChild(a);
    URL.revokeObjectURL(url);
}

document.addEventListener('DOMContentLoaded', function() {
    scrollToBottom();
    updateMessageCount();
    document.getElementById('message-input').focus();
});