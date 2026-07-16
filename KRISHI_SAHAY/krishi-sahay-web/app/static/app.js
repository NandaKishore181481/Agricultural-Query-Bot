// ====== VIEW SWITCHING LOGIC ======
function switchView(targetId) {
    // Hide all views
    document.querySelectorAll('.view-section').forEach(section => {
        section.classList.remove('active');
    });
    
    // Deactivate all nav links
    document.querySelectorAll('.nav-item').forEach(item => {
        item.classList.remove('active');
    });
    
    // Show target view
    document.getElementById(targetId).classList.add('active');
    
    // Activate nav link if exists
    const activeLink = document.querySelector(`.nav-item[data-target="${targetId}"]`);
    if (activeLink) {
        activeLink.classList.add('active');
    }

    // Scroll to top
    window.scrollTo({ top: 0, behavior: 'smooth' });
}

// Add event listeners to nav links
document.querySelectorAll('.nav-item').forEach(item => {
    item.addEventListener('click', (e) => {
        e.preventDefault();
        const targetId = item.getAttribute('data-target');
        switchView(targetId);
    });
});

// ====== DARK MODE TOGGLE ======
const themeToggle = document.getElementById('theme-toggle');
themeToggle.addEventListener('click', () => {
    document.body.classList.toggle('dark-mode');
    const isDark = document.body.classList.contains('dark-mode');
    themeToggle.innerHTML = isDark ? '<i class="ph ph-sun"></i>' : '<i class="ph ph-moon"></i>';
});

// ====== MOBILE MENU TOGGLE ======
const mobileMenuBtn = document.querySelector('.mobile-menu-btn');
const navbar = document.querySelector('.navbar');
if (mobileMenuBtn && navbar) {
    mobileMenuBtn.addEventListener('click', () => {
        navbar.classList.toggle('nav-open');
    });
}


// ====== AI CHAT LOGIC ======
const chatInput = document.getElementById('chat-input');
const chatMessages = document.getElementById('chat-messages');
const langSelect = document.querySelector('.lang-select');

function appendMessage(role, content) {
    const msgDiv = document.createElement('div');
    msgDiv.className = `message ${role}-message`;
    
    const icon = role === 'ai' ? '<i class="ph-fill ph-robot"></i>' : '<i class="ph-fill ph-user"></i>';
    
    msgDiv.innerHTML = `
        <div class="message-avatar">${icon}</div>
        <div class="message-content glass-bubble">
            <p>${content}</p>
        </div>
    `;
    
    chatMessages.appendChild(msgDiv);
    chatMessages.scrollTop = chatMessages.scrollHeight;
}

function handleChatEnter(event) {
    if (event.key === 'Enter') {
        sendMessage();
    }
}

async function sendMessage() {
    const text = chatInput.value.trim();
    if (!text) return;
    
    // Show user message
    appendMessage('user', text);
    chatInput.value = '';
    
    // Show typing indicator
    const typingId = 'typing-' + Date.now();
    const typingDiv = document.createElement('div');
    typingDiv.id = typingId;
    typingDiv.className = `message ai-message`;
    typingDiv.innerHTML = `
        <div class="message-avatar"><i class="ph-fill ph-robot"></i></div>
        <div class="message-content glass-bubble">
            <p>Thinking...</p>
        </div>
    `;
    chatMessages.appendChild(typingDiv);
    chatMessages.scrollTop = chatMessages.scrollHeight;

    try {
        const lang = langSelect.value;
        const response = await fetch('/api/chat', {
            method: 'POST',
            headers: { 'Content-Type': 'application/json' },
            body: JSON.stringify({ message: text, lang: lang })
        });
        
        const data = await response.json();
        
        // Remove typing indicator
        document.getElementById(typingId).remove();
        
        // Show AI response
        if (data.response) {
            appendMessage('ai', data.response);
        } else {
            appendMessage('ai', "Sorry, I couldn't process that.");
        }
    } catch (error) {
        console.error("Chat Error:", error);
        document.getElementById(typingId).remove();
        appendMessage('ai', "Network error. Please try again.");
    }
}

function clearChat() {
    chatMessages.innerHTML = `
        <div class="message ai-message">
            <div class="message-avatar"><i class="ph-fill ph-robot"></i></div>
            <div class="message-content glass-bubble">
                <p>Chat history cleared. How can I help you?</p>
            </div>
        </div>
    `;
}

// Add event listeners to suggested chips
document.querySelectorAll('.prompt-chip').forEach(chip => {
    chip.addEventListener('click', () => {
        chatInput.value = chip.innerText;
        sendMessage();
    });
});


