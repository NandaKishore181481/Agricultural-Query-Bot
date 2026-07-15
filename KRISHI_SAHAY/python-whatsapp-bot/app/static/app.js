const chatBox = document.getElementById('chat-box');
const chatInput = document.getElementById('chat-input');
const languageSelect = document.getElementById('language');

function appendMessage(text, sender, isHTML = false) {
    const div = document.createElement('div');
    div.className = `message ${sender}`;
    if (isHTML) {
        div.innerHTML = text;
    } else {
        div.innerText = text;
    }
    chatBox.appendChild(div);
    chatBox.scrollTop = chatBox.scrollHeight;
    return div;
}

function handleEnter(event) {
    if (event.key === 'Enter') {
        sendMessage();
    }
}

async function sendMessage() {
    const text = chatInput.value.trim();
    if (!text) return;

    appendMessage(text, 'user');
    chatInput.value = '';

    const lang = languageSelect.value;
    
    // Add loading indicator
    const loadingMsg = appendMessage('...', 'bot uploading');

    try {
        const response = await fetch('/api/chat', {
            method: 'POST',
            headers: { 'Content-Type': 'application/json' },
            body: JSON.stringify({ message: text, lang: lang })
        });
        
        const data = await response.json();
        chatBox.removeChild(loadingMsg);
        
        // Use marked.js if available, otherwise just format basic markdown
        const formattedResponse = formatMarkdown(data.response);
        appendMessage(formattedResponse, 'bot', true);
    } catch (err) {
        chatBox.removeChild(loadingMsg);
        appendMessage('Error connecting to the server.', 'bot');
    }
}

async function handleImageUpload(input) {
    const file = input.files[0];
    if (!file) return;

    const lang = languageSelect.value;
    const loadingMsg = appendMessage(`Uploading image: ${file.name}...`, 'user uploading');

    const formData = new FormData();
    formData.append('image', file);
    formData.append('lang', lang);

    try {
        const response = await fetch('/api/predict', {
            method: 'POST',
            body: formData
        });
        
        const data = await response.json();
        chatBox.removeChild(loadingMsg);
        
        if (data.error) {
            appendMessage(data.error, 'bot');
        } else if (data.status === 'healthy') {
            appendMessage(data.message, 'bot');
        } else {
            const p = data.prediction;
            let html = `<strong>Identified: ${p.Name}</strong><br>`;
            html += `<em>Plant: ${p.Plant || 'Unknown'}</em><br><br>`;
            html += `${p.Description}<br><br>`;
            html += `<strong>Symptoms:</strong> ${p.Symptoms}<br><br>`;
            html += `<strong>Solutions:</strong><br>`;
            
            if (p.Solutions) {
                if (p.Solutions.Chemical) html += `🧪 <em>Chemical:</em> ${p.Solutions.Chemical.join(' ')}<br>`;
                if (p.Solutions.Organic) html += `🌿 <em>Organic:</em> ${p.Solutions.Organic.join(' ')}<br>`;
            }
            
            appendMessage(html, 'bot', true);
        }
    } catch (err) {
        chatBox.removeChild(loadingMsg);
        appendMessage('Error uploading the image.', 'bot');
    }
    
    input.value = ''; // Reset file input
}

function changeLanguage() {
    const lang = languageSelect.value;
    const msg = {
        'en': 'Language changed to English.',
        'hi': 'भाषा हिंदी में बदल दी गई है।',
        'te': 'భాష తెలుగుకి మార్చబడింది.'
    };
    appendMessage(msg[lang], 'bot');
}

// Very basic markdown formatter for bold text
function formatMarkdown(text) {
    if (!text) return "";
    return text.replace(/\*\*(.*?)\*\*/g, '<strong>$1</strong>')
               .replace(/\n/g, '<br>');
}
