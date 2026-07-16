// ====== NAVIGATION ======
function switchView(viewId) {
    // Update hash without triggering hashchange again
    if(window.location.hash !== `#${viewId}`) {
        window.history.pushState(null, null, `#${viewId}`);
    }

    document.querySelectorAll('.view-section').forEach(section => {
        section.classList.remove('active');
    });
    document.querySelectorAll('.nav-item').forEach(item => {
        item.classList.remove('active');
    });
    
    document.getElementById(viewId).classList.add('active');
    
    // Find nav item (might be in mobile menu or desktop)
    const navItems = document.querySelectorAll(`.nav-item[data-target="${viewId}"]`);
    navItems.forEach(item => item.classList.add('active'));

    // Close mobile menu if open
    const navbar = document.querySelector('.navbar');
    if(navbar) navbar.classList.remove('nav-open');
}

// Handle browser back/forward and initial load
window.addEventListener('hashchange', () => {
    const hash = window.location.hash.substring(1);
    if(hash) switchView(hash);
});

// Setup click listeners for navigation links
document.querySelectorAll('.nav-item').forEach(item => {
    item.addEventListener('click', (e) => {
        e.preventDefault();
        const targetId = item.getAttribute('data-target');
        switchView(targetId);
    });
});

// Initial View Load based on URL hash
window.addEventListener('DOMContentLoaded', () => {
    const hash = window.location.hash.substring(1);
    if(hash) {
        switchView(hash);
    } else {
        switchView('home-view');
    }
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

// ====== SPEECH RECOGNITION ======
function startVoiceRecognition() {
    const SpeechRecognition = window.SpeechRecognition || window.webkitSpeechRecognition;
    if (!SpeechRecognition) {
        alert("Sorry, your browser doesn't support voice recognition. Please try Chrome or Safari.");
        return;
    }

    const recognition = new SpeechRecognition();
    const micIcon = document.getElementById('mic-icon');
    const inputField = document.getElementById('chat-input');
    const langSelect = document.getElementById('lang-select');
    
    // Map our app languages to speech recognition languages
    const langMap = {
        'en': 'en-US',
        'hi': 'hi-IN',
        'te': 'te-IN'
    };
    recognition.lang = langMap[langSelect.value] || 'en-US';
    recognition.interimResults = false;
    recognition.maxAlternatives = 1;

    recognition.onstart = function() {
        micIcon.classList.remove('ph-microphone');
        micIcon.classList.add('ph-waveform', 'text-yellow');
        inputField.placeholder = "Listening...";
    };

    recognition.onresult = function(event) {
        const transcript = event.results[0][0].transcript;
        inputField.value = transcript;
    };

    recognition.onspeechend = function() {
        recognition.stop();
    };

    recognition.onend = function() {
        micIcon.classList.add('ph-microphone');
        micIcon.classList.remove('ph-waveform', 'text-yellow');
        inputField.placeholder = "Ask anything about farming...";
    };

    recognition.onerror = function(event) {
        console.error("Speech Recognition Error:", event.error);
        alert("Voice recognition failed. Please ensure you have granted microphone permissions.");
        micIcon.classList.add('ph-microphone');
        micIcon.classList.remove('ph-waveform', 'text-yellow');
        inputField.placeholder = "Ask anything about farming...";
    };

    recognition.start();
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

// ====== WEATHER LOGIC ======
async function fetchWeatherManual() {
    const city = document.getElementById('weather-location-input').value;
    if(!city) return;
    try {
        const geoRes = await fetch('https://geocoding-api.open-meteo.com/v1/search?name=' + city + '&count=1');
        const geoData = await geoRes.json();
        if(geoData.results && geoData.results.length > 0) {
            const { latitude, longitude, name } = geoData.results[0];
            getWeatherFromCoords(latitude, longitude, name);
        } else {
            alert('City not found!');
        }
    } catch(err) {
        console.error(err);
    }
}

function fetchWeatherGPS() {
    if(navigator.geolocation) {
        navigator.geolocation.getCurrentPosition(
            (pos) => getWeatherFromCoords(pos.coords.latitude, pos.coords.longitude, 'Your Location'),
            (err) => alert('Location access denied or failed.')
        );
    }
}

async function getWeatherFromCoords(lat, lon, locationName) {
    document.getElementById('weather-location-input').value = locationName;
    document.getElementById('weather-desc').innerText = 'Fetching...';
    try {
        const res = await fetch('https://api.open-meteo.com/v1/forecast?latitude='+lat+'&longitude='+lon+'&current=temperature_2m,relative_humidity_2m,precipitation,wind_speed_10m&timezone=auto');
        const data = await res.json();
        const current = data.current;
        document.getElementById('weather-temp').innerText = current.temperature_2m + '°C';
        document.getElementById('weather-humidity').innerText = current.relative_humidity_2m + '%';
        document.getElementById('weather-wind').innerText = current.wind_speed_10m + ' km/h';
        document.getElementById('weather-rain').innerText = current.precipitation > 0 ? 'High' : '0%';
        document.getElementById('weather-desc').innerText = 'Updated Just Now';
        document.getElementById('weather-advice').innerHTML = current.precipitation > 0 
            ? 'Rain detected! Avoid spraying chemicals or fertilizers today. Ensure proper drainage in fields.'
            : 'Conditions are dry. Good time for harvesting or spraying. Check soil moisture and irrigate if necessary.';
    } catch (e) {
        document.getElementById('weather-desc').innerText = 'Failed to load';
    }
}

// ====== MANDI PRICES LOGIC ======
const mandiData = [
    { crop: 'Tomato', price: '₹45', trend: 'up', diff: '+₹5', market: 'Bowenpally Market' },
    { crop: 'Onion', price: '₹30', trend: 'down', diff: '-₹2', market: 'Bowenpally Market' },
    { crop: 'Rice (Sona Masuri)', price: '₹55', trend: 'neutral', diff: '₹0', market: 'Malakpet Market' },
    { crop: 'Wheat', price: '₹28', trend: 'up', diff: '+₹1', market: 'Siddipet Market' },
    { crop: 'Cotton', price: '₹7200', trend: 'up', diff: '+₹150', market: 'Warangal Market' },
    { crop: 'Chilli', price: '₹150', trend: 'down', diff: '-₹10', market: 'Guntur Market' }
];

function renderMandi(data) {
    const grid = document.getElementById('mandi-grid');
    if(!grid) return;
    grid.innerHTML = data.map(item => `
        <div class='mandi-card glass-panel'>
            <div class='crop-header'>
                <h3>${item.crop}</h3>
                <span class='trend ${item.trend}'><i class='ph-bold ph-arrow-${item.trend === 'up' ? 'up-right' : item.trend === 'down' ? 'down-right' : 'minus'}'></i> ${item.diff}</span>
            </div>
            <div class='price-big'>${item.price} <span>/ ${item.price.includes('7200') ? 'quintal' : 'kg'}</span></div>
            <p class='market-name'><i class='ph ph-storefront'></i> ${item.market}</p>
            <p class='date'>Updated: Today, 09:00 AM</p>
        </div>
    `).join('');
}

function filterMandi() {
    const query = document.getElementById('mandi-search').value.toLowerCase();
    const filtered = mandiData.filter(d => d.crop.toLowerCase().includes(query) || d.market.toLowerCase().includes(query));
    renderMandi(filtered);
}

// ====== SCHEMES LOGIC ======
const schemesData = [
    { title: 'PM Kisan Samman Nidhi', desc: 'Financial benefit of ₹6,000 per year is provided to all landholding farmer families.', tags: ['Financial Aid', 'Central Govt'] },
    { title: 'Rythu Bandhu', desc: 'Investment support scheme by providing a grant of ₹5,000 per acre per farmer each season.', tags: ['State Govt', 'Investment'] },
    { title: 'Pradhan Mantri Fasal Bima Yojana', desc: 'Crop insurance scheme integrating multiple stakeholders on a single platform.', tags: ['Insurance', 'Central Govt'] },
    { title: 'Kisan Credit Card', desc: 'Provides adequate and timely credit support from the banking system under a single window.', tags: ['Credit', 'Banking'] }
];

function renderSchemes(data) {
    const list = document.getElementById('schemes-list');
    if(!list) return;
    list.innerHTML = data.map(item => `
        <div class='scheme-card glass-panel'>
            <div class='scheme-content'>
                <h3>${item.title}</h3>
                <p class='scheme-desc'>${item.desc}</p>
                <div class='scheme-tags'>
                    ${item.tags.map(t => `<span class='tag'>${t}</span>`).join('')}
                </div>
            </div>
            <div class='scheme-action'>
                <button class='btn btn-primary'>Check Eligibility</button>
            </div>
        </div>
    `).join('');
}

function filterSchemes() {
    const query = document.getElementById('scheme-search').value.toLowerCase();
    const filtered = schemesData.filter(d => d.title.toLowerCase().includes(query) || d.desc.toLowerCase().includes(query));
    renderSchemes(filtered);
}

// ====== DASHBOARD LOGIC ======
function addCrop() {
    const input = document.getElementById('new-crop-input');
    const crop = input.value.trim();
    if(crop) {
        let crops = JSON.parse(localStorage.getItem('myCrops') || '["Tomato", "Bell Pepper"]');
        if(!crops.includes(crop)) {
            crops.push(crop);
            localStorage.setItem('myCrops', JSON.stringify(crops));
            renderCrops();
        }
        input.value = '';
    }
}

function renderCrops() {
    const container = document.getElementById('my-crops-list');
    if(!container) return;
    let crops = JSON.parse(localStorage.getItem('myCrops') || '["Tomato", "Bell Pepper"]');
    container.innerHTML = crops.map(c => `<span class='crop-tag'>${c} <i class='ph ph-x' style='cursor:pointer' onclick='removeCrop("${c}")'></i></span>`).join('');
}

function removeCrop(crop) {
    let crops = JSON.parse(localStorage.getItem('myCrops') || '[]');
    crops = crops.filter(c => c !== crop);
    localStorage.setItem('myCrops', JSON.stringify(crops));
    renderCrops();
}

function updateRecentChats() {
    const list = document.getElementById('recent-chats-list');
    if(!list) return;
    let chats = JSON.parse(localStorage.getItem('chatHistory') || '[]');
    if(chats.length === 0) {
        list.innerHTML = '<li>No recent consultations. Start chatting with the AI Assistant!</li>';
    } else {
        // Show last 3 messages from the user
        const userChats = chats.filter(c => c.type === 'user').slice(-3).reverse();
        list.innerHTML = userChats.map(c => `<li><i class='ph ph-chat-circle'></i> ${c.text.substring(0, 30)}... <span class='date'>Recent</span></li>`).join('');
    }
}

// Hook into the existing appendMessage to save chat history
if (typeof originalAppendMessage === 'undefined') {
    window.originalAppendMessage = window.appendMessage;
    window.appendMessage = function(sender, text, isHtml) {
        if(window.originalAppendMessage) window.originalAppendMessage(sender, text, isHtml);
        if(sender === 'user') {
            let chats = JSON.parse(localStorage.getItem('chatHistory') || '[]');
            chats.push({type: 'user', text: text});
            localStorage.setItem('chatHistory', JSON.stringify(chats));
            updateRecentChats();
        }
    }
}

// Init all
window.addEventListener('DOMContentLoaded', () => {
    renderMandi(mandiData);
    renderSchemes(schemesData);
    renderCrops();
    updateRecentChats();
});