// ====== DISEASE DETECTION LOGIC ======
const dropZone = document.getElementById('drop-zone');
const fileInput = document.getElementById('file-input');
const previewContainer = document.getElementById('preview-container');
const imagePreview = document.getElementById('image-preview');
const scanAnim = document.getElementById('scanning-anim');
const resultsCard = document.getElementById('results-card');
let currentFile = null;

// Drag and drop events
dropZone.addEventListener('dragover', (e) => {
    e.preventDefault();
    dropZone.style.background = 'rgba(46, 125, 50, 0.2)';
});
dropZone.addEventListener('dragleave', (e) => {
    e.preventDefault();
    dropZone.style.background = 'rgba(46, 125, 50, 0.05)';
});
dropZone.addEventListener('drop', (e) => {
    e.preventDefault();
    dropZone.style.background = 'rgba(46, 125, 50, 0.05)';
    if (e.dataTransfer.files.length > 0) {
        handleFiles(e.dataTransfer.files[0]);
    }
});

function handleFileSelect(event) {
    if (event.target.files.length > 0) {
        handleFiles(event.target.files[0]);
    }
}

function handleFiles(file) {
    if (!file.type.startsWith('image/')) {
        alert("Please upload an image file.");
        return;
    }
    
    currentFile = file;
    const reader = new FileReader();
    reader.onload = (e) => {
        imagePreview.src = e.target.result;
        dropZone.style.display = 'none';
        previewContainer.style.display = 'block';
        resultsCard.style.display = 'none';
    };
    reader.readAsDataURL(file);
}

function resetUpload() {
    currentFile = null;
    fileInput.value = '';
    dropZone.style.display = 'block';
    previewContainer.style.display = 'none';
    resultsCard.style.display = 'none';
}

async function analyzeImage() {
    if (!currentFile) return;
    
    document.getElementById('analyze-btn').disabled = true;
    scanAnim.style.display = 'block';
    
    const formData = new FormData();
    formData.append('image', currentFile);
    formData.append('lang', langSelect.value);

    try {
        const response = await fetch('/api/predict', {
            method: 'POST',
            body: formData
        });
        
        const data = await response.json();
        
        scanAnim.style.display = 'none';
        document.getElementById('analyze-btn').disabled = false;
        
        if (data.status === "healthy") {
            displayResults({
                Name: "Healthy Plant \u2705",
                Plant: "Unknown (Appears Healthy)",
                Description: "The uploaded leaf shows no visible signs of disease.",
                Symptoms: "None",
                Solutions: { Organic: ["Continue good agricultural practices."], Chemical: ["No action needed."] }
            });
        } else if (data.prediction) {
            displayResults(data.prediction);
        } else {
            alert(data.error || "Failed to analyze image.");
        }
    } catch (error) {
        console.error("Prediction Error:", error);
        scanAnim.style.display = 'none';
        document.getElementById('analyze-btn').disabled = false;
        alert("Network error. Could not reach the server.");
    }
}

function displayResults(data) {
    resultsCard.style.display = 'block';
    
    document.getElementById('disease-name').innerText = data.Name || 'Unknown Disease';
    document.getElementById('disease-desc').innerText = data.Description || 'No description available.';
    document.getElementById('disease-symptoms').innerText = data.Symptoms || 'No symptoms listed.';
    
    const orgList = document.getElementById('organic-treatment');
    orgList.innerHTML = '';
    if (data.Solutions && data.Solutions.Organic) {
        data.Solutions.Organic.forEach(item => {
            const li = document.createElement('li');
            li.innerText = item;
            orgList.appendChild(li);
        });
    } else {
        orgList.innerHTML = '<li>No organic treatment found.</li>';
    }
    
    const chemList = document.getElementById('chemical-treatment');
    chemList.innerHTML = '';
    if (data.Solutions && data.Solutions.Chemical) {
        data.Solutions.Chemical.forEach(item => {
            const li = document.createElement('li');
            li.innerText = item;
            chemList.appendChild(li);
        });
    } else {
        chemList.innerHTML = '<li>No chemical treatment found.</li>';
    }
}

// Result Tabs logic
document.querySelectorAll('.tab-btn').forEach(btn => {
    btn.addEventListener('click', () => {
        document.querySelectorAll('.tab-btn').forEach(b => b.classList.remove('active'));
        document.querySelectorAll('.tab-content').forEach(c => c.classList.remove('active'));
        
        btn.classList.add('active');
        document.getElementById('tab-' + btn.getAttribute('data-tab')).classList.add('active');
    });
});
